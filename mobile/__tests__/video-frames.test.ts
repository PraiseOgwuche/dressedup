import { sampleVideoTimestamps, videoDraftIdentity } from '../utils/videoFrames';

describe('sampleVideoTimestamps', () => {
  it('samples one centered frame per two seconds', () => {
    expect(sampleVideoTimestamps(6_000, 15)).toEqual([1_000, 3_000, 5_000]);
  });

  it('spreads long videos across the frame limit', () => {
    const timestamps = sampleVideoTimestamps(60_000, 15);

    expect(timestamps).toHaveLength(15);
    expect(timestamps[0]).toBe(2_000);
    expect(timestamps[14]).toBe(58_000);
  });

  it('falls back safely when duration metadata is unavailable', () => {
    expect(sampleVideoTimestamps(undefined, 15)).toEqual([0]);
  });

  it('returns no frames when the limit is zero', () => {
    expect(sampleVideoTimestamps(10_000, 0)).toEqual([]);
  });

  it('gives repeated views of the same detected garment one identity', () => {
    const first = videoDraftIdentity({
      name: 'Oxford Shirt',
      category: 'Tops',
      subcategory: 'Shirt',
      brand: 'Example',
      color: 'Blue',
    });
    const repeated = videoDraftIdentity({
      name: ' oxford shirt ',
      category: 'tops',
      subcategory: 'shirt',
      brand: 'EXAMPLE',
      color: 'blue',
    });

    expect(repeated).toBe(first);
  });
});
