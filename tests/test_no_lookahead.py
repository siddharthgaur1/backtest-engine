"""Minimal assert-based self-checks (no framework, no fixtures)."""
import pandas as pd

from backtest_engine import Backtest, Direction, Strategy


def make_bars(closes: list[float]) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=len(closes), freq="D")
    return pd.DataFrame(
        {"open": closes, "high": [c * 1.01 for c in closes],
         "low": [c * 0.99 for c in closes], "close": closes,
         "volume": [1_000_000] * len(closes)},
        index=dates,
    )


class BuyOnFirstBar(Strategy):
    """Fires exactly one LONG signal on the first bar it sees."""

    def __init__(self, data_handler):
        super().__init__(data_handler)
        self.fired = False

    def on_market(self, symbol: str) -> None:
        if not self.fired:
            self.fired = True
            self.signal(symbol, Direction.LONG)


def test_fill_happens_at_next_bar_open_not_current_close():
    # bar0 close=100 (very different from bar1 open=200): if the fill used
    # the CURRENT bar's close, fill price would be 100, not 200.
    closes = [100, 200, 200, 200, 200]
    bt = Backtest({"TEST": make_bars(closes)}, BuyOnFirstBar, initial_capital=1_000_000, risk_pct=0.5)
    result = bt.run()

    trades = result["trades"]
    assert len(trades) == 1, trades
    fill_price = trades[0]["price"]
    assert fill_price == 200, f"expected fill at next bar's open (200), got {fill_price}"


def test_no_fill_on_last_bar_no_future_data():
    class BuyOnLastBar(Strategy):
        def on_market(self, symbol: str) -> None:
            bars = self.data.get_latest_bars(symbol, 1)
            if len(bars) == 1 and bars.index[0] == self.data.dates[-1]:
                self.signal(symbol, Direction.LONG)

    bt = Backtest({"TEST": make_bars([100, 101, 102])}, BuyOnLastBar)
    result = bt.run()
    assert len(result["trades"]) == 0, "no future bar exists to fill against on the last bar"


def test_metrics_present_after_run():
    bt = Backtest({"TEST": make_bars([100, 102, 101, 105, 110, 108, 112])}, BuyOnFirstBar)
    result = bt.run()
    assert "sharpe" in result["metrics"]
    assert "max_drawdown" in result["metrics"]


if __name__ == "__main__":
    test_fill_happens_at_next_bar_open_not_current_close()
    test_no_fill_on_last_bar_no_future_data()
    test_metrics_present_after_run()
    print("all tests passed")
