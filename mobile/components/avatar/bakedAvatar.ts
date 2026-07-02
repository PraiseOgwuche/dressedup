import * as THREE from 'three';

/**
 * Baked avatar geometry produced by `scripts/bake-avatar.js` from the CC0
 * base mesh (assets/avatar/LICENSE.txt). The body was skinned at rest pose,
 * normalized (1.72m tall, feet at y=0, facing +Z), and pre-sliced into
 * garment shells that sit a few millimeters above the skin.
 */
// eslint-disable-next-line @typescript-eslint/no-var-requires
const baked = require('../../assets/avatar/baked-avatar.json') as BakedAvatar;

export type GarmentShellName = 'tank' | 'tee' | 'long' | 'outer' | 'pants' | 'shorts' | 'shoes';

type BakedMesh = {
  p: number[];
  n: number[];
  uv?: number[];
  i: number[];
};

type BakedAvatar = {
  meta: {
    height: number;
    landmarks: Record<string, number>;
  };
  body: BakedMesh;
  garments: Record<GarmentShellName, BakedMesh>;
};

export const AVATAR_HEIGHT: number = baked.meta.height;
export const AVATAR_LANDMARKS: Record<string, number> = baked.meta.landmarks;

function toGeometry(mesh: BakedMesh): THREE.BufferGeometry {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(mesh.p, 3));
  geometry.setAttribute('normal', new THREE.Float32BufferAttribute(mesh.n, 3));
  if (mesh.uv) {
    geometry.setAttribute('uv', new THREE.Float32BufferAttribute(mesh.uv, 2));
  }
  geometry.setIndex(mesh.i);
  return geometry;
}

const cache = new Map<string, THREE.BufferGeometry>();

export function getBodyGeometry(): THREE.BufferGeometry {
  let geo = cache.get('body');
  if (!geo) {
    geo = toGeometry(baked.body);
    cache.set('body', geo);
  }
  return geo;
}

export function getGarmentGeometry(name: GarmentShellName): THREE.BufferGeometry {
  let geo = cache.get(name);
  if (!geo) {
    geo = toGeometry(baked.garments[name]);
    cache.set(name, geo);
  }
  return geo;
}
