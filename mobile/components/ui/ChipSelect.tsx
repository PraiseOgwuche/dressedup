import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { COLORS } from '../../constants/config';

type Props = {
  label?: string;
  options: string[];
  /** Selected value (single mode) or values (multiple mode). */
  selected?: string | string[];
  /** Called with the tapped option; parent decides set/toggle/clear. */
  onSelect: (value: string) => void;
  multiple?: boolean;
  hint?: string;
};

export function ChipSelect({ label, options, selected, onSelect, multiple, hint }: Props) {
  const isSelected = (option: string) =>
    Array.isArray(selected) ? selected.includes(option) : selected === option;

  return (
    <View style={styles.wrap}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
      <View style={styles.row}>
        {options.map((option) => {
          const active = isSelected(option);
          return (
            <Pressable
              key={option}
              onPress={() => onSelect(option)}
              style={[styles.chip, active && styles.chipActive]}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>{option}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { marginBottom: 16 },
  label: { fontSize: 14, fontWeight: '600', color: COLORS.text, marginBottom: 6 },
  hint: { fontSize: 12, color: COLORS.textLight, marginBottom: 8 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  chipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  chipText: { fontSize: 14, color: COLORS.text, textTransform: 'capitalize' },
  chipTextActive: { color: '#fff', fontWeight: '700' },
});
