#!/usr/bin/env python3
"""Simple CLI tool to fetch current stock price and render a recent ASCII trend."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from typing import Iterable, List, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

YAHOO_CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?"
    "range={days}d&interval=1d&includePrePost=false&events=div%2Csplits"
)
USER_AGENT = "Mozilla/5.0 (compatible; StockTrendBot/1.0; +https://github.com)"

GLYPH_HEIGHT = 7
GLYPH_WIDTH = 5


def _glyph(rows: Sequence[str]) -> Tuple[str, ...]:
    """Normalize glyph rows to a fixed width."""

    normalized = []
    for row in rows:
        normalized.append(row.ljust(GLYPH_WIDTH)[:GLYPH_WIDTH])
    return tuple(normalized)


FONT_5X7 = {
    " ": _glyph([
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
    ]),
    "0": _glyph([
        " ### ",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        " ### ",
    ]),
    "1": _glyph([
        "  #  ",
        " ##  ",
        "# #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "#####",
    ]),
    "2": _glyph([
        " ### ",
        "#   #",
        "    #",
        "   # ",
        "  #  ",
        " #   ",
        "#####",
    ]),
    "3": _glyph([
        " ### ",
        "#   #",
        "    #",
        " ### ",
        "    #",
        "#   #",
        " ### ",
    ]),
    "4": _glyph([
        "   # ",
        "  ## ",
        " # # ",
        "#  # ",
        "#####",
        "   # ",
        "   # ",
    ]),
    "5": _glyph([
        "#####",
        "#    ",
        "#    ",
        "#### ",
        "    #",
        "    #",
        "#### ",
    ]),
    "6": _glyph([
        " ### ",
        "#    ",
        "#    ",
        "#### ",
        "#   #",
        "#   #",
        " ### ",
    ]),
    "7": _glyph([
        "#####",
        "    #",
        "   # ",
        "  #  ",
        " #   ",
        " #   ",
        " #   ",
    ]),
    "8": _glyph([
        " ### ",
        "#   #",
        "#   #",
        " ### ",
        "#   #",
        "#   #",
        " ### ",
    ]),
    "9": _glyph([
        " ### ",
        "#   #",
        "#   #",
        " ####",
        "    #",
        "    #",
        " ### ",
    ]),
    "A": _glyph([
        " ### ",
        "#   #",
        "#   #",
        "#####",
        "#   #",
        "#   #",
        "#   #",
    ]),
    "B": _glyph([
        "#### ",
        "#   #",
        "#   #",
        "#### ",
        "#   #",
        "#   #",
        "#### ",
    ]),
    "C": _glyph([
        " ### ",
        "#   #",
        "#    ",
        "#    ",
        "#    ",
        "#   #",
        " ### ",
    ]),
    "D": _glyph([
        "#### ",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#### ",
    ]),
    "E": _glyph([
        "#####",
        "#    ",
        "#    ",
        "#### ",
        "#    ",
        "#    ",
        "#####",
    ]),
    "F": _glyph([
        "#####",
        "#    ",
        "#    ",
        "#### ",
        "#    ",
        "#    ",
        "#    ",
    ]),
    "G": _glyph([
        " ### ",
        "#   #",
        "#    ",
        "# ###",
        "#   #",
        "#   #",
        " ### ",
    ]),
    "H": _glyph([
        "#   #",
        "#   #",
        "#   #",
        "#####",
        "#   #",
        "#   #",
        "#   #",
    ]),
    "I": _glyph([
        "#####",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "#####",
    ]),
    "J": _glyph([
        "#####",
        "   # ",
        "   # ",
        "   # ",
        "   # ",
        "#  # ",
        " ##  ",
    ]),
    "K": _glyph([
        "#   #",
        "#  # ",
        "# #  ",
        "##   ",
        "# #  ",
        "#  # ",
        "#   #",
    ]),
    "L": _glyph([
        "#    ",
        "#    ",
        "#    ",
        "#    ",
        "#    ",
        "#    ",
        "#####",
    ]),
    "M": _glyph([
        "#   #",
        "## ##",
        "# # #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
    ]),
    "N": _glyph([
        "#   #",
        "##  #",
        "# # #",
        "#  ##",
        "#   #",
        "#   #",
        "#   #",
    ]),
    "O": _glyph([
        " ### ",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        " ### ",
    ]),
    "P": _glyph([
        "#### ",
        "#   #",
        "#   #",
        "#### ",
        "#    ",
        "#    ",
        "#    ",
    ]),
    "Q": _glyph([
        " ### ",
        "#   #",
        "#   #",
        "#   #",
        "# # #",
        "#  # ",
        " ## #",
    ]),
    "R": _glyph([
        "#### ",
        "#   #",
        "#   #",
        "#### ",
        "# #  ",
        "#  # ",
        "#   #",
    ]),
    "S": _glyph([
        " ####",
        "#    ",
        "#    ",
        " ### ",
        "    #",
        "    #",
        "#### ",
    ]),
    "T": _glyph([
        "#####",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
    ]),
    "U": _glyph([
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        " ### ",
    ]),
    "V": _glyph([
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        " # # ",
        "  #  ",
    ]),
    "W": _glyph([
        "#   #",
        "#   #",
        "#   #",
        "# # #",
        "# # #",
        "## ##",
        "#   #",
    ]),
    "X": _glyph([
        "#   #",
        "#   #",
        " # # ",
        "  #  ",
        " # # ",
        "#   #",
        "#   #",
    ]),
    "Y": _glyph([
        "#   #",
        "#   #",
        " # # ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
    ]),
    "Z": _glyph([
        "#####",
        "    #",
        "   # ",
        "  #  ",
        " #   ",
        "#    ",
        "#####",
    ]),
    ".": _glyph([
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
        " ##  ",
        " ##  ",
    ]),
    "-": _glyph([
        "     ",
        "     ",
        "     ",
        "#####",
        "     ",
        "     ",
        "     ",
    ]),
    ":": _glyph([
        "     ",
        " ##  ",
        " ##  ",
        "     ",
        " ##  ",
        " ##  ",
        "     ",
    ]),
    "/": _glyph([
        "    #",
        "    #",
        "   # ",
        "  #  ",
        "  #  ",
        " #   ",
        "#    ",
    ]),
}


def build_message_columns(message: str, height: int) -> List[List[int]]:
    """Convert a text message into dot-matrix columns."""

    if height < GLYPH_HEIGHT:
        raise ValueError("height must be at least glyph height")

    top_padding = (height - GLYPH_HEIGHT) // 2
    bottom_padding = height - GLYPH_HEIGHT - top_padding
    columns: List[List[int]] = []
    blank_column = [0] * height

    for char in message.upper():
        glyph = FONT_5X7.get(char, FONT_5X7[" "])
        for x in range(GLYPH_WIDTH):
            column = [0] * height
            for y in range(GLYPH_HEIGHT):
                if glyph[y][x] != " ":
                    column[top_padding + y] = 1
            columns.append(column)
        columns.append(blank_column[:])

    # add trailing spacing to separate repetitions of the message
    columns.extend(blank_column[:] for _ in range(GLYPH_WIDTH))
    return columns or [blank_column[:]]


class DotMatrixTicker:
    """Simple Tkinter-based dot matrix ticker display."""

    def __init__(
        self,
        root,
        messages: Sequence[str],
        width: int = 64,
        height: int = 32,
        pixel_size: int = 8,
        delay_seconds: float = 0.05,
    ) -> None:
        import tkinter as tk

        self.root = root
        self.width = width
        self.height = height
        self.pixel_size = pixel_size
        self.interval_ms = max(10, int(delay_seconds * 1000))
        self.on_color = "#39ff14"
        self.off_color = "#041f04"

        self.canvas = tk.Canvas(
            root,
            width=width * pixel_size,
            height=height * pixel_size,
            bg="black",
            highlightthickness=0,
        )
        self.canvas.pack()

        message_text = "   ".join(messages).strip()
        if not message_text:
            message_text = "NO DATA"

        self.columns = build_message_columns(message_text + "   ", height)
        if len(self.columns) < width:
            padding = width - len(self.columns)
            blank_column = [0] * height
            self.columns.extend([blank_column[:] for _ in range(padding)])

        self.pixels = [
            [
                self.canvas.create_rectangle(
                    x * pixel_size,
                    y * pixel_size,
                    (x + 1) * pixel_size,
                    (y + 1) * pixel_size,
                    outline="",
                    fill=self.off_color,
                )
                for x in range(width)
            ]
            for y in range(height)
        ]

        self.offset = 0
        self._schedule_next_frame()

    def _schedule_next_frame(self) -> None:
        if not self.columns:
            return
        self._draw_frame()
        self.root.after(self.interval_ms, self._schedule_next_frame)

    def _draw_frame(self) -> None:
        column_count = len(self.columns)
        start = self.offset
        for x in range(self.width):
            column = self.columns[(start + x) % column_count]
            for y in range(self.height):
                fill = self.on_color if column[y] else self.off_color
                self.canvas.itemconfigure(self.pixels[y][x], fill=fill)
        self.offset = (self.offset + 1) % column_count


def launch_ticker_window(
    messages: Sequence[str],
    *,
    width: int = 64,
    height: int = 32,
    pixel_size: int = 8,
    delay_seconds: float = 0.05,
) -> int:
    """Launch the Tkinter ticker window and block until it closes."""

    try:
        import tkinter as tk
    except ImportError:
        print("Error: tkinter is not available on this system; cannot launch ticker.", file=sys.stderr)
        return 1

    try:
        root = tk.Tk()
    except Exception as exc:  # pragma: no cover - environment-specific GUI setup
        print(
            "Error: unable to start Tkinter window (" + str(exc) + ").",
            file=sys.stderr,
        )
        return 1

    root.title("Stock Trend Ticker")

    DotMatrixTicker(
        root,
        messages,
        width=width,
        height=height,
        pixel_size=pixel_size,
        delay_seconds=delay_seconds,
    )

    try:
        root.mainloop()
    except KeyboardInterrupt:  # pragma: no cover - interactive utility
        root.destroy()
    return 0


class StockLookupError(RuntimeError):
    """Raised when stock data cannot be retrieved."""


def fetch_chart_payload(symbol: str, days: int) -> dict:
    """Fetch chart data for the symbol from Yahoo Finance."""

    if days < 1:
        raise ValueError("days must be a positive integer")

    request = Request(YAHOO_CHART_URL.format(symbol=symbol, days=days))
    request.add_header("User-Agent", USER_AGENT)

    try:
        with urlopen(request, timeout=10) as response:
            payload = response.read()
    except HTTPError as exc:  # pragma: no cover - simple CLI utility
        raise StockLookupError(f"HTTP error {exc.code} when fetching {symbol!r}.") from exc
    except URLError as exc:  # pragma: no cover
        raise StockLookupError(f"Unable to reach data provider: {exc.reason}.") from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise StockLookupError("Received invalid JSON data.") from exc


def extract_price_points(payload: dict) -> Tuple[str, float, str, List[Tuple[dt.date, float]]]:
    """Extract meta information and daily close points from payload."""

    chart = payload.get("chart", {})
    errors = chart.get("error")
    if errors:
        message = errors.get("code", "unknown error")
        raise StockLookupError(f"Data provider error: {message}.")

    results = chart.get("result") or []
    if not results:
        raise StockLookupError("No data returned for the given symbol.")

    result = results[0]
    meta = result.get("meta", {})
    symbol = meta.get("symbol", "Unknown")
    currency = meta.get("currency", "USD")
    current_price = meta.get("regularMarketPrice")

    timestamps = result.get("timestamp") or []
    quotes = result.get("indicators", {}).get("quote", [])
    closes: Iterable[float | None] = quotes[0].get("close", []) if quotes else []

    points: List[Tuple[dt.date, float]] = []
    for raw_ts, price in zip(timestamps, closes):
        if price is None:
            continue
        date = dt.datetime.fromtimestamp(raw_ts).date()
        points.append((date, float(price)))

    if not points:
        raise StockLookupError("No valid closing prices in the requested range.")

    if current_price is None:
        current_price = points[-1][1]

    return symbol, float(current_price), currency, points


def render_ascii_chart(points: List[Tuple[dt.date, float]], width: int = 32) -> str:
    """Render a simple horizontal ASCII bar chart for the price points."""

    prices = [price for _, price in points]
    low = min(prices)
    high = max(prices)
    span = high - low

    if span == 0:
        span = 1

    bars = []
    for date, price in points:
        normalized = (price - low) / span
        bar_len = max(1, round(normalized * width))
        bars.append(f"{date.isoformat()} | {price:8.2f} | {'#' * bar_len}")

    return "\n".join(bars)


def render_ascii_bar_chart(points: List[Tuple[dt.date, float]], height: int = 10) -> str:
    """Render a vertical ASCII bar chart for the price points."""

    prices = [price for _, price in points]
    low = min(prices)
    high = max(prices)
    span = high - low

    if span == 0:
        span = 1

    heights = [max(1, round(((price - low) / span) * height)) for price in prices]
    grid = []
    for level in range(height, 0, -1):
        row_cells = ["#" if bar_height >= level else " " for bar_height in heights]
        grid.append(" ".join(row_cells))

    axis = "-" * (len(points) * 2 - 1)
    date_labels = " ".join(date.strftime("%m-%d") for date, _ in points)

    sections = [
        f"High: {high:.2f}",
        "\n".join(grid),
        axis,
        date_labels,
        f"Low : {low:.2f}",
    ]

    return "\n".join(sections)


def format_summary(symbol: str, price: float, currency: str) -> str:
    return f"Current price for {symbol}: {price:.2f} {currency}"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch the current stock price, display ASCII charts, and optionally launch a dot-matrix ticker.",
    )
    parser.add_argument(
        "symbols",
        metavar="SYMBOL",
        nargs="+",
        help="Ticker symbol(s), e.g. AAPL MSFT TSLA",
    )
    parser.add_argument(
        "-d",
        "--days",
        metavar="N",
        type=int,
        default=5,
        help="Number of days of history to fetch (default: 5)",
    )
    parser.add_argument(
        "--chart",
        choices=("rows", "bars"),
        default="rows",
        help=(
            "ASCII chart style: 'rows' for horizontal bars, 'bars' for vertical bar chart"
        ),
    )
    parser.add_argument(
        "--ticker",
        action="store_true",
        help="Launch a 32x64 dot-matrix GUI ticker that scrolls requested stocks and prices.",
    )
    parser.add_argument(
        "--ticker-speed",
        metavar="SECONDS",
        type=float,
        default=0.05,
        help="Scroll speed in seconds per column shift for the ticker (default: 0.05).",
    )

    args = parser.parse_args(argv)
    symbols = [entry.upper().strip() for entry in args.symbols]
    days = args.days

    summaries = []
    first_points: List[Tuple[dt.date, float]] | None = None
    first_chart_symbol: str | None = None

    try:
        for index, symbol_input in enumerate(symbols):
            payload = fetch_chart_payload(symbol_input, days)
            symbol, price, currency, points = extract_price_points(payload)
            summaries.append({
                "symbol": symbol,
                "price": price,
                "currency": currency,
                "points": points,
            })
            if index == 0:
                first_points = points
                first_chart_symbol = symbol
    except StockLookupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for info in summaries:
        print(format_summary(info["symbol"], info["price"], info["currency"]))

    if first_points and first_chart_symbol:
        renderers = {
            "rows": render_ascii_chart,
            "bars": render_ascii_bar_chart,
        }
        renderer = renderers[args.chart]

        print(f"\n{days}-day trend ({args.chart}) for {first_chart_symbol}:")
        print(renderer(first_points))

    if args.ticker:
        ticker_messages = [
            f"{info['symbol']} {info['price']:.2f} {info['currency']}"
            for info in summaries
        ]
        result = launch_ticker_window(
            ticker_messages,
            delay_seconds=max(0.01, args.ticker_speed),
        )
        if result != 0:
            return result

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
