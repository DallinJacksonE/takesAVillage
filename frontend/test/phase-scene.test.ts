import { getPhaseScene } from "../src/components/gameplay/phaseScene";

describe("getPhaseScene", () => {
  it("replaces the axial map with a forest clearing during trade", () => {
    expect(getPhaseScene("TRADE")).toEqual({
      label: "Trade clearing",
      showAxialMap: false,
      theme: "trade",
    });
  });

  it("keeps the authoritative axial village visible during work", () => {
    expect(getPhaseScene("WORK")).toEqual({
      label: "Village work map",
      showAxialMap: true,
      theme: "work",
    });
  });

  it("uses the dark clearing without axial tiles during night", () => {
    expect(getPhaseScene("NIGHT")).toEqual({
      label: "Night clearing",
      showAxialMap: false,
      theme: "night",
    });
  });
});