import { Platform, TextStyle, ViewStyle } from 'react-native';

/**
 * Design D — Hybrid, unified.
 * Ink black = primary actions everywhere. Cream vs white = zone (editorial vs utility).
 * Warm sand = muted fills (chips, inputs) — never cold grey.
 */
export const THEME = {
  /** Shared tokens — the app's visual signature */
  brand: {
    ink: '#1C1C1C',
    cream: '#F7F3EE',
    sand: '#EDE6DC',
    sandLight: '#F5F0E8',
    gold: '#B8956B',
    goldDark: '#8A7355',
    white: '#FFFFFF',
  },
  editorial: {
    background: '#F7F3EE',
    surface: '#FFFCF8',
    text: '#1C1C1C',
    textMuted: '#6B6560',
    accent: '#B8956B',
    accentDark: '#8A7355',
    border: '#E8E2D9',
    pill: '#EDE6DC',
  },
  utility: {
    background: '#FFFFFF',
    surface: '#FFFFFF',
    surfaceMuted: '#F5F0E8',
    text: '#1C1C1C',
    textMuted: '#6B6560',
    accent: '#1C1C1C',
    accentSoft: '#EDE6DC',
    border: '#E8E2D9',
  },
  shared: {
    success: '#4A7C59',
    error: '#C45C5C',
    warning: '#C4923A',
    white: '#FFFFFF',
  },
} as const;

export const FONTS = {
  serif: Platform.select({ ios: 'Georgia', android: 'serif', default: 'serif' }) as string,
  sans: Platform.select({ ios: 'System', android: 'sans-serif', default: 'System' }) as string,
};

export const SHADOW = {
  soft: {
    shadowColor: '#1C1C1C',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 14,
    elevation: 3,
  } satisfies ViewStyle,
  lift: {
    shadowColor: '#1C1C1C',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 20,
    elevation: 5,
  } satisfies ViewStyle,
};

export const editorialTitle = (size = 28): TextStyle => ({
  fontFamily: FONTS.serif,
  fontSize: size,
  fontWeight: '400',
  color: THEME.editorial.text,
  letterSpacing: -0.5,
});

export const utilityTitle = (size = 22): TextStyle => ({
  fontFamily: FONTS.sans,
  fontSize: size,
  fontWeight: '700',
  color: THEME.utility.text,
  letterSpacing: -0.3,
});

export const sectionLabel = (): TextStyle => ({
  fontSize: 11,
  fontWeight: '700',
  color: THEME.utility.textMuted,
  letterSpacing: 1.2,
  textTransform: 'uppercase',
});
