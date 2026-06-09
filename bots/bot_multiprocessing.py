import asyncio
import os
import json
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
    
    async def main():
        # INITIALIZE WITH ASSIGNED DNA
        if assigned_genome_dict:
            genome = Genome(**assigned_genome_dict)
        else:
            genome = Genome.random()
            
        bot = GeneticBot(genome)
        host_ready_event = asyncio.Event()

        socket = BotSocket(
            game_id=game_id,
            bot_secret=bot_secret,
            http_url=os.environ.get("GAME_SERVER_HTTP_URL", "http://game-server:8000"),
            ws_url=os.environ.get("GAME_SERVER_WS_URL", "ws://game-server:8000/ws")
        )

        async def on_game_state(state):
            nonlocal fitness_sent
            
            # WAIT FOR HOST FIRST
            if not host_ready_event.is_set():
                if state.get("host_connected") is True:
                    host_ready_event.set()
                else:
                    return  # ⛔ do nothing until host joins

            me = state.get("me", {})
            if me.get("health") == "dead" and not fitness_sent:
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
                await socket.disconnect()
                return

            if state.get("status") != "RUNNING" or not host_ready_event.is_set():
                return
            
            action = bot.choose_action(state)
            if action:
                await socket.submit_action(action)
                if state.get("phase") in ["TRADE", "NIGHT"] and action["action_command"] == "CAMPFIRE":
                    await socket.submit_action({
                        "action_command": "FINISH_PHASE",
                        "payload": {}
                    })

        socket.on_game_state = on_game_state
        success = await socket.connect()

        if success:
            while socket._listen_task and not socket._listen_task.done():
                await asyncio.sleep(1)

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

        await asyncio.sleep(2)  # Don't block the event loop


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
    genomes = seed_genomes(base_genome, bot_count)

    for i in range(bot_count):
        assigned_genome = genomes[i].__dict__
        p = multiprocessing.Process(
            target=run_bot_process,
            args=(game_id, bot_secret, training_data_queue, assigned_genome)
        )
        p.start()
        active_bot_processes.append(p)
        print(f"🚀 Spawned bot {p.pid} for game {game_id}")
