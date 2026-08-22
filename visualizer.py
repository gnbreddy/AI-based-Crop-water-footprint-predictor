import os
import matplotlib.pyplot as plt
import folium
import numpy as np
import ee
from config import (
    HEATMAP_YIELD_BASELINE,
    MAP_INITIAL_LOCATION,
    MAP_INITIAL_ZOOM,
    ROI_COORDS,
    OUTPUT_DIR
)

def plot_feature_importance(best_run, save_path=None):
    """
    Plots horizontal bar chart of LightGBM feature importance (gain weights).
    """
    best_weights = best_run.get('weight_adjustments', {})
    if not best_weights:
        print("[Visualizer] No feature weights available to plot.")
        return

    sorted_weights = sorted(best_weights.items(), key=lambda item: item[1], reverse=True)
    feats, gains = zip(*sorted_weights)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(feats[::-1], gains[::-1], color='#008080', edgecolor='#004d4d', alpha=0.85)
    
    ax.set_title(
        f"LightGBM Feature Weight Adjustments\n(Optimal Validation Fold: Year {best_run.get('predicted_year', 'N/A')} | R² = {best_run.get('r2_accuracy', 0)*100:.1f}%)",
        fontsize=13,
        fontweight='bold',
        pad=15
    )
    ax.set_xlabel("Gain (Error Reduction Impact)", fontsize=11)
    ax.grid(axis='x', linestyle='--', alpha=0.5)

    # Annotate values on the bars
    for bar in bars:
        width = bar.get_width()
        ax.text(width * 1.01, bar.get_y() + bar.get_height()/2, f'{width:.1f}',
                va='center', ha='left', fontsize=9, color='#333333')

    plt.tight_layout()

    if save_path is None:
        save_path = os.path.join(OUTPUT_DIR, 'feature_importance.png')
    
    plt.savefig(save_path, dpi=300)
    print(f"[Visualizer] Feature importance chart saved to: {save_path}")
    plt.close()

def plot_learning_curve(process_history, save_path=None):
    """
    Plots the longitudinal accuracy (R²) and error reduction (RMSE/MAE) trajectories
    across cyclic expanding-window training epochs (e.g., 2000 -> 2025).
    """
    if not process_history:
        print("[Visualizer] No process history available to plot learning curve.")
        return

    epochs = [r['predicted_year'] for r in process_history]
    r2_scores = [r['r2_accuracy'] * 100.0 for r in process_history]
    rmse_scores = [r['rmse'] for r in process_history]
    mae_scores = [r['mae'] for r in process_history]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Subplot 1: R² Accuracy %
    ax1.plot(epochs, r2_scores, marker='o', color='#2ca02c', linewidth=2.5, label='Validation R² (%)')
    ax1.axhline(np.mean(r2_scores), color='#2ca02c', linestyle='--', alpha=0.6, label=f'Mean R² ({np.mean(r2_scores):.1f}%)')
    ax1.set_ylabel("R² Accuracy (%)", fontsize=11, fontweight='bold')
    ax1.set_title("Cyclic Expanding-Window Learning Curve (2000 -> 2025 Epochs)\n[1; 1,2; 1,2,3; 1,2,3,4; ...]", fontsize=13, fontweight='bold', pad=12)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='lower right')

    # Subplot 2: Error Reduction (RMSE & MAE)
    ax2.plot(epochs, rmse_scores, marker='s', color='#d62728', linewidth=2, label='RMSE (mm)')
    ax2.plot(epochs, mae_scores, marker='^', color='#1f77b4', linewidth=2, label='MAE (mm)')
    ax2.set_xlabel("Unseen Validation Year (Epoch Target)", fontsize=11, fontweight='bold')
    ax2.set_ylabel("Error Metric (mm)", fontsize=11, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='upper right')

    plt.xticks(epochs, rotation=45)
    plt.tight_layout()

    if save_path is None:
        save_path = os.path.join(OUTPUT_DIR, 'learning_curve_epochs.png')

    plt.savefig(save_path, dpi=300)
    print(f"[Visualizer] Expanding-window learning curve saved to: {save_path}")
    plt.close()

def plot_water_footprint_breakdown(cwf_results, save_path=None):
    """
    Plots the breakdown of Green vs Blue Crop Water Footprint (m3/ton).
    """
    gwf = cwf_results.get('green_water_footprint_m3_ton', 0.0)
    bwf = cwf_results.get('blue_water_footprint_m3_ton', 0.0)
    twf = cwf_results.get('total_water_footprint_m3_ton', 0.0)

    labels = ['Green Water Footprint\n(Rainfall)', 'Blue Water Footprint\n(Irrigation)']
    values = [gwf, bwf]
    colors = ['#2ca02c', '#1f77b4']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Bar chart
    bars = ax1.bar(labels, values, color=colors, edgecolor='black', alpha=0.85)
    ax1.set_ylabel("Water Footprint ($m^3/ton$)", fontsize=11)
    ax1.set_title(f"Total Water Footprint: {twf:.2f} $m^3/ton$", fontsize=12, fontweight='bold')
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height * 1.01,
                 f'{height:.2f} $m^3/t$', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Pie chart
    if twf > 0:
        ax2.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140,
                wedgeprops={'edgecolor': 'white', 'linewidth': 2})
        ax2.set_title("Partitioning Ratio", fontsize=12, fontweight='bold')

    plt.tight_layout()

    if save_path is None:
        save_path = os.path.join(OUTPUT_DIR, 'water_footprint_breakdown.png')

    plt.savefig(save_path, dpi=300)
    print(f"[Visualizer] CWF breakdown chart saved to: {save_path}")
    plt.close()

def generate_footprint_map(target_year, save_path=None):
    """
    Generates an interactive Folium geospatial heatmap of the Green Water Footprint
    over the Region of Interest (ROI), utilizing Earth Engine tile services with fallback.
    """
    if save_path is None:
        save_path = os.path.join(OUTPUT_DIR, f"water_footprint_map_{target_year}.html")

    m = folium.Map(
        location=MAP_INITIAL_LOCATION,
        zoom_start=MAP_INITIAL_ZOOM,
        tiles="CartoDB positron"
    )

    # Draw ROI Bounding Box
    min_lon, min_lat, max_lon, max_lat = ROI_COORDS
    bounds = [[min_lat, min_lon], [max_lat, max_lon]]
    folium.Rectangle(
        bounds=bounds,
        color="#ff7800",
        weight=2,
        fill=True,
        fill_opacity=0.1,
        popup=f"Study Area ROI [{min_lat}, {min_lon}] to [{max_lat}, {max_lon}]"
    ).add_to(m)

    # Attempt to load GEE MODIS Green Water Footprint overlay
    try:
        roi = ee.Geometry.Rectangle(ROI_COORDS)
        start_date, end_date = f'{target_year}-01-01', f'{target_year}-12-31'
        modis_et = ee.ImageCollection('MODIS/061/MOD16A2') \
            .filterDate(start_date, end_date) \
            .select('ET') \
            .mean() \
            .multiply(0.1)

        # GWF in m3/ton: (ET mm * 10) / Yield (ton/ha)
        gwf_image = modis_et.multiply(10).divide(HEATMAP_YIELD_BASELINE).clip(roi)
        
        vis_params = {
            'min': 50,
            'max': 180,
            'palette': ['#0000ff', '#00ff00', '#ffff00', '#ffa500', '#ff0000']
        }
        
        map_id_dict = ee.Image(gwf_image).getMapId(vis_params)
        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine / MODIS',
            name=f'Green Water Footprint {target_year} (m3/ton)',
            overlay=True,
            control=True,
            opacity=0.75
        ).add_to(m)
        print("[Visualizer] Added Google Earth Engine MODIS raster layer to map.")
    except Exception as e:
        print(f"[Visualizer] Notice: GEE Tile Layer offline or unauthenticated ({e}). Map created with ROI bounding box.")

    folium.LayerControl().add_to(m)
    m.save(save_path)
    print(f"[Visualizer] Interactive spatial map saved to: {save_path}")
    return save_path
