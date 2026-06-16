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
# Global state to keep track of running processes
active_bot_processes = []
training_data_queue = multiprocessing.Queue()

def run_bot_process(game_id: str,
                    bot_secret: str,
                    result_queue: multiprocessing.Queue,
                    assigned_genome_dict: dict | None = None):
    """
    Runs entirely inside a new, isolated memory space.
    """
    fitness_sent = False
    training = False
    
    async def main():
        # INITIALIZE WITH ASSIGNED DNA
        if assigned_genome_dict:
            genome = Genome(**assigned_genome_dict)
        else:
            genome = Genome.random()
            
        bot = GeneticBot(genome)
        host_ready_event = asyncio.Event()
        game_ended = False

        socket = BotSocket(
            game_id=game_id,
            bot_secret=bot_secret,
            http_url=os.environ.get("GAME_SERVER_HTTP_URL", "http://localhost:5000"),
            ws_url=os.environ.get("GAME_SERVER_WS_URL", "ws://localhost:5000/ws")
        )

        async def on_game_state(state):
            nonlocal fitness_sent, game_ended, training
            
            # WAIT FOR HOST FIRST
            if not host_ready_event.is_set():
                if state.get("host_connected") is True:
                    host_ready_event.set()
                else:
                    return  # ⛔ do nothing until host joins

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

            if state.get("status") == "ENDED":
                game_ended = True
                await socket.disconnect()
                return

            if state.get("status") != "RUNNING" or not host_ready_event.is_set():
                return
            
            action = bot.choose_action(state)
            if action:
                await socket.submit_action(action)
                if action["action_command"] == "EMPLOYMENT" and not state.get("training"):
                    await asyncio.sleep(5)
                elif state.get("training"):
                    training = True
                if state.get("phase") == "NIGHT" and action["action_command"] == "CAMPFIRE":
                    await socket.submit_action({
                        "action_command": "FINISH_PHASE",
                        "payload": {}
                    })
            # Auto-finalize accepted trades we haven't finalized yet
            me_actions = me.get("actions", [])
            for a in me_actions:
                try:
                    if a.get("type") == "TRADE" and a.get("status") == "ACCEPTED":
                        is_initiator = a.get("initiator_id") == me.get("id")
                        already_finalized = a.get("initiator_finalized") if is_initiator else a.get("target_finalized")
                        if already_finalized:
                            continue

                        # Determine which items this side should ship
                        promised = a.get("offer_items") if is_initiator else a.get("request_items")
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

                        # Submit finalize even if feasible is empty (server will cap),
                        # but prefer to send something only if feasible non-empty.
                        if feasible:
                            await socket.submit_action({
                                "action_command": "FINALIZE",
                                "payload": {
                                    "action_id": a.get("id"),
                                    "actual_items": feasible
                                }
                            })
                            await asyncio.sleep(0.2)
                except Exception:
                    # Defensive: don't let auto-finalize break the bot loop
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

    asyncio.run(main())


async def process_training_data(queue: multiprocessing.Queue):
    """
    Constantly reads from the IPC queue and saves the bot results.
    """
    while True:
        while not queue.empty():
            result = queue.get()

            # For now, let's append it to a local JSONL file
            with open("bot_training_data.jsonl", "a") as f:
                f.write(json.dumps(result) + "\n")

            print(f"📊 Saved training data! Bot Fitness: {result['fitness']}")

        await asyncio.sleep(0.5)  # Poll more frequently during training


async def reap_zombies():
    """
    Periodically checks for finished processes and calls .join()
    on them to prevent zombie processes from eating up container RAM.
    """
    global active_bot_processes

    while True:
        alive_processes = []
        for p in active_bot_processes:
            if not p.is_alive():
                p.join()  # Crucial: releases OS resources
                print(f"🧹 Reaped finished bot process {p.pid}")
            else:
                alive_processes.append(p)

        active_bot_processes = alive_processes
        await asyncio.sleep(5)  # Check every 5 seconds


def spawn_bot_processes(game_id: str, bot_count: int, bot_secret: str, base_genome: dict | None = None):
    """
    Helper function to abstract the multiprocessing trigger out of the API layer.
    """
    # If the caller provided a full population list, use that directly.
    if isinstance(base_genome, list):
        genomes = base_genome
    else:
        genomes = seed_genomes(base_genome, bot_count)

    for i in range(bot_count):
        # Support both Genome objects and plain dicts
        g = genomes[i]
        assigned_genome = g.__dict__ if hasattr(g, "__dict__") else g
        p = multiprocessing.Process(
            target=run_bot_process,
            args=(game_id, bot_secret, training_data_queue, assigned_genome)
        )
        p.start()
        active_bot_processes.append(p)
        print(f"🚀 Spawned bot {p.pid} for game {game_id}")
