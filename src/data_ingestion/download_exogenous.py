import os
import yfinance as yf
import pandas as pd
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from fredapi import Fred

# Cargar variables de entorno (API Keys)
load_dotenv()

# Configurar el sistema de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Carga los archivos de configuración en diccionarios."""
    with open("config/exogenous.yaml", "r") as f:
        exogenous_config = yaml.safe_load(f)
        
    with open("config/paths.yaml", "r") as f:
        paths_config = yaml.safe_load(f)
        
    return exogenous_config, paths_config

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def execute_yfinance_download(ticker: str, start_date: str, end_date: str = None) -> pd.DataFrame:
    """Ejecuta la descarga de YFinance con reintentos automáticos."""
    kwargs = {"start": start_date, "progress": False, "multi_level_index": False}
    if end_date:
        kwargs["end"] = end_date
    return yf.download(ticker, **kwargs)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def execute_fred_download(ticker: str, start_date: str, end_date: str = None) -> pd.DataFrame:
    """Ejecuta la descarga desde FRED usando la API Key."""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise ValueError("FRED_API_KEY no encontrada en el archivo .env")
    
    fred = Fred(api_key=api_key)
    kwargs = {"observation_start": start_date}
    if end_date:
         kwargs["observation_end"] = end_date
         
    series = fred.get_series(ticker, **kwargs)
    
    if series.empty:
        return pd.DataFrame()
        
    # Guardamos los datos macro de FRED tal cual en su frecuencia original (Mensual/Trimestral).
    # Las transformaciones (ffill, interpolación) se documentarán y aplicarán en la etapa de preprocesamiento.
    df = pd.DataFrame(series, columns=['Value'])
    df.index.name = 'Date'
    
    # Recortar al start_date oficial
    df = df.loc[start_date:]

    return df[['Value']]

def download_exogenous_factor(name: str, ticker: str, output_dir: Path, start_date: str, end_date: str = None) -> None:
    """Enruta y descarga datos crudos usando API mappings."""
    logging.info(f"Descargando {name} ({ticker}) desde {start_date}...")
    
    try:
        # Enrutador de APIs
        if ticker.startswith("FRED:"):
            real_ticker = ticker.split("FRED:")[1]
            df = execute_fred_download(real_ticker, start_date, end_date)
            # Renombrar 'Value' al nombre exacto de la variable macro
            df.rename(columns={'Value': name}, inplace=True)
        else:
            df = execute_yfinance_download(ticker, start_date, end_date)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Filtrar a OHLCV solo si es data de mercado financiero
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            available_cols = [col for col in required_cols if col in df.columns]
            df = df[available_cols]

        if df.empty:
            logging.warning(f"No hay datos disponibles para {name} ({ticker})")
            return

        output_file = output_dir / f"{name}.csv"
        df.to_csv(output_file)
        logging.info(f"✅ Guardado con éxito → {output_file}")

    except Exception as e:
        logging.error(f"❌ Falló la descarga para {name} tras varios intentos: {str(e)}")

def main() -> None:
    # 1. Leer Configuración 
    exogenous_config, paths_config = load_config()
    
    # Extraer fechas de configuración
    dates_config = exogenous_config.get("dates", {})
    start_date = dates_config.get("start_date", "2015-07-01")
    end_date = dates_config.get("end_date")
    if not end_date:  
        end_date = None
        
    # Rutas base
    base_raw_exog = Path(paths_config["data"]["raw_exogenous"])
    
    # Descargar datos de mercado
    market_factors = exogenous_config.get("market", [])
    if market_factors:
        market_dir = base_raw_exog / "market"
        market_dir.mkdir(parents=True, exist_ok=True)
        for item in market_factors:
            download_exogenous_factor(item["name"], item["ticker"], market_dir, start_date, end_date)

    # Descargar datos macro
    macro_factors = exogenous_config.get("macro", [])
    if macro_factors:
        macro_dir = base_raw_exog / "macro"
        macro_dir.mkdir(parents=True, exist_ok=True)
        for item in macro_factors:
            download_exogenous_factor(item["name"], item["ticker"], macro_dir, start_date, end_date)

if __name__ == "__main__":
    # Asegurarnos de que estamos ejecutando desde la raíz del proyecto
    project_root = Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    main()

