package com.kfzeng.xiangqi.engine;

import com.kfzeng.xiangqi.core.GameState;
import com.kfzeng.xiangqi.core.Piece;

import java.util.Map;

public class AnalysisLine {
    public final int multipv;
    public final String bestMove;
    public final String scoreText;
    public final String pv;
    public final String bestMoveCn;
    public final String pvCn;
    public final int depth;
    public final long nodes;
    public final long nps;
    public final int timeMs;
    public final int[] wdl;

    public AnalysisLine(String bestMove, String scoreText, String pv) {
        this(1, bestMove, scoreText, pv, "", "", 0, 0, 0, 0, null);
    }

    public AnalysisLine(int multipv, String bestMove, String scoreText, String pv, String bestMoveCn, String pvCn,
                        int depth, long nodes, long nps, int timeMs, int[] wdl) {
        this.multipv = multipv;
        this.bestMove = bestMove == null ? "" : bestMove;
        this.scoreText = scoreText == null ? "" : scoreText;
        this.pv = pv == null ? "" : pv;
        this.bestMoveCn = bestMoveCn == null ? "" : bestMoveCn;
        this.pvCn = pvCn == null ? "" : pvCn;
        this.depth = depth;
        this.nodes = nodes;
        this.nps = nps;
        this.timeMs = timeMs;
        this.wdl = wdl;
    }

    public AnalysisLine withChinese(Map<String, Piece> board) {
        Map<String, Piece> copy = GameState.copyBoard(board);
        String bestCn = bestMove.length() == 4 ? GameState.moveToChinese(copy, bestMove) : "";
        StringBuilder cn = new StringBuilder();
        for (String move : pv.split("\\s+")) {
            if (move.length() != 4) continue;
            if (cn.length() > 0) cn.append(' ');
            cn.append(GameState.moveToChinese(copy, move));
            GameState.applyMove(copy, move);
        }
        return new AnalysisLine(multipv, bestMove, scoreText, pv, bestCn, cn.toString(), depth, nodes, nps, timeMs, wdl);
    }

    public String moveText(boolean uci) {
        if (uci || bestMoveCn.isEmpty()) return bestMove.isEmpty() ? "无" : bestMove;
        return bestMoveCn + " (" + bestMove + ")";
    }

    public String pvText(boolean uci) {
        String text = uci ? pv : pvCn;
        if (text == null || text.isEmpty()) text = uci ? bestMove : bestMoveCn;
        return text == null || text.isEmpty() ? "无主变" : text;
    }
}
