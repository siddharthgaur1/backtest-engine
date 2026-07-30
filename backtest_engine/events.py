from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Direction(Enum):
    LONG = auto()
    SHORT = auto()
    FLAT = auto()


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()


@dataclass
class MarketEvent:
    symbol: str
    bar: dict  # {"date", "open", "high", "low", "close", "volume"}


@dataclass
class SignalEvent:
    symbol: str
    direction: Direction
    strength: float = 1.0


@dataclass
class OrderEvent:
    symbol: str
    direction: Direction
    quantity: int
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = None


@dataclass
class FillEvent:
    symbol: str
    direction: Direction
    quantity: int
    fill_price: float
    commission: float
