import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { THEME, utilityTitle, SHADOW } from '../../constants/theme';

type Props = {
  title: string;
  subtitle?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
};

export function CollapsibleSection({ title, subtitle, defaultOpen = false, children }: Props) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <View style={styles.wrap}>
      <Pressable style={styles.header} onPress={() => setOpen((v) => !v)}>
        <View style={styles.headerText}>
          <Text style={styles.title}>{title}</Text>
          {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
        </View>
        <Text style={styles.chevron}>{open ? '−' : '+'}</Text>
      </Pressable>
      {open ? <View style={styles.body}>{children}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: THEME.utility.surface,
    borderRadius: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    ...SHADOW.soft,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  headerText: { flex: 1, paddingRight: 12 },
  title: utilityTitle(17),
  subtitle: { fontSize: 13, color: THEME.utility.textMuted, marginTop: 4, lineHeight: 18 },
  chevron: { fontSize: 22, fontWeight: '300', color: THEME.brand.ink },
  body: { paddingHorizontal: 16, paddingBottom: 16 },
});
