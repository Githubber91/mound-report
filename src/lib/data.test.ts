import { describe, expect, it } from "vitest";
import type { PitcherSummary } from "@/lib/data";
import { armSideBreak, normalise, searchPitchers } from "@/lib/data";

const pitcher = (id: number, name: string, pitches: number): PitcherSummary => ({
  id,
  name,
  hand: "R",
  pitches,
  arsenal: ["FF"],
});

const pitchers = [
  pitcher(1, "Paul Skenes", 2890),
  pitcher(2, "Tarik Skubal", 2356),
  pitcher(3, "Cristopher Sánchez", 3158),
  pitcher(4, "Aaron Sanchez", 400),
  pitcher(5, "Skye Bolt", 120),
];

describe("normalise", () => {
  it("ignores accents and case", () => {
    expect(normalise("  Sánchez ")).toBe("sanchez");
  });
});

describe("searchPitchers", () => {
  it("finds names without typing accents", () => {
    expect(searchPitchers(pitchers, "sanchez").map((p) => p.id)).toEqual([3, 4]);
  });

  it("puts first-name matches first, then surnames, then the rest", () => {
    // "Skye" starts with "sk"; Skenes and Skubal are surname matches, busiest first.
    expect(searchPitchers(pitchers, "sk").map((p) => p.id)).toEqual([5, 1, 2]);
  });

  it("needs every word to match", () => {
    expect(searchPitchers(pitchers, "paul sk").map((p) => p.id)).toEqual([1]);
    expect(searchPitchers(pitchers, "paul skubal")).toEqual([]);
  });

  it("returns nothing for an empty query", () => {
    expect(searchPitchers(pitchers, "   ")).toEqual([]);
  });
});

describe("armSideBreak", () => {
  it("flips the catcher's view for right-handers only", () => {
    expect(armSideBreak(-12.6, "R")).toBe(12.6);
    expect(armSideBreak(12.6, "L")).toBe(12.6);
  });
});
