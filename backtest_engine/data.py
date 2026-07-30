from __future__ import annotations

import pandas as pd


class HistoricalDataHandler:
    """Delivers bars strictly in time order. A strategy can only see bars up to
    (and including) the current pointer via get_latest_bars — never the future.
    The broker is the only caller allowed to peek at next_bar, to fill orders
    at the next bar's open (no-lookahead).
    """

    def __init__(self, bars: dict[str, pd.DataFrame]):
        # each df indexed by date, columns: open, high, low, close, volume
        self.symbols = list(bars.keys())
        self.bars = bars
        self.dates = sorted(set().union(*(df.index for df in bars.values())))
        self.pointer = -1

    def next_bar_exists(self) -> bool:
        return self.pointer + 1 < len(self.dates)

    def advance(self) -> None:
        self.pointer += 1

    def current_date(self):
        return self.dates[self.pointer]

    def current_bar(self, symbol: str) -> dict | None:
        date = self.current_date()
        if date not in self.bars[symbol].index:
            return None
        row = self.bars[symbol].loc[date]
        return {"date": date, **row.to_dict()}

    def peek_next_bar(self, symbol: str) -> dict | None:
        """Only the broker may call this, to fill at next bar's open."""
        nxt = self.pointer + 1
        if nxt >= len(self.dates):
            return None
        date = self.dates[nxt]
        if date not in self.bars[symbol].index:
            return None
        row = self.bars[symbol].loc[date]
        return {"date": date, **row.to_dict()}

    def get_latest_bars(self, symbol: str, n: int) -> pd.DataFrame:
        upto = self.current_date()
        df = self.bars[symbol]
        return df[df.index <= upto].tail(n)
