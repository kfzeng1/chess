package com.kfzeng.xiangqi.core;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class GameState {
    public static final String FILES = "abcdefghi";
    public final Map<String, Piece> board = new HashMap<>();
    public final ArrayList<String> moves = new ArrayList<>();
    private final ArrayDeque<Map<String, Piece>> history = new ArrayDeque<>();
    public String lastMove;

    public void reset() {
        board.clear();
        moves.clear();
        history.clear();
        lastMove = null;
        put("a0","red","rook"); put("b0","red","knight"); put("c0","red","bishop"); put("d0","red","advisor"); put("e0","red","king"); put("f0","red","advisor"); put("g0","red","bishop"); put("h0","red","knight"); put("i0","red","rook");
        put("b2","red","cannon"); put("h2","red","cannon"); put("a3","red","pawn"); put("c3","red","pawn"); put("e3","red","pawn"); put("g3","red","pawn"); put("i3","red","pawn");
        put("a9","black","rook"); put("b9","black","knight"); put("c9","black","bishop"); put("d9","black","advisor"); put("e9","black","king"); put("f9","black","advisor"); put("g9","black","bishop"); put("h9","black","knight"); put("i9","black","rook");
        put("b7","black","cannon"); put("h7","black","cannon"); put("a6","black","pawn"); put("c6","black","pawn"); put("e6","black","pawn"); put("g6","black","pawn"); put("i6","black","pawn");
    }

    private void put(String square, String side, String role) {
        board.put(square, new Piece(side, role));
    }

    public String sideToMove() {
        return moves.size() % 2 == 0 ? "red" : "black";
    }

    public void applyMove(String move) {
        history.push(new HashMap<>(board));
        Piece piece = board.remove(move.substring(0, 2));
        if (piece != null) board.put(move.substring(2, 4), piece);
        moves.add(move);
        lastMove = move;
    }

    public void undo() {
        if (history.isEmpty()) return;
        board.clear();
        board.putAll(history.pop());
        if (!moves.isEmpty()) moves.remove(moves.size() - 1);
        lastMove = moves.isEmpty() ? null : moves.get(moves.size() - 1);
    }

    public Map<String, Piece> boardSnapshot() {
        return copyBoard(board);
    }

    public String movesText(boolean uci) {
        if (moves.isEmpty()) return "尚未走子";
        if (uci) return String.join(" ", moves);
        Map<String, Piece> copy = new HashMap<>();
        GameState initial = new GameState();
        initial.reset();
        copy.putAll(initial.board);
        ArrayList<String> cn = new ArrayList<>();
        for (String move : moves) {
            cn.add(moveToChinese(copy, move));
            applyMove(copy, move);
        }
        return String.join(" ", cn);
    }

    public List<String> legalMoves() {
        ArrayList<String> result = new ArrayList<>();
        String side = sideToMove();
        for (String move : pseudoLegalMoves(board, side)) {
            Map<String, Piece> next = copyBoard(board);
            applyMove(next, move);
            if (!isInCheck(next, side)) result.add(move);
        }
        return result;
    }

    private List<String> pseudoLegalMoves() {
        ArrayList<String> result = new ArrayList<>();
        String side = sideToMove();
        for (String square : new ArrayList<>(board.keySet())) {
            Piece piece = board.get(square);
            if (piece != null && piece.side.equals(side)) pieceMoves(square, piece, result);
        }
        return result;
    }

    private void pieceMoves(String square, Piece piece, List<String> out) {
        int file = FILES.indexOf(square.charAt(0));
        int rank = Character.digit(square.charAt(1), 10);
        switch (piece.role) {
            case "rook":
                slide(square, piece, out, false);
                break;
            case "cannon":
                slide(square, piece, out, true);
                break;
            case "knight":
                for (int[] move : new int[][]{{1,2,0,1},{-1,2,0,1},{1,-2,0,-1},{-1,-2,0,-1},{2,1,1,0},{2,-1,1,0},{-2,1,-1,0},{-2,-1,-1,0}}) {
                    if (!board.containsKey(name(file + move[2], rank + move[3]))) add(square, piece, file + move[0], rank + move[1], out);
                }
                break;
            case "bishop":
                for (int[] move : new int[][]{{2,2},{-2,2},{2,-2},{-2,-2}}) {
                    int targetRank = rank + move[1];
                    if ((piece.side.equals("red") && targetRank > 4) || (piece.side.equals("black") && targetRank < 5)) continue;
                    if (!board.containsKey(name(file + move[0] / 2, rank + move[1] / 2))) add(square, piece, file + move[0], targetRank, out);
                }
                break;
            case "advisor":
                for (int[] move : new int[][]{{1,1},{-1,1},{1,-1},{-1,-1}}) {
                    if (palace(piece.side, file + move[0], rank + move[1])) add(square, piece, file + move[0], rank + move[1], out);
                }
                break;
            case "king":
                for (int[] move : new int[][]{{1,0},{-1,0},{0,1},{0,-1}}) {
                    if (palace(piece.side, file + move[0], rank + move[1])) add(square, piece, file + move[0], rank + move[1], out);
                }
                int dy = piece.side.equals("red") ? 1 : -1;
                int y = rank + dy;
                while (inside(file, y)) {
                    Piece target = board.get(name(file, y));
                    if (target != null) {
                        if (!target.side.equals(piece.side) && "king".equals(target.role)) out.add(square + name(file, y));
                        break;
                    }
                    y += dy;
                }
                break;
            case "pawn":
                int forward = piece.side.equals("red") ? 1 : -1;
                add(square, piece, file, rank + forward, out);
                boolean crossed = piece.side.equals("red") ? rank >= 5 : rank <= 4;
                if (crossed) {
                    add(square, piece, file - 1, rank, out);
                    add(square, piece, file + 1, rank, out);
                }
                break;
        }
    }

    private void slide(String square, Piece piece, List<String> out, boolean cannon) {
        int file = FILES.indexOf(square.charAt(0));
        int rank = Character.digit(square.charAt(1), 10);
        for (int[] direction : new int[][]{{1,0},{-1,0},{0,1},{0,-1}}) {
            boolean screen = false;
            int x = file + direction[0];
            int y = rank + direction[1];
            while (inside(x, y)) {
                Piece target = board.get(name(x, y));
                if (!cannon) {
                    if (target == null) out.add(square + name(x, y));
                    else {
                        if (!target.side.equals(piece.side)) out.add(square + name(x, y));
                        break;
                    }
                } else if (!screen) {
                    if (target == null) out.add(square + name(x, y));
                    else screen = true;
                } else {
                    if (target != null) {
                        if (!target.side.equals(piece.side)) out.add(square + name(x, y));
                        break;
                    }
                }
                x += direction[0];
                y += direction[1];
            }
        }
    }

    private void add(String square, Piece piece, int file, int rank, List<String> out) {
        if (!inside(file, rank)) return;
        Piece target = board.get(name(file, rank));
        if (target == null || !target.side.equals(piece.side)) out.add(square + name(file, rank));
    }

    private boolean palace(String side, int file, int rank) {
        return file >= 3 && file <= 5 && (side.equals("red") ? rank >= 0 && rank <= 2 : rank >= 7 && rank <= 9);
    }

    private boolean inside(int file, int rank) {
        return file >= 0 && file < 9 && rank >= 0 && rank < 10;
    }

    private String name(int file, int rank) {
        if (!inside(file, rank)) return "";
        return "" + FILES.charAt(file) + rank;
    }

    public static Map<String, Piece> copyBoard(Map<String, Piece> source) {
        return new HashMap<>(source);
    }

    public static List<String> pseudoLegalMoves(Map<String, Piece> source, String side) {
        GameState temp = new GameState();
        temp.board.clear();
        temp.board.putAll(source);
        ArrayList<String> result = new ArrayList<>();
        for (String square : new ArrayList<>(temp.board.keySet())) {
            Piece piece = temp.board.get(square);
            if (piece != null && piece.side.equals(side)) temp.pieceMoves(square, piece, result);
        }
        return result;
    }

    public static boolean isInCheck(Map<String, Piece> source, String side) {
        String kingSquare = null;
        for (Map.Entry<String, Piece> entry : source.entrySet()) {
            Piece piece = entry.getValue();
            if (piece.side.equals(side) && "king".equals(piece.role)) {
                kingSquare = entry.getKey();
                break;
            }
        }
        if (kingSquare == null) return true;
        String enemy = side.equals("red") ? "black" : "red";
        for (String move : pseudoLegalMoves(source, enemy)) {
            if (move.substring(2, 4).equals(kingSquare)) return true;
        }
        return false;
    }

    public static void applyMove(Map<String, Piece> board, String move) {
        Piece piece = board.remove(move.substring(0, 2));
        if (piece != null) board.put(move.substring(2, 4), piece);
    }

    public static String moveToChinese(Map<String, Piece> board, String move) {
        if (move == null || move.length() != 4) return "";
        Piece piece = board.get(move.substring(0, 2));
        if (piece == null) return move;
        int fx = FILES.indexOf(move.charAt(0));
        int fy = Character.digit(move.charAt(1), 10);
        int tx = FILES.indexOf(move.charAt(2));
        int ty = Character.digit(move.charAt(3), 10);
        String label = label(piece);
        String srcFile = fileName(piece.side, fx);
        String dstFile = fileName(piece.side, tx);
        String action;
        String suffix;
        if ("knight".equals(piece.role) || "bishop".equals(piece.role) || "advisor".equals(piece.role)) {
            boolean forward = piece.side.equals("red") ? ty > fy : ty < fy;
            action = forward ? "进" : "退";
            suffix = dstFile;
        } else if (fx == tx) {
            boolean forward = piece.side.equals("red") ? ty > fy : ty < fy;
            action = forward ? "进" : "退";
            suffix = stepName(piece.side, Math.abs(ty - fy));
        } else {
            action = "平";
            suffix = dstFile;
        }
        return label + srcFile + action + suffix;
    }

    public static String label(Piece piece) {
        if ("king".equals(piece.role)) return piece.side.equals("red") ? "帅" : "将";
        if ("advisor".equals(piece.role)) return piece.side.equals("red") ? "仕" : "士";
        if ("bishop".equals(piece.role)) return piece.side.equals("red") ? "相" : "象";
        if ("rook".equals(piece.role)) return "车";
        if ("knight".equals(piece.role)) return "马";
        if ("cannon".equals(piece.role)) return "炮";
        return piece.side.equals("red") ? "兵" : "卒";
    }

    private static String fileName(String side, int file) {
        String redDigits = "九八七六五四三二一";
        return side.equals("red") ? String.valueOf(redDigits.charAt(file)) : String.valueOf(file + 1);
    }

    private static String stepName(String side, int delta) {
        String redDigits = "九八七六五四三二一";
        return side.equals("red") ? String.valueOf(redDigits.charAt(9 - delta)) : String.valueOf(delta);
    }
}
