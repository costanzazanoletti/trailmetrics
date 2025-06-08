function haversineDistance(
  [lat1, lon1]: [number, number],
  [lat2, lon2]: [number, number]
): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const R = 6371000; // raggio terrestre in metri
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export function computeDistanceFromLatLng(
  latlng: [number, number][]
): number[] {
  const distance: number[] = [0];
  for (let i = 1; i < latlng.length; i++) {
    const d = haversineDistance(latlng[i - 1], latlng[i]);
    distance.push(distance[i - 1] + d);
  }
  return distance;
}
