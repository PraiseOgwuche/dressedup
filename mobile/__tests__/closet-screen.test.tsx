import React from 'react';
import { render } from '@testing-library/react-native';

import ClosetScreen from '../app/(tabs)/closet';

jest.mock('expo-router', () => ({
  useFocusEffect: jest.fn(),
}));

jest.mock('../store/closetStore', () => ({
  useClosetStore: () => ({
    items: [],
    laundry: null,
    isLoading: false,
    fetchItems: jest.fn(),
    fetchLaundry: jest.fn(),
    wearItem: jest.fn(),
    washItem: jest.fn(),
    soilItem: jest.fn(),
    washAll: jest.fn(),
    createItem: jest.fn(),
    updateItem: jest.fn(),
    deleteItem: jest.fn(),
  }),
}));

describe('ClosetScreen', () => {
  it('renders empty closet state', () => {
    const { getByText } = render(<ClosetScreen />);
    expect(getByText('Your closet is empty')).toBeTruthy();
    expect(getByText('Add Item')).toBeTruthy();
  });
});

