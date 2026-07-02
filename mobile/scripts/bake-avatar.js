#!/usr/bin/env node
/**
 * Bakes the rigged CC0 base mesh (assets/avatar/base-mesh-male.glb) into a
 * compact JSON asset the app can render directly:
 *
 *  - Applies linear-blend skinning at the rest pose (so the exported vertices
 *    match exactly what three.js would draw), then normalizes the body to
 *    HUMANOID_HEIGHT with feet at y=0, centered on x/z.
 *  - Slices the body surface into garment "shells" by bone weight + landmark
 *    Y cuts (tee = torso + upper arms, pants = hips + legs, ...), inflates
 *    each shell along vertex normals so it reads as fabric over skin, and
 *    bakes planar UVs for photo-swatch texturing.
 *
 * Output: assets/avatar/baked-avatar.json  (re-run after swapping the GLB)
 *
 *   node scripts/bake-avatar.js
 */

const fs = require('fs');
const path = require('path');

const GLB_PATH = path.join(__dirname, '..', 'assets', 'avatar', 'base-mesh-male.glb');
const OUT_PATH = path.join(__dirname, '..', 'assets', 'avatar', 'baked-avatar.json');
const HUMANOID_HEIGHT = 1.72;

// ---------------------------------------------------------------------------
// GLB parsing
// ---------------------------------------------------------------------------

function parseGlb(buffer) {
  const jsonLen = buffer.readUInt32LE(12);
  const json = JSON.parse(buffer.slice(20, 20 + jsonLen).toString());
  const binStart = 20 + jsonLen + 8;
  const bin = buffer.slice(binStart);
  return { json, bin };
}

const COMPONENT_READERS = {
  5121: (buf, off) => buf.readUInt8(off), // UNSIGNED_BYTE
  5123: (buf, off) => buf.readUInt16LE(off), // UNSIGNED_SHORT
  5125: (buf, off) => buf.readUInt32LE(off), // UNSIGNED_INT
  5126: (buf, off) => buf.readFloatLE(off), // FLOAT
};
const COMPONENT_SIZES = { 5121: 1, 5123: 2, 5125: 4, 5126: 4 };
const TYPE_COUNTS = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };

function readAccessor(gltf, bin, accessorIndex) {
  const acc = gltf.accessors[accessorIndex];
  const view = gltf.bufferViews[acc.bufferView];
  const compSize = COMPONENT_SIZES[acc.componentType];
  const compCount = TYPE_COUNTS[acc.type];
  const read = COMPONENT_READERS[acc.componentType];
  const stride = view.byteStride || compSize * compCount;
  const base = (view.byteOffset || 0) + (acc.byteOffset || 0);
  const out = new Array(acc.count * compCount);
  for (let i = 0; i < acc.count; i++) {
    for (let c = 0; c < compCount; c++) {
      out[i * compCount + c] = read(bin, base + i * stride + c * compSize);
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Minimal mat4 helpers (column-major, glTF convention)
// ---------------------------------------------------------------------------

function mat4Identity() {
  return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
}

function mat4Multiply(a, b) {
  const out = new Array(16);
  for (let col = 0; col < 4; col++) {
    for (let row = 0; row < 4; row++) {
      let sum = 0;
      for (let k = 0; k < 4; k++) sum += a[k * 4 + row] * b[col * 4 + k];
      out[col * 4 + row] = sum;
    }
  }
  return out;
}

function mat4FromTrs(t, q, s) {
  const [x, y, z, w] = q;
  const x2 = x + x;
  const y2 = y + y;
  const z2 = z + z;
  const xx = x * x2;
  const xy = x * y2;
  const xz = x * z2;
  const yy = y * y2;
  const yz = y * z2;
  const zz = z * z2;
  const wx = w * x2;
  const wy = w * y2;
  const wz = w * z2;
  const [sx, sy, sz] = s;
  return [
    (1 - (yy + zz)) * sx, (xy + wz) * sx, (xz - wy) * sx, 0,
    (xy - wz) * sy, (1 - (xx + zz)) * sy, (yz + wx) * sy, 0,
    (xz + wy) * sz, (yz - wx) * sz, (1 - (xx + yy)) * sz, 0,
    t[0], t[1], t[2], 1,
  ];
}

function mat4TransformPoint(m, p) {
  return [
    m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
    m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13],
    m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14],
  ];
}

function mat4TransformDirection(m, v) {
  return [
    m[0] * v[0] + m[4] * v[1] + m[8] * v[2],
    m[1] * v[0] + m[5] * v[1] + m[9] * v[2],
    m[2] * v[0] + m[6] * v[1] + m[10] * v[2],
  ];
}

// ---------------------------------------------------------------------------
// Skinning at rest pose
// ---------------------------------------------------------------------------

function computeWorldMatrices(gltf) {
  const nodes = gltf.nodes;
  const world = new Array(nodes.length);
  const visit = (index, parentMatrix) => {
    const node = nodes[index];
    const local = node.matrix
      ? node.matrix.slice()
      : mat4FromTrs(
          node.translation || [0, 0, 0],
          node.rotation || [0, 0, 0, 1],
          node.scale || [1, 1, 1],
        );
    world[index] = mat4Multiply(parentMatrix, local);
    for (const child of node.children || []) visit(child, world[index]);
  };
  for (const root of gltf.scenes[gltf.scene || 0].nodes) visit(root, mat4Identity());
  return world;
}

function normalize3(v) {
  const len = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / len, v[1] / len, v[2] / len];
}

function main() {
  const { json: gltf, bin } = parseGlb(fs.readFileSync(GLB_PATH));

  const prim = gltf.meshes[0].primitives[0];
  const positions = readAccessor(gltf, bin, prim.attributes.POSITION);
  const normals = readAccessor(gltf, bin, prim.attributes.NORMAL);
  const joints = readAccessor(gltf, bin, prim.attributes.JOINTS_0);
  const weights = readAccessor(gltf, bin, prim.attributes.WEIGHTS_0);
  const indices = readAccessor(gltf, bin, prim.indices);

  const skin = gltf.skins[0];
  const ibms = readAccessor(gltf, bin, skin.inverseBindMatrices);
  const world = computeWorldMatrices(gltf);

  // jointMatrix[j] = jointWorld * inverseBindMatrix (glTF skinning; the
  // skinned mesh's own node transform is ignored per spec).
  const jointMatrices = skin.joints.map((nodeIndex, j) =>
    mat4Multiply(world[nodeIndex], ibms.slice(j * 16, j * 16 + 16)),
  );
  const jointNames = skin.joints.map((nodeIndex) => gltf.nodes[nodeIndex].name);

  const vertCount = positions.length / 3;
  const skinnedPos = new Array(vertCount);
  const skinnedNorm = new Array(vertCount);
  const dominantJoint = new Array(vertCount);

  for (let v = 0; v < vertCount; v++) {
    const p = positions.slice(v * 3, v * 3 + 3);
    const n = normals.slice(v * 3, v * 3 + 3);
    let px = 0;
    let py = 0;
    let pz = 0;
    let nx = 0;
    let ny = 0;
    let nz = 0;
    let totalW = 0;
    let bestW = -1;
    let bestJ = 0;
    for (let k = 0; k < 4; k++) {
      const w = weights[v * 4 + k];
      if (w <= 0) continue;
      totalW += w;
      const j = joints[v * 4 + k];
      if (w > bestW) {
        bestW = w;
        bestJ = j;
      }
      const m = jointMatrices[j];
      const tp = mat4TransformPoint(m, p);
      const tn = mat4TransformDirection(m, n);
      px += tp[0] * w;
      py += tp[1] * w;
      pz += tp[2] * w;
      nx += tn[0] * w;
      ny += tn[1] * w;
      nz += tn[2] * w;
    }
    if (totalW === 0) {
      skinnedPos[v] = p;
      skinnedNorm[v] = normalize3(n);
      dominantJoint[v] = -1;
    } else {
      skinnedPos[v] = [px / totalW, py / totalW, pz / totalW];
      skinnedNorm[v] = normalize3([nx, ny, nz]);
      dominantJoint[v] = bestJ;
    }
  }

  // This export faces +X; rotate -90 deg about Y so the avatar faces +Z
  // (toward the default camera).
  const faceForward = ([x, y, z]) => [-z, y, x];
  for (let v = 0; v < vertCount; v++) {
    skinnedPos[v] = faceForward(skinnedPos[v]);
    skinnedNorm[v] = faceForward(skinnedNorm[v]);
  }

  // --- Normalize: height = HUMANOID_HEIGHT, feet at y=0, centered on x/z ---
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  let minZ = Infinity;
  let maxZ = -Infinity;
  for (const [x, y, z] of skinnedPos) {
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
    if (z < minZ) minZ = z;
    if (z > maxZ) maxZ = z;
  }
  const scale = HUMANOID_HEIGHT / (maxY - minY);
  const cx = (minX + maxX) / 2;
  const cz = (minZ + maxZ) / 2;
  const normalizePoint = ([x, y, z]) => [(x - cx) * scale, (y - minY) * scale, (z - cz) * scale];
  for (let v = 0; v < vertCount; v++) skinnedPos[v] = normalizePoint(skinnedPos[v]);

  // --- Landmarks from joint origins (bone heads) ---
  const jointY = {};
  skin.joints.forEach((nodeIndex, j) => {
    const m = world[nodeIndex];
    jointY[jointNames[j]] = (m[13] - minY) * scale;
  });
  const waistY = jointY['spine.001'];
  const shoulderY = (jointY['upper_arm.L'] + jointY['upper_arm.R']) / 2;
  const elbowY = (jointY['forearm.L'] + jointY['forearm.R']) / 2;
  const wristY = (jointY['hand.L'] + jointY['hand.R']) / 2;
  const hipY = (jointY['thigh.L'] + jointY['thigh.R']) / 2;
  const kneeY = (jointY['shin.L'] + jointY['shin.R']) / 2;
  const ankleY = (jointY['foot.L'] + jointY['foot.R']) / 2;

  const nameOf = (v) => (dominantJoint[v] >= 0 ? jointNames[dominantJoint[v]] : '');
  const isBone = (v, ...prefixes) => prefixes.some((p) => nameOf(v) === p || nameOf(v).startsWith(`${p}.`));

  // --- Bone groups ---
  const TORSO = (v) => isBone(v, 'spine', 'spine.001', 'spine.002', 'spine.003', 'spine.004', 'shoulder');
  const ARMS = (v) => isBone(v, 'shoulder', 'upper_arm', 'forearm');
  const LEGS = (v) => isBone(v, 'spine', 'pelvis', 'thigh', 'shin', 'foot');
  const FEET = (v) => isBone(v, 'foot', 'toe', 'heel', 'shin');

  const neckY = jointY['spine.004'];
  const collarY = neckY + 0.015;
  const shortSleeveCut = elbowY + 0.5 * (shoulderY - elbowY);
  const longSleeveCut = wristY + 0.1 * (elbowY - wristY);
  const teeHem = hipY - 0.01;
  const jacketHem = hipY - 0.07;
  const pantsWaist = waistY - 0.03;
  const shortsCut = kneeY + 0.45 * (hipY - kneeY);
  const pantsCuff = ankleY + 0.015;
  const shoeCollar = ankleY + 0.05;

  // Each garment = union of parts. A part keeps triangles touching its bone
  // group, then clips them to a clean horizontal Y band (collar/hem/cuff).
  const regions = {
    tank: [{ bones: TORSO, band: [teeHem, collarY] }],
    tee: [
      { bones: TORSO, band: [teeHem, collarY] },
      { bones: ARMS, band: [shortSleeveCut, collarY] },
    ],
    long: [
      { bones: TORSO, band: [teeHem, collarY] },
      { bones: ARMS, band: [longSleeveCut, collarY] },
    ],
    outer: [
      { bones: TORSO, band: [jacketHem, collarY] },
      { bones: ARMS, band: [longSleeveCut, collarY] },
    ],
    pants: [{ bones: LEGS, band: [pantsCuff, pantsWaist] }],
    shorts: [{ bones: LEGS, band: [shortsCut, pantsWaist] }],
    shoes: [{ bones: FEET, band: [-Infinity, shoeCollar] }],
  };

  // Offsets are staggered so overlapping layers (shoes < bottoms < tops <
  // outerwear) always keep a few mm of separation — no z-fighting.
  const inflation = {
    tank: 0.016,
    tee: 0.016,
    long: 0.016,
    outer: 0.03,
    pants: 0.011,
    shorts: 0.011,
    shoes: 0.007,
  };

  const round = (x) => Math.round(x * 10000) / 10000;

  // Sutherland–Hodgman clip of a polygon against y >= limit or y <= limit.
  // Vertices are {pos, norm}; new boundary vertices are interpolated.
  const clipPoly = (poly, limit, keepAbove) => {
    const inside = (v) => (keepAbove ? v.pos[1] >= limit : v.pos[1] <= limit);
    const lerpV = (a, b) => {
      const t = (limit - a.pos[1]) / (b.pos[1] - a.pos[1]);
      const mix = (u, w) => u + (w - u) * t;
      return {
        pos: [mix(a.pos[0], b.pos[0]), limit, mix(a.pos[2], b.pos[2])],
        norm: normalize3([
          mix(a.norm[0], b.norm[0]),
          mix(a.norm[1], b.norm[1]),
          mix(a.norm[2], b.norm[2]),
        ]),
      };
    };
    const out = [];
    for (let k = 0; k < poly.length; k++) {
      const cur = poly[k];
      const prev = poly[(k + poly.length - 1) % poly.length];
      const curIn = inside(cur);
      const prevIn = inside(prev);
      if (curIn) {
        if (!prevIn) out.push(lerpV(prev, cur));
        out.push(cur);
      } else if (prevIn) {
        out.push(lerpV(prev, cur));
      }
    }
    return out;
  };

  const buildShell = (parts, offset) => {
    const outTris = [];

    for (const { bones, band } of parts) {
      const passes = new Array(vertCount);
      for (let v = 0; v < vertCount; v++) passes[v] = bones(v);

      for (let t = 0; t < indices.length; t += 3) {
        const ids = [indices[t], indices[t + 1], indices[t + 2]];
        if (!ids.some((v) => passes[v])) continue;

        let poly = ids.map((v) => ({ pos: skinnedPos[v], norm: skinnedNorm[v] }));
        if (band[0] > -Infinity) poly = clipPoly(poly, band[0], true);
        if (poly.length >= 3 && band[1] < Infinity) poly = clipPoly(poly, band[1], false);
        for (let k = 1; k + 1 < poly.length; k++) outTris.push([poly[0], poly[k], poly[k + 1]]);
      }
    }

    // Weld duplicate vertices (parts overlap at shoulder seams) and inflate
    // along normals.
    const remap = new Map();
    const p = [];
    const n = [];
    const i = [];
    let gMinX = Infinity;
    let gMaxX = -Infinity;
    let gMinY = Infinity;
    let gMaxY = -Infinity;
    const keyOf = (v) => `${round(v.pos[0])},${round(v.pos[1])},${round(v.pos[2])}`;
    for (const tri of outTris) {
      const triIdx = [];
      for (const v of tri) {
        const key = keyOf(v);
        let idx = remap.get(key);
        if (idx === undefined) {
          idx = remap.size;
          remap.set(key, idx);
          const ox = v.pos[0] + v.norm[0] * offset;
          const oy = v.pos[1] + v.norm[1] * offset;
          const oz = v.pos[2] + v.norm[2] * offset;
          p.push(round(ox), round(oy), round(oz));
          n.push(round(v.norm[0]), round(v.norm[1]), round(v.norm[2]));
          if (ox < gMinX) gMinX = ox;
          if (ox > gMaxX) gMaxX = ox;
          if (oy < gMinY) gMinY = oy;
          if (oy > gMaxY) gMaxY = oy;
        }
        triIdx.push(idx);
      }
      // Drop degenerate slivers produced by welding clipped edges.
      if (triIdx[0] !== triIdx[1] && triIdx[1] !== triIdx[2] && triIdx[0] !== triIdx[2]) {
        i.push(...triIdx);
      }
    }

    // Planar UVs (front projection). Back faces mirror the image, which reads
    // fine for fabric swatches.
    const uv = [];
    const w = gMaxX - gMinX || 1;
    const h = gMaxY - gMinY || 1;
    for (let k = 0; k < p.length; k += 3) {
      uv.push(round((p[k] - gMinX) / w), round((p[k + 1] - gMinY) / h));
    }
    return { p, n, uv, i };
  };

  const body = {
    p: skinnedPos.flatMap(([x, y, z]) => [round(x), round(y), round(z)]),
    n: skinnedNorm.flatMap(([x, y, z]) => [round(x), round(y), round(z)]),
    i: indices,
  };

  const garments = {};
  for (const [name, predicate] of Object.entries(regions)) {
    garments[name] = buildShell(predicate, inflation[name]);
    const tris = garments[name].i.length / 3;
    console.log(`  ${name}: ${garments[name].p.length / 3} verts, ${tris} tris`);
  }

  const out = {
    meta: {
      height: HUMANOID_HEIGHT,
      landmarks: {
        waistY: round(waistY),
        hipY: round(hipY),
        kneeY: round(kneeY),
        ankleY: round(ankleY),
        shoulderY: round(shoulderY),
        elbowY: round(elbowY),
        wristY: round(wristY),
      },
    },
    body,
    garments,
  };

  fs.writeFileSync(OUT_PATH, JSON.stringify(out));
  const kb = (fs.statSync(OUT_PATH).size / 1024).toFixed(0);
  console.log(`body: ${vertCount} verts, ${indices.length / 3} tris`);
  console.log(`landmarks:`, out.meta.landmarks);
  console.log(`wrote ${OUT_PATH} (${kb} KB)`);
}

main();
