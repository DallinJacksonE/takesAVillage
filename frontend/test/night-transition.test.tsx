import { act, render } from "@testing-library/react";
import NightTransitionAcknowledger from "../src/components/gameplay/NightTransitionAcknowledger";
import type { GameStateDTO } from "../src/dtos";

describe("NightTransitionAcknowledger", () => {
  it("acknowledges an affected local player after the one-shot sprite duration", () => {
    jest.useFakeTimers();
    const onComplete = jest.fn();
    const state = {
      me: { id: "player-1" },
      player_list: [{
        id: "player-1",
        visual_state: { animation: "HURT", location: { kind: "NIGHT_COLD", slot: 0 } },
      }],
      night_transition: {
        id: "night-1",
        deadline: 105,
        affected_player_ids: ["player-1"],
      },
    } as GameStateDTO;

    render(<NightTransitionAcknowledger state={state} onComplete={onComplete} />);
    act(() => jest.advanceTimersByTime(1800));

    expect(onComplete).toHaveBeenCalledWith("night-1");
    jest.useRealTimers();
  });

  it("does not acknowledge transitions belonging to another player", () => {
    jest.useFakeTimers();
    const onComplete = jest.fn();
    const state = {
      me: { id: "player-1" },
      player_list: [],
      night_transition: {
        id: "night-1",
        deadline: 105,
        affected_player_ids: ["player-2"],
      },
    } as unknown as GameStateDTO;

    render(<NightTransitionAcknowledger state={state} onComplete={onComplete} />);
    act(() => jest.runAllTimers());

    expect(onComplete).not.toHaveBeenCalled();
    jest.useRealTimers();
  });
});