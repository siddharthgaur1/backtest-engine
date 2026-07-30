"""Runs on synthetic data (no network) so it's reproducible without a data
source. Swap `make_synthetic_bars` for a yfinance download to backtest a
real ticker.
"""
import numpy as np
import pandas as pd

from backtest_engine import Backtest, Direction, MomentumStrategy, Strategy


def make_synthetic_bars(n: int = 500, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0004, 0.015, n)  # slight upward drift, ~24% annualized vol
    close = 1000 * np.cumprod(1 + returns)
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {"open": close * (1 + rng.normal(0, 0.001, n)), "high": close * 1.005,
         "low": close * 0.995, "close": close, "volume": rng.integers(1e6, 5e6, n)},
        index=dates,
    )


class BuyAndHold(Strategy):
    def __init__(self, data_handler):
        super().__init__(data_handler)
        self.bought = False

    def on_market(self, symbol: str) -> None:
        if not self.bought:
            self.bought = True
            self.signal(symbol, Direction.LONG)


if __name__ == "__main__":
    bars = make_synthetic_bars()

    momentum = Backtest({"SYN": bars}, MomentumStrategy, {"lookback": 20}).run()
    buyhold = Backtest({"SYN": bars}, BuyAndHold).run()

    print("Momentum:", momentum["metrics"])
    print("Buy & Hold:", buyhold["metrics"])
    beat = momentum["metrics"]["total_return"] > buyhold["metrics"]["total_return"]
    print(f"Momentum {'beat' if beat else 'did NOT beat'} buy-and-hold after costs.")
