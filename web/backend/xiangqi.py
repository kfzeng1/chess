from __future__ import annotations

from dataclasses import dataclass


FILES = "abcdefghi"
RED_DIGITS = "九八七六五四三二一"
BLACK_DIGITS = "123456789"


@dataclass(frozen=True)
class Piece:
    side: str
    role: str


START_BOARD: dict[str, Piece] = {
    "a0": Piece("red", "rook"),
    "b0": Piece("red", "knight"),
    "c0": Piece("red", "bishop"),
    "d0": Piece("red", "advisor"),
    "e0": Piece("red", "king"),
    "f0": Piece("red", "advisor"),
    "g0": Piece("red", "bishop"),
    "h0": Piece("red", "knight"),
    "i0": Piece("red", "rook"),
    "b2": Piece("red", "cannon"),
    "h2": Piece("red", "cannon"),
    "a3": Piece("red", "pawn"),
    "c3": Piece("red", "pawn"),
    "e3": Piece("red", "pawn"),
    "g3": Piece("red", "pawn"),
    "i3": Piece("red", "pawn"),
    "a9": Piece("black", "rook"),
    "b9": Piece("black", "knight"),
    "c9": Piece("black", "bishop"),
    "d9": Piece("black", "advisor"),
    "e9": Piece("black", "king"),
    "f9": Piece("black", "advisor"),
    "g9": Piece("black", "bishop"),
    "h9": Piece("black", "knight"),
    "i9": Piece("black", "rook"),
    "b7": Piece("black", "cannon"),
    "h7": Piece("black", "cannon"),
    "a6": Piece("black", "pawn"),
    "c6": Piece("black", "pawn"),
    "e6": Piece("black", "pawn"),
    "g6": Piece("black", "pawn"),
    "i6": Piece("black", "pawn"),
}


PIECE_LABELS = {
    ("red", "king"): "帅",
    ("red", "advisor"): "仕",
    ("red", "bishop"): "相",
    ("red", "rook"): "车",
    ("red", "knight"): "马",
    ("red", "cannon"): "炮",
    ("red", "pawn"): "兵",
    ("black", "king"): "将",
    ("black", "advisor"): "士",
    ("black", "bishop"): "象",
    ("black", "rook"): "车",
    ("black", "knight"): "马",
    ("black", "cannon"): "炮",
    ("black", "pawn"): "卒",
}


def initial_board() -> dict[str, Piece]:
    return dict(START_BOARD)


def side_to_move(moves: list[str]) -> str:
    return "red" if len(moves) % 2 == 0 else "black"


def parse_square(square: str) -> tuple[int, int]:
    if len(square) != 2 or square[0] not in FILES or square[1] not in "0123456789":
        raise ValueError(f"invalid square: {square}")
    return FILES.index(square[0]), int(square[1])


def validate_move(move: str) -> None:
    if len(move) != 4:
        raise ValueError(f"invalid move: {move}")
    parse_square(move[:2])
    parse_square(move[2:])


def apply_move(board: dict[str, Piece], move: str) -> Piece:
    validate_move(move)
    src = move[:2]
    dst = move[2:]
    piece = board.get(src)
    if piece is None:
        raise ValueError(f"no piece on source square: {src}")
    board.pop(src)
    board[dst] = piece
    return piece


def board_after(moves: list[str]) -> dict[str, Piece]:
    board = initial_board()
    for move in moves:
        apply_move(board, move)
    return board


def file_name(side: str, file_idx: int) -> str:
    return RED_DIGITS[file_idx] if side == "red" else BLACK_DIGITS[file_idx]


def step_name(side: str, delta: int) -> str:
    if side == "red":
        return RED_DIGITS[9 - delta]
    return str(delta)


def move_to_chinese(board: dict[str, Piece], move: str) -> str:
    validate_move(move)
    src = move[:2]
    dst = move[2:]
    piece = board.get(src)
    if piece is None:
        return move

    fx, fy = parse_square(src)
    tx, ty = parse_square(dst)
    label = PIECE_LABELS[(piece.side, piece.role)]
    src_file = file_name(piece.side, fx)
    dst_file = file_name(piece.side, tx)

    if piece.role in {"knight", "bishop", "advisor"}:
        forward = ty > fy if piece.side == "red" else ty < fy
        action = "进" if forward else "退"
        suffix = dst_file
    elif fx == tx:
        forward = ty > fy if piece.side == "red" else ty < fy
        action = "进" if forward else "退"
        suffix = step_name(piece.side, abs(ty - fy))
    else:
        action = "平"
        suffix = dst_file

    return f"{label}{src_file}{action}{suffix}"


def moves_to_chinese(moves: list[str]) -> list[str]:
    board = initial_board()
    result: list[str] = []
    for move in moves:
        result.append(move_to_chinese(board, move))
        apply_move(board, move)
    return result


def pv_to_chinese(history: list[str], pv: list[str]) -> list[str]:
    board = board_after(history)
    result: list[str] = []
    for move in pv:
        result.append(move_to_chinese(board, move))
        try:
            apply_move(board, move)
        except ValueError:
            pass
    return result


def move_rows(moves: list[str], notation: str = "cn") -> list[dict[str, str]]:
    shown = moves_to_chinese(moves) if notation == "cn" else moves
    rows = []
    for idx in range(0, len(shown), 2):
        rows.append({
            "round": str(idx // 2 + 1),
            "red": shown[idx],
            "black": shown[idx + 1] if idx + 1 < len(shown) else "",
        })
    return rows
