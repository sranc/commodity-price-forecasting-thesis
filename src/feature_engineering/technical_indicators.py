import pandas as pd

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates technical indicators for a given dataframe containing raw metal prices.
    Assumes the dataframe has a 'Close' column.
    """
    df_feat = df.copy()

    # Returns
    df_feat["return"] = df_feat["Close"].pct_change()

    # Moving averages
    df_feat["ma7"] = df_feat["Close"].rolling(7).mean()
    df_feat["ma30"] = df_feat["Close"].rolling(30).mean()

    # Volatility
    df_feat["volatility7"] = df_feat["Close"].rolling(7).std()

    # Momentum
    df_feat["momentum7"] = df_feat["Close"] - df_feat["Close"].shift(7)

    df_feat = df_feat.dropna()

    return df_feat
