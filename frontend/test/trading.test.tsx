import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  TradeDesk,
  TradeCard,
  ShippingWindow,
  renderItems,
} from "../src/components/gameplay/trading";
import { PlayerProvider } from "../src/components/hooks/usePlayerName";
import type { GameStateDTO, PublicPlayerDTO, TradeActionDTO } from "../src/dtos";

const createMockPlayer = (id: string, name: string): PublicPlayerDTO => ({
  id,
  name,
  health: "healthy",
  fire_status: "HOST",
  fire_guests: [],
  developments: [],
  finished_phase: false,
  phase_state: "ACTIVE",
  visual_state: { animation: "IDLE", location: { kind: "HOME" } },
});

describe("trading components", () => {
  describe("renderItems", () => {
    it("returns 'Nothing' for undefined or empty bundle", () => {
      expect(renderItems(undefined)).toBe("Nothing");
      expect(renderItems({})).toBe("Nothing");
      expect(renderItems({ food: 0, wood: 0 })).toBe("Nothing");
    });

    it("formats positive resource values", () => {
      expect(renderItems({ food: 2, wood: 5 })).toBe("2 food, 5 wood");
    });
  });

  describe("TradeCard", () => {
    const mockTrade: TradeActionDTO = {
      id: "trade-101",
      initiator_id: "player-2",
      target_id: "player-1",
      offer_items: { food: 3 },
      request_items: { wood: 2 },
      status: "PENDING",
      type: "TRADE",
      waiting_on_id: "player-1",
      initiator_finalized: false,
      target_finalized: false,
    };

    const getName = (id: string) => (id === "player-2" ? "Bob" : "Alice");

    it("renders partner name and trade details correctly for recipient", () => {
      render(
        <TradeCard
          trade={mockTrade}
          meId="player-1"
          getPlayerName={getName}
          onAccept={jest.fn()}
          onDeny={jest.fn()}
          onCounterTrade={jest.fn()}
        />,
      );

      expect(screen.getByText("Bob")).toBeDefined();
      expect(screen.getByText("3 food")).toBeDefined();
      expect(screen.getByText("2 wood")).toBeDefined();
    });

    it("triggers onAccept and onDeny callbacks", () => {
      const handleAccept = jest.fn();
      const handleDeny = jest.fn();

      render(
        <TradeCard
          trade={mockTrade}
          meId="player-1"
          getPlayerName={getName}
          onAccept={handleAccept}
          onDeny={handleDeny}
          onCounterTrade={jest.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: "Accept" }));
      expect(handleAccept).toHaveBeenCalledWith("trade-101");

      fireEvent.click(screen.getByRole("button", { name: "Reject" }));
      expect(handleDeny).toHaveBeenCalledWith("trade-101");
    });

    it("supports opening counter offer form and submitting", () => {
      const handleCounter = jest.fn();

      render(
        <TradeCard
          trade={mockTrade}
          meId="player-1"
          getPlayerName={getName}
          onAccept={jest.fn()}
          onDeny={jest.fn()}
          onCounterTrade={handleCounter}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: "Counter" }));
      expect(screen.getByText("Counter Offer")).toBeDefined();

      fireEvent.click(screen.getByRole("button", { name: "Send Counter Offer" }));
      expect(handleCounter).toHaveBeenCalledWith(
        "trade-101",
        expect.any(Object),
        expect.any(Object),
      );
    });
  });

  describe("ShippingWindow", () => {
    const acceptedTrade: TradeActionDTO = {
      id: "trade-accepted-1",
      initiator_id: "player-1",
      target_id: "player-2",
      offer_items: { wood: 2 },
      request_items: { iron: 1 },
      status: "ACCEPTED",
      type: "TRADE",
      waiting_on_id: "",
      initiator_finalized: false,
      target_finalized: false,
    };

    it("allows adjusting payload and finalizing shipment", () => {
      const handleFinalize = jest.fn();
      render(
        <ShippingWindow
          trade={acceptedTrade}
          meId="player-1"
          onFinalizeTrade={handleFinalize}
          getPlayerName={(id) => (id === "player-2" ? "Bob" : "Alice")}
        />,
      );

      expect(screen.getByText(/Bob/)).toBeDefined();
      expect(screen.getByText("Ship Goods")).toBeDefined();

      fireEvent.click(screen.getByRole("button", { name: "Ship Goods" }));
      expect(handleFinalize).toHaveBeenCalledWith("trade-accepted-1", { wood: 2 });
    });

    it("displays waiting status when already shipped", () => {
      const finalizedTrade: TradeActionDTO = {
        ...acceptedTrade,
        initiator_finalized: true,
      };

      render(
        <ShippingWindow
          trade={finalizedTrade}
          meId="player-1"
          onFinalizeTrade={jest.fn()}
          getPlayerName={() => "Bob"}
        />,
      );

      expect(
        screen.getByText(/Waiting for Bob to send their goods/),
      ).toBeDefined();
    });

    it("preserves user adjustments to shipping payload across re-renders with new trade object references", () => {
      const handleFinalize = jest.fn();
      const { rerender } = render(
        <ShippingWindow
          trade={{ ...acceptedTrade, offer_items: { wood: 2 } }}
          meId="player-1"
          onFinalizeTrade={handleFinalize}
          getPlayerName={() => "Bob"}
        />,
      );

      // Decrement wood (second resource: food, wood, iron)
      const minusButtons = screen.getAllByRole("button", { name: "-" });
      fireEvent.click(minusButtons[1]);

      // Re-render with a newly created object (e.g. on timer tick or websocket state update)
      rerender(
        <ShippingWindow
          trade={{ ...acceptedTrade, offer_items: { wood: 2 } }}
          meId="player-1"
          onFinalizeTrade={handleFinalize}
          getPlayerName={() => "Bob"}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: "Ship Goods" }));
      expect(handleFinalize).toHaveBeenCalledWith("trade-accepted-1", { wood: 1 });
    });
  });

  describe("TradeDesk", () => {
    it("renders drafting, outbox, and calls onDraftTrade", () => {
      const player1 = createMockPlayer("p-1", "Alice");
      const player2 = createMockPlayer("p-2", "Bob");
      const players = [player1, player2];

      const outgoingTrade: TradeActionDTO = {
        id: "trade-out-1",
        initiator_id: "p-1",
        target_id: "p-2",
        offer_items: { food: 1 },
        request_items: { wood: 1 },
        status: "PENDING",
        type: "TRADE",
        waiting_on_id: "p-2",
        initiator_finalized: false,
        target_finalized: false,
      };

      const gameState = {
        me: {
          ...player1,
          resources: { food: 5, wood: 5, iron: 5 },
          actions: [outgoingTrade],
          trade_history: [
            {
              id: "hist-1",
              target_id: "p-2",
              offered: { food: 1 },
              requested: { wood: 1 },
              actual_sent: { food: 1 },
              actual_received: { wood: 1 },
            },
          ],
        },
        player_list: players,
        public_interactions: [],
      } as unknown as GameStateDTO;

      const handleDraft = jest.fn();
      const handleCancel = jest.fn();

      render(
        <PlayerProvider players={players}>
          <TradeDesk
            state={gameState}
            onDraftTrade={handleDraft}
            onCounterTrade={jest.fn()}
            onAcceptTrade={jest.fn()}
            onDenyTrade={jest.fn()}
            onCancelTrade={handleCancel}
            onFinalizeTrade={jest.fn()}
          />
        </PlayerProvider>,
      );

      // Verify Trade Desk title
      expect(screen.getByText("Trade Desk")).toBeDefined();

      // Verify Recent Trades
      expect(screen.getByText("Recent Trades")).toBeDefined();
      expect(screen.getByText("With Bob")).toBeDefined();

      // Verify Outbox
      expect(screen.getByText("Awaiting Reply (1)")).toBeDefined();
      expect(screen.getByText("To: Bob")).toBeDefined();

      // Revoke button
      fireEvent.click(screen.getByRole("button", { name: "Revoke" }));
      expect(handleCancel).toHaveBeenCalledWith("trade-out-1");

      // Draft trade with Bob
      fireEvent.click(screen.getByRole("button", { name: "Bob" }));
      expect(screen.getByText("Send Trade Offer")).toBeDefined();
      fireEvent.click(screen.getByRole("button", { name: "Send Trade Offer" }));
      expect(handleDraft).toHaveBeenCalledWith("p-2", expect.any(Object), expect.any(Object));
    });
  });
});
