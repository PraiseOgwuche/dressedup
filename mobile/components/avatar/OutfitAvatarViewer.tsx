import React, { Component, ReactNode, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Canvas } from '@react-three/fiber/native';

import { AVATAR_VIEWPORT_HEIGHT } from '../../constants/avatar';
import { THEME, FONTS } from '../../constants/theme';
import { MannequinScene } from './MannequinScene';

type ViewerProps = {
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
            camera={{ position: [0, 0.9, 2.75], fov: 35 }}
            gl={{ antialias: true }}
            onCreated={({ gl, camera }) => {
              gl.setClearColor('#F4F2EE');
              camera.lookAt(0, 0.8, 0);
            }}
          >
            <ambientLight intensity={0.58} />
            <directionalLight position={[2.4, 4.4, 2.6]} intensity={1.4} />
            <directionalLight position={[-2.6, 2.4, 1.4]} intensity={0.5} color="#FFF5EA" />
            <directionalLight position={[0.2, 2.8, -3.4]} intensity={0.75} color="#E6ECF3" />
            <hemisphereLight args={['#FAF8F4', '#D2CCC2', 0.4]} />
            <MannequinScene
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
            />
          </Canvas>
        </AvatarErrorBoundary>
      </Pressable>
      <Text style={styles.hint}>{paused ? 'Tap to resume spin' : 'Tap to pause · today\'s fit on mannequin'}</Text>
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
