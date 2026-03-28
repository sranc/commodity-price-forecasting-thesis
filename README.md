# Commodity Price Forecasting Thesis

## Overview

This project aims to forecast the prices of four major commodities (Gold, Silver, Copper, Zinc) using a hybrid approach of statistical models (ARIMA/GARCH) and deep learning (LSTM).

## Structure

- `data/`: Data lake (Raw -> Processed). **DO NOT EDIT RAW DATA.**
- `src/`: Source code for ingestion, processing, and modeling.
- `notebooks/`: Exploratory analysis and prototyping.
- `reports/`: Quarto-based thesis documents.
- `config/`: Configuration files for reproducibility and scalability.

## Quick Start

1. Install Python dependencies: `pip install -r requirements.txt`
2. (Optional) Restore R environment: `renv::restore()`
3. Check `config/metals.yaml` for target commodities.
4. Run data ingestion: `python src/data_ingestion/api_fetch.py` (Example)

## Tech Stack

- **Python**: Deep Learning (TensorFlow/PyTorch), Data Engineering.
- **R**: Statistical Modeling (forecast, rugarch), Reporting (Quarto).
