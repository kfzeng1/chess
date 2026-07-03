import com.kfzeng.xiangqi.engine.AnalysisResult;
import com.kfzeng.xiangqi.engine.PikafishEngine;
import com.kfzeng.xiangqi.engine.SearchLimit;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class EngineSmokeTest {
    public static void main(String[] args) throws Exception {
        File binary = new File("engines/pikafish-avxvnni");
        File nnue = new File("engines/pikafish.nnue");
        PikafishEngine engine = new PikafishEngine(binary, nnue);
        try {
            smoke(engine, new ArrayList<>(), SearchLimit.depth(1));
            smoke(engine, List.of("h2e2"), SearchLimit.movetime(200));
        } finally {
            engine.close();
        }
        System.out.println("Android engine parser smoke test passed.");
    }

    private static void smoke(PikafishEngine engine, List<String> moves, SearchLimit limit) throws Exception {
        AnalysisResult result = engine.analyze(moves, limit);
        require(!result.lines.isEmpty(), "expected at least one MultiPV line for " + limit.goCommand());
        require(result.lines.size() <= 5, "expected MultiPV line count <= 5, got " + result.lines.size());
        require(result.bestMove.length() == 4, "expected 4-char bestmove, got " + result.bestMove);
        require(!result.pv.isEmpty(), "expected non-empty pv for " + limit.goCommand());
        require(result.lines.get(0).depth >= 1, "expected depth >= 1");
        require(result.scoreText.startsWith("红方 ") || result.scoreText.startsWith("黑方 "),
                "expected red-perspective score text, got " + result.scoreText);
        require(result.wdl == null || result.wdl.length == 3, "expected WDL triplet when present");
        System.out.println(limit.goCommand() + " -> " + result.bestMove + " / " + result.scoreText
                + " / lines " + result.lines.size());
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
