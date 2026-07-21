import { Platform, TextStyle, ViewStyle } from 'react-native';

/**
 * Paper & Ink — editorial restraint.
 * Ink near-black = primary actions. Cool paper vs white = zone (editorial vs utility).
 * Mist = muted fills (chips, inputs) — cool, never beige.
 * Ink-blue = the single accent: selected states, links, highlights. Used rarely, like printing ink.
 */
export const THEME = {
  /** Shared tokens — the app's visual signature */
  brand: {
    ink: '#0E1116',
    paper: '#EEF0F2',
    mist: '#E4E8EC',
    mistLight: '#F3F5F7',
    accent: '#1F3A5F',
    accentDark: '#16293F',
    white: '#FFFFFF',
  },
  editorial: {
    background: '#EEF0F2',
    surface: '#FFFFFF',
    text: '#0E1116',
    textMuted: '#5C6570',
    accent: '#1F3A5F',
    accentDark: '#16293F',
    border: '#DDE2E7',
    pill: '#E4E8EC',
  },
  utility: {
    background: '#FFFFFF',
    surface: '#FFFFFF',
    surfaceMuted: '#F3F5F7',
    text: '#0E1116',
    textMuted: '#5C6570',
    accent: '#1F3A5F',
    accentSoft: '#E7EDF5',
    border: '#E2E6EA',
  },
  shared: {
    success: '#2F6B4F',
    error: '#B4433F',
    warning: '#A8721C',
    white: '#FFFFFF',
  },
} as const;

export const FONTS = {
  serif: Platform.select({ ios: 'Georgia', android: 'serif', default: 'serif' }) as string,
  sans: Platform.select({ ios: 'System', android: 'sans-serif', default: 'System' }) as string,
};

export const SHADOW = {
  soft: {
    shadowColor: '#0E1116',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 14,
    elevation: 3,
  } satisfies ViewStyle,
  lift: {
    shadowColor: '#0E1116',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.1,
    shadowRadius: 20,
    elevation: 5,
  } satisfies ViewStyle,
};

/** Serif is reserved for the brand wordmark only (splash, auth logo). */
export const brandWordmark = (size = 40): TextStyle => ({
  fontFamily: FONTS.serif,
  fontSize: size,
  fontWeight: '400',
  color: THEME.editorial.text,
  letterSpacing: -0.5,
});

/** Editorial-zone titles — strong sans, tight tracking. */
export const editorialTitle = (size = 28): TextStyle => ({
  fontFamily: FONTS.sans,
  fontSize: size,
  fontWeight: '700',
  color: THEME.editorial.text,
  letterSpacing: -0.6,
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
