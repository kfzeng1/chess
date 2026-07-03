from __future__ import annotations

import json
import mimetypes
import os
import hashlib
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .engine import SearchLimit, close_global_engine, fake_analysis, get_engine
from .xiangqi import START_BOARD, Piece, board_after, is_in_check, legal_moves, move_rows, moves_to_chinese, side_to_move, validate_legal_sequence, validate_move


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "web" / "frontend"
ASSETS_DIR = ROOT / "assets"
LOG_DIR = ROOT / "logs"
EVENT_LOG = LOG_DIR / "game-events.jsonl"


def piece_payload(square: str, piece: Piece) -> dict[str, str]:
    return {
        "square": square,
        "side": piece.side,
        "role": piece.role,
        "image": f"/assets/pieces/{piece.side}_{piece.role}.png",
    }


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
    except (BrokenPipeError, ConnectionResetError):
        return


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


def position_id(moves: list[str]) -> str:
    raw = "\n".join(moves).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def write_event(payload: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": time.time(),
        **payload,
    }
    with EVENT_LOG.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


class XiangqiHandler(BaseHTTPRequestHandler):
    server_version = "XiangqiAI/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def do_GET(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path == "/api/health":
            self.handle_health()
            return
        if path == "/api/state":
            self.handle_state()
            return
        self.serve_static(path)

    def do_HEAD(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path.startswith("/api/"):
            self.send_response(405)
            self.end_headers()
            return
        self.serve_static(path, head_only=True)

    def do_POST(self) -> None:
        path = unquote(urlparse(self.path).path)
        try:
            if path == "/api/analyze":
                self.handle_analyze()
                return
            if path == "/api/position":
                self.handle_position()
                return
            if path == "/api/log":
                self.handle_log()
                return
            json_response(self, 404, {"error": "not found"})
        except (BrokenPipeError, ConnectionResetError):
            return
        except ValueError as exc:
            json_response(self, 400, {"error": str(exc)})
        except Exception as exc:
            json_response(self, 500, {"error": str(exc)})

    def handle_state(self) -> None:
        pieces = [piece_payload(square, piece) for square, piece in sorted(START_BOARD.items())]
        initial_legal = legal_moves(dict(START_BOARD), "red")
        json_response(self, 200, {
            "pieces": pieces,
            "sideToMove": "red",
            "moves": [],
            "positionId": position_id([]),
            "legalMoves": initial_legal,
            "gameOver": len(initial_legal) == 0,
            "inCheck": False,
            "moveRows": [],
            "assets": {"board": "/assets/board.png"},
        })

    def handle_health(self) -> None:
        json_response(self, 200, {
            "ok": True,
            "engine": "fake" if os.environ.get("XIANGQI_FAKE_ENGINE") == "1" else "pikafish",
            "version": "0.1",
        })

    def handle_position(self) -> None:
        payload = read_json(self)
        moves = normalize_moves(payload.get("moves", []))
        validate_legal_sequence(moves)
        pos_id = position_id(moves)
        board = board_after(moves)
        turn = side_to_move(moves)
        allowed = legal_moves(board, turn)
        in_check = is_in_check(board, turn)
        pieces = [piece_payload(square, piece) for square, piece in sorted(board.items())]
        json_response(self, 200, {
            "pieces": pieces,
            "sideToMove": turn,
            "moves": moves,
            "positionId": pos_id,
            "legalMoves": allowed,
            "gameOver": len(allowed) == 0,
            "inCheck": in_check,
            "movesCn": moves_to_chinese(moves),
            "moveRowsCn": move_rows(moves, "cn"),
            "moveRowsUci": move_rows(moves, "uci"),
        })

    def handle_analyze(self) -> None:
        payload = read_json(self)
        moves = normalize_moves(payload.get("moves", []))
        validate_legal_sequence(moves)
        pos_id = position_id(moves)
        expected_position_id = payload.get("positionId")
        if expected_position_id is not None and str(expected_position_id) != pos_id:
            raise ValueError("positionId does not match moves")
        limit = SearchLimit.from_payload(payload.get("limit"))
        multipv = int(payload.get("multipv", 5))
        if os.environ.get("XIANGQI_FAKE_ENGINE") == "1":
            analysis = fake_analysis(moves, multipv)
        else:
            analysis = get_engine().analyze(moves, limit, multipv)
        json_response(self, 200, {
            "sideToMove": side_to_move(moves),
            "positionId": pos_id,
            "limit": {"mode": limit.mode, "value": limit.value, "command": "go " + " ".join(limit.go_args())},
            **analysis,
        })

    def handle_log(self) -> None:
        payload = read_json(self)
        if not isinstance(payload, dict):
            raise ValueError("log payload must be an object")
        write_event(payload)
        json_response(self, 200, {"ok": True})

    def serve_static(self, path: str, head_only: bool = False) -> None:
        if path in {"", "/"}:
            file_path = FRONTEND_DIR / "index.html"
        elif path.startswith("/assets/"):
            file_path = ASSETS_DIR / path.removeprefix("/assets/")
        else:
            file_path = FRONTEND_DIR / path.lstrip("/")

        try:
            resolved = file_path.resolve()
            allowed = (FRONTEND_DIR.resolve(), ASSETS_DIR.resolve())
            if not any(resolved == base or base in resolved.parents for base in allowed):
                raise FileNotFoundError
            data = resolved.read_bytes()
        except FileNotFoundError:
            json_response(self, 404, {"error": "not found"})
            return

        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head_only:
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                return


def normalize_moves(raw_moves: Any) -> list[str]:
    if not isinstance(raw_moves, list):
        raise ValueError("moves must be a list")
    moves = [str(move) for move in raw_moves]
    for move in moves:
        validate_move(move)
    return moves


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    httpd = ThreadingHTTPServer((host, port), XiangqiHandler)
    print(f"Xiangqi AI web app: http://{host}:{port}")
    try:
        httpd.serve_forever()
    finally:
        close_global_engine()
        httpd.server_close()


if __name__ == "__main__":
    run(
        host=os.environ.get("XIANGQI_HOST", "127.0.0.1"),
        port=int(os.environ.get("XIANGQI_PORT", "8080")),
    )
