import { describe, expect, it, vi } from "vitest";

import { gameStateSchema } from "@takes-a-village/shared";
import { Game } from "../../src/game/game.js";

describe("TypeScript game domain", () => {
  function makeGame(ruleset = "default") {
    const game = new Game("g_test", "player-1", ruleset, 0, false, () => 100);
    game.addPlayer("player-1");
    game.addPlayer("player-2");
    return game;
  }

  it("starts in work phase with a generated, serializable map", () => {
    const game = makeGame();
    expect(game.startGame()).toBe(true);
    expect(game.startGame()).toBe(false);
    expect(game.status).toBe("RUNNING");
    expect(game.phase).toBe("WORK");
    expect(game.day).toBe(1);
    expect(Object.keys(game.mapData).length).toBeGreaterThan(0);
    expect(gameStateSchema.parse(game.getStateForPlayer("player-1"))).toBeTruthy();
  });

  it("builds a development, spends only its sparse cost, and finishes work", () => {
    const game = makeGame();
    game.startGame();
    const player = game.players.get("player-1")!;
    const tile = Object.values(game.mapData).find((candidate) => candidate.type === "Farm")!;
    const starting = { ...player.resources };

    expect(game.handleAction("player-1", { action_command: "BUILD_DEV", payload: { tile_id: tile.id } })).toBe(true);
    expect(player.resources).toEqual({ ...starting, wood: starting.wood - 2 });
    expect(player.developments).toHaveLength(1);
    expect(game.mapData[tile.id]?.development?.owner_id).toBe(player.id);
    expect(player.finishedPhase).toBe(true);
    expect(game.handleAction("player-1", { action_command: "BUILD_DEV", payload: { tile_id: tile.id } })).toBe(false);
  });

  it("advances WORK, TRADE, NIGHT and consumes food at day rollover", () => {
    const game = makeGame();
    game.startGame();
    for (const player of game.players.values()) {
      player.resources.food = 5;
      player.fireStatus = "HOST";
    }

    game.nextPhase();
    expect(game.phase).toBe("TRADE");
    game.nextPhase();
    expect(game.phase).toBe("NIGHT");
    game.nextPhase();
    expect(game.phase).toBe("WORK");
    expect(game.day).toBe(2);
    for (const player of game.players.values()) expect(player.resources.food).toBe(4);
  });

  it("starts a fire only at night and ends the game after the final night", () => {
    const game = makeGame();
    game.startGame();
    const player = game.players.get("player-1")!;
    expect(game.handleAction(player.id, { action_command: "START_FIRE", payload: {} })).toBe(false);
    game.phase = "NIGHT";
    const startingWood = player.resources.wood;
    expect(game.handleAction(player.id, { action_command: "START_FIRE", payload: {} })).toBe(true);
    expect(player.fireStatus).toBe("HOST");
    expect(player.resources.wood).toBe(startingWood - 1);

    game.day = game.gameLength;
    game.nextPhase();
    expect(game.status).toBe("ENDED");
    expect(game.phase).toBe("NIGHT");
  });

  it("finishing all living players advances while ignoring dead players", () => {
    const game = makeGame();
    game.startGame();
    game.players.get("player-2")!.health = "dead";
    expect(game.handleAction("player-1", { action_command: "FINISH_PHASE", payload: {} })).toBe(true);
    expect(game.phase).toBe("TRADE");
  });

  it("drafts, accepts, finalizes, and executes a trade", () => {
    const game = makeGame();
    game.startGame();
    game.phase = "TRADE";
    const first = game.players.get("player-1")!;
    const second = game.players.get("player-2")!;
    first.resources.food = 3;
    first.resources.wood = 0;
    second.resources.food = 0;
    second.resources.wood = 2;

    expect(game.handleAction(first.id, {
      action_command: "TRADE",
      payload: {
        type: "TRADE",
        target_id: second.id,
        offer_items: { food: 2 },
        request_items: { wood: 1 },
      },
    })).toBe(true);

    const trade = first.actions[0];
    expect(trade).toMatchObject({ type: "TRADE", status: "PENDING", waiting_on_id: second.id });
    expect(second.actions[0]?.id).toBe(trade?.id);
    expect(game.handleAction(second.id, {
      action_command: "ACCEPT",
      payload: { action_id: trade?.id },
    })).toBe(true);
    expect(first.actions[0]).toMatchObject({ status: "ACCEPTED", waiting_on_id: null });

    expect(game.handleAction(first.id, {
      action_command: "FINALIZE",
      payload: { action_id: trade?.id, actual_items: { food: 2 } },
    })).toBe(true);
    expect(game.handleAction(second.id, {
      action_command: "FINALIZE",
      payload: { action_id: trade?.id, actual_items: { wood: 1 } },
    })).toBe(true);

    expect(first.resources).toEqual({ food: 1, wood: 1, iron: 1 });
    expect(second.resources).toEqual({ food: 2, wood: 1, iron: 1 });
    expect(first.tradeHistory[0]).toMatchObject({ actual_sent: { food: 2 }, actual_received: { wood: 1 } });
    expect(second.tradeHistory[0]).toMatchObject({ actual_sent: { wood: 1 }, actual_received: { food: 2 } });
  });

  it("caps finalized trade items to the available inventory", () => {
    const game = makeGame();
    const first = game.players.get("player-1")!;
    const second = game.players.get("player-2")!;
    first.resources.food = 1;
    second.resources.food = 0;

    expect(game.handleAction(first.id, {
      action_command: "TRADE",
      payload: { type: "TRADE", target_id: second.id, offer_items: { food: 5 }, request_items: {} },
    })).toBe(true);
    const tradeId = first.actions[0]?.id;
    expect(game.handleAction(second.id, { action_command: "ACCEPT", payload: { action_id: tradeId } })).toBe(true);
    expect(game.handleAction(first.id, {
      action_command: "FINALIZE",
      payload: { action_id: tradeId, actual_items: { food: 5 } },
    })).toBe(true);
    expect(game.handleAction(second.id, {
      action_command: "FINALIZE",
      payload: { action_id: tradeId, actual_items: {} },
    })).toBe(true);

    expect(first.resources.food).toBe(0);
    expect(second.resources.food).toBe(1);
    expect(first.tradeHistory[0]?.actual_sent).toEqual({ food: 1 });
  });

  it("rejects negative finalized trade items without mutating inventory", () => {
    const game = makeGame();
    const first = game.players.get("player-1")!;
    const second = game.players.get("player-2")!;
    const beforeFirst = { ...first.resources };
    const beforeSecond = { ...second.resources };

    expect(game.handleAction(first.id, {
      action_command: "TRADE",
      payload: { type: "TRADE", target_id: second.id, offer_items: { food: 1 }, request_items: {} },
    })).toBe(true);
    const tradeId = first.actions[0]?.id;
    expect(game.handleAction(second.id, { action_command: "ACCEPT", payload: { action_id: tradeId } })).toBe(true);
    expect(game.handleAction(first.id, {
      action_command: "FINALIZE",
      payload: { action_id: tradeId, actual_items: { food: -2 } },
    })).toBe(false);

    expect(first.resources).toEqual(beforeFirst);
    expect(second.resources).toEqual(beforeSecond);
    expect(first.tradeHistory).toEqual([]);
    expect(second.tradeHistory).toEqual([]);
  });

  it("allows the waiting player to barter and the initiator to cancel", () => {
    const game = makeGame();
    const first = game.players.get("player-1")!;
    const second = game.players.get("player-2")!;
    expect(game.handleAction(first.id, {
      action_command: "TRADE",
      payload: { type: "TRADE", target_id: second.id, offer_items: { food: 1 }, request_items: { wood: 1 } },
    })).toBe(true);
    const tradeId = first.actions[0]?.id;

    expect(game.handleAction(second.id, {
      action_command: "BARTER",
      payload: { action_id: tradeId, offer_items: { food: 2 }, request_items: {} },
    })).toBe(true);
    expect(first.actions[0]).toMatchObject({
      status: "PENDING",
      waiting_on_id: first.id,
      offer_items: { food: 2 },
      request_items: {},
    });
    expect(game.handleAction(first.id, {
      action_command: "CANCEL",
      payload: { action_id: tradeId },
    })).toBe(true);
    expect(first.actions[0]).toMatchObject({ status: "CANCELED", waiting_on_id: null });
  });

  it("allows the waiting player to deny a trade", () => {
    const game = makeGame();
    const first = game.players.get("player-1")!;
    const second = game.players.get("player-2")!;
    expect(game.handleAction(first.id, {
      action_command: "TRADE",
      payload: { type: "TRADE", target_id: second.id, offer_items: { food: 1 }, request_items: {} },
    })).toBe(true);
    const tradeId = first.actions[0]?.id;

    expect(game.handleAction(second.id, {
      action_command: "DENY",
      payload: { action_id: tradeId },
    })).toBe(true);
    expect(first.actions[0]).toMatchObject({ status: "DENIED", waiting_on_id: null });
  });

  it("accepts an employment offer for a development owned by the employer", () => {
    const game = makeGame();
    game.startGame();
    const employer = game.players.get("player-1")!;
    const worker = game.players.get("player-2")!;
    const tile = Object.values(game.mapData).find((candidate) => candidate.type === "Farm")!;
    expect(game.handleAction(employer.id, {
      action_command: "BUILD_DEV",
      payload: { tile_id: tile.id },
    })).toBe(true);
    employer.finishedPhase = false;
    const developmentId = employer.developments[0]!;

    expect(game.handleAction(employer.id, {
      action_command: "EMPLOYMENT",
      payload: {
        type: "EMPLOYMENT",
        target_id: worker.id,
        dev_id: developmentId,
        wage: 2,
        wage_type: "food",
        is_application: false,
      },
    })).toBe(true);
    const contract = employer.actions.find((action) => action.type === "EMPLOYMENT");
    expect(contract).toMatchObject({ status: "PENDING", waiting_on_id: worker.id });
    expect(worker.actions.find((action) => action.id === contract?.id)).toBe(contract);

    expect(game.handleAction(worker.id, {
      action_command: "ACCEPT",
      payload: { action_id: contract?.id, type: "EMPLOYMENT" },
    })).toBe(true);
    expect(contract).toMatchObject({ status: "ACCEPTED", waiting_on_id: null });
    expect(worker.availableWork[0]).toMatchObject({
      development: { id: developmentId },
      wage: 2,
      wage_type: "food",
      employer_id: employer.id,
      action_id: contract?.id,
    });
  });

  it("commits accepted work and gives its production to the development owner", () => {
    const game = makeGame();
    game.startGame();
    const employer = game.players.get("player-1")!;
    const worker = game.players.get("player-2")!;
    const tile = Object.values(game.mapData).find((candidate) => candidate.type === "Farm")!;
    expect(game.handleAction(employer.id, { action_command: "BUILD_DEV", payload: { tile_id: tile.id } })).toBe(true);
    employer.finishedPhase = false;
    const developmentId = employer.developments[0]!;
    expect(game.handleAction(employer.id, {
      action_command: "EMPLOYMENT",
      payload: {
        type: "EMPLOYMENT",
        target_id: worker.id,
        dev_id: developmentId,
        wage: 2,
        wage_type: "food",
        is_application: false,
      },
    })).toBe(true);
    const contract = employer.actions.find((action) => action.type === "EMPLOYMENT")!;
    expect(game.handleAction(worker.id, {
      action_command: "ACCEPT",
      payload: { action_id: contract.id, type: "EMPLOYMENT" },
    })).toBe(true);
    const job = worker.availableWork[0]!;
    const employerFood = employer.resources.food;
    const workerFood = worker.resources.food;

    expect(game.handleAction(worker.id, {
      action_command: "COMMIT_WORK",
      payload: { job },
    })).toBe(true);
    expect(worker.committedAction).toEqual(job);
    expect(contract).toMatchObject({ status: "COMPLETED" });
    expect(worker.finishedPhase).toBe(true);
    expect(game.handleAction(employer.id, { action_command: "FINISH_PHASE", payload: {} })).toBe(true);

    expect(game.phase).toBe("TRADE");
    expect(employer.resources.food).toBe(employerFood + 2);
    expect(worker.resources.food).toBe(workerFood);
    expect(worker.committedAction).toBeNull();
    expect(employer.actions.some((action) => action.type === "EMPLOYMENT")).toBe(false);
    expect(worker.actions.some((action) => action.type === "EMPLOYMENT")).toBe(false);
  });

  it("accepts a campfire offer and seats the guest exactly once", () => {
    const game = makeGame();
    game.startGame();
    game.phase = "NIGHT";
    const host = game.players.get("player-1")!;
    const guest = game.players.get("player-2")!;
    expect(game.handleAction(host.id, { action_command: "START_FIRE", payload: {} })).toBe(true);

    expect(game.handleAction(host.id, {
      action_command: "CAMPFIRE",
      payload: { type: "CAMPFIRE", target_id: guest.id, is_request: false },
    })).toBe(true);
    const contract = host.actions.find((action) => action.type === "CAMPFIRE")!;
    expect(contract).toMatchObject({ status: "PENDING", waiting_on_id: guest.id, is_request: false });
    expect(game.handleAction(guest.id, {
      action_command: "ACCEPT",
      payload: { action_id: contract.id },
    })).toBe(true);

    expect(contract).toMatchObject({ status: "ACCEPTED", waiting_on_id: null });
    expect(host.fireGuests).toEqual([guest.id]);
    expect(guest.fireStatus).toBe("GUEST");
    expect(host.fireHistory[0]).toMatchObject({ role: "host", guests: [guest.id] });
    expect(guest.fireHistory[0]).toMatchObject({ role: "guest", guests: [guest.id] });
    expect(game.handleAction(guest.id, {
      action_command: "ACCEPT",
      payload: { action_id: contract.id },
    })).toBe(false);
    expect(host.fireGuests).toEqual([guest.id]);
    game.nextPhase();
    expect(host.actions.some((action) => action.type === "CAMPFIRE")).toBe(false);
    expect(guest.actions.some((action) => action.type === "CAMPFIRE")).toBe(false);
  });

  it("maintains an owned development for its dynamic resource cost", () => {
    const game = makeGame();
    game.startGame();
    const owner = game.players.get("player-1")!;
    const tile = Object.values(game.mapData).find((candidate) => candidate.type === "Farm")!;
    expect(game.handleAction(owner.id, { action_command: "BUILD_DEV", payload: { tile_id: tile.id } })).toBe(true);
    owner.finishedPhase = false;
    const development = game.developments.get(owner.developments[0]!)!;
    development.maintenance_days = 1;
    const before = { ...owner.resources };

    expect(game.handleAction(owner.id, {
      action_command: "MAINTAIN_DEV",
      payload: { dev_id: development.id },
    })).toBe(true);

    expect(development.maintenance_days).toBe(game.rules.MAINTENANCE_DAYS);
    expect(owner.resources).toEqual({
      ...before,
      wood: before.wood - 2,
      iron: before.iron - 1,
    });
    expect(owner.finishedPhase).toBe(true);
  });

  it("upgrades an owned development and refreshes its dynamic costs", () => {
    const game = makeGame();
    game.startGame();
    const owner = game.players.get("player-1")!;
    const tile = Object.values(game.mapData).find((candidate) => candidate.type === "Farm")!;
    expect(game.handleAction(owner.id, { action_command: "BUILD_DEV", payload: { tile_id: tile.id } })).toBe(true);
    owner.finishedPhase = false;
    owner.resources.wood = 20;
    owner.resources.food = 20;
    owner.resources.iron = 20;
    const development = game.developments.get(owner.developments[0]!)!;

    expect(game.handleAction(owner.id, {
      action_command: "UPGRADE_DEV",
      payload: { dev_id: development.id },
    })).toBe(true);

    expect(development.level).toBe(3);
    expect(development.can_upgrade).toBe(false);
    expect(development.maintenance_days).toBe(game.rules.MAINTENANCE_DAYS);
    expect(development.maintenance_cost).toEqual({ wood: 3, iron: 2 });
    expect(development.upgrade_cost).toEqual({ wood: 7, iron: 3 });
    expect(owner.resources).toEqual({ wood: 15, food: 20, iron: 18 });
    expect(owner.finishedPhase).toBe(true);
  });

  it("degrades an unmaintained development after night", () => {
    const game = makeGame();
    game.startGame();
    const owner = game.players.get("player-1")!;
    const tile = Object.values(game.mapData).find((candidate) => candidate.type === "Farm")!;
    expect(game.handleAction(owner.id, { action_command: "BUILD_DEV", payload: { tile_id: tile.id } })).toBe(true);
    const development = game.developments.get(owner.developments[0]!)!;
    development.maintenance_days = 0;
    game.phase = "NIGHT";

    game.nextPhase();

    expect(game.phase).toBe("WORK");
    expect(development.level).toBe(1);
    expect(development.maintenance_days).toBe(game.rules.MAINTENANCE_DAYS - 1);
    expect(development.maintenance_cost).toEqual({ wood: 1, iron: 0 });
    expect(development.upgrade_cost).toEqual({ wood: 3, iron: 1 });
    expect(development.can_upgrade).toBe(true);
  });

  it("schedules a development contest and activates it on the next work day", () => {
    const game = makeGame();
    game.startGame();
    const owner = game.players.get("player-1")!;
    const attacker = game.players.get("player-2")!;
    const tile = Object.values(game.mapData).find((candidate) => candidate.type === "Farm")!;
    expect(game.handleAction(owner.id, { action_command: "BUILD_DEV", payload: { tile_id: tile.id } })).toBe(true);
    const development = game.developments.get(owner.developments[0]!)!;

    expect(game.handleAction(attacker.id, {
      action_command: "CONTEST_DEV",
      payload: { dev_id: development.id, side: "INITIATOR" },
    })).toBe(true);
    expect(development.pending_contest).toBe(true);
    expect(development.is_contested).toBe(false);
    expect(development.contest_initiator_id).toBe(attacker.id);
    expect(attacker.timeline.at(-1)).toEqual({
      type: "ACTION_COMPLETED",
      data: { action: "CONTEST_SCHEDULED", dev_id: development.id },
    });

    expect(game.phase).toBe("TRADE");
    game.nextPhase();
    game.nextPhase();

    expect(game.day).toBe(2);
    expect(game.phase).toBe("WORK");
    expect(development.pending_contest).toBe(false);
    expect(development.is_contested).toBe(true);
    expect(owner.timeline.at(-1)).toEqual({
      type: "CONTEST_STARTED",
      data: { dev_id: development.id, attacker: attacker.id },
    });
  });

  it("transfers a contested development when the attacker participates and the owner does not", () => {
    const game = makeGame();
    game.startGame();
    const owner = game.players.get("player-1")!;
    const attacker = game.players.get("player-2")!;
    const tile = Object.values(game.mapData).find((candidate) => candidate.type === "Farm")!;
    expect(game.handleAction(owner.id, { action_command: "BUILD_DEV", payload: { tile_id: tile.id } })).toBe(true);
    owner.finishedPhase = false;
    const development = game.developments.get(owner.developments[0]!)!;
    development.is_contested = true;
    development.contest_initiator_id = attacker.id;

    expect(game.handleAction(attacker.id, {
      action_command: "CONTEST_DEV",
      payload: { dev_id: development.id, side: "CONTESTER" },
    })).toBe(true);
    expect(attacker.committedAction).toEqual({
      type: "CONTEST_ACTION",
      dev_id: development.id,
      side: "CONTESTER",
    });
    expect(gameStateSchema.parse(game.getStateForPlayer(attacker.id))).toBeTruthy();
    expect(attacker.finishedPhase).toBe(true);
    expect(game.handleAction(attacker.id, {
      action_command: "CONTEST_DEV",
      payload: { dev_id: development.id, side: "CONTESTER" },
    })).toBe(false);
    expect(development.contester_supporters).toEqual([attacker.id]);
    expect(game.handleAction(owner.id, { action_command: "FINISH_PHASE", payload: {} })).toBe(true);

    expect(game.phase).toBe("TRADE");
    expect(development.owner_id).toBe(attacker.id);
    expect(development.is_contested).toBe(false);
    expect(development.contest_initiator_id).toBeNull();
    expect(owner.developments).not.toContain(development.id);
    expect(attacker.developments).toContain(development.id);
    expect(attacker.committedAction).toBeNull();
  });

  it("rejects group-chat messages from non-members", () => {
    const game = makeGame();
    const outsider = game.addPlayer("player-3");
    expect(game.createChat("player-1", "private", ["player-1", "player-2"])).toBe(true);
    const chat = game.chats[0]!;

    expect(game.handleChat(outsider.id, "secret", chat.id)).toBeNull();
    expect(game.chatMessages).toEqual([]);
  });

  it("rejects chat creation when any requested member is unknown", () => {
    const game = makeGame();

    expect(game.createChat("player-1", "invalid", ["player-2", "missing-player"])).toBe(false);
    expect(game.chats).toEqual([]);
  });

  it("raises sickness risk for hunger and cold before applying the nightly health roll", () => {
    const game = makeGame();
    game.startGame();
    const player = game.players.get("player-1")!;
    player.resources.food = 0;
    game.phase = "NIGHT";
    const random = vi.spyOn(Math, "random").mockReturnValue(0);

    game.nextPhase();

    random.mockRestore();
    expect(player.health).toBe("sick");
    expect(player.sicknessChance).toBeCloseTo(
      game.rules.DEFAULT_SICKNESS
        + game.rules.HUNGER_SICKNESS_INCREASE
        + game.rules.COLD_SICKNESS_INCREASE,
    );
    expect(player.fireStatus).toBe("COLD");
    expect(player.availableWork).toEqual([]);
  });

  it("moves a fed and warm sick player through recovery to healthy", () => {
    const game = makeGame();
    game.startGame();
    const player = game.players.get("player-1")!;
    player.health = "sick";
    player.sicknessChance = 0.5;
    player.resources.food = 2;
    player.fireStatus = "HOST";
    game.phase = "NIGHT";
    const random = vi.spyOn(Math, "random").mockReturnValue(0.99);

    game.nextPhase();

    expect(player.health).toBe("recovering");
    expect(player.sicknessChance).toBeCloseTo(0.43);
    player.fireStatus = "HOST";
    game.phase = "NIGHT";
    game.nextPhase();

    random.mockRestore();
    expect(player.health).toBe("healthy");
    expect(player.sicknessChance).toBe(game.rules.DEFAULT_SICKNESS);
    expect(player.resources.food).toBe(0);
  });
});
