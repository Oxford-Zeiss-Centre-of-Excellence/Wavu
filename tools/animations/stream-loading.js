// Generator for guide/assets/img/stream/stream-loading.svg
const fs = require('fs');
const T = 13;
const f = v => +(+v).toFixed(1);
const kt = t => +(t / T).toFixed(3);
const EASE = '.42 0 .58 1';
function anim(attr, kf, opts = {}) {
  kf = kf.slice().sort((p, q) => p[0] - q[0]);
  if (kf[0][0] !== 0) kf.unshift([0, kf[0][1]]);
  if (kf[kf.length - 1][0] !== T) kf.push([T, kf[kf.length - 1][1]]);
  const vals = kf.map(k => k[1]).join(';');
  const kts = kf.map(k => kt(k[0])).join(';');
  const spl = opts.spline ? ` calcMode="spline" keySplines="${Array(kf.length - 1).fill(EASE).join(';')}"` : '';
  const tag = opts.type ? 'animateTransform' : 'animate';
  const typ = opts.type ? ` type="${opts.type}"` : '';
  return `<${tag} attributeName="${attr}"${typ} dur="${T}s" repeatCount="indefinite" values="${vals}" keyTimes="${kts}"${spl}/>`;
}
const P = { top: '#f3e5f5', mid: '#e1bee7', st: '#6a1b9a' }, O = { top: '#fff3e0', mid: '#ffcc80', st: '#ef6c00' }, G = { top: '#e8f5e9', mid: '#a5d6a7', st: '#2e7d32' };
const out = [];
out.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 380" role="img" aria-labelledby="t d">`);
out.push(`<title id="t">One chunk at a time, from the image group to the label group</title>`);
out.push(`<desc id="d">One OME-Zarr store holds two groups: on the left the input group /image with its chunk files (purple), on the right the output group /label with empty slots (green). The worker reads one chunk at a time into its small memory box, processes it (the chunk turns orange, then green), writes the result chunk into the matching slot of /label and lets the chunk go. Each processed chunk also leaves a tiny per-chunk results table that stacks up beside the memory box. After the last chunk the small tables move to the right edge and merge, row by row, into one assembled results table.</desc>`);
out.push(`<rect width="960" height="380" rx="16" fill="#fafafa" stroke="#cfd8dc"/>`);

// folder shape helper (tab on the top-left)
const folder = (x, y, w, h, tab, fill, st, sw) => `<path d="M${x} ${y + 10}v-6a4 4 0 0 1 4 -4h${tab}l8 8h${w - tab - 12}a4 4 0 0 1 4 4v${h - 12}a4 4 0 0 1 -4 4h${-(w - 8)}a4 4 0 0 1 -4 -4z" fill="${fill}" stroke="${st}" stroke-width="${sw}" stroke-linejoin="round"/>`;
// store and its two groups
out.push(folder(24, 10, 620, 172, 120, '#ffffff', '#002147', 2.5));
const LBL = 'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="13"';
out.push(`<text x="44" y="38" ${LBL} font-weight="600" fill="#002147">data.ome.zarr</text>`);
out.push(folder(44, 48, 280, 122, 70, '#f3e5f5', '#6a1b9a', 2));
out.push(`<rect x="52" y="49" width="56" height="7" rx="3" fill="#6a1b9a"/>`);
out.push(`<text x="56" y="74" ${LBL} fill="#6a1b9a">/image</text>`);
out.push(folder(344, 48, 280, 122, 70, '#e8f5e9', '#2e7d32', 2));
out.push(`<rect x="352" y="49" width="56" height="7" rx="3" fill="#2e7d32"/>`);
out.push(`<text x="356" y="74" ${LBL} fill="#2e7d32">/label</text>`);

const S = 34;
const cols = [0, 1, 2], rows = [0, 1];
const imgPos = (c, r) => [110 + c * 56, 80 + r * 44];
const labPos = (c, r) => [410 + c * 56, 80 + r * 44];
const file = (x, y, fill, st) => `<path d="M${x} ${y}h${S - 9}l9 9v${S - 9}h${-S}z" fill="${fill}" stroke="${st}" stroke-width="1.5" stroke-linejoin="round"/><path d="M${x + S - 9} ${y}v9h9" fill="none" stroke="${st}" stroke-width="1.2"/>`;

// worker with memory box and a turning wheel
const W = { x: 240, y: 212, w: 330, h: 150 };
out.push(`<rect x="${W.x}" y="${W.y}" width="${W.w}" height="${W.h}" rx="14" fill="#e3f2fd" stroke="#1565c0" stroke-width="2"/>`);
const M = { x: 262, y: 236, w: 120, h: 104 };
out.push(`<rect x="${M.x}" y="${M.y}" width="${M.w}" height="${M.h}" rx="8" fill="#fff" stroke="#002147" stroke-width="2" stroke-dasharray="6 4"/>`);
for (let q = 0; q < 6; q++) out.push(`<rect x="${M.x + 10 + q * 19}" y="${M.y + M.h}" width="8" height="7" fill="#002147"/>`);
const memC = [M.x + M.w / 2 - S / 2, M.y + M.h / 2 - S / 2];

const t0 = i => 0.6 + i * 1.3;
const order = [];
for (const r of rows) for (const c of cols) order.push([c, r]);

// memory box flashes orange while processing
{
  const kf = [[0, 0]];
  order.forEach((_, i) => { const s = t0(i); kf.push([s + 0.4, 0], [s + 0.5, 1], [s + 0.75, 1], [s + 0.85, 0]); });
  out.push(`<rect x="${M.x}" y="${M.y}" width="${M.w}" height="${M.h}" rx="8" fill="none" stroke="#ef6c00" stroke-width="3" opacity="0">${anim('opacity', kf)}</rect>`);
}
// wheel in the worker, turning
const gear = (r, n, dpt) => { let d = ''; const m = n * 4; for (let q = 0; q < m; q++) { const a = q / m * 2 * Math.PI, rr = q % 4 < 2 ? r + dpt : r; d += (q ? 'L' : 'M') + f(rr * Math.cos(a)) + ' ' + f(rr * Math.sin(a)); } return d + 'Z'; };

// /image files and /label slots
order.forEach(([c, r], i) => {
  const [x, y] = imgPos(c, r), [lx, ly] = labPos(c, r), s = t0(i);
  out.push(file(x, y, '#e1bee7', '#6a1b9a'));
  out.push(`<rect x="${x - 3}" y="${y - 3}" width="${S + 6}" height="${S + 6}" rx="5" fill="none" stroke="#ef6c00" stroke-width="2.5" opacity="0">${anim('opacity', [[0, 0], [s - 0.15, 0], [s, 1], [s + 0.35, 1], [s + 0.5, 0]])}</rect>`);
  out.push(`<rect x="${lx}" y="${ly}" width="${S}" height="${S}" rx="3" fill="#fff" fill-opacity=".6" stroke="#2e7d32" stroke-width="1.5" stroke-dasharray="4 3"/>`);
});

// gear at the worker's right-top corner
out.push(`<g transform="translate(${W.x + W.w - 22} ${W.y + 20})"><path d="${gear(9, 7, 3)}" fill="#1565c0" fill-opacity=".7"><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="4s" repeatCount="indefinite"/></path><circle r="3" fill="#e3f2fd"/></g>`);

// moving chunks (copies): /image -> memory -> /label
const END = 12.2, OFF = 12.7;
order.forEach(([c, r], i) => {
  const [x, y] = imgPos(c, r), [lx, ly] = labPos(c, r), s = t0(i);
  const pos = [[0, `${x} ${y}`], [s, `${x} ${y}`], [s + 0.4, `${memC[0]} ${memC[1]}`], [s + 0.8, `${memC[0]} ${memC[1]}`], [s + 1.2, `${lx} ${ly}`], [OFF, `${lx} ${ly}`], [OFF + 0.05, `${x} ${y}`]];
  const col = k => [[0, P[k]], [s + 0.42, P[k]], [s + 0.52, O[k]], [s + 0.68, O[k]], [s + 0.8, G[k]], [OFF, G[k]], [OFF + 0.05, P[k]]];
  const op = [[0, 0], [s - 0.01, 0], [s, 1], [END, 1], [OFF, 0]];
  out.push(`<g transform="translate(${x} ${y})" opacity="0">${anim('opacity', op)}${anim('transform', pos, { type: 'translate', spline: true })}<rect width="${S}" height="${S}" rx="4" fill="${P.mid}" stroke="${P.st}" stroke-width="2">${anim('fill', col('mid'))}${anim('stroke', col('st'))}</rect><rect x="5" y="5" width="${S - 10}" height="${S - 10}" rx="2" fill="${P.top}">${anim('fill', col('top'))}</rect></g>`);
});

// per-chunk result tables: appear in memory, stack beside it, then merge into one long table
const card = (w, h) => `<rect width="${w}" height="${h}" rx="3" fill="#fff" stroke="#1565c0" stroke-width="1.5"/><rect x="5" y="${h / 2 - 2.5}" width="${w * 0.3}" height="5" rx="2.5" fill="#1565c0" fill-opacity=".5"/><rect x="${w * 0.45}" y="${h / 2 - 2.5}" width="${w * 0.42}" height="5" rx="2.5" fill="#2e7d32" fill-opacity=".7"/>`;
const CW = 60, CH = 18;
const stackPos = i => [400 + (i % 2) * 80, 246 + Math.floor(i / 2) * 32];
const MERGE = 8.6, SC = 1.6, RH = CH * SC, MW = CW * SC, MX = 790, MY = 200 - RH * 3.5;
const mergedPos = i => [MX, MY + RH + i * RH];
order.forEach((_, i) => {
  const s = t0(i), [sx, sy] = stackPos(i), [mx, my] = mergedPos(i);
  const mc = [M.x + M.w / 2 - CW / 2, M.y + M.h - CH - 6];
  const pos = [[0, `${mc[0]} ${mc[1]}`], [s + 0.8, `${mc[0]} ${mc[1]}`], [s + 1.2, `${sx} ${sy}`], [MERGE + i * 0.08, `${sx} ${sy}`], [MERGE + 0.6 + i * 0.08, `${mx} ${my}`]];
  const op = [[0, 0], [s + 0.75, 0], [s + 0.85, 1], [END, 1], [OFF, 0]];
  out.push(`<g transform="translate(${mc[0]} ${mc[1]})" opacity="0">${anim('opacity', op)}${anim('transform', pos, { type: 'translate', spline: true })}<g>${anim('transform', [[0, '1'], [MERGE + i * 0.08, '1'], [MERGE + 0.6 + i * 0.08, `${SC}`], [OFF, `${SC}`], [OFF + 0.05, '1']], { type: 'scale', spline: true })}${card(CW, CH)}</g></g>`);
});
// header of the merged table
out.push(`<g opacity="0">${anim('opacity', [[0, 0], [MERGE + 0.7, 0], [MERGE + 1.0, 1], [END, 1], [OFF, 0]])}<rect x="${MX}" y="${MY}" width="${MW}" height="${RH}" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="2"/><rect x="${MX - 5}" y="${MY - 5}" width="${MW + 10}" height="${RH * 7 + 10}" rx="6" fill="none" stroke="#1565c0" stroke-width="2"/></g>`);

out.push('</svg>');
const svg = out.join('\n');
fs.writeFileSync(process.argv[2], svg);
console.log(svg.length, 'bytes');
