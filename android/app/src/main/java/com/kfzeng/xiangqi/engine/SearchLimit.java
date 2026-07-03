package com.kfzeng.xiangqi.engine;

import java.util.Locale;

public class SearchLimit {
    public final String mode;
    public final int value;

    public SearchLimit(String mode, int value) {
        if ("depth".equals(mode)) {
            this.mode = "depth";
            this.value = Math.max(1, Math.min(30, value));
        } else {
            this.mode = "movetime";
            this.value = Math.max(50, Math.min(30000, value));
        }
    }

    public static SearchLimit movetime(int ms) {
        return new SearchLimit("movetime", ms);
    }

    public static SearchLimit depth(int depth) {
        return new SearchLimit("depth", depth);
    }

    public String goCommand() {
        return "go " + mode + " " + value;
    }

    public String label() {
        if ("depth".equals(mode)) return "depth " + value;
        return String.format(Locale.US, "%.1fs", value / 1000f);
    }
}
