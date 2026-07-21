import React, { useMemo } from 'react';
import * as THREE from 'three';

import { getGarmentGeometry, GarmentShellName } from './bakedAvatar';

/**
 * Garment shells are slices of the actual body surface, inflated along vertex
 * normals at bake time. We paint them as opaque fabric from the item color —
 * never as transparent flat-lay / cutout photos (those read as floating cards
 * on the mannequin). Real photos stay in the swap gallery below the avatar.
 */

const TOP_SHELLS: Record<string, GarmentShellName> = {
  tank: 'tank',
  'tank-top': 'tank',
  'sports-bra': 'tank',
  vest: 'tank',
  camisole: 'tank',
  't-shirt': 'tee',
  tee: 'tee',
  crewneck: 'tee',
  'crew-neck': 'tee',
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

const DRESS_SUBS = new Set([
  'dress',
  'midi',
  'maxi',
  'mini',
  'jumpsuit',
  'romper',
  'gown',
  'sundress',
]);

const SHORT_BOTTOMS = new Set([
  'shorts',
  'athletic-shorts',
  'board-shorts',
  'skirt',
  'drawstring',
  'drawstring-shorts',
  'chino-shorts',
  'denim-shorts',
  'mini',
]);

export function isDressCategory(category?: string | null, subcategory?: string | null): boolean {
  const cat = (category ?? '').toLowerCase();
  const sub = (subcategory ?? '').toLowerCase();
  return cat === 'dress' || cat === 'jumpsuit' || DRESS_SUBS.has(sub) || sub.includes('jumpsuit');
}

export function topShellFor(
  subcategory?: string | null,
  category?: string | null,
): GarmentShellName {
  if (isDressCategory(category, subcategory)) return 'dress';
  const key = (subcategory ?? '').toLowerCase();
  return TOP_SHELLS[key] ?? 'tee';
}

export function bottomShellFor(subcategory?: string | null): GarmentShellName {
  const key = (subcategory ?? '').toLowerCase();
  if (SHORT_BOTTOMS.has(key)) return 'shorts';
  if (key.includes('short') || key.includes('skirt')) return 'shorts';
  return 'pants';
}

type GarmentShellProps = {
  shell: GarmentShellName;
  color: string;
  /** Kept for API compatibility; photos are not UV-mapped onto shells. */
  uri?: string | null;
  roughness?: number;
  metalness?: number;
};

export function GarmentShell({
  shell,
  color,
  roughness = 0.78,
  metalness,
}: GarmentShellProps) {
  const geometry = getGarmentGeometry(shell);
  const metal = metalness ?? (shell === 'shoes' ? 0.12 : 0.02);

  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: color || '#888888',
        roughness,
        metalness: metal,
        side: THREE.FrontSide,
        depthWrite: true,
        polygonOffset: true,
        polygonOffsetFactor: shell === 'outer' ? -2 : -1,
        polygonOffsetUnits: shell === 'outer' ? -2 : -1,
      }),
    [color, roughness, metal, shell],
  );

  return <mesh geometry={geometry} material={material} />;
}
