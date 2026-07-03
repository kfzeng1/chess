package com.kfzeng.xiangqi.ui;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.view.MotionEvent;
import android.view.View;

import com.kfzeng.xiangqi.R;
import com.kfzeng.xiangqi.core.GameState;
import com.kfzeng.xiangqi.core.Piece;

import java.util.HashMap;
import java.util.Map;

public class BoardView extends View {
    public static final float CROP_LEFT = 120f;
    public static final float CROP_TOP = 120f;
    public static final float CROP_RIGHT = 1680f;
    public static final float CROP_BOTTOM = 1880f;
    public static final float CROP_ASPECT = (CROP_BOTTOM - CROP_TOP) / (CROP_RIGHT - CROP_LEFT);

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

    private void load(String key, int res) {
        bitmaps.put(key, BitmapFactory.decodeResource(getResources(), res));
    }

    public void setMoveListener(Runnable listener) {
        moveListener = listener;
    }

    public void setFlipped(boolean value) {
        flipped = value;
        invalidate();
    }

    public void clearSelection() {
        selected = null;
        invalidate();
    }

    @Override protected void onDraw(Canvas canvas) {
        float w = getWidth();
        float h = getHeight();
        float drawW = w;
        float drawH = drawW * CROP_ASPECT;
        if (drawH > h) {
            drawH = h;
            drawW = drawH / CROP_ASPECT;
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
            if (bmp != null) canvas.drawBitmap(bmp, null, new RectF(xy[0] - size / 2, xy[1] - size / 2, xy[0] + size / 2, xy[1] + size / 2), paint);
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
        if (flipped) {
            file = 8 - file;
            rank = 9 - rank;
        }
        float drawW = w;
        float drawH = drawW * CROP_ASPECT;
        if (drawH > h) {
            drawH = h;
            drawW = drawH / CROP_ASPECT;
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
                String square = "" + GameState.FILES.charAt(f) + r;
                float[] p = point(square, w, h);
                float dx = x - p[0];
                float dy = y - p[1];
                float d = dx * dx + dy * dy;
                if (d < bestDist) {
                    bestDist = d;
                    best = square;
                }
            }
        }
        return best;
    }
}
