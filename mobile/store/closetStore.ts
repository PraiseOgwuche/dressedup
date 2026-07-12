import { create } from 'zustand';

import { closetAPI } from '../services/api';
import { getApiErrorMessage } from '../services/errors';
import { ClosetItem, ClosetItemCreate, LaundrySummary } from '../types';

interface ClosetState {
  items: ClosetItem[];
  laundry: LaundrySummary | null;
  isLoading: boolean;
  error: string | null;
  fetchItems: () => Promise<void>;
  fetchLaundry: () => Promise<void>;
  createItem: (payload: ClosetItemCreate) => Promise<void>;
  updateItem: (itemId: number, payload: Partial<ClosetItemCreate>) => Promise<void>;
  deleteItem: (itemId: number) => Promise<void>;
  replacePhoto: (itemId: number, garment: { uri: string; name?: string | null; mimeType?: string | null }) => Promise<void>;
  backfillCutouts: (limit?: number) => Promise<{ updated: number; skipped: number }>;
  wearItem: (itemId: number) => Promise<void>;
  washItem: (itemId: number) => Promise<void>;
  soilItem: (itemId: number) => Promise<void>;
  washAll: (itemIds?: number[]) => Promise<void>;
  clearError: () => void;
}

export const useClosetStore = create<ClosetState>((set, get) => ({
  items: [],
  laundry: null,
  isLoading: false,
  error: null,
  fetchItems: async () => {
    set({ isLoading: true, error: null });
    try {
      const items = await closetAPI.list();
      set({ items, isLoading: false });
    } catch (error: any) {
      set({ error: getApiErrorMessage(error, 'Failed to load closet'), isLoading: false });
      throw error;
    }
  },
  fetchLaundry: async () => {
    try {
      const laundry = await closetAPI.laundrySummary();
      set({ laundry });
    } catch (error: any) {
      // Non-fatal: the closet still works without the laundry banner.
      set({ error: getApiErrorMessage(error, 'Failed to load laundry status') });
    }
  },
  wearItem: async (itemId) => {
    await closetAPI.wear(itemId);
    await Promise.all([get().fetchItems(), get().fetchLaundry()]);
  },
  washItem: async (itemId) => {
    await closetAPI.wash(itemId);
    await Promise.all([get().fetchItems(), get().fetchLaundry()]);
  },
  soilItem: async (itemId) => {
    await closetAPI.soil(itemId);
    await Promise.all([get().fetchItems(), get().fetchLaundry()]);
  },
  washAll: async (itemIds) => {
    const laundry = await closetAPI.washAll(itemIds);
    set({ laundry });
    await get().fetchItems();
  },
  createItem: async (payload) => {
    set({ isLoading: true, error: null });
    try {
      await closetAPI.create(payload);
      await get().fetchItems();
    } catch (error: any) {
      set({ error: getApiErrorMessage(error, 'Failed to create item'), isLoading: false });
      throw error;
    }
  },
  updateItem: async (itemId, payload) => {
    set({ isLoading: true, error: null });
    try {
      await closetAPI.update(itemId, payload);
      await get().fetchItems();
    } catch (error: any) {
      set({ error: getApiErrorMessage(error, 'Failed to update item'), isLoading: false });
      throw error;
    }
  },
  deleteItem: async (itemId) => {
    set({ isLoading: true, error: null });
    try {
      await closetAPI.remove(itemId);
      await get().fetchItems();
    } catch (error: any) {
      set({ error: getApiErrorMessage(error, 'Failed to delete item'), isLoading: false });
      throw error;
    }
  },
  replacePhoto: async (itemId, garment) => {
    set({ error: null });
    try {
      await closetAPI.replacePhoto(itemId, garment);
      await get().fetchItems();
    } catch (error: any) {
      set({ error: getApiErrorMessage(error, 'Failed to replace photo') });
      throw error;
    }
  },
  backfillCutouts: async (limit = 20) => {
    set({ error: null });
    try {
      const result = await closetAPI.backfillCutouts(limit);
      if (result.updated > 0) {
        await get().fetchItems();
      }
      return { updated: result.updated, skipped: result.skipped };
    } catch (error: any) {
      set({ error: getApiErrorMessage(error, 'Failed to improve photos') });
      throw error;
    }
  },
  clearError: () => set({ error: null }),
}));

