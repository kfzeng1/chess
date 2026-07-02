from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .engine import SearchLimit, fake_analysis, get_engine
from .xiangqi import START_BOARD, Piece, board_after, move_rows, moves_to_chinese, side_to_move, validate_move


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "web" / "frontend"
ASSETS_DIR = ROOT / "assets"


def piece_payload(square: str, piece: Piece) -> dict[str, str]:
    return {
        "square": square,
        "side": piece.side,
        "role": piece.role,
        "image": f"/assets/pieces/{piece.side}_{piece.role}.png",
    }


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


class XiangqiHandler(BaseHTTPRequestHandler):
    server_version = "XiangqiAI/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def do_GET(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path == "/api/state":
            self.handle_state()
            return
        self.serve_static(path)

    def do_POST(self) -> None:
        path = unquote(urlparse(self.path).path)
        try:
            if path == "/api/analyze":
                self.handle_analyze()
                return
            if path == "/api/position":
                self.handle_position()
                return
            json_response(self, 404, {"error": "not found"})
        except ValueError as exc:
            json_response(self, 400, {"error": str(exc)})
        except Exception as exc:
            json_response(self, 500, {"error": str(exc)})

    def handle_state(self) -> None:
        pieces = [piece_payload(square, piece) for square, piece in sorted(START_BOARD.items())]
        json_response(self, 200, {
            "pieces": pieces,
            "sideToMove": "red",
            "moves": [],
            "moveRows": [],
            "assets": {"board": "/assets/board.png"},
        })

    def handle_position(self) -> None:
        payload = read_json(self)
        moves = normalize_moves(payload.get("moves", []))
        board = board_after(moves)
        pieces = [piece_payload(square, piece) for square, piece in sorted(board.items())]
        json_response(self, 200, {
            "pieces": pieces,
            "sideToMove": side_to_move(moves),
            "moves": moves,
            "movesCn": moves_to_chinese(moves),
            "moveRowsCn": move_rows(moves, "cn"),
            "moveRowsUci": move_rows(moves, "uci"),
        })

    def handle_analyze(self) -> None:
        payload = read_json(self)
        moves = normalize_moves(payload.get("moves", []))
        limit = SearchLimit.from_payload(payload.get("limit"))
        multipv = int(payload.get("multipv", 5))
        if os.environ.get("XIANGQI_FAKE_ENGINE") == "1":
            analysis = fake_analysis(moves, multipv)
        else:
            analysis = get_engine().analyze(moves, limit, multipv)
        json_response(self, 200, {
            "sideToMove": side_to_move(moves),
            "limit": {"mode": limit.mode, "value": limit.value, "command": "go " + " ".join(limit.go_args())},
            **analysis,
        })

    def serve_static(self, path: str) -> None:
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
        self.wfile.write(data)


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
        httpd.server_close()


if __name__ == "__main__":
    run(
        host=os.environ.get("XIANGQI_HOST", "127.0.0.1"),
        port=int(os.environ.get("XIANGQI_PORT", "8080")),
    )
