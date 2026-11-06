// Generator for guide/assets/img/stream/data-factory.svg
const fs = require('fs');
const T = 12;
const a = 32, c = 0.8660254, s = 0.5;
const f = v => +v.toFixed(1);
const kt = t => +(t / T).toFixed(3);
const EASE = '.42 0 .58 1';

const COL = {
  p: { top: '#f3e5f5', l: '#e1bee7', r: '#ce93d8', st: '#6a1b9a' },
  o: { top: '#fff3e0', l: '#ffe0b2', r: '#ffcc80', st: '#ef6c00' },
  g: { top: '#e8f5e9', l: '#c8e6c9', r: '#a5d6a7', st: '#2e7d32' },
};
const pts = arr => arr.map(([x, y]) => `${f(x)} ${f(y)}`).join(' ');
// faces of a cube of edge e whose front-bottom vertex is at (0,0)
function faces(e) {
  const w = e * c;
  return {
    top: [[0, -e], [w, -1.5 * e], [0, -2 * e], [-w, -1.5 * e]],
    r: [[0, 0], [w, -0.5 * e], [w, -1.5 * e], [0, -e]],
    l: [[0, 0], [-w, -0.5 * e], [-w, -1.5 * e], [0, -e]],
  };
}
// iso projection relative to a cube center (cx,cy) for a cube of edge L=2a with min corner at origin
const L = 2 * a;
function P(cx, cy, x, y, z) { // x,y,z with origin at centre of cube base-ish: cube spans 0..L
  return [cx + (x - y) * c, cy + (x + y) * s - z - L * 0 ];
}
// cube from 0..L: top-back (0,0,L) -> (cx, cy - L), front-bottom (L,L,0)->(cx, cy+L)
const LEFT = [140, 200], RIGHT = [800, 200];
const lanesY = [124, 196, 268, 340];
const XS = 272, XST = 480, XOUT = 655;
const E = 20; // explode offset

// chunks in painter order
const chunks = [];
for (const k of [0, 1]) for (const [i, j] of [[0, 0], [1, 0], [0, 1], [1, 1]]) chunks.push({ i, j, k });

function anchor(cen, ch, ex) {
  const ox = ex ? (ch.i ? E : -E) : 0, oy = ex ? (ch.j ? E : -E) : 0, oz = ex ? (ch.k ? E : -E) : 0;
  return P(cen[0], cen[1], ch.i * a + a + ox, ch.j * a + a + oy, ch.k * a + oz);
}

function anim(attr, kf, opts = {}) {
  kf.sort((p, q) => p[0] - q[0]);
  const vals = kf.map(k => k[1]).join(';');
  const kts = kf.map(k => kt(k[0])).join(';');
  const spl = opts.spline ? ` calcMode="spline" keySplines="${Array(kf.length - 1).fill(EASE).join(';')}"` : '';
  const tag = (opts.translate || opts.scale) ? 'animateTransform' : 'animate';
  const typ = opts.translate ? ' type="translate"' : opts.scale ? ' type="scale"' : '';
  return `<${tag} attributeName="${attr}"${typ} dur="${T}s" repeatCount="indefinite" values="${vals}" keyTimes="${kts}"${spl}/>`;
}

let out = [];
out.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 380" role="img" aria-labelledby="t d">`);
out.push(`<title id="t">Chopped into chunks, cooked in parallel sub-kitchens, served as one meal</title>`);
out.push(`<desc id="d">A big raw 3-D block of image data lies on a chopping board. A knife cuts it along a grid into eight smaller pieces, the chunks of an OME-Zarr store. The pieces travel in parallel to four small sub-kitchens, the parallel workers; each kitchen cooks one piece at a time on its stove (the piece turns from purple to orange while cooking, then green when done), so only a few pieces are in work at once. The cooked pieces are assembled on one plate into the finished meal, the result block, which glows before the cycle repeats.</desc>`);
out.push(`<defs><filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="12"/></filter>`);
out.push(`</defs>`);
out.push(`<rect width="960" height="380" rx="16" fill="#fafafa" stroke="#cfd8dc"/>`);

// iso slab (board / plate helper)
function isoEllipse(cx, cy, rx) { return `cx="${cx}" cy="${cy}" rx="${rx}" ry="${f(rx * 0.577)}"`; }
// ---- chopping board under the raw block (blue plastic board, iso slab)
{
  const cx = LEFT[0], cy = LEFT[1] + L / 2, hw = 84, hh = 84 * 0.5, th = 9;
  const top = [[cx - hw, cy], [cx, cy - hh], [cx + hw, cy], [cx, cy + hh]];
  out.push(`<polygon points="${pts([[cx - hw, cy], [cx, cy + hh], [cx + hw, cy], [cx + hw, cy + th], [cx, cy + hh + th], [cx - hw, cy + th]])}" fill="#90caf9" stroke="#1565c0" stroke-width="2" stroke-linejoin="round"/>`);
  out.push(`<polygon points="${pts(top)}" fill="#e3f2fd" stroke="#1565c0" stroke-width="2" stroke-linejoin="round"/>`);
}
// ---- plate under the result
{
  const cx = RIGHT[0], cy = RIGHT[1] + L / 2;
  out.push(`<ellipse ${isoEllipse(cx, cy + 6, 90)} fill="#cfd8dc"/>`);
  out.push(`<ellipse ${isoEllipse(cx, cy, 90)} fill="#ffffff" stroke="#78909c" stroke-width="2"/>`);
  out.push(`<ellipse ${isoEllipse(cx, cy, 70)} fill="none" stroke="#b0bec5" stroke-width="1.5"/>`);
}

// ---- sub-kitchens: one small stove with a pan per lane, flames and steam while cooking
const d = n => n * 0.25;
const windows = n => [[4.2 + d(n), 5.0 + d(n)], [5.9 + d(n), 6.7 + d(n)]];
lanesY.forEach((y, n) => {
  const kf = [[0, 0], [T, 0]];
  for (const [w0, w1] of windows(n)) kf.push([w0 - 0.15, 0], [w0 + 0.15, 1], [w1 - 0.25, 1], [w1 + 0.1, 0]);
  const bx = XST - 58, bw = 124;
  out.push(`<rect x="${bx}" y="${y - 52}" width="${bw}" height="64" rx="10" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/>`);
  // stove knobs
  out.push(`<circle cx="${bx + 10}" cy="${y - 4}" r="3.5" fill="#fff" stroke="#2e7d32" stroke-width="1.5"/><circle cx="${bx + 10}" cy="${y - 16}" r="3.5" fill="#fff" stroke="#2e7d32" stroke-width="1.5"/>`);
  // flames (under the pan), visible only while cooking
  let fl = `<g opacity="0">${anim('opacity', kf)}`;
  for (const dx of [-18, 0, 18]) {
    fl += `<path d="M${XST + dx - 4} ${y + 6}q4 -9 4 -9q0 0 4 9z" fill="#ffb74d" stroke="#ef6c00" stroke-width="1.2" stroke-linejoin="round" transform-origin="${XST + dx} ${y + 6}"><animateTransform attributeName="transform" type="scale" values="1 1;1 .7;1 1" dur="${0.5 + Math.abs(dx) / 60}s" repeatCount="indefinite"/></path>`;
  }
  // steam on the right, rising
  for (let q = 0; q < 2; q++) {
    const sx = XST + 44 + q * 9;
    fl += `<path d="M${sx} ${y - 26}q-4 -5 0 -10q4 -5 0 -10" fill="none" stroke="#90a4ae" stroke-width="2" stroke-linecap="round"><animateTransform attributeName="transform" type="translate" values="0 4;0 -8" dur="1.6s" begin="${-q * 0.8}s" repeatCount="indefinite"/><animate attributeName="opacity" values="0;.9;0" dur="1.6s" begin="${-q * 0.8}s" repeatCount="indefinite"/></path>`;
  }
  fl += '</g>';
  out.push(fl);
  // pan: shallow iso dish with a handle
  out.push(`<path d="M${XST + 34} ${y - 12}L${XST + 54} ${y - 18}" stroke="#002147" stroke-width="5" stroke-linecap="round"/>`);
  out.push(`<ellipse cx="${XST}" cy="${y - 9}" rx="36" ry="12" fill="#546e7a"/><ellipse cx="${XST}" cy="${y - 12}" rx="36" ry="12" fill="#eceff1" stroke="#002147" stroke-width="2"/>`);
});

// ---- result glow (behind)
{
  const [cx, cy] = RIGHT;
  const hex = [[cx, cy + L], [cx + L * c, cy + L / 2], [cx + L * c, cy - L / 2], [cx, cy - L], [cx - L * c, cy - L / 2], [cx - L * c, cy + L / 2]];
  out.push(`<polygon points="${pts(hex)}" fill="#66bb6a" filter="url(#glow)" opacity="0">${anim('opacity', [[0, 0], [8.8, 0], [9.2, 1], [9.9, .55], [10.5, 1], [11.2, 0], [T, 0]], { spline: true })}</polygon>`);
}

// ---- raw block (overlay with grid lines)
function bigCube(cen, col, extra) {
  const [cx, cy] = cen;
  const F = faces(L);
  const tr = `translate(${cx} ${cy + L})`;
  let g = `<g transform="${tr}" stroke="${col.st}" stroke-width="2" stroke-linejoin="round">`;
  g += `<polygon points="${pts(F.top)}" fill="${col.top}"/><polygon points="${pts(F.l)}" fill="${col.l}"/><polygon points="${pts(F.r)}" fill="${col.r}"/>`;
  return g + (extra || '') + '</g>';
}
{
  // grid lines: midlines of each visible face, drawn with dash animation
  const w = L * c, h = L;
  const lines = [
    // top face midlines
    [[w / 2, -1.25 * h], [-w / 2, -1.75 * h]], [[-w / 2, -1.25 * h], [w / 2, -1.75 * h]],
    // right face
    [[w / 2, -0.25 * h], [w / 2, -1.25 * h]], [[0, -0.5 * h], [w, -1.0 * h]],
    // left face
    [[-w / 2, -0.25 * h], [-w / 2, -1.25 * h]], [[0, -0.5 * h], [-w, -1.0 * h]],
  ];
  let g = '<g stroke-width="1.6" fill="none">';
  lines.forEach(([[x0, y0], [x1, y1]], li) => {
    const [c0, c1] = [0, 4].includes(li) ? [1.1, 1.35] : [1.75, 2.0];
    g += `<path d="M${f(x0)} ${f(y0)}L${f(x1)} ${f(y1)}" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1">${anim('stroke-dashoffset', [[0, 1], [c0, 1], [c1, 0], [11.4, 0], [11.45, 1], [T, 1]], { spline: true })}</path>`;
  });
  g += '</g>';
  const kfo = [[0, 1], [2.2, 1], [2.22, 0], [11.6, 0], [12, 1]];
  out.push(`<g opacity="1">${anim('opacity', kfo)}${bigCube(LEFT, COL.p, g)}</g>`);
}

// ---- chunks
out.push(`<g>${anim('opacity', [[0, 1], [11.2, 1], [11.7, 0], [11.9, 0], [T, 1]])}`);
chunks.forEach((ch, idx) => {
  const batch = ch.k; // 0 = first batch (bottom layer), 1 = second
  const n = idx % 4, ln = lanesY[n];
  const TL = anchor(LEFT, ch, false), EX = anchor(LEFT, ch, true), RT = anchor(RIGHT, ch, false);
  const LS = [XS, ln], ST = [XST, ln], OU = [XOUT, ln];
  const dd = d(n);
  let kf;
  if (batch === 0) {
    kf = [[0, TL], [2.2, TL], [2.8, EX], [2.9 + dd, EX], [3.5 + dd, LS], [4.2 + dd, ST], [5.0 + dd, ST], [5.7 + dd, OU], [6.3 + dd, RT]];
  } else {
    kf = [[0, TL], [2.2, TL], [2.8, EX], [4.3 + dd, EX], [4.9 + dd, LS], [5.2 + dd, LS], [5.9 + dd, ST], [6.7 + dd, ST], [7.4 + dd, OU], [8.0 + dd, RT]];
  }
  kf.push([11.75, RT], [11.8, TL], [T, TL]);
  const tkf = kf.map(([t, p]) => [t, `${f(p[0])} ${f(p[1])}`]);
  const [w0, w1] = windows(n)[batch];
  const colkf = key => [[0, COL.p[key]], [w0, COL.p[key]], [w0 + 0.15, COL.o[key]], [w1 - 0.2, COL.o[key]], [w1, COL.g[key]], [11.75, COL.g[key]], [11.8, COL.p[key]], [T, COL.p[key]]];
  const op = [[0, 0], [2.18, 0], [2.2, 1], [11.75, 1], [11.77, 0], [T, 0]];
  const F = faces(a);
  let g = `<g transform="translate(${f(TL[0])} ${f(TL[1])})">${anim('transform', tkf, { translate: true, spline: true })}`;
  g += `<g opacity="0" stroke="${COL.p.st}" stroke-width="1.8" stroke-linejoin="round">${anim('opacity', op)}${anim('stroke', colkf('st'))}`;
  for (const key of ['top', 'l', 'r']) g += `<polygon points="${pts(F[key])}" fill="${COL.p[key]}">${anim('fill', colkf(key))}</polygon>`;
  g += '</g></g>';
  out.push(g);
});

out.push('</g>');
// knife (cleaver): two chops while the grid cuts appear
{
  const up = 96, dn = 168, x1 = LEFT[0] - 28, x2 = LEFT[0] + 28;
  const kf = [[0, `${x1} ${up}`], [0.7, `${x1} ${up - 20}`], [1.0, `${x1} ${up}`], [1.25, `${x1} ${dn}`], [1.45, `${x1} ${up}`], [1.6, `${x2} ${up}`], [1.9, `${x2} ${dn}`], [2.1, `${x2} ${up}`], [2.4, `${x2} ${up - 20}`], [T, `${x1} ${up}`]];
  const op = [[0, 0], [0.7, 0], [0.95, 1], [2.15, 1], [2.4, 0], [T, 0]];
  out.push(`<g transform="translate(${x1} ${up})" opacity="0">${anim('opacity', op)}${anim('transform', kf, { translate: true, spline: true })}<rect x="26" y="-31" width="38" height="11" rx="5" fill="#002147"/><path d="M-30 0H28V-36H-24Q-32 -36 -32 -28Z" fill="#eceff1" stroke="#546e7a" stroke-width="2" stroke-linejoin="round"/><circle cx="-18" cy="-27" r="3" fill="none" stroke="#546e7a" stroke-width="1.5"/></g>`);
}
out.push('</svg>');
const svg = out.join('\n');
fs.writeFileSync(process.argv[2], svg);
console.log(svg.length, 'bytes');
