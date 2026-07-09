import { create } from 'zustand';

import { socialAPI } from '../services/api';
import { FeedActivityItem } from '../types';

interface FeedActivityState {
  unreadCount: number;
  items: FeedActivityItem[];
  loading: boolean;
  refresh: () => Promise<void>;
  markSeen: () => Promise<void>;
}

export const useFeedActivityStore = create<FeedActivityState>((set) => ({
  unreadCount: 0,
  items: [],
  loading: false,
  refresh: async () => {
    set({ loading: true });
    try {
      const response = await socialAPI.getActivity();
      set({
        unreadCount: response.unread_count,
        items: response.items,
      });
    } catch {
      // Keep last known badge count on transient errors.
    } finally {
      set({ loading: false });
    }
  },
  markSeen: async () => {
    try {
      await socialAPI.markActivitySeen();
      set((state) => ({
        unreadCount: 0,
        items: state.items.map((item) => ({ ...item, is_unread: false })),
      }));
    } catch {
      // Non-blocking — sheet can still close.
    }
  },
}));
