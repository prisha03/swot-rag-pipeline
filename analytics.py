# src/analytics.py

import numpy as np
import pandas as pd
from itertools import combinations
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error, mean_absolute_error


def compute_correlations(
    df: pd.DataFrame,
    return_col: str,
    features: list[str]
) -> pd.Series:
    """
    Compute Pearson correlation between each feature and the return column.
    """
    corr = df[features + [return_col]].corr().loc[features, return_col]
    return corr


def granger_tests(
    df: pd.DataFrame,
    return_col: str,
    features: list[str],
    maxlag: int = 4
) -> dict:
    """
    Run Granger-causality tests for each feature → return_col.
    Returns a dict of feature → {lag: p-value}.
    """
    results = {}
    for feat in features:
        data = df[[return_col, feat]].dropna()
        test = grangercausalitytests(data, maxlag=maxlag, verbose=False)
        pvals = {lag: test[lag][0]['ssr_ftest'][1] for lag in range(1, maxlag+1)}
        results[feat] = pvals
    return results


def fit_arimax(
    y: pd.Series,
    exog: pd.DataFrame,
    order: tuple[int,int,int] = (1,1,1)
) -> SARIMAX:
    """
    Fit an ARIMAX model and return the fitted results.
    """
    model = SARIMAX(y, exog=exog, order=order)
    return model.fit(disp=False)


def forecast_arimax(
    res,
    last_exog: pd.Series,
    steps: int = 4
) -> pd.Series:
    """
    Forecast `steps` ahead by repeating the last exog row.
    """
    tiled = np.tile(last_exog.values, (steps, 1))
    future_index = pd.date_range(
        start=last_exog.name + pd.offsets.QuarterEnd(),
        periods=steps,
        freq='Q'
    )
    future = pd.DataFrame(
        tiled,
        columns=last_exog.index,
        index=future_index
    )
    return res.get_forecast(steps=steps, exog=future).predicted_mean


def evaluate_forecasts(
    true: pd.Series,
    preds: dict[str, pd.Series]
) -> pd.DataFrame:
    """
    Compute RMSE and MAE for multiple forecasts.
    preds: dict of {name: forecast_series}.
    Returns a DataFrame indexed by forecast name.
    """
    metrics = {}
    for name, pred in preds.items():
        y_true, y_pred = true.align(pred, join='inner')
        metrics[name] = {
            'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
            'MAE':  mean_absolute_error(y_true, y_pred)
        }
    return pd.DataFrame(metrics).T


def select_exog_by_aic(
    y: pd.Series,
    candidates: pd.DataFrame,
    order: tuple[int,int,int] = (1,1,1)
) -> tuple[list[str], object]:
    """
    Forward‐select exogenous features to minimize AIC in a SARIMAX(p,d,q) model.

    Returns:
      - selected: list of feature names
      - best_model: the fitted SARIMAXResults
    """
    remaining = list(candidates.columns)
    selected = []
    current_aic = np.inf
    best_model = None

    while remaining:
        trials = []
        for feat in remaining:
            try_feats = selected + [feat]
            exog_try = candidates[try_feats].shift(1).dropna()
            y_aligned, exog_aligned = y.align(exog_try, join='inner')
            model = SARIMAX(y_aligned, exog=exog_aligned, order=order)
            res = model.fit(disp=False)
            trials.append((res.aic, feat, res))
        # choose best
        trials.sort(key=lambda x: x[0])
        best_aic, best_feat, best_res = trials[0]
        if best_aic < current_aic:
            current_aic = best_aic
            selected.append(best_feat)
            best_model = best_res
            remaining.remove(best_feat)
            print(f"Added exog '{best_feat}' with AIC={best_aic:.1f}")
        else:
            break

    return selected, best_model

