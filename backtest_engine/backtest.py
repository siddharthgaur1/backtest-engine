from __future__ import annotations

from backtest_engine.analytics import compute_metrics
from backtest_engine.broker import SimulatedBroker
from backtest_engine.data import HistoricalDataHandler
from backtest_engine.portfolio import Portfolio


class Backtest:
    def __init__(self, bars: dict, strategy_cls, strategy_kwargs: dict | None = None,
                 initial_capital: float = 1_000_000, risk_pct: float = 0.1):
        self.data = HistoricalDataHandler(bars)
        self.strategy = strategy_cls(self.data, **(strategy_kwargs or {}))
        self.portfolio = Portfolio(self.data, initial_capital, risk_pct)
        self.broker = SimulatedBroker(self.data)

    def run(self) -> dict:
        while self.data.next_bar_exists():
            self.data.advance()

            for symbol in self.data.symbols:
                if self.data.current_bar(symbol) is None:
                    continue
                self.strategy.on_market(symbol)

            for sig in self.strategy.pending_signals:
                order = self.portfolio.on_signal(sig)
                if order is None:
                    continue
                fill = self.broker.execute_order(order)
                if fill is not None:
                    self.portfolio.on_fill(fill)
            self.strategy.pending_signals.clear()

            self.portfolio.mark_to_market()

        metrics = compute_metrics(self.portfolio.equity_curve, self.portfolio.trades, self.portfolio.initial_capital)
        return {
            "metrics": metrics,
            "equity_curve": self.portfolio.equity_curve,
            "trades": self.portfolio.trades,
        }
