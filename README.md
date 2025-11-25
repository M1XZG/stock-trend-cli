# Stock Trend CLI

A lightweight command-line helper that fetches the current stock price for a ticker symbol and prints an ASCII chart of recent daily closes. Data is retrieved directly from the Yahoo Finance chart API using Python's standard library only.

## Features

- 📈 Prints the latest regular-market price extracted from Yahoo Finance.
- 🗓️ Configurable history window via `--days` (defaults to 5).
- 🎨 Two ASCII chart styles: horizontal row chart (`rows`) or vertical bar chart (`bars`).
- ⚙️ Zero external dependencies—runs anywhere Python 3 is available.

## Requirements

- Python 3.9 or newer (earlier versions may work but aren’t validated).
- Internet access (the tool queries Yahoo Finance).

## Quick start

```bash
python3 stock_trend.py AAPL
```

Example output:

```text
Current price for AAPL: 189.87 USD

5-day trend (rows):
2025-11-19 |   187.63 | #########################
2025-11-20 |   188.42 | ##########################
2025-11-21 |   189.12 | ############################
2025-11-22 |   189.70 | #############################
2025-11-25 |   189.87 | #############################
```

## Usage

```text
usage: stock_trend.py [-h] [-d N] [--chart {rows,bars}] SYMBOL
```

| Option | Description |
| --- | --- |
| `SYMBOL` | Ticker symbol, e.g. `AAPL`, `MSFT`, `TSLA`. |
| `-d`, `--days` | Number of calendar days of history to fetch (default: 5). |
| `--chart` | ASCII chart style: `rows` for horizontal bars, `bars` for a vertical bar chart. |

### Examples

- Show 10 days of history with the vertical bar chart:

  ```bash
  python3 stock_trend.py MSFT --days 10 --chart bars
  ```

- Fetch two weeks of data for Tesla using horizontal rows:

  ```bash
  python3 stock_trend.py TSLA --days 14
  ```

## Notes

- Prices are sourced from Yahoo Finance; availability or accuracy isn’t guaranteed.
- The script skips days without a reported closing price.
- For large `--days` values, Yahoo may return less data than requested depending on the ticker.

## Development

Clone the repository and create a virtual environment if desired:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Run the script locally:

```bash
python3 stock_trend.py NVDA --chart bars
```

Currently there are no automated tests, but you can verify the module imports cleanly with:

```bash
python3 -m unittest
```

## License

This project is provided under the MIT License. See `LICENSE` if present or add one that suits your needs.
