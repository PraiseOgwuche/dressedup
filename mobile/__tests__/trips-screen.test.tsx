import React from 'react';
import { render } from '@testing-library/react-native';

import TripsScreen from '../app/(tabs)/trips';

jest.mock('expo-router', () => {
  const React = require('react');
  return {
    useFocusEffect: (cb: () => void) => {
      React.useEffect(cb, [cb]);
    },
  };
});

jest.mock('../store/authStore', () => ({
  useAuthStore: (selector: (state: { user: { is_premium: boolean; premium_trial_ends_at: string } }) => unknown) =>
    selector({
      user: {
        is_premium: true,
        premium_trial_ends_at: '2099-01-01T00:00:00Z',
      },
    }),
}));

jest.mock('../services/api', () => ({
  tripsAPI: {
    listPlans: jest.fn().mockResolvedValue([]),
    getPacking: jest.fn(),
    reshuffleDay: jest.fn(),
    createPlan: jest.fn(),
    updatePlan: jest.fn(),
    deletePlan: jest.fn(),
  },
}));

describe('TripsScreen', () => {
  it('renders trips header', () => {
    const { getByText } = render(<TripsScreen />);
    expect(getByText('Trips')).toBeTruthy();
    expect(getByText('+ New trip')).toBeTruthy();
  });
});
