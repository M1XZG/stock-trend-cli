#!/usr/bin/env python3
"""Simple CLI tool to fetch current stock price and render a recent ASCII trend."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
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

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_CYAN = "\033[96m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"


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


def render_ascii_chart(points: List[Tuple[dt.date, float]], width: int = 32, use_color: bool = False) -> str:
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
        bar_color = (COLOR_GREEN if price >= (low + span / 2) else COLOR_RED) if use_color else ""
        reset = COLOR_RESET if use_color else ""
        bars.append(f"{date.isoformat()} | {price:8.2f} | {bar_color}{'#' * bar_len}{reset}")

    return "\n".join(bars)


def render_ascii_bar_chart(points: List[Tuple[dt.date, float]], height: int = 10, use_color: bool = False) -> str:
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
        row_cells = []
        for i, bar_height in enumerate(heights):
            if bar_height >= level:
                bar_color = (COLOR_GREEN if prices[i] >= (low + span / 2) else COLOR_RED) if use_color else ""
                reset = COLOR_RESET if use_color else ""
                row_cells.append(f"{bar_color}#{reset}")
            else:
                row_cells.append(" ")
        grid.append(" ".join(row_cells))

    axis = "-" * (len(points) * 2 - 1)
    date_labels = " ".join(date.strftime("%m-%d") for date, _ in points)

    high_color = COLOR_CYAN if use_color else ""
    low_color = COLOR_CYAN if use_color else ""
    reset = COLOR_RESET if use_color else ""

    sections = [
        f"{high_color}High: {high:.2f}{reset}",
        "\n".join(grid),
        axis,
        date_labels,
        f"{low_color}Low : {low:.2f}{reset}",
    ]

    return "\n".join(sections)


def format_summary(symbol: str, price: float, currency: str, use_color: bool = False) -> str:
    if use_color:
        return f"Current price for {COLOR_YELLOW}{symbol}{COLOR_RESET}: {COLOR_GREEN}{price:.2f}{COLOR_RESET} {currency}"
    return f"Current price for {symbol}: {price:.2f} {currency}"


def save_chart_images(
    symbol: str,
    points: List[Tuple[dt.date, float]],
    output_dir: Path,
    chart_width: int = 800,
    chart_height: int = 400,
) -> tuple[Path, Path]:
    """Generate and save BMP and PNG chart images."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Error: Pillow library is required for image generation.", file=sys.stderr)
        print("Install it with: pip install Pillow", file=sys.stderr)
        raise

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract data
    dates = [date for date, _ in points]
    prices = [price for _, price in points]
    low = min(prices)
    high = max(prices)
    span = high - low if high != low else 1

    # Create image
    img = Image.new('RGB', (chart_width, chart_height), color='white')
    draw = ImageDraw.Draw(img)

    # Define chart area with margins
    margin_left = 60
    margin_right = 40
    margin_top = 40
    margin_bottom = 60
    chart_area_width = chart_width - margin_left - margin_right
    chart_area_height = chart_height - margin_top - margin_bottom

    # Draw title
    title = f"{symbol} - {len(points)} Day Trend"
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    draw.text((chart_width // 2 - 80, 10), title, fill='black', font=font)

    # Draw axes
    draw.line(
        [(margin_left, margin_top), (margin_left, chart_height - margin_bottom)],
        fill='black', width=2
    )
    draw.line(
        [(margin_left, chart_height - margin_bottom),
         (chart_width - margin_right, chart_height - margin_bottom)],
        fill='black', width=2
    )

    # Draw price labels on Y-axis
    num_price_labels = 5
    for i in range(num_price_labels):
        price_val = low + (span * i / (num_price_labels - 1))
        y_pos = chart_height - margin_bottom - (i * chart_area_height / (num_price_labels - 1))
        draw.text((5, y_pos - 5), f"{price_val:.2f}", fill='black', font=small_font)
        draw.line(
            [(margin_left - 5, y_pos), (margin_left, y_pos)],
            fill='black', width=1
        )

    # Calculate bar width
    bar_width = chart_area_width / len(points)
    bar_spacing = bar_width * 0.2
    actual_bar_width = bar_width - bar_spacing

    # Draw bars and date labels
    for i, (date, price) in enumerate(points):
        # Calculate bar position and height
        x_pos = margin_left + (i * bar_width) + (bar_spacing / 2)
        normalized_height = ((price - low) / span) * chart_area_height
        bar_top = chart_height - margin_bottom - normalized_height
        bar_bottom = chart_height - margin_bottom

        # Choose color (green for higher, blue for lower)
        bar_color = '#4CAF50' if price >= (low + span / 2) else '#2196F3'

        # Draw bar
        draw.rectangle(
            [x_pos, bar_top, x_pos + actual_bar_width, bar_bottom],
            fill=bar_color, outline='black'
        )

        # Draw date label (show every nth date to avoid crowding)
        if len(points) <= 10 or i % max(1, len(points) // 10) == 0:
            date_str = date.strftime("%m/%d")
            draw.text(
                (x_pos, chart_height - margin_bottom + 5),
                date_str, fill='black', font=small_font
            )

    # Draw legend
    legend_y = chart_height - 20
    draw.text((margin_left, legend_y), f"Low: {low:.2f}", fill='black', font=small_font)
    draw.text(
        (chart_width // 2 - 30, legend_y),
        f"High: {high:.2f}", fill='black', font=small_font
    )

    # Generate timestamp for unique filenames
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    bmp_path = output_dir / f"{symbol}_{timestamp}.bmp"
    png_path = output_dir / f"{symbol}_{timestamp}.png"

    # Save images
    img.save(bmp_path, 'BMP')
    img.save(png_path, 'PNG')

    return bmp_path, png_path


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
        "-c",
        "--colour",
        "--color",
        action="store_true",
        dest="colour",
        help="Enable colored output in the terminal",
    )
    parser.add_argument(
        "--save-charts",
        metavar="DIR",
        type=str,
        help="Generate and save BMP and PNG chart images to the specified directory",
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
        print(format_summary(info["symbol"], info["price"], info["currency"], use_color=args.colour))

    if first_points and first_chart_symbol:
        renderers = {
            "rows": lambda pts: render_ascii_chart(pts, use_color=args.colour),
            "bars": lambda pts: render_ascii_bar_chart(pts, use_color=args.colour),
        }
        renderer = renderers[args.chart]

        color_prefix = COLOR_MAGENTA if args.colour else ""
        color_suffix = COLOR_RESET if args.colour else ""
        print(f"\n{color_prefix}{days}-day trend ({args.chart}) for {first_chart_symbol}:{color_suffix}")
        print(renderer(first_points))

    # Save chart images if requested
    if args.save_charts and first_points and first_chart_symbol:
        try:
            output_dir = Path(args.save_charts)
            bmp_path, png_path = save_chart_images(
                first_chart_symbol,
                first_points,
                output_dir
            )
            success_color = COLOR_GREEN if args.colour else ""
            reset = COLOR_RESET if args.colour else ""
            print(f"\n{success_color}Charts saved:{reset}")
            print(f"  BMP: {bmp_path}")
            print(f"  PNG: {png_path}")
        except ImportError:
            pass  # Error already printed in save_chart_images
        except Exception as exc:
            error_color = COLOR_RED if args.colour else ""
            reset = COLOR_RESET if args.colour else ""
            print(f"{error_color}Error saving charts: {exc}{reset}", file=sys.stderr)

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
