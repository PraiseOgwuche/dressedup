import React from 'react';
import { StyleProp, ViewStyle } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { THEME } from '../constants/theme';

/**
 * DressedUp mark — hanger hook forms a D, spread collar on the bar.
 * viewBox 0 0 80 80
 */
const HANGER =
  'M 40 6 V 14 C 40 14 18 15 13 31 C 8 45 18 56 32 56 H 62';

const COLLAR =
  'M 27 56 L 40 78 L 53 56 M 27 56 Q 40 63 53 56';

type Props = {
  size?: number;
  color?: string;
  strokeWidth?: number;
  style?: StyleProp<ViewStyle>;
};

function strokeForSize(size: number) {
  if (size <= 30) return 3.2;
  if (size <= 48) return 2.8;
  if (size <= 80) return 2.5;
  return 2.2;
}

export function LogoMark({
  size = 64,
  color = THEME.brand.ink,
  strokeWidth,
  style,
}: Props) {
  const stroke = strokeWidth ?? strokeForSize(size);

  return (
    <Svg width={size} height={size} viewBox="0 0 80 80" style={style}>
      <Path
        d={HANGER}
        stroke={color}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <Path
        d={COLLAR}
        stroke={color}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </Svg>
  );
}
