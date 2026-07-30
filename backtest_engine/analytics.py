from __future__ import annotations

import math

import pandas as pd

RISK_FREE_ANNUAL = 0.065  # India ~6.5%
TRADING_DAYS = 252


def compute_metrics(equity_curve: list[tuple], trades: list[dict], initial_capital: float) -> dict:
    if len(equity_curve) < 2:
        return {"error": "not enough data to compute metrics"}

    dates, equity = zip(*equity_curve)
    series = pd.Series(equity, index=pd.to_datetime(list(dates)))
    returns = series.pct_change().dropna()

    total_return = series.iloc[-1] / initial_capital - 1
    years = max((series.index[-1] - series.index[0]).days / 365.25, 1e-9)
    cagr = (series.iloc[-1] / initial_capital) ** (1 / years) - 1

    daily_rf = (1 + RISK_FREE_ANNUAL) ** (1 / TRADING_DAYS) - 1
    excess = returns - daily_rf
    sharpe = (excess.mean() / excess.std() * math.sqrt(TRADING_DAYS)) if excess.std() > 0 else 0.0

    downside = excess[excess < 0]
    sortino = (excess.mean() / downside.std() * math.sqrt(TRADING_DAYS)) if len(downside) and downside.std() > 0 else 0.0

    running_max = series.cummax()
    drawdown = series / running_max - 1
    max_drawdown = drawdown.min()
    calmar = cagr / abs(max_drawdown) if max_drawdown < 0 else 0.0

    return {
        "total_return": round(total_return, 4),
        "cagr": round(cagr, 4),
        "sharpe": round(sharpe, 3),
        "sortino": round(sortino, 3),
        "max_drawdown": round(max_drawdown, 4),
        "calmar": round(calmar, 3),
        "num_trades": len(trades),
        "final_equity": round(series.iloc[-1], 2),
    }
