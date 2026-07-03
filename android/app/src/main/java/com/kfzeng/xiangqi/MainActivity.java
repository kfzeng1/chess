package com.kfzeng.xiangqi;

import android.app.Activity;
import android.app.Dialog;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.ScrollView;
import android.widget.TextView;

import com.kfzeng.xiangqi.backend.ApkBackend;
import com.kfzeng.xiangqi.core.GameState;
import com.kfzeng.xiangqi.engine.AnalysisLine;
import com.kfzeng.xiangqi.engine.AnalysisResult;
import com.kfzeng.xiangqi.ui.BoardView;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends Activity {
    interface ToggleSetter { void set(boolean value); }
    interface SliderFormatter { String format(int value); }

    private GameState game;
    private BoardView boardView;
    private TextView turnText;
    private TextView moveCountText;
    private TextView thinkingText;
    private TextView redWdl;
    private TextView drawWdl;
    private TextView blackWdl;
    private TextView turnStat;
    private TextView roundStat;
    private TextView redClock;
    private TextView blackClock;
    private String analysisSummary = "正在启动离线 Pikafish。";
    private Button autoButton;
    private Button manualAiButton;
    private ApkBackend backend;
    private AnalysisResult lastAnalysis;
    private boolean autoMode = true;
    private boolean redAi = false;
    private boolean blackAi = true;
    private boolean flipped = false;
    private boolean engineBusy = false;
    private int analysisSerial = 0;
    private int redAiMoveTimeMs = 1000;
    private int blackAiMoveTimeMs = 1000;
    private int delegateDelayMs = 1000;
    private boolean notationUci = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        backend = new ApkBackend(this);
        game = backend.game();
        game.reset();
        setContentView(buildLayout());
        refreshUi();
        analyzePosition(false);
    }

    @Override
    protected void onDestroy() {
        if (backend != null) backend.close();
        super.onDestroy();
    }

    private View buildLayout() {
        int pad = dp(8);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xffece7de);
        root.setPadding(0, statusBarHeight(), 0, 0);

        LinearLayout top = new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setPadding(dp(10), dp(6), dp(10), dp(4));
        TextView mark = text("象", 15, 0xfffff3df, true);
        mark.setGravity(Gravity.CENTER);
        mark.setBackground(makeRound(0xffc7352d, 0xff8e1f1b, dp(15)));
        top.addView(mark, new LinearLayout.LayoutParams(dp(28), dp(28)));
        TextView title = text("象棋 AI 对弈", 16, 0xff29241f, true);
        LinearLayout.LayoutParams titleLp = new LinearLayout.LayoutParams(0, dp(34), 1);
        titleLp.leftMargin = dp(10);
        top.addView(title, titleLp);
        Button config = smallButton("配置");
        config.setOnClickListener(v -> showConfigDialog());
        top.addView(config, new LinearLayout.LayoutParams(dp(62), dp(34)));
        Button analysis = smallButton("分析");
        analysis.setOnClickListener(v -> showAnalysisDialog());
        LinearLayout.LayoutParams analysisLp = new LinearLayout.LayoutParams(dp(62), dp(34));
        analysisLp.leftMargin = dp(6);
        top.addView(analysis, analysisLp);
        root.addView(top);

        TextView engineStatus = text("● 离线 APK · Pikafish 20260628 arm64", 13, 0xff287f83, false);
        engineStatus.setGravity(Gravity.CENTER_VERTICAL);
        engineStatus.setPadding(dp(10), 0, dp(10), 0);
        engineStatus.setBackground(makeRound(0xffffffff, 0xffd2c7b8, dp(18)));
        LinearLayout.LayoutParams engineLp = new LinearLayout.LayoutParams(-1, dp(30));
        engineLp.leftMargin = dp(10);
        engineLp.rightMargin = dp(10);
        root.addView(engineStatus, engineLp);

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(false);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(8), dp(6), dp(8), dp(10));
        scroll.addView(content);

        LinearLayout boardShell = new LinearLayout(this);
        boardShell.setOrientation(LinearLayout.VERTICAL);
        boardShell.setPadding(dp(6), dp(6), dp(6), dp(7));
        boardShell.setBackground(makeRound(0xfffbfaf7, 0xffd2c7b8, dp(8)));
        content.addView(boardShell, new LinearLayout.LayoutParams(-1, -2));

        LinearLayout statusLine = new LinearLayout(this);
        statusLine.setGravity(Gravity.CENTER_VERTICAL);
        turnText = text("红方回合", 15, 0xff29241f, true);
        statusLine.addView(turnText, new LinearLayout.LayoutParams(0, dp(34), 1));
        moveCountText = chip("0 步");
        statusLine.addView(moveCountText, new LinearLayout.LayoutParams(dp(66), dp(30)));
        thinkingText = chip("待命");
        LinearLayout.LayoutParams thinkLp = new LinearLayout.LayoutParams(dp(66), dp(30));
        thinkLp.leftMargin = dp(6);
        statusLine.addView(thinkingText, thinkLp);
        boardShell.addView(statusLine);

        GridLayout wdlGrid = new GridLayout(this);
        wdlGrid.setColumnCount(3);
        redWdl = wdlBox("红胜 -", 0xffc7352d);
        drawWdl = wdlBox("和棋 -", 0xff4b433a);
        blackWdl = wdlBox("黑胜 -", 0xff282522);
        addGrid(wdlGrid, redWdl, 1);
        addGrid(wdlGrid, drawWdl, 1);
        addGrid(wdlGrid, blackWdl, 1);
        LinearLayout.LayoutParams wdlLp = new LinearLayout.LayoutParams(-1, dp(30));
        wdlLp.topMargin = dp(1);
        boardShell.addView(wdlGrid, wdlLp);

        boardView = new BoardView(this, game);
        boardView.setMoveListener(() -> {
            refreshUi();
            analyzePosition(false);
        });
        int boardWidth = Math.max(dp(300), getResources().getDisplayMetrics().widthPixels - dp(32));
        int maxBoardHeight = Math.max(dp(340), getResources().getDisplayMetrics().heightPixels - dp(390));
        int boardHeight = Math.min(Math.round(boardWidth * BoardView.CROP_ASPECT), maxBoardHeight);
        LinearLayout.LayoutParams boardLp = new LinearLayout.LayoutParams(-1, boardHeight);
        boardLp.topMargin = dp(4);
        boardShell.addView(boardView, boardLp);

        LinearLayout icons = new LinearLayout(this);
        icons.setOrientation(LinearLayout.HORIZONTAL);
        icons.setPadding(0, dp(6), 0, 0);
        icons.addView(iconAction("↻", "新局", v -> newGame()), new LinearLayout.LayoutParams(0, dp(56), 1));
        icons.addView(iconAction("↶", "悔棋", v -> undo()), new LinearLayout.LayoutParams(0, dp(56), 1));
        icons.addView(iconAction("⇅", "翻转", v -> flip()), new LinearLayout.LayoutParams(0, dp(56), 1));
        boardShell.addView(icons);

        LinearLayout delegated = new LinearLayout(this);
        delegated.setOrientation(LinearLayout.HORIZONTAL);
        delegated.setPadding(0, dp(6), 0, 0);
        autoButton = actionButton("自动代走：开", 0xffc7352d);
        autoButton.setOnClickListener(v -> {
            autoMode = !autoMode;
            refreshUi();
            maybeAutoMove();
        });
        manualAiButton = actionButton("本步 AI", 0xff287f83);
        manualAiButton.setOnClickListener(v -> playAiMove());
        delegated.addView(autoButton, new LinearLayout.LayoutParams(0, dp(42), 1));
        LinearLayout.LayoutParams manualLp = new LinearLayout.LayoutParams(0, dp(42), 1);
        manualLp.leftMargin = dp(8);
        delegated.addView(manualAiButton, manualLp);
        boardShell.addView(delegated);

        GridLayout stats = new GridLayout(this);
        stats.setColumnCount(2);
        stats.setPadding(0, dp(6), 0, 0);
        turnStat = statBox("当前方", "红方");
        roundStat = statBox("回合数", "0");
        redClock = statBox("红方用时", "00:00");
        blackClock = statBox("黑方用时", "00:00");
        addGrid(stats, turnStat, 1);
        addGrid(stats, roundStat, 1);
        addGrid(stats, redClock, 1);
        addGrid(stats, blackClock, 1);
        boardShell.addView(stats);

        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        return root;
    }

    private void showConfigDialog() {
        Dialog dialog = sideDialog(Gravity.START, "对局配置");
        LinearLayout body = dialog.findViewById(1001);
        body.addView(toggleRow("红方", "AI", redAi, value -> { redAi = value; refreshUi(); maybeAutoMove(); }));
        body.addView(toggleRow("黑方", "AI", blackAi, value -> { blackAi = value; refreshUi(); maybeAutoMove(); }));
        body.addView(sliderRow("代走间隔", "分析完成后至少等待", 0, 5000, 500, delegateDelayMs, value -> {
            delegateDelayMs = value;
            return String.format(Locale.US, "%.1fs", value / 1000f);
        }));
        body.addView(sliderRow("红方 AI 搜索", "红方走棋时使用的 Pikafish 时间", 100, 5000, 100, redAiMoveTimeMs, value -> {
            redAiMoveTimeMs = value;
            return String.format(Locale.US, "%.1fs · go movetime %d", value / 1000f, value);
        }));
        body.addView(sliderRow("黑方 AI 搜索", "黑方走棋时使用的 Pikafish 时间", 100, 5000, 100, blackAiMoveTimeMs, value -> {
            blackAiMoveTimeMs = value;
            return String.format(Locale.US, "%.1fs · go movetime %d", value / 1000f, value);
        }));
        body.addView(section("引擎", "Pikafish dev-20260628-553282ed / Android arm64"));
        dialog.show();
    }

    private void showAnalysisDialog() {
        Dialog dialog = sideDialog(Gravity.END, "AI 分析");
        LinearLayout body = dialog.findViewById(1001);
        body.addView(notationRow(() -> {
            dialog.dismiss();
            showAnalysisDialog();
        }));
        body.addView(analysisCard("当前结论", analysisSummary, 0xff287f83, true));
        body.addView(analysisCard("主变", lastAnalysis == null ? "正在分析" : lastAnalysis.pvText(notationUci), 0xff8b5b28, false));
        body.addView(recommendationsSection());
        body.addView(analysisCard("走法记录", game.movesText(notationUci), 0xff4b433a, false));
        body.addView(analysisCard("说明", "分数始终按红方视角显示：红方 +0.24 表示红方略优，黑方 +0.24 表示黑方略优。WDL 为红胜、和棋、黑胜。", 0xff766b5f, false));
        dialog.show();
    }

    private Dialog sideDialog(int gravity, String titleText) {
        Dialog dialog = new Dialog(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xfffbfaf7);
        LinearLayout header = new LinearLayout(this);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(12), 0, dp(8), 0);
        header.addView(text(titleText, 16, 0xff29241f, true), new LinearLayout.LayoutParams(0, dp(44), 1));
        Button close = smallButton("×");
        close.setOnClickListener(v -> dialog.dismiss());
        header.addView(close, new LinearLayout.LayoutParams(dp(38), dp(34)));
        root.addView(header);
        ScrollView scroll = new ScrollView(this);
        LinearLayout body = new LinearLayout(this);
        body.setId(1001);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(10), dp(8), dp(10), dp(16));
        scroll.addView(body);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        dialog.setContentView(root);
        Window window = dialog.getWindow();
        dialog.setOnShowListener(d -> {
            Window w = dialog.getWindow();
            if (w == null) return;
            WindowManager.LayoutParams lp = new WindowManager.LayoutParams();
            lp.copyFrom(w.getAttributes());
            lp.width = Math.min(dp(340), (int)(getResources().getDisplayMetrics().widthPixels * 0.88f));
            lp.height = WindowManager.LayoutParams.MATCH_PARENT;
            lp.gravity = gravity;
            w.setAttributes(lp);
        });
        if (window != null) window.setBackgroundDrawableResource(android.R.color.transparent);
        return dialog;
    }

    private TextView section(String title, String value) {
        TextView view = text(title + "\n" + value, 14, 0xff29241f, false);
        view.setPadding(dp(10), dp(10), dp(10), dp(10));
        view.setBackground(makeRound(0xffffffff, 0xffe2d9ce, dp(8)));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.bottomMargin = dp(8);
        view.setLayoutParams(lp);
        return view;
    }

    private View notationRow(Runnable redraw) {
        LinearLayout row = new LinearLayout(this);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(10), dp(8), dp(10), dp(8));
        row.setBackground(makeRound(0xfff4efe7, 0xffe2d9ce, dp(8)));
        TextView label = text("着法显示", 14, 0xff29241f, true);
        row.addView(label, new LinearLayout.LayoutParams(0, dp(38), 1));
        Button readable = smallButton("用户着法");
        Button uci = smallButton("UCI 坐标");
        View.OnClickListener listener = v -> {
            notationUci = v == uci;
            renderAnalysisText();
            redraw.run();
        };
        readable.setOnClickListener(listener);
        uci.setOnClickListener(listener);
        readable.setTextColor(!notationUci ? 0xffffffff : 0xff29241f);
        readable.setBackground(makeRound(!notationUci ? 0xff287f83 : 0xffffffff, 0xffd2c7b8, dp(7)));
        uci.setTextColor(notationUci ? 0xffffffff : 0xff29241f);
        uci.setBackground(makeRound(notationUci ? 0xff287f83 : 0xffffffff, 0xffd2c7b8, dp(7)));
        row.addView(readable, new LinearLayout.LayoutParams(dp(88), dp(36)));
        LinearLayout.LayoutParams uciLp = new LinearLayout.LayoutParams(dp(82), dp(36));
        uciLp.leftMargin = dp(6);
        row.addView(uci, uciLp);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.bottomMargin = dp(10);
        row.setLayoutParams(lp);
        return row;
    }

    private View analysisCard(String title, String value, int accent, boolean important) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(10), dp(9), dp(10), dp(10));
        card.setBackground(makeRound(0xffffffff, 0xffe2d9ce, dp(8)));
        TextView titleView = text(title, 12, accent, true);
        titleView.setGravity(Gravity.CENTER_VERTICAL);
        card.addView(titleView, new LinearLayout.LayoutParams(-1, dp(22)));
        TextView valueView = text(value == null || value.isEmpty() ? "无" : value, important ? 16 : 14, 0xff29241f, important);
        valueView.setGravity(Gravity.START);
        valueView.setLineSpacing(dp(2), 1.0f);
        LinearLayout.LayoutParams valueLp = new LinearLayout.LayoutParams(-1, -2);
        valueLp.topMargin = dp(2);
        card.addView(valueView, valueLp);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.bottomMargin = dp(9);
        card.setLayoutParams(lp);
        return card;
    }

    private View recommendationsSection() {
        LinearLayout section = new LinearLayout(this);
        section.setOrientation(LinearLayout.VERTICAL);
        section.setPadding(dp(10), dp(9), dp(10), dp(10));
        section.setBackground(makeRound(0xffffffff, 0xffe2d9ce, dp(8)));

        LinearLayout header = new LinearLayout(this);
        header.setGravity(Gravity.CENTER_VERTICAL);
        TextView title = text("推荐着法", 12, 0xffc7352d, true);
        header.addView(title, new LinearLayout.LayoutParams(0, dp(24), 1));
        TextView count = text(lastAnalysis == null ? "等待" : "MultiPV " + lastAnalysis.lines.size(), 11, 0xff766b5f, false);
        count.setGravity(Gravity.CENTER_VERTICAL | Gravity.RIGHT);
        header.addView(count, new LinearLayout.LayoutParams(dp(86), dp(24)));
        section.addView(header);

        if (lastAnalysis == null || lastAnalysis.lines.isEmpty()) {
            section.addView(recommendationCard(1, "正在分析", "等待分数", "引擎返回后显示候选着法"));
        } else {
            int limit = Math.min(5, lastAnalysis.lines.size());
            for (int i = 0; i < limit; i++) {
                AnalysisLine line = lastAnalysis.lines.get(i);
                section.addView(recommendationCard(
                        i + 1,
                        line.moveText(notationUci),
                        line.scoreText.isEmpty() ? "等待分数" : line.scoreText,
                        line.pvText(notationUci)));
            }
        }

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.bottomMargin = dp(9);
        section.setLayoutParams(lp);
        return section;
    }

    private View recommendationCard(int rank, String move, String score, String pv) {
        LinearLayout card = new LinearLayout(this);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(8), dp(7), dp(8), dp(7));
        card.setBackground(makeRound(rank == 1 ? 0xfffff4f1 : 0xfffbfaf7, rank == 1 ? 0xffe0aca5 : 0xffe2d9ce, dp(7)));

        TextView badge = text(String.valueOf(rank), 12, 0xffffffff, true);
        badge.setGravity(Gravity.CENTER);
        badge.setBackground(makeRound(rank == 1 ? 0xffc7352d : 0xff282522, rank == 1 ? 0xffc7352d : 0xff282522, dp(12)));
        card.addView(badge, new LinearLayout.LayoutParams(dp(24), dp(24)));

        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        TextView moveText = text(move == null || move.isEmpty() ? "无" : move, 14, 0xff29241f, true);
        moveText.setGravity(Gravity.START);
        main.addView(moveText, new LinearLayout.LayoutParams(-1, dp(24)));
        TextView pvText = text((notationUci ? "pv " : "主变 ") + (pv == null || pv.isEmpty() ? "无" : pv), 11, 0xff766b5f, false);
        pvText.setGravity(Gravity.START);
        pvText.setSingleLine(true);
        main.addView(pvText, new LinearLayout.LayoutParams(-1, dp(20)));
        LinearLayout.LayoutParams mainLp = new LinearLayout.LayoutParams(0, -2, 1);
        mainLp.leftMargin = dp(8);
        card.addView(main, mainLp);

        TextView eval = text(score == null || score.isEmpty() ? "无分数" : score, 12, rank == 1 ? 0xffc7352d : 0xff4b433a, true);
        eval.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        eval.setSingleLine(true);
        card.addView(eval, new LinearLayout.LayoutParams(dp(86), dp(44)));

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.topMargin = dp(7);
        card.setLayoutParams(lp);
        return card;
    }

    private View toggleRow(String title, String suffix, boolean checked, ToggleSetter setter) {
        LinearLayout row = new LinearLayout(this);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(10), dp(8), dp(10), dp(8));
        row.setBackground(makeRound(0xffffffff, 0xffe2d9ce, dp(8)));
        TextView label = text(title, 14, 0xff29241f, true);
        row.addView(label, new LinearLayout.LayoutParams(0, dp(42), 1));
        LinearLayout segmented = new LinearLayout(this);
        segmented.setOrientation(LinearLayout.HORIZONTAL);
        segmented.setPadding(dp(3), dp(3), dp(3), dp(3));
        segmented.setBackground(makeRound(0xfff4efe7, 0xffd2c7b8, dp(8)));
        Button human = smallButton("人类");
        Button ai = smallButton(suffix);
        final boolean[] value = new boolean[] { checked };
        int activeColor = title.contains("红") ? 0xffc7352d : 0xff282522;
        Runnable paintButtons = () -> {
            human.setTextColor(!value[0] ? 0xffffffff : 0xff766b5f);
            human.setBackground(makeRound(!value[0] ? activeColor : 0x00ffffff, !value[0] ? activeColor : 0x00ffffff, dp(6)));
            ai.setTextColor(value[0] ? 0xffffffff : 0xff766b5f);
            ai.setBackground(makeRound(value[0] ? activeColor : 0x00ffffff, value[0] ? activeColor : 0x00ffffff, dp(6)));
        };
        human.setOnClickListener(v -> {
            value[0] = false;
            paintButtons.run();
            setter.set(false);
        });
        ai.setOnClickListener(v -> {
            value[0] = true;
            paintButtons.run();
            setter.set(true);
        });
        paintButtons.run();
        segmented.addView(human, new LinearLayout.LayoutParams(dp(76), dp(34)));
        segmented.addView(ai, new LinearLayout.LayoutParams(dp(76), dp(34)));
        row.addView(segmented, new LinearLayout.LayoutParams(dp(158), dp(40)));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.bottomMargin = dp(8);
        row.setLayoutParams(lp);
        return row;
    }

    private View sliderRow(String title, String subtitle, int min, int max, int step, int current, SliderFormatter formatter) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(10), dp(9), dp(10), dp(9));
        box.setBackground(makeRound(0xffffffff, 0xffe2d9ce, dp(8)));
        TextView label = text(title + "  " + formatter.format(current) + "\n" + subtitle, 13, 0xff29241f, false);
        box.addView(label);
        SeekBar seek = new SeekBar(this);
        seek.setMax((max - min) / step);
        seek.setProgress((current - min) / step);
        seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                int value = min + progress * step;
                label.setText(title + "  " + formatter.format(value) + "\n" + subtitle);
                if (fromUser) formatter.format(value);
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) {}
            @Override public void onStopTrackingTouch(SeekBar seekBar) {
                int value = min + seekBar.getProgress() * step;
                formatter.format(value);
            }
        });
        box.addView(seek);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.bottomMargin = dp(8);
        box.setLayoutParams(lp);
        return box;
    }

    private void newGame() {
        analysisSerial++;
        game.reset();
        lastAnalysis = null;
        analysisSummary = "等待重新分析。";
        boardView.clearSelection();
        refreshUi();
        analyzePosition(false);
    }

    private void undo() {
        analysisSerial++;
        game.undo();
        lastAnalysis = null;
        analysisSummary = "等待重新分析。";
        boardView.clearSelection();
        refreshUi();
        analyzePosition(false);
    }

    private void flip() {
        flipped = !flipped;
        boardView.setFlipped(flipped);
    }

    private void playAiMove() {
        if (!engineBusy) analyzePosition(true);
    }

    private void analyzePosition(boolean playBestMove) {
        if (engineBusy) return;
        final int serial = ++analysisSerial;
        final ArrayList<String> moves = new ArrayList<>(game.moves);
        final String requestPositionId = backend.positionId(moves);
        engineBusy = true;
        thinkingText.setText(playBestMove ? "代走" : "分析");
        manualAiButton.setEnabled(false);
        autoButton.setEnabled(false);
        analysisSummary = "Pikafish 正在计算...";
        new Thread(() -> {
            try {
                AnalysisResult result = backend.analyze(moves, currentAiMoveTimeMs());
                runOnUiThread(() -> applyAnalysis(serial, requestPositionId, result, playBestMove));
            } catch (Exception ex) {
                runOnUiThread(() -> {
                    if (serial != analysisSerial) return;
                    engineBusy = false;
                    thinkingText.setText("异常");
                    manualAiButton.setEnabled(true);
                    autoButton.setEnabled(true);
                    analysisSummary = "分析失败：" + ex.getMessage();
                });
            }
        }).start();
    }

    private int currentAiMoveTimeMs() {
        return "red".equals(game.sideToMove()) ? redAiMoveTimeMs : blackAiMoveTimeMs;
    }

    private void applyAnalysis(int serial, String requestPositionId, AnalysisResult result, boolean playBestMove) {
        if (serial != analysisSerial) return;
        if (!backend.positionId(game.moves).equals(requestPositionId)) {
            engineBusy = false;
            autoMode = false;
            analysisSummary = "分析局面不匹配，已关闭自动代走。";
            thinkingText.setText("不匹配");
            manualAiButton.setEnabled(true);
            autoButton.setEnabled(true);
            refreshUi();
            return;
        }
        engineBusy = false;
        lastAnalysis = result.withChinese(game.boardSnapshot());
        if (result.wdl != null) {
            redWdl.setText("红胜 " + result.wdl[0]);
            drawWdl.setText("和棋 " + result.wdl[1]);
            blackWdl.setText("黑胜 " + result.wdl[2]);
        }
        renderAnalysisText();
        if (playBestMove || shouldAutoPlayCurrentSide()) {
            if (scheduleBestMove(serial, result.bestMove, !playBestMove)) return;
        }
        thinkingText.setText("待命");
        manualAiButton.setEnabled(true);
        autoButton.setEnabled(true);
        refreshUi();
    }

    private void renderAnalysisText() {
        if (lastAnalysis == null) return;
        analysisSummary = lastAnalysis.summary(notationUci);
    }

    private void maybeAutoMove() {
        if (!autoMode || engineBusy || game.legalMoves().isEmpty()) return;
        if (shouldAutoPlayCurrentSide()) {
            analyzePosition(true);
        }
    }

    private boolean shouldAutoPlayCurrentSide() {
        String side = game.sideToMove();
        return autoMode && (("red".equals(side) && redAi) || ("black".equals(side) && blackAi));
    }

    private boolean scheduleBestMove(int serial, String bestMove, boolean requireAutoCheck) {
        if (bestMove == null || bestMove.length() != 4) return false;
        if (!game.legalMoves().contains(bestMove)) {
            analysisSummary = "AI 返回不合法着法，已停止代走：" + bestMove;
            autoMode = false;
            refreshUi();
            return false;
        }
        thinkingText.setText("等待");
        manualAiButton.setEnabled(true);
        autoButton.setEnabled(true);
        refreshUi();
        boardView.postDelayed(() -> {
            if (engineBusy || serial != analysisSerial) return;
            if (requireAutoCheck && !shouldAutoPlayCurrentSide()) {
                thinkingText.setText("待命");
                manualAiButton.setEnabled(true);
                autoButton.setEnabled(true);
                refreshUi();
                return;
            }
            game.applyMove(bestMove);
            boardView.clearSelection();
            lastAnalysis = null;
            analysisSummary = "等待重新分析。";
            refreshUi();
            analyzePosition(false);
        }, delegateDelayMs);
        return true;
    }

    private void refreshUi() {
        String sideName = game.sideToMove().equals("red") ? "红方" : "黑方";
        turnText.setText(sideName + "回合");
        moveCountText.setText(game.moves.size() + " 步");
        if (!engineBusy) thinkingText.setText("待命");
        if (lastAnalysis == null || lastAnalysis.wdl == null) {
            redWdl.setText("红胜 -");
            drawWdl.setText("和棋 -");
            blackWdl.setText("黑胜 -");
        }
        turnStat.setText("当前方\n" + sideName);
        roundStat.setText("回合数\n" + (game.moves.size() + 1) / 2);
        redClock.setText("红方用时\n--:--");
        blackClock.setText("黑方用时\n--:--");
        autoButton.setText(autoMode ? "自动代走：开" : "自动代走：关");
        autoButton.setTextColor(autoMode ? 0xffffffff : 0xff29241f);
        autoButton.setBackground(makeRound(autoMode ? 0xffc7352d : 0xffffffff, autoMode ? 0xff9e322d : 0xffd2c7b8, dp(7)));
        manualAiButton.setEnabled(!engineBusy);
        autoButton.setEnabled(!engineBusy);
        boardView.invalidate();
    }

    private TextView text(String value, int sp, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(sp);
        t.setTextColor(color);
        t.setGravity(Gravity.CENTER_VERTICAL);
        if (bold) t.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        return t;
    }

    private TextView chip(String value) {
        TextView t = text(value, 13, 0xff29241f, true);
        t.setGravity(Gravity.CENTER);
        t.setBackground(makeRound(0xffffffff, 0xffd2c7b8, dp(7)));
        return t;
    }

    private TextView wdlBox(String value, int color) {
        TextView t = chip(value);
        t.setTextColor(color);
        return t;
    }

    private TextView statBox(String title, String value) {
        TextView t = text(title + "\n" + value, 12, 0xff29241f, true);
        t.setPadding(dp(9), dp(5), dp(9), dp(5));
        t.setBackground(makeRound(0xffffffff, 0xffe2d9ce, dp(7)));
        return t;
    }

    private Button smallButton(String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setTextColor(0xff29241f);
        b.setTextSize(14);
        b.setAllCaps(false);
        b.setMinHeight(0);
        b.setMinWidth(0);
        b.setPadding(dp(8), 0, dp(8), 0);
        b.setBackground(makeRound(0xffffffff, 0xffd2c7b8, dp(7)));
        return b;
    }

    private Button actionButton(String label, int color) {
        Button b = smallButton(label);
        b.setTextColor(0xffffffff);
        b.setTextSize(16);
        b.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        b.setBackground(makeRound(color, color, dp(7)));
        return b;
    }

    private View iconAction(String icon, String label, View.OnClickListener listener) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(4), 0, dp(4), 0);
        TextView l = text(label, 10, 0xff766b5f, true);
        l.setGravity(Gravity.CENTER);
        box.addView(l, new LinearLayout.LayoutParams(-1, dp(17)));
        Button b = smallButton(icon);
        b.setTextSize(20);
        b.setOnClickListener(listener);
        box.addView(b, new LinearLayout.LayoutParams(-1, dp(38)));
        return box;
    }

    private void addGrid(GridLayout grid, View child, int weight) {
        GridLayout.LayoutParams lp = new GridLayout.LayoutParams();
        int columns = Math.max(1, grid.getColumnCount());
        int totalWidth = getResources().getDisplayMetrics().widthPixels - dp(28);
        lp.width = Math.max(dp(64), totalWidth / columns - dp(8));
        lp.height = GridLayout.LayoutParams.WRAP_CONTENT;
        lp.columnSpec = GridLayout.spec(GridLayout.UNDEFINED);
        lp.setMargins(dp(4), dp(4), dp(4), dp(4));
        grid.addView(child, lp);
    }

    private android.graphics.drawable.Drawable makeRound(int fill, int stroke, int radius) {
        android.graphics.drawable.GradientDrawable d = new android.graphics.drawable.GradientDrawable();
        d.setColor(fill);
        d.setStroke(dp(1), stroke);
        d.setCornerRadius(radius);
        return d;
    }

    private int dp(int value) {
        return (int)(value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private int statusBarHeight() {
        int id = getResources().getIdentifier("status_bar_height", "dimen", "android");
        return id > 0 ? getResources().getDimensionPixelSize(id) : 0;
    }

}
