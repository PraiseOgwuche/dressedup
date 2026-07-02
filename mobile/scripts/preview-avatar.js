#!/usr/bin/env node
/**
 * Offline software render of the baked avatar (body + garment shells) to PNG,
 * so shell fit can be checked without launching the app.
 *
 *   node scripts/preview-avatar.js [outfile.png] [yawDegrees]
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const baked = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'assets', 'avatar', 'baked-avatar.json')),
);

const W = 460;
const H = 900;
const OUT = process.argv[2] || path.join(__dirname, 'avatar-preview.png');
const YAW = ((Number(process.argv[3]) || 20) * Math.PI) / 180;

const LIGHT = normalize([0.4, 0.8, 0.6]);
const BG = [247, 243, 238];

function normalize(v) {
  const l = Math.hypot(...v) || 1;
  return v.map((x) => x / l);
}

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

const layers = [
  { mesh: baked.body, color: hexToRgb('#E3B48C') },
  { mesh: baked.garments.tee, color: hexToRgb('#B14A32') },
  { mesh: baked.garments.pants, color: hexToRgb('#D9CBB4') },
  { mesh: baked.garments.shoes, color: hexToRgb('#EDEDE8') },
];

// Collect world-space triangles from all layers.
const tris = [];
for (const { mesh, color } of layers) {
  const { p, i } = mesh;
  for (let t = 0; t < i.length; t += 3) {
    const idx = [i[t], i[t + 1], i[t + 2]];
    const verts = idx.map((v) => [p[v * 3], p[v * 3 + 1], p[v * 3 + 2]]);
    tris.push({ verts, color });
  }
}

// Rotate around Y, then orthographic projection.
const cos = Math.cos(YAW);
const sin = Math.sin(YAW);
const project = ([x, y, z]) => {
  const rx = x * cos + z * sin;
  const rz = -x * sin + z * cos;
  const s = H / 2.0; // 2m world height mapped to image height
  return [W / 2 + rx * s, H - (y * 1.02 + 0.04) * s, rz];
};

const screenTris = tris.map(({ verts, color }) => {
  const pv = verts.map(project);
  const [a, b, c] = pv;
  const e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const e2 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
  // Screen-space normal (y axis flipped already by projection).
  let n = [
    e1[1] * e2[2] - e1[2] * e2[1],
    e1[2] * e2[0] - e1[0] * e2[2],
    e1[0] * e2[1] - e1[1] * e2[0],
  ];
  n = normalize(n);
  if (n[2] < 0) n = n.map((x) => -x);
  const lambert = Math.max(0.35, n[0] * LIGHT[0] - n[1] * LIGHT[1] + n[2] * LIGHT[2] * 0.9 + 0.25);
  const depth = (a[2] + b[2] + c[2]) / 3;
  return { pv, color: color.map((ch) => Math.min(255, ch * lambert)), depth };
});

screenTris.sort((t1, t2) => t1.depth - t2.depth);

const px = Buffer.alloc(W * H * 3);
for (let i = 0; i < W * H; i++) {
  px[i * 3] = BG[0];
  px[i * 3 + 1] = BG[1];
  px[i * 3 + 2] = BG[2];
}

function fillTriangle([a, b, c], color) {
  const minX = Math.max(0, Math.floor(Math.min(a[0], b[0], c[0])));
  const maxX = Math.min(W - 1, Math.ceil(Math.max(a[0], b[0], c[0])));
  const minY = Math.max(0, Math.floor(Math.min(a[1], b[1], c[1])));
  const maxY = Math.min(H - 1, Math.ceil(Math.max(a[1], b[1], c[1])));
  const area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  if (Math.abs(area) < 1e-9) return;
  for (let y = minY; y <= maxY; y++) {
    for (let x = minX; x <= maxX; x++) {
      const w0 = ((b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])) / area;
      const w1 = ((c[0] - b[0]) * (y - b[1]) - (c[1] - b[1]) * (x - b[0])) / area;
      const w2 = ((a[0] - c[0]) * (y - c[1]) - (a[1] - c[1]) * (x - c[0])) / area;
      if (w0 < 0 || w1 < 0 || w2 < 0) continue;
      const o = (y * W + x) * 3;
      px[o] = color[0];
      px[o + 1] = color[1];
      px[o + 2] = color[2];
    }
  }
}

for (const { pv, color } of screenTris) fillTriangle(pv, color);

// --- Minimal PNG encode (8-bit RGB, no filter) ---
function crc32(buf) {
  let c = ~0;
  for (let i = 0; i < buf.length; i++) {
    c ^= buf[i];
    for (let k = 0; k < 8; k++) c = (c >>> 1) ^ (0xedb88320 & -(c & 1));
  }
  return ~c >>> 0;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const typeBuf = Buffer.from(type);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])));
  return Buffer.concat([len, typeBuf, data, crc]);
}

const ihdr = Buffer.alloc(13);
ihdr.writeUInt32BE(W, 0);
ihdr.writeUInt32BE(H, 4);
ihdr[8] = 8; // bit depth
ihdr[9] = 2; // color type RGB

const raw = Buffer.alloc(H * (W * 3 + 1));
for (let y = 0; y < H; y++) {
  raw[y * (W * 3 + 1)] = 0;
  px.copy(raw, y * (W * 3 + 1) + 1, y * W * 3, (y + 1) * W * 3);
}

const png = Buffer.concat([
  Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
  chunk('IHDR', ihdr),
  chunk('IDAT', zlib.deflateSync(raw)),
  chunk('IEND', Buffer.alloc(0)),
]);

fs.writeFileSync(OUT, png);
console.log(`wrote ${OUT}`);
