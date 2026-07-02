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


def square_name(file_idx: int, rank: int) -> str:
    return f"{FILES[file_idx]}{rank}"


def in_bounds(file_idx: int, rank: int) -> bool:
    return 0 <= file_idx < 9 and 0 <= rank < 10


def in_palace(side: str, file_idx: int, rank: int) -> bool:
    if file_idx < 3 or file_idx > 5:
        return False
    return 0 <= rank <= 2 if side == "red" else 7 <= rank <= 9


def add_if_available(board: dict[str, Piece], moves: list[str], src: str, side: str, file_idx: int, rank: int) -> None:
    if not in_bounds(file_idx, rank):
        return
    dst = square_name(file_idx, rank)
    target = board.get(dst)
    if target is None or target.side != side:
        moves.append(src + dst)


def sliding_moves(board: dict[str, Piece], src: str, side: str, cannon: bool = False) -> list[str]:
    fx, fy = parse_square(src)
    moves: list[str] = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        seen_screen = False
        x, y = fx + dx, fy + dy
        while in_bounds(x, y):
            dst = square_name(x, y)
            target = board.get(dst)
            if not cannon:
                if target is None:
                    moves.append(src + dst)
                else:
                    if target.side != side:
                        moves.append(src + dst)
                    break
            elif not seen_screen:
                if target is None:
                    moves.append(src + dst)
                else:
                    seen_screen = True
            else:
                if target is not None:
                    if target.side != side:
                        moves.append(src + dst)
                    break
            x += dx
            y += dy
    return moves


def knight_moves(board: dict[str, Piece], src: str, side: str) -> list[str]:
    fx, fy = parse_square(src)
    moves: list[str] = []
    candidates = [
        (1, 2, 0, 1), (-1, 2, 0, 1), (1, -2, 0, -1), (-1, -2, 0, -1),
        (2, 1, 1, 0), (2, -1, 1, 0), (-2, 1, -1, 0), (-2, -1, -1, 0),
    ]
    for dx, dy, lx, ly in candidates:
        leg_x, leg_y = fx + lx, fy + ly
        if not in_bounds(leg_x, leg_y):
            continue
        if square_name(leg_x, leg_y) in board:
            continue
        add_if_available(board, moves, src, side, fx + dx, fy + dy)
    return moves


def bishop_moves(board: dict[str, Piece], src: str, side: str) -> list[str]:
    fx, fy = parse_square(src)
    moves: list[str] = []
    for dx, dy in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
        tx, ty = fx + dx, fy + dy
        if not in_bounds(tx, ty):
            continue
        if side == "red" and ty > 4:
            continue
        if side == "black" and ty < 5:
            continue
        if square_name(fx + dx // 2, fy + dy // 2) in board:
            continue
        add_if_available(board, moves, src, side, tx, ty)
    return moves


def advisor_moves(board: dict[str, Piece], src: str, side: str) -> list[str]:
    fx, fy = parse_square(src)
    moves: list[str] = []
    for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        tx, ty = fx + dx, fy + dy
        if in_palace(side, tx, ty):
            add_if_available(board, moves, src, side, tx, ty)
    return moves


def king_moves(board: dict[str, Piece], src: str, side: str) -> list[str]:
    fx, fy = parse_square(src)
    moves: list[str] = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        tx, ty = fx + dx, fy + dy
        if in_palace(side, tx, ty):
            add_if_available(board, moves, src, side, tx, ty)

    dy = 1 if side == "red" else -1
    y = fy + dy
    while in_bounds(fx, y):
        target = board.get(square_name(fx, y))
        if target is not None:
            if target.role == "king" and target.side != side:
                moves.append(src + square_name(fx, y))
            break
        y += dy
    return moves


def pawn_moves(board: dict[str, Piece], src: str, side: str) -> list[str]:
    fx, fy = parse_square(src)
    moves: list[str] = []
    forward = 1 if side == "red" else -1
    add_if_available(board, moves, src, side, fx, fy + forward)
    crossed = fy >= 5 if side == "red" else fy <= 4
    if crossed:
        add_if_available(board, moves, src, side, fx - 1, fy)
        add_if_available(board, moves, src, side, fx + 1, fy)
    return moves


def legal_moves_for_piece(board: dict[str, Piece], square: str) -> list[str]:
    piece = board[square]
    if piece.role == "rook":
        return sliding_moves(board, square, piece.side)
    if piece.role == "cannon":
        return sliding_moves(board, square, piece.side, cannon=True)
    if piece.role == "knight":
        return knight_moves(board, square, piece.side)
    if piece.role == "bishop":
        return bishop_moves(board, square, piece.side)
    if piece.role == "advisor":
        return advisor_moves(board, square, piece.side)
    if piece.role == "king":
        return king_moves(board, square, piece.side)
    if piece.role == "pawn":
        return pawn_moves(board, square, piece.side)
    return []


def legal_moves(board: dict[str, Piece], side: str) -> list[str]:
    result: list[str] = []
    for square, piece in board.items():
        if piece.side == side:
            result.extend(legal_moves_for_piece(board, square))
    return sorted(result)


def validate_legal_sequence(moves: list[str]) -> None:
    board = initial_board()
    for idx, move in enumerate(moves):
        side = "red" if idx % 2 == 0 else "black"
        allowed = legal_moves(board, side)
        if move not in allowed:
            raise ValueError(f"illegal move for {side}: {move}")
        apply_move(board, move)


def apply_move(board: dict[str, Piece], move: str) -> Piece:
    validate_move(move)
    src = move[:2]
    dst = move[2:]
    piece = board.get(src)
    if piece is None:
        raise ValueError(f"no piece on source square: {src}")
    target = board.get(dst)
    if target is not None and target.side == piece.side:
        raise ValueError(f"cannot capture own piece: {dst}")
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
