import asyncio
import os
import json
from models.goap_genetic.GOAPGenetic import GOAPGenetic
from models.goap_genetic.goap_genome import GOAPGenome
from models.genetic.Genome import Genome
from models.genetic.GeneticBot import GeneticBot
from models.genetic.fitness import calculate_fitness_report
from botsocket import BotSocket
from training_seeder import seed_genomes
import multiprocessing
from logger import Logger  # <-- Import the Logger

active_bot_processes = []
training_data_queue = multiprocessing.Queue()

# Instantiate a logger for the parent server process
server_logger = Logger("SERVER_MANAGER")

# Extract mapping to a constant so it can be dynamically read by the API
AVAILABLE_BOT_MODELS = {
    "genetic": GeneticBot,
    "GOAPGenetic": GOAPGenetic
}


class ActionSubmissionGate:
    """Suppress duplicate websocket action submissions for unchanged state."""

    def __init__(self):
        self._last_submission_key = None

    def should_submit(self, state: dict, action: dict) -> bool:
        submission_key = (
            self._state_key(state),
            json.dumps(action, sort_keys=True),
        )
        if submission_key == self._last_submission_key:
            return False
        self._last_submission_key = submission_key
        return True

    def _state_key(self, state: dict) -> str:
        me = state.get("me", {})
        observed_contracts = [
            {
                "id": action.get("id"),
                "type": action.get("type"),
                "status": action.get("status"),
                "waiting_on_id": action.get("waiting_on_id"),
                "initiator_finalized": action.get("initiator_finalized"),
                "target_finalized": action.get("target_finalized"),
            }
            for action in me.get("actions", [])
        ]
        fingerprint = {
            "day": state.get("day"),
            "phase": state.get("phase"),
            "status": state.get("status"),
            "bot_id": me.get("id"),
            "finished_phase": me.get("finished_phase", False),
            "health": me.get("health"),
            "resources": me.get("resources", {}),
            "actions": observed_contracts,
        }
        return json.dumps(fingerprint, sort_keys=True)


def get_bot(bot_name: str):
    return AVAILABLE_BOT_MODELS.get(bot_name, GeneticBot)


def get_available_models() -> list[str]:
    return list(AVAILABLE_BOT_MODELS.keys())


def create_genome_for_model(bot_type: str, genome_dict: dict | None = None):
    if bot_type == "GOAPGenetic":
        if genome_dict:
            return GOAPGenome.from_dict(genome_dict)
        return GOAPGenome.random()
    if genome_dict:
        return Genome(**genome_dict)
    return Genome.random()


def seed_genomes_for_model(bot_type: str,
                           base_genome: dict | list | None,
                           bot_count: int) -> list:
    if isinstance(base_genome, list):
        return [create_genome_for_model(bot_type, genome) for genome in base_genome]

    if bot_type != "GOAPGenetic":
        return seed_genomes(base_genome, bot_count)

    if not base_genome:
        return [GOAPGenome.random() for _ in range(bot_count)]

    parent = GOAPGenome.from_dict(base_genome)
    genomes = [parent]
    for _ in range(bot_count - 1):
        genomes.append(GOAPGenome.mutate(parent))
    return genomes


def run_bot_process(game_id: str,
                    bot_secret: str,
                    result_queue: multiprocessing.Queue,
                    bot_type: str,
                    assigned_genome_dict: dict | None = None):

    # Instantiate a unique logger for this specific child process using its PID
    bot_logger = Logger(f"Worker_{os.getpid()}", game_id=game_id)
    bot_logger.info(f"Sarting isolated process for game {game_id}")

    fitness_sent = False
    training = False

    async def main():
        genome = create_genome_for_model(bot_type, assigned_genome_dict)

        bot = get_bot(bot_type)(genome)
        # Pass the logger to the bot so it can log logic decisions (optional)
        bot.logger = bot_logger

        bot.logger.info(
            f"loaded genome: {json.dumps(genome.__dict__, indent=2)}"
        )

        host_ready_event = asyncio.Event()
        game_ended = False
        submission_gate = ActionSubmissionGate()

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

            nonlocal fitness_sent, game_ended, training

            if not host_ready_event.is_set():
                if state.get("host_connected") is True:
                    bot_logger.info("Host joined. Activating bot logic.")
                    host_ready_event.set()
                else:
                    return

            me = state.get("me", {})
            if (me.get("health") == "dead" and not fitness_sent) or (state.get("status") == "ENDED" and not fitness_sent):
                fitness_report = calculate_fitness_report(state)
                fitness_score = fitness_report.score

                result_queue.put({
                    "game_id": game_id,
                    "Day": state.get("day"),
                    "bot_id": me.get("id"),
                    "fitness": fitness_score,
                    "fitness_components": fitness_report.components,
                    "stats": fitness_report.stats,
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
                if action and submission_gate.should_submit(state, action):
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
            except Exception as e:
                bot_logger.stdout_error(
                    "Failed to process game logic", exception=e)

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


def spawn_bot_processes(game_id: str, bot_count: int,
                        bot_secret: str,
                        bot_model: str = "genetic",
                        base_genome: dict | None = None):
    genomes = seed_genomes_for_model(bot_model, base_genome, bot_count)

    for i in range(bot_count):
        g = genomes[i]
        assigned_genome = g.__dict__ if hasattr(g, "__dict__") else g
        p = multiprocessing.Process(
            target=run_bot_process,
            args=(game_id, bot_secret,
                  training_data_queue,
                  bot_model,
                  assigned_genome)
        )
        p.start()
        active_bot_processes.append(p)
        server_logger.info(f"Spawned bot {p.pid} for game {game_id}")
