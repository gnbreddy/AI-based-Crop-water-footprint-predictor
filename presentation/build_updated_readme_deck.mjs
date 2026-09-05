import pptxgen from 'pptxgenjs';

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'AquaCrop AI';
pptx.subject = 'Project presentation based on the current README';
pptx.title = 'AquaCrop AI — Project Overview';
pptx.company = 'AquaCrop AI';
pptx.lang = 'en-IN';
pptx.theme = {
  headFontFace: 'Aptos Display', bodyFontFace: 'Aptos', lang: 'en-IN'
};
pptx.defineLayout({ name: 'CUSTOM_WIDE', width: 13.333, height: 7.5 });
pptx.layout = 'CUSTOM_WIDE';
pptx.defineSlideMaster({
  title: 'AQUA', background: { color: '081B2D' },
  objects: [
    { rect: { x: 0, y: 0, w: 13.333, h: 0.13, fill: { color: '22C55E' }, line: { color: '22C55E' } } },
    { text: { text: 'AQUACROP AI  |  UNIVERSAL CROP WATER FOOTPRINT PREDICTOR', options: { x: 0.55, y: 7.12, w: 9.5, h: 0.18, fontFace: 'Aptos', fontSize: 7.5, color: '93AFC4', margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.08, color: '55D6BE', fontFace: 'Aptos', fontSize: 8 }
});

const C = { navy: '081B2D', panel: '102C44', panel2: '133854', green: '22C55E', teal: '55D6BE', cyan: '54C5EB', white: 'F3F8FC', muted: 'B7CBD9', amber: 'F6B44C', red: 'F07B70', line: '28516C' };
const I = (n) => n;
function addText(s, text, x, y, w, h, o = {}) {
  s.addText(text, { x, y, w, h, margin: o.margin ?? 0.04, fontFace: o.fontFace ?? 'Aptos', fontSize: o.fontSize ?? 15, color: o.color ?? C.white, bold: o.bold ?? false, breakLine: false, fit: 'shrink', valign: o.valign ?? 'mid', align: o.align ?? 'left', bullet: o.bullet, paraSpaceAfterPt: o.paraSpaceAfterPt, ...o });
}
function rect(s, x, y, w, h, fill = C.panel, line = C.line, radius = 0.08) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: radius, fill: { color: fill }, line: { color: line, transparency: 15, width: 0.8 } });
}
function title(s, section, heading, sub) {
  addText(s, section.toUpperCase(), 0.6, 0.4, 5.4, 0.24, { fontSize: 9, color: C.teal, bold: true, charSpacing: 1.3 });
  addText(s, heading, 0.6, 0.68, 12.0, 0.48, { fontSize: 25, bold: true });
  if (sub) addText(s, sub, 0.6, 1.22, 12.0, 0.28, { fontSize: 10.5, color: C.muted });
}
function chip(s, text, x, y, w, color = C.teal) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.37, rectRadius: 0.08, fill: { color, transparency: 82 }, line: { color, transparency: 45, width: 0.6 } });
  addText(s, text, x + 0.08, y + 0.05, w - 0.16, 0.22, { fontSize: 8.5, bold: true, color });
}
function bulletList(s, items, x, y, w, h, size = 14) {
  const runs = [];
  items.forEach((t, idx) => {
    runs.push({ text: t, options: { bullet: { indent: 14 }, hanging: 3, breakLine: idx < items.length - 1 } });
  });
  s.addText(runs, { x, y, w, h, fontFace: 'Aptos', fontSize: size, color: C.white, breakLine: false, margin: 0.1, paraSpaceAfterPt: 10, breakLine: false, fit: 'shrink', valign: 'mid' });
}
function metric(s, x, y, w, value, label, color = C.teal) {
  rect(s, x, y, w, 1.03, C.panel2);
  addText(s, value, x + 0.18, y + 0.15, w - 0.36, 0.35, { fontSize: 22, bold: true, color });
  addText(s, label, x + 0.18, y + 0.6, w - 0.36, 0.22, { fontSize: 9.3, color: C.muted });
}
function image(s, path, x, y, w, h) { s.addImage({ path, x, y, w, h, sizing: { type: 'contain', x, y, w, h } }); }
function note(s, text) { s.addNotes(text); }

// 1. Introduction
{ const s = pptx.addSlide('AQUA');
  s.addShape(pptx.ShapeType.arc, { x: 8.4, y: 0.4, w: 4.7, h: 4.7, adjustPoint: 0.4, line: { color: C.teal, transparency: 48, width: 3 }, adjustPoint: 0.25 });
  addText(s, '01 · INTRODUCTION', 0.65, 0.58, 3.4, 0.22, { fontSize: 9, color: C.teal, bold: true, charSpacing: 1.2 });
  addText(s, 'AquaCrop AI', 0.65, 1.0, 6.8, 0.65, { fontSize: 34, bold: true });
  addText(s, 'Universal AI-Based Crop Water Footprint Predictor', 0.65, 1.72, 7.0, 0.35, { fontSize: 17, color: C.teal, bold: true });
  addText(s, 'A project overview of a full-stack agro-hydrological platform that turns Earth observation data into crop-water footprint estimates.', 0.65, 2.3, 6.45, 0.72, { fontSize: 16, color: C.muted, valign: 'top' });
  metric(s, 0.65, 3.45, 1.9, '3', 'simple user inputs'); metric(s, 2.78, 3.45, 1.9, '26 yrs', 'earth-observation archive'); metric(s, 4.91, 3.45, 1.9, '4 tiers', 'decoupled architecture');
  chip(s, 'Earth observation', 8.2, 2.35, 1.55); chip(s, 'Water stewardship', 9.92, 2.35, 1.75); chip(s, 'Full stack', 11.84, 2.35, 1.05);
  addText(s, 'From location selection to footprint reporting — designed for field-relevant decisions.', 8.2, 3.05, 4.35, 0.55, { fontSize: 14, color: C.white, bold: true });
  note(s, 'Introduce the platform as a practical bridge between remotely sensed climate information and transparent crop-water reporting.'); }

// 2 Motivation
{ const s = pptx.addSlide('AQUA'); title(s, '02 · Motivation', 'Why crop-water visibility matters', 'Agricultural water decisions need timely, understandable, location-aware information.');
  const cards = [ ['Water pressure', 'Irrigation and groundwater extraction can place severe pressure on regional water resources.', C.cyan], ['Climate variability', 'Weather, vegetation condition and root-zone moisture vary across seasons and locations.', C.amber], ['Information gap', 'Farm users rarely have access to meteorological instruments or complex model inputs.', C.teal] ];
  cards.forEach((c, i) => { const x = 0.65 + i * 4.15; rect(s, x, 2.0, 3.7, 3.35); s.addShape(pptx.ShapeType.ellipse, { x: x + 0.25, y: 2.28, w: 0.46, h: 0.46, fill: { color: c[2] }, line: { color: c[2] } }); addText(s, c[0], x + 0.25, 2.95, 3.15, 0.34, { fontSize: 18, bold: true }); addText(s, c[1], x + 0.25, 3.55, 3.15, 1.12, { fontSize: 13, color: C.muted, valign: 'top' }); });
  addText(s, 'Project response: combine satellite and reanalysis sources with an accessible web workflow.', 0.75, 6.0, 11.7, 0.34, { fontSize: 15, bold: true, color: C.teal, align: 'center' }); }

// 3 Problem
{ const s = pptx.addSlide('AQUA'); title(s, '03 · Problem statement', 'Conventional workflows are difficult to use at field scale', 'The challenge is both scientific and operational: accurate inputs are not readily available to every user.');
  const left = ['Many tools require a long list of atmospheric, crop and soil parameters.', 'Static assumptions may not reflect observed vegetation and local soil-water conditions.', 'Standalone calculations are disconnected from maps, databases, APIs and operational dashboards.'];
  rect(s, 0.65, 1.95, 5.65, 4.2, C.panel); addText(s, 'Current friction', 0.95, 2.25, 4.8, 0.35, { fontSize: 19, bold: true, color: C.red }); bulletList(s, left, 0.95, 2.85, 4.85, 2.6, 13.5);
  rect(s, 7.05, 1.95, 5.65, 4.2, C.panel2); addText(s, 'Project direction', 7.35, 2.25, 4.8, 0.35, { fontSize: 19, bold: true, color: C.teal }); bulletList(s, ['Automate data retrieval and physical normalization.', 'Keep the user journey focused on location, crop and forecast horizon.', 'Deliver results through reusable services, dashboards and auditable records.'], 7.35, 2.85, 4.85, 2.6, 13.5);
  s.addShape(pptx.ShapeType.chevron, { x: 6.3, y: 3.6, w: 0.7, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } }); }

// 4 Literature
{ const s = pptx.addSlide('AQUA'); title(s, '04 · Literature survey', 'Scientific foundations behind the platform', 'The system is grounded in established hydrology, crop science and water-footprint practice.');
  const rows = [ ['FAO-56', 'Reference evapotranspiration and crop-coefficient methods'], ['FAO-33', 'Yield response to water and crop stress relationships'], ['Water Footprint Network', 'Green and blue water-footprint accounting'], ['Earth observation research', 'Satellite vegetation, evapotranspiration and precipitation products'] ];
  rows.forEach((r, i) => { const y = 1.85 + i * 1.05; rect(s, 0.8, y, 11.75, 0.78, i % 2 ? C.panel2 : C.panel); addText(s, r[0], 1.08, y + 0.18, 2.25, 0.25, { fontSize: 15, bold: true, color: C.teal }); addText(s, r[1], 3.55, y + 0.18, 8.3, 0.3, { fontSize: 14, color: C.white }); });
  addText(s, 'AquaCrop AI integrates these foundations into a deployable digital system.', 0.9, 6.2, 11.3, 0.34, { fontSize: 16, bold: true, color: C.amber, align: 'center' }); }

// 5 gaps
{ const s = pptx.addSlide('AQUA'); title(s, '05 · Gaps identified', 'From research methods to a usable platform', 'The project targets the gap between detailed scientific models and real operational workflows.');
  const gaps = [['Input burden', 'Field users should not need to enter complex thermodynamic measurements.'], ['Data fragmentation', 'Climate, vegetation and precipitation products are commonly separated.'], ['Low interoperability', 'A model alone does not provide APIs, persistence, maps or deployment.'], ['Limited traceability', 'Operational systems need stored records and repeatable requests.']];
  gaps.forEach((g, i) => { const x = i % 2 ? 6.8 : 0.75, y = i < 2 ? 1.95 : 4.1; rect(s, x, y, 5.75, 1.55); addText(s, `0${i+1}`, x + 0.25, y + 0.25, 0.55, 0.35, { fontSize: 18, bold: true, color: C.teal }); addText(s, g[0], x + 1.0, y + 0.22, 4.2, 0.3, { fontSize: 16, bold: true }); addText(s, g[1], x + 1.0, y + 0.68, 4.25, 0.48, { fontSize: 11.5, color: C.muted, valign: 'top' }); }); }

// 6 objectives
{ const s = pptx.addSlide('AQUA'); title(s, '06 · Objectives', 'What the project sets out to deliver', 'A science-informed product that is simple to use, operationally robust and ready to extend.');
  const objectives = ['Consolidate multi-year Earth observation data for crop-water analysis.', 'Build location- and crop-aware water-footprint calculations.', 'Minimise the user input burden through a guided three-input experience.', 'Provide web, API and database layers for real-world use.', 'Support scalable ingestion, auditability and future decision-support features.'];
  objectives.forEach((o, i) => { const y = 1.75 + i * 0.88; s.addShape(pptx.ShapeType.ellipse, { x: 0.85, y: y + 0.05, w: 0.38, h: 0.38, fill: { color: C.green }, line: { color: C.green } }); addText(s, String(i + 1), 0.96, y + 0.115, 0.15, 0.13, { fontSize: 7.5, color: C.navy, bold: true, align: 'center' }); addText(s, o, 1.5, y, 10.65, 0.42, { fontSize: 15, color: C.white }); }); }

// 7 architecture
{ const s = pptx.addSlide('AQUA'); title(s, '07 · Architecture / methodology', 'Four tiers, one connected workflow', 'A decoupled architecture separates data preparation, physical processing, footprint calculation and delivery.');
  const stages = [['User request', 'Location · crop · horizon'], ['Data & context', 'Archive, crop and soil profiles'], ['Physical processing', 'Climate and crop-water normalization'], ['Footprint service', 'Green/blue CWF and results'], ['Delivery', 'API · dashboard · database']];
  stages.forEach((a, i) => { const x = 0.55 + i * 2.57; rect(s, x, 2.35, 2.15, 1.75, i === 4 ? '16465A' : C.panel); addText(s, `TIER ${i+1}`, x + 0.18, 2.63, 1.7, 0.2, { fontSize: 8.5, bold: true, color: C.teal }); addText(s, a[0], x + 0.18, 3.02, 1.75, 0.36, { fontSize: 14, bold: true }); addText(s, a[1], x + 0.18, 3.5, 1.72, 0.27, { fontSize: 9.5, color: C.muted, valign: 'top' }); if (i < 4) s.addShape(pptx.ShapeType.chevron, { x: x + 2.2, y: 2.93, w: 0.29, h: 0.55, fill: { color: C.teal }, line: { color: C.teal } }); });
  addText(s, 'Decoupling improves maintainability: each tier can be tested, evolved and deployed independently.', 1.1, 5.25, 11.0, 0.34, { fontSize: 14, color: C.amber, bold: true, align: 'center' }); }

// 8 Dataset
{ const s = pptx.addSlide('AQUA'); title(s, '08 · Dataset & data sources', 'A multi-sensor archive for agricultural context', 'The data foundation combines climate reanalysis, satellite vegetation and precipitation products.');
  const sources = [['ECMWF ERA5-Land', 'Atmosphere, radiation, wind and soil-moisture layers', 'Hourly · ~9 km'], ['NASA MODIS', 'Evapotranspiration, NDVI and EVI vegetation measures', '8–16 day · 250 m–1 km'], ['CHIRPS', 'Satellite–station blended precipitation', 'Daily · ~5.5 km']];
  sources.forEach((a, i) => { const x = 0.7 + i * 4.18; rect(s, x, 2.05, 3.65, 2.45, i === 1 ? C.panel2 : C.panel); addText(s, a[0], x + 0.25, 2.38, 3.0, 0.3, { fontSize: 16, bold: true, color: C.teal }); addText(s, a[1], x + 0.25, 3.02, 3.0, 0.65, { fontSize: 11.5, color: C.white, valign: 'top' }); chip(s, a[2], x + 0.25, 3.93, 2.55, C.amber); });
  metric(s, 1.25, 5.2, 3.0, '2000–2025', 'archive coverage'); metric(s, 5.15, 5.2, 3.0, '300,232', 'observational records'); metric(s, 9.05, 5.2, 3.0, '5 nodes', 'Kolhapur monitoring locations'); }

// 9 inputs target model
{ const s = pptx.addSlide('AQUA'); title(s, '09 · Input features, target & model', 'User simplicity backed by agro-hydrological context', 'The platform transforms readily available location and crop context into water-footprint outputs.');
  rect(s, 0.7, 1.9, 3.15, 3.6); addText(s, 'User inputs', 1.0, 2.25, 2.35, 0.35, { fontSize: 19, bold: true, color: C.teal }); ['Location', 'Crop type', 'Forecast horizon'].forEach((t,i) => { rect(s, 1.0, 2.95 + i * 0.65, 2.45, 0.43, C.panel2); addText(s, t, 1.18, 3.05 + i * 0.65, 2.0, 0.18, { fontSize: 12, bold: true }); });
  s.addShape(pptx.ShapeType.chevron, { x: 4.15, y: 3.23, w: 0.78, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
  rect(s, 5.25, 1.9, 3.15, 3.6); addText(s, 'System context', 5.55, 2.25, 2.35, 0.35, { fontSize: 19, bold: true, color: C.cyan }); addText(s, 'Satellite and reanalysis variables\nCrop profiles and soil properties\nPhysical crop-water calculations', 5.55, 2.95, 2.45, 1.35, { fontSize: 13, color: C.muted, breakLine: false, valign: 'top' });
  s.addShape(pptx.ShapeType.chevron, { x: 8.7, y: 3.23, w: 0.78, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
  rect(s, 9.8, 1.9, 2.8, 3.6, C.panel2); addText(s, 'Outputs', 10.1, 2.25, 2.1, 0.35, { fontSize: 19, bold: true, color: C.green }); addText(s, 'Crop water footprint\nGreen-water contribution\nBlue-water requirement\nYield-aware context', 10.1, 2.95, 2.05, 1.35, { fontSize: 13, color: C.muted, valign: 'top' }); }

// 10 preprocessing
{ const s = pptx.addSlide('AQUA'); title(s, '10 · Data preprocessing & feature engineering', 'From raw observations to physically meaningful inputs', 'Data is harmonised, checked and transformed before crop-water calculations are applied.');
  const steps = [['1', 'Harmonise', 'Align timestamps, units and source-specific formats.'], ['2', 'Validate', 'Apply quality checks and physical bounds.'], ['3', 'Derive', 'Calculate climate and soil-water descriptors.'], ['4', 'Connect', 'Attach crop, soil and location profiles.']];
  steps.forEach((a,i) => { const x = 0.65 + i * 3.15; s.addShape(pptx.ShapeType.ellipse, { x: x + 0.95, y: 2.0, w: 1.1, h: 1.1, fill: { color: i % 2 ? C.panel2 : C.panel }, line: { color: C.teal, width: 1.2 } }); addText(s, a[0], x + 1.28, 2.32, 0.45, 0.28, { fontSize: 17, color: C.teal, bold: true, align: 'center' }); addText(s, a[1], x + 0.4, 3.35, 2.25, 0.32, { fontSize: 16, bold: true, align: 'center' }); addText(s, a[2], x + 0.25, 3.9, 2.55, 0.65, { fontSize: 11, color: C.muted, align: 'center', valign: 'top' }); if (i<3) s.addShape(pptx.ShapeType.line, { x: x + 2.55, y: 2.55, w: 0.85, h: 0, line: { color: C.teal, width: 1.5, beginArrowType: 'none', endArrowType: 'triangle' } }); });
  addText(s, 'Result: a consistent agronomic data layer suitable for transparent water-footprint reporting.', 0.85, 5.45, 11.6, 0.32, { fontSize: 15, color: C.amber, bold: true, align: 'center' }); }

// 11 CWF calculation
{ const s = pptx.addSlide('AQUA'); title(s, '11 · Model training & CWF calculation', 'Water-footprint accounting that keeps sources visible', 'The calculation separates rain-fed contribution from irrigation-related demand and relates water use to crop output.');
  rect(s, 0.75, 2.0, 3.35, 2.6); addText(s, 'Effective rainfall', 1.05, 2.35, 2.6, 0.3, { fontSize: 17, bold: true, color: C.green }); addText(s, 'Water available from precipitation and soil storage contributes to the green component.', 1.05, 3.0, 2.5, 0.76, { fontSize: 12, color: C.muted, valign: 'top' });
  rect(s, 5.0, 2.0, 3.35, 2.6, C.panel2); addText(s, 'Crop water use', 5.3, 2.35, 2.6, 0.3, { fontSize: 17, bold: true, color: C.cyan }); addText(s, 'Crop and climate context inform the consumptive water-use estimate.', 5.3, 3.0, 2.5, 0.76, { fontSize: 12, color: C.muted, valign: 'top' });
  rect(s, 9.25, 2.0, 3.35, 2.6); addText(s, 'Footprint output', 9.55, 2.35, 2.6, 0.3, { fontSize: 17, bold: true, color: C.teal }); addText(s, 'Green and blue components are reported per yield unit and per land area.', 9.55, 3.0, 2.5, 0.76, { fontSize: 12, color: C.muted, valign: 'top' });
  s.addShape(pptx.ShapeType.chevron, { x: 4.25, y: 2.92, w: 0.5, h: 0.65, fill: { color: C.teal }, line: { color: C.teal } }); s.addShape(pptx.ShapeType.chevron, { x: 8.5, y: 2.92, w: 0.5, h: 0.65, fill: { color: C.teal }, line: { color: C.teal } });
  addText(s, 'Outputs are designed to make the origin and scale of agricultural water use understandable.', 0.85, 5.45, 11.6, 0.32, { fontSize: 15, color: C.amber, bold: true, align: 'center' }); }

// 12 implementation
{ const s = pptx.addSlide('AQUA'); title(s, '12 · System implementation', 'Production-oriented full-stack implementation', 'The repository contains interfaces, APIs, persistence and asynchronous ingestion components.');
  const units = [['Web dashboard', 'Flask dashboard, map-based interactions and a React implementation'], ['REST services', 'FastAPI endpoints for prediction, profiles, records and system status'], ['Data layer', 'SQLite for local use and PostgreSQL 16 for containerised deployment'], ['Streaming worker', 'Asynchronous queue, batch processing and graceful shutdown']];
  units.forEach((a,i) => { const x = i % 2 ? 6.78 : 0.7, y = i < 2 ? 1.8 : 4.0; rect(s, x, y, 5.85, 1.52, i === 3 ? C.panel2 : C.panel); addText(s, a[0], x + 0.27, y + 0.25, 2.3, 0.3, { fontSize: 16, bold: true, color: C.teal }); addText(s, a[1], x + 0.27, y + 0.72, 5.05, 0.48, { fontSize: 11.5, color: C.muted, valign: 'top' }); }); }

// 13 Limitations
{ const s = pptx.addSlide('AQUA'); title(s, '13 · Limitations & future scope', 'What remains to be extended', 'The current platform establishes a strong base while highlighting opportunities for broader coverage and operational integration.');
  const left = ['Current geography is centred on the Kolhapur monitoring region.', 'Data resolution and update cadence depend on upstream observation products.', 'On-farm recommendations need local validation and stakeholder feedback.'];
  const right = ['Smart irrigation scheduling with rain-delay logic.', 'Water-to-rupees and energy-use calculator.', 'Irrigation-method and crop-switching simulation.', 'Reservoir and canal-release integration.'];
  rect(s, 0.7, 1.85, 5.8, 4.15); addText(s, 'Current limitations', 1.0, 2.2, 4.5, 0.32, { fontSize: 18, bold: true, color: C.amber }); bulletList(s, left, 0.95, 2.85, 4.95, 2.2, 13);
  rect(s, 6.85, 1.85, 5.8, 4.15, C.panel2); addText(s, 'Roadmap', 7.15, 2.2, 4.5, 0.32, { fontSize: 18, bold: true, color: C.teal }); bulletList(s, right, 7.1, 2.85, 4.95, 2.2, 13); }

// 14 results
{ const s = pptx.addSlide('AQUA'); title(s, '14 · Results of individual objectives', 'Delivered capabilities across the project', 'The repository demonstrates an end-to-end foundation rather than a standalone calculation script.');
  const data = [['Data foundation', '26 annual data files and a compiled multi-year dataset', C.cyan], ['User experience', 'Three-input flow with selectable locations, crops and horizons', C.green], ['System services', 'Dashboard, REST gateway, records and profile endpoints', C.teal], ['Operational readiness', 'Container configuration, worker process and automated tests', C.amber]];
  data.forEach((a,i) => { const x = i % 2 ? 6.8 : 0.72, y = i < 2 ? 1.85 : 4.05; rect(s, x, y, 5.8, 1.55); s.addShape(pptx.ShapeType.ellipse, { x: x + 0.28, y: y + 0.35, w: 0.58, h: 0.58, fill: { color: a[2] }, line: { color: a[2] } }); addText(s, '✓', x + 0.41, y + 0.43, 0.28, 0.15, { fontSize: 11, color: C.navy, bold: true, align: 'center' }); addText(s, a[0], x + 1.1, y + 0.26, 4.2, 0.3, { fontSize: 16, bold: true }); addText(s, a[1], x + 1.1, y + 0.74, 4.2, 0.4, { fontSize: 11.5, color: C.muted, valign: 'top' }); }); }

// 15 comparative graph
{ const s = pptx.addSlide('AQUA'); title(s, '15 · Comparative analysis', 'Capability comparison: conventional workflow vs. AquaCrop AI', 'This graph compares workflow coverage, not a predictive-performance benchmark.');
  const labels = ['Data integration', 'Input simplicity', 'System delivery', 'Traceability', 'Deployment readiness']; const conv = [2, 2, 1, 1, 1]; const aqua = [5, 5, 5, 5, 5];
  labels.forEach((lab, i) => { const y = 1.9 + i * 0.78; addText(s, lab, 0.75, y + 0.06, 2.35, 0.2, { fontSize: 11, color: C.white, align: 'right' }); for(let j=0;j<5;j++){ s.addShape(pptx.ShapeType.rect, { x: 3.35 + j * 0.56, y: y, w: 0.42, h: 0.25, fill: { color: j < conv[i] ? C.amber : C.line, transparency: j < conv[i] ? 0 : 25 }, line: { color: j < conv[i] ? C.amber : C.line } }); s.addShape(pptx.ShapeType.rect, { x: 7.0 + j * 0.56, y: y, w: 0.42, h: 0.25, fill: { color: j < aqua[i] ? C.teal : C.line, transparency: j < aqua[i] ? 0 : 25 }, line: { color: j < aqua[i] ? C.teal : C.line } }); } });
  chip(s, 'Conventional workflow', 3.3, 1.35, 2.25, C.amber); chip(s, 'AquaCrop AI', 7.0, 1.35, 1.7, C.teal);
  rect(s, 10.15, 1.8, 2.1, 3.95, C.panel2); addText(s, 'Interpretation', 10.42, 2.15, 1.55, 0.3, { fontSize: 15, bold: true, color: C.teal }); addText(s, 'AquaCrop AI adds integrated data, user-facing delivery, persistent records and deployable services around crop-water calculations.', 10.42, 2.85, 1.55, 1.85, { fontSize: 11, color: C.muted, valign: 'top' });
  addText(s, 'Scale: 1 = limited coverage · 5 = integrated capability', 0.85, 6.35, 8.4, 0.22, { fontSize: 9, color: C.muted }); }

// 16 Conclusion
{ const s = pptx.addSlide('AQUA');
  addText(s, 'Conclusion', 0.65, 1.0, 5.0, 0.55, { fontSize: 32, bold: true });
  addText(s, 'AquaCrop AI brings together Earth observation, crop-water science and production software into a practical foundation for sustainable agricultural water management.', 0.65, 1.85, 7.0, 0.95, { fontSize: 18, color: C.muted, valign: 'top' });
  const keys = [['Accessible', 'Three guided inputs for the user'], ['Connected', 'Data, services, dashboards and records'], ['Extensible', 'A clear base for irrigation decision support']];
  keys.forEach((a,i) => { const x = 0.7 + i * 4.1; rect(s, x, 3.55, 3.55, 1.65, i === 1 ? C.panel2 : C.panel); addText(s, a[0], x + 0.25, 3.9, 3.0, 0.3, { fontSize: 18, bold: true, color: C.teal, align: 'center' }); addText(s, a[1], x + 0.25, 4.45, 3.0, 0.32, { fontSize: 11.5, color: C.white, align: 'center' }); });
  addText(s, 'Thank you', 0.65, 6.05, 12.0, 0.45, { fontSize: 23, bold: true, color: C.green, align: 'center' }); }

await pptx.writeFile({ fileName: 'presentation/AquaCrop_AI_Updated_Project_Overview.pptx' });
