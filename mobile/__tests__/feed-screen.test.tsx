import React from 'react';
import { render } from '@testing-library/react-native';

import FeedScreen from '../app/(tabs)/feed';

jest.mock('expo-router', () => {
  const React = require('react');
  return {
    useFocusEffect: (cb: () => void) => {
      React.useEffect(cb, [cb]);
    },
    useRouter: () => ({
      push: jest.fn(),
    }),
  };
});

jest.mock('../services/pushNotifications', () => ({
  getDeviceTimezone: () => 'UTC',
}));

jest.mock('../services/api', () => ({
  socialAPI: {
    listPosts: jest.fn().mockResolvedValue([]),
    getStreak: jest.fn().mockResolvedValue({
      current_streak: 0,
      longest_streak: 0,
      total_fit_days: 0,
      active_this_week: 0,
      timezone: 'UTC',
    }),
    getActivity: jest.fn().mockResolvedValue({ items: [], unread_count: 0 }),
    markActivitySeen: jest.fn().mockResolvedValue(undefined),
  },
}));

jest.mock('../store/feedActivityStore', () => ({
  useFeedActivityStore: (selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      items: [],
      loading: false,
      unreadCount: 0,
      refresh: jest.fn(),
      markSeen: jest.fn(),
    }),
}));

describe('FeedScreen', () => {
  it('renders feed header and scope tabs', () => {
    const { getByText } = render(<FeedScreen />);
    expect(getByText('Feed')).toBeTruthy();
    expect(getByText('All')).toBeTruthy();
    expect(getByText('Following')).toBeTruthy();
    expect(getByText('Yours')).toBeTruthy();
  });
});
