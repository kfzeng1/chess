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
from web.backend.xiangqi import board_after, move_rows, moves_to_chinese, side_to_move


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


class EngineParsingTest(unittest.TestCase):
    def test_parse_info_line_with_wdl_and_pv(self) -> None:
        line = "info depth 12 seldepth 18 multipv 2 score cp 21 wdl 59 927 14 nodes 2000 nps 50000 pv g3g4 h7g7 b2e2"
        parsed = parse_info(line)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["multipv"], 2)
        self.assertEqual(parsed["score"]["display"], "红方 +0.21")
        self.assertEqual(parsed["wdl"], [59, 927, 14])
        self.assertEqual(parsed["pv"], ["g3g4", "h7g7", "b2e2"])

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
        self.assertEqual(len(data["pieces"]), 32)

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

    def test_analyze_endpoint_fake_engine(self) -> None:
        status, data = self.request("POST", "/api/analyze", {
            "moves": [],
            "limit": {"mode": "movetime", "value": 100},
            "multipv": 3,
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["limit"]["command"], "go movetime 100")
        self.assertEqual(len(data["lines"]), 3)
        self.assertIn("pv_cn", data["lines"][0])


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
