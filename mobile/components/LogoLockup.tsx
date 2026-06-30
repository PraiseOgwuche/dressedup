import React from 'react';
import { StyleProp, StyleSheet, Text, View, ViewStyle } from 'react-native';

import { THEME } from '../constants/theme';
import { LogoMark } from './LogoMark';

type Props = {
  size?: 'sm' | 'md' | 'lg' | 'splash';
  showWordmark?: boolean;
  color?: string;
  style?: StyleProp<ViewStyle>;
};

const MARK_SIZE = {
  sm: 34,
  md: 48,
  lg: 80,
  splash: 100,
} as const;

export function LogoLockup({
  size = 'md',
  showWordmark = true,
  color = THEME.brand.ink,
  style,
}: Props) {
  const markSize = MARK_SIZE[size];
  const wordmarkStyle =
    size === 'splash' ? styles.wordmarkSplash : size === 'lg' ? styles.wordmarkLg : styles.wordmark;

  return (
    <View
      style={[styles.wrap, style]}
      accessibilityRole="image"
      accessibilityLabel="DressedUp"
    >
      <LogoMark size={markSize} color={color} />
      {showWordmark ? (
        <Text style={[wordmarkStyle, { color: THEME.editorial.accentDark }]}>DRESSEDUP</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { alignItems: 'center' },
  wordmark: {
    marginTop: 8,
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 3.2,
  },
  wordmarkLg: {
    marginTop: 14,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 4,
  },
  wordmarkSplash: {
    marginTop: 20,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 4.5,
  },
});
