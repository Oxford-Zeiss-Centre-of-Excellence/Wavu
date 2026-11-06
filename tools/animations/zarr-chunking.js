// Generator for guide/assets/img/stream/zarr-chunking.svg
const fs = require('fs');
const T = 12;
const f = v => +(+v).toFixed(1);
const kt = t => +(t / T).toFixed(4);
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
const out = [];
out.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 360" role="img" aria-labelledby="t d">`);
out.push(`<title id="t">An image cut into chunks, one file per chunk</title>`);
out.push(`<desc id="d">A large image is divided into a grid of chunks, and each chunk is saved as its own small file in an OME-Zarr folder. A reader then fetches only the chunks it needs, one file at a time, and the numbers measured on each fetched chunk fill a results table row by row and a plot bar by bar.</desc>`);
out.push(`<rect width="960" height="360" rx="16" fill="#fafafa" stroke="#cfd8dc"/>`);

const C = 44, IM = [36, 92];
const FO = { x: 309, y: 70, w: 200, h: 226 };
const RD = { x: 606, y: 136, w: 100, h: 88 };
const TB = { x: 803, y: 52, w: 120, h: 118 };
const PL = { x: 803, y: 192, w: 120, h: 114 };
const FS = 34, fileXY = (c, r) => [FO.x + 21 + c * 42, FO.y + 40 + r * 44];
const FADE0 = 11.2, FADE1 = 11.7;

// stage 1: the image
out.push(`<defs><clipPath id="ci"><rect x="${IM[0]}" y="${IM[1]}" width="${4 * C}" height="${4 * C}" rx="6"/></clipPath></defs>`);
const blobs = [[112, 111, 10], [61, 189, 8], [134, 94, 7], [133, 249, 7], [92, 208, 12], [164, 161, 12], [56, 255, 8], [75, 104, 8], [190, 117, 9], [176, 156, 9], [185, 167, 8], [165, 172, 8], [188, 223, 7], [163, 187, 11], [195, 139, 12], [70, 165, 11]];
out.push(`<g clip-path="url(#ci)"><rect x="${IM[0]}" y="${IM[1]}" width="${4 * C}" height="${4 * C}" fill="#e3f2fd"/>${blobs.map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="#90caf9" opacity=".8"/>`).join('')}</g>`);
out.push(`<rect x="${IM[0]}" y="${IM[1]}" width="${4 * C}" height="${4 * C}" rx="6" fill="none" stroke="#002147" stroke-width="2"/>`);
let gl = '';
for (let q = 1; q < 4; q++) gl += `<path d="M${IM[0] + q * C} ${IM[1]}v${4 * C}M${IM[0]} ${IM[1] + q * C}h${4 * C}"/>`;
out.push(`<g stroke="#002147" stroke-width="1.5" stroke-dasharray="5 4" opacity="0">${anim('opacity', [[0, 0], [0.2, 0], [0.9, 1], [FADE0, 1], [FADE1, 0]])}${gl}</g>`);

// stage 2: the OME-Zarr folder, one file per chunk
out.push(`<path d="M${FO.x} ${FO.y + 14}v-8a6 6 0 0 1 6 -6h70l10 10h${FO.w - 92}a6 6 0 0 1 6 6v${FO.h - 16}a6 6 0 0 1 -6 6h${-(FO.w - 12)}a6 6 0 0 1 -6 -6z" fill="#f3e5f5" stroke="#6a1b9a" stroke-width="2"/>`);
const order = [];
for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) order.push([c, r]);
order.forEach(([c, r], i) => {
  const s = 1.0 + i * 0.2, [fx, fy] = fileXY(c, r), ix = IM[0] + c * C, iy = IM[1] + r * C;
  out.push(`<path d="M${fx} ${fy}h${FS - 9}l9 9v${FS - 9}h${-FS}z" fill="#fff" stroke="#6a1b9a" stroke-width="1.5" stroke-linejoin="round">${anim('fill', [[0, '#ffffff'], [s + 0.5, '#ffffff'], [s + 0.6, '#e1bee7'], [FADE1, '#e1bee7'], [FADE1 + 0.05, '#ffffff']])}</path><path d="M${fx + FS - 9} ${fy}v9h9" fill="none" stroke="#6a1b9a" stroke-width="1.2"/>`);
  // the chunk flies from the image into its file
  out.push(`<rect width="${C}" height="${C}" rx="4" fill="#fff3e0" stroke="#ef6c00" stroke-width="2" opacity="0">${anim('opacity', [[0, 0], [s - 0.01, 0], [s, 1], [s + 0.5, 1], [s + 0.6, 0]])}${anim('x', [[0, ix], [s, ix], [s + 0.55, fx]], { spline: true })}${anim('y', [[0, iy], [s, iy], [s + 0.55, fy]], { spline: true })}${anim('width', [[0, C], [s, C], [s + 0.55, FS]])}${anim('height', [[0, C], [s, C], [s + 0.55, FS]])}</rect>`);
});

// stage 3: the reader
out.push(`<rect x="${RD.x}" y="${RD.y}" width="${RD.w}" height="${RD.h}" rx="12" fill="#e3f2fd" stroke="#1565c0" stroke-width="2"/><rect x="${RD.x + 22}" y="${RD.y + 16}" width="56" height="56" rx="6" fill="#fff" stroke="#1565c0" stroke-width="1.5" stroke-dasharray="4 3"/>`);

// stage 4: table and plot
out.push(`<rect x="${TB.x}" y="${TB.y}" width="${TB.w}" height="${TB.h}" rx="6" fill="#fff" stroke="#1565c0" stroke-width="2"/><path d="M${TB.x} ${TB.y + 18}h${TB.w}" stroke="#1565c0" stroke-width="1.5"/><rect x="${TB.x + 1}" y="${TB.y + 1}" width="${TB.w - 2}" height="17" rx="5" fill="#e3f2fd"/><path d="M${TB.x + 42} ${TB.y}v${TB.h}" stroke="#1565c0" stroke-opacity=".4" stroke-width="1"/>`);
for (let q = 1; q < 4; q++) out.push(`<path d="M${TB.x} ${TB.y + 18 + q * 25}h${TB.w}" stroke="#1565c0" stroke-opacity=".25" stroke-width="1"/>`);
out.push(`<rect x="${PL.x}" y="${PL.y}" width="${PL.w}" height="${PL.h}" rx="6" fill="#fff" stroke="#1565c0" stroke-width="2"/><path d="M${PL.x + 14} ${PL.y + 12}V${PL.y + PL.h - 14}H${PL.x + PL.w - 10}" fill="none" stroke="#002147" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`);

const picks = [5, 10, 3, 14], widths = [44, 30, 56, 38], hs = [38, 62, 48, 74];
const base = PL.y + PL.h - 14;
picks.forEach((idx, j) => {
  const [c, r] = order[idx], [fx, fy] = fileXY(c, r), s = 4.6 + j * 1.4;
  const rx = RD.x + 28, ry = RD.y + 22;
  // highlight the file being fetched
  out.push(`<rect x="${fx - 4}" y="${fy - 4}" width="${FS + 8}" height="${FS + 8}" rx="6" fill="none" stroke="#1565c0" stroke-width="3" opacity="0">${anim('opacity', [[0, 0], [s - 0.2, 0], [s, 1], [s + 0.5, 1], [s + 0.7, 0]])}</rect>`);
  // the fetched chunk travels into the reader
  out.push(`<rect rx="4" fill="#e1bee7" stroke="#1565c0" stroke-width="2" opacity="0">${anim('opacity', [[0, 0], [s, 0], [s + 0.05, 1], [s + 1.05, 1], [s + 1.25, 0]])}${anim('x', [[0, fx], [s, fx], [s + 0.55, rx]], { spline: true })}${anim('y', [[0, fy], [s, fy], [s + 0.55, ry]], { spline: true })}${anim('width', [[0, FS], [s, FS], [s + 0.55, 44]])}${anim('height', [[0, FS], [s, FS], [s + 0.55, 44]])}</rect>`);
  // numbers fly on to the table and the plot
  const rowY = TB.y + 18 + j * 25 + 12.5, bx = PL.x + 26 + j * 22;
  const t1 = s + 0.75, t2 = s + 1.25;
  const cx0 = RD.x + RD.w / 2, cy0 = RD.y + RD.h / 2;
  for (const [tx, ty] of [[TB.x + 10, rowY], [bx + 6, base - hs[j]]]) {
    out.push(`<circle cx="${cx0}" cy="${cy0}" r="4.5" fill="#66bb6a" stroke="#2e7d32" stroke-width="1.2" opacity="0">${anim('opacity', [[0, 0], [t1, 0], [t1 + 0.05, 1], [t2 - 0.05, 1], [t2, 0]])}${anim('transform', [[0, '0 0'], [t1, '0 0'], [t2, `${f(tx - cx0)} ${f(ty - cy0)}`]], { type: 'translate', spline: true })}</circle>`);
  }
  out.push(`<g opacity="0">${anim('opacity', [[0, 0], [t2 - 0.05, 0], [t2 + 0.1, 1], [FADE0, 1], [FADE1, 0]])}<rect x="${TB.x + 8}" y="${rowY - 3.5}" width="24" height="7" rx="3.5" fill="#1565c0" fill-opacity=".55"/><rect x="${TB.x + 50}" y="${rowY - 3.5}" width="0" height="7" rx="3.5" fill="#2e7d32" fill-opacity=".75">${anim('width', [[0, 0], [t2, 0], [t2 + 0.3, widths[j]], [FADE1, widths[j]], [FADE1 + 0.05, 0]], { spline: true })}</rect></g>`);
  out.push(`<rect x="${bx}" y="${base}" width="12" height="0" rx="2" fill="#a5d6a7" stroke="#2e7d32" stroke-width="1.2">${anim('height', [[0, 0], [t2 - 0.05, 0], [t2 + 0.35, hs[j]], [FADE1, hs[j]], [FADE1 + 0.05, 0]], { spline: true })}${anim('y', [[0, base], [t2 - 0.05, base], [t2 + 0.35, base - hs[j]], [FADE1, base - hs[j]], [FADE1 + 0.05, base]], { spline: true })}${anim('opacity', [[0, 1], [FADE0, 1], [FADE1, 0], [FADE1 + 0.05, 1]])}</rect>`);
});
out.push('</svg>');
const svg = out.join('\n');
fs.writeFileSync(process.argv[2], svg);
console.log(svg.length, 'bytes');
