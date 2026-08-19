import { getTimerSeverity } from "../src/components/gameplay/layout/timerPresentation";

describe("getTimerSeverity", () => {
  it.each([
    [31, "normal"],
    [30, "warning"],
    [15, "warning"],
    [14, "critical"],
    [0, "critical"],
  ])("maps %i seconds to %s", (seconds, expected) => {
    expect(getTimerSeverity(seconds)).toBe(expected);
  });
});
