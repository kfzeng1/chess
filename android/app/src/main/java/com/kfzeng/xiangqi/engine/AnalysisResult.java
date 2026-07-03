package com.kfzeng.xiangqi.engine;

import com.kfzeng.xiangqi.core.Piece;

import java.util.ArrayList;
import java.util.Map;

public class AnalysisResult {
    public final ArrayList<AnalysisLine> lines;
    public final String bestMove;
    public final String bestMoveCn;
    public final String scoreText;
    public final String pv;
    public final String pvCn;
    public final int[] wdl;

    public AnalysisResult(ArrayList<AnalysisLine> lines, int[] wdl) {
        this.lines = lines == null ? new ArrayList<>() : lines;
        AnalysisLine best = this.lines.isEmpty() ? new AnalysisLine("", "", "") : this.lines.get(0);
        this.bestMove = best.bestMove;
        this.bestMoveCn = best.bestMoveCn;
        this.scoreText = best.scoreText;
        this.pv = best.pv;
        this.pvCn = best.pvCn;
        this.wdl = wdl != null ? wdl : best.wdl;
    }

    public AnalysisResult withChinese(Map<String, Piece> board) {
        ArrayList<AnalysisLine> translated = new ArrayList<>();
        for (AnalysisLine line : lines) translated.add(line.withChinese(board));
        return new AnalysisResult(translated, wdl);
    }

    public String bestMoveText(boolean uci) {
        return lines.isEmpty() ? "无" : lines.get(0).moveText(uci);
    }

    public String pvText(boolean uci) {
        return lines.isEmpty() ? "无主变" : lines.get(0).pvText(uci);
    }

    public String summary(boolean uci) {
        String score = scoreText.isEmpty() ? "无分数" : scoreText;
        return "推荐 " + bestMoveText(uci) + "，" + score + "，主变 " + pvText(uci);
    }
}
