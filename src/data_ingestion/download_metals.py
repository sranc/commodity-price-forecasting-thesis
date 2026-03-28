import yfinance as yf
import pandas as pd
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List
from tenacity import retry, stop_after_attempt, wait_exponential

# Configurar el sistema de logs (mejor que prints)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def load_config() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Carga los archivos de configuración en diccionarios."""
    with open("config/metals.yaml", "r") as f:
        metals_config = yaml.safe_load(f)
        
    with open("config/paths.yaml", "r") as f:
        paths_config = yaml.safe_load(f)
        
    return metals_config, paths_config

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def execute_yfinance_download(ticker: str, start_date: str, end_date: str = None) -> pd.DataFrame:
    """Ejecuta la descarga de YFinance con reintentos automáticos."""
    kwargs = {"start": start_date, "progress": False, "multi_level_index": False}
    if end_date:
        kwargs["end"] = end_date
    return yf.download(ticker, **kwargs)

def download_metal(name: str, ticker: str, output_dir: Path, start_date: str, end_date: str = None) -> None:
    """Descarga datos crudos guardándolos SIN ALTERARLOS usando yfinance."""
    logging.info(f"Descargando {name} ({ticker}) desde {start_date}...")
    
    try:
        df = execute_yfinance_download(ticker, start_date, end_date)
        
        if df.empty:
            logging.warning(f"No hay datos disponibles para {name} ({ticker})")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        df = df[required_cols]

        output_file = output_dir / f"{name}.csv"
        df.to_csv(output_file)
        logging.info(f"✅ Guardado con éxito → {output_file}")

    except Exception as e:
        logging.error(f"❌ Falló la descarga para {name} tras varios intentos: {str(e)}")

def main() -> None:
    # 1. Leer Configuración 
    metals_config, paths_config = load_config()
    target_metals: List[Dict[str, str]] = metals_config.get("metals", [])
    
    # Extraer fechas de configuración
    dates_config = metals_config.get("dates", {})
    start_date = dates_config.get("start_date", "2015-07-01") # Adaptado al Zinc
    end_date = dates_config.get("end_date")
    if not end_date:  
        end_date = None
    
    # 2. Configurar directorio RAW
    output_dir = Path(paths_config["data"]["raw_targets"])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Descargar respetando la config
    for metal_info in target_metals:
        name = metal_info.get("name")
        ticker = metal_info.get("ticker")
        
        if name and ticker:
            download_metal(name, ticker, output_dir, start_date, end_date)
        else:
            logging.warning(f"Entrada inválida en config. Se requiere 'name' y 'ticker': {metal_info}")

if __name__ == "__main__":
    import os
    # Asegurarnos de que estamos ejecutando desde la raíz del proyecto
    project_root = Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    main()