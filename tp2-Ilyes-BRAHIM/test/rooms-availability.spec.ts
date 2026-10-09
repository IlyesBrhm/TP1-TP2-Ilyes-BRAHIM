import { describe, it, expect } from "vitest";
import { createApp } from "../src/app.js";

async function get(path: string) {
  const app = createApp();
  const server = app.listen(0);
  const { port } = server.address() as { port: number };
  try {
    const res = await fetch(`http://127.0.0.1:${port}${path}`);
    return { status: res.status, body: (await res.json()) as Record<string, unknown> };
  } finally {
    server.close();
  }
}

// Donnees amorcees dans src/store.ts :
//   salle-a : 2026-10-05T09:00:00Z -> 2026-10-05T11:00:00Z
//   amphi   : 2026-10-06T14:00:00Z -> 2026-10-06T17:00:00Z
describe("GET /rooms/:id/availability", () => {
  it("rend les creneaux libres autour des reservations du jour", async () => {
    const res = await get("/rooms/salle-a/availability?date=2026-10-05");
    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      roomId: "salle-a",
      date: "2026-10-05",
      freeSlots: [
        { startsAt: "2026-10-05T00:00:00Z", endsAt: "2026-10-05T09:00:00Z" },
        { startsAt: "2026-10-05T11:00:00Z", endsAt: "2026-10-06T00:00:00Z" }
      ]
    });
  });

  it("rend la journee entiere pour une salle sans reservation", async () => {
    const res = await get("/rooms/salle-b/availability?date=2026-10-05");
    expect(res.status).toBe(200);
    expect(res.body.freeSlots).toEqual([
      { startsAt: "2026-10-05T00:00:00Z", endsAt: "2026-10-06T00:00:00Z" }
    ]);
  });

  it("ignore les reservations des autres salles et des autres jours", async () => {
    const res = await get("/rooms/amphi/availability?date=2026-10-05");
    expect(res.status).toBe(200);
    expect(res.body.freeSlots).toEqual([
      { startsAt: "2026-10-05T00:00:00Z", endsAt: "2026-10-06T00:00:00Z" }
    ]);
  });

  it("rend 404 pour une salle inconnue", async () => {
    const res = await get("/rooms/cave/availability?date=2026-10-05");
    expect(res.status).toBe(404);
  });

  it("rend 400 sans parametre date", async () => {
    const res = await get("/rooms/salle-a/availability");
    expect(res.status).toBe(400);
  });

  it("rend 400 pour une date mal formee", async () => {
    const res = await get("/rooms/salle-a/availability?date=05/10/2026");
    expect(res.status).toBe(400);
  });

  it("rend 400 pour une date calendaire inexistante", async () => {
    const res = await get("/rooms/salle-a/availability?date=2026-02-30");
    expect(res.status).toBe(400);
  });
});
