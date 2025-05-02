export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
    .toString()
    .padStart(2, '0');
  const m = Math.floor((seconds % 3600) / 60)
    .toString()
    .padStart(2, '0');
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, '0');
  return `${h}:${m}:${s}`;
}

export function formatTime(seconds: number) {
  const h = Math.floor(seconds / 3600)
    .toString()
    .padStart(2, '0');
  const m = Math.floor((seconds % 3600) / 60)
    .toString()
    .padStart(2, '0');
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, '0');
  return `${h}:${m}:${s}`;
}

export function formatPace(speed: number | undefined) {
  if (!speed || speed <= 0) return 'N/A';
  const speedKmH = speed * 3.6;
  const paceSecPerKm = 3600 / speedKmH;
  const paceMin = Math.floor(paceSecPerKm / 60);
  const paceSec = Math.round(paceSecPerKm % 60);
  return `${paceMin}:${paceSec.toString().padStart(2, '0')}/km`;
}

export const getShortSegmentId = (segmentId: string) =>
  segmentId.includes('-') ? segmentId.split('-')[1] : segmentId;

export function getGradeCategoryRange(gradeCategory: number): [number, number] {
  const halfWidth = 1.25; // 2.5 / 2
  return [gradeCategory - halfWidth, gradeCategory + halfWidth];
}
