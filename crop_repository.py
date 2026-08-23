from db_models import SessionLocal, CropProfileModel, SoilProfileModel, init_db

class CropSoilRepository:
    """
    Plug-and-Play Repository for Biological Crops and Soil Hydraulic Properties.
    
    Supports runtime database queries, in-memory caching, and dynamic registration
    of custom regional crop genotypes or soil profiles.
    """
    def __init__(self):
        init_db()

    def get_crop_profile(self, crop_key: str, growth_stage: str = 'average') -> dict:
        """
        Fetches the phenological crop profile from database.
        
        Args:
            crop_key (str): Crop identifier (e.g. 'sugarcane', 'cotton', 'wheat', 'rice').
            growth_stage (str): 'initial', 'mid', 'end', or 'average'.
            
        Returns:
            dict: Phenological constants (Kc, baseline yield, root depth, p depletion).
        """
        db = SessionLocal()
        try:
            profile = db.query(CropProfileModel).filter_by(crop_key=crop_key.lower()).first()
            if not profile:
                # Fallback to sugarcane if unknown
                profile = db.query(CropProfileModel).filter_by(crop_key='sugarcane').first()

            kc_map = {
                'initial': profile.kc_ini,
                'mid': profile.kc_mid,
                'end': profile.kc_end,
                'average': profile.kc_avg
            }
            kc_selected = kc_map.get(growth_stage.lower(), profile.kc_avg)

            return {
                'crop_key': profile.crop_key,
                'name': profile.name,
                'kc_selected': kc_selected,
                'kc_ini': profile.kc_ini,
                'kc_mid': profile.kc_mid,
                'kc_end': profile.kc_end,
                'kc_avg': profile.kc_avg,
                'yield_baseline_ton_ha': profile.yield_baseline_ton_ha,
                'root_depth_m': profile.root_depth_m,
                'depletion_fraction_p': profile.depletion_fraction_p
            }
        finally:
            db.close()

    def get_soil_profile(self, soil_key: str) -> dict:
        """
        Fetches the hydraulic soil matrix properties from database.
        
        Args:
            soil_key (str): Soil texture key (e.g. 'loam', 'clay', 'sandy_loam').
            
        Returns:
            dict: Hydraulic parameters (FC, WP, infiltration alpha).
        """
        db = SessionLocal()
        try:
            profile = db.query(SoilProfileModel).filter_by(soil_key=soil_key.lower()).first()
            if not profile:
                profile = db.query(SoilProfileModel).filter_by(soil_key='loam').first()

            return {
                'soil_key': profile.soil_key,
                'name': profile.name,
                'field_capacity_fc': profile.field_capacity_fc,
                'wilting_point_wp': profile.wilting_point_wp,
                'infiltration_alpha': profile.infiltration_alpha,
                'description': profile.description
            }
        finally:
            db.close()

    def register_custom_crop(self, 
                             crop_key: str, 
                             name: str, 
                             kc_ini: float, 
                             kc_mid: float, 
                             kc_end: float, 
                             kc_avg: float, 
                             yield_baseline_ton_ha: float, 
                             root_depth_m: float = 1.0, 
                             depletion_fraction_p: float = 0.5) -> bool:
        """
        Dynamically registers a custom crop profile into the database at runtime.
        """
        db = SessionLocal()
        try:
            existing = db.query(CropProfileModel).filter_by(crop_key=crop_key.lower()).first()
            if existing:
                existing.name = name
                existing.kc_ini = kc_ini
                existing.kc_mid = kc_mid
                existing.kc_end = kc_end
                existing.kc_avg = kc_avg
                existing.yield_baseline_ton_ha = yield_baseline_ton_ha
                existing.root_depth_m = root_depth_m
                existing.depletion_fraction_p = depletion_fraction_p
            else:
                new_crop = CropProfileModel(
                    crop_key=crop_key.lower(),
                    name=name,
                    kc_ini=kc_ini,
                    kc_mid=kc_mid,
                    kc_end=kc_end,
                    kc_avg=kc_avg,
                    yield_baseline_ton_ha=yield_baseline_ton_ha,
                    root_depth_m=root_depth_m,
                    depletion_fraction_p=depletion_fraction_p
                )
                db.add(new_crop)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"[Repo] Error registering custom crop: {e}")
            return False
        finally:
            db.close()
