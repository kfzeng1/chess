from __future__ import annotations

import json
import os
import re
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

from web.backend.engine import SearchLimit, parse_info
from web.backend.server import XiangqiHandler
from web.backend.xiangqi import Piece, board_after, is_in_check, legal_moves, move_rows, moves_to_chinese, side_to_move, validate_legal_sequence


ROOT = Path(__file__).resolve().parents[1]


class XiangqiCoreTest(unittest.TestCase):
    def test_side_to_move_counts_each_move_as_one_round(self) -> None:
        self.assertEqual(side_to_move([]), "red")
        self.assertEqual(side_to_move(["h2e2"]), "black")
        self.assertEqual(side_to_move(["h2e2", "h9g7"]), "red")

    def test_chinese_notation_is_generated_from_board_state(self) -> None:
        self.assertEqual(moves_to_chinese(["h2e2"])[0], "炮二平五")
        rows = move_rows(["h2e2", "h9g7"], "cn")
        self.assertEqual(rows[0]["red"], "炮二平五")
        self.assertEqual(rows[0]["black"], "马8进7")

    def test_board_after_applies_capture_or_move(self) -> None:
        board = board_after(["h2e2"])
        self.assertNotIn("h2", board)
        self.assertEqual(board["e2"].role, "cannon")

    def test_initial_legal_moves_include_common_openings(self) -> None:
        moves = legal_moves(board_after([]), "red")
        self.assertIn("h2e2", moves)
        self.assertIn("c3c4", moves)
        self.assertIn("b0c2", moves)

    def test_legal_sequence_rejects_own_capture(self) -> None:
        validate_legal_sequence(["h2e2", "h9g7"])
        with self.assertRaises(ValueError):
            validate_legal_sequence(["h2h0"])

    def test_legal_moves_filter_flying_general_check(self) -> None:
        board = {
            "e0": Piece("red", "king"),
            "e9": Piece("black", "king"),
        }
        self.assertTrue(is_in_check(board, "red"))
        moves = legal_moves(board, "red")
        self.assertIn("e0d0", moves)
        self.assertIn("e0f0", moves)
        self.assertNotIn("e0e1", moves)


class EngineParsingTest(unittest.TestCase):
    def test_parse_info_line_with_wdl_and_pv(self) -> None:
        line = "info depth 12 seldepth 18 multipv 2 score cp 21 wdl 59 927 14 nodes 2000 nps 50000 pv g3g4 h7g7 b2e2"
        parsed = parse_info(line)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["multipv"], 2)
        self.assertEqual(parsed["score"]["display"], "红方 +0.21")
        self.assertEqual(parsed["score"]["value"], 21)
        self.assertEqual(parsed["score"]["engineValue"], 21)
        self.assertEqual(parsed["score"]["engineSide"], "red")
        self.assertEqual(parsed["wdl"], [59, 927, 14])
        self.assertEqual(parsed["pv"], ["g3g4", "h7g7", "b2e2"])

    def test_parse_info_line_normalizes_black_score_to_red_pov(self) -> None:
        line = "info depth 12 multipv 1 score cp 24 wdl 64 923 13 nodes 2000 nps 50000 pv h9g7 h2e2"
        parsed = parse_info(line, "black")
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["score"]["value"], -24)
        self.assertEqual(parsed["score"]["display"], "黑方 +0.24")
        self.assertEqual(parsed["score"]["engineValue"], 24)
        self.assertEqual(parsed["score"]["engineSide"], "black")
        self.assertEqual(parsed["wdl"], [13, 923, 64])

    def test_parse_info_line_normalizes_black_mate_to_red_pov(self) -> None:
        black_mates = parse_info("info depth 8 score mate 3 pv h9g7", "black")
        red_mates = parse_info("info depth 8 score mate -2 pv h9g7", "black")
        self.assertIsNotNone(black_mates)
        self.assertIsNotNone(red_mates)
        assert black_mates is not None
        assert red_mates is not None
        self.assertEqual(black_mates["score"]["display"], "黑方 M3")
        self.assertEqual(red_mates["score"]["display"], "红方 M2")

    def test_search_limit_clamps_values(self) -> None:
        self.assertEqual(SearchLimit.from_payload({"mode": "depth", "value": 99}).go_args(), ["depth", "30"])
        self.assertEqual(SearchLimit.from_payload({"mode": "movetime", "value": 1}).go_args(), ["movetime", "50"])


class ServerApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["XIANGQI_FAKE_ENGINE"] = "1"
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), XiangqiHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        os.environ.pop("XIANGQI_FAKE_ENGINE", None)

    def request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        return response.status, data

    def test_state_endpoint(self) -> None:
        status, data = self.request("GET", "/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(data["sideToMove"], "red")
        self.assertEqual(data["positionId"], "e3b0c44298fc1c14")
        self.assertEqual(len(data["pieces"]), 32)
        self.assertFalse(data["gameOver"])

    def test_health_endpoint(self) -> None:
        status, data = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["engine"], "fake")

    def test_static_frontend_assets(self) -> None:
        for path in ["/", "/style.css", "/app.js", "/manifest.webmanifest", "/service-worker.js", "/assets/board.png"]:
            conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
            conn.request("GET", path)
            response = conn.getresponse()
            response.read()
            conn.close()
            self.assertEqual(response.status, 200, path)

    def test_static_head_request(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("HEAD", "/manifest.webmanifest")
        response = conn.getresponse()
        response.read()
        conn.close()
        self.assertEqual(response.status, 200)

    def test_position_endpoint(self) -> None:
        status, data = self.request("POST", "/api/position", {"moves": ["h2e2"]})
        self.assertEqual(status, 200)
        self.assertEqual(data["sideToMove"], "black")
        self.assertEqual(data["movesCn"], ["炮二平五"])
        self.assertIn("positionId", data)
        self.assertIn("h9g7", data["legalMoves"])
        self.assertFalse(data["gameOver"])

    def test_position_endpoint_rejects_illegal_history(self) -> None:
        status, data = self.request("POST", "/api/position", {"moves": ["h2h0"]})
        self.assertEqual(status, 400)
        self.assertIn("illegal move", data["error"])

    def test_analyze_endpoint_fake_engine(self) -> None:
        status, data = self.request("POST", "/api/analyze", {
            "moves": [],
            "positionId": "e3b0c44298fc1c14",
            "limit": {"mode": "movetime", "value": 100},
            "multipv": 3,
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["limit"]["command"], "go movetime 100")
        self.assertEqual(len(data["lines"]), 3)
        self.assertIn("pv_cn", data["lines"][0])

    def test_analyze_endpoint_rejects_mismatched_position_id(self) -> None:
        status, data = self.request("POST", "/api/analyze", {
            "moves": [],
            "positionId": "wrong",
            "limit": {"mode": "movetime", "value": 100},
            "multipv": 1,
        })
        self.assertEqual(status, 400)
        self.assertIn("positionId", data["error"])

    def test_analyze_endpoint_fake_engine_uses_current_side(self) -> None:
        status, data = self.request("POST", "/api/analyze", {
            "moves": ["h2e2"],
            "limit": {"mode": "movetime", "value": 100},
            "multipv": 3,
        })
        self.assertEqual(status, 200)
        self.assertTrue(data["bestmove"][1].isdigit())
        self.assertIn(data["bestmove"][:2], {"a6", "b7", "b9", "c6", "c9", "d9", "e6", "e9", "f9", "g6", "g9", "h7", "h9", "i6", "a9", "i9"})


class FrontendReferenceTest(unittest.TestCase):
    def test_index_references_existing_frontend_files(self) -> None:
        html = (ROOT / "web" / "frontend" / "index.html").read_text(encoding="utf-8")
        refs = re.findall(r'href="(/[^"]+)"|src="(/[^"]+)"', html)
        paths = [match[0] or match[1] for match in refs]
        for path in paths:
            if path.startswith("/assets/"):
                self.assertTrue((ROOT / path.lstrip("/")).exists(), path)
            elif path.startswith("/"):
                self.assertTrue((ROOT / "web" / "frontend" / path.lstrip("/")).exists(), path)

    def test_manifest_icon_exists(self) -> None:
        manifest = json.loads((ROOT / "web" / "frontend" / "manifest.webmanifest").read_text(encoding="utf-8"))
        for icon in manifest["icons"]:
            self.assertTrue((ROOT / icon["src"].lstrip("/")).exists(), icon["src"])


if __name__ == "__main__":
    unittest.main()
