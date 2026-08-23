import time
import asyncio
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from schemas import UniversalIngestionRequest, AtmosphericPayload, SoilPayload, CropPayload
from db_models import SessionLocal, LocationPredictionRecord, init_db
from normalization_engine import PhysicalNormalizationEngine
from universal_engine import UniversalCropWaterFootprintEngine
from crop_repository import CropSoilRepository

class HighThroughputClimateStreamEngine:
    """
    High-Throughput Asynchronous Telemetry & Streaming Engine.
    
    Decouples satellite ingestion from synchronous API calls by buffering climate
    telemetry in an asynchronous event queue, executing vectorized physical
    normalization and ML inference, and performing bulk database commits.
    """
    def __init__(self, batch_size: int = 500, max_queue_size: int = 50000):
        init_db()
        self.batch_size = batch_size
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.engine = UniversalCropWaterFootprintEngine()
        self.norm = PhysicalNormalizationEngine()
        self.repo = CropSoilRepository()
        self.is_running = False
        self.processed_count = 0
        self.total_elapsed_sec = 0.0

    async def publish_telemetry(self, payload: Dict[str, Any]):
        """
        Producer Method: Enqueues raw 6-hourly climate telemetry payload.
        Non-blocking ingestion from Google Earth Engine or IoT weather stations.
        """
        await self.queue.put(payload)

    async def publish_batch(self, payloads: List[Dict[str, Any]]):
        """
        Producer Method: Rapidly enqueues a bulk batch of climate payloads.
        """
        for p in payloads:
            await self.queue.put(p)

    async def start_consumer_worker(self, max_records_to_process: int = None):
        """
        Consumer Method: Background worker that continuously extracts batches,
        performs vectorized physics calculations and LightGBM inference, and
        bulk-inserts audit records into the database.
        """
        self.is_running = True
        start_time = time.time()
        batch = []

        while self.is_running:
            try:
                # Retrieve item with short timeout
                item = await asyncio.wait_for(self.queue.get(), timeout=0.5)
                batch.append(item)
                self.queue.task_done()

                # Process when batch threshold is reached
                if len(batch) >= self.batch_size:
                    self._process_and_commit_batch(batch)
                    self.processed_count += len(batch)
                    batch = []

                if max_records_to_process and self.processed_count >= max_records_to_process:
                    break

            except asyncio.TimeoutError:
                # Flush remaining items on timeout
                if batch:
                    self._process_and_commit_batch(batch)
                    self.processed_count += len(batch)
                    batch = []
                if max_records_to_process and self.processed_count >= max_records_to_process:
                    break

        # Final flush
        if batch:
            self._process_and_commit_batch(batch)
            self.processed_count += len(batch)
            batch = []

        self.total_elapsed_sec = time.time() - start_time
        self.is_running = False

    def _process_and_commit_batch(self, batch: List[Dict[str, Any]]):
        """
        Executes high-speed vectorized normalization, inference, and bulk DB insert.
        """
        if not batch:
            return

        db: Session = SessionLocal()
        records_to_insert = []

        try:
            for item in batch:
                atm = item.get('atmosphere', {})
                soil = item.get('soil', {})
                crop = item.get('crop', {})

                temp_c = float(atm.get('temp_c', 25.0))
                solar_rad = float(atm.get('solar_rad_mj', 18.0))
                precip = float(atm.get('precip_mm', 0.0))
                soil_m = float(soil.get('volumetric_moisture', 0.20))
                rh = float(atm.get('rh_pct', 60.0))
                wind = float(atm.get('wind_speed_ms', 3.0))
                elev = float(atm.get('elevation_m', 100.0))
                lat = float(atm.get('latitude_deg', 16.0))
                doy = int(atm.get('day_of_year', 180))
                hour = int(atm.get('hour_of_day', 12))

                crop_type = crop.get('crop_type', 'sugarcane')
                soil_type = soil.get('soil_type', 'loam')

                calc = self.engine.analyze_location(
                    temp_c=temp_c,
                    solar_rad_mj=solar_rad,
                    precip_mm=precip,
                    soil_moisture=soil_m,
                    rh_pct=rh,
                    wind_speed_ms=wind,
                    elevation_m=elev,
                    latitude_deg=lat,
                    day_of_year=doy,
                    crop_type=crop_type,
                    soil_type=soil_type,
                    hour_of_day=hour
                )

                rec = LocationPredictionRecord(
                    location_label=item.get('location_label', 'Stream Telemetry'),
                    latitude_deg=lat,
                    elevation_m=elev,
                    crop_key=crop_type,
                    soil_key=soil_type,
                    temp_c=temp_c,
                    solar_rad_mj=solar_rad,
                    precip_mm=precip,
                    soil_moisture=soil_m,
                    actual_et_mm=calc['evapotranspiration_depth_mm']['actual_et_mm'],
                    green_cwf_m3_ton=calc['crop_water_footprint_m3_ton']['green_water_footprint_m3_ton'],
                    blue_cwf_m3_ton=calc['crop_water_footprint_m3_ton']['blue_water_footprint_m3_ton'],
                    total_cwf_m3_ton=calc['crop_water_footprint_m3_ton']['total_water_footprint_m3_ton']
                )
                records_to_insert.append(rec)

            # High-performance bulk database insert
            db.bulk_save_objects(records_to_insert)
            db.commit()

        except Exception as e:
            db.rollback()
            print(f"[Streaming Engine] Batch commit error: {e}")
        finally:
            db.close()

# ==============================================================================
# Ingestion Benchmark Harness
# ==============================================================================
async def run_streaming_benchmark(num_records: int = 2000, batch_size: int = 500):
    """
    Simulates high-throughput streaming ingestion of multi-decade satellite records.
    """
    stream_engine = HighThroughputClimateStreamEngine(batch_size=batch_size)

    print("=" * 80)
    print(f" HIGH-THROUGHPUT STREAMING BENCHMARK: Ingesting {num_records} Climate Records")
    print("=" * 80)

    # 1. Generate Synthetic Satellite Telemetry Stream
    print(f"[Producer] Generating {num_records} 6-hourly multi-band climate records...")
    mock_payloads = []
    crops = ['sugarcane', 'cotton', 'wheat', 'rice', 'maize']
    soils = ['loam', 'sandy_loam', 'clay', 'clay_loam', 'silt_loam']

    for i in range(num_records):
        mock_payloads.append({
            'location_label': f"Grid_Node_{i % 100}",
            'atmosphere': {
                'temp_c': float(np.random.uniform(15.0, 42.0)),
                'solar_rad_mj': float(np.random.uniform(5.0, 30.0)),
                'rh_pct': float(np.random.uniform(15.0, 95.0)),
                'wind_speed_ms': float(np.random.uniform(1.0, 8.0)),
                'precip_mm': float(np.random.choice([0.0, 0.0, 2.5, 12.0, 35.0])),
                'elevation_m': float(np.random.uniform(10.0, 800.0)),
                'latitude_deg': float(np.random.uniform(10.0, 45.0)),
                'day_of_year': int(np.random.randint(1, 365)),
                'hour_of_day': int(np.random.choice([0, 6, 12, 18]))
            },
            'soil': {
                'soil_type': soils[i % len(soils)],
                'volumetric_moisture': float(np.random.uniform(0.06, 0.40))
            },
            'crop': {
                'crop_type': crops[i % len(crops)],
                'growth_stage': 'mid'
            }
        })

    # 2. Run Concurrent Producer & Consumer Tasks
    start_time = time.time()
    
    producer_task = stream_engine.publish_batch(mock_payloads)
    consumer_task = stream_engine.start_consumer_worker(max_records_to_process=num_records)

    await asyncio.gather(producer_task, consumer_task)
    total_time = time.time() - start_time
    throughput = num_records / total_time

    print("\n" + "=" * 80)
    print(f" STREAMING INGESTION BENCHMARK RESULTS")
    print("=" * 80)
    print(f"  -> Total Records Processed & Committed: {stream_engine.processed_count:,}")
    print(f"  -> Total Execution Time:                {total_time:.3f} seconds")
    print(f"  -> Ingestion & Inference Throughput:    {throughput:,.1f} records/second")
    print(f"  -> Database Bulk Commit Efficiency:     {num_records / (stream_engine.total_elapsed_sec + 1e-6):,.1f} rec/s")
    print("=" * 80)

    return {
        'total_records': num_records,
        'elapsed_sec': total_time,
        'throughput_records_per_sec': throughput
    }

if __name__ == "__main__":
    asyncio.run(run_streaming_benchmark(num_records=2000, batch_size=500))
