import { render, screen } from "@testing-library/react";
import TradeDesk from "../src/components/gameplay/trading/TradeDesk";
import { PlayerProvider } from "../src/components/hooks/usePlayerName";
import type { GameStateDTO, PublicPlayerDTO } from "../src/dtos";

const player = (id: string, name: string): PublicPlayerDTO => ({
  id,
  name,
  health: "healthy",
  fire_status: "COLD",
  fire_guests: [],
  developments: [],
  finished_phase: false,
  phase_state: "ACTIVE",
  visual_state: { animation: "IDLE", location: { kind: "HOME" } },
});

describe("public trade activity", () => {
  it("shows third-party participants and status without trade terms", () => {
    const observer = player("player-1", "Ash");
    const initiator = player("player-2", "Bramble");
    const target = player("player-3", "Clover");
    const players = [observer, initiator, target];
    const state = {
      me: {
        ...observer,
        sickness_chance: 0,
        resources: { food: 1, wood: 1, iron: 0 },
        available_work: [],
        committed_action: null,
        actions: [],
        timeline: [],
        trade_history: [],
      },
      player_list: players,
      public_interactions: [{
        id: "trade-1",
        kind: "TRADE",
        participant_ids: ["player-2", "player-3"],
        status: "PENDING",
      }],
    } as unknown as GameStateDTO;

    render(
      <PlayerProvider players={players}>
        <TradeDesk
          state={state}
          onDraftTrade={jest.fn()}
          onCounterTrade={jest.fn()}
          onAcceptTrade={jest.fn()}
          onDenyTrade={jest.fn()}
          onCancelTrade={jest.fn()}
          onFinalizeTrade={jest.fn()}
        />
      </PlayerProvider>,
    );

    expect(screen.getByText("Village Activity")).not.toBeNull();
    expect(screen.getByText("Bramble ↔ Clover")).not.toBeNull();
    expect(screen.getByText("Negotiating")).not.toBeNull();
    expect(screen.queryByText(/food|wood/i)).toBeNull();
  });
});
