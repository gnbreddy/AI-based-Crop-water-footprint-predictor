import os
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

# ==============================================================================
# ORM Model: Soil Hydraulic Database Table
# ==============================================================================
class SoilProfileModel(Base):
    __tablename__ = 'soil_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    soil_key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    field_capacity_fc = Column(Float, nullable=False)
    wilting_point_wp = Column(Float, nullable=False)
    infiltration_alpha = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

# ==============================================================================
# ORM Model: Crop Phenology & Baseline Yield Database Table
# ==============================================================================
class CropProfileModel(Base):
    __tablename__ = 'crop_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    crop_key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    kc_ini = Column(Float, nullable=False)
    kc_mid = Column(Float, nullable=False)
    kc_end = Column(Float, nullable=False)
    kc_avg = Column(Float, nullable=False)
    yield_baseline_ton_ha = Column(Float, nullable=False)
    root_depth_m = Column(Float, nullable=False)
    depletion_fraction_p = Column(Float, nullable=False)
    created_at = Column(DateTime, default=get_utc_now)

# ==============================================================================
# ORM Model: Location Ingestion & Calculation Audit Table
# ==============================================================================
class LocationPredictionRecord(Base):
    __tablename__ = 'prediction_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_label = Column(String(100), nullable=False)
    latitude_deg = Column(Float, nullable=False)
    elevation_m = Column(Float, nullable=False)
    crop_key = Column(String(50), nullable=False)
    soil_key = Column(String(50), nullable=False)
    temp_c = Column(Float, nullable=False)
    solar_rad_mj = Column(Float, nullable=False)
    precip_mm = Column(Float, nullable=False)
    soil_moisture = Column(Float, nullable=False)
    actual_et_mm = Column(Float, nullable=False)
    green_cwf_m3_ton = Column(Float, nullable=False)
    blue_cwf_m3_ton = Column(Float, nullable=False)
    total_cwf_m3_ton = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=get_utc_now)

# Database Engine Initialization with WAL Mode & High-Concurrency Timeout
DB_URL = os.getenv('DATABASE_URL', 'sqlite:///data/universal_agri.db')

if DB_URL.startswith("sqlite"):
    engine = create_engine(
        DB_URL,
        echo=False,
        connect_args={"check_same_thread": False, "timeout": 60.0}
    )
else:
    engine = create_engine(DB_URL, echo=False, pool_size=20, max_overflow=30)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    """Initializes database schema and auto-seeds baseline FAO crop and soil tables."""
    os.makedirs('data', exist_ok=True)
    
    # Enable Write-Ahead Logging (WAL) for zero-lock concurrency in SQLite
    if DB_URL.startswith("sqlite"):
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            conn.exec_driver_sql("PRAGMA busy_timeout=60000;")
            
    Base.metadata.create_all(bind=engine)
    seed_initial_data()

def seed_initial_data():
    """Seeds standardized FAO-56 crop profiles and USDA soil hydraulic matrices."""
    from universal_engine import SOIL_DATABASE, CROP_DATABASE

    db = SessionLocal()
    try:
        # Seed Soils
        for key, s in SOIL_DATABASE.items():
            existing = db.query(SoilProfileModel).filter_by(soil_key=key).first()
            if not existing:
                soil_entry = SoilProfileModel(
                    soil_key=key,
                    name=key.replace('_', ' ').title(),
                    field_capacity_fc=s['field_capacity_fc'],
                    wilting_point_wp=s['wilting_point_wp'],
                    infiltration_alpha=s['infiltration_alpha'],
                    description=s['description']
                )
                db.add(soil_entry)

        # Seed Crops
        for key, c in CROP_DATABASE.items():
            existing = db.query(CropProfileModel).filter_by(crop_key=key).first()
            if not existing:
                crop_entry = CropProfileModel(
                    crop_key=key,
                    name=c['name'],
                    kc_ini=c['kc_ini'],
                    kc_mid=c['kc_mid'],
                    kc_end=c['kc_end'],
                    kc_avg=c['kc_avg'],
                    yield_baseline_ton_ha=c['yield_baseline_ton_ha'],
                    root_depth_m=c['root_depth_m'],
                    depletion_fraction_p=c['depletion_fraction_p']
                )
                db.add(crop_entry)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[DB] Notice: Seeding handled or skipped ({e})")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("[DB] Universal Agro-Hydrological Database initialized and seeded successfully.")
