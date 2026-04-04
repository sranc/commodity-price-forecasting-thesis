import pandas as pd
import yaml
from pathlib import Path
import logging
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def get_daily_raw_files(paths_cfg: dict, targets_cfg: list, exogenous_cfg: dict) -> dict:
    """Retorna un diccionario con las rutas de los CSVs diarios a procesar y su categoría."""
    raw_targets_dir = Path(paths_cfg["data"]["raw_targets"])
    raw_market_dir = Path(paths_cfg["data"]["raw_exogenous"]) / "market"
    
    files_to_process = {}
    
    # Target files (Diarios)
    for target in targets_cfg.get("metals", []):
        name = target["name"]
        files_to_process[name] = {
            "filepath": raw_targets_dir / f"{name}.csv",
            "category": "targets"
        }
        
    # Exogenous (Market) files (Diarios)
    # Nota: Macro son mensuales, esos no entran acá.
    for marker in exogenous_cfg.get("market", []):
        name = marker["name"]
        files_to_process[name] = {
            "filepath": raw_market_dir / f"{name}.csv",
            "category": "exogenous/market"
        }
        
    return files_to_process

def process_and_align_daily_data(daily_files: dict, interim_dir: Path):
    """Carga los CSVs, determina el rango temporal global y alinea cada dataset a un índice Business Day."""
    dfs = {}
    categories = {}
    min_date = None
    max_date = None
    
    # 1. Cargar todos los dataframes y encontrar las fechas globales
    for name, info in daily_files.items():
        filepath = info["filepath"]
        categories[name] = info["category"]
        
        if not filepath.exists():
            continue
        
        df = pd.read_csv(filepath, parse_dates=['Date'], index_col='Date')
        dfs[name] = df
        
        if df.empty:
            continue
            
        current_min = df.index.min()
        current_max = df.index.max()
        
        if min_date is None or current_min < min_date:
            min_date = current_min
        if max_date is None or current_max > max_date:
            max_date = current_max
            
    if not dfs:
        logging.error("No se cargaron datos.")
        return
        
    logging.info(f"Rango global detectado: {min_date.date()} hasta {max_date.date()}")
    
    # 2. Crear Índice Continuo de días hábiles (Business Days)
    bdate_index = pd.bdate_range(start=min_date, end=max_date, name='Date')
    logging.info(f"Índice continuo de días hábiles con {len(bdate_index)} días.")
    
    # 3. Alinear, interpolar (ffill) y guardar archivos por separado
    for name, df in dfs.items():
        # Re-indexar al nuevo calendario matriz
        aligned_df = df.reindex(bdate_index)
        
        # Recuento de nulos inducidos por la alineación
        initial_nans = aligned_df.isnull().sum().sum()
        
        # Forward fill (rellenar feriados)
        aligned_df = aligned_df.ffill()
        
        # En caso de haber días hábiles previos sin datos al puro inicio (bfill)
        aligned_df = aligned_df.bfill()
        
        final_nans = aligned_df.isnull().sum().sum()
        logging.info(f" - {name}: Alineado. Nulos arreglados: {initial_nans} -> {final_nans}")
        
        # Exportar
        category_dir = interim_dir / categories[name]
        category_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = category_dir / f"{name}.csv"
        aligned_df.to_csv(output_file)
        logging.info(f"   [OK] Guardado en: data/interim/{categories[name]}/{name}.csv")

def main():
    root_dir = Path(__file__).resolve().parents[2]
    config_dir = root_dir / "config"
    
    # Load configs
    paths_cfg = load_config(config_dir / "paths.yaml")
    targets_cfg = load_config(config_dir / "metals.yaml")
    exogenous_cfg = load_config(config_dir / "exogenous.yaml")
    
    interim_dir = root_dir / paths_cfg["data"]["interim"]
    interim_dir.mkdir(parents=True, exist_ok=True)
    
    daily_files = get_daily_raw_files(paths_cfg, targets_cfg, exogenous_cfg)
    
    logging.info(f"Archivos diarios encontrados listos para limpiar:")
    for name, info in daily_files.items():
        filepath = info["filepath"]
        if filepath.exists():
            logging.info(f" - [{info['category']}] {name}: {filepath.name}")
        else:
            logging.warning(f" - [{info['category']}] {name}: {filepath.name} NO ENCONTRADO")
            
    logging.info("Iniciando procesamiento y alineación de fechas...")
    process_and_align_daily_data(daily_files, interim_dir)

if __name__ == "__main__":
    main()
