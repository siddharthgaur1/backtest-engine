from __future__ import annotations

from backtest_engine.events import Direction, FillEvent, OrderEvent, OrderType, SignalEvent


class Portfolio:
    """Converts signals into sized orders (fixed-fraction sizing), and tracks
    cash/positions/equity as fills come back from the broker.
    """

    def __init__(self, data_handler, initial_capital: float, risk_pct: float = 0.1):
        self.data_handler = data_handler
        self.cash = initial_capital
        self.initial_capital = initial_capital
        self.risk_pct = risk_pct  # fraction of equity risked per new position
        self.positions: dict[str, int] = {}
        self.equity_curve: list[tuple] = []  # (date, equity)
        self.trades: list[dict] = []

    def current_equity(self) -> float:
        equity = self.cash
        for symbol, qty in self.positions.items():
            bar = self.data_handler.current_bar(symbol)
            if bar and qty:
                equity += qty * bar["close"]
        return equity

    def on_signal(self, signal: SignalEvent) -> OrderEvent | None:
        bar = self.data_handler.current_bar(signal.symbol)
        if bar is None:
            return None
        held = self.positions.get(signal.symbol, 0)

        if signal.direction == Direction.FLAT:
            if held == 0:
                return None
            direction = Direction.SHORT if held > 0 else Direction.LONG
            return OrderEvent(signal.symbol, direction, abs(held), OrderType.MARKET)

        if signal.direction == Direction.LONG and held > 0:
            return None
        if signal.direction == Direction.SHORT and held < 0:
            return None

        equity = self.current_equity()
        budget = equity * self.risk_pct
        qty = max(int(budget // bar["close"]), 0)
        if qty == 0:
            return None

        # flip an opposing position first, then open the new one, in one order
        qty += abs(held)
        return OrderEvent(signal.symbol, signal.direction, qty, OrderType.MARKET)

    def on_fill(self, fill: FillEvent) -> None:
        signed_qty = fill.quantity if fill.direction == Direction.LONG else -fill.quantity
        self.cash -= signed_qty * fill.fill_price
        self.cash -= fill.commission
        self.positions[fill.symbol] = self.positions.get(fill.symbol, 0) + signed_qty
        self.trades.append(
            {
                "date": self.data_handler.current_date(),
                "symbol": fill.symbol,
                "direction": fill.direction.name,
                "quantity": fill.quantity,
                "price": fill.fill_price,
                "commission": fill.commission,
            }
        )

    def mark_to_market(self) -> None:
        self.equity_curve.append((self.data_handler.current_date(), self.current_equity()))
