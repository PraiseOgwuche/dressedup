import React, { useMemo } from 'react';
import * as THREE from 'three';

import { getBodyGeometry } from './bakedAvatar';

const SKIN_COLOR = '#D9A57E';

export { AVATAR_HEIGHT as HUMANOID_HEIGHT } from './bakedAvatar';

/**
 * The human base body, pre-baked to static geometry (1.72m tall, feet at
 * y=0, facing +Z) by scripts/bake-avatar.js — no GLTF parsing at runtime.
 */
export function HumanoidBody() {
  const geometry = getBodyGeometry();
  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: SKIN_COLOR,
        roughness: 0.55,
        metalness: 0.02,
      }),
    [],
  );

  return <mesh geometry={geometry} material={material} />;
}
