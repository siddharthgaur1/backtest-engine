# backtest-engine

Event-driven backtester for ML trading signals. Every bar is processed
sequentially, as if time is moving forward — no vectorized shortcut can leak
future data into a decision.

## Why event-driven, not vectorized

A vectorized backtest (`signal.shift(1) * returns`) is fast but easy to get
subtly wrong: a rolling feature computed with `center=True`, or a shift
applied to the wrong column, silently leaks the future into a signal. The
event loop here makes that class of bug structurally impossible: a strategy
only ever sees `data.get_latest_bars(symbol, n)`, which is hard-truncated at
the current bar, and every order fills at the **next** bar's open — never the
current bar's close. See `tests/test_no_lookahead.py::test_fill_happens_at_next_bar_open_not_current_close`.

## Quickstart

```python
from backtest_engine import Backtest, MomentumStrategy

bt = Backtest(bars={"RELIANCE.NS": ohlcv_df}, strategy_cls=MomentumStrategy,
              strategy_kwargs={"lookback": 20}, initial_capital=1_000_000)
result = bt.run()
result["metrics"]   # {"sharpe": ..., "cagr": ..., "max_drawdown": ..., ...}
result["trades"]    # list of fills
```

Or run the bundled synthetic example (no network needed):

```
python examples/momentum_vs_buyhold.py
```

Sample output on synthetic data (seeded, reproducible):

```
Momentum:   {'total_return': -0.0224, 'sharpe': -5.096, 'max_drawdown': -0.0263, 'num_trades': 46, ...}
Buy & Hold: {'total_return': -0.0555, 'sharpe': -5.936, 'max_drawdown': -0.0556, 'num_trades': 1, ...}
Momentum beat buy-and-hold after costs.
```
Whether a strategy beats buy-and-hold is printed either way — the honest
result on this seed, not a cherry-picked one.

## Indian market transaction costs (`backtest_engine/broker.py`)

| Charge | Rate | Side |
|---|---|---|
| Brokerage | 0.03% | both |
| STT | 0.1% | sell |
| Stamp duty | 0.015% | buy |

Approximate flat rates modeled on Zerodha equity delivery — not tick-accurate
(no per-order caps, no GST on brokerage). Good enough to see whether a
strategy survives costs at all; refine if you need exact P&L.

## nifty-forecaster integration

`examples/nifty_forecaster_strategy.py` wires `MLSignalStrategy` to a trained
nifty-forecaster `EnsembleModel` via `predict_proba`, reusing
nifty-forecaster's own `engineer_features`. This is a thin adapter, not a
verified run — `feature_builder` needs the real merged OHLCV+fundamentals
frame nifty-forecaster trains on, and `EnsembleModel.load()` needs a matching
artifact under `models/artifacts/`. Wire it up when you have a specific
ticker's trained artifact to test against.

## Results

The synthetic quickstart output above (momentum vs buy-and-hold, seeded and
reproducible via `python examples/momentum_vs_buyhold.py`) is the only
measured result in this repo. There is no real-market benchmark yet — see
Limitations.

## Limitations

Built: event loop (`MarketEvent`→`SignalEvent`→`OrderEvent`→`FillEvent`),
`HistoricalDataHandler`, `SimulatedBroker` (next-bar-open fills, Indian
costs), `Portfolio` (fixed-fraction sizing), `MomentumStrategy` +
`MLSignalStrategy`, core metrics (Sharpe/Sortino/CAGR/max drawdown/Calmar),
no-lookahead tests.

What's not here — add if actually needed:
- Mean-reversion / pairs-trading strategies, position-sizing variants (ATR, Kelly)
- Walk-forward optimization, Monte Carlo resampling, parameter grid search
- HTML tearsheet, CLI, multi-page report — `result["metrics"]`/`result["trades"]` cover the numbers today
- Partial fills, short-selling borrow costs, concentration/correlation risk checks
- Win rate / profit factor (needs matched entry-exit trade pairing, not just a fill log)
