import React, { useState } from 'react';
import {
  View,
  TextInput,
  Text,
  StyleSheet,
  TextInputProps,
  TouchableOpacity,
} from 'react-native';
import { THEME, sectionLabel } from '../../constants/theme';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  secureTextEntry?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  secureTextEntry,
  ...props
}) => {
  const [isSecure, setIsSecure] = useState(secureTextEntry);

  return (
    <View style={styles.container}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      <View style={styles.inputContainer}>
        <TextInput
          style={[styles.input, error && styles.inputError]}
          placeholderTextColor={THEME.utility.textMuted}
          secureTextEntry={isSecure}
          {...props}
        />
        {secureTextEntry ? (
          <TouchableOpacity
            style={styles.eyeIcon}
            onPress={() => setIsSecure(!isSecure)}
          >
            <Text style={styles.eyeText}>{isSecure ? 'Show' : 'Hide'}</Text>
          </TouchableOpacity>
        ) : null}
      </View>
      {error ? <Text style={styles.errorText}>{error}</Text> : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  label: {
    ...sectionLabel(),
    marginBottom: 8,
  },
  inputContainer: {
    position: 'relative',
  },
  input: {
    borderWidth: 1,
    borderColor: THEME.utility.border,
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 16,
    fontSize: 16,
    backgroundColor: THEME.editorial.pill,
    color: THEME.utility.text,
  },
  inputError: {
    borderColor: THEME.shared.error,
  },
  eyeIcon: {
    position: 'absolute',
    right: 16,
    top: 16,
  },
  eyeText: {
    fontSize: 13,
    fontWeight: '600',
    color: THEME.brand.ink,
  },
  errorText: {
    color: THEME.shared.error,
    fontSize: 12,
    marginTop: 4,
    marginLeft: 4,
  },
});
