// GreenPulse mid-sem deck (Role 4). Text from docs/deck_outline.md; figures from figures/.
// Usage: npm install pptxgenjs  then  node scripts/13_build_deck.js docs/GreenPulse_midsem.pptx
const pptxgen = require('pptxgenjs');
const path = require('path');
const sizeOf = (p) => {
  // PNG width/height from the IHDR chunk.
  const b = require('fs').readFileSync(p);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
};

const REPO = path.resolve(__dirname, '..');
const FIG = (n) => path.join(REPO, 'figures', n);
const OUT = process.argv[2] || 'GreenPulse_midsem.pptx';

const C = {
  forest: '1F4D3A', forestDeep: '163A2B', leaf: 'E9F1EB', leafMid: 'C9DECF',
  heat: 'C8640A', ink: '1F2328', muted: '5F6670', line: 'D7DDD9', white: 'FFFFFF',
};
const HEAD = 'Cambria', BODY = 'Calibri';
const W = 10, H = 5.625, M = 0.5;

const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = 'GreenPulse: mid-semester evaluation';

// ---------- helpers ----------
function header(s, section, title, presenter) {
  s.background = { color: C.white };
  s.addText(section.toUpperCase(), {
    x: M, y: 0.28, w: 2.2, h: 0.26, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 9, bold: true, color: C.forest, charSpacing: 2,
  });
  s.addText(presenter, {
    x: W - M - 3, y: 0.28, w: 3, h: 0.26, isTextBox: true, margin: 0, align: 'right',
    fontFace: BODY, fontSize: 9, color: C.muted,
  });
  s.addText(title, {
    x: M, y: 0.55, w: W - 2 * M, h: 0.75, isTextBox: true, margin: 0, valign: 'top',
    fontFace: HEAD, fontSize: 20, bold: true, color: C.ink, fit: 'shrink',
  });
}
function caption(s, text, y = H - 0.38) {
  s.addText(text, {
    x: M, y, w: W - 2 * M, h: 0.24, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 8.5, color: C.muted, italic: true,
  });
}
function img(s, file, x, y, opt = {}) {
  const { w: pw, h: ph } = sizeOf(FIG(file));
  const r = pw / ph;
  let w = opt.w, h = opt.h;
  if (w && !h) h = w / r;
  if (h && !w) w = h * r;
  if (opt.w && opt.h) { // fit inside box, keep ratio, centre
    if (opt.w / opt.h > r) { w = opt.h * r; h = opt.h; x += (opt.w - w) / 2; }
    else { w = opt.w; h = opt.w / r; y += (opt.h - h) / 2; }
  }
  s.addImage({ path: FIG(file), x, y, w, h, altText: file });
  return { x, y, w, h };
}
function bullets(s, items, x, y, w, h, size = 13) {
  const runs = [];
  items.forEach((it, i) => {
    const last = i === items.length - 1;
    const level = typeof it === 'object' && it.sub ? 1 : 0;
    const parts = typeof it === 'string' ? [{ t: it }] : (it.parts || [{ t: it.t }]);
    parts.forEach((p, j) => {
      runs.push({
        text: p.t,
        options: {
          bold: !!p.b, color: p.c || C.ink,
          bullet: j === 0 ? (level ? { indent: 14 } : { indent: 14 }) : undefined,
          indentLevel: j === 0 ? level : undefined,
          breakLine: j === parts.length - 1 && !last,
          paraSpaceAfter: j === parts.length - 1 ? 5 : undefined,
        },
      });
    });
  });
  s.addText(runs, {
    x, y, w, h, isTextBox: true, margin: 0, valign: 'top',
    fontFace: BODY, fontSize: size, color: C.ink, fit: 'shrink',
  });
}
function stat(s, x, y, w, big, label, color = C.forest, bigSize = 26) {
  s.addText(big, {
    x, y, w, h: 0.55, isTextBox: true, margin: 0, valign: 'bottom',
    fontFace: HEAD, fontSize: bigSize, bold: true, color,
  });
  s.addText(label, {
    x, y: y + 0.57, w, h: 0.6, isTextBox: true, margin: 0, valign: 'top',
    fontFace: BODY, fontSize: 10.5, color: C.muted, fit: 'shrink',
  });
}
function card(s, x, y, w, h, fill = C.leaf) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill },
  });
}
function cardText(s, x, y, w, h, head, body, size = 11.5, headColor = C.forest) {
  s.addText([
    { text: head, options: { bold: true, color: headColor, fontSize: size + 1.5, breakLine: true, paraSpaceAfter: 4 } },
    { text: body, options: { color: C.ink, fontSize: size } },
  ], { x: x + 0.18, y: y + 0.14, w: w - 0.36, h: h - 0.28, isTextBox: true, margin: 0, valign: 'top', fontFace: BODY, fit: 'shrink' });
}
function arrow(s, x, y, w) {
  s.addShape(pres.shapes.RIGHT_ARROW, { x, y, w, h: 0.28, fill: { color: C.leafMid }, line: { color: C.leafMid } });
}
function numCircle(s, x, y, label, fill = C.forest) {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.42, h: 0.42, fill: { color: fill }, line: { color: fill } });
  s.addText(label, { x, y, w: 0.42, h: 0.42, isTextBox: true, margin: 0, align: 'center', valign: 'middle',
    fontFace: BODY, fontSize: 11, bold: true, color: C.white });
}
function table(s, rows, x, y, w, colW, size = 11) {
  const head = rows[0].map((t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.forest } } }));
  const body = rows.slice(1).map((r, i) => r.map((t) => ({
    text: t, options: { color: C.ink, fill: { color: i % 2 ? C.white : C.leaf } },
  })));
  s.addTable([head, ...body], {
    x, y, w, colW, fontFace: BODY, fontSize: size, valign: 'middle',
    border: { type: 'solid', color: C.line, pt: 0.5 }, margin: [3, 6, 3, 6],
  });
}

// ---------- 1. Title ----------
{
  const s = pres.addSlide();
  s.background = { color: C.forestDeep };
  s.addText('NATURE-BASED SOLUTIONS FOR URBAN HEAT · MID-SEMESTER EVALUATION', {
    x: M, y: 0.9, w: 9, h: 0.3, isTextBox: true, margin: 0, fontFace: BODY, fontSize: 10, bold: true, color: C.leafMid, charSpacing: 2,
  });
  s.addText('GreenPulse', {
    x: M, y: 1.35, w: 9, h: 0.9, isTextBox: true, margin: 0, fontFace: HEAD, fontSize: 48, bold: true, color: C.white,
  });
  s.addText('Does urban vegetation cool Indian cities, and when?', {
    x: M, y: 2.3, w: 9, h: 0.6, isTextBox: true, margin: 0, fontFace: HEAD, fontSize: 24, italic: true, color: C.leafMid,
  });
  s.addText('303 cities · 3 seasons · 1 km satellite squares · 2019–2024', {
    x: M, y: 3.05, w: 9, h: 0.35, isTextBox: true, margin: 0, fontFace: BODY, fontSize: 14, color: 'F2B66D',
  });
  s.addText('Atharv Johar · Himani Das · Ishaan Karan · Nidhi Vaidya · Prajna Penmetsa', {
    x: M, y: 4.55, w: 9, h: 0.35, isTextBox: true, margin: 0, fontFace: BODY, fontSize: 13, color: C.white,
  });
  s.addNotes('Presenter: Role 4. One line: we test whether existing greenery cools Indian cities, and under what conditions it cools most.');
}

// ---------- 2. Problem ----------
{
  const s = pres.addSlide();
  header(s, 'Problem', 'Cities are hotter than their surroundings, and greening is the go-to fix', 'Presenter: Role 4');
  bullets(s, [
    'Dense buildings, sealed surfaces and waste heat make cities hotter than the land around them.',
    'Trees, parks and green space are promoted as low-cost cooling: through shade, and through evaporation from leaves.',
    { parts: [{ t: 'Trees cool 2–3× more than grass or green roofs ' }, { t: '(Kim et al. 2024)', c: C.muted }] },
  ], M, 1.45, 5.2, 2.1, 14);
  stat(s, 6.2, 1.4, 3.3, '+1.5 °C', 'urban surfaces by day, 419 cities (Peng et al. 2012); +1.1 °C at night', C.heat, 28);
  stat(s, 6.2, 2.55, 3.3, '0.94 °C', 'cooler in parks by day, meta-analysis (Bowler et al. 2010)', C.forest, 28);
  card(s, M, 3.85, W - 2 * M, 1.15, C.forest);
  s.addText([
    { text: 'Our question  ', options: { bold: true, color: 'F2B66D' } },
    { text: 'Can existing urban vegetation measurably reduce heat exposure, and under what environmental conditions is the cooling effect strongest?', options: { color: C.white } },
  ], { x: M + 0.25, y: 3.95, w: W - 2 * M - 0.5, h: 0.95, isTextBox: true, margin: 0, valign: 'middle', fontFace: HEAD, fontSize: 16 });
  s.addNotes([
    'The question has two halves: does greenery cool at all, and where and when does it cool most?',
    'The second half is the interesting one, and it is where the literature disagrees (next slide).',
    'Peng 2012 numbers are MODIS surface temperature; Bowler 2010 is air temperature in parks.',
  ].join('\n'));
}

// ---------- 3. Debate ----------
{
  const s = pres.addSlide();
  header(s, 'Problem', 'The evidence disagrees on dry climates, and mostly measures surface heat', 'Presenter: Role 4');
  const cw = (W - 2 * M - 0.3) / 2;
  card(s, M, 1.4, cw, 1.95, 'FBEBDD');
  cardText(s, M, 1.4, cw, 1.95, 'Dry cities cool LESS',
    'Guo et al. 2026 (761 cities): in 22% of cities under 1,000 mm/yr, vegetation causes net warming.\n\nSchwaab et al. 2021 (293 cities): under hot extremes, trees cool less in the dry south of Europe (0–4 K) than in central Europe (8–12 K).', 11, C.heat);
  card(s, M + cw + 0.3, 1.4, cw, 1.95);
  cardText(s, M + cw + 0.3, 1.4, cw, 1.95, 'Dry cities cool MORE',
    'Manoli et al. 2019: greening is more efficient in dry regions, but only with irrigation.\n\nYang et al. 2022 (510 cities): tree cooling efficiency is higher in hot, dry cities.', 11);
  const tw = (W - 2 * M - 0.4) / 3;
  const items = [
    ['Humid cities: a new warning', 'Borah et al. 2026, 138 Indian cities: high canopy activity goes with a higher Heat Index at pre-monsoon midday (an association).'],
    ['The metric problem', 'Satellites overstate the heat island ~6× vs air temperature (Venter 2021); tree cooling ~12× (Du 2024).'],
    ['The geography gap', 'Most evidence is from Europe, China and North America. India spans desert to very wet.'],
  ];
  items.forEach(([h, b], i) => {
    const x = M + i * (tw + 0.2);
    s.addText([
      { text: h, options: { bold: true, color: C.forest, breakLine: true, paraSpaceAfter: 3 } },
      { text: b, options: { color: C.ink } },
    ], { x, y: 3.55, w: tw, h: 1.55, isTextBox: true, margin: 0, valign: 'top', fontFace: BODY, fontSize: 10.5, fit: 'shrink' });
  });
  s.addNotes([
    'India spans the whole moisture range, from Jodhpur (desert) to Kochi (very wet), so it is a natural place to test the dry-climate disagreement.',
    'Which paper does each step follow? Cooling slope: Yang 2022, Schwaab 2021. Background climate: Zhao 2014, Manoli 2019, Guo 2026. 1,000 mm threshold: Guo, Manoli. Day vs night: Yang 2022, Du 2024, Ibsen 2021. Heat Index: Borah 2026. People-weighting: Chakraborty 2019, Chen 2022, Li 2024. No monsoon: Kumar 2017. Surface overstates felt heat: Venter 2021, Du 2024.',
  ].join('\n'));
}

// ---------- 4. Hypotheses ----------
{
  const s = pres.addSlide();
  header(s, 'Problem', 'Five hypotheses we test at mid-sem', 'Presenter: Role 4');
  const hs = [
    ['H1', 'Greener squares are cooler by day in most cities.'],
    ['H2', 'The cooling slope changes with background moisture. We test which way.'],
    ['H3', 'Night cooling is weaker, and may reverse in dry cities.'],
    ['H4', 'The same city cools differently before and after the monsoon.'],
    ['H5', 'Crowded squares are less green and hotter, so people feel more heat than the city average.'],
  ];
  hs.forEach(([k, t], i) => {
    const y = 1.45 + i * 0.66;
    numCircle(s, M, y, k);
    s.addText(t, { x: M + 0.6, y: y - 0.06, w: 8.4, h: 0.55, isTextBox: true, margin: 0, valign: 'middle', fontFace: BODY, fontSize: 14, color: C.ink });
  });
  s.addText('After mid-sem: H6, turning surface cooling into felt heat (Heat Index).', {
    x: M + 0.6, y: 4.85, w: 8.3, h: 0.3, isTextBox: true, margin: 0, fontFace: BODY, fontSize: 12, italic: true, color: C.muted,
  });
  s.addNotes('Each hypothesis maps to a result slide: H1 slide 12, H2 slides 11 and 13, H3 slides 11 and 13, H4 slide 14, H5 slide 15.');
}

// ---------- 5. Data ----------
{
  const s = pres.addSlide();
  header(s, 'Data', 'Seven open datasets, all in Google Earth Engine except OpenStreetMap', 'Presenter: Role 1');
  table(s, [
    ['Dataset', 'Resolution', 'Used for'],
    ['MODIS LST (Aqua, MYD11A2)', '1 km, 8-day, ~13:30 / ~01:30', 'Day and night surface temperature'],
    ['MODIS vegetation (MOD13A1)', '500 m → 1 km', 'Greenness: NDVI (main), EVI (check)'],
    ['ERA5-Land', '~9 km', 'City climate: rain, temperature, humidity, soil moisture, Heat Index'],
    ['GHSL built-up (2020)', '100 m', 'Built-up share: control and urban filter'],
    ['WorldPop (2020)', '100 m', 'People per square'],
    ['OpenStreetMap', 'Vector', 'Water share per square'],
    ['SRTM', '30 m', 'Elevation, a control'],
  ], M, 1.45, W - 2 * M, [2.6, 2.3, 4.1], 11.5);
  caption(s, 'Everything finer than 1 km is averaged up to the 1 km temperature grid, never the other way round.', 4.95);
  s.addNotes([
    'All seven are free and open. The professor assigned five; we added SRTM elevation as a control and use OpenStreetMap only for water.',
    'Aqua, not Terra: its ~13:30 overpass is closer to the hottest part of the day.',
    'LST is surface temperature (roofs, roads, leaves), not the air temperature people feel (Venter 2021; Du 2024).',
    'Likely question, why 1 km when GHSL and WorldPop are 100 m: 1 km is the native MODIS LST resolution; shrinking it would invent detail the satellite never measured.',
  ].join('\n'));
}

// ---------- 6. Study area ----------
{
  const s = pres.addSlide();
  header(s, 'Data', '303 Indian cities across the full moisture range, in three seasons', 'Presenter: Role 1');
  img(s, 'B_city_map.png', M, 1.35, { w: 4.2, h: 3.75 });
  bullets(s, [
    { parts: [{ t: 'Cities: ', b: true }, { t: 'every Indian urban centre over 3 lakh people (GHS Urban Centre Database), 303 in all.' }] },
    { parts: [{ t: 'Rainfall: ', b: true }, { t: '262 mm (Bikaner) to 3,792 mm (Darjeeling). Jodhpur 411 mm, Kochi 3,131 mm. 72 cities under 1,000 mm.' }] },
    { parts: [{ t: 'Seasons: ', b: true }, { t: 'pre-monsoon (Apr–May), post-monsoon (Oct–Nov), winter (Dec–Feb).' }] },
    { parts: [{ t: 'Years: ', b: true }, { t: '2019–2024 averages, so no single year dominates.' }] },
    { parts: [{ t: 'Seasons differ: ', b: true }, { t: 'median square 39.7 °C by day pre-monsoon, 31.2 °C post-monsoon, 27.9 °C winter.' }] },
  ], 5.0, 1.45, 4.5, 3.6, 12.5);
  caption(s, 'City outlines: GHS-UCDB R2024A · Boundary: Natural Earth (India point of view) · Rainfall: ERA5-Land 2019–2024 (city_climate.csv)');
  s.addNotes([
    'A "city" is a GHSL urban centre: connected 1 km cells with at least 1,500 people/km² and 50,000 people in total. Same rule in every state, unlike municipal boundaries.',
    '53,614 squares of 1 km, about 297 million people (WorldPop 2020).',
    'Likely question, why not the monsoon: next slide (Role 5). Kumar et al. 2017 excluded it for the same reason.',
    'Cloud measure on this slide: the other three seasons keep 94–98% of 8-day images after quality filtering (median over land squares). Slide 6b uses a different measure (all squares, water counted as unusable).',
    'Likely question, why is Kochi warmer in winter: Kerala\'s April–May is already wet (622 mm in Kochi); winter is dry and sunny.',
  ].join('\n'));
}

// ---------- 6b. Monsoon ----------
{
  const s = pres.addSlide();
  header(s, 'Data', 'No monsoon season: cloud leaves too few usable satellite images', 'Presenter: Role 5');
  stat(s, M, 1.3, 2.6, '85% → 25%', 'usable daytime images in Mumbai, Apr–May vs Jun–Sep', C.heat, 26);
  stat(s, 3.4, 1.3, 2.6, '19%', 'Kolkata in Jun–Sep, the lowest of six cities checked', C.heat, 26);
  s.addText('Kumar et al. (2017) also excluded June–September for cloud.', {
    x: 6.3, y: 1.45, w: 3.2, h: 0.8, isTextBox: true, margin: 0, fontFace: BODY, fontSize: 12, italic: true, color: C.muted, valign: 'middle',
  });
  img(s, 'M_lst_availability.png', M, 2.6, { w: W - 2 * M, h: 2.5 });
  caption(s, 'Share of 8-day images passing the quality filter, averaged over every square in the outline (water counts as unusable). lst_availability_by_month.csv');
  s.addNotes([
    'Same MODIS quality mask as the main pipeline, measured month by month over 2019–2024 in six cities.',
    'The loss is large and uneven between cities, so monsoon estimates would rest on very different amounts of data.',
    'This measure averages over all squares including water, so Mumbai\'s 85% here is lower than slide 6\'s land-only ~98%. Compare months within this chart.',
    'Likely question, why not keep the monsoon with fewer images: coverage is too uneven between cities to compare fairly.',
  ].join('\n'));
}

// ---------- 7. Method: sampling ----------
{
  const s = pres.addSlide();
  header(s, 'Method', 'Each city becomes a grid of 1 km squares', 'Presenter: Role 1');
  const steps = [
    ['1 km MODIS grid', 'Every square inside the city outline'],
    ['Quality filter', 'Keep readings rated reliable (error ≤ 2 K); no reading = open water'],
    ['Seasonal means', '2019–2024: day/night LST, NDVI, EVI, built-up, people, elevation'],
    ['Urban squares', 'Keep squares at least 10% built-up'],
  ];
  const bw = 1.95, gap = 0.35;
  steps.forEach(([h, b], i) => {
    const x = M + i * (bw + gap);
    card(s, x, 1.55, bw, 1.75);
    numCircle(s, x + 0.15, 1.7, String(i + 1));
    s.addText([
      { text: h, options: { bold: true, color: C.forest, breakLine: true, paraSpaceAfter: 3, fontSize: 13 } },
      { text: b, options: { color: C.ink, fontSize: 11 } },
    ], { x: x + 0.15, y: 2.2, w: bw - 0.3, h: 1.05, isTextBox: true, margin: 0, valign: 'top', fontFace: BODY, fit: 'shrink' });
    if (i < steps.length - 1) arrow(s, x + bw + 0.04, 2.28, gap - 0.08);
  });
  stat(s, M, 3.6, 2.6, '202 of 303', 'cities have ≥ 30 urban squares, our minimum for an estimate', C.forest, 24);
  bullets(s, [
    { parts: [{ t: 'Checked: ', b: true }, { t: 'reproduces the pilot exactly (Jodhpur 254 squares, Kochi 1,238); population within 0.02% of WorldPop; range checks on all 303 cities.' }] },
  ], 3.6, 3.7, 5.9, 1.2, 12);
  s.addNotes([
    'Quality filter: keep "good" readings, plus "other quality" readings with error at most 2 K. Cloudy readings are dropped before averaging.',
    'Dropped: squares with no temperature are open water (the same squares are missing in every season, so not cloud); squares under 10% built-up are not urban; cities with fewer than 30 urban squares get no estimate (101 of 303).',
    'Likely question, how do you know missing squares are water: a cloudy square would be missing in some seasons only. In all 303 cities the same squares are missing in all three seasons.',
  ].join('\n'));
}

// ---------- 8. Method: regression ----------
{
  const s = pres.addSlide();
  header(s, 'Method', 'The cooling slope: how much cooler greener squares are, other things equal', 'Presenter: Role 3');
  card(s, M, 1.4, W - 2 * M, 0.62, C.forest);
  s.addText('LST = b0 + b1·NDVI + b2·built + b3·elevation + b4·water      cooling slope = b1 ÷ 10  (°C per 0.1 NDVI)', {
    x: M + 0.2, y: 1.4, w: W - 2 * M - 0.4, h: 0.62, isTextBox: true, margin: 0, valign: 'middle', fontFace: 'Courier New', fontSize: 12.5, color: C.white, bold: true,
  });
  img(s, 'A_pilot_raw_vs_adjusted.png', M, 2.2, { w: 6.0 });
  bullets(s, [
    { parts: [{ t: 'Negative = greener squares are cooler.', b: true, c: C.heat }] },
    { parts: [{ t: 'Why controls: ', b: true }, { t: 'Jodhpur raw −0.59 (not significant) → −1.32 holding built-up fixed. Bare desert outskirts hide the effect.' }] },
    { parts: [{ t: 'Why clustered uncertainty: ', b: true }, { t: 'neighbouring squares are alike, so 95% ranges treat ~5 km blocks as one unit.' }] },
    { parts: [{ t: 'One fit ', b: true }, { t: 'per city × season × day/night, within a city, so climate is held fixed.' }] },
  ], 6.75, 2.2, 2.75, 2.9, 11.5);
  s.addNotes([
    'About 29,000 fits in all, including robustness variants. Each uses all urban squares (built ≥ 10%) of one city.',
    'Likely question, is this causal: no. It is an association with built-up share, elevation and water held fixed.',
  ].join('\n'));
}

// ---------- 9. Method: climate + people ----------
{
  const s = pres.addSlide();
  header(s, 'Method', 'Climate is one value per city; exposure is weighted by people', 'Presenter: Role 2 (climate) · Role 4 (people)');
  const cw = (W - 2 * M - 0.3) / 2;
  card(s, M, 1.45, cw, 3.55);
  cardText(s, M, 1.45, cw, 3.55, 'Background climate (ERA5-Land, ~9 km)',
    '9 km cannot resolve neighbourhoods, so it describes the climate each city sits in.\n\nDryness: annual rainfall (main), soil moisture (second). Potential evaporation is unreliable in arid areas, so not used.\n\nHeat Index: computed daily (NOAA formula) from the day\'s maximum temperature and mean dewpoint, then averaged.', 12);
  card(s, M + cw + 0.3, 1.45, cw, 3.55);
  cardText(s, M + cw + 0.3, 1.45, cw, 3.55, 'People-weighting (WorldPop 2020)',
    'Each square\'s temperature is weighted by how many people live there.\n\nGap = people-weighted minus plain average.\n\nGap > 0: people live in hotter-than-average squares. Same urban squares and 30-square minimum as the cooling slope.', 12);
  s.addNotes([
    'Role 2: one value per city per season. A monthly-mean Heat Index would understate the hot afternoons, hence daily. Neither rainfall nor soil moisture sees irrigation (Manoli 2019).',
    'Role 4: comparing people-weighted with plain averages shows whether the heat sits where people are.',
    'Likely question, can one climate value describe a whole city: it describes the background climate we compare across cities; differences inside a city come from the 1 km squares.',
  ].join('\n'));
}

// ---------- 10. Pilot ----------
{
  const s = pres.addSlide();
  header(s, 'Results', 'Pilot: greener squares are cooler by day in both a desert city and a wet one', 'Presenter: Role 3');
  img(s, 'A_pilot_scatter.png', M, 1.35, { w: 4.9, h: 3.8 });
  stat(s, 5.75, 1.4, 3.75, '−1.32 °C', 'Jodhpur (desert), per 0.1 NDVI by day · 95%: −1.98 to −0.67', C.forest, 26);
  stat(s, 5.75, 2.55, 3.75, '−1.04 °C', 'Kochi (wet), per 0.1 NDVI by day · 95%: −1.57 to −0.51', C.forest, 26);
  stat(s, 5.75, 3.7, 3.75, '+0.62 °C', 'Jodhpur at night: greener is warmer (only once built-up is controlled)', C.heat, 26);
  caption(s, 'Pilot spec (built-up control only). Final spec with elevation and water: Jodhpur −1.45, Kochi −1.90. cooling_efficiency.csv');
  s.addNotes([
    'Each dot is a 1 km square with built-up share removed from both axes; the line slope equals the regression coefficient exactly.',
    'Jodhpur\'s warm green nights are not unusual: before the monsoon 24% of 135 cities have significantly greener-is-warmer nights, mostly dry ones.',
    'Likely question, why does Kochi change with controls: water. Water squares are cool and low in NDVI; adding the water control moves Kochi from −1.44 to −1.90.',
  ].join('\n'));
}

// ---------- 11. Headline ----------
{
  const s = pres.addSlide();
  header(s, 'Results', 'By day, cooling does not depend on rainfall; at night, wetter cities cool more', 'Presenter: Role 2');
  img(s, 'D_ce_vs_rain.png', M, 1.35, { w: 6.5, h: 3.8 });
  stat(s, 7.2, 1.45, 2.3, '+0.17', 'day, pre-monsoon, per 10× rain · 95% CI −0.73 to +1.07: no trend', C.muted, 24);
  stat(s, 7.2, 2.6, 2.3, '−1.16', 'night, pre-monsoon, per 10× rain (135 cities): wetter cools more', C.forest, 24);
  stat(s, 7.2, 3.75, 2.3, '−0.98', 'night, post-monsoon (141 cities)', C.forest, 24);
  caption(s, 'Top row day, bottom row night; one column per season; 202 cities by day. main_result_regressions.csv');
  s.addNotes([
    'Each dot is a city\'s cooling slope; the line is a regression across cities weighting precise cities more. A flat daytime line means greener squares are about as much cooler in Jodhpur\'s climate as in Kochi\'s.',
    'By day this supports neither side of the dry-climate debate. At night it sides with Guo and Schwaab (weaker cooling in dry places).',
    'The night trend holds unweighted, with capped weights, without few-block cities, and with city size, air temperature and density added (pre −0.92, post −0.77).',
    'By day the honest summary is "no robust pattern": one coastal city alone can flip the pre-monsoon sign.',
  ].join('\n'));
}

// ---------- 12. Map ----------
{
  const s = pres.addSlide();
  header(s, 'Results', 'Greener is cooler by day almost everywhere in India', 'Presenter: Role 2');
  img(s, 'D_ce_map_pre_day.png', M, 1.3, { w: 4.6, h: 3.85 });
  stat(s, 5.6, 1.45, 3.9, '151 of 202', 'cities (75%) cool significantly by day before the monsoon; 191 have a negative slope', C.forest, 26);
  stat(s, 5.6, 2.6, 3.9, '2%', 'significantly greener-is-warmer by day: rare and scattered, no region stands out', C.heat, 26);
  stat(s, 5.6, 3.75, 3.9, '101', 'cities too small for an estimate (fewer than 30 urban squares)', C.muted, 26);
  caption(s, 'Blue = cooling, red = warming, hollow = not significant, size = population. Pre-monsoon, day. cooling_efficiency.csv');
  s.addNotes([
    'Hollow markers lean towards small cities: fewer squares, wider 95% range. The most extreme slopes on both ends are also small cities.',
    'Likely question, is there a regional pattern: not by day; slide 11 tests that formally.',
  ].join('\n'));
}

// ---------- 13. Threshold ----------
{
  const s = pres.addSlide();
  header(s, 'Results', 'Dry Indian cities do not warm by day; their green squares warm at night', 'Presenter: Role 2');
  table(s, [
    ['Pre-monsoon', 'Cities', 'Median slope', 'Significant cooling', 'Greener-is-warmer'],
    ['Day, < 1,000 mm', '56', '−1.06', '77%', '0%'],
    ['Day, ≥ 1,000 mm', '146', '−1.18', '74%', '3%'],
    ['Night, < 1,000 mm', '39', '+0.46', '5%', '38%'],
    ['Night, ≥ 1,000 mm', '96', '−0.03', '24%', '18%'],
  ], M, 1.45, 5.6, [1.6, 0.75, 1.05, 1.15, 1.05], 11.5);
  card(s, 6.45, 1.45, 3.05, 2.3, 'FBEBDD');
  cardText(s, 6.45, 1.45, 3.05, 2.3, 'Against Guo et al. 2026',
    'Guo found 22% net warming under 1,000 mm. By day we find none (0 of 56 dry cities). At night, 38% of dry cities have warmer green squares, twice the wet share (18%).', 11, C.heat);
  bullets(s, [
    'Warm green nights fall steadily with rainfall: 50% under 750 mm, 28% at 750–1,500 mm, 3% over 1,500 mm.',
    'With a 6-night cut-off (48 dry cities) the night result is stronger: 54% vs 18%.',
  ], M, 3.95, W - 2 * M, 1.1, 12);
  caption(s, 'Slopes in °C per 0.1 NDVI; negative = greener is cooler. main_result_bins.csv');
  s.addNotes([
    'Why not Guo\'s daytime warming? Guo\'s cities are arid worldwide; India\'s dry cities are semi-arid, and much urban greenery is watered (Manoli 2019), which rainfall cannot see. Different method, so a contrast, not a replication.',
    'Likely question, are the night numbers reliable with so few dry cities: only 39 dry cities have night estimates, but the result strengthens with a 6-night cut-off.',
  ].join('\n'));
}

// ---------- 14. Seasons ----------
{
  const s = pres.addSlide();
  header(s, 'Results', 'In the same city, daytime cooling weakens after the monsoon; night cooling strengthens', 'Presenter: Role 3');
  img(s, 'S_season_paired.png', M, 1.4, { w: 6.1 });
  stat(s, 6.85, 1.45, 2.65, '81%', 'of 202 cities cool less by day after the monsoon (median +0.43; Wilcoxon p ≈ 7e-19)', C.heat, 26);
  stat(s, 6.85, 2.6, 2.65, '69%', 'of 127 cities cool more at night after the monsoon (median −0.16)', C.forest, 26);
  bullets(s, [
    'Same city, same squares, different season: everything fixed about the city cancels out.',
    'Soil wetting does not clearly explain the change (−1.71 per m³/m³, 95% CI −3.65 to +0.24, p = 0.09).',
  ], M, 4.35, W - 2 * M, 0.8, 11.5);
  caption(s, 'Backup figure: S_dce_vs_dsoil.png. seasons.csv, seasons_summary.csv');
  s.addNotes([
    'Our cleanest test of conditions (H4), because the city is held fixed.',
    'Pre-monsoon daytime cooling is strongest (median −1.13 vs −0.67 post, −0.81 winter). One untested reading: most sun and hottest surfaces in Apr–May, so more heat for vegetation to offset.',
    'Likely question, is it just noise: across 202 cities Wilcoxon p ≈ 7e-19; per city 30% significantly weaker vs 2% stronger, with a conservative standard error.',
  ].join('\n'));
}

// ---------- 15. Exposure ----------
{
  const s = pres.addSlide();
  header(s, 'Results', 'Crowded squares are less green, and the less green they are, the hotter', 'Presenter: Role 4');
  img(s, 'F_exposure_by_season.png', M, 1.3, { w: 4.7, h: 3.15 });
  img(s, 'F_crowded_vs_green.png', 5.35, 1.3, { w: 4.15, h: 3.15 });
  const sw = (W - 2 * M - 0.6) / 4;
  [['90–96%', 'cities where crowded squares are less green'],
   ['96–97%', 'people live in hotter squares at night'],
   ['ρ ≈ −0.73', 'less green crowded squares → bigger heat gap'],
   ['+1.08 °C', 'largest gap, Kolkata (median +0.1 to +0.2)']].forEach(([b, l], i) => {
    s.addText([
      { text: b, options: { bold: true, color: i === 3 ? C.heat : C.forest, fontSize: 15, fontFace: HEAD, breakLine: true } },
      { text: l, options: { color: C.muted, fontSize: 9.5 } },
    ], { x: M + i * (sw + 0.2), y: 4.5, w: sw, h: 0.78, isTextBox: true, margin: 0, valign: 'top', fontFace: BODY, fit: 'shrink' });
  });
  s.addNotes([
    'People-weighting: each square\'s temperature weighted by the people living there (WorldPop 2020), compared with the plain average.',
    'Night is the clearest result (135–157 cities with night data; humid cities under-represented because of cloud). By day 63% pre-monsoon, 87% post-monsoon, 73% winter.',
    'Before the monsoon some large cities go the other way: Surat, Pune, Mumbai, Kozhikode, Indore, Nagpur, Jaipur. Most are wet, so it is not simply a dry-city effect; the reason is not established.',
    'Rainfall makes only a small difference, and only pre-monsoon (55% of dry vs 66% of wet cities).',
    'Population density, not income: say "crowded", never "poor". Chakraborty et al. 2019 found poorer neighbourhoods hotter in 72% of 25 cities.',
    'Likely question, is +0.1 °C meaningful: the point is the direction (almost every city at night) and the link to greenness; in some cities it is about 1 °C. Surface temperature overstates felt heat.',
  ].join('\n'));
}

// ---------- 15b. Water ----------
{
  const s = pres.addSlide();
  header(s, 'Results', 'Water does not explain away the vegetation effect', 'Presenter: Role 5');
  img(s, 'G_water_effect.png', M, 1.35, { w: 6.3 });
  stat(s, 7.05, 1.45, 2.45, '−1.05 → −1.13', 'median pre-monsoon day slope, without → with the water control (202 cities)', C.forest, 20);
  stat(s, 7.05, 2.6, 2.45, '+0.94 → +0.94', 'Jodhpur at night: warm green nights are not caused by water', C.heat, 20);
  bullets(s, [
    'Water share = fraction of each MODIS square covered by OpenStreetMap water polygons.',
    'Known gap: OSM maps the sea as a coastline, not a polygon.',
  ], M, 4.45, W - 2 * M, 0.7, 11.5);
  caption(s, 'Same regression with built-up + elevation, with and without water share. cooling_efficiency.csv');
  s.addNotes([
    'Water-rich squares can be cooler and less green, so water is a possible confounder.',
    'The overall daytime slope changes only slightly and Jodhpur\'s night slope is unchanged.',
    'Likely question, how was water share calculated: OSM water polygons intersected with each MODIS square in the sinusoidal projection.',
  ].join('\n'));
}

// ---------- 16. Robustness ----------
{
  const s = pres.addSlide();
  header(s, 'Results', 'Daytime cooling survives every check; the controls are what matter', 'Presenter: Role 3');
  img(s, 'H_robustness_table.png', M, 1.3, { w: W - 2 * M, h: 2.7 });
  const sw = (W - 2 * M - 0.4) / 3;
  [['70–77%', 'cities cool significantly by day under every variant'],
   ['ρ = 0.56', 'city ranking without controls: the variant that matters most'],
   ['ρ = 0.91', 'without the water control: changes little']].forEach(([b, l], i) => {
    stat(s, M + i * (sw + 0.2), 4.1, sw, b, l, i === 1 ? C.heat : C.forest, 20);
  });
  s.addNotes([
    'Variants: EVI instead of NDVI, 20% built-up cut-off, each control removed, water squares dropped, 6-night cut-off.',
    'The rainfall slope changes sign across variants and is never significant at 5%, so "no clear daytime rainfall pattern" is the safe reading.',
    'The night result depends on the built-up control: without it greener looks cooler at night in 53–75% of cities. Built-up surfaces hold heat at night.',
    'A 6-night cut-off adds 24–32 cities at night, about three-quarters of them wet, and does not change the picture (ρ 0.91–0.95).',
    'Likely question, why do NDVI and EVI disagree: on significance in 14% of cities; not explained by NDVI being tied to built-up (16% vs 13%, p = 0.54). An open point.',
  ].join('\n'));
}

// ---------- 17. Observations ----------
{
  const s = pres.addSlide();
  header(s, 'Observations', 'What we observe so far', 'Each presenter reads their own line');
  const obs = [
    ['H1', 'Greener is cooler by day almost everywhere: 75% of 202 cities pre-monsoon (median −1.13 °C per 0.1 NDVI); 70–74% in other seasons.'],
    ['H2', 'Not by day: no clear trend with rainfall (+0.17 per 10× rain, CI −0.73 to +1.07), and no dry city warms by day (0 of 56 vs Guo\'s 22%).'],
    ['H3', 'Nights centre on zero; wetter cities cool more (−1.16 per 10× rain). 38% of 39 dry vs 18% of 96 wet cities have warmer green nights.'],
    ['H4', 'Same city: daytime cooling weaker after the monsoon in 81% of 202; night cooling stronger in 69% of 127. Soil wetting does not explain it.'],
    ['H5', 'Crowded squares less green in 90–96% of cities; hotter at night in 96–97%, by day 63–87%; less green → hotter (ρ ≈ −0.73).'],
    ['Data', 'Monsoon excluded (Mumbai 85% → 25% usable images); 101 of 303 cities too small; water control barely moves results.'],
  ];
  const cw = (W - 2 * M - 0.25) / 2, ch = 1.12;
  obs.forEach(([k, t], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * (cw + 0.25), y = 1.35 + row * (ch + 0.12);
    card(s, x, y, cw, ch);
    s.addText(k, { x: x + 0.15, y: y + 0.12, w: 0.7, h: 0.35, isTextBox: true, margin: 0, fontFace: HEAD, fontSize: 15, bold: true, color: k === 'Data' ? C.muted : C.forest });
    s.addText(t, { x: x + 0.85, y: y + 0.1, w: cw - 1.0, h: ch - 0.2, isTextBox: true, margin: 0, valign: 'top', fontFace: BODY, fontSize: 10.5, color: C.ink, fit: 'shrink' });
  });
  caption(s, 'All results are associations, not causes. Sources: docs/observations.md and data/results/.');
  s.addNotes('H1 Role 3 · H2 Role 2 · H3 Roles 2/3 (humid cities have less night data; holds with a 6-night cut-off, 54% vs 18%) · H4 Role 3 · H5 Role 4 · Data Roles 1/5. One breath per line.');
}

// ---------- 18. Limitations + next ----------
{
  const s = pres.addSlide();
  s.background = { color: C.forestDeep };
  s.addText('NEXT', { x: M, y: 0.28, w: 2, h: 0.26, isTextBox: true, margin: 0, fontFace: BODY, fontSize: 9, bold: true, color: C.leafMid, charSpacing: 2 });
  s.addText('Presenter: Role 4', { x: W - M - 3, y: 0.28, w: 3, h: 0.26, isTextBox: true, margin: 0, align: 'right', fontFace: BODY, fontSize: 9, color: C.leafMid });
  s.addText('About 50–60% done: the core results are in', { x: M, y: 0.55, w: 9, h: 0.6, isTextBox: true, margin: 0, fontFace: HEAD, fontSize: 24, bold: true, color: C.white });
  const cw = (W - 2 * M - 0.3) / 2;
  const col = (x, head, items) => {
    s.addText(head, { x, y: 1.45, w: cw, h: 0.35, isTextBox: true, margin: 0, fontFace: HEAD, fontSize: 15, bold: true, color: 'F2B66D' });
    s.addText(items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: i < items.length - 1, paraSpaceAfter: 5 } })), {
      x, y: 1.9, w: cw, h: 3.2, isTextBox: true, margin: 0, valign: 'top', fontFace: BODY, fontSize: 12.5, color: C.white, fit: 'shrink',
    });
  };
  col(M, 'Left for the final', [
    'H6: turn surface cooling into felt heat (Heat Index), using the surface-to-air ratios from Venter 2021 and Du 2024',
    'Who receives the cooling: a Lorenz curve',
    'Building height (GHSL 2018) as an urban-form control',
    'Optional: Hyderabad case study with Landsat at 30 m',
  ]);
  col(M + cw + 0.3, 'Limitations', [
    'Surface temperature, not the heat people feel',
    'ERA5 gives city-level climate only (~9 km)',
    'Associations, not causes',
    'No monsoon season; humid cities thinner at night',
    'OSM misses the sea as water',
    'NDVI cannot separate trees from grass or crops',
  ]);
  s.addNotes('Done: pipeline, 303 cities × 3 seasons sampled, cooling slopes, climate, exposure, main results. Close by restating the answer: greenery cools by day almost everywhere; the conditions that matter show up at night and between seasons.');
}

pres.writeFile({ fileName: OUT }).then((f) => console.log('wrote', f));
