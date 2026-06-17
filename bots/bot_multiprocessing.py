import asyncio
import os
import json
from socket import socket
from models.genetic.Genome import Genome
from models.genetic.GeneticBot import GeneticBot
from models.genetic.fitness import calculate_fitness
from botsocket import BotSocket
from training_seeder import seed_genomes
import multiprocessing
from logger import Logger  # <-- Import the Logger

active_bot_processes = []
training_data_queue = multiprocessing.Queue()

# Instantiate a logger for the parent server process
server_logger = Logger("SERVER_MANAGER")


def run_bot_process(game_id: str,
                    bot_secret: str,
                    result_queue: multiprocessing.Queue,
                    assigned_genome_dict: dict | None = None):

    # Instantiate a unique logger for this specific child process using its PID
    bot_logger = Logger(f"Worker_{os.getpid()}", game_id=game_id)
    bot_logger.info(f"Sarting isolated process for game {game_id}")

    fitness_sent = False
    training = False

    async def main():
        if assigned_genome_dict:
            genome = Genome(**assigned_genome_dict)
        else:
            genome = Genome.random()

        bot = GeneticBot(genome)
        # Pass the logger to the bot so it can log logic decisions (optional)
        bot.logger = bot_logger

        host_ready_event = asyncio.Event()
        game_ended = False

        # Pass the logger into the socket client
        socket = BotSocket(
            game_id=game_id,
            bot_secret=bot_secret,
            logger=bot_logger,  # <-- Inject here
            http_url=os.environ.get(
                "GAME_SERVER_HTTP_URL", "http://localhost:5000"),
            ws_url=os.environ.get("GAME_SERVER_WS_URL",
                                  "ws://localhost:5000/ws")
        )

        async def on_game_state(state):

            nonlocal fitness_sent, game_ended

            if not host_ready_event.is_set():
                if state.get("host_connected") is True:
                    bot_logger.info("Host joined. Activating bot logic.")
                    host_ready_event.set()
                else:
                    return

            me = state.get("me", {})
            if (me.get("health") == "dead" and not fitness_sent) or (state.get("status") == "ENDED" and not fitness_sent):
                fitness_score = calculate_fitness(state)

                result_queue.put({
                    "game_id": game_id,
                    "Day": state.get("day"),
                    "bot_id": me.get("id"),
                    "fitness": fitness_score,
                    "genome": bot.genome.__dict__
                })
                fitness_sent = True
                bot_logger.info(
                    f"Bot died/Game ended. Fitness: {fitness_score} sent to parent.")

            if state.get("status") == "ENDED":
                game_ended = True
                await socket.disconnect()
                return

            if state.get("status") != "RUNNING" or not host_ready_event.is_set():
                return

            try:
                action = bot.choose_action(state)
                if action:
                    await socket.submit_action(action)
                    if action["action_command"] == "EMPLOYMENT" and not state.get("training"):
                        await asyncio.sleep(5)
                    elif state.get("training"):
                        training = True
                    if state.get("phase") in ["TRADE", "NIGHT"] and action["action_command"] == "CAMPFIRE":
                        await socket.submit_action({
                            "action_command": "FINISH_PHASE",
                            "payload": {}
                        })
            except Exception as e:
                bot_logger.stdout_error(
                    "Failed to process game logic", exception=e)

            # Auto-finalize accepted trades
            me_actions = me.get("actions", [])
            for a in me_actions:
                try:
                    if a.get("type") == "TRADE" and a.get("status") == "ACCEPTED":
                        is_initiator = a.get("initiator_id") == me.get("id")
                        already_finalized = a.get(
                            "initiator_finalized") if is_initiator else a.get("target_finalized")
                        if already_finalized:
                            continue

                        promised = a.get("offer_items") if is_initiator else a.get(
                            "request_items")
                        feasible = {}
                        for r, qty in (promised or {}).items():
                            try:
                                q = int(qty)
                            except Exception:
                                q = 0
                            available = int(me.get("resources", {}).get(r, 0))
                            send_amt = max(0, min(q, available))
                            if send_amt > 0:
                                feasible[r] = send_amt

                        if feasible:
                            await socket.submit_action({
                                "action_command": "FINALIZE",
                                "payload": {
                                    "action_id": a.get("id"),
                                    "actual_items": feasible
                                }
                            })
                            await asyncio.sleep(0.2)
                except Exception as e:
                    bot_logger.handled_error(
                        "Trade auto-finalize failed", exception=e)
                    continue

        socket.on_game_state = on_game_state
        await asyncio.sleep(1.0)  # add backoff after reconnect attempt
        success = await socket.connect()

        while not game_ended:
            if success:
                while socket._listen_task and not socket._listen_task.done():
                    if training:
                        await asyncio.sleep(.01)
                    else:
                        await asyncio.sleep(0.25)
            if game_ended:
                break
            await asyncio.sleep(0.2)
            success = await socket.connect()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        bot_logger.info("Process interrupted by user.")
    except Exception as e:
        bot_logger.stdout_error(
            "Fatal error in bot process event loop", exception=e)


async def process_training_data(queue: multiprocessing.Queue):
    server_logger.info("Starting training data aggregation loop.")
    while True:
        while not queue.empty():
            result = queue.get()
            with open("bot_training_data.jsonl", "a") as f:
                f.write(json.dumps(result) + "\n")
            server_logger.info(f"📊 Saved training data! Bot Fitness:    "
                               f"{result['fitness']}")
        await asyncio.sleep(0.5)


async def reap_zombies():
    server_logger.info("Starting zombie process reaper.")
    global active_bot_processes
    while True:
        alive_processes = []
        for p in active_bot_processes:
            if not p.is_alive():
                p.join()
                server_logger.info(f"🧹 Reaped finished bot process {p.pid}")
            else:
                alive_processes.append(p)
        active_bot_processes = alive_processes
        await asyncio.sleep(5)


def spawn_bot_processes(game_id: str, bot_count: int, bot_secret: str, base_genome: dict | None = None):
    if isinstance(base_genome, list):
        genomes = base_genome
    else:
        genomes = seed_genomes(base_genome, bot_count)

    for i in range(bot_count):
        g = genomes[i]
        assigned_genome = g.__dict__ if hasattr(g, "__dict__") else g
        p = multiprocessing.Process(
            target=run_bot_process,
            args=(game_id, bot_secret, training_data_queue, assigned_genome)
        )
        p.start()
        active_bot_processes.append(p)
        server_logger.info(f"Spawned bot {p.pid} for game {game_id}")
