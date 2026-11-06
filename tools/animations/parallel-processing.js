// Generator for guide/assets/img/stream/parallel-processing.svg
const fs = require('fs');
const T = 10;
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
const out = [];
out.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 360" role="img" aria-labelledby="t d">`);
out.push(`<title id="t">Several chunks processed at once</title>`);
out.push(`<desc id="d">Four workers, drawn as turning wheels, each take a different chunk of the input image together with a thin border borrowed from its neighbours (the halo). They process the four chunks at the same time, trim the border, and send the results two ways: the processed chunk goes back into its place in the output image grid (the chunk assembly), and its numbers become a new row of a growing results table (the result assembly). Row by row the whole image is done.</desc>`);
out.push(`<rect width="960" height="360" rx="16" fill="#fafafa" stroke="#cfd8dc"/>`);

const C = 44, IN = [40, 92], OUTG = [560, 92];
const cellC = (o, c, r) => [o[0] + c * C + C / 2, o[1] + r * C + C / 2];
// input image
out.push(`<defs><clipPath id="ci"><rect x="${IN[0]}" y="${IN[1]}" width="${4 * C}" height="${4 * C}"/></clipPath><path id="wh" d="${(() => { let d = ''; const m = 32; for (let q = 0; q < m; q++) { const a = q / m * 2 * Math.PI, rr = q % 4 < 2 ? 21 : 16; d += (q ? 'L' : 'M') + f(rr * Math.cos(a)) + ' ' + f(rr * Math.sin(a)); } return d + 'Z'; })()}"/></defs>`);
out.push(`<rect x="${IN[0]}" y="${IN[1]}" width="${4 * C}" height="${4 * C}" rx="4" fill="#e3f2fd" stroke="#002147" stroke-width="2"/>`);
const blobs = [[87, 187, 8], [144, 200, 6], [52, 233, 8], [87, 257, 9], [180, 176, 10], [73, 201, 11], [132, 218, 10], [60, 220, 10], [97, 107, 11], [124, 214, 11], [161, 246, 8], [190, 120, 9], [150, 140, 7]];
out.push(`<g clip-path="url(#ci)">${blobs.map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="#90caf9" opacity=".8"/>`).join('')}</g>`);
let grid = '';
for (let q = 1; q < 4; q++) grid += `<path d="M${IN[0] + q * C} ${IN[1]}v${4 * C}M${IN[0]} ${IN[1] + q * C}h${4 * C}"/>`;
out.push(`<g stroke="#002147" stroke-width="1" stroke-dasharray="4 3">${grid}</g>`);
// output chunk assembly
out.push(`<rect x="${OUTG[0]}" y="${OUTG[1]}" width="${4 * C}" height="${4 * C}" rx="4" fill="#fff" stroke="#6a1b9a" stroke-width="2"/>`);
let og = '';
for (let q = 1; q < 4; q++) og += `<path d="M${OUTG[0] + q * C} ${OUTG[1]}v${4 * C}M${OUTG[0]} ${OUTG[1] + q * C}h${4 * C}"/>`;
out.push(`<g stroke="#6a1b9a" stroke-opacity=".6" stroke-width="1" stroke-dasharray="4 3">${og}</g>`);

// worker lanes (narrow) with wheels
const LX = 296, LW = 184, laneY = k => 30 + k * 80, LH = 62;
const start = r => 0.3 + r * 2.2;
const WHX = LX + 34, CHX = LX + 120;
for (let k = 0; k < 4; k++) {
  const y = laneY(k);
  out.push(`<rect x="${LX}" y="${y}" width="${LW}" height="${LH}" rx="12" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/>`);
  const rot = [[0, '0']];
  let ang = 0;
  for (let r = 0; r < 4; r++) { const s = start(r); rot.push([s + 0.5, `${ang}`]); ang += 360; rot.push([s + 1.35, `${ang}`]); }
  rot.push([T, `${ang}`]);
  out.push(`<g transform="translate(${WHX} ${y + LH / 2})"><g>${anim('transform', rot, { type: 'rotate' })}<use href="#wh" fill="#2e7d32" fill-opacity=".8"/><circle r="9" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/><path d="M-9 0H9M0 -9V9" stroke="#2e7d32" stroke-width="2"/></g></g>`);
}

// result table (result assembly)
const TX = 776, TY = 44, TW = 150, RH = 15;
out.push(`<rect x="${TX}" y="${TY}" width="${TW}" height="${18 + 16 * RH + 4}" rx="6" fill="#fff" stroke="#1565c0" stroke-width="2"/><path d="M${TX} ${TY + 18}h${TW}" stroke="#1565c0" stroke-width="1.5"/><rect x="${TX + 1}" y="${TY + 1}" width="${TW - 2}" height="17" rx="5" fill="#e3f2fd"/><path d="M${TX + 50} ${TY}v${18 + 16 * RH + 4}" stroke="#1565c0" stroke-opacity=".4" stroke-width="1"/>`);
const FADE0 = 9.45, FADE1 = 9.8;
const rowY = i => TY + 18 + 2 + i * RH;
let rows = `<g>${anim('opacity', [[0, 1], [FADE0, 1], [FADE1, 0], [T - 0.05, 0], [T, 1]])}`;
const vals = [0.55, 0.8, 0.4, 0.7, 0.9, 0.5, 0.65, 0.35, 0.75, 0.6, 0.85, 0.45, 0.7, 0.55, 0.95, 0.5];

// chunks
for (let r = 0; r < 4; r++) {
  const s = start(r);
  // halos on the input grid
  for (let k = 0; k < 4; k++) {
    const [cx, cy] = cellC(IN, k, r);
    out.push(`<rect x="${cx - C / 2 - 7}" y="${cy - C / 2 - 7}" width="${C + 14}" height="${C + 14}" rx="3" fill="none" stroke="#ef6c00" stroke-width="2" stroke-dasharray="5 3" opacity="0">${anim('opacity', [[0, 0], [s - 0.25, 0], [s, 1], [s + 0.2, 1], [s + 0.45, 0]])}</rect>`);
  }
  for (let k = 0; k < 4; k++) {
    const [ix, iy] = cellC(IN, k, r), [ox, oy] = cellC(OUTG, k, r), lx = CHX + k * 0, ly = laneY(k) + LH / 2;
    const t1 = s + 0.5, w1 = s + 1.35, t2 = s + 1.9;
    const pos = [[0, `${ix} ${iy}`], [s, `${ix} ${iy}`], [t1, `${lx} ${ly}`], [w1, `${lx} ${ly}`], [t2, `${ox} ${oy}`], [FADE1, `${ox} ${oy}`], [FADE1 + 0.05, `${ix} ${iy}`]];
    const col = [[0, '#bbdefb'], [t1 + 0.1, '#bbdefb'], [w1 - 0.2, '#ffb74d'], [FADE1, '#ffb74d'], [FADE1 + 0.05, '#bbdefb']];
    const op = [[0, 0], [s - 0.01, 0], [s, 1], [FADE0, 1], [FADE1, 0]];
    const halo = [[0, 1], [w1 - 0.2, 1], [w1, 0], [FADE1, 0], [FADE1 + 0.05, 1]];
    // halo shrinks onto the chunk while it is trimmed
    out.push(`<g transform="translate(${ix} ${iy})" opacity="0">${anim('opacity', op)}${anim('transform', pos, { type: 'translate', spline: true })}<rect x="${-C / 2 - 7}" y="${-C / 2 - 7}" width="${C + 14}" height="${C + 14}" rx="3" fill="#fff3e0" stroke="#ef6c00" stroke-width="1.5" stroke-dasharray="5 3">${anim('opacity', halo)}</rect><rect x="${-C / 2 + 1}" y="${-C / 2 + 1}" width="${C - 2}" height="${C - 2}" rx="3" fill="#bbdefb" stroke="#002147" stroke-width="1.5">${anim('fill', col)}</rect></g>`);
    // numbers fly to the table
    const i = r * 4 + k, ry = rowY(i) + RH / 2 - 1, tt = w1 + 0.05 + k * 0.06;
    out.push(`<circle cx="${lx + C / 2}" cy="${ly}" r="4" fill="#66bb6a" stroke="#2e7d32" stroke-width="1.2" opacity="0">${anim('opacity', [[0, 0], [tt, 0], [tt + 0.05, 1], [tt + 0.5, 1], [tt + 0.55, 0]])}${anim('transform', [[0, '0 0'], [tt, '0 0'], [tt + 0.55, `${TX + 10 - lx - C / 2} ${ry - ly}`]], { type: 'translate', spline: true })}</circle>`);
    rows += `<g opacity="0">${anim('opacity', [[0, 0], [tt + 0.5, 0], [tt + 0.65, 1], [FADE1, 1], [FADE1 + 0.05, 0]])}<rect x="${TX + 10}" y="${ry - 3}" width="30" height="6" rx="3" fill="#1565c0" fill-opacity=".5"/><rect x="${TX + 60}" y="${ry - 3}" width="${f(vals[i] * 80)}" height="6" rx="3" fill="#2e7d32" fill-opacity=".75"/></g>`;
  }
}
out.push(rows + '</g>');
out.push('</svg>');
const svg = out.join('\n');
fs.writeFileSync(process.argv[2], svg);
console.log(svg.length, 'bytes');
