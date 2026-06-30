import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
} from 'react-native';
import { THEME } from '../../constants/theme';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'editorial' | 'editorialOutline';
  disabled?: boolean;
  loading?: boolean;
  style?: ViewStyle;
}

const INK = THEME.brand.ink;

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  disabled = false,
  loading = false,
  style,
}) => {
  const spinnerColor =
    variant === 'outline' || variant === 'editorialOutline' ? INK : '#fff';

  return (
    <TouchableOpacity
      style={[
        styles.button,
        styles[variant],
        disabled && styles.disabled,
        style,
      ]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.85}
    >
      {loading ? (
        <ActivityIndicator color={spinnerColor} />
      ) : (
        <Text style={[styles.text, styles[`${variant}Text` as keyof typeof styles]]}>
          {title}
        </Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    paddingVertical: 14,
    paddingHorizontal: 22,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 52,
  },
  primary: {
    backgroundColor: INK,
  },
  secondary: {
    backgroundColor: THEME.editorial.accentDark,
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: INK,
  },
  editorial: {
    backgroundColor: INK,
  },
  editorialOutline: {
    backgroundColor: THEME.brand.white,
    borderWidth: 1.5,
    borderColor: INK,
    marginTop: 10,
  },
  disabled: {
    opacity: 0.45,
  },
  text: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  primaryText: {
    color: '#fff',
  },
  secondaryText: {
    color: '#fff',
  },
  outlineText: {
    color: INK,
  },
  editorialText: {
    color: '#fff',
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  editorialOutlineText: {
    color: INK,
    fontWeight: '600',
  },
});
