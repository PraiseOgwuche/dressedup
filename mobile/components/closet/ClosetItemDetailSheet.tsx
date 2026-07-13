import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { mediaUrl, TAXONOMY } from '../../constants/config';
import { THEME, FONTS, SHADOW, utilityTitle } from '../../constants/theme';
import { closetAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { ClosetItem, ClosetItemContext } from '../../types';
import { Button } from '../ui/Button';
import { ChipSelect } from '../ui/ChipSelect';

type Props = {
  visible: boolean;
  item: ClosetItem | null;
  onClose: () => void;
  onEdit: (item: ClosetItem) => void;
  onWear: (item: ClosetItem) => Promise<void> | void;
  onSoilOrWash: (item: ClosetItem) => Promise<void> | void;
  onTagsChange: (item: ClosetItem, tags: string[]) => Promise<void> | void;
};

function wearLine(item: ClosetItem): string {
  const limit = item.effective_wear_limit;
  const worn = `Worn ${item.times_worn}×`;
  if (limit == null) return `${worn} · not laundered by wear`;
  return `${worn} · ${item.wears_since_wash}/${limit} since wash`;
}

function pieceLabel(piece?: ClosetItem | null): string {
  if (!piece) return '—';
  return piece.name;
}

export function ClosetItemDetailSheet({
  visible,
  item,
  onClose,
  onEdit,
  onWear,
  onSoilOrWash,
  onTagsChange,
}: Props) {
  const [context, setContext] = useState<ClosetItemContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!visible || !item) {
      setContext(null);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    closetAPI
      .getContext(item.id)
      .then((data) => {
        if (!cancelled) setContext(data);
      })
      .catch((err) => {
        if (!cancelled) setError(getApiErrorMessage(err, 'Could not load item details.'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [visible, item?.id]);

  if (!item) return null;

  const display = context?.item ?? item;
  const thumb = mediaUrl(display.thumbnail_url ?? display.image_url);
  const cutout = Boolean(display.thumbnail_url?.includes('/cutouts/'));
  const tags = display.tags ?? [];
  const pair = context?.pair_preview;

  const run = async (action: () => Promise<void> | void) => {
    setBusy(true);
    try {
      await action();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={styles.container}>
        <ScrollView contentContainerStyle={styles.content}>
          <Pressable onPress={onClose} style={styles.closeLink}>
            <Text style={styles.closeText}>Close</Text>
          </Pressable>

          <View style={[styles.hero, cutout && styles.heroCutout]}>
            {thumb ? (
              <Image source={{ uri: thumb }} style={styles.heroImage} resizeMode={cutout ? 'contain' : 'cover'} />
            ) : (
              <View style={styles.heroPlaceholder}>
                <Text style={styles.heroEmoji}>👕</Text>
              </View>
            )}
          </View>

          <Text style={styles.title}>{display.name}</Text>
          <Text style={styles.meta}>
            {[display.brand, display.subcategory ?? display.category, display.color]
              .filter(Boolean)
              .join(' · ')}
          </Text>
          <Text style={styles.wear}>{wearLine(display)}</Text>
          <Text style={styles.status}>{display.is_clean ? 'Clean' : 'In the hamper'}</Text>

          {loading ? (
            <ActivityIndicator style={{ marginVertical: 16 }} color={THEME.brand.ink} />
          ) : null}
          {error ? <Text style={styles.error}>{error}</Text> : null}

          {context ? (
            <View style={styles.usageCard}>
              <Text style={styles.sectionLabel}>In your looks</Text>
              <Text style={styles.usageText}>
                {context.usage.looks_count === 0
                  ? 'Not in saved looks or posts yet — pair it below to start.'
                  : `Used in ${context.usage.looks_count} look${context.usage.looks_count === 1 ? '' : 's'}` +
                    (context.usage.signal_count
                      ? ` · ${context.usage.signal_count} style signal${context.usage.signal_count === 1 ? '' : 's'}`
                      : '')}
              </Text>
              {context.slot ? (
                <Text style={styles.slotBadge}>Slot · {context.slot}</Text>
              ) : null}
            </View>
          ) : null}

          {pair ? (
            <View style={styles.pairCard}>
              <Text style={styles.sectionLabel}>Pair with</Text>
              <Text style={styles.pairTitle}>{pair.title}</Text>
              {pair.rationale ? <Text style={styles.pairBody}>{pair.rationale}</Text> : null}
              <Text style={styles.pairLine}>Top · {pieceLabel(pair.top)}</Text>
              <Text style={styles.pairLine}>Bottom · {pieceLabel(pair.bottom)}</Text>
              <Text style={styles.pairLine}>Shoes · {pieceLabel(pair.shoes)}</Text>
              {pair.outerwear ? (
                <Text style={styles.pairLine}>Layer · {pieceLabel(pair.outerwear)}</Text>
              ) : null}
            </View>
          ) : null}

          <Text style={styles.sectionLabel}>Capsules</Text>
          <Text style={styles.hint}>Soft groups like Travel or Work — tap to toggle.</Text>
          <ChipSelect
            options={TAXONOMY.capsules}
            selected={tags}
            onSelect={(value) => {
              const next = tags.includes(value)
                ? tags.filter((t) => t !== value)
                : [...tags, value];
              run(() => onTagsChange(display, next));
            }}
            multiple
          />

          <View style={styles.actions}>
            <Button
              title="Wore it today"
              variant="outline"
              disabled={busy}
              onPress={() => run(() => onWear(display))}
              style={styles.actionBtn}
            />
            <Button
              title={display.is_clean ? 'Mark dirty' : 'Mark clean'}
              variant="secondary"
              disabled={busy}
              onPress={() => run(() => onSoilOrWash(display))}
              style={styles.actionBtn}
            />
          </View>
          <Button title="Edit details" onPress={() => onEdit(display)} />
        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.utility.background },
  content: { padding: 22, paddingBottom: 40, gap: 10 },
  closeLink: { alignSelf: 'flex-start', marginBottom: 4 },
  closeText: { fontSize: 15, fontWeight: '600', color: THEME.editorial.accentDark },
  hero: {
    width: '100%',
    aspectRatio: 3 / 4,
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: THEME.editorial.pill,
    marginBottom: 8,
    ...SHADOW.soft,
  },
  heroCutout: { backgroundColor: THEME.brand.sand, padding: 16 },
  heroImage: { width: '100%', height: '100%' },
  heroPlaceholder: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  heroEmoji: { fontSize: 64 },
  title: { ...utilityTitle(26), textAlign: 'left' },
  meta: { fontSize: 14, color: THEME.utility.textMuted, textTransform: 'capitalize' },
  wear: { fontSize: 13, fontWeight: '600', color: THEME.utility.text },
  status: { fontSize: 12, fontWeight: '700', color: THEME.editorial.accentDark, textTransform: 'uppercase' },
  error: { color: THEME.shared.error, fontSize: 13 },
  sectionLabel: {
    marginTop: 10,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
  },
  hint: { fontSize: 13, color: THEME.utility.textMuted, marginBottom: 4 },
  usageCard: {
    backgroundColor: THEME.utility.surfaceMuted,
    borderRadius: 16,
    padding: 14,
    gap: 6,
  },
  usageText: { fontSize: 14, lineHeight: 20, color: THEME.utility.text },
  slotBadge: {
    alignSelf: 'flex-start',
    marginTop: 4,
    fontSize: 11,
    fontWeight: '700',
    color: THEME.brand.ink,
    textTransform: 'uppercase',
  },
  pairCard: {
    backgroundColor: THEME.brand.sand,
    borderRadius: 16,
    padding: 14,
    gap: 4,
    ...SHADOW.soft,
  },
  pairTitle: { fontFamily: FONTS.sans, fontSize: 16, fontWeight: '700', color: THEME.utility.text },
  pairBody: { fontSize: 13, lineHeight: 18, color: THEME.utility.textMuted, marginBottom: 6 },
  pairLine: { fontSize: 13, color: THEME.utility.text },
  actions: { flexDirection: 'row', gap: 10, marginTop: 8, marginBottom: 8 },
  actionBtn: { flex: 1 },
});
