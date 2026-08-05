"""Regenerate docs/demo.svg from the bundled example's real output.

Runs the documented command and records exactly what it printed, so the README
image cannot drift from the numbers in the Results section:

    python examples/render_demo_svg.py
"""

from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

from rich.console import Console

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "demo.svg"
CMD = [sys.executable, "examples/momentum_vs_buyhold.py"]


def main() -> None:
    proc = subprocess.run(CMD, cwd=REPO, capture_output=True, text=True,
                          timeout=600, check=True)

    console = Console(record=True, width=104, file=io.StringIO(), force_terminal=True)
    console.print("[bold green]$[/] [bold]python examples/momentum_vs_buyhold.py[/]")
    console.print()

    for line in proc.stdout.strip().splitlines():
        # np.float64(...) is real repr noise from the metrics dict; strip it so
        # the image reads as numbers rather than as numpy internals.
        clean = re.sub(r"np\.float64\(([-\d.]+)\)", r"\1", line)
        if clean.startswith("Momentum:"):
            console.print(f"[cyan]{clean}[/]")
        elif clean.startswith("Buy & Hold:"):
            console.print(f"[magenta]{clean}[/]")
        elif "beat" in clean:
            console.print(f"[bold green]{clean}[/]")
        else:
            console.print(clean)

    console.print()
    console.print("[dim]# synthetic seeded data, after Indian transaction costs "
                  "(STT, brokerage, stamp duty)[/]")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    console.save_svg(str(OUT), title="backtest-engine")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
