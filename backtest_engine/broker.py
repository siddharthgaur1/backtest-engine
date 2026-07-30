from __future__ import annotations

from backtest_engine.events import Direction, FillEvent, OrderEvent, OrderType

# ponytail: flat approximate rates modeled on Zerodha equity delivery; not tick-accurate
BROKERAGE_PCT = 0.0003       # 0.03% per trade
STT_SELL_PCT = 0.001         # 0.1% on sell side (equity delivery)
STAMP_DUTY_BUY_PCT = 0.00015  # 0.015% on buy side
SEBI_CHARGES_PCT = 0.0000001  # negligible but included for completeness


class SimulatedBroker:
    """Fills market orders at the NEXT bar's open — never the current bar's
    close — so a strategy can never trade on information it couldn't have had.
    """

    def __init__(self, data_handler):
        self.data_handler = data_handler

    def execute_order(self, order: OrderEvent) -> FillEvent | None:
        next_bar = self.data_handler.peek_next_bar(order.symbol)
        if next_bar is None:
            return None  # no future bar to fill against (end of data)

        if order.order_type == OrderType.MARKET:
            fill_price = next_bar["open"]
        else:  # LIMIT: fill only if next bar's range touches the limit
            if order.direction == Direction.LONG and next_bar["low"] > order.limit_price:
                return None
            if order.direction == Direction.SHORT and next_bar["high"] < order.limit_price:
                return None
            fill_price = order.limit_price

        gross = fill_price * order.quantity
        commission = gross * (BROKERAGE_PCT + SEBI_CHARGES_PCT)
        if order.direction == Direction.LONG:
            commission += gross * STAMP_DUTY_BUY_PCT
        else:
            commission += gross * STT_SELL_PCT

        return FillEvent(
            symbol=order.symbol,
            direction=order.direction,
            quantity=order.quantity,
            fill_price=fill_price,
            commission=commission,
        )
