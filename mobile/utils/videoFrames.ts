const DEFAULT_FRAME_INTERVAL_MS = 2_000;

type VideoDraftIdentity = {
  name?: string | null;
  category?: string | null;
  subcategory?: string | null;
  brand?: string | null;
  product_name?: string | null;
  color?: string | null;
};

/**
 * Select representative moments without uploading the original video.
 * Times are kept away from the exact start/end, which are often blurry.
 */
export function sampleVideoTimestamps(
  durationMs: number | null | undefined,
  maxFrames: number,
  intervalMs = DEFAULT_FRAME_INTERVAL_MS,
): number[] {
  if (maxFrames <= 0) return [];
  if (!Number.isFinite(durationMs) || !durationMs || durationMs <= 0) return [0];

  const safeDuration = Math.max(1, durationMs);
  const frameCount = Math.min(maxFrames, Math.max(1, Math.ceil(safeDuration / intervalMs)));
  const segment = safeDuration / frameCount;

  return Array.from({ length: frameCount }, (_, index) =>
    Math.min(Math.max(0, safeDuration - 1), Math.round(segment * (index + 0.5))),
  );
}

/** Collapse repeated views of the same garment before the review queue. */
export function videoDraftIdentity(draft: VideoDraftIdentity): string {
  return [
    draft.category,
    draft.subcategory,
    draft.brand,
    draft.product_name,
    draft.name,
    draft.color,
  ]
    .map((value) => value?.trim().toLowerCase() ?? '')
    .join('|');
}
