import { ClosetItem } from '../types';
import { CleanFilter, ClosetSort, filterAndSortCloset, uniqueSorted } from '../utils/closetQuery';

describe('closetQuery', () => {
  const items: ClosetItem[] = [
    {
      id: 1,
      user_id: 1,
      name: 'Navy Tee',
      category: 'top',
      brand: 'Uniqlo',
      color: 'navy',
      formality: 'casual',
      seasons: ['summer'],
      is_clean: true,
      times_worn: 5,
      wears_since_wash: 2,
      effective_wear_limit: 5,
      source: 'photo',
      needs_review: true,
      created_at: '2026-07-01T00:00:00Z',
    },
    {
      id: 2,
      user_id: 1,
      name: 'Black Jeans',
      category: 'bottom',
      brand: 'Levi',
      color: 'black',
      formality: 'casual',
      seasons: ['all-season'],
      is_clean: false,
      times_worn: 1,
      wears_since_wash: 4,
      effective_wear_limit: 4,
      source: 'manual',
      needs_review: false,
      created_at: '2026-07-10T00:00:00Z',
    },
  ];

  const base = {
    searchQuery: '',
    categoryFilter: '',
    cleanFilter: 'all' as CleanFilter,
    colorFilter: '',
    brandFilter: '',
    seasonFilter: '',
    formalityFilter: '',
    sort: 'newest' as ClosetSort,
  };

  it('filters review inbox', () => {
    const result = filterAndSortCloset(items, { ...base, cleanFilter: 'review' });
    expect(result.map((i) => i.id)).toEqual([1]);
  });

  it('sorts least worn', () => {
    const result = filterAndSortCloset(items, { ...base, sort: 'least_worn' });
    expect(result.map((i) => i.id)).toEqual([2, 1]);
  });

  it('sorts needs wash with dirty first', () => {
    const result = filterAndSortCloset(items, { ...base, sort: 'needs_wash' });
    expect(result[0].id).toBe(2);
  });

  it('filters brand and color', () => {
    const result = filterAndSortCloset(items, {
      ...base,
      brandFilter: 'uniqlo',
      colorFilter: 'navy',
    });
    expect(result.map((i) => i.id)).toEqual([1]);
  });

  it('uniqueSorted normalizes', () => {
    expect(uniqueSorted(['Navy', 'navy', ' Black ', null])).toEqual(['black', 'navy']);
  });
});
