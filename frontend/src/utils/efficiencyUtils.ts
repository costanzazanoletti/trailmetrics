import { Segment } from '../types/activity';

/**
 * Decides if wee need to execute polling for missing efficiency zones
 */
export function shouldPollForZones(segments: Segment[]): boolean {
  if (segments.length === 0) return false;

  const missingZones = segments.filter(
    (seg) => !seg.efficiencyZone || !seg.gradeEfficiencyZone
  );

  const missingRatio = missingZones.length / segments.length;

  // if more than 20% of segments miss we execute the polling
  return missingRatio > 0.2;
}
