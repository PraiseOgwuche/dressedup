import React, { useMemo } from 'react';
import * as THREE from 'three';

import { getBodyGeometry, getGarmentGeometry } from './bakedAvatar';
import { FaceFeatures } from './FaceFeatures';
import { RpmAvatar } from './RpmAvatar';

export { AVATAR_HEIGHT as HUMANOID_HEIGHT } from './bakedAvatar';

type Props = {
  avatarUrl?: string | null;
  onRpmFailed?: () => void;
};

/**
 * Loads a personalized GLB when `avatarUrl` is set; otherwise the baked mannequin.
 */
export function HumanoidBody({ avatarUrl, onRpmFailed }: Props) {
  const bodyGeo = getBodyGeometry();
  const hairGeo = getGarmentGeometry('hair');

  const skin = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#C99574',
        roughness: 0.62,
        metalness: 0.02,
      }),
    [],
  );

  const hair = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#4A372C',
        roughness: 0.88,
        metalness: 0.01,
      }),
    [],
  );

  if (avatarUrl) {
    return <RpmAvatar url={avatarUrl} onFailed={onRpmFailed} />;
  }

  return (
    <group>
      <mesh geometry={bodyGeo} material={skin} />
      <mesh geometry={hairGeo} material={hair} />
      <FaceFeatures />
    </group>
  );
}
