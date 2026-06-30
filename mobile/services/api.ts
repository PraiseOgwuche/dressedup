import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import { API_CONFIG } from '../constants/config';
import {
  User,
  LoginCredentials,
  RegisterData,
  AuthResponse,
  ClosetItem,
  ClosetItemCreate,
  IngestResult,
  BatchIngestResult,
  MultiIngestResult,
  ReceiptIngestResult,
  LaundrySummary,
  OutfitSuggestion,
  OutfitAskResponse,
  SocialPost,
  SocialPostLikeResult,
  OutfitSharePayload,
  StreakStats,
  ShopRecommendationsResponse,
  TripPlan,
  TripPackingPlan,
  DailyPlan,
  DailyRoutine,
  NotificationTestResult,
  EmailIngestSettings,
  EmailIngestLog,
  EmailIngestResult,
  OutfitFeedbackPayload,
  OutfitSwapOptions,
  OutfitSlotKey,
} from '../types';

type ImageUpload = { uri: string; name?: string | null; mimeType?: string | null };

const toFilePart = (image: ImageUpload, fallbackName: string) => ({
  uri: image.uri,
  name: image.name || fallbackName,
  type: image.mimeType || 'image/jpeg',
});

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const isRetryableError = (error: unknown): boolean => {
  const err = error as { response?: { status?: number }; code?: string; message?: string };
  if (!err?.response) return true;
  if (err.code === 'ECONNABORTED') return true;
  const status = err.response.status;
  return status === 502 || status === 503 || status === 504;
};

/** Retry auth calls — Render free tier sleeps and the first request often times out. */
async function withAuthRetry<T>(fn: () => Promise<T>): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      if (attempt > 0) {
        await axios.get(`${API_CONFIG.BASE_URL}/health`, { timeout: API_CONFIG.TIMEOUT });
        await sleep(2000 * attempt);
      }
      return await fn();
    } catch (error) {
      lastError = error;
      if (!isRetryableError(error) || attempt === 2) {
        throw error;
      }
    }
  }
  throw lastError;
}

const api = axios.create({
  baseURL: `${API_CONFIG.BASE_URL}${API_CONFIG.API_VERSION}`,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await SecureStore.getItemAsync('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear storage and redirect to login
      await SecureStore.deleteItemAsync('access_token');
      // You'll handle navigation in the auth store
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: async (data: RegisterData): Promise<User> => {
    const response = await withAuthRetry(() => api.post<User>('/auth/register', data));
    return response.data;
  },

  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await withAuthRetry(() => api.post<AuthResponse>('/auth/login', credentials));
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

export const closetAPI = {
  list: async (): Promise<ClosetItem[]> => {
    const response = await api.get<ClosetItem[]>('/closet/items');
    return response.data;
  },
  create: async (payload: ClosetItemCreate): Promise<ClosetItem> => {
    const response = await api.post<ClosetItem>('/closet/items', payload);
    return response.data;
  },
  update: async (itemId: number, payload: Partial<ClosetItemCreate>): Promise<ClosetItem> => {
    const response = await api.put<ClosetItem>(`/closet/items/${itemId}`, payload);
    return response.data;
  },
  remove: async (itemId: number): Promise<void> => {
    await api.delete(`/closet/items/${itemId}`);
  },
  ingest: async (garment: ImageUpload, label?: ImageUpload | null): Promise<IngestResult> => {
    const form = new FormData();
    form.append('garment', toFilePart(garment, 'garment.jpg') as any);
    if (label) {
      form.append('label', toFilePart(label, 'label.jpg') as any);
    }
    const response = await api.post<IngestResult>('/closet/ingest', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  ingestBatch: async (garments: ImageUpload[]): Promise<BatchIngestResult> => {
    const form = new FormData();
    garments.forEach((image, i) => {
      form.append('garments', toFilePart(image, `garment-${i}.jpg`) as any);
    });
    const response = await api.post<BatchIngestResult>('/closet/ingest/batch', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // bulk vision calls take longer than the default
    });
    return response.data;
  },
  ingestMulti: async (garment: ImageUpload, label?: ImageUpload | null): Promise<MultiIngestResult> => {
    const form = new FormData();
    form.append('garment', toFilePart(garment, 'flatlay.jpg') as any);
    if (label) {
      form.append('label', toFilePart(label, 'label.jpg') as any);
    }
    const response = await api.post<MultiIngestResult>('/closet/ingest/multi', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 90000,
    });
    return response.data;
  },
  ingestReceipt: async (receipt: ImageUpload): Promise<ReceiptIngestResult> => {
    const form = new FormData();
    form.append('receipt', toFilePart(receipt, 'receipt.jpg') as any);
    const response = await api.post<ReceiptIngestResult>('/closet/ingest/receipt', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 90000,
    });
    return response.data;
  },
  ingestLabel: async (label: ImageUpload): Promise<IngestResult> => {
    const form = new FormData();
    form.append('label', toFilePart(label, 'label.jpg') as any);
    const response = await api.post<IngestResult>('/closet/ingest/label', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  wear: async (itemId: number): Promise<ClosetItem> => {
    const response = await api.post<ClosetItem>(`/closet/items/${itemId}/wear`);
    return response.data;
  },
  wash: async (itemId: number): Promise<ClosetItem> => {
    const response = await api.post<ClosetItem>(`/closet/items/${itemId}/wash`);
    return response.data;
  },
  soil: async (itemId: number): Promise<ClosetItem> => {
    const response = await api.post<ClosetItem>(`/closet/items/${itemId}/soil`);
    return response.data;
  },
  washAll: async (itemIds?: number[]): Promise<LaundrySummary> => {
    const response = await api.post<LaundrySummary>('/closet/laundry/wash-all', {
      item_ids: itemIds ?? null,
    });
    return response.data;
  },
  laundrySummary: async (): Promise<LaundrySummary> => {
    const response = await api.get<LaundrySummary>('/closet/laundry/summary');
    return response.data;
  },
};

export const emailIngestAPI = {
  getSettings: async (): Promise<EmailIngestSettings> => {
    const response = await api.get<EmailIngestSettings>('/closet/email-ingest');
    return response.data;
  },
  getLogs: async (): Promise<EmailIngestLog[]> => {
    const response = await api.get<EmailIngestLog[]>('/closet/email-ingest/logs');
    return response.data;
  },
  simulate: async (attachment: ImageUpload, subject?: string): Promise<EmailIngestResult> => {
    const form = new FormData();
    form.append('attachment', toFilePart(attachment, 'receipt.jpg') as any);
    if (subject) {
      form.append('subject', subject);
    }
    const response = await api.post<EmailIngestResult>('/closet/email-ingest/simulate', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 90000,
    });
    return response.data;
  },
};

export const outfitAPI = {
  getSuggestion: async (
    occasion?: string,
    weatherTag?: string,
    swap?: OutfitSwapOptions,
    trend?: string,
  ): Promise<OutfitSuggestion> => {
    const response = await api.get<OutfitSuggestion>('/outfits/suggestion', {
      params: {
        occasion,
        weather_tag: weatherTag,
        trend,
        ...(swap
          ? {
              swap_slot: swap.swapSlot,
              top_id: swap.topId ?? undefined,
              bottom_id: swap.bottomId ?? undefined,
              shoes_id: swap.shoesId ?? undefined,
              outerwear_id: swap.outerwearId ?? undefined,
            }
          : {}),
      },
    });
    return response.data;
  },
  getTrends: async (): Promise<{ id: string; label: string }[]> => {
    const response = await api.get<{ id: string; label: string }[]>('/outfits/trends');
    return response.data;
  },
  ask: async (query: string): Promise<OutfitAskResponse> => {
    const response = await withAuthRetry(() =>
      api.post<OutfitAskResponse>('/outfits/ask', { query }),
    );
    return response.data;
  },
  plan: async (activities: string[], weatherTag?: string): Promise<DailyPlan> => {
    const response = await api.get<DailyPlan>('/outfits/plan', {
      params: {
        activities: (activities.length ? activities : ['work']).join(','),
        weather_tag: weatherTag,
      },
    });
    return response.data;
  },
  getRoutine: async (): Promise<DailyRoutine> => {
    const response = await api.get<DailyRoutine>('/outfits/routine');
    return response.data;
  },
  updateRoutine: async (payload: Partial<DailyRoutine>): Promise<DailyRoutine> => {
    const response = await api.put<DailyRoutine>('/outfits/routine', payload);
    return response.data;
  },
  planToday: async (): Promise<DailyPlan> => {
    const response = await api.get<DailyPlan>('/outfits/plan/today');
    return response.data;
  },
  feedback: async (payload: OutfitFeedbackPayload) => {
    const response = await api.post('/outfits/feedback', payload);
    return response.data;
  },
};

export const notificationsAPI = {
  register: async (payload: { token: string; platform?: string; timezone: string }): Promise<void> => {
    await api.post('/notifications/register', payload);
  },
  unregister: async (payload: { token: string }): Promise<void> => {
    await api.delete('/notifications/register', { data: payload });
  },
  test: async (): Promise<NotificationTestResult> => {
    const response = await api.post<NotificationTestResult>('/notifications/test');
    return response.data;
  },
};

export const socialAPI = {
  listPosts: async (): Promise<SocialPost[]> => {
    const response = await api.get<SocialPost[]>('/social/posts');
    return response.data;
  },
  createPost: async (payload: {
    top_id?: number;
    bottom_id?: number;
    shoes_id?: number;
    outerwear_id?: number;
    caption?: string;
    photo?: ImageUpload | null;
  }): Promise<SocialPost> => {
    const form = new FormData();
    if (payload.top_id != null) form.append('top_id', String(payload.top_id));
    if (payload.bottom_id != null) form.append('bottom_id', String(payload.bottom_id));
    if (payload.shoes_id != null) form.append('shoes_id', String(payload.shoes_id));
    if (payload.outerwear_id != null) form.append('outerwear_id', String(payload.outerwear_id));
    if (payload.caption?.trim()) form.append('caption', payload.caption.trim());
    if (payload.photo) {
      form.append('photo', toFilePart(payload.photo, 'fit.jpg') as any);
    }
    const response = await api.post<SocialPost>('/social/posts', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  toggleLike: async (postId: number): Promise<SocialPostLikeResult> => {
    const response = await api.post<SocialPostLikeResult>(`/social/posts/${postId}/like`);
    return response.data;
  },
  getStreak: async (timezone?: string): Promise<StreakStats> => {
    const response = await api.get<StreakStats>('/social/streak', {
      params: timezone ? { timezone } : undefined,
    });
    return response.data;
  },
};

export const shopAPI = {
  getRecommendations: async (): Promise<ShopRecommendationsResponse> => {
    const response = await api.get<ShopRecommendationsResponse>('/shop/recommendations');
    return response.data;
  },
};

export const tripsAPI = {
  listPlans: async (): Promise<TripPlan[]> => {
    const response = await api.get<TripPlan[]>('/trips/plans');
    return response.data;
  },
  createPlan: async (payload: {
    destination: string;
    weather_tag?: string;
    start_date?: string;
    end_date?: string;
    days?: number;
    notes?: string;
  }): Promise<TripPlan> => {
    const response = await api.post<TripPlan>('/trips/plans', payload);
    return response.data;
  },
  getPacking: async (planId: number): Promise<TripPackingPlan> => {
    const response = await api.get<TripPackingPlan>(`/trips/plans/${planId}/packing`);
    return response.data;
  },
};

export default api;
