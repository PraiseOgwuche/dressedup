import React, { useEffect, useRef, useState } from 'react';
import { Animated, StyleSheet, Text, View } from 'react-native';
import * as SplashScreen from 'expo-splash-screen';

import { THEME, brandWordmark } from '../constants/theme';

const WORD = 'DressedUp';
const LETTER_MS = 72;
const HOLD_AFTER_MS = 700;

type Props = {
  authReady: boolean;
  onFinish: () => void;
};

export function BrandSplash({ authReady, onFinish }: Props) {
  const [letterCount, setLetterCount] = useState(0);
  const [showRule, setShowRule] = useState(false);
  const [showTagline, setShowTagline] = useState(false);
  const [animDone, setAnimDone] = useState(false);
  const fade = useRef(new Animated.Value(1)).current;
  const ruleOpacity = useRef(new Animated.Value(0)).current;
  const taglineOpacity = useRef(new Animated.Value(0)).current;
  const finished = useRef(false);

  // Hide native splash as soon as this screen mounts — same paper bg, one continuous page.
  useEffect(() => {
    SplashScreen.hideAsync().catch(() => {});
  }, []);

  // Letter-by-letter typewriter
  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    for (let i = 1; i <= WORD.length; i += 1) {
      timers.push(
        setTimeout(() => setLetterCount(i), i * LETTER_MS),
      );
    }

    const afterWord = WORD.length * LETTER_MS + 120;
    timers.push(
      setTimeout(() => {
        setShowRule(true);
        Animated.timing(ruleOpacity, {
          toValue: 1,
          duration: 320,
          useNativeDriver: true,
        }).start();
      }, afterWord),
    );

    timers.push(
      setTimeout(() => {
        setShowTagline(true);
        Animated.timing(taglineOpacity, {
          toValue: 1,
          duration: 420,
          useNativeDriver: true,
        }).start(() => setAnimDone(true));
      }, afterWord + 280),
    );

    return () => timers.forEach(clearTimeout);
  }, [ruleOpacity, taglineOpacity]);

  // Exit once auth is ready and intro animation has finished
  useEffect(() => {
    if (!authReady || !animDone || finished.current) return;

    const timer = setTimeout(() => {
      if (finished.current) return;
      finished.current = true;
      Animated.timing(fade, {
        toValue: 0,
        duration: 320,
        useNativeDriver: true,
      }).start(({ finished: done }) => {
        if (done) onFinish();
      });
    }, HOLD_AFTER_MS);

    return () => clearTimeout(timer);
  }, [authReady, animDone, fade, onFinish]);

  return (
    <View style={styles.container}>
      <Animated.View style={[styles.content, { opacity: fade }]}>
        <Text style={styles.wordmark} accessibilityRole="header">
          {WORD.slice(0, letterCount)}
        </Text>

        {showRule ? (
          <Animated.View style={[styles.rule, { opacity: ruleOpacity }]} />
        ) : (
          <View style={styles.rulePlaceholder} />
        )}

        {showTagline ? (
          <Animated.Text style={[styles.tagline, { opacity: taglineOpacity }]}>
            Your personal wardrobe assistant.
          </Animated.Text>
        ) : null}
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.editorial.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  wordmark: {
    ...brandWordmark(44),
    textAlign: 'center',
    minHeight: 52,
  },
  rulePlaceholder: {
    width: 56,
    height: 1,
    marginTop: 18,
    marginBottom: 18,
  },
  rule: {
    width: 56,
    height: 1,
    backgroundColor: THEME.editorial.accent,
    marginTop: 18,
    marginBottom: 18,
  },
  tagline: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 1.6,
    textTransform: 'uppercase',
    color: THEME.editorial.textMuted,
    textAlign: 'center',
    lineHeight: 22,
  },
});
