import React from 'react';
import {
  Linking,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { FONTS, THEME } from '../../constants/theme';
import { Button } from '../ui/Button';

type Props = {
  visible: boolean;
  onClose: () => void;
  /** Reserved for a future avatar provider export callback. */
  onExported?: (avatarUrl: string) => void;
};

/**
 * Personalized avatar creation is temporarily unavailable.
 * Ready Player Me ended public services in January 2026; the classic mannequin remains the default.
 */
export function AvatarCreatorModal({ visible, onClose }: Props) {
  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <View style={styles.header}>
          <Text style={styles.title}>3D avatar</Text>
          <Pressable onPress={onClose} hitSlop={12}>
            <Text style={styles.close}>Close</Text>
          </Pressable>
        </View>

        <View style={styles.body}>
          <Text style={styles.headline}>Avatar creation unavailable</Text>
          <Text style={styles.copy}>
            The previous third-party avatar creator shut down in January 2026.
            Personalized selfie avatars cannot be created until a new provider is integrated.
          </Text>
          <Text style={styles.copy}>
            Today uses the classic mannequin in the meantime. Your closet colors and outfit
            shells continue to work as usual.
          </Text>

          <Button title="Continue with mannequin" onPress={onClose} style={styles.btn} />
          <Button
            title="Learn more"
            variant="outline"
            onPress={() => {
              Linking.openURL(
                'https://avatarsdk.com/blog/2026/01/15/switch-from-ready-player-me-to-avatar-sdk-fast-familiar-production-ready/',
              ).catch(() => undefined);
            }}
            style={styles.btn}
          />
        </View>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: THEME.editorial.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  title: {
    fontFamily: FONTS.sans,
    fontWeight: '700',
    fontSize: 18,
    color: THEME.editorial.text,
  },
  close: {
    fontFamily: FONTS.sans,
    fontSize: 16,
    color: THEME.editorial.accent,
  },
  body: {
    flex: 1,
    paddingHorizontal: 22,
    paddingTop: 24,
    gap: 14,
  },
  headline: {
    fontFamily: FONTS.sans,
    fontWeight: '700',
    fontSize: 22,
    color: THEME.editorial.text,
  },
  copy: {
    fontFamily: FONTS.sans,
    fontSize: 15,
    lineHeight: 22,
    color: THEME.editorial.textMuted,
  },
  btn: { width: '100%', marginTop: 4 },
});
