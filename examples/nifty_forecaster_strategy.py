"""Wires trained nifty-forecaster models into MLSignalStrategy.

Thin adapter only — reuses nifty-forecaster's own feature engineering and
saved model artifacts rather than reimplementing them. Requires the
nifty-forecaster repo checked out as a sibling directory (or on PYTHONPATH)
and a trained model artifact under models/artifacts/.
"""
import sys
from pathlib import Path

NIFTY_FORECASTER_PATH = Path(__file__).resolve().parents[2] / "nifty-forecaster"
sys.path.insert(0, str(NIFTY_FORECASTER_PATH))

from features.engineer import engineer_features  # noqa: E402
from models.ensemble import EnsembleModel  # noqa: E402

from backtest_engine import Backtest, MLSignalStrategy  # noqa: E402


def load_model(ticker: str) -> EnsembleModel:
    artifact = NIFTY_FORECASTER_PATH / "models" / "artifacts" / f"{ticker.replace('.', '_')}.joblib"
    return EnsembleModel.load(artifact)  # ponytail: assumes EnsembleModel exposes .load(); adjust if not


def feature_builder(bars_df):
    """bars_df -> the exact feature row nifty-forecaster's model expects.

    nifty-forecaster's engineer_features works on its own merged OHLCV+
    fundamentals frame, not a bare price window — plug in the equivalent
    transform here once you have a specific ticker's artifact to test against.
    """
    feats = engineer_features(bars_df.rename(columns=str.title))
    return feats.tail(1)


def run(ticker: str = "RELIANCE.NS"):
    import yfinance as yf

    df = yf.download(ticker, start="2022-01-01", auto_adjust=True)
    df.columns = [c.lower() for c in df.columns]
    model = load_model(ticker)

    bt = Backtest(
        bars={ticker: df},
        strategy_cls=MLSignalStrategy,
        strategy_kwargs={"model": model, "feature_builder": feature_builder},
    )
    result = bt.run()
    print(result["metrics"])


if __name__ == "__main__":
    run()
