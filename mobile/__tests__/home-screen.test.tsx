import React from 'react';
import { render } from '@testing-library/react-native';

import HomeScreen from '../app/(tabs)/home';

jest.mock('expo-router', () => ({
  useFocusEffect: jest.fn(),
  useRouter: () => ({ push: jest.fn() }),
}));

jest.mock('../store/authStore', () => ({
  useAuthStore: () => ({
    user: {
      id: 1,
      full_name: 'Test User',
      email: 'test@example.com',
      is_active: true,
      is_premium: false,
      created_at: new Date().toISOString(),
    },
  }),
}));

jest.mock('../store/closetStore', () => ({
  useClosetStore: () => ({
    items: [],
    laundry: null,
    fetchItems: jest.fn(),
    fetchLaundry: jest.fn(),
  }),
}));

jest.mock('../store/routineStore', () => ({
  useRoutineStore: () => ({
    sendMyPlan: jest.fn(),
    consumePendingPlan: jest.fn(() => null),
    loading: false,
  }),
}));

jest.mock('../constants/avatar', () => ({
  AVATAR_3D_ENABLED: false,
  AVATAR_SPIN_SPEED: 0.45,
  AVATAR_VIEWPORT_HEIGHT: 300,
}));

jest.mock('../services/api', () => ({
  outfitAPI: {
    getSuggestion: jest.fn().mockResolvedValue({
      title: "Today's outfit suggestion",
      top: { name: 'Blue Shirt' },
      bottom: { name: 'Black Jeans' },
      shoes: { name: 'White Sneakers' },
      alternatives: [],
    }),
    plan: jest.fn().mockResolvedValue({ activities: [] }),
  },
  closetAPI: {
    wear: jest.fn(),
  },
  socialAPI: {
    createPost: jest.fn(),
  },
}));

describe('HomeScreen', () => {
  it('renders generator and greeting', () => {
    const { getByText } = render(<HomeScreen />);
    expect(getByText('DRESSEDUP')).toBeTruthy();
    expect(getByText(/Good morning, Test/)).toBeTruthy();
    expect(getByText("Today's look")).toBeTruthy();
  });
});

