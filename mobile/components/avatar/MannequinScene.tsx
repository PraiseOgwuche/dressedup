import React, { Suspense, useRef } from 'react';
import { useFrame } from '@react-three/fiber/native';
import * as THREE from 'three';

import { AVATAR_SPIN_SPEED } from '../../constants/avatar';
import { HumanoidBody } from './HumanoidBody';
import { GarmentShell, topShellFor, bottomShellFor, isDressCategory } from './garmentShells';

export type MannequinSceneProps = {
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
  paused?: boolean;
  onRpmFailed?: () => void;
};

function SoftContactShadow() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.009, 0]} renderOrder={-1}>
      <circleGeometry args={[0.3, 48]} />
      <meshBasicMaterial color="#1A1A1A" transparent opacity={0.18} depthWrite={false} />
    </mesh>
  );
}

function Pedestal() {
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.001, 0]}>
        <circleGeometry args={[0.5, 64]} />
        <meshStandardMaterial color="#E8ECF0" roughness={0.94} metalness={0.01} />
      </mesh>
      <mesh position={[0, -0.015, 0]}>
        <cylinderGeometry args={[0.5, 0.54, 0.03, 64]} />
        <meshStandardMaterial color="#D5DBE2" roughness={0.9} metalness={0.01} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.002, 0]}>
        <ringGeometry args={[0.475, 0.5, 64]} />
        <meshStandardMaterial color="#C5CDD6" roughness={0.85} metalness={0.04} />
      </mesh>
      <SoftContactShadow />
    </group>
  );
}

function RotatingOutfit({
  avatarUrl,
  topUri,
  bottomUri,
  shoesUri,
  outerUri,
  topSubcategory,
  bottomSubcategory,
  topCategory,
  topColor = '#6B7686',
  bottomColor = '#3E4A5A',
  shoesColor = '#2A2E35',
  outerColor = '#54606E',
  paused = false,
  onRpmFailed,
}: MannequinSceneProps) {
  const group = useRef<THREE.Group>(null);
  const idle = useRef(0);

  useFrame((_, delta) => {
    if (!group.current || paused) return;
    group.current.rotation.y += delta * AVATAR_SPIN_SPEED;
    // Soft idle motion (breath + sway) until a rigged animation is available.
    idle.current += delta;
    const breath = Math.sin(idle.current * 1.55) * 0.012;
    const sway = Math.sin(idle.current * 0.65) * 0.018;
    group.current.position.y = breath;
    group.current.rotation.z = sway;
  });

  const dressLook = isDressCategory(topCategory, topSubcategory);
  const hasOuter = outerUri != null;
  const hasTop = topUri != null;
  const hasBottom = bottomUri != null && !dressLook;
  const hasShoes = shoesUri != null;
  const topShell = topShellFor(topSubcategory, topCategory);
  // Color shells always render so closet colors stay visible on any body mesh.
  const showShells = true;

  return (
    <group ref={group}>
      <Pedestal />
      <HumanoidBody avatarUrl={avatarUrl} onRpmFailed={onRpmFailed} />

      {showShells && hasBottom ? (
        <GarmentShell
          shell={bottomShellFor(bottomSubcategory)}
          color={bottomColor}
          roughness={0.86}
        />
      ) : null}
      {showShells && hasTop ? (
        <GarmentShell
          shell={topShell}
          color={topColor}
          roughness={dressLook ? 0.82 : 0.8}
        />
      ) : null}
      {showShells && hasOuter ? (
        <GarmentShell shell="outer" color={outerColor} roughness={0.7} />
      ) : null}
      {showShells && hasShoes ? (
        <GarmentShell shell="shoes" color={shoesColor} roughness={0.48} metalness={0.14} />
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
