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
            camera={{ position: [0, 1.05, 3.1], fov: 38 }}
            gl={{ antialias: true }}
            onCreated={({ gl, camera }) => {
              gl.setClearColor('#F7F3EE');
              camera.lookAt(0, 0.88, 0);
            }}
          >
            {/* Soft three-point studio lighting */}
            <ambientLight intensity={0.55} />
            <directionalLight position={[2.5, 4, 3]} intensity={1.5} />
            <directionalLight position={[-3, 2.5, 1]} intensity={0.6} color="#FFF4E6" />
            <directionalLight position={[0, 3, -4]} intensity={0.8} color="#E8EEF5" />
            <MannequinScene
              topUri={topUri}
              bottomUri={bottomUri}
              shoesUri={shoesUri}
              outerUri={outerUri}
              topSubcategory={topSubcategory}
              bottomSubcategory={bottomSubcategory}
              shoesSubcategory={shoesSubcategory}
              outerSubcategory={outerSubcategory}
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
