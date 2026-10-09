import { describe, it, expect } from "vitest";
import { parseDay, computeFreeSlots } from "../src/lib/availability.js";

function dayBounds(date: string) {
  const parsed = parseDay(date);
  if (!parsed.ok) throw new Error(`date de test invalide : ${date}`);
  return parsed.value;
}

describe("parseDay", () => {
  it("convertit une date en bornes UTC de la journee", () => {
    expect(parseDay("2026-10-05")).toEqual({
      ok: true,
      value: {
        start: Date.parse("2026-10-05T00:00:00Z"),
        end: Date.parse("2026-10-06T00:00:00Z")
      }
    });
  });

  it("gere le passage a l'annee suivante", () => {
    const parsed = parseDay("2026-12-31");
    expect(parsed.ok).toBe(true);
    if (parsed.ok) {
      expect(new Date(parsed.value.end).toISOString().slice(0, 10)).toBe("2027-01-01");
    }
  });

  it("refuse un format non ISO", () => {
    expect(parseDay("05/10/2026").ok).toBe(false);
  });

  it("refuse une date calendaire inexistante", () => {
    expect(parseDay("2026-02-30").ok).toBe(false);
  });
});

describe("computeFreeSlots", () => {
  const { start, end } = dayBounds("2026-10-05");

  it("rend la journee entiere quand rien n'est reserve", () => {
    expect(computeFreeSlots(start, end, [])).toEqual([
      { startsAt: "2026-10-05T00:00:00Z", endsAt: "2026-10-06T00:00:00Z" }
    ]);
  });

  it("coupe la journee autour d'une reservation", () => {
    expect(
      computeFreeSlots(start, end, [
        { startsAt: "2026-10-05T09:00:00Z", endsAt: "2026-10-05T11:00:00Z" }
      ])
    ).toEqual([
      { startsAt: "2026-10-05T00:00:00Z", endsAt: "2026-10-05T09:00:00Z" },
      { startsAt: "2026-10-05T11:00:00Z", endsAt: "2026-10-06T00:00:00Z" }
    ]);
  });

  it("fusionne deux reservations mitoyennes sans creer de trou", () => {
    expect(
      computeFreeSlots(start, end, [
        { startsAt: "2026-10-05T09:00:00Z", endsAt: "2026-10-05T10:00:00Z" },
        { startsAt: "2026-10-05T10:00:00Z", endsAt: "2026-10-05T11:00:00Z" }
      ])
    ).toEqual([
      { startsAt: "2026-10-05T00:00:00Z", endsAt: "2026-10-05T09:00:00Z" },
      { startsAt: "2026-10-05T11:00:00Z", endsAt: "2026-10-06T00:00:00Z" }
    ]);
  });

  it("fusionne deux reservations qui se recouvrent", () => {
    expect(
      computeFreeSlots(start, end, [
        { startsAt: "2026-10-05T09:00:00Z", endsAt: "2026-10-05T12:00:00Z" },
        { startsAt: "2026-10-05T10:00:00Z", endsAt: "2026-10-05T11:00:00Z" }
      ])
    ).toEqual([
      { startsAt: "2026-10-05T00:00:00Z", endsAt: "2026-10-05T09:00:00Z" },
      { startsAt: "2026-10-05T12:00:00Z", endsAt: "2026-10-06T00:00:00Z" }
    ]);
  });

  it("rogne une reservation venue de la veille", () => {
    expect(
      computeFreeSlots(start, end, [
        { startsAt: "2026-10-04T22:00:00Z", endsAt: "2026-10-05T02:00:00Z" }
      ])
    ).toEqual([{ startsAt: "2026-10-05T02:00:00Z", endsAt: "2026-10-06T00:00:00Z" }]);
  });

  it("rogne une reservation qui deborde sur le lendemain", () => {
    expect(
      computeFreeSlots(start, end, [
        { startsAt: "2026-10-05T22:00:00Z", endsAt: "2026-10-06T02:00:00Z" }
      ])
    ).toEqual([{ startsAt: "2026-10-05T00:00:00Z", endsAt: "2026-10-05T22:00:00Z" }]);
  });

  it("ignore une reservation hors de la journee", () => {
    expect(
      computeFreeSlots(start, end, [
        { startsAt: "2026-10-07T09:00:00Z", endsAt: "2026-10-07T10:00:00Z" }
      ])
    ).toEqual([{ startsAt: "2026-10-05T00:00:00Z", endsAt: "2026-10-06T00:00:00Z" }]);
  });

  it("ne rend aucun creneau quand la journee est entierement reservee", () => {
    expect(
      computeFreeSlots(start, end, [
        { startsAt: "2026-10-05T00:00:00Z", endsAt: "2026-10-06T00:00:00Z" }
      ])
    ).toEqual([]);
  });
});
