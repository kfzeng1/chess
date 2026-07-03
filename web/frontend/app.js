const files = "abcdefghi";
const state = {
  pieces: new Map(),
  moves: [],
  sideToMove: "red",
  legalMoves: [],
  gameOver: false,
  inCheck: false,
  positionId: "",
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
  analysisKey: "",
  clocks: { red: 0, black: 0 },
  lastClockTick: Date.now(),
  generation: 0,
  auditLogs: [],
  mismatchCount: 0,
  mismatchHandling: false,
  analysisInFlight: false,
  analysisInFlightCount: 0,
  pendingProtectedActions: new Map(),
  flushingProtectedActions: false,
  undoTimer: null,
};

const el = {
  board: document.getElementById("board"),
  turnText: document.getElementById("turnText"),
  turnStat: document.getElementById("turnStat"),
  roundStat: document.getElementById("roundStat"),
  redClock: document.getElementById("redClock"),
  blackClock: document.getElementById("blackClock"),
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
  auditLog: document.getElementById("auditLog"),
  mismatchCount: document.getElementById("mismatchCount"),
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
  if (state.gameOver) {
    el.turnText.textContent = state.inCheck ? `${sideName(state.sideToMove)}将死` : `${sideName(state.sideToMove)}困毙`;
  } else {
    el.turnText.textContent = `${sideName(state.sideToMove)}回合`;
  }
  el.turnStat.textContent = sideName(state.sideToMove);
  el.roundStat.textContent = String(state.moves.length);
  el.moveCount.textContent = `${state.moves.length} 步`;
  el.redLabel.textContent = state.players.red === "human" ? "Human" : "Pikafish";
  el.blackLabel.textContent = state.players.black === "human" ? "Human" : "Pikafish";
  el.manualAi.disabled = state.gameOver;
  renderClocks();
}

function formatClock(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function renderClocks() {
  el.redClock.textContent = formatClock(state.clocks.red);
  el.blackClock.textContent = formatClock(state.clocks.black);
}

function tickClock() {
  const now = Date.now();
  const elapsed = now - state.lastClockTick;
  state.lastClockTick = now;
  if (!state.gameOver) {
    state.clocks[state.sideToMove] += elapsed;
    renderClocks();
  }
}

function renderHistory(positionData) {
  const rows = state.notation === "cn" ? positionData.moveRowsCn : positionData.moveRowsUci;
  el.historyModeLabel.textContent = state.notation === "cn" ? "中文" : "UCI";
  el.historyMoves.innerHTML = rows.map((row) => (
    `<span class="num">${row.round}.</span><span class="red">${row.red}</span><span class="black">${row.black}</span>`
  )).join("");
}

function addAudit(message, mismatch = false) {
  const stamp = new Date().toLocaleTimeString("zh-CN", { hour12: false });
  if (mismatch) state.mismatchCount += 1;
  state.auditLogs.unshift({ stamp, message, mismatch });
  state.auditLogs = state.auditLogs.slice(0, 8);
  renderAudit();
}

function resetAudit() {
  state.auditLogs = [];
  state.mismatchCount = 0;
  renderAudit();
}

function renderAudit() {
  el.mismatchCount.textContent = `不匹配 ${state.mismatchCount}`;
  el.auditLog.innerHTML = state.auditLogs.map((item) => (
    `<div class="audit-item ${item.mismatch ? "mismatch" : ""}"><span>${item.message}</span><span>${item.stamp}</span></div>`
  )).join("");
}

function setAutoMode(enabled) {
  state.autoMode = enabled;
  el.autoMode.textContent = state.autoMode ? "自动代走：开" : "自动代走：关";
  el.autoMode.classList.toggle("is-off", !state.autoMode);
  el.autoMode.setAttribute("aria-pressed", state.autoMode ? "true" : "false");
  if (!state.autoMode) clearTimeout(state.autoTimer);
  else scheduleAuto();
}

function resetAnalysis() {
  state.analysis = null;
  state.analysisKey = "";
  renderAnalysis();
}

async function runAfterAnalysis(key, action) {
  state.pendingProtectedActions.set(key, action);
  if (state.analysisInFlight || state.flushingProtectedActions) return;
  state.flushingProtectedActions = true;
  try {
    while (!state.analysisInFlight && state.pendingProtectedActions.size > 0) {
      const [[nextKey, nextAction]] = state.pendingProtectedActions;
      state.pendingProtectedActions.delete(nextKey);
      await nextAction();
    }
  } finally {
    state.flushingProtectedActions = false;
  }
}

function flushProtectedActions() {
  if (state.analysisInFlight || state.flushingProtectedActions || state.pendingProtectedActions.size === 0) return;
  state.flushingProtectedActions = true;
  (async () => {
    try {
      while (!state.analysisInFlight && state.pendingProtectedActions.size > 0) {
        const [[nextKey, nextAction]] = state.pendingProtectedActions;
        state.pendingProtectedActions.delete(nextKey);
        await nextAction();
      }
    } finally {
      state.flushingProtectedActions = false;
    }
  })().catch(showError);
}

function scheduleUndoAnalysis() {
  clearTimeout(state.undoTimer);
  state.undoTimer = setTimeout(() => {
    state.undoTimer = null;
    refreshAnalysis().then(() => scheduleAuto()).catch(showError);
  }, 500);
}

async function restoreToMoves(moves) {
  clearTimeout(state.autoTimer);
  state.generation += 1;
  state.moves = [...moves];
  state.lastMove = state.moves.at(-1) || null;
  state.selected = null;
  state.analysis = null;
  state.analysisKey = "";
  await syncPosition();
  await refreshAnalysis();
}

async function handleMismatch(message, restoreMoves = state.moves) {
  addAudit(message, true);
  if (state.mismatchHandling) return;
  state.mismatchHandling = true;
  const targetMoves = [...restoreMoves];
  try {
    clearTimeout(state.undoTimer);
    state.pendingProtectedActions.clear();
    setAutoMode(false);
    await restoreToMoves(targetMoves);
    window.alert(`检测到代走不匹配：${message}\n\n已关闭自动代走，并回到触发检查时的局面。`);
  } catch (error) {
    console.error(error);
    window.alert(`检测到代走不匹配：${message}\n\n自动代走已关闭，但回滚局面失败：${error.message}`);
  } finally {
    state.mismatchHandling = false;
  }
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
    el.wdlRed.textContent = "红胜 -";
    el.wdlDraw.textContent = "和棋 -";
    el.wdlBlack.textContent = "黑胜 -";
    return;
  }

  const best = analysis.lines[0];
  const pv = state.notation === "cn" ? best.pv_cn : best.pv;
  el.pvLine.innerHTML = pv.map((move, idx) => `<span class="move-chip ${idx % 2 === 0 ? "red" : "black"}">${move}</span>`).join("");
  el.depthText.textContent = `depth ${best.depth || "-"} / nps ${best.nps || "-"}`;
  el.nodesText.textContent = `${best.nodes || 0} nodes`;
  if (best.wdl) {
    el.wdlRed.textContent = `红胜 ${Math.round(best.wdl[0] / 10)}%`;
    el.wdlDraw.textContent = `和棋 ${Math.round(best.wdl[1] / 10)}%`;
    el.wdlBlack.textContent = `黑胜 ${Math.round(best.wdl[2] / 10)}%`;
  } else {
    el.wdlRed.textContent = "红胜 -";
    el.wdlDraw.textContent = "和棋 -";
    el.wdlBlack.textContent = "黑胜 -";
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
  state.positionId = data.positionId || "";
  state.legalMoves = data.legalMoves || [];
  state.gameOver = Boolean(data.gameOver);
  state.inCheck = Boolean(data.inCheck);
  renderBoard();
  renderStatus();
  renderHistory(data);
}

async function movePiece(move) {
  clearTimeout(state.autoTimer);
  clearTimeout(state.undoTimer);
  const previousMoves = [...state.moves];
  const previousLastMove = state.lastMove;
  const previousGeneration = state.generation;
  state.generation += 1;
  state.moves.push(move);
  state.lastMove = move;
  state.selected = null;
  state.analysis = null;
  state.analysisKey = "";
  try {
    await syncPosition();
    await refreshAnalysis();
    scheduleAuto();
  } catch (error) {
    state.moves = previousMoves;
    state.lastMove = previousLastMove;
    state.generation = previousGeneration + 1;
    state.selected = null;
    await syncPosition();
    throw error;
  }
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

function currentLimit(side = state.sideToMove) {
  const config = state.aiSearch[side];
  return {
    mode: config.mode,
    value: config.mode === "depth" ? config.depth : Math.round(config.movetime * 1000),
  };
}

function movesKey() {
  return state.moves.join(" ");
}

async function refreshAnalysis() {
  if (state.gameOver) {
    state.analysis = null;
    state.analysisKey = movesKey();
    renderAnalysis();
    return true;
  }
  const key = movesKey();
  const movesSnapshot = [...state.moves];
  const sideSnapshot = state.sideToMove;
  const generationSnapshot = state.generation;
  const positionIdSnapshot = state.positionId;
  state.analysisInFlightCount += 1;
  state.analysisInFlight = true;
  el.thinking.textContent = "思考中";
  el.engineStatus.textContent = "Pikafish thinking";
  try {
    const data = await api("/api/analyze", { moves: movesSnapshot, positionId: positionIdSnapshot, limit: currentLimit(sideSnapshot), multipv: 5 });
    if (key !== movesKey() || generationSnapshot !== state.generation) {
      addAudit("丢弃过期分析");
      return false;
    }
    if (data.positionId !== state.positionId) {
      await handleMismatch("分析 positionId 不匹配", movesSnapshot);
      return false;
    }
    state.analysis = data;
    state.analysisKey = key;
    renderAnalysis();
    el.thinking.textContent = "待命";
    el.engineStatus.textContent = "Pikafish ready";
    return true;
  } finally {
    state.analysisInFlightCount = Math.max(0, state.analysisInFlightCount - 1);
    state.analysisInFlight = state.analysisInFlightCount > 0;
    if (!state.analysisInFlight) flushProtectedActions();
  }
}

async function playAiMove() {
  if (state.gameOver) return;
  if (state.analysisInFlight) {
    await runAfterAnalysis("manual-ai", () => playAiMove());
    return;
  }
  const generationSnapshot = state.generation;
  const movesSnapshot = [...state.moves];
  if (!state.analysis || state.analysisKey !== movesKey()) {
    const refreshed = await refreshAnalysis();
    if (!refreshed) return;
  }
  if (generationSnapshot !== state.generation) {
    addAudit("代走任务过期");
    return;
  }
  if (state.analysis?.positionId === state.positionId && state.analysis?.bestmove && state.legalMoves.includes(state.analysis.bestmove)) {
    addAudit(`代走 ${state.analysis.bestmove}`);
    await movePiece(state.analysis.bestmove);
  } else if (state.analysis?.bestmove) {
    await handleMismatch("bestmove 审核失败，重新分析", movesSnapshot);
  }
}

function scheduleAuto() {
  clearTimeout(state.autoTimer);
  if (state.gameOver) return;
  if (!state.autoMode || state.players[state.sideToMove] !== "ai") return;
  if (state.analysisInFlight || !state.analysis || state.analysisKey !== movesKey()) return;
  const delay = Number(el.delayRange.value) * 1000;
  const generationSnapshot = state.generation;
  const sideSnapshot = state.sideToMove;
  state.autoTimer = setTimeout(() => {
    if (generationSnapshot === state.generation && sideSnapshot === state.sideToMove && state.autoMode && state.players[state.sideToMove] === "ai") {
      playAiMove().catch(showError);
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
  if (/positionId|illegal|bestmove|不匹配/i.test(error.message)) {
    handleMismatch(error.message, state.moves);
  }
  console.error(error);
}

function bindControls() {
  document.getElementById("newGame").addEventListener("click", () => {
    clearTimeout(state.autoTimer);
    clearTimeout(state.undoTimer);
    state.pendingProtectedActions.clear();
    state.generation += 1;
    state.moves = [];
    state.selected = null;
    state.lastMove = null;
    resetAnalysis();
    state.clocks = { red: 0, black: 0 };
    state.lastClockTick = Date.now();
    resetAudit();
    addAudit("新局");
    syncPosition().then(() => refreshAnalysis()).then(() => scheduleAuto()).catch(showError);
  });
  document.getElementById("undoMove").addEventListener("click", () => {
    clearTimeout(state.autoTimer);
    if (state.moves.length === 0) return;
    state.generation += 1;
    state.moves.pop();
    state.lastMove = state.moves.at(-1) || null;
    resetAnalysis();
    syncPosition().then(() => scheduleUndoAnalysis()).catch(showError);
  });
  document.getElementById("flipBoard").addEventListener("click", () => {
    state.flipped = !state.flipped;
    renderBoard();
  });
  el.autoMode.addEventListener("click", () => {
    runAfterAnalysis("auto-mode", async () => setAutoMode(!state.autoMode)).catch(showError);
  });
  el.manualAi.addEventListener("click", () => runAfterAnalysis("manual-ai", () => playAiMove()).catch(showError));
  el.delayRange.addEventListener("input", () => {
    runAfterAnalysis("delay", async () => {
      el.delayLabel.textContent = `${Number(el.delayRange.value).toFixed(1)}s 最小间隔`;
      scheduleAuto();
    }).catch(showError);
  });
  document.querySelectorAll(".segmented").forEach((segmented) => {
    segmented.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      runAfterAnalysis(`player-${segmented.dataset.side}`, async () => {
        const side = segmented.dataset.side;
        state.players[side] = button.dataset.player;
        segmented.querySelectorAll("button").forEach((item) => item.classList.remove("active-red", "active-black"));
        button.classList.add(side === "red" ? "active-red" : "active-black");
        renderStatus();
        scheduleAuto();
      }).catch(showError);
    });
  });
  document.querySelectorAll("[data-ai-mode-tabs]").forEach((tabs) => {
    tabs.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      runAfterAnalysis(`ai-mode-${tabs.dataset.aiModeTabs}`, async () => {
        const side = tabs.dataset.aiModeTabs;
        state.aiSearch[side].mode = button.dataset.aiMode;
        updateAiSearch(side);
      }).catch(showError);
    });
  });
  document.querySelectorAll("[data-ai-range]").forEach((range) => {
    range.addEventListener("input", () => {
      const side = range.dataset.aiRange;
      runAfterAnalysis(`ai-range-${side}`, async () => {
        const config = state.aiSearch[side];
        if (config.mode === "movetime") config.movetime = Number(range.value);
        else config.depth = Number(range.value);
        updateAiSearch(side);
      }).catch(showError);
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
setInterval(tickClock, 500);
renderAudit();
syncPosition().then(() => refreshAnalysis()).then(() => scheduleAuto()).catch(showError);

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/service-worker.js").catch((error) => {
    console.warn("service worker registration failed", error);
  });
}
