package com.kfzeng.xiangqi.engine;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class PikafishEngine {
    private static final Pattern MULTIPV_RE = Pattern.compile("\\bmultipv\\s+(\\d+)\\b");
    private static final Pattern SCORE_RE = Pattern.compile("\\bscore\\s+(cp|mate)\\s+(-?\\d+)(?:\\s+(lowerbound|upperbound))?\\b");
    private static final Pattern WDL_RE = Pattern.compile("\\bwdl\\s+(\\d+)\\s+(\\d+)\\s+(\\d+)\\b");
    private static final Pattern PV_RE = Pattern.compile("\\bpv(?:\\s+(.*))?$");
    private static final Pattern DEPTH_RE = Pattern.compile("\\bdepth\\s+(\\d+)\\b");
    private static final Pattern NODES_RE = Pattern.compile("\\bnodes\\s+(\\d+)\\b");
    private static final Pattern NPS_RE = Pattern.compile("\\bnps\\s+(\\d+)\\b");
    private static final Pattern TIME_RE = Pattern.compile("\\btime\\s+(\\d+)\\b");

    private final Process process;
    private final Writer stdin;
    private final BufferedReader stdout;

    public PikafishEngine(File binary, File nnue) throws IOException {
        if (!binary.exists()) throw new IOException("missing engine: " + binary.getAbsolutePath());
        ProcessBuilder builder = new ProcessBuilder(binary.getAbsolutePath());
        builder.directory(nnue.getParentFile());
        builder.redirectErrorStream(true);
        process = builder.start();
        stdin = new OutputStreamWriter(process.getOutputStream());
        stdout = new BufferedReader(new InputStreamReader(process.getInputStream()));
        send("uci");
        readUntil("uciok");
        send("setoption name UCI_ShowWDL value true");
        send("setoption name EvalFile value " + nnue.getAbsolutePath());
        send("isready");
        readUntil("readyok");
    }

    public synchronized AnalysisResult analyze(List<String> moves, SearchLimit limit) throws IOException {
        int multipv = 5;
        send("setoption name MultiPV value " + multipv);
        send("isready");
        readUntil("readyok");
        StringBuilder position = new StringBuilder("position startpos");
        if (!moves.isEmpty()) {
            position.append(" moves ");
            for (String move : moves) position.append(move).append(' ');
        }
        send(position.toString().trim());
        send(limit.goCommand());

        String bestMove = "";
        HashMap<Integer, AnalysisLine> infos = new HashMap<>();
        int[] wdl = null;
        String side = moves.size() % 2 == 0 ? "red" : "black";

        while (true) {
            String line = readLine();
            if (line.startsWith("bestmove")) {
                String[] parts = line.split("\\s+");
                if (parts.length > 1 && parts[1].length() == 4) bestMove = parts[1];
                break;
            }
            if (!line.startsWith("info")) continue;
            AnalysisLine parsed = parseInfo(line, side);
            if (parsed != null) {
                infos.put(parsed.multipv, parsed);
                if (parsed.multipv == 1 && parsed.wdl != null) wdl = parsed.wdl;
            }
        }

        ArrayList<AnalysisLine> lines = new ArrayList<>();
        for (int i = 1; i <= multipv; i++) {
            AnalysisLine info = infos.get(i);
            if (info == null) continue;
            if (i == 1 && info.bestMove.isEmpty() && bestMove.length() == 4) {
                info = new AnalysisLine(info.multipv, bestMove, info.scoreText, bestMove,
                        "", "", info.depth, info.nodes, info.nps, info.timeMs, info.wdl);
            }
            lines.add(info);
        }
        if (lines.isEmpty() && bestMove.length() == 4) {
            lines.add(new AnalysisLine(1, bestMove, "", bestMove, "", "", 0, 0, 0, 0, wdl));
        }
        return new AnalysisResult(lines, wdl);
    }

    public void close() {
        try {
            send("quit");
        } catch (Exception ignored) {
        }
        process.destroy();
    }

    private static AnalysisLine parseInfo(String line, String side) {
        Matcher pvMatch = PV_RE.matcher(line);
        Matcher scoreMatch = SCORE_RE.matcher(line);
        Matcher wdlMatch = WDL_RE.matcher(line);
        if (!pvMatch.find() && !scoreMatch.find() && !wdlMatch.find()) return null;

        int multipv = intMatch(MULTIPV_RE, line, 1);
        int depth = intMatch(DEPTH_RE, line, 0);
        long nodes = longMatch(NODES_RE, line, 0);
        long nps = longMatch(NPS_RE, line, 0);
        int timeMs = intMatch(TIME_RE, line, 0);

        String scoreText = "";
        scoreMatch.reset();
        if (scoreMatch.find()) {
            String kind = scoreMatch.group(1);
            int value = Integer.parseInt(scoreMatch.group(2));
            String bound = scoreMatch.group(3);
            if ("black".equals(side)) value = -value;
            scoreText = formatScore(kind, value, boundToRedPov(bound, side));
        }

        int[] wdl = null;
        wdlMatch.reset();
        if (wdlMatch.find()) {
            int win = Integer.parseInt(wdlMatch.group(1));
            int draw = Integer.parseInt(wdlMatch.group(2));
            int lose = Integer.parseInt(wdlMatch.group(3));
            wdl = "red".equals(side) ? new int[] { win, draw, lose } : new int[] { lose, draw, win };
        }

        String pv = "";
        pvMatch.reset();
        if (pvMatch.find() && pvMatch.group(1) != null) pv = normalizePv(pvMatch.group(1));
        String best = "";
        for (String move : pv.split("\\s+")) {
            if (move.length() == 4) {
                best = move;
                break;
            }
        }
        return new AnalysisLine(multipv, best, scoreText, pv, "", "", depth, nodes, nps, timeMs, wdl);
    }

    private static String normalizePv(String text) {
        StringBuilder result = new StringBuilder();
        for (String move : text.trim().split("\\s+")) {
            if (move.length() != 4 || "0000".equals(move)) continue;
            if (result.length() > 0) result.append(' ');
            result.append(move);
        }
        return result.toString();
    }

    private static int intMatch(Pattern pattern, String line, int fallback) {
        Matcher matcher = pattern.matcher(line);
        return matcher.find() ? Integer.parseInt(matcher.group(1)) : fallback;
    }

    private static long longMatch(Pattern pattern, String line, long fallback) {
        Matcher matcher = pattern.matcher(line);
        return matcher.find() ? Long.parseLong(matcher.group(1)) : fallback;
    }

    private static String boundToRedPov(String bound, String side) {
        if (bound == null || "red".equals(side)) return bound;
        if ("lowerbound".equals(bound)) return "upperbound";
        if ("upperbound".equals(bound)) return "lowerbound";
        return bound;
    }

    private static String formatScore(String kind, int value, String bound) {
        if ("mate".equals(kind)) return value >= 0 ? "红方 M" + value : "黑方 M" + Math.abs(value);
        float pawns = value / 100f;
        if (pawns >= 0) return String.format(Locale.US, "红方 %s%.2f", boundOperator(bound, "red"), pawns);
        return String.format(Locale.US, "黑方 %s%.2f", boundOperator(bound, "black"), Math.abs(pawns));
    }

    private static String boundOperator(String bound, String advantageSide) {
        if (bound == null) return "+";
        if ("red".equals(advantageSide)) return "lowerbound".equals(bound) ? ">=" : "<=";
        return "lowerbound".equals(bound) ? "<=" : ">=";
    }

    private void send(String command) throws IOException {
        stdin.write(command + "\n");
        stdin.flush();
    }

    private String readLine() throws IOException {
        String line = stdout.readLine();
        if (line == null) throw new IOException("engine stopped");
        return line;
    }

    private void readUntil(String marker) throws IOException {
        while (true) {
            String line = readLine();
            if (marker.equals(line)) return;
        }
    }
}
