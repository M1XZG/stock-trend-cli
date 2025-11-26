#!/usr/bin/env node

/**
 * Lightweight Express server that renders a dot-matrix style web UI
 * for scrolling stock quotes. Launch with:
 *   node server.js AAPL MSFT --port 4000
 */

const path = require("path");
const express = require("express");

const USER_AGENT = "Mozilla/5.0 (compatible; StockTrendWeb/1.0; +https://github.com)";
const DEFAULT_SYMBOLS = ["AAPL"];
const DEFAULT_PORT = process.env.PORT ? Number(process.env.PORT) : 4173;
const DEFAULT_REFRESH_MINUTES = process.env.REFRESH_MINUTES
  ? Number(process.env.REFRESH_MINUTES)
  : 30;

const openPromise = import("open")
  .then((mod) => mod.default || mod)
  .catch((error) => {
    console.warn("Warning: unable to load 'open' package:", error.message);
    return null;
  });

const fetchProviderPromise = (async () => {
  if (typeof fetch === "function") {
    return (...args) => fetch(...args);
  }
  const { default: nodeFetch } = await import("node-fetch");
  return (...args) => nodeFetch(...args);
})();

async function fetchStockQuote(symbol) {
  const normalized = symbol.trim().toUpperCase();
  const fetchImpl = await fetchProviderPromise;
  const url =
    `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(normalized)}?` +
    "range=5d&interval=1d&includePrePost=false&events=div%2Csplits";

  const response = await fetchImpl(url, {
    headers: { "User-Agent": USER_AGENT },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${normalized}: HTTP ${response.status}`);
  }

  const payload = await response.json();
  const chart = payload.chart || {};
  if (chart.error) {
    const message = chart.error.description || chart.error.code;
    throw new Error(`Provider error for ${normalized}: ${message}`);
  }

  const results = Array.isArray(chart.result) ? chart.result : [];
  if (!results.length) {
    throw new Error(`No data returned for ${normalized}`);
  }

  const meta = results[0].meta || {};
  const currentPrice = meta.regularMarketPrice;
  const currency = meta.currency || "USD";
  const previousClose = meta.chartPreviousClose;
  const timestamp = meta.regularMarketTime;

  const change =
    typeof currentPrice === "number" && typeof previousClose === "number"
      ? currentPrice - previousClose
      : null;

  const changePercent =
    typeof currentPrice === "number" && typeof previousClose === "number"
      ? (change / previousClose) * 100
      : null;

  return {
    symbol: normalized,
    price: typeof currentPrice === "number" ? currentPrice : null,
    currency,
    change,
    changePercent,
    timestamp,
  };
}

function parseArguments(argv) {
  const args = argv.slice(2);
  const symbols = [];
  let port = DEFAULT_PORT;
  let refreshMinutes = DEFAULT_REFRESH_MINUTES;

  for (let i = 0; i < args.length; i += 1) {
    const token = args[i];
    if (token === "--port" || token === "-p") {
      const next = args[i + 1];
      if (!next || Number.isNaN(Number(next))) {
        throw new Error("--port expects a numeric argument");
      }
      port = Number(next);
      i += 1;
      continue;
    }

    if (token.startsWith("--port=")) {
      const value = token.split("=")[1];
      if (Number.isNaN(Number(value))) {
        throw new Error("--port expects a numeric argument");
      }
      port = Number(value);
      continue;
    }

    if (token === "--refresh" || token === "--refresh-minutes") {
      const next = args[i + 1];
      if (!next || Number.isNaN(Number(next))) {
        throw new Error("--refresh expects a numeric value in minutes");
      }
      refreshMinutes = Number(next);
      i += 1;
      continue;
    }

    if (token.startsWith("--refresh=") || token.startsWith("--refresh-minutes=")) {
      const value = token.split("=")[1];
      if (Number.isNaN(Number(value))) {
        throw new Error("--refresh expects a numeric value in minutes");
      }
      refreshMinutes = Number(value);
      continue;
    }

    symbols.push(token.trim());
  }

  if (Number.isNaN(refreshMinutes) || refreshMinutes <= 0) {
    throw new Error("Refresh interval must be a positive number of minutes");
  }

  return {
    port,
    symbols: symbols.length ? symbols : DEFAULT_SYMBOLS,
    refreshMs: refreshMinutes * 60 * 1000,
  };
}

function createServer(options) {
  const app = express();
  const symbols = options.symbols;
  let refreshMs = options.refreshMs;

  const state = {
    quotes: [],
    updatedAt: 0,
    lastError: null,
  };

  let refreshInFlight = null;
  let timer = null;

  const stopTimer = () => {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  };

  app.use(express.json());

  async function refreshQuotes(force = false) {
    const now = Date.now();
    if (!force && state.quotes.length && now - state.updatedAt < refreshMs) {
      return;
    }

    if (refreshInFlight) {
      await refreshInFlight;
      return;
    }

    refreshInFlight = (async () => {
      try {
        const quotes = await Promise.all(symbols.map((symbol) => fetchStockQuote(symbol)));
        state.quotes = quotes;
        state.updatedAt = Date.now();
        state.lastError = null;
      } catch (error) {
        state.lastError = error;
        throw error;
      } finally {
        refreshInFlight = null;
      }
    })();

    await refreshInFlight;
  }

  refreshQuotes(true).catch((error) => {
    console.warn("Initial quote refresh failed:", error.message);
  });

  const startTimer = () => {
    stopTimer();
    timer = setInterval(() => {
      refreshQuotes().catch((error) => {
        console.warn("Quote refresh error:", error.message);
      });
    }, refreshMs);
    if (typeof timer.unref === "function") {
      timer.unref();
    }
  };

  startTimer();

  app.use(express.static(path.join(__dirname, "public")));

  app.get("/api/data", async (req, res) => {
    const querySymbols = (req.query.symbols || "")
      .split(",")
      .map((entry) => entry.trim())
      .filter(Boolean);

    try {
      if (querySymbols.length) {
        const quotes = await Promise.all(
          querySymbols.map((symbol) => fetchStockQuote(symbol)),
        );
        res.json({
          updatedAt: Date.now(),
          quotes,
          refreshMs: options.refreshMs,
        });
        return;
      }

      await refreshQuotes(!state.quotes.length);
      if (!state.quotes.length && state.lastError) {
        throw state.lastError;
      }

      res.json({
        updatedAt: state.updatedAt,
        quotes: state.quotes,
        refreshMs,
      });
    } catch (error) {
      res.status(502).json({
        error: error.message || String(error),
      });
    }
  });

  app.post("/api/settings/refresh", async (req, res) => {
    const raw =
      (req.body && (req.body.minutes ?? req.body.refreshMinutes)) ??
      req.query.minutes ??
      req.query.refreshMinutes;

    const minutes = Number(raw);
    if (!Number.isFinite(minutes)) {
      res.status(400).json({ error: "Refresh minutes must be numeric" });
      return;
    }

    if (minutes < 5 || minutes > 720) {
      res.status(400).json({ error: "Refresh minutes must be between 5 and 720" });
      return;
    }

    const newRefreshMs = Math.round(minutes * 60 * 1000);
    if (newRefreshMs !== refreshMs) {
      refreshMs = newRefreshMs;
      startTimer();
      refreshQuotes(true).catch((error) => {
        console.warn("Immediate refresh after interval change failed:", error.message);
      });
    }

    res.json({ refreshMs, refreshMinutes: Math.round(refreshMs / 60000) });
  });

  // fallback to index.html for root
  app.get("*", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html"));
  });

  app.locals.stopTimer = stopTimer;
  return app;
}

async function main() {
  let parsed;
  try {
    parsed = parseArguments(process.argv);
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exitCode = 1;
    return;
  }

  const app = createServer(parsed);
  const server = app.listen(parsed.port, () => {
    const address = `http://localhost:${parsed.port}`;
    const refreshMinutes = (parsed.refreshMs / 60000).toFixed(1).replace(/\.0$/, "");
    console.log(
      `📟  Stock trend web UI available at ${address} (auto-refresh every ${refreshMinutes} min)`,
    );
    openPromise
      .then((open) => {
        if (typeof open === "function") {
          return open(address);
        }
        return null;
      })
      .catch((error) => {
        console.warn("Warning: unable to open browser automatically:", error.message);
      });
  });

  const signals = ["SIGINT", "SIGTERM"];
  server.on("close", () => {
    if (typeof app.locals.stopTimer === "function") {
      app.locals.stopTimer();
    }
  });

  const shutdown = () => {
    server.close(() => process.exit(0));
  };
  signals.forEach((sig) => process.on(sig, shutdown));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
