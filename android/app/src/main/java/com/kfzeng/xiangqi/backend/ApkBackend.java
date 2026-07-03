package com.kfzeng.xiangqi.backend;

import android.content.Context;

import com.kfzeng.xiangqi.core.GameState;
import com.kfzeng.xiangqi.engine.AnalysisResult;
import com.kfzeng.xiangqi.engine.PikafishEngine;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.List;

public class ApkBackend {
    private final Context context;
    private final GameState game = new GameState();
    private PikafishEngine engine;

    public ApkBackend(Context context) {
        this.context = context.getApplicationContext();
    }

    public GameState game() {
        return game;
    }

    public AnalysisResult analyze(List<String> moves, int movetimeMs) throws IOException {
        return getEngine().analyze(moves, movetimeMs);
    }

    public String positionId(List<String> moves) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(String.join("\n", moves).getBytes(java.nio.charset.StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder();
            for (int i = 0; i < 8; i++) hex.append(String.format("%02x", hash[i]));
            return hex.toString();
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException(ex);
        }
    }

    public void close() {
        if (engine != null) {
            engine.close();
            engine = null;
        }
    }

    private PikafishEngine getEngine() throws IOException {
        if (engine == null) {
            File nnue = copyAsset("pikafish.nnue");
            File binary = new File(context.getApplicationInfo().nativeLibraryDir, "libpikafish.so");
            engine = new PikafishEngine(binary, nnue);
        }
        return engine;
    }

    private File copyAsset(String name) throws IOException {
        File dst = new File(context.getFilesDir(), name);
        if (dst.exists() && dst.length() > 0) return dst;
        try (InputStream in = context.getAssets().open(name); FileOutputStream out = new FileOutputStream(dst)) {
            byte[] buf = new byte[64 * 1024];
            int n;
            while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
        }
        return dst;
    }
}
