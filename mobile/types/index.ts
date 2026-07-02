export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_premium: boolean;
  premium_trial_ends_at?: string | null;
  created_at: string;
}

export const hasPremiumAccess = (user?: User | null): boolean => {
  if (!user) return false;
  if (user.is_premium) return true;
  if (user.premium_trial_ends_at) {
    return new Date(user.premium_trial_ends_at) > new Date();
  }
  return false;
};

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
}

export interface ClosetItem {
  id: number;
  user_id: number;
  name: string;
  category: string;
  subcategory?: string | null;
  brand?: string | null;
  product_name?: string | null;
  size?: string | null;
  color?: string | null;
  color_hex?: string | null;
  pattern?: string | null;
  material?: string | null;
  occasion?: string[] | null;
  formality?: string | null;
  weather_tag?: string[] | null;
  seasons?: string[] | null;
  image_url?: string | null;
  thumbnail_url?: string | null;
  is_clean: boolean;
  times_worn: number;
  wears_since_wash: number;
  last_worn_at?: string | null;
  last_washed_at?: string | null;
  wear_limit?: number | null;
  effective_wear_limit?: number | null;
  source: string;
  needs_review: boolean;
  created_at: string;
}

export interface LaundrySummary {
  clean_count: number;
  dirty_count: number;
  laundry_due: boolean;
  depleted_categories: string[];
  clean_by_category: Record<string, number>;
  dirty_by_category: Record<string, number>;
  message: string;
}

export interface ClosetItemCreate {
  name: string;
  category: string;
  subcategory?: string;
  brand?: string;
  product_name?: string;
  size?: string;
  color?: string;
  color_hex?: string;
  pattern?: string;
  material?: string;
  occasion?: string[];
  formality?: string;
  weather_tag?: string[];
  seasons?: string[];
  image_url?: string;
  thumbnail_url?: string;
  is_clean: boolean;
  source?: string;
  needs_review?: boolean;
  confidence?: Record<string, number>;
  ai_metadata?: Record<string, unknown>;
}

export interface DraftItem {
  name: string;
  category: string;
  subcategory?: string | null;
  brand?: string | null;
  product_name?: string | null;
  size?: string | null;
  color?: string | null;
  color_hex?: string | null;
  pattern?: string | null;
  material?: string | null;
  occasion: string[];
  formality?: string | null;
  weather_tag: string[];
  seasons: string[];
  source: string;
  confidence: Record<string, number>;
  needs_review: boolean;
  sku?: string | null;
  price?: number | null;
  purchase_date?: string | null;
}

export interface IngestResult {
  draft: DraftItem;
  image_url: string;
  thumbnail_url: string;
}

export interface BatchIngestEntry {
  filename?: string | null;
  result?: IngestResult | null;
  error?: string | null;
}

export interface BatchIngestResult {
  entries: BatchIngestEntry[];
}

export interface MultiIngestEntry {
  index: number;
  draft: DraftItem;
  image_url: string;
  thumbnail_url: string;
}

export interface MultiIngestResult {
  source_image_url: string;
  entries: MultiIngestEntry[];
}

export interface ReceiptIngestResult {
  source_image_url: string;
  merchant?: string | null;
  purchase_date?: string | null;
  entries: MultiIngestEntry[];
}

export interface OutfitSuggestion {
  title: string;
  weather_tag?: string | null;
  occasion?: string | null;
  trend?: string | null;
  rationale?: string | null;
  styling_note?: string | null;
  top?: ClosetItem | null;
  bottom?: ClosetItem | null;
  shoes?: ClosetItem | null;
  outerwear?: ClosetItem | null;
  alternatives: ClosetItem[];
}

export interface ParsedOutfitIntent {
  occasion?: string | null;
  weather_tag?: string | null;
  trend?: string | null;
  interpretation: string;
}

export interface OutfitAskResponse {
  query: string;
  parsed: ParsedOutfitIntent;
  suggestion: OutfitSuggestion;
}

export type OutfitSlotKey = 'top' | 'bottom' | 'shoes' | 'outerwear';

export interface OutfitSwapOptions {
  swapSlot: OutfitSlotKey;
  topId?: number | null;
  bottomId?: number | null;
  shoesId?: number | null;
  outerwearId?: number | null;
}

export interface OutfitFeedbackPayload {
  top_id?: number | null;
  bottom_id?: number | null;
  shoes_id?: number | null;
  outerwear_id?: number | null;
  signal: 'like' | 'dislike' | 'wore';
  occasion?: string | null;
  weather_tag?: string | null;
}

export interface PlanActivity {
  activity: string;
  occasion: string;
  mode: 'wear' | 'pack';
  title: string;
  rationale?: string | null;
  top?: ClosetItem | null;
  bottom?: ClosetItem | null;
  shoes?: ClosetItem | null;
  outerwear?: ClosetItem | null;
  packing_list: ClosetItem[];
}

export interface DailyPlan {
  weather_tag?: string | null;
  activities: PlanActivity[];
  routine_enabled?: boolean | null;
  source?: string | null;
}

export interface DailyRoutine {
  enabled: boolean;
  wake_time: string;
  weekday_activities: string[];
  weekend_activities: string[];
  gym_days: string[];
  default_weather_tag?: string | null;
  notifications_enabled: boolean;
  timezone: string;
}

export interface NotificationTestResult {
  title: string;
  body: string;
  tokens_sent: number;
  push_result: Record<string, unknown>;
}

export interface EmailIngestSettings {
  enabled: boolean;
  address?: string | null;
  instructions: string;
}

export interface EmailIngestLog {
  id: number;
  sender?: string | null;
  subject?: string | null;
  items_created: number;
  attachments_processed: number;
  errors?: string[] | null;
  created_at: string;
}

export interface EmailIngestResult {
  items_created: number;
  attachments_processed: number;
  errors: string[];
  log_id?: number | null;
}

export interface SocialPost {
  id: number;
  user_id: number;
  user_name: string;
  caption?: string | null;
  look_name?: string | null;
  occasion?: string | null;
  photo_url?: string | null;
  top?: ClosetItem | null;
  bottom?: ClosetItem | null;
  shoes?: ClosetItem | null;
  outerwear?: ClosetItem | null;
  reactions_count: number;
  comments_count: number;
  liked_by_me: boolean;
  is_mine: boolean;
  following_author: boolean;
  created_at: string;
}

export type FeedScope = 'all' | 'following' | 'mine';

export interface SocialComment {
  id: number;
  post_id: number;
  user_id: number;
  user_name: string;
  body: string;
  is_mine: boolean;
  created_at: string;
}

export interface SocialUserSummary {
  id: number;
  full_name: string;
  post_count: number;
  follower_count: number;
  is_following: boolean;
  is_self: boolean;
}

export interface SocialFollowResult {
  following: boolean;
  follower_count: number;
}

export interface SocialPostLikeResult {
  liked: boolean;
  reactions_count: number;
}

export type OutfitSharePayload = {
  top?: ClosetItem | null;
  bottom?: ClosetItem | null;
  shoes?: ClosetItem | null;
  outerwear?: ClosetItem | null;
};

export interface StreakStats {
  current_streak: number;
  longest_streak: number;
  total_fit_days: number;
  active_this_week: number;
  last_active_date?: string | null;
  timezone: string;
}

export interface TripPlan {
  id: number;
  user_id: number;
  destination: string;
  weather_tag?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  days: number;
  notes?: string | null;
  is_completed: boolean;
  created_at: string;
}

export interface TripDayOutfit {
  day: number;
  title: string;
  trip_date?: string | null;
  weather_tag?: string | null;
  weather_summary?: string | null;
  rationale?: string | null;
  top?: ClosetItem | null;
  bottom?: ClosetItem | null;
  shoes?: ClosetItem | null;
  outerwear?: ClosetItem | null;
}

export interface TripPackingPlan {
  trip: TripPlan;
  days: TripDayOutfit[];
  packing_list: ClosetItem[];
  summary: string;
  weather_source?: string | null;
  weather_note?: string | null;
}

export interface ShopOutfitGarment {
  id: number;
  name: string;
  category: string;
  color?: string | null;
  image_url?: string | null;
  thumbnail_url?: string | null;
  is_shop_pick?: boolean;
}

export interface ShopOutfitPreview {
  score: number;
  top?: ShopOutfitGarment | null;
  bottom?: ShopOutfitGarment | null;
  shoes?: ShopOutfitGarment | null;
  outerwear?: ShopOutfitGarment | null;
}

export interface ShopRecommendation {
  product_id: string;
  brand: string;
  name: string;
  category: string;
  color?: string | null;
  price_usd: number;
  product_url: string;
  buy_url: string;
  image_url?: string | null;
  retailer?: string | null;
  pitch: string;
  outfit_count: number;
  sample_outfits?: ShopOutfitPreview[];
  reason: string;
  priority: string;
}

export interface ShopRecommendationsResponse {
  summary: string;
  styling_insight?: string | null;
  recommendations: ShopRecommendation[];
}

export type StyleEventType =
  | 'like'
  | 'dislike'
  | 'wore'
  | 'swap'
  | 'shop_tap'
  | 'shop_preview'
  | 'feed_share'
  | 'feed_like';

export interface StyleSignalPayload {
  event_type: StyleEventType;
  top_id?: number | null;
  bottom_id?: number | null;
  shoes_id?: number | null;
  outerwear_id?: number | null;
  product_id?: string | null;
  post_id?: number | null;
  occasion?: string | null;
  weather_tag?: string | null;
}

export type ListingType = 'sell' | 'gift';
export type ListingCondition = 'like_new' | 'good' | 'fair';
export type ListingStatus = 'active' | 'gone' | 'removed';

export interface ClosetListing {
  id: number;
  user_id: number;
  seller_name: string;
  listing_type: ListingType;
  title: string;
  description?: string | null;
  price_cents?: number | null;
  condition: ListingCondition;
  status: ListingStatus;
  is_mine: boolean;
  item: ClosetItem;
  created_at: string;
}

export interface ListingInterestResult {
  mailto: string;
  seller_name: string;
}
