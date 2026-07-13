import { ClosetItem } from '../types';

export type CleanFilter = 'all' | 'clean' | 'dirty' | 'review';
export type ClosetSort = 'newest' | 'least_worn' | 'needs_wash';

export type ClosetQuery = {
  searchQuery: string;
  categoryFilter: string;
  cleanFilter: CleanFilter;
  colorFilter: string;
  brandFilter: string;
  seasonFilter: string;
  formalityFilter: string;
  tagFilter: string;
  sort: ClosetSort;
};

export function uniqueSorted(values: Array<string | null | undefined>): string[] {
  return Array.from(
    new Set(
      values
        .map((v) => (v ?? '').trim().toLowerCase())
        .filter(Boolean),
    ),
  ).sort((a, b) => a.localeCompare(b));
}

export function filterAndSortCloset(items: ClosetItem[], query: ClosetQuery): ClosetItem[] {
  const q = query.searchQuery.trim().toLowerCase();

  const filtered = items.filter((item) => {
    if (query.categoryFilter && item.category !== query.categoryFilter) return false;
    if (query.cleanFilter === 'clean' && !item.is_clean) return false;
    if (query.cleanFilter === 'dirty' && item.is_clean) return false;
    if (query.cleanFilter === 'review' && !item.needs_review) return false;
    if (query.colorFilter && (item.color ?? '').toLowerCase() !== query.colorFilter) return false;
    if (query.brandFilter && (item.brand ?? '').toLowerCase() !== query.brandFilter) return false;
    if (query.formalityFilter && (item.formality ?? '') !== query.formalityFilter) return false;
    if (query.tagFilter) {
      const tags = (item.tags ?? []).map((t) => t.toLowerCase());
      if (!tags.includes(query.tagFilter.toLowerCase())) return false;
    }
    if (query.seasonFilter) {
      const seasons = item.seasons ?? [];
      if (!seasons.includes(query.seasonFilter) && !seasons.includes('all-season')) return false;
    }
    if (!q) return true;
    const haystack = [
      item.name,
      item.brand,
      item.category,
      item.subcategory,
      item.color,
      item.formality,
      ...(item.tags ?? []),
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    return haystack.includes(q);
  });

  const sorted = [...filtered];
  if (query.sort === 'least_worn') {
    sorted.sort((a, b) => a.times_worn - b.times_worn || b.id - a.id);
  } else if (query.sort === 'needs_wash') {
    sorted.sort((a, b) => {
      if (a.is_clean !== b.is_clean) return a.is_clean ? 1 : -1;
      const aRatio =
        a.effective_wear_limit != null && a.effective_wear_limit > 0
          ? a.wears_since_wash / a.effective_wear_limit
          : 0;
      const bRatio =
        b.effective_wear_limit != null && b.effective_wear_limit > 0
          ? b.wears_since_wash / b.effective_wear_limit
          : 0;
      return bRatio - aRatio || b.id - a.id;
    });
  } else {
    sorted.sort((a, b) => {
      const aTime = new Date(a.created_at).getTime();
      const bTime = new Date(b.created_at).getTime();
      return bTime - aTime || b.id - a.id;
    });
  }

  return sorted;
}
