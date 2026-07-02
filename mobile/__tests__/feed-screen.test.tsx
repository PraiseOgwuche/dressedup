import React from 'react';
import { render } from '@testing-library/react-native';

import FeedScreen from '../app/(tabs)/feed';

jest.mock('expo-router', () => {
  const React = require('react');
  return {
    useFocusEffect: (cb: () => void) => {
      React.useEffect(cb, [cb]);
    },
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
  },
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
