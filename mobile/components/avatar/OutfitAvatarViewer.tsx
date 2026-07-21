import React, { Component, ReactNode, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Canvas } from '@react-three/fiber/native';

import { AVATAR_VIEWPORT_HEIGHT } from '../../constants/avatar';
import { THEME, FONTS } from '../../constants/theme';
import { MannequinScene } from './MannequinScene';

type ViewerProps = {
  avatarUrl?: string | null;
  topUri?: string | null;
  bottomUri?: string | null;
  shoesUri?: string | null;
  outerUri?: string | null;
  topSubcategory?: string | null;
  bottomSubcategory?: string | null;
  shoesSubcategory?: string | null;
  outerSubcategory?: string | null;
  topCategory?: string | null;
  topColor?: string;
  bottomColor?: string;
  shoesColor?: string;
  outerColor?: string;
  onFailed?: () => void;
};

type ErrorBoundaryProps = {
  children: ReactNode;
  onError: () => void;
  fallback: ReactNode;
};

type ErrorBoundaryState = { failed: boolean };

class AvatarErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { failed: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { failed: true };
  }

  componentDidCatch() {
    this.props.onError();
  }

  render() {
    if (this.state.failed) return this.props.fallback;
    return this.props.children;
  }
}

export function OutfitAvatarViewer({
  avatarUrl,
  topUri,
  bottomUri,
  shoesUri,
  outerUri,
  topSubcategory,
  bottomSubcategory,
  shoesSubcategory,
  outerSubcategory,
  topCategory,
  topColor,
  bottomColor,
  shoesColor,
  outerColor,
  onFailed,
}: ViewerProps) {
  const [paused, setPaused] = useState(false);
  const [glFailed, setGlFailed] = useState(false);

  if (glFailed) return null;

  return (
    <View style={styles.wrap}>
      <Pressable onPress={() => setPaused((p) => !p)} style={styles.canvasTap}>
        <AvatarErrorBoundary onError={() => { setGlFailed(true); onFailed?.(); }} fallback={null}>
          <Canvas
            style={styles.canvas}
            camera={{ position: [0, 0.88, 3.35], fov: 34 }}
            gl={{ antialias: true }}
            onCreated={({ gl, camera }) => {
              gl.setClearColor(THEME.editorial.background);
              camera.lookAt(0, 0.84, 0);
            }}
          >
            <ambientLight intensity={0.62} />
            <directionalLight position={[2.4, 4.4, 2.6]} intensity={1.35} />
            <directionalLight position={[-2.6, 2.4, 1.4]} intensity={0.55} color="#FFF5EA" />
            <directionalLight position={[0.2, 2.8, -3.4]} intensity={0.7} color="#E6ECF3" />
            <hemisphereLight args={['#F5F7F9', '#C8D0D8', 0.42]} />
            <MannequinScene
              avatarUrl={avatarUrl}
              topUri={topUri}
              bottomUri={bottomUri}
              shoesUri={shoesUri}
              outerUri={outerUri}
              topSubcategory={topSubcategory}
              bottomSubcategory={bottomSubcategory}
              shoesSubcategory={shoesSubcategory}
              outerSubcategory={outerSubcategory}
              topCategory={topCategory}
              topColor={topColor}
              bottomColor={bottomColor}
              shoesColor={shoesColor}
              outerColor={outerColor}
              paused={paused}
              onRpmFailed={onFailed}
            />
          </Canvas>
        </AvatarErrorBoundary>
      </Pressable>
      <Text style={styles.hint}>{paused ? 'Tap to resume' : 'Tap to pause · today\'s fit'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    marginBottom: 8,
  },
  canvasTap: {
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: THEME.editorial.background,
    borderWidth: 1,
    borderColor: THEME.editorial.border,
  },
  canvas: {
    width: '100%',
    height: AVATAR_VIEWPORT_HEIGHT,
  },
  hint: {
    marginTop: 8,
    fontSize: 12,
    color: THEME.editorial.textMuted,
    textAlign: 'center',
    fontFamily: FONTS.sans,
  },
});
