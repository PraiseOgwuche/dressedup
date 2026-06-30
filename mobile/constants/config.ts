import { THEME } from './theme';

export const API_CONFIG = {
  BASE_URL:
    process.env.EXPO_PUBLIC_API_BASE_URL ||
    (__DEV__
      ? 'http://localhost:8000' // Use your local IP for physical device: 'http://192.168.x.x:8000'
      : 'https://your-production-api.com'),
  API_VERSION: '/api/v1',
  // Render free tier cold starts can take 30–60s.
  TIMEOUT: 60000,
};

/** Resolve a server media path (e.g. "/media/items/x.jpg") to a full URL. */
export const mediaUrl = (path?: string | null): string | undefined =>
  path ? (path.startsWith('http') ? path : `${API_CONFIG.BASE_URL}${path}`) : undefined;

/** Controlled vocabularies — keep in sync with backend app/taxonomy.py. */
export const TAXONOMY = {
  categories: [
    'top', 'bottom', 'dress', 'outerwear', 'footwear', 'activewear',
    'swimwear', 'underwear', 'headwear', 'bag', 'accessory', 'jewelry',
  ],
  subcategories: {
    top: ['t-shirt', 'shirt', 'blouse', 'sweater', 'tank', 'hoodie', 'polo'],
    bottom: ['jeans', 'trousers', 'shorts', 'skirt', 'leggings', 'joggers'],
    dress: ['mini', 'midi', 'maxi', 'gown', 'jumpsuit'],
    outerwear: ['jacket', 'coat', 'blazer', 'cardigan', 'parka', 'vest'],
    footwear: ['sneakers', 'boots', 'heels', 'flats', 'sandals', 'loafers'],
    activewear: ['sports-bra', 'athletic-top', 'athletic-shorts', 'tracksuit'],
    swimwear: ['bikini', 'one-piece', 'trunks', 'board-shorts'],
    underwear: ['bra', 'briefs', 'boxers', 'socks', 'undershirt'],
    headwear: ['cap', 'beanie', 'hat', 'headband'],
    bag: ['tote', 'backpack', 'crossbody', 'clutch', 'duffel'],
    accessory: ['belt', 'scarf', 'sunglasses', 'watch', 'gloves', 'tie'],
    jewelry: ['ring', 'necklace', 'earrings', 'bracelet', 'anklet', 'brooch'],
  } as Record<string, string[]>,
  patterns: ['solid', 'striped', 'plaid', 'checked', 'floral', 'polka-dot', 'graphic', 'animal-print', 'camo'],
  formality: ['loungewear', 'casual', 'smart-casual', 'business', 'formal'],
  seasons: ['spring', 'summer', 'fall', 'winter', 'all-season'],
  weather: ['hot', 'warm', 'mild', 'cold', 'rainy', 'snow'],
  occasions: ['everyday', 'work', 'date', 'party', 'formal-event', 'workout', 'travel', 'loungewear', 'outdoor'],
  trends: ['quiet-luxury', 'streetwear', 'minimalist', 'preppy', 'classic'],
  activities: ['work', 'gym', 'everyday', 'date', 'party', 'travel', 'outdoor'],
  weekdays: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
};

export const COLORS = {
  primary: THEME.brand.ink,
  secondary: THEME.editorial.accentDark,
  success: THEME.shared.success,
  error: THEME.shared.error,
  warning: THEME.shared.warning,
  text: THEME.utility.text,
  textLight: THEME.utility.textMuted,
  background: THEME.utility.background,
  backgroundLight: THEME.utility.surfaceMuted,
  border: THEME.utility.border,
  editorial: THEME.editorial,
  utility: THEME.utility,
};
