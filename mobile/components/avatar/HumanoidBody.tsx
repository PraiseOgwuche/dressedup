import React, { useMemo } from 'react';
import * as THREE from 'three';

import { getBodyGeometry, getGarmentGeometry } from './bakedAvatar';

export { AVATAR_HEIGHT as HUMANOID_HEIGHT } from './bakedAvatar';

/**
 * The human base body + a soft hair cap, pre-baked by scripts/bake-avatar.js.
 */
export function HumanoidBody() {
  const bodyGeo = getBodyGeometry();
  const hairGeo = getGarmentGeometry('hair');

  const skin = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#C48A68',
        roughness: 0.58,
        metalness: 0.03,
      }),
    [],
  );

  const hair = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#2A2420',
        roughness: 0.9,
        metalness: 0.02,
      }),
    [],
  );

  return (
    <group>
      <mesh geometry={bodyGeo} material={skin} />
      <mesh geometry={hairGeo} material={hair} />
    </group>
  );
}
