package com.kfzeng.xiangqi;

import android.app.Activity;
import android.app.Dialog;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.os.Bundle;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MainActivity extends Activity {
    interface ToggleSetter { void set(boolean value); }
    interface SliderFormatter { String format(int value); }

    private final GameState game = new GameState();
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
    private TextView analysisText;
    private Button autoButton;
    private Button manualAiButton;
    private PikafishEngine engine;
    private AnalysisResult lastAnalysis;
    private boolean autoMode = true;
    private boolean redAi = false;
    private boolean blackAi = true;
    private boolean flipped = false;
    private boolean engineBusy = false;
    private int analysisSerial = 0;
    private int aiMoveTimeMs = 1000;
    private int delegateDelayMs = 1000;
    private boolean notationUci = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        game.reset();
        setContentView(buildLayout());
        refreshUi();
        analyzePosition(false);
    }

    @Override
    protected void onDestroy() {
        if (engine != null) engine.close();
        super.onDestroy();
    }

    private View buildLayout() {
        int pad = dp(8);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xffece7de);

        LinearLayout top = new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setPadding(dp(10), dp(8), dp(10), dp(6));
        TextView mark = text("象", 15, 0xfffff3df, true);
        mark.setGravity(Gravity.CENTER);
        mark.setBackground(makeRound(0xffc7352d, 0xff8e1f1b, dp(15)));
        top.addView(mark, new LinearLayout.LayoutParams(dp(30), dp(30)));
        TextView title = text("象棋 AI 对弈", 17, 0xff29241f, true);
        LinearLayout.LayoutParams titleLp = new LinearLayout.LayoutParams(0, dp(38), 1);
        titleLp.leftMargin = dp(10);
        top.addView(title, titleLp);
        Button config = smallButton("配置");
        config.setOnClickListener(v -> showConfigDialog());
        top.addView(config, new LinearLayout.LayoutParams(dp(66), dp(36)));
        Button analysis = smallButton("分析");
        analysis.setOnClickListener(v -> showAnalysisDialog());
        LinearLayout.LayoutParams analysisLp = new LinearLayout.LayoutParams(dp(66), dp(36));
        analysisLp.leftMargin = dp(6);
        top.addView(analysis, analysisLp);
        root.addView(top);

        TextView engineStatus = text("● 离线 APK · Pikafish 20260628 arm64", 13, 0xff287f83, false);
        engineStatus.setGravity(Gravity.CENTER_VERTICAL);
        engineStatus.setPadding(dp(10), 0, dp(10), 0);
        engineStatus.setBackground(makeRound(0xffffffff, 0xffd2c7b8, dp(18)));
        LinearLayout.LayoutParams engineLp = new LinearLayout.LayoutParams(-1, dp(34));
        engineLp.leftMargin = dp(10);
        engineLp.rightMargin = dp(10);
        root.addView(engineStatus, engineLp);

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(false);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(8), dp(8), dp(8), dp(12));
        scroll.addView(content);

        LinearLayout boardShell = new LinearLayout(this);
        boardShell.setOrientation(LinearLayout.VERTICAL);
        boardShell.setPadding(dp(6), dp(8), dp(6), dp(8));
        boardShell.setBackground(makeRound(0xfffbfaf7, 0xffd2c7b8, dp(8)));
        content.addView(boardShell, new LinearLayout.LayoutParams(-1, -2));

        LinearLayout statusLine = new LinearLayout(this);
        statusLine.setGravity(Gravity.CENTER_VERTICAL);
        turnText = text("红方回合", 15, 0xff29241f, true);
        statusLine.addView(turnText, new LinearLayout.LayoutParams(0, dp(38), 1));
        moveCountText = chip("0 步");
        statusLine.addView(moveCountText, new LinearLayout.LayoutParams(dp(72), dp(34)));
        thinkingText = chip("待命");
        LinearLayout.LayoutParams thinkLp = new LinearLayout.LayoutParams(dp(72), dp(34));
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
        LinearLayout.LayoutParams wdlLp = new LinearLayout.LayoutParams(-1, dp(36));
        wdlLp.topMargin = dp(2);
        boardShell.addView(wdlGrid, wdlLp);

        boardView = new BoardView(this, game);
        boardView.setMoveListener(() -> {
            refreshUi();
            analyzePosition(false);
        });
        int boardWidth = Math.max(dp(300), getResources().getDisplayMetrics().widthPixels - dp(32));
        int boardHeight = Math.round(boardWidth * BoardView.CROP_ASPECT);
        LinearLayout.LayoutParams boardLp = new LinearLayout.LayoutParams(-1, boardHeight);
        boardLp.topMargin = dp(6);
        boardShell.addView(boardView, boardLp);

        LinearLayout icons = new LinearLayout(this);
        icons.setOrientation(LinearLayout.HORIZONTAL);
        icons.setPadding(0, dp(8), 0, 0);
        icons.addView(iconAction("↻", "新局", v -> newGame()), new LinearLayout.LayoutParams(0, dp(64), 1));
        icons.addView(iconAction("↶", "悔棋", v -> undo()), new LinearLayout.LayoutParams(0, dp(64), 1));
        icons.addView(iconAction("⇅", "翻转", v -> flip()), new LinearLayout.LayoutParams(0, dp(64), 1));
        boardShell.addView(icons);

        LinearLayout delegated = new LinearLayout(this);
        delegated.setOrientation(LinearLayout.HORIZONTAL);
        delegated.setPadding(0, dp(8), 0, 0);
        autoButton = actionButton("自动代走：开", 0xffc7352d);
        autoButton.setOnClickListener(v -> {
            autoMode = !autoMode;
            refreshUi();
            maybeAutoMove();
        });
        manualAiButton = actionButton("本步 AI", 0xff287f83);
        manualAiButton.setOnClickListener(v -> playAiMove());
        delegated.addView(autoButton, new LinearLayout.LayoutParams(0, dp(46), 1));
        LinearLayout.LayoutParams manualLp = new LinearLayout.LayoutParams(0, dp(46), 1);
        manualLp.leftMargin = dp(8);
        delegated.addView(manualAiButton, manualLp);
        boardShell.addView(delegated);

        GridLayout stats = new GridLayout(this);
        stats.setColumnCount(2);
        stats.setPadding(0, dp(8), 0, 0);
        turnStat = statBox("当前方", "红方");
        roundStat = statBox("回合数", "0");
        redClock = statBox("红方用时", "00:00");
        blackClock = statBox("黑方用时", "00:00");
        addGrid(stats, turnStat, 1);
        addGrid(stats, roundStat, 1);
        addGrid(stats, redClock, 1);
        addGrid(stats, blackClock, 1);
        boardShell.addView(stats);

        analysisText = text("正在启动离线 Pikafish。", 13, 0xff766b5f, false);
        analysisText.setPadding(dp(10), dp(10), dp(10), dp(10));
        analysisText.setBackground(makeRound(0xfff4efe7, 0xffe2d9ce, dp(7)));
        // Kept for dialog state updates; hidden on the main screen to match the mobile layout.
        analysisText.setVisibility(View.GONE);

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
        body.addView(sliderRow("AI 用时", "每步 Pikafish 搜索时间", 100, 5000, 100, aiMoveTimeMs, value -> {
            aiMoveTimeMs = value;
            return String.format(Locale.US, "%.1fs", value / 1000f);
        }));
        body.addView(toggleRow("着法显示", "UCI", notationUci, value -> { notationUci = value; refreshUi(); renderAnalysisText(); }));
        body.addView(section("引擎", "Pikafish dev-20260628-553282ed / Android arm64"));
        dialog.show();
    }

    private void showAnalysisDialog() {
        Dialog dialog = sideDialog(Gravity.END, "AI 分析");
        LinearLayout body = dialog.findViewById(1001);
        body.addView(section("主变", lastAnalysis == null ? "正在分析" : lastAnalysis.pvText(notationUci)));
        String best = lastAnalysis == null ? "正在分析" : lastAnalysis.bestMoveText(notationUci);
        String score = lastAnalysis == null || lastAnalysis.scoreText.isEmpty() ? "等待分数" : lastAnalysis.scoreText;
        body.addView(section("推荐着法", best + "\n" + score));
        body.addView(section("走法记录", game.movesText(notationUci)));
        body.addView(section("说明", "score 正数为红方优势。WDL 顺序为红胜、和棋、黑胜。"));
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

    private View toggleRow(String title, String suffix, boolean checked, ToggleSetter setter) {
        LinearLayout row = new LinearLayout(this);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(10), dp(8), dp(10), dp(8));
        row.setBackground(makeRound(0xffffffff, 0xffe2d9ce, dp(8)));
        TextView label = text(title, 14, 0xff29241f, true);
        row.addView(label, new LinearLayout.LayoutParams(0, dp(42), 1));
        Button button = smallButton((checked ? "开启 " : "关闭 ") + suffix);
        button.setTextColor(checked ? 0xffffffff : 0xff29241f);
        button.setBackground(makeRound(checked ? 0xff287f83 : 0xffffffff, 0xffd2c7b8, dp(7)));
        final boolean[] value = new boolean[] { checked };
        button.setOnClickListener(v -> {
            value[0] = !value[0];
            button.setText((value[0] ? "开启 " : "关闭 ") + suffix);
            button.setTextColor(value[0] ? 0xffffffff : 0xff29241f);
            button.setBackground(makeRound(value[0] ? 0xff287f83 : 0xffffffff, 0xffd2c7b8, dp(7)));
            setter.set(value[0]);
        });
        row.addView(button, new LinearLayout.LayoutParams(dp(112), dp(38)));
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
        boardView.clearSelection();
        refreshUi();
        analyzePosition(false);
    }

    private void undo() {
        analysisSerial++;
        game.undo();
        lastAnalysis = null;
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
        engineBusy = true;
        thinkingText.setText(playBestMove ? "代走" : "分析");
        manualAiButton.setEnabled(false);
        autoButton.setEnabled(false);
        analysisText.setText("Pikafish 正在计算...");
        new Thread(() -> {
            try {
                AnalysisResult result = getEngine().analyze(moves, aiMoveTimeMs);
                runOnUiThread(() -> applyAnalysis(serial, result, playBestMove));
            } catch (Exception ex) {
                runOnUiThread(() -> {
                    if (serial != analysisSerial) return;
                    engineBusy = false;
                    thinkingText.setText("异常");
                    manualAiButton.setEnabled(true);
                    autoButton.setEnabled(true);
                    analysisText.setText("分析失败：" + ex.getMessage());
                });
            }
        }).start();
    }

    private PikafishEngine getEngine() throws IOException {
        if (engine == null) {
            File nnue = copyAsset("pikafish.nnue");
            File binary = new File(getApplicationInfo().nativeLibraryDir, "libpikafish.so");
            engine = new PikafishEngine(binary, nnue);
        }
        return engine;
    }

    private File copyAsset(String name) throws IOException {
        File dst = new File(getFilesDir(), name);
        if (dst.exists() && dst.length() > 0) return dst;
        try (InputStream in = getAssets().open(name); FileOutputStream out = new FileOutputStream(dst)) {
            byte[] buf = new byte[64 * 1024];
            int n;
            while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
        }
        return dst;
    }

    private void applyAnalysis(int serial, AnalysisResult result, boolean playBestMove) {
        if (serial != analysisSerial) return;
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
        analysisText.setText(lastAnalysis.summary(notationUci));
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
            analysisText.setText("AI 返回不合法着法，已停止代走：" + bestMove);
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
        TextView t = text(title + "\n" + value, 13, 0xff29241f, true);
        t.setPadding(dp(10), dp(7), dp(10), dp(7));
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
        TextView l = text(label, 11, 0xff766b5f, true);
        l.setGravity(Gravity.CENTER);
        box.addView(l, new LinearLayout.LayoutParams(-1, dp(20)));
        Button b = smallButton(icon);
        b.setTextSize(22);
        b.setOnClickListener(listener);
        box.addView(b, new LinearLayout.LayoutParams(-1, dp(44)));
        return box;
    }

    private void addGrid(GridLayout grid, View child, int weight) {
        GridLayout.LayoutParams lp = new GridLayout.LayoutParams();
        lp.width = 0;
        lp.height = GridLayout.LayoutParams.WRAP_CONTENT;
        lp.columnSpec = GridLayout.spec(GridLayout.UNDEFINED, weight);
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

    public static class BoardView extends View {
        static final float CROP_LEFT = 120f;
        static final float CROP_TOP = 120f;
        static final float CROP_RIGHT = 1680f;
        static final float CROP_BOTTOM = 1880f;
        static final float CROP_ASPECT = (CROP_BOTTOM - CROP_TOP) / (CROP_RIGHT - CROP_LEFT);
        private final GameState game;
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Map<String, Bitmap> bitmaps = new HashMap<>();
        private Bitmap board;
        private String selected;
        private boolean flipped;
        private Runnable moveListener;

        public BoardView(Activity activity, GameState game) {
            super(activity);
            this.game = game;
            board = BitmapFactory.decodeResource(getResources(), R.drawable.board);
            load("red_king", R.drawable.red_king); load("red_advisor", R.drawable.red_advisor);
            load("red_bishop", R.drawable.red_bishop); load("red_rook", R.drawable.red_rook);
            load("red_knight", R.drawable.red_knight); load("red_cannon", R.drawable.red_cannon);
            load("red_pawn", R.drawable.red_pawn); load("black_king", R.drawable.black_king);
            load("black_advisor", R.drawable.black_advisor); load("black_bishop", R.drawable.black_bishop);
            load("black_rook", R.drawable.black_rook); load("black_knight", R.drawable.black_knight);
            load("black_cannon", R.drawable.black_cannon); load("black_pawn", R.drawable.black_pawn);
        }

        private void load(String key, int res) { bitmaps.put(key, BitmapFactory.decodeResource(getResources(), res)); }
        public void setMoveListener(Runnable listener) { moveListener = listener; }
        public void setFlipped(boolean value) { flipped = value; invalidate(); }
        public void clearSelection() { selected = null; invalidate(); }

        @Override protected void onDraw(Canvas canvas) {
            float w = getWidth();
            float h = getHeight();
            float targetAspect = CROP_ASPECT;
            float drawW = w;
            float drawH = drawW * targetAspect;
            if (drawH > h) {
                drawH = h;
                drawW = drawH / targetAspect;
            }
            float left = (w - drawW) / 2f;
            float top = (h - drawH) / 2f;
            RectF dst = new RectF(left, top, left + drawW, top + drawH);
            android.graphics.Rect src = new android.graphics.Rect(
                    Math.round(CROP_LEFT), Math.round(CROP_TOP),
                    Math.round(CROP_RIGHT), Math.round(CROP_BOTTOM));
            canvas.drawBitmap(board, src, dst, paint);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(1);
            paint.setColor(0xffd2c7b8);
            canvas.drawRoundRect(dst, 4, 4, paint);
            paint.setStyle(Paint.Style.FILL);
            for (Map.Entry<String, Piece> entry : game.board.entrySet()) {
                float[] xy = point(entry.getKey(), w, h);
                float size = drawW * 0.095f;
                Bitmap bmp = bitmaps.get(entry.getValue().side + "_" + entry.getValue().role);
                if (bmp != null) canvas.drawBitmap(bmp, null, new RectF(xy[0]-size/2, xy[1]-size/2, xy[0]+size/2, xy[1]+size/2), paint);
                if (entry.getKey().equals(selected)) {
                    paint.setStyle(Paint.Style.STROKE);
                    paint.setStrokeWidth(4);
                    paint.setColor(0xff287f83);
                    canvas.drawCircle(xy[0], xy[1], size * 0.58f, paint);
                    paint.setStyle(Paint.Style.FILL);
                }
            }
        }

        @Override public boolean onTouchEvent(MotionEvent event) {
            if (event.getAction() != MotionEvent.ACTION_UP) return true;
            String square = nearestSquare(event.getX(), event.getY(), getWidth(), getHeight());
            Piece piece = game.board.get(square);
            if (selected == null) {
                if (piece != null && piece.side.equals(game.sideToMove())) selected = square;
            } else {
                String move = selected + square;
                if (game.legalMoves().contains(move)) {
                    game.applyMove(move);
                    selected = null;
                    if (moveListener != null) moveListener.run();
                } else if (piece != null && piece.side.equals(game.sideToMove())) {
                    selected = square;
                } else {
                    selected = null;
                }
            }
            invalidate();
            return true;
        }

        private float[] point(String square, float w, float h) {
            int file = GameState.FILES.indexOf(square.charAt(0));
            int rank = Character.digit(square.charAt(1), 10);
            if (flipped) { file = 8 - file; rank = 9 - rank; }
            float targetAspect = CROP_ASPECT;
            float drawW = w;
            float drawH = drawW * targetAspect;
            if (drawH > h) {
                drawH = h;
                drawW = drawH / targetAspect;
            }
            float left = (w - drawW) / 2f;
            float top = (h - drawH) / 2f;
            float rawX = 278 + file * 156;
            float rawY = 298 + (9 - rank) * 156;
            float x = left + (rawX - CROP_LEFT) / (CROP_RIGHT - CROP_LEFT) * drawW;
            float y = top + (rawY - CROP_TOP) / (CROP_BOTTOM - CROP_TOP) * drawH;
            return new float[] { x, y };
        }

        private String nearestSquare(float x, float y, float w, float h) {
            String best = "a0";
            float bestDist = Float.MAX_VALUE;
            for (int f = 0; f < 9; f++) {
                for (int r = 0; r < 10; r++) {
                    String sq = "" + GameState.FILES.charAt(f) + r;
                    float[] p = point(sq, w, h);
                    float dx = x - p[0], dy = y - p[1];
                    float d = dx * dx + dy * dy;
                    if (d < bestDist) { bestDist = d; best = sq; }
                }
            }
            return best;
        }
    }

    static class AnalysisResult {
        final String bestMove;
        final String scoreText;
        final String pv;
        final String bestMoveCn;
        final String pvCn;
        final int[] wdl;

        AnalysisResult(String bestMove, String scoreText, String pv, int[] wdl) {
            this(bestMove, scoreText, pv, "", "", wdl);
        }

        AnalysisResult(String bestMove, String scoreText, String pv, String bestMoveCn, String pvCn, int[] wdl) {
            this.bestMove = bestMove == null ? "" : bestMove;
            this.scoreText = scoreText == null ? "" : scoreText;
            this.pv = pv == null ? "" : pv;
            this.bestMoveCn = bestMoveCn == null ? "" : bestMoveCn;
            this.pvCn = pvCn == null ? "" : pvCn;
            this.wdl = wdl;
        }

        AnalysisResult withChinese(Map<String, Piece> board) {
            Map<String, Piece> copy = GameState.copyBoard(board);
            String bestCn = bestMove.length() == 4 ? GameState.moveToChinese(copy, bestMove) : "";
            StringBuilder cn = new StringBuilder();
            for (String move : pv.split("\\s+")) {
                if (move.length() != 4) continue;
                if (cn.length() > 0) cn.append(' ');
                cn.append(GameState.moveToChinese(copy, move));
                GameState.applyMove(copy, move);
            }
            return new AnalysisResult(bestMove, scoreText, pv, bestCn, cn.toString(), wdl);
        }

        String bestMoveText(boolean uci) {
            if (uci || bestMoveCn.isEmpty()) return bestMove.isEmpty() ? "无" : bestMove;
            return bestMoveCn + " (" + bestMove + ")";
        }

        String pvText(boolean uci) {
            String text = uci ? pv : pvCn;
            if (text == null || text.isEmpty()) text = uci ? bestMove : bestMoveCn;
            return text == null || text.isEmpty() ? "无主变" : text;
        }

        String summary(boolean uci) {
            String score = scoreText.isEmpty() ? "无分数" : scoreText;
            return "推荐 " + bestMoveText(uci) + "，" + score + "，主变 " + pvText(uci);
        }
    }

    static class PikafishEngine {
        private static final Pattern SCORE_RE = Pattern.compile("\\bscore\\s+(cp|mate)\\s+(-?\\d+)");
        private static final Pattern WDL_RE = Pattern.compile("\\bwdl\\s+(\\d+)\\s+(\\d+)\\s+(\\d+)\\b");
        private static final Pattern PV_RE = Pattern.compile("\\bpv(?:\\s+(.*))?$");
        private final Process process;
        private final Writer stdin;
        private final BufferedReader stdout;

        PikafishEngine(File binary, File nnue) throws IOException {
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

        synchronized AnalysisResult analyze(List<String> moves, int movetimeMs) throws IOException {
            send("setoption name MultiPV value 1");
            send("isready");
            readUntil("readyok");
            StringBuilder position = new StringBuilder("position startpos");
            if (!moves.isEmpty()) {
                position.append(" moves ");
                for (String move : moves) position.append(move).append(' ');
            }
            send(position.toString().trim());
            send("go movetime " + movetimeMs);

            String bestMove = "";
            String scoreText = "";
            String pv = "";
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
                Matcher score = SCORE_RE.matcher(line);
                if (score.find()) {
                    String kind = score.group(1);
                    int value = Integer.parseInt(score.group(2));
                    if ("black".equals(side)) value = -value;
                    scoreText = formatScore(kind, value);
                }
                Matcher wdlMatch = WDL_RE.matcher(line);
                if (wdlMatch.find()) {
                    int win = Integer.parseInt(wdlMatch.group(1));
                    int draw = Integer.parseInt(wdlMatch.group(2));
                    int lose = Integer.parseInt(wdlMatch.group(3));
                    wdl = "red".equals(side) ? new int[] { win, draw, lose } : new int[] { lose, draw, win };
                }
                Matcher pvMatch = PV_RE.matcher(line);
                if (pvMatch.find() && pvMatch.group(1) != null) pv = pvMatch.group(1).trim();
            }
            return new AnalysisResult(bestMove, scoreText, pv, wdl);
        }

        void close() {
            try {
                send("quit");
            } catch (Exception ignored) {
            }
            process.destroy();
        }

        private static String formatScore(String kind, int value) {
            if ("mate".equals(kind)) return value >= 0 ? "红方 M" + value : "黑方 M" + Math.abs(value);
            float pawns = value / 100f;
            if (pawns >= 0) return String.format(Locale.US, "红方 +%.2f", pawns);
            return String.format(Locale.US, "黑方 +%.2f", Math.abs(pawns));
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

    static class Piece {
        final String side, role;
        Piece(String side, String role) { this.side = side; this.role = role; }
    }

    static class GameState {
        static final String FILES = "abcdefghi";
        final Map<String, Piece> board = new HashMap<>();
        final ArrayList<String> moves = new ArrayList<>();
        final ArrayDeque<Map<String, Piece>> history = new ArrayDeque<>();
        String lastMove;

        void reset() {
            board.clear(); moves.clear(); history.clear(); lastMove = null;
            put("a0","red","rook"); put("b0","red","knight"); put("c0","red","bishop"); put("d0","red","advisor"); put("e0","red","king"); put("f0","red","advisor"); put("g0","red","bishop"); put("h0","red","knight"); put("i0","red","rook");
            put("b2","red","cannon"); put("h2","red","cannon"); put("a3","red","pawn"); put("c3","red","pawn"); put("e3","red","pawn"); put("g3","red","pawn"); put("i3","red","pawn");
            put("a9","black","rook"); put("b9","black","knight"); put("c9","black","bishop"); put("d9","black","advisor"); put("e9","black","king"); put("f9","black","advisor"); put("g9","black","bishop"); put("h9","black","knight"); put("i9","black","rook");
            put("b7","black","cannon"); put("h7","black","cannon"); put("a6","black","pawn"); put("c6","black","pawn"); put("e6","black","pawn"); put("g6","black","pawn"); put("i6","black","pawn");
        }
        void put(String sq, String side, String role) { board.put(sq, new Piece(side, role)); }
        String sideToMove() { return moves.size() % 2 == 0 ? "red" : "black"; }
        void applyMove(String move) {
            history.push(new HashMap<>(board));
            Piece p = board.remove(move.substring(0,2));
            if (p != null) board.put(move.substring(2,4), p);
            moves.add(move); lastMove = move;
        }
        void undo() {
            if (history.isEmpty()) return;
            board.clear(); board.putAll(history.pop());
            if (!moves.isEmpty()) moves.remove(moves.size()-1);
            lastMove = moves.isEmpty() ? null : moves.get(moves.size()-1);
        }
        String firstLegalMove() { List<String> legal = legalMoves(); return legal.isEmpty() ? null : legal.get(0); }
        Map<String, Piece> boardSnapshot() { return copyBoard(board); }
        String movesText(boolean uci) {
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

        List<String> legalMoves() {
            ArrayList<String> result = new ArrayList<>();
            String side = sideToMove();
            for (String move : pseudoLegalMoves(board, side)) {
                Map<String, Piece> next = copyBoard(board);
                applyMove(next, move);
                if (!isInCheck(next, side)) result.add(move);
            }
            return result;
        }

        List<String> pseudoLegalMoves() {
            ArrayList<String> result = new ArrayList<>();
            String side = sideToMove();
            for (String sq : new ArrayList<>(board.keySet())) {
                Piece p = board.get(sq);
                if (p != null && p.side.equals(side)) pieceMoves(sq, p, result);
            }
            return result;
        }
        void pieceMoves(String sq, Piece p, List<String> out) {
            int f = FILES.indexOf(sq.charAt(0)), r = Character.digit(sq.charAt(1),10);
            switch (p.role) {
                case "rook": slide(sq,p, out, false); break;
                case "cannon": slide(sq,p, out, true); break;
                case "knight": for (int[] m : new int[][]{{1,2,0,1},{-1,2,0,1},{1,-2,0,-1},{-1,-2,0,-1},{2,1,1,0},{2,-1,1,0},{-2,1,-1,0},{-2,-1,-1,0}}) if (!board.containsKey(name(f+m[2],r+m[3]))) add(sq,p,f+m[0],r+m[1],out); break;
                case "bishop": for (int[] m : new int[][]{{2,2},{-2,2},{2,-2},{-2,-2}}) { int tr=r+m[1]; if ((p.side.equals("red")&&tr>4)||(p.side.equals("black")&&tr<5)) continue; if(!board.containsKey(name(f+m[0]/2,r+m[1]/2))) add(sq,p,f+m[0],tr,out);} break;
                case "advisor": for (int[] m : new int[][]{{1,1},{-1,1},{1,-1},{-1,-1}}) if (palace(p.side,f+m[0],r+m[1])) add(sq,p,f+m[0],r+m[1],out); break;
                case "king":
                    for (int[] m : new int[][]{{1,0},{-1,0},{0,1},{0,-1}}) if (palace(p.side,f+m[0],r+m[1])) add(sq,p,f+m[0],r+m[1],out);
                    int dy = p.side.equals("red") ? 1 : -1;
                    int y = r + dy;
                    while (inside(f, y)) {
                        Piece t = board.get(name(f, y));
                        if (t != null) {
                            if (!t.side.equals(p.side) && "king".equals(t.role)) out.add(sq + name(f, y));
                            break;
                        }
                        y += dy;
                    }
                    break;
                case "pawn": int forward=p.side.equals("red")?1:-1; add(sq,p,f,r+forward,out); boolean crossed=p.side.equals("red")?r>=5:r<=4; if(crossed){add(sq,p,f-1,r,out); add(sq,p,f+1,r,out);} break;
            }
        }
        void slide(String sq, Piece p, List<String> out, boolean cannon) {
            int f = FILES.indexOf(sq.charAt(0)), r = Character.digit(sq.charAt(1),10);
            for (int[] d : new int[][]{{1,0},{-1,0},{0,1},{0,-1}}) {
                boolean screen=false; int x=f+d[0], y=r+d[1];
                while (inside(x,y)) {
                    Piece t=board.get(name(x,y));
                    if(!cannon){ if(t==null) out.add(sq+name(x,y)); else { if(!t.side.equals(p.side)) out.add(sq+name(x,y)); break; } }
                    else if(!screen){ if(t==null) out.add(sq+name(x,y)); else screen=true; }
                    else { if(t!=null){ if(!t.side.equals(p.side)) out.add(sq+name(x,y)); break; } }
                    x+=d[0]; y+=d[1];
                }
            }
        }
        void add(String sq, Piece p, int f, int r, List<String> out) { if(!inside(f,r)) return; Piece t=board.get(name(f,r)); if(t==null || !t.side.equals(p.side)) out.add(sq+name(f,r)); }
        boolean palace(String side,int f,int r){ return f>=3&&f<=5&&(side.equals("red")?r>=0&&r<=2:r>=7&&r<=9); }
        boolean inside(int f,int r){ return f>=0&&f<9&&r>=0&&r<10; }
        String name(int f,int r){ if(!inside(f,r)) return ""; return ""+FILES.charAt(f)+r; }

        static Map<String, Piece> copyBoard(Map<String, Piece> source) {
            return new HashMap<>(source);
        }

        static List<String> pseudoLegalMoves(Map<String, Piece> source, String side) {
            GameState temp = new GameState();
            temp.board.clear();
            temp.board.putAll(source);
            ArrayList<String> result = new ArrayList<>();
            for (String sq : new ArrayList<>(temp.board.keySet())) {
                Piece p = temp.board.get(sq);
                if (p != null && p.side.equals(side)) temp.pieceMoves(sq, p, result);
            }
            return result;
        }

        static boolean isInCheck(Map<String, Piece> source, String side) {
            String kingSquare = null;
            for (Map.Entry<String, Piece> entry : source.entrySet()) {
                Piece p = entry.getValue();
                if (p.side.equals(side) && "king".equals(p.role)) {
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

        static void applyMove(Map<String, Piece> board, String move) {
            Piece p = board.remove(move.substring(0, 2));
            if (p != null) board.put(move.substring(2, 4), p);
        }

        static String moveToChinese(Map<String, Piece> board, String move) {
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
                boolean forward = "red".equals(piece.side) ? ty > fy : ty < fy;
                action = forward ? "进" : "退";
                suffix = dstFile;
            } else if (fx == tx) {
                boolean forward = "red".equals(piece.side) ? ty > fy : ty < fy;
                action = forward ? "进" : "退";
                suffix = stepName(piece.side, Math.abs(ty - fy));
            } else {
                action = "平";
                suffix = dstFile;
            }
            return label + srcFile + action + suffix;
        }

        static String label(Piece p) {
            if ("king".equals(p.role)) return "red".equals(p.side) ? "帅" : "将";
            if ("advisor".equals(p.role)) return "red".equals(p.side) ? "仕" : "士";
            if ("bishop".equals(p.role)) return "red".equals(p.side) ? "相" : "象";
            if ("rook".equals(p.role)) return "车";
            if ("knight".equals(p.role)) return "马";
            if ("cannon".equals(p.role)) return "炮";
            return "red".equals(p.side) ? "兵" : "卒";
        }

        static String fileName(String side, int file) {
            String redDigits = "九八七六五四三二一";
            return "red".equals(side) ? String.valueOf(redDigits.charAt(file)) : String.valueOf(file + 1);
        }

        static String stepName(String side, int delta) {
            String redDigits = "九八七六五四三二一";
            return "red".equals(side) ? String.valueOf(redDigits.charAt(9 - delta)) : String.valueOf(delta);
        }
    }
}
