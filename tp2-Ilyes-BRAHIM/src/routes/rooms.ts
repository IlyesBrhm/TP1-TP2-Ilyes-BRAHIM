import { Router } from "express";
import { rooms, findRoom, bookingsForRoom } from "../store.js";
import { parseDay, computeFreeSlots } from "../lib/availability.js";
import { ValidationError } from "../lib/validate.js";

export const roomsRouter = Router();

roomsRouter.get("/", (_req, res) => {
  res.json({ rooms });
});

roomsRouter.get("/:id", (req, res) => {
  const room = findRoom(req.params.id);
  if (!room) {
    res.status(404).json({ error: "salle inconnue" });
    return;
  }
  res.json({ room, bookings: bookingsForRoom(room.id) });
});

roomsRouter.get("/:id/availability", (req, res) => {
  const room = findRoom(req.params.id);
  if (!room) {
    res.status(404).json({ error: "salle inconnue" });
    return;
  }
  try {
    const date = req.query.date;
    if (typeof date !== "string" || date === "") {
      throw new ValidationError("date invalide : date");
    }
    const parsed = parseDay(date);
    if (!parsed.ok) {
      throw new ValidationError(parsed.error ?? `date invalide : ${date}`);
    }
    const freeSlots = computeFreeSlots(parsed.value.start, parsed.value.end, bookingsForRoom(room.id));
    res.json({ roomId: room.id, date, freeSlots });
  } catch (err) {
    if (err instanceof ValidationError) {
      res.status(err.status).json({ error: err.message });
      return;
    }
    throw err;
  }
});
