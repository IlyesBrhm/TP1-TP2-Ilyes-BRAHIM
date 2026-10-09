export interface Slot {
  startsAt: string;
  endsAt: string;
}

export interface DayRange {
  ok: boolean;
  value: { start: number; end: number };
  error?: string;
}

export function parseDay(date: string): DayRange {
  const invalid: DayRange = {
    ok: false,
    value: { start: 0, end: 0 },
    error: `date invalide : ${date}`
  };
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return invalid;
  }
  const [year, month, day] = date.split("-").map(Number);
  const start = Date.UTC(year, month - 1, day);
  const probe = new Date(start);
  if (
    probe.getUTCFullYear() !== year ||
    probe.getUTCMonth() !== month - 1 ||
    probe.getUTCDate() !== day
  ) {
    return invalid;
  }
  return { ok: true, value: { start, end: Date.UTC(year, month - 1, day + 1) } };
}

function toIso(ms: number): string {
  return new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z");
}

export function computeFreeSlots(
  dayStart: number,
  dayEnd: number,
  busy: ReadonlyArray<{ startsAt: string; endsAt: string }>
): Slot[] {
  const clipped = busy
    .map((b) => ({ start: Date.parse(b.startsAt), end: Date.parse(b.endsAt) }))
    .filter((b) => Number.isFinite(b.start) && Number.isFinite(b.end))
    .map((b) => ({ start: Math.max(b.start, dayStart), end: Math.min(b.end, dayEnd) }))
    .filter((b) => b.start < b.end)
    .sort((a, b) => a.start - b.start);

  const free: Slot[] = [];
  let cursor = dayStart;
  for (const b of clipped) {
    if (b.start > cursor) {
      free.push({ startsAt: toIso(cursor), endsAt: toIso(b.start) });
    }
    cursor = Math.max(cursor, b.end);
  }
  if (cursor < dayEnd) {
    free.push({ startsAt: toIso(cursor), endsAt: toIso(dayEnd) });
  }
  return free;
}

export default computeFreeSlots;
