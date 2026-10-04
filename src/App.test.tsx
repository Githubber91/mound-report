import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "@/App";
import type { DataIndex, PitcherDetail } from "@/lib/data";
import { SCHEMA_VERSION } from "@/lib/data";

const index: DataIndex = {
  schema_version: SCHEMA_VERSION,
  data_version: "2026-10-03",
  season: 2026,
  through: "2026-09-27",
  source: "test",
  pitchers: [
    { id: 694973, name: "Paul Skenes", hand: "R", pitches: 2890, arsenal: ["FF", "ST"] },
    { id: 669373, name: "Tarik Skubal", hand: "L", pitches: 2356, arsenal: ["FF", "CH"] },
  ],
};

const skenes: PitcherDetail = {
  schema_version: SCHEMA_VERSION,
  id: 694973,
  name: "Paul Skenes",
  hand: "R",
  season: 2026,
  pitches: 2890,
  through: "2026-09-27",
  arsenal: [
    {
      code: "FF",
      name: "4-Seam Fastball",
      count: 1180,
      usage_pct: 40.8,
      velocity_mph: 96.8,
      max_velocity_mph: 99.5,
      spin_rpm: 2176,
      horizontal_break_in: -12.6,
      vertical_break_in: 13,
      whiff_pct: 27.1,
    },
  ],
  movement: { FF: [[-12, 13]] },
};

function mockFetch(files: Record<string, unknown>): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const match = Object.keys(files).find((path) => url.endsWith(path));
      return match
        ? new Response(JSON.stringify(files[match]), { status: 200 })
        : new Response("", { status: 404 });
    }),
  );
}

describe("App", () => {
  beforeEach(() => {
    window.location.hash = "";
    mockFetch({ "index.json": index, "pitchers/694973.json": skenes });
  });
  afterEach(() => vi.unstubAllGlobals());

  it("searches pitchers by name", async () => {
    render(<App />);
    const box = await screen.findByRole("searchbox", { name: /find a pitcher/i });
    await userEvent.type(box, "skub");
    const results = screen.getByRole("list", { name: /matching pitchers/i });
    expect(within(results).getByRole("link", { name: /tarik skubal/i })).toHaveAttribute(
      "href",
      "#/pitcher/669373",
    );
    expect(within(results).queryByText(/paul skenes/i)).not.toBeInTheDocument();
  });

  it("shows a pitcher's arsenal, with break from his arm side", async () => {
    window.location.hash = "#/pitcher/694973";
    render(<App />);
    expect(
      await screen.findByRole("heading", { level: 1, name: "Paul Skenes" }),
    ).toBeVisible();
    const row = screen.getByRole("row", { name: /4-seam fastball/i });
    expect(within(row).getByText("96.8")).toBeInTheDocument();
    expect(within(row).getByText("arm")).toBeInTheDocument();
  });

  it("explains when a pitcher isn't found", async () => {
    window.location.hash = "#/pitcher/1";
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/don't have stats/i);
  });

  it("refuses data from a newer, incompatible export", async () => {
    mockFetch({ "index.json": { ...index, schema_version: SCHEMA_VERSION + 1 } });
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/out of date/i);
  });
});
