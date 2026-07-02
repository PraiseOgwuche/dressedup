import React from 'react';
import { render } from '@testing-library/react-native';

import ShopScreen from '../app/(tabs)/shop';

jest.mock('expo-router', () => {
  const React = require('react');
  return {
    useFocusEffect: (cb: () => void) => {
      React.useEffect(cb, [cb]);
    },
  };
});

jest.mock('../services/openUrl', () => ({
  openExternalUrl: jest.fn(),
}));

jest.mock('../services/api', () => ({
  shopAPI: {
    getRecommendations: jest.fn().mockResolvedValue({
      summary: 'Top pick ready',
      styling_insight: 'Add versatile bottoms to unlock more outfits.',
      recommendations: [],
    }),
  },
  marketplaceAPI: {
    browse: jest.fn().mockResolvedValue([]),
    mine: jest.fn().mockResolvedValue([]),
  },
  styleAPI: {
    track: jest.fn().mockResolvedValue(undefined),
  },
}));

describe('ShopScreen', () => {
  it('renders shop sections', () => {
    const { getByText } = render(<ShopScreen />);
    expect(getByText('Shop')).toBeTruthy();
    expect(getByText('New picks')).toBeTruthy();
    expect(getByText('Pass it on')).toBeTruthy();
  });
});
