import random
from Bots.Genome import Genome
from Bots.GeneticBot import GeneticBot
from service.actions.action_dispatcher import ActionDispatcher


def calculate_fitness(player, game):

    fitness = 0

    # survival
    fitness += game.day * 200

    # resources
    fitness += sum(
        player.resources.values()
    ) * 25

    fitness += 100 * sum(
        game.developments[dev_id].level
        for dev_id in player.developments
    )

    if player.health == "dead":
        fitness -= 2000

    return fitness


def create_training_game(genomes):

    game = Game(
        game_id="training",
        host_id="trainer",
        training=True
    )

    bots = []

    for i, genome in enumerate(genomes):

        player_id = f"bot_{i}"

        game.add_player(player_id)

        bots.append(
            GeneticBot(genome)
        )

    game.start_game()

    return game, bots


# =========================
# Game Simulation
# =========================

def run_game(genomes):

    game, bots = create_training_game(genomes)

    while game.status != "ENDED":

        if game.phase == "WORK":

            for bot, player in zip(
                bots,
                game.players.values()
            ):

                if player.health == "dead":
                    continue

                action = bot.choose_action(game, player)

                if not action:
                    player.finished_phase = True
                    continue

                if action.get("action_type") == "BUILD":

                    ActionDispatcher.dispatch(
                        game,
                        player.session_id,
                        {
                            "action_command": "BUILD_DEV",
                            "payload": {
                                "tile_id": action["tile_id"]
                            }
                        }
                    )

                else:

                    ActionDispatcher.dispatch(
                        game,
                        player.session_id,
                        {
                            "action_command": "COMMIT_WORK",
                            "payload": {
                                "job": action
                            }
                        }
                    )

                player.finished_phase = True

        game.next_phase()

        if game.day > game.game_length:
            game.status = "ENDED"

    return [
        calculate_fitness(player, game)
        for player in game.players.values()
    ]

# =========================
# Evolution
# =========================


POP_SIZE = 200
LOBBY_SIZE = 10

SURVIVORS = 40
ELITES = 5

GENERATIONS = 100


population = [
    Genome.random()
    for _ in range(POP_SIZE)
]

for generation in range(GENERATIONS):

    random.shuffle(population)

    lobbies = [
        population[i:i + LOBBY_SIZE]
        for i in range(0, len(population), LOBBY_SIZE)
    ]

    results = []

    for lobby in lobbies:

        if len(lobby) < LOBBY_SIZE:
            continue
        fitnesses = run_game(lobby)

        for genome, fitness in zip(
            lobby,
            fitnesses
        ):
            results.append(
                (fitness, genome)
            )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    best_fitness = results[0][0]
    avg_fitness = (
        sum(f for f, _ in results)
        / len(results)
    )

    print(
        f"Generation {generation:03d} | "
        f"Best={best_fitness:.2f} | "
        f"Average={avg_fitness:.2f}"
    )

    parents = [
        genome
        for _, genome in results[:SURVIVORS]
    ]

    new_population = parents[:ELITES]

    while len(new_population) < POP_SIZE:

        parent_a = random.choice(parents)
        parent_b = random.choice(parents)

        child = Genome.crossover(
            parent_a,
            parent_b
        )

        child = Genome.mutate(child)

        new_population.append(child)

    population = new_population

print("Training complete.")
