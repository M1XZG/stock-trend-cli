const WIDTH = 64;
const HEIGHT = 32;
const SCROLL_INTERVAL = 70; // milliseconds between column shifts

const canvas = document.getElementById("matrix");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");

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

function buildColumns(message, height = HEIGHT) {
  const glyphHeight = FONT.height;
  const glyphWidth = FONT.width;
  const topPad = Math.floor((height - glyphHeight) / 2);
  const bottomPad = height - glyphHeight - topPad;
  const blankColumn = Array(height).fill(0);
  const output = [];

  const addBlank = () => output.push([...blankColumn]);

  for (const char of message.toUpperCase()) {
    const glyph = FONT.data[char] || FONT.data[" "];
    for (let x = 0; x < glyphWidth; x += 1) {
      const column = Array(height).fill(0);
      for (let y = 0; y < glyphHeight; y += 1) {
        if (glyph[y][x] !== " ") {
          column[topPad + y] = 1;
        }
      }
      output.push(column);
    }
    addBlank();
  }

  for (let i = 0; i < glyphWidth; i += 1) {
    addBlank();
  }

  return output.length ? output : [blankColumn];
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
  if (timestamp - lastStep >= SCROLL_INTERVAL) {
    offset = (offset + 1) % columns.length;
    lastStep = timestamp;
    drawFrame();
  }
  window.requestAnimationFrame(step);
}

async function loadData() {
  try {
    statusEl.textContent = "Fetching quotes…";
    const response = await fetch("/api/data");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    if (!payload.quotes || !payload.quotes.length) {
      throw new Error("No quotes available");
    }

    const formatChange = (quote) => {
      if (typeof quote.change !== "number" || typeof quote.changePercent !== "number") {
        return "";
      }
      const sign = quote.change >= 0 ? "+" : "-";
      return `${sign}${Math.abs(quote.change).toFixed(2)} (${sign}${Math.abs(quote.changePercent).toFixed(2)}%)`;
    };

    const message = payload.quotes
      .map((quote) => {
        const price = typeof quote.price === "number" ? quote.price.toFixed(2) : "?";
        const change = formatChange(quote);
        const pieces = [quote.symbol, price];
        if (quote.currency) {
          pieces.push(quote.currency);
        }
        if (change) {
          pieces.push(change);
        }
        return pieces.join(" ");
      })
      .join("   ");

    columns = buildColumns(message);
    drawFrame();
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
  } catch (error) {
    statusEl.textContent = `Error fetching quotes: ${error.message}`;
  }
}

window.requestAnimationFrame(step);
loadData();
setInterval(loadData, 60_000);
