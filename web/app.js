/**
 * AquaCrop AI — Interactive 1990–2050 Crop Water Footprint Web Application
 */

// --- Historical Validated Dataset (1990–2025) ---
const HISTORICAL_DATA = {
  years: [
    1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999,
    2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
    2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
    2020, 2021, 2022, 2023, 2024, 2025
  ],
  total_cwf: [
    221.64, 222.57, 222.67, 221.70, 221.92, 222.14, 222.20, 221.61, 221.92, 222.05,
    221.50, 222.38, 221.80, 222.02, 221.95, 221.43, 222.22, 221.66, 222.20, 221.75,
    221.93, 221.87, 221.74, 222.03, 221.39, 221.84, 221.80, 221.79, 222.01, 221.89,
    221.58, 221.73, 221.62, 222.20, 221.74, 222.08
  ],
  green_cwf: [
    38.03, 45.93, 40.76, 39.72, 39.94, 42.10, 42.67, 38.50, 42.30, 41.03,
    38.60, 39.10, 37.80, 38.90, 38.50, 38.20, 39.40, 38.10, 39.20, 38.40,
    38.80, 38.70, 38.50, 38.90, 38.30, 38.63, 38.50, 38.40, 38.80, 38.60,
    38.55, 38.65, 38.58, 38.92, 38.61, 38.70
  ],
  blue_cwf: [
    183.61, 176.64, 181.91, 181.98, 181.98, 180.04, 179.53, 183.11, 179.62, 181.02,
    182.90, 183.28, 184.00, 183.12, 183.45, 183.23, 182.82, 183.56, 183.00, 183.35,
    183.13, 183.17, 183.24, 183.13, 183.09, 183.21, 183.30, 183.39, 183.21, 183.29,
    183.03, 183.08, 183.04, 183.28, 183.13, 183.38
  ],
  stats: {
    1990: { r2: 98.12, rmse: 0.2275, mae: 0.1793, corr: 0.9907, act_et: 4.554, pred_et: 4.556 },
    1995: { r2: 98.39, rmse: 0.2088, mae: 0.1663, corr: 0.9920, act_et: 4.565, pred_et: 4.580 },
    2000: { r2: 98.69, rmse: 0.1865, mae: 0.1474, corr: 0.9934, act_et: 4.564, pred_et: 4.557 },
    2005: { r2: 98.67, rmse: 0.1879, mae: 0.1486, corr: 0.9933, act_et: 4.556, pred_et: 4.558 },
    2010: { r2: 98.70, rmse: 0.1865, mae: 0.1497, corr: 0.9935, act_et: 4.567, pred_et: 4.569 },
    2012: { r2: 98.73, rmse: 0.1834, mae: 0.1467, corr: 0.9936, act_et: 4.563, pred_et: 4.565 },
    2015: { r2: 98.70, rmse: 0.1863, mae: 0.1497, corr: 0.9935, act_et: 4.561, pred_et: 4.566 },
    2020: { r2: 98.62, rmse: 0.1928, mae: 0.1541, corr: 0.9931, act_et: 4.562, pred_et: 4.560 },
    2025: { r2: 98.56, rmse: 0.1933, mae: 0.1524, corr: 0.9928, act_et: 4.559, pred_et: 4.560 }
  }
};

// Default Simulation Parameters
let simParams = {
  tempDelta: 2.0,      // +2.0 C by target horizon
  solarDelta: 5.0,     // +5% Solar radiation
  precipDelta: -10.0,  // -10% Precipitation
  alpha: 0.90,         // Effective rainfall retention
  yield: 150.0,        // Crop yield ton/ha
  kc: 0.50,            // Crop coefficient
  cropName: 'sugarcane',
  region: 'kolhapur',
  targetHorizonYear: 2050,
  durationMode: 'annual',
  displayMode: 'total' // 'total' or 'partition'
};

// Regional Agro-Ecological Profiles
const REGIONAL_PROFILES = {
  kolhapur: {
    crop: 'sugarcane',
    name: 'Kolhapur Sugarcane',
    regionName: 'Kolhapur (India)',
    climate: 'Tropical Wet/Dry Monsoon',
    soil: 'Clay Loam (Heavy Black Soil)',
    kc: 0.50,
    yield: 150.0,
    minYield: 60,
    maxYield: 250,
    seasonDays: 360,
    baseHistoricalTWF: 222.1,
    desc: 'Kolhapur (India) • Tropical Monsoon • Clay Loam • Sugarcane Season: 360 days'
  },
  nile_delta: {
    crop: 'cotton',
    name: 'Nile Delta Cotton',
    regionName: 'Nile Delta (Egypt)',
    climate: 'Hyper-Arid / Desert Heat',
    soil: 'Silt Loam / Alluvial Clay',
    kc: 0.85,
    yield: 3.5,
    minYield: 1.5,
    maxYield: 7.0,
    seasonDays: 180,
    baseHistoricalTWF: 1950.0,
    desc: 'Nile Delta (Egypt) • Hyper-Arid Mediterranean • Alluvial Silt • Cotton Season: 180 days'
  },
  kansas: {
    crop: 'wheat',
    name: 'Kansas Wheat',
    regionName: 'Kansas (USA High Plains)',
    climate: 'Continental Semi-Arid',
    soil: 'Silt Loam (Mollisol)',
    kc: 1.15,
    yield: 5.0,
    minYield: 2.0,
    maxYield: 10.0,
    seasonDays: 140,
    baseHistoricalTWF: 1180.0,
    desc: 'Kansas (USA) • Continental Semi-Arid • Deep Silt Loam • Winter Wheat Season: 140 days'
  },
  mekong_delta: {
    crop: 'rice',
    name: 'Mekong Monsoon Rice',
    regionName: 'Mekong Delta (Vietnam)',
    climate: 'Tropical Monsoon Deluge',
    soil: 'Fluvisol Heavy Clay',
    kc: 1.20,
    yield: 4.5,
    minYield: 2.0,
    maxYield: 9.0,
    seasonDays: 120,
    baseHistoricalTWF: 1420.0,
    desc: 'Mekong Delta (Vietnam) • Tropical Monsoon • River Basin Clay • Paddy Rice Season: 120 days'
  }
};

let mainChart = null;
let pieChart = null;

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initUIControls();
  populateYearSelector();
  initMainChart();
  initPieChart(2025);
  updateCalculations();
});

// Setup UI event listeners
function initUIControls() {
  // Sliders
  const sliders = [
    { id: 'slider-temp', param: 'tempDelta', disp: 'val-temp', fmt: v => `+${parseFloat(v).toFixed(1)} °C` },
    { id: 'slider-solar', param: 'solarDelta', disp: 'val-solar', fmt: v => `${v > 0 ? '+' : ''}${v} %` },
    { id: 'slider-precip', param: 'precipDelta', disp: 'val-precip', fmt: v => `${v > 0 ? '+' : ''}${v} %` },
    { id: 'slider-alpha', param: 'alpha', disp: 'val-alpha', fmt: v => parseFloat(v).toFixed(2) },
    { id: 'slider-yield', param: 'yield', disp: 'val-yield', fmt: v => `${v} ton/ha` }
  ];

  sliders.forEach(s => {
    const el = document.getElementById(s.id);
    if (!el) return;
    el.addEventListener('input', (e) => {
      simParams[s.param] = parseFloat(e.target.value);
      document.getElementById(s.disp).textContent = s.fmt(e.target.value);
      updateCalculations();
    });
  });

  // Time Horizon Buttons
  document.querySelectorAll('.btn-horizon').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-horizon').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const yr = parseInt(btn.dataset.year);
      simParams.targetHorizonYear = yr;
      const slider = document.getElementById('slider-horizon');
      if (slider) slider.value = yr;
      const valDisp = document.getElementById('val-horizon');
      if (valDisp) valDisp.textContent = `Year ${yr}`;
      updateHorizonLabels(yr);
      updateCalculations();
    });
  });

  // Target Horizon Custom Slider
  const horizonSlider = document.getElementById('slider-horizon');
  if (horizonSlider) {
    horizonSlider.addEventListener('input', (e) => {
      const yr = parseInt(e.target.value);
      simParams.targetHorizonYear = yr;
      document.getElementById('val-horizon').textContent = `Year ${yr}`;
      document.querySelectorAll('.btn-horizon').forEach(b => {
        if (parseInt(b.dataset.year) === yr) b.classList.add('active');
        else b.classList.remove('active');
      });
      updateHorizonLabels(yr);
      updateCalculations();
    });
  }

  // Duration Scope Toggle (Annual vs Growing Season)
  const btnAnn = document.getElementById('btn-duration-annual');
  const btnSea = document.getElementById('btn-duration-seasonal');
  if (btnAnn && btnSea) {
    btnAnn.addEventListener('click', () => {
      btnAnn.classList.add('active');
      btnSea.classList.remove('active');
      simParams.durationMode = 'annual';
      updateCalculations();
    });
    btnSea.addEventListener('click', () => {
      btnSea.classList.add('active');
      btnAnn.classList.remove('active');
      simParams.durationMode = 'growing_season';
      updateCalculations();
    });
  }

  // Regional Preset buttons
  document.querySelectorAll('.btn-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-preset').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const regKey = btn.dataset.region || btn.dataset.crop;
      const reg = REGIONAL_PROFILES[regKey] || REGIONAL_PROFILES[btn.dataset.crop];
      if (reg) {
        simParams.region = regKey;
        simParams.kc = reg.kc;
        simParams.yield = reg.yield;
        simParams.cropName = reg.crop;
        
        const badgeDesc = document.getElementById('region-badge-desc');
        if (badgeDesc) badgeDesc.textContent = reg.desc;

        const seasonDaysBadge = document.getElementById('season-days-badge');
        if (seasonDaysBadge) seasonDaysBadge.textContent = `${reg.seasonDays}d`;

        const yieldSlider = document.getElementById('slider-yield');
        if (yieldSlider) {
          yieldSlider.min = reg.minYield;
          yieldSlider.max = reg.maxYield;
          yieldSlider.step = (reg.maxYield > 50) ? 5 : 0.1;
          yieldSlider.value = reg.yield;
          document.getElementById('val-yield').textContent = `${reg.yield} ton/ha`;
        }
        updateCalculations();
      }
    });
  });

  // Display Mode toggle
  document.getElementById('btn-show-total').addEventListener('click', () => {
    document.getElementById('btn-show-total').classList.add('active');
    document.getElementById('btn-show-partition').classList.remove('active');
    simParams.displayMode = 'total';
    updateCalculations();
  });

  document.getElementById('btn-show-partition').addEventListener('click', () => {
    document.getElementById('btn-show-partition').classList.add('active');
    document.getElementById('btn-show-total').classList.remove('active');
    simParams.displayMode = 'partition';
    updateCalculations();
  });

  // Reset button
  document.getElementById('btn-reset-params').addEventListener('click', () => {
    simParams.tempDelta = 2.0;
    simParams.solarDelta = 5.0;
    simParams.precipDelta = -10.0;
    simParams.alpha = 0.90;
    simParams.yield = 150.0;
    simParams.kc = 0.50;
    simParams.targetHorizonYear = 2050;
    simParams.durationMode = 'annual';
    simParams.region = 'kolhapur';

    document.getElementById('slider-temp').value = 2.0;
    document.getElementById('val-temp').textContent = '+2.0 °C';
    document.getElementById('slider-solar').value = 5;
    document.getElementById('val-solar').textContent = '+5 %';
    document.getElementById('slider-precip').value = -10;
    document.getElementById('val-precip').textContent = '-10 %';
    document.getElementById('slider-alpha').value = 0.90;
    document.getElementById('val-alpha').textContent = '0.90';
    document.getElementById('slider-yield').value = 150;
    document.getElementById('val-yield').textContent = '150 ton/ha';
    
    if (horizonSlider) horizonSlider.value = 2050;
    const valH = document.getElementById('val-horizon');
    if (valH) valH.textContent = 'Year 2050';

    document.querySelectorAll('.btn-horizon').forEach(b => {
      if (b.dataset.year === "2050") b.classList.add('active');
      else b.classList.remove('active');
    });

    if (btnAnn && btnSea) {
      btnAnn.classList.add('active');
      btnSea.classList.remove('active');
    }

    document.querySelectorAll('.btn-preset').forEach(b => b.classList.remove('active'));
    document.querySelector('.btn-preset[data-crop="sugarcane"]').classList.add('active');

    updateHorizonLabels(2050);
    updateCalculations();
  });

  // Year selector
  document.getElementById('year-selector').addEventListener('change', (e) => {
    const yr = parseInt(e.target.value);
    updateHistoricalExplorer(yr);
  });
}

function updateHorizonLabels(yr) {
  const el1 = document.getElementById('display-horizon-year');
  if (el1) el1.textContent = yr;
  const el2 = document.getElementById('display-horizon-badge');
  if (el2) el2.textContent = yr;
  const el3 = document.getElementById('footer-horizon-lbl');
  if (el3) el3.textContent = yr;
  const el4 = document.getElementById('kpi-horizon-lbl');
  if (el4) el4.textContent = `Projected ${yr} Total CWF`;
}

function populateYearSelector() {
  const select = document.getElementById('year-selector');
  HISTORICAL_DATA.years.slice().reverse().forEach(yr => {
    const opt = document.createElement('option');
    opt.value = yr;
    opt.textContent = `Year ${yr}`;
    if (yr === 2025) opt.selected = true;
    select.appendChild(opt);
  });
}

// Generate the self-completing future curve across the chosen horizon
function computeProjections() {
  const futureYears = [];
  const futureTotal = [];
  const futureGreen = [];
  const futureBlue = [];

  const targetYear = simParams.targetHorizonYear || 2050;
  const reg = REGIONAL_PROFILES[simParams.region] || REGIONAL_PROFILES.kolhapur;
  const durationFactor = (simParams.durationMode === 'growing_season') ? (reg.seasonDays / 365.25) : 1.0;
  const regScale = (reg.baseHistoricalTWF / 222.1);

  const baseline2025Total = HISTORICAL_DATA.total_cwf[HISTORICAL_DATA.total_cwf.length - 1] * regScale * durationFactor;
  const baseline2025Green = HISTORICAL_DATA.green_cwf[HISTORICAL_DATA.green_cwf.length - 1] * regScale * durationFactor;
  const baseline2025Blue = HISTORICAL_DATA.blue_cwf[HISTORICAL_DATA.blue_cwf.length - 1] * regScale * durationFactor;

  const totalYearsSpan = Math.max(1, targetYear - 2025);

  for (let year = 2026; year <= targetYear; year++) {
    futureYears.push(year);
    const progress = (year - 2025) / totalYearsSpan; // 0.0 to 1.0

    // Thermodynamic Scaling Factors
    const curTempDrift = simParams.tempDelta * progress;
    const curSolarDrift = (simParams.solarDelta / 100.0) * progress;
    const curPrecipDrift = (simParams.precipDelta / 100.0) * progress;

    // Potential Evapotranspiration Expansion (Clausius-Clapeyron + direct flux)
    const etMultiplier = (1.0 + 0.045 * curTempDrift + curSolarDrift);
    
    // Effective Rainfall change
    const curAlpha = 0.95 - (0.95 - simParams.alpha) * progress;
    const rainMultiplier = Math.max(0.1, (1.0 + curPrecipDrift) * (curAlpha / 0.95));

    // Yield scaling vs baseline
    const yieldMultiplier = reg.yield / simParams.yield;
    const cropKcMultiplier = simParams.kc / reg.kc;

    // Projected CWF components
    const projectedGreen = Math.max(5.0, baseline2025Green * rainMultiplier * cropKcMultiplier * yieldMultiplier);
    const projectedTotal = baseline2025Total * etMultiplier * cropKcMultiplier * yieldMultiplier;
    const projectedBlue = Math.max(5.0, projectedTotal - projectedGreen);

    futureGreen.push(projectedGreen);
    futureBlue.push(projectedBlue);
    futureTotal.push(projectedTotal);
  }

  return {
    futureYears,
    futureTotal,
    futureGreen,
    futureBlue,
    regScale,
    durationFactor
  };
}

// Update live calculations and re-render chart
function updateCalculations() {
  const proj = computeProjections();

  const targetYear = simParams.targetHorizonYear || 2050;
  const valHorizonTotal = proj.futureTotal[proj.futureTotal.length - 1] || (HISTORICAL_DATA.total_cwf[HISTORICAL_DATA.total_cwf.length - 1] * proj.regScale * proj.durationFactor);
  const valHorizonGreen = proj.futureGreen[proj.futureGreen.length - 1] || (HISTORICAL_DATA.green_cwf[HISTORICAL_DATA.green_cwf.length - 1] * proj.regScale * proj.durationFactor);
  const valHorizonBlue = proj.futureBlue[proj.futureBlue.length - 1] || (HISTORICAL_DATA.blue_cwf[HISTORICAL_DATA.blue_cwf.length - 1] * proj.regScale * proj.durationFactor);
  
  const baseline = HISTORICAL_DATA.total_cwf[HISTORICAL_DATA.total_cwf.length - 1] * proj.regScale * proj.durationFactor;
  const pctShift = ((valHorizonTotal - baseline) / baseline) * 100.0;

  // Update KPI Cards
  document.getElementById('kpi-2050-twf').innerHTML = `${valHorizonTotal.toFixed(1)} <span class="unit">m³/ton</span>`;
  
  const deltaBadge = document.getElementById('kpi-2050-delta');
  if (pctShift >= 0) {
    deltaBadge.innerHTML = `<span class="badge-tag warning">+${pctShift.toFixed(1)}% ${targetYear} Shift</span>`;
  } else {
    deltaBadge.innerHTML = `<span class="badge-tag info">${pctShift.toFixed(1)}% ${targetYear} Shift</span>`;
  }

  const blueShare = (valHorizonBlue / valHorizonTotal) * 100.0;
  document.getElementById('kpi-blue-share').textContent = `Blue Water: ${valHorizonBlue.toFixed(1)} m³/ton (${blueShare.toFixed(0)}%)`;
  
  const stressEl = document.getElementById('kpi-irrigation-stress');
  const blueThreshold = 190.0 * proj.regScale * proj.durationFactor;
  if (valHorizonBlue > blueThreshold * 1.1) {
    stressEl.textContent = 'Critical Alert';
    stressEl.style.color = '#ef4444';
  } else if (valHorizonBlue > blueThreshold) {
    stressEl.textContent = 'High Stress';
    stressEl.style.color = '#f59e0b';
  } else {
    stressEl.textContent = 'Moderate';
    stressEl.style.color = '#10b981';
  }

  // Update Footer Metrics
  const base1990 = HISTORICAL_DATA.total_cwf[0] * proj.regScale * proj.durationFactor;
  const base2025 = HISTORICAL_DATA.total_cwf[HISTORICAL_DATA.total_cwf.length - 1] * proj.regScale * proj.durationFactor;
  
  const f1990El = document.getElementById('footer-1990-val');
  if (f1990El) f1990El.textContent = `${base1990.toFixed(1)} m³/t`;

  const f2025El = document.getElementById('footer-2025-val');
  if (f2025El) f2025El.textContent = `${base2025.toFixed(1)} m³/t`;

  document.getElementById('footer-2050-val').textContent = `${valHorizonTotal.toFixed(1)} m³/t`;
  const varNet = ((valHorizonTotal - base1990) / base1990) * 100.0;
  document.getElementById('footer-variance-val').textContent = `${varNet >= 0 ? '+' : ''}${varNet.toFixed(1)}% (${(valHorizonTotal / base1990).toFixed(2)}x)`;

  // Update Main Chart
  updateChartData(proj);
}


// Chart.js Main Curve Initialization
function initMainChart() {
  const ctx = document.getElementById('cwfCurveChart').getContext('2d');

  mainChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: []
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          labels: {
            color: '#94a3b8',
            font: { family: 'Plus Jakarta Sans', size: 12 }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          titleFont: { family: 'Outfit', size: 13, weight: 'bold' },
          bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)} m³/ton`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#64748b',
            font: { family: 'Outfit', size: 11 },
            maxTicksLimit: 15
          }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#64748b',
            font: { family: 'Outfit', size: 11 }
          },
          title: {
            display: true,
            text: 'Crop Water Footprint (m³/ton)',
            color: '#94a3b8',
            font: { family: 'Plus Jakarta Sans', size: 12, weight: 600 }
          }
        }
      }
    }
  });
}

function updateChartData(proj) {
  if (!mainChart) return;

  const allYears = [...HISTORICAL_DATA.years, ...proj.futureYears];
  mainChart.data.labels = allYears;
  const targetYear = simParams.targetHorizonYear || 2050;

  const histScaledTotal = HISTORICAL_DATA.total_cwf.map(v => v * proj.regScale * proj.durationFactor);
  const histScaledGreen = HISTORICAL_DATA.green_cwf.map(v => v * proj.regScale * proj.durationFactor);
  const histScaledBlue = HISTORICAL_DATA.blue_cwf.map(v => v * proj.regScale * proj.durationFactor);

  if (simParams.displayMode === 'total') {
    // Mode 1: Total CWF with dashed future extension
    const histData = [...histScaledTotal, ...Array(proj.futureYears.length).fill(null)];
    const futData = [...Array(HISTORICAL_DATA.years.length - 1).fill(null), histScaledTotal[histScaledTotal.length - 1], ...proj.futureTotal];

    mainChart.data.datasets = [
      {
        label: 'Historical Validated CWF (1990–2025)',
        data: histData,
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.1)',
        borderWidth: 2.5,
        pointRadius: 2,
        tension: 0.2,
        fill: false
      },
      {
        label: `AI Projected Horizon (2026–${targetYear})`,
        data: futData,
        borderColor: '#34d399',
        backgroundColor: 'rgba(52, 211, 153, 0.1)',
        borderWidth: 2.5,
        borderDash: [6, 6],
        pointRadius: 2,
        pointBackgroundColor: '#34d399',
        tension: 0.2,
        fill: false
      }
    ];
  } else {
    // Mode 2: Partitioned Green vs Blue
    const greenHist = [...histScaledGreen, ...Array(proj.futureYears.length).fill(null)];
    const greenFut = [...Array(HISTORICAL_DATA.years.length - 1).fill(null), histScaledGreen[histScaledGreen.length - 1], ...proj.futureGreen];

    const blueHist = [...histScaledBlue, ...Array(proj.futureYears.length).fill(null)];
    const blueFut = [...Array(HISTORICAL_DATA.years.length - 1).fill(null), histScaledBlue[histScaledBlue.length - 1], ...proj.futureBlue];

    mainChart.data.datasets = [
      {
        label: 'Green Water (Rainfall) 1990–2025',
        data: greenHist,
        borderColor: '#10b981',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.2
      },
      {
        label: `Green Water Projected (2026–${targetYear})`,
        data: greenFut,
        borderColor: '#10b981',
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 0,
        tension: 0.2
      },
      {
        label: 'Blue Water (Irrigation) 1990–2025',
        data: blueHist,
        borderColor: '#3b82f6',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.2
      },
      {
        label: `Blue Water Projected (2026–${targetYear})`,
        data: blueFut,
        borderColor: '#3b82f6',
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 0,
        tension: 0.2
      }
    ];
  }

  mainChart.update();
}


// Historical Explorer & Pie Chart
function initPieChart(initialYear) {
  const ctx = document.getElementById('historicalPieChart').getContext('2d');
  pieChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Green Water (Rain)', 'Blue Water (Irrigation)'],
      datasets: [{
        data: [38.7, 183.4],
        backgroundColor: ['#10b981', '#3b82f6'],
        borderWidth: 0,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 11 } }
        }
      },
      cutout: '70%'
    }
  });

  updateHistoricalExplorer(initialYear);
}

function updateHistoricalExplorer(year) {
  const idx = HISTORICAL_DATA.years.indexOf(year);
  if (idx === -1) return;

  document.getElementById('exp-year-display').textContent = `Year ${year}`;
  
  const eraBadge = document.getElementById('exp-era-badge');
  if (year < 2000) {
    eraBadge.textContent = 'Pre-MODIS Blind Hindcast (1990–1999)';
    eraBadge.style.color = '#c084fc';
    eraBadge.style.background = 'rgba(139, 92, 246, 0.15)';
    eraBadge.style.borderColor = 'rgba(139, 92, 246, 0.3)';
  } else {
    eraBadge.textContent = 'Satellite Validated Record (2000–2025)';
    eraBadge.style.color = '#38bdf8';
    eraBadge.style.background = 'rgba(6, 182, 212, 0.12)';
    eraBadge.style.borderColor = 'rgba(6, 182, 212, 0.3)';
  }

  // Lookup nearest stats
  const statKey = HISTORICAL_DATA.stats[year] ? year : Object.keys(HISTORICAL_DATA.stats).reduce((prev, curr) => Math.abs(curr - year) < Math.abs(prev - year) ? curr : prev);
  const st = HISTORICAL_DATA.stats[statKey];

  document.getElementById('exp-r2').textContent = `${st.r2.toFixed(2)}%`;
  document.getElementById('exp-rmse').textContent = `${st.rmse.toFixed(4)} mm`;
  document.getElementById('exp-mae').textContent = `${st.mae.toFixed(4)} mm`;
  document.getElementById('exp-corr').textContent = `${st.corr.toFixed(4)}`;
  document.getElementById('exp-act-et').textContent = `${st.act_et.toFixed(3)} mm`;
  document.getElementById('exp-pred-et').textContent = `${st.pred_et.toFixed(3)} mm`;

  // Update Doughnut
  const gwf = HISTORICAL_DATA.green_cwf[idx];
  const bwf = HISTORICAL_DATA.blue_cwf[idx];

  if (pieChart) {
    pieChart.data.datasets[0].data = [gwf, bwf];
    pieChart.update();
  }
}
