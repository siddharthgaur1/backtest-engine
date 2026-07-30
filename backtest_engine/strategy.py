from __future__ import annotations

from backtest_engine.events import Direction, SignalEvent


class Strategy:
    """Subclass and implement on_market. Only self.data.get_latest_bars(...)
    is available — there is no way to reach a future bar from here.
    """

    def __init__(self, data_handler):
        self.data = data_handler
        self.pending_signals: list[SignalEvent] = []

    def on_market(self, symbol: str) -> None:
        raise NotImplementedError

    def signal(self, symbol: str, direction: Direction, strength: float = 1.0) -> None:
        self.pending_signals.append(SignalEvent(symbol, direction, strength))


class MomentumStrategy(Strategy):
    """Buy top performers over `lookback` bars, go flat on bottom performers."""

    def __init__(self, data_handler, lookback: int = 20, threshold: float = 0.0):
        super().__init__(data_handler)
        self.lookback = lookback
        self.threshold = threshold

    def on_market(self, symbol: str) -> None:
        bars = self.data.get_latest_bars(symbol, self.lookback + 1)
        if len(bars) < self.lookback + 1:
            return
        momentum = bars["close"].iloc[-1] / bars["close"].iloc[0] - 1
        if momentum > self.threshold:
            self.signal(symbol, Direction.LONG)
        elif momentum < -self.threshold:
            self.signal(symbol, Direction.FLAT)


class MLSignalStrategy(Strategy):
    """Plugs in any model exposing predict_proba(features) -> [[p_down, p_up]].

    feature_builder(bars_df) -> feature row (whatever shape the model expects).
    """

    def __init__(self, data_handler, model, feature_builder, lookback: int = 30, threshold: float = 0.6):
        super().__init__(data_handler)
        self.model = model
        self.feature_builder = feature_builder
        self.lookback = lookback
        self.threshold = threshold

    def on_market(self, symbol: str) -> None:
        bars = self.data.get_latest_bars(symbol, self.lookback)
        if len(bars) < self.lookback:
            return
        features = self.feature_builder(bars)
        proba = self.model.predict_proba(features)[0]
        if proba[1] > self.threshold:
            self.signal(symbol, Direction.LONG, strength=proba[1])
        elif proba[0] > self.threshold:
            self.signal(symbol, Direction.FLAT, strength=proba[0])
