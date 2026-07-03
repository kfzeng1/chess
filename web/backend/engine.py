from __future__ import annotations

import os
import re
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .xiangqi import apply_move, board_after, legal_moves, pv_to_chinese, side_to_move


ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = ROOT / "engines" / "pikafish-avxvnni"
ENGINE_CWD = ROOT / "engines"

INFO_RE = re.compile(r"\bmultipv\s+(\d+)\b")
SCORE_RE = re.compile(r"\bscore\s+(cp|mate)\s+(-?\d+)\b")
WDL_RE = re.compile(r"\bwdl\s+(\d+)\s+(\d+)\s+(\d+)\b")
PV_RE = re.compile(r"\bpv\s+(.+)$")
DEPTH_RE = re.compile(r"\bdepth\s+(\d+)\b")
NODES_RE = re.compile(r"\bnodes\s+(\d+)\b")
NPS_RE = re.compile(r"\bnps\s+(\d+)\b")


@dataclass
class SearchLimit:
    mode: str
    value: float

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "SearchLimit":
        if not payload:
            return cls("movetime", 1000)
        mode = str(payload.get("mode", "movetime"))
        value = float(payload.get("value", 1000))
        if mode == "depth":
            return cls("depth", max(1, min(30, int(value))))
        if mode == "movetime":
            return cls("movetime", max(50, min(30000, int(value))))
        raise ValueError(f"unsupported search mode: {mode}")

    def go_args(self) -> list[str]:
        if self.mode == "depth":
            return ["depth", str(int(self.value))]
        return ["movetime", str(int(self.value))]


class Pikafish:
    def __init__(self, path: Path = ENGINE_PATH) -> None:
        if not path.exists():
            raise FileNotFoundError(path)
        self.path = path
        self._lock = threading.Lock()
        self._proc = subprocess.Popen(
            [str(path)],
            cwd=str(ENGINE_CWD),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._send("uci")
        self._read_until("uciok")
        self._send("setoption name UCI_ShowWDL value true")
        self._send("isready")
        self._read_until("readyok")

    def close(self) -> None:
        if self._proc.poll() is None:
            try:
                self._send("quit")
            finally:
                self._proc.terminate()

    def _send(self, command: str) -> None:
        if self._proc.stdin is None:
            raise RuntimeError("engine stdin closed")
        self._proc.stdin.write(command + "\n")
        self._proc.stdin.flush()

    def _readline(self) -> str:
        if self._proc.stdout is None:
            raise RuntimeError("engine stdout closed")
        line = self._proc.stdout.readline()
        if line == "":
            raise RuntimeError("engine stopped")
        return line.strip()

    def _read_until(self, marker: str) -> list[str]:
        lines = []
        while True:
            line = self._readline()
            lines.append(line)
            if line == marker:
                return lines

    def analyze(self, moves: list[str], limit: SearchLimit, multipv: int = 5) -> dict[str, Any]:
        multipv = max(1, min(10, int(multipv)))
        with self._lock:
            self._send(f"setoption name MultiPV value {multipv}")
            self._send("isready")
            self._read_until("readyok")
            position = "position startpos"
            if moves:
                position += " moves " + " ".join(moves)
            self._send(position)
            self._send("go " + " ".join(limit.go_args()))

            infos: dict[int, dict[str, Any]] = {}
            bestmove = None
            while True:
                line = self._readline()
                if line.startswith("bestmove"):
                    parts = line.split()
                    bestmove = parts[1] if len(parts) > 1 else None
                    break
                if line.startswith("info"):
                    parsed = parse_info(line, side_to_move(moves))
                    if parsed:
                        infos[parsed["multipv"]] = parsed

        lines = []
        for idx in sorted(infos):
            info = infos[idx]
            pv = info.get("pv", [])
            lines.append({
                **info,
                "bestmove": pv[0] if pv else "",
                "pv_cn": pv_to_chinese(moves, pv) if pv else [],
            })

        return {
            "bestmove": bestmove,
            "bestmove_cn": pv_to_chinese(moves, [bestmove])[0] if bestmove else "",
            "lines": lines,
        }


def parse_info(line: str, score_side: str = "red") -> dict[str, Any] | None:
    multipv_match = INFO_RE.search(line)
    pv_match = PV_RE.search(line)
    if not pv_match:
        return None

    multipv = int(multipv_match.group(1)) if multipv_match else 1
    score_match = SCORE_RE.search(line)
    wdl_match = WDL_RE.search(line)
    depth_match = DEPTH_RE.search(line)
    nodes_match = NODES_RE.search(line)
    nps_match = NPS_RE.search(line)

    score = None
    if score_match:
        kind = score_match.group(1)
        raw_value = int(score_match.group(2))
        red_value = score_to_red_pov(kind, raw_value, score_side)
        score = {
            "type": kind,
            "value": red_value,
            "display": format_score(kind, red_value),
            "engineValue": raw_value,
            "engineSide": score_side,
        }

    wdl = None
    if wdl_match:
        raw_wdl = [int(wdl_match.group(1)), int(wdl_match.group(2)), int(wdl_match.group(3))]
        wdl = raw_wdl if score_side == "red" else [raw_wdl[2], raw_wdl[1], raw_wdl[0]]

    return {
        "multipv": multipv,
        "depth": int(depth_match.group(1)) if depth_match else None,
        "nodes": int(nodes_match.group(1)) if nodes_match else None,
        "nps": int(nps_match.group(1)) if nps_match else None,
        "score": score,
        "wdl": wdl,
        "pv": pv_match.group(1).split(),
    }


def score_to_red_pov(kind: str, value: int, score_side: str) -> int:
    if score_side not in {"red", "black"}:
        raise ValueError(f"unsupported score side: {score_side}")
    return value if score_side == "red" else -value


def format_score(kind: str, value: int) -> str:
    if kind == "mate":
        return f"红方 M{value}" if value > 0 else f"黑方 M{abs(value)}"
    pawns = value / 100
    if pawns >= 0:
        return f"红方 +{pawns:.2f}"
    return f"黑方 +{abs(pawns):.2f}"


_ENGINE: Pikafish | None = None


def get_engine() -> Pikafish:
    global _ENGINE
    if os.environ.get("XIANGQI_FAKE_ENGINE") == "1":
        raise RuntimeError("fake engine mode should bypass get_engine")
    if _ENGINE is None:
        _ENGINE = Pikafish()
    return _ENGINE


def close_global_engine() -> None:
    global _ENGINE
    if _ENGINE is not None:
        _ENGINE.close()
        _ENGINE = None


def fake_analysis(moves: list[str], multipv: int = 5) -> dict[str, Any]:
    board = board_after(moves)
    side = side_to_move(moves)
    candidates = legal_moves(board, side)[:multipv]
    lines = []
    for idx, move in enumerate(candidates, start=1):
        pv = build_fake_pv(moves, move)
        lines.append({
            "multipv": idx,
            "depth": 12,
            "nodes": 1000 * idx,
            "nps": 50000,
            "score": fake_score(24 - idx, side),
            "wdl": fake_wdl([64 - idx, 923 + idx, 13], side),
            "pv": pv,
            "bestmove": move,
            "pv_cn": pv_to_chinese(moves, pv),
        })
    return {
        "bestmove": candidates[0] if candidates else "",
        "bestmove_cn": pv_to_chinese(moves, [candidates[0]])[0] if candidates else "",
        "lines": lines,
    }


def fake_score(raw_value: int, score_side: str) -> dict[str, Any]:
    red_value = score_to_red_pov("cp", raw_value, score_side)
    return {
        "type": "cp",
        "value": red_value,
        "display": format_score("cp", red_value),
        "engineValue": raw_value,
        "engineSide": score_side,
    }


def fake_wdl(raw_wdl: list[int], score_side: str) -> list[int]:
    return raw_wdl if score_side == "red" else [raw_wdl[2], raw_wdl[1], raw_wdl[0]]


def build_fake_pv(history: list[str], first_move: str, length: int = 3) -> list[str]:
    board = board_after(history)
    pv = [first_move]
    apply_move(board, first_move)
    side = "black" if side_to_move(history) == "red" else "red"
    while len(pv) < length:
        options = legal_moves(board, side)
        if not options:
            break
        move = options[0]
        pv.append(move)
        apply_move(board, move)
        side = "black" if side == "red" else "red"
    return pv
