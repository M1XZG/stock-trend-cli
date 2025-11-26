const WIDTH = 64;
const HEIGHT = 32;
const DEFAULT_SCROLL_INTERVAL = 70; // milliseconds between column shifts
const REFRESH_MIN_MINUTES = 5;
const REFRESH_MAX_MINUTES = 720;
const DEFAULT_REFRESH_MINUTES = 30;
let scrollInterval = DEFAULT_SCROLL_INTERVAL;
let doubleLineMode = false;
let requestedSymbols = [];
let latestQuotes = [];
let refreshIntervalMinutes = DEFAULT_REFRESH_MINUTES;
let pollIntervalMs = DEFAULT_REFRESH_MINUTES * 60_000;
let pollTimerId = null;

const canvas = document.getElementById("matrix");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");
const controlsForm = document.getElementById("controls");
const symbolsInput = document.getElementById("symbolsInput");
const speedSlider = document.getElementById("speedSlider");
const speedValue = document.getElementById("speedValue");
const refreshSlider = document.getElementById("refreshSlider");
const refreshValue = document.getElementById("refreshValue");
const doubleLineCheckbox = document.getElementById("doubleLine");

const FONT = (() => {
  const GLYPH_HEIGHT = 7;
  const GLYPH_WIDTH = 5;

  const glyph = (rows) => rows.map((row) => row.padEnd(GLYPH_WIDTH, " ").slice(0, GLYPH_WIDTH));

  const base = {
    " ": glyph(["     ", "     ", "     ", "     ", "     ", "     ", "     "]),
    "0": glyph([" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "]),
    "1": glyph(["  #  ", " ##  ", "# #  ", "  #  ", "  #  ", "  #  ", "#####"]),
    "2": glyph([" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"]),
    "3": glyph([" ### ", "#   #", "    #", " ### ", "    #", "#   #", " ### "]),
    "4": glyph(["   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "]),
    "5": glyph(["#####", "#    ", "#    ", "#### ", "    #", "    #", "#### "]),
    "6": glyph([" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "]),
    "7": glyph(["#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "]),
    "8": glyph([" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "]),
    "9": glyph([" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "]),
    "A": glyph([" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"]),
    "B": glyph(["#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "]),
    "C": glyph([" ### ", "#   #", "#    ", "#    ", "#    ", "#   #", " ### "]),
    "D": glyph(["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "]),
    "E": glyph(["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"]),
    "F": glyph(["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "]),
    "G": glyph([" ### ", "#   #", "#    ", "# ###", "#   #", "#   #", " ### "]),
    "H": glyph(["#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"]),
    "I": glyph(["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"]),
    "J": glyph(["#####", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "]),
    "K": glyph(["#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"]),
    "L": glyph(["#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"]),
    "M": glyph(["#   #", "## ##", "# # #", "#   #", "#   #", "#   #", "#   #"]),
    "N": glyph(["#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"]),
    "O": glyph([" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "]),
    "P": glyph(["#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "]),
    "Q": glyph([" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"]),
    "R": glyph(["#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"]),
    "S": glyph([" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "]),
    "T": glyph(["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "]),
    "U": glyph(["#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "]),
    "V": glyph(["#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "]),
    "W": glyph(["#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"]),
    "X": glyph(["#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"]),
    "Y": glyph(["#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "]),
    "Z": glyph(["#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"]),
    "-": glyph(["     ", "     ", "     ", "#####", "     ", "     ", "     "]),
    "+": glyph(["     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "]),
    ".": glyph(["     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "]),
    ":": glyph(["     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "]),
    "/": glyph(["    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "]),
    "%": glyph(["#   #", "   # ", "  #  ", " #   ", "#   #", "     ", "     "]),
  };

  return { data: base, width: GLYPH_WIDTH, height: GLYPH_HEIGHT };
})();

let columns = [[0]];
let offset = 0;
let lastStep = 0;

function buildColumns(messageOrMessages, height = HEIGHT) {
  const glyphHeight = FONT.height;
  const glyphWidth = FONT.width;
  const blankColumn = Array(height).fill(0);
  const lines = Array.isArray(messageOrMessages)
    ? messageOrMessages
    : [messageOrMessages];
  const lineCount = Math.max(1, lines.length);

  const allocations = [];
  const baseHeight = Math.floor(height / lineCount);
  let remainder = height - baseHeight * lineCount;
  let offsetBase = 0;

  for (let i = 0; i < lineCount; i += 1) {
    const segmentHeight = baseHeight + (remainder > 0 ? 1 : 0);
    if (remainder > 0) {
      remainder -= 1;
    }
    const available = Math.max(segmentHeight, glyphHeight);
    const maxTop = Math.max(0, available - glyphHeight);
    const topPad = Math.floor(maxTop / 2);
    const baseRow = Math.min(offsetBase + topPad, Math.max(0, height - glyphHeight));
    allocations.push({
      message: (lines[i] ?? " ").toString(),
      baseRow,
    });
    offsetBase += segmentHeight;
  }

  const perLineColumns = allocations.map(({ message, baseRow }) => {
    const lineColumns = [];
    const text = message.length ? message.toUpperCase() : " ";

    for (const char of text) {
      const glyph = FONT.data[char] || FONT.data[" "];
      for (let x = 0; x < glyphWidth; x += 1) {
        const column = Array(height).fill(0);
        for (let y = 0; y < glyphHeight; y += 1) {
          if (glyph[y][x] !== " ") {
            const row = baseRow + y;
            if (row >= 0 && row < height) {
              column[row] = 1;
            }
          }
        }
        lineColumns.push(column);
      }
      lineColumns.push(blankColumn.slice());
    }

    for (let i = 0; i < glyphWidth; i += 1) {
      lineColumns.push(blankColumn.slice());
    }

    return lineColumns;
  });

  const maxColumns = Math.max(1, ...perLineColumns.map((cols) => cols.length));
  const output = [];

  for (let idx = 0; idx < maxColumns; idx += 1) {
    const column = Array(height).fill(0);
    for (const lineColumns of perLineColumns) {
      const source = lineColumns[idx];
      if (!source) {
        continue;
      }
      for (let y = 0; y < height; y += 1) {
        if (source[y]) {
          column[y] = 1;
        }
      }
    }
    output.push(column);
  }

  return output.length ? output : [blankColumn.slice()];
}

function drawFrame() {
  for (let x = 0; x < WIDTH; x += 1) {
    const column = columns[(offset + x) % columns.length];
    for (let y = 0; y < HEIGHT; y += 1) {
      ctx.fillStyle = column[y] ? "#39ff14" : "#021502";
      ctx.fillRect(x, y, 1, 1);
    }
  }
}

function step(timestamp) {
  if (timestamp - lastStep >= scrollInterval) {
    offset = (offset + 1) % columns.length;
    lastStep = timestamp;
    drawFrame();
  }
  window.requestAnimationFrame(step);
}

function updateSpeedLabel() {
  if (speedValue) {
    speedValue.textContent = `${scrollInterval} ms`;
  }
}

function updateRefreshLabel(minutes) {
  if (!refreshValue) {
    return;
  }
  const value = minutes >= 60
    ? `${(minutes / 60).toFixed(minutes % 60 === 0 ? 0 : 1)} h`
    : `${minutes} min`;
  refreshValue.textContent = value;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function schedulePoll(intervalMs) {
  if (!Number.isFinite(intervalMs) || intervalMs <= 0) {
    return;
  }
  if (pollTimerId && intervalMs === pollIntervalMs) {
    return;
  }
  if (pollTimerId) {
    clearInterval(pollTimerId);
  }
  pollIntervalMs = intervalMs;
  pollTimerId = setInterval(loadData, intervalMs);
}

function parseSymbols(value) {
  if (!value) {
    return [];
  }
  return value
    .split(/[\s,]+/)
    .map((entry) => entry.trim().toUpperCase())
    .filter(Boolean);
}

function formatQuote(quote) {
  const price = typeof quote.price === "number" ? quote.price.toFixed(2) : "?";
  const pieces = [quote.symbol, price];
  if (quote.currency) {
    pieces.push(quote.currency);
  }

  if (typeof quote.change === "number" && typeof quote.changePercent === "number") {
    const sign = quote.change >= 0 ? "+" : "-";
    pieces.push(
      `${sign}${Math.abs(quote.change).toFixed(2)} (${sign}${Math.abs(quote.changePercent).toFixed(2)}%)`,
    );
  }

  return pieces.join(" ");
}

function rebuildColumns() {
  if (!latestQuotes.length) {
    return;
  }

  const formatted = latestQuotes.map((quote) => formatQuote(quote));

  if (doubleLineMode) {
    const top = [];
    const bottom = [];
    formatted.forEach((entry, index) => {
      if (index % 2 === 0) {
        top.push(entry);
      } else {
        bottom.push(entry);
      }
    });
    if (!top.length) {
      top.push(" ");
    }
    if (!bottom.length) {
      bottom.push(" ");
    }
    columns = buildColumns([top.join("   "), bottom.join("   ")]);
  } else {
    columns = buildColumns(formatted.join("   "));
  }

  offset = 0;
  lastStep = 0;
  drawFrame();
}

async function loadData() {
  try {
    statusEl.textContent = "Fetching quotes…";
    const query = requestedSymbols.length
      ? `?symbols=${encodeURIComponent(requestedSymbols.join(","))}`
      : "";
    const response = await fetch(`/api/data${query}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    if (!payload.quotes || !payload.quotes.length) {
      throw new Error("No quotes available");
    }
    latestQuotes = payload.quotes;
    if (!requestedSymbols.length && symbolsInput && !symbolsInput.value) {
      symbolsInput.placeholder = payload.quotes.map((quote) => quote.symbol).join(" ") || symbolsInput.placeholder;
    }

    rebuildColumns();
    const updatedAtText = new Date(payload.updatedAt).toLocaleTimeString();
    let refreshNote = "";
    if (typeof payload.refreshMs === "number" && !Number.isNaN(payload.refreshMs)) {
      const minutes = payload.refreshMs / 60000;
      if (minutes >= 1) {
        const display = minutes % 1 === 0 ? minutes.toFixed(0) : minutes.toFixed(1);
        refreshNote = ` • Server refresh ${display} min`;
      } else {
        const seconds = Math.max(1, Math.round(payload.refreshMs / 1000));
        refreshNote = ` • Server refresh ${seconds}s`;
      }
    }

    statusEl.textContent = `Last updated ${updatedAtText}${refreshNote}`;

    if (typeof payload.refreshMs === "number" && !Number.isNaN(payload.refreshMs)) {
      const serverMinutes = clamp(
        Math.round(payload.refreshMs / 60000),
        REFRESH_MIN_MINUTES,
        REFRESH_MAX_MINUTES,
      );
      refreshIntervalMinutes = serverMinutes;
      schedulePoll(serverMinutes * 60_000);
      if (refreshSlider && document.activeElement !== refreshSlider) {
        refreshSlider.value = String(serverMinutes);
        updateRefreshLabel(serverMinutes);
      }
    }
  } catch (error) {
    statusEl.textContent = `Error fetching quotes: ${error.message}`;
  }
}

window.requestAnimationFrame(step);
loadData();
schedulePoll(refreshIntervalMinutes * 60_000);

if (controlsForm) {
  controlsForm.addEventListener("submit", (event) => {
    event.preventDefault();
    requestedSymbols = parseSymbols(symbolsInput?.value ?? "");
    loadData();
  });
}

if (speedSlider) {
  scrollInterval = Number(speedSlider.value) || DEFAULT_SCROLL_INTERVAL;
  updateSpeedLabel();
  speedSlider.addEventListener("input", () => {
    scrollInterval = Number(speedSlider.value) || DEFAULT_SCROLL_INTERVAL;
    updateSpeedLabel();
  });
}

if (refreshSlider) {
  const initialMinutes = clamp(Number(refreshSlider.value) || DEFAULT_REFRESH_MINUTES, REFRESH_MIN_MINUTES, REFRESH_MAX_MINUTES);
  refreshSlider.value = String(initialMinutes);
  refreshIntervalMinutes = initialMinutes;
  updateRefreshLabel(initialMinutes);
  schedulePoll(initialMinutes * 60_000);

  refreshSlider.addEventListener("input", () => {
    const minutes = clamp(Number(refreshSlider.value) || DEFAULT_REFRESH_MINUTES, REFRESH_MIN_MINUTES, REFRESH_MAX_MINUTES);
    updateRefreshLabel(minutes);
  });

  refreshSlider.addEventListener("change", () => {
    const minutes = clamp(Number(refreshSlider.value) || DEFAULT_REFRESH_MINUTES, REFRESH_MIN_MINUTES, REFRESH_MAX_MINUTES);
    refreshSlider.value = String(minutes);
    refreshIntervalMinutes = minutes;
    updateRefreshLabel(minutes);
    statusEl.textContent = `Updating refresh interval to ${minutes} min…`;

    fetch("/api/settings/refresh", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ minutes }),
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        const minutesFromServer = data && typeof data.refreshMs === "number"
          ? clamp(Math.round(data.refreshMs / 60000), REFRESH_MIN_MINUTES, REFRESH_MAX_MINUTES)
          : minutes;
        refreshIntervalMinutes = minutesFromServer;
        schedulePoll(minutesFromServer * 60_000);
        updateRefreshLabel(minutesFromServer);
        statusEl.textContent = `Refresh interval set to ${minutesFromServer} min`;
        return loadData();
      })
      .catch((error) => {
        statusEl.textContent = `Error updating refresh interval: ${error.message}`;
      });
  });
}

if (doubleLineCheckbox) {
  doubleLineCheckbox.addEventListener("change", () => {
    doubleLineMode = doubleLineCheckbox.checked;
    rebuildColumns();
  });
}
