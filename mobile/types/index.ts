export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_premium: boolean;
  created_at: string;
}

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

export interface OutfitSuggestion {
  title: string;
  weather_tag?: string | null;
  occasion?: string | null;
  rationale?: string | null;
  top?: ClosetItem | null;
  bottom?: ClosetItem | null;
  shoes?: ClosetItem | null;
  outerwear?: ClosetItem | null;
  alternatives: ClosetItem[];
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

export interface SocialPost {
  id: number;
  user_id: number;
  caption: string;
  look_name?: string | null;
  occasion?: string | null;
  reactions_count: number;
  comments_count: number;
  created_at: string;
}

export interface TripPlan {
  id: number;
  user_id: number;
  destination: string;
  weather_tag?: string | null;
  days: number;
  notes?: string | null;
  is_completed: boolean;
  created_at: string;
}

export interface ShopRecommendation {
  category: string;
  reason: string;
  priority: string;
}
