import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { THEME, sectionLabel } from '../../constants/theme';

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

export function ChipSelect({ label, options, selected, onSelect, hint }: Props) {
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
  label: { ...sectionLabel(), marginBottom: 8 },
  hint: { fontSize: 12, color: THEME.utility.textMuted, marginBottom: 8 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: THEME.editorial.pill,
  },
  chipActive: { backgroundColor: THEME.brand.ink },
  chipText: { fontSize: 14, color: THEME.utility.text, textTransform: 'capitalize' },
  chipTextActive: { color: '#fff', fontWeight: '700' },
});
