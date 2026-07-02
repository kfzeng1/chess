const files = "abcdefghi";
const state = {
  pieces: new Map(),
  moves: [],
  sideToMove: "red",
  legalMoves: [],
  selected: null,
  lastMove: null,
  flipped: false,
  autoMode: true,
  notation: "cn",
  players: { red: "human", black: "ai" },
  aiSearch: {
    red: { mode: "movetime", movetime: 1, depth: 12 },
    black: { mode: "depth", movetime: 2, depth: 16 },
  },
  analysis: null,
  autoTimer: null,
};

const el = {
  board: document.getElementById("board"),
  turnText: document.getElementById("turnText"),
  turnStat: document.getElementById("turnStat"),
  roundStat: document.getElementById("roundStat"),
  moveCount: document.getElementById("moveCount"),
  thinking: document.getElementById("thinking"),
  redLabel: document.getElementById("redLabel"),
  blackLabel: document.getElementById("blackLabel"),
  autoMode: document.getElementById("autoMode"),
  manualAi: document.getElementById("manualAi"),
  delayRange: document.getElementById("delayRange"),
  delayLabel: document.getElementById("delayLabel"),
  pvLine: document.getElementById("pvLine"),
  recommendations: document.getElementById("recommendations"),
  historyMoves: document.getElementById("historyMoves"),
  historyModeLabel: document.getElementById("historyModeLabel"),
  depthText: document.getElementById("depthText"),
  nodesText: document.getElementById("nodesText"),
  wdlRed: document.getElementById("wdlRed"),
  wdlDraw: document.getElementById("wdlDraw"),
  wdlBlack: document.getElementById("wdlBlack"),
  engineStatus: document.getElementById("engineStatus"),
};

function sideName(side) {
  return side === "red" ? "红方" : "黑方";
}

function squareToCoord(square) {
  const file = files.indexOf(square[0]);
  const rank = Number(square[1]);
  return state.flipped ? { f: 8 - file, r: 9 - rank } : { f: file, r: rank };
}

async function api(path, payload) {
  const options = payload === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  };
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "request failed");
  return data;
}

function renderBoard() {
  el.board.querySelectorAll(".piece,.square-target,.hint").forEach((node) => node.remove());
  for (let f = 0; f < 9; f += 1) {
    for (let r = 0; r < 10; r += 1) {
      const coord = state.flipped ? { f: 8 - f, r: 9 - r } : { f, r };
      const button = document.createElement("button");
      button.className = "square-target";
      button.style.setProperty("--f", coord.f);
      button.style.setProperty("--r", coord.r);
      button.type = "button";
      button.dataset.square = `${files[f]}${r}`;
      button.addEventListener("click", () => handleSquareClick(button.dataset.square));
      el.board.appendChild(button);
    }
  }

  for (const [square, piece] of state.pieces) {
    const coord = squareToCoord(square);
    const img = document.createElement("img");
    img.className = "piece";
    if (state.selected === square) img.classList.add("selected");
    if (state.lastMove?.slice(0, 2) === square) img.classList.add("last-from");
    if (state.lastMove?.slice(2, 4) === square) img.classList.add("last-to");
    img.style.setProperty("--f", coord.f);
    img.style.setProperty("--r", coord.r);
    img.src = piece.image;
    img.alt = "";
    img.dataset.square = square;
    img.addEventListener("click", (event) => {
      event.stopPropagation();
      handleSquareClick(square);
    });
    el.board.appendChild(img);
  }

  if (state.selected) {
    state.legalMoves
      .filter((move) => move.slice(0, 2) === state.selected)
      .forEach((move) => {
        const coord = squareToCoord(move.slice(2, 4));
        const hint = document.createElement("span");
        hint.className = "hint";
        hint.style.setProperty("--f", coord.f);
        hint.style.setProperty("--r", coord.r);
        el.board.appendChild(hint);
      });
  }
}

function renderStatus() {
  el.turnText.textContent = `${sideName(state.sideToMove)}回合`;
  el.turnStat.textContent = sideName(state.sideToMove);
  el.roundStat.textContent = String(state.moves.length);
  el.moveCount.textContent = `${state.moves.length} 步`;
  el.redLabel.textContent = state.players.red === "human" ? "Human" : "Pikafish";
  el.blackLabel.textContent = state.players.black === "human" ? "Human" : "Pikafish";
  el.manualAi.disabled = state.players[state.sideToMove] !== "human";
}

function renderHistory(positionData) {
  const rows = state.notation === "cn" ? positionData.moveRowsCn : positionData.moveRowsUci;
  el.historyModeLabel.textContent = state.notation === "cn" ? "中文" : "UCI";
  el.historyMoves.innerHTML = rows.map((row) => (
    `<span class="num">${row.round}.</span><span class="red">${row.red}</span><span class="black">${row.black}</span>`
  )).join("");
}

function scoreText(line) {
  return line.score?.display || "-";
}

function renderAnalysis() {
  const analysis = state.analysis;
  if (!analysis?.lines?.length) {
    el.pvLine.innerHTML = "";
    el.recommendations.innerHTML = "";
    el.depthText.textContent = "未分析";
    el.nodesText.textContent = "0 nodes";
    return;
  }

  const best = analysis.lines[0];
  const pv = state.notation === "cn" ? best.pv_cn : best.pv;
  el.pvLine.innerHTML = pv.map((move, idx) => `<span class="move-chip ${idx % 2 === 0 ? "red" : "black"}">${move}</span>`).join("");
  el.depthText.textContent = `depth ${best.depth || "-"} / nps ${best.nps || "-"}`;
  el.nodesText.textContent = `${best.nodes || 0} nodes`;
  if (best.wdl) {
    el.wdlRed.textContent = `红胜 ${Math.round(best.wdl[0] / 10)}%`;
    el.wdlDraw.textContent = `和 ${Math.round(best.wdl[1] / 10)}%`;
    el.wdlBlack.textContent = `黑胜 ${Math.round(best.wdl[2] / 10)}%`;
  }

  el.recommendations.innerHTML = analysis.lines.map((line, idx) => {
    const move = state.notation === "cn" ? line.pv_cn[0] : line.bestmove;
    const linePv = state.notation === "cn" ? line.pv_cn.join(" ") : line.pv.join(" ");
    const wdl = line.wdl ? `WDL ${line.wdl.join("/")}` : "";
    return `
      <div class="rec ${idx === 0 ? "best" : ""}">
        <div class="rank">${idx + 1}</div>
        <div class="rec-main"><strong>${move}</strong><span>${state.notation === "cn" ? "主变" : "pv"} ${linePv}</span></div>
        <div class="eval"><strong>${scoreText(line)}</strong><span>${wdl}</span></div>
      </div>
    `;
  }).join("");
}

async function syncPosition() {
  const data = await api("/api/position", { moves: state.moves });
  state.pieces = new Map(data.pieces.map((piece) => [piece.square, piece]));
  state.sideToMove = data.sideToMove;
  state.legalMoves = data.legalMoves || [];
  renderBoard();
  renderStatus();
  renderHistory(data);
  scheduleAuto();
}

function movePiece(move) {
  state.moves.push(move);
  state.lastMove = move;
  state.selected = null;
  state.analysis = null;
  return syncPosition();
}

function handleSquareClick(square) {
  if (state.players[state.sideToMove] !== "human") return;
  const piece = state.pieces.get(square);
  if (!state.selected) {
    if (piece?.side === state.sideToMove) {
      state.selected = square;
      renderBoard();
    }
    return;
  }
  if (piece?.side === state.sideToMove) {
    state.selected = square;
    renderBoard();
    return;
  }
  const move = state.selected + square;
  if (!state.legalMoves.includes(move)) return;
  movePiece(move).catch(showError);
}

function currentLimit() {
  const config = state.aiSearch[state.sideToMove];
  return {
    mode: config.mode,
    value: config.mode === "depth" ? config.depth : Math.round(config.movetime * 1000),
  };
}

async function analyze(applyBest = false) {
  el.thinking.textContent = "思考中";
  el.engineStatus.textContent = "Pikafish thinking";
  const data = await api("/api/analyze", { moves: state.moves, limit: currentLimit(), multipv: 5 });
  state.analysis = data;
  renderAnalysis();
  el.thinking.textContent = "待命";
  el.engineStatus.textContent = "Pikafish ready";
  if (applyBest && data.bestmove) {
    await movePiece(data.bestmove);
  }
}

function scheduleAuto() {
  clearTimeout(state.autoTimer);
  if (!state.autoMode || state.players[state.sideToMove] !== "ai") return;
  const delay = Number(el.delayRange.value) * 1000;
  state.autoTimer = setTimeout(() => {
    if (state.autoMode && state.players[state.sideToMove] === "ai") {
      analyze(true).catch(showError);
    }
  }, delay);
}

function updateAiSearch(side) {
  const config = state.aiSearch[side];
  const label = document.querySelector(`[data-ai-label="${side}"]`);
  const range = document.querySelector(`[data-ai-range="${side}"]`);
  const command = document.querySelector(`[data-ai-command="${side}"]`);
  document.querySelectorAll(`[data-ai-mode-tabs="${side}"] button`).forEach((button) => {
    button.classList.toggle(side === "red" ? "active-red" : "active-black", button.dataset.aiMode === config.mode);
  });
  if (config.mode === "movetime") {
    range.min = "0.1"; range.max = "30"; range.step = "0.1"; range.value = String(config.movetime);
    label.textContent = `每步 ${config.movetime.toFixed(1)}s`;
    command.textContent = `go movetime ${Math.round(config.movetime * 1000)}`;
  } else {
    range.min = "1"; range.max = "30"; range.step = "1"; range.value = String(config.depth);
    label.textContent = `depth ${config.depth}`;
    command.textContent = `go depth ${config.depth}`;
  }
}

function showError(error) {
  el.thinking.textContent = "错误";
  el.engineStatus.textContent = error.message;
  console.error(error);
}

function bindControls() {
  document.getElementById("newGame").addEventListener("click", () => {
    state.moves = [];
    state.selected = null;
    state.lastMove = null;
    state.analysis = null;
    syncPosition().catch(showError);
    renderAnalysis();
  });
  document.getElementById("undoMove").addEventListener("click", () => {
    state.moves.pop();
    state.lastMove = state.moves.at(-1) || null;
    state.analysis = null;
    syncPosition().catch(showError);
    renderAnalysis();
  });
  document.getElementById("flipBoard").addEventListener("click", () => {
    state.flipped = !state.flipped;
    renderBoard();
  });
  el.autoMode.addEventListener("click", () => {
    state.autoMode = !state.autoMode;
    el.autoMode.textContent = state.autoMode ? "自动模式：开" : "自动模式：关";
    el.autoMode.classList.toggle("is-off", !state.autoMode);
    scheduleAuto();
  });
  el.manualAi.addEventListener("click", () => analyze(true).catch(showError));
  el.delayRange.addEventListener("input", () => {
    el.delayLabel.textContent = `${Number(el.delayRange.value).toFixed(1)}s 后判断`;
    scheduleAuto();
  });
  document.querySelectorAll(".segmented").forEach((segmented) => {
    segmented.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      const side = segmented.dataset.side;
      state.players[side] = button.dataset.player;
      segmented.querySelectorAll("button").forEach((item) => item.classList.remove("active-red", "active-black"));
      button.classList.add(side === "red" ? "active-red" : "active-black");
      renderStatus();
      scheduleAuto();
    });
  });
  document.querySelectorAll("[data-ai-mode-tabs]").forEach((tabs) => {
    tabs.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      const side = tabs.dataset.aiModeTabs;
      state.aiSearch[side].mode = button.dataset.aiMode;
      updateAiSearch(side);
    });
  });
  document.querySelectorAll("[data-ai-range]").forEach((range) => {
    range.addEventListener("input", () => {
      const side = range.dataset.aiRange;
      const config = state.aiSearch[side];
      if (config.mode === "movetime") config.movetime = Number(range.value);
      else config.depth = Number(range.value);
      updateAiSearch(side);
    });
  });
  document.querySelectorAll("[data-notation-mode]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.notation = button.dataset.notationMode;
      document.querySelectorAll("[data-notation-mode]").forEach((item) => item.classList.toggle("active-red", item === button));
      const data = await api("/api/position", { moves: state.moves });
      renderHistory(data);
      renderAnalysis();
    });
  });
}

bindControls();
updateAiSearch("red");
updateAiSearch("black");
syncPosition().then(() => analyze(false)).catch(showError);

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/service-worker.js").catch((error) => {
    console.warn("service worker registration failed", error);
  });
}
