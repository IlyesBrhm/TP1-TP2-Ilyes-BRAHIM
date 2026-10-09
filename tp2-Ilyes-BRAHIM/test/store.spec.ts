import { describe, it, expect } from "vitest";
import { rooms, findRoom, bookingsForRoom } from "../src/store.js";

// Le store sera remplace par la vraie base (INFRA-140). En attendant, ces tests
// exercent le vrai store en memoire, pas un double.
describe("store", () => {
  it("expose le catalogue de salles", () => {
    expect(rooms.length).toBeGreaterThan(0);
  });

  it("retrouve une salle par son identifiant", () => {
    const room = findRoom("salle-a");
    expect(room?.id).toBe("salle-a");
    expect(room?.capacity).toBe(12);
  });

  it("ne retourne rien pour une salle inconnue", () => {
    expect(findRoom("cave")).toBeUndefined();
  });

  it("ne retourne aucune reservation pour une salle libre", () => {
    expect(bookingsForRoom("labo")).toHaveLength(0);
  });

  it("retourne les reservations d'une salle qui en a", () => {
    const reservations = bookingsForRoom("salle-a");
    expect(reservations.length).toBeGreaterThan(0);
    expect(reservations.every((b) => b.roomId === "salle-a")).toBe(true);
  });
});
