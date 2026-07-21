import React, { Suspense, useRef } from 'react';
import { useFrame } from '@react-three/fiber/native';
import * as THREE from 'three';

import { AVATAR_SPIN_SPEED } from '../../constants/avatar';
import { HumanoidBody } from './HumanoidBody';
import { GarmentShell, topShellFor, bottomShellFor } from './garmentShells';

export type MannequinSceneProps = {
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
  paused?: boolean;
};

function RotatingOutfit({
  topUri,
  bottomUri,
  shoesUri,
  outerUri,
  topSubcategory,
  bottomSubcategory,
  shoesSubcategory,
  outerSubcategory,
  topColor = '#6B7686',
  bottomColor = '#3E4A5A',
  shoesColor = '#2A2E35',
  outerColor = '#54606E',
  paused = false,
}: MannequinSceneProps) {
  const group = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (!group.current || paused) return;
    group.current.rotation.y += delta * AVATAR_SPIN_SPEED;
  });

  const hasOuter = Boolean(outerUri);

  return (
    <group ref={group}>
      {/* Pedestal */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.006, 0]}>
        <circleGeometry args={[0.55, 48]} />
        <meshStandardMaterial color="#E7DFD3" roughness={0.95} />
      </mesh>
      <mesh position={[0, -0.012, 0]}>
        <cylinderGeometry args={[0.55, 0.58, 0.035, 48]} />
        <meshStandardMaterial color="#D8CDBD" roughness={0.9} />
      </mesh>

      <HumanoidBody />

      {bottomUri ? (
        <GarmentShell
          shell={bottomShellFor(bottomSubcategory)}
          color={bottomColor}
          uri={bottomUri}
        />
      ) : null}
      {topUri ? (
        <GarmentShell shell={topShellFor(topSubcategory)} color={topColor} uri={topUri} />
      ) : null}
      {hasOuter ? (
        <GarmentShell shell="outer" color={outerColor} uri={outerUri} roughness={0.7} />
      ) : null}
      {shoesUri ? (
        <GarmentShell shell="shoes" color={shoesColor} uri={shoesUri} roughness={0.6} />
      ) : null}
    </group>
  );
}

export function MannequinScene(props: MannequinSceneProps) {
  return (
    <Suspense fallback={null}>
      <RotatingOutfit {...props} />
    </Suspense>
  );
}
