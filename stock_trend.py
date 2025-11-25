#!/usr/bin/env python3
"""Simple CLI tool to fetch current stock price and render a recent ASCII trend."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from typing import Iterable, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

YAHOO_CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?"
    "range={days}d&interval=1d&includePrePost=false&events=div%2Csplits"
)
USER_AGENT = "Mozilla/5.0 (compatible; StockTrendBot/1.0; +https://github.com)"


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
        description="Fetch the current stock price and display an ASCII chart of recent history.",
    )
    parser.add_argument(
        "symbol",
        metavar="SYMBOL",
        help="Ticker symbol, e.g. AAPL or MSFT",
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

    args = parser.parse_args(argv)
    symbol_input = args.symbol.upper().strip()
    days = args.days

    try:
        payload = fetch_chart_payload(symbol_input, days)
        symbol, price, currency, points = extract_price_points(payload)
    except StockLookupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(format_summary(symbol, price, currency))
    renderers = {
        "rows": render_ascii_chart,
        "bars": render_ascii_bar_chart,
    }
    renderer = renderers[args.chart]

    print(f"\n{days}-day trend ({args.chart}):")
    print(renderer(points))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
