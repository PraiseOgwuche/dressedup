import React, { useMemo } from 'react';
import * as THREE from 'three';

import { getGarmentGeometry, GarmentShellName } from './bakedAvatar';
import { useNativeTexture } from './useNativeTexture';

/**
 * Garment shells are slices of the actual body surface, inflated a few
 * millimeters along the vertex normals at bake time — so every garment
 * drapes perfectly over the avatar with no boxes or intersections.
 */

const TOP_SHELLS: Record<string, GarmentShellName> = {
  tank: 'tank',
  'tank-top': 'tank',
  'sports-bra': 'tank',
  vest: 'tank',
  camisole: 'tank',
  't-shirt': 'tee',
  tee: 'tee',
  polo: 'tee',
  'athletic-top': 'tee',
  jersey: 'tee',
  shirt: 'long',
  blouse: 'long',
  sweater: 'long',
  sweatshirt: 'long',
  hoodie: 'long',
  cardigan: 'long',
  turtleneck: 'long',
  'long-sleeve': 'long',
  tracksuit: 'long',
};

const SHORT_BOTTOMS = new Set([
  'shorts',
  'athletic-shorts',
  'board-shorts',
  'skirt',
  'mini',
  'midi',
]);

export function topShellFor(subcategory?: string | null): GarmentShellName {
  const key = (subcategory ?? '').toLowerCase();
  return TOP_SHELLS[key] ?? 'tee';
}

export function bottomShellFor(subcategory?: string | null): GarmentShellName {
  const key = (subcategory ?? '').toLowerCase();
  return SHORT_BOTTOMS.has(key) ? 'shorts' : 'pants';
}

/** True when the URI points at a background-removed cutout from the backend. */
export function isCutoutUri(uri?: string | null): boolean {
  if (!uri) return false;
  const lower = uri.toLowerCase();
  return lower.includes('/cutouts/') || lower.endsWith('.png');
}

type GarmentShellProps = {
  shell: GarmentShellName;
  color: string;
  /** Optional item photo, applied as a subtle fabric swatch over the color. */
  uri?: string | null;
  roughness?: number;
};

export function GarmentShell({ shell, color, uri, roughness = 0.82 }: GarmentShellProps) {
  const geometry = getGarmentGeometry(shell);
  const texture = useNativeTexture(uri);

  const material = useMemo(() => {
    const cutout = isCutoutUri(uri);
    if (texture) {
      texture.wrapS = THREE.ClampToEdgeWrapping;
      texture.wrapT = THREE.ClampToEdgeWrapping;
      if (cutout) {
        // Backend cutout: garment-only transparent PNG — map the full image.
        texture.repeat.set(1, 1);
        texture.offset.set(0, 0);
      } else {
        // Original flat-lay photo still has bed/floor — sample the center swatch.
        texture.repeat.set(0.42, 0.42);
        texture.offset.set(0.29, 0.29);
      }
      texture.needsUpdate = true;
      return new THREE.MeshStandardMaterial({
        map: texture,
        color: '#ffffff',
        roughness,
        metalness: 0,
        side: THREE.DoubleSide,
        transparent: cutout,
        alphaTest: cutout ? 0.06 : 0,
        depthWrite: !cutout,
      });
    }
    return new THREE.MeshStandardMaterial({
      color,
      roughness,
      metalness: 0,
      side: THREE.DoubleSide,
    });
  }, [texture, color, roughness]);

  return <mesh geometry={geometry} material={material} />;
}
