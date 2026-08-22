# AI-based Crop Water Footprint Predictor

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LightGBM](https://img.shields.io/badge/Model-LightGBM-green.svg)](https://lightgbm.readthedocs.io/)
[![Google Earth Engine](https://img.shields.io/badge/Data-Google%20Earth%20Engine-34A853.svg)](https://earthengine.google.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An agro-hydrological Machine Learning system that combines Google Earth Engine (GEE) satellite imagery with LightGBM gradient boosted decision trees to track, partition, and predict agricultural **Crop Water Footprints (CWF)** across multi-decade timelines (1990–2025).

The system accurately partitions water consumption into **Green Water** (natural rainfall consumed) and **Blue Water** (pumped irrigation water consumed) in $m^3/\text{ton}$ according to FAO-56 / Water Footprint Network standards.

---

## 🌟 Key Highlights & Accuracy

* **Multi-Decade Predictive Accuracy (2000–2025)**: Achieves **$98.64\%$ $R^2$ accuracy** with an $\text{RMSE} = 0.1897\text{ }mm$ across 37,984 6-hourly timesteps.
* **Pre-MODIS Blind Historical Hindcast (1990–1999)**: Inferred 10 years of historical crop water usage prior to modern satellite availability with **$98.33\%$ $R^2$ accuracy**.
* **Physics-Informed Feature Representation**: Uses 22 engineered features including multi-step lag memory (6h, 24h), rolling statistics (24h, 48h), and cyclical solar harmonics ($\sin/\cos$).
* **Outlier Cleansing & Robustness**: Employs an `IsolationForest` pipeline to pre-filter atmospheric sensor and cloud-mask artifacts.

---

## 📊 Summary Performance (1990–2025)

| Period | Evaluation Domain | Samples | $R^2$ Accuracy (%) | RMSE ($mm$) | MAE ($mm$) | Pearson $r$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **1990–1999** | Blind Pre-MODIS Hindcast | 14,608 | **98.33%** | 0.2123 | 0.1687 | 0.9917 |
| **2000–2025** | Multi-Decade Validation | 37,984 | **98.64%** | 0.1897 | 0.1506 | 0.9932 |
| **1990–2025** | **Total 36-Year Pipeline** | **52,592** | **98.55%** | **0.1963** | **0.1557** | **0.9928** |

---

## 📁 Repository Structure

```
├── config.py                 # Central configurations, hyperparameters & physical constants
├── extractor.py              # Google Earth Engine data extraction engine
├── compiler.py               # Time-series ingestion, cleaning & 22-feature engineering
├── trainer.py                # Expanding-window validation & locked production trainer
├── evaluator.py              # 2000–2025 annual ground-truth statistical evaluator
├── evaluate_1990s.py         # 1990–1999 historical hindcast evaluator
├── hindcast_predictor.py     # Blind historical CWF prediction engine for 1990–1999
├── calibrator.py             # FAO-56 / WFN Crop Water Footprint calculator & optimizer
├── visualizer.py             # Feature importance, learning curves, CWF breakdowns & maps
├── mock_data_generator.py    # Synthetic multi-decade generator for offline experimentation
├── test_pipeline.py          # Pytest automated test suite
├── main.py                   # Unified CLI orchestrator
├── requirements.txt          # Python dependencies
├── WALKTHROUGH.md            # Detailed 36-year mathematical and visual report
├── outputs/                  # Exported models, visualizations & summary tables
│   ├── final_production_model.pkl
│   ├── annual_accuracy_comparison.png
│   ├── cwf_prediction_1990_1999.png
│   └── water_footprint_breakdown.png
└── data/                     # Ingested datasets, predictions, and weight CSVs
```

---

## 🚀 Quickstart Guide

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/gnbreddy/AI-based-Crop-water-footprint-predictor.git
cd AI-based-Crop-water-footprint-predictor
pip install -r requirements.txt
```

### 2. Configure Environment (Optional for GEE)
Create a `.env` file from the provided template:
```bash
cp .env.example .env
# Edit .env and insert your Google Cloud project ID
```

### 3. Run the Complete Pipeline
```bash
# Run training, calibration, and visualization
python main.py --all --start-year 2000 --end-year 2025

# Evaluate 2000-2025 annual accuracy
python evaluator.py

# Run blind historical hindcasting for 1990-1999
python hindcast_predictor.py

# Run automated test suite
python -m pytest -v test_pipeline.py
```

---

## ⚖️ License
This project is licensed under the MIT License.
