import { create } from 'zustand';

import { outfitAPI } from '../services/api';
import { registerPushWithBackend } from '../services/pushNotifications';
import { DailyPlan, DailyRoutine } from '../types';

interface RoutineState {
  routine: DailyRoutine | null;
  pendingPlan: DailyPlan | null;
  loading: boolean;
  saving: boolean;
  fetchRoutine: () => Promise<void>;
  saveRoutine: (patch: Partial<DailyRoutine>) => Promise<void>;
  sendMyPlan: () => Promise<DailyPlan>;
  consumePendingPlan: () => DailyPlan | null;
  syncPushIfEnabled: () => Promise<void>;
}

export const useRoutineStore = create<RoutineState>((set, get) => ({
  routine: null,
  pendingPlan: null,
  loading: false,
  saving: false,
  fetchRoutine: async () => {
    set({ loading: true });
    try {
      const routine = await outfitAPI.getRoutine();
      set({ routine });
    } finally {
      set({ loading: false });
    }
  },
  saveRoutine: async (patch) => {
    set({ saving: true });
    try {
      const routine = await outfitAPI.updateRoutine(patch);
      set({ routine });
    } finally {
      set({ saving: false });
    }
  },
  sendMyPlan: async () => {
    set({ loading: true });
    try {
      const plan = await outfitAPI.planToday();
      set({ pendingPlan: plan });
      return plan;
    } finally {
      set({ loading: false });
    }
  },
  consumePendingPlan: () => {
    const plan = get().pendingPlan;
    if (plan) set({ pendingPlan: null });
    return plan;
  },
  syncPushIfEnabled: async () => {
    const routine = get().routine;
    if (!routine?.notifications_enabled) return;
    try {
      await registerPushWithBackend();
    } catch {
      // Expo Go / missing EAS project — push only works in a dev build.
    }
  },
}));
