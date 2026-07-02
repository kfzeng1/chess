# 象棋 AI 项目交接文档

## 📋 项目概述

这是一个基于 Pikafish 引擎的象棋 AI 对弈平台项目。目前已完成基础资源生成和 UI 设计。

---

## 🎯 当前进度

### ✅ 已完成

1. **Pikafish 引擎集成**
   - 引擎位置：`engines/pikafish-avxvnni`
   - UCI 协议通信已测试
   - 支持 MultiPV（多主变例）
   - 返回格式：`bestmove h2e2 ponder h9g7`

2. **棋盘和棋子资源**
   - 棋盘：`assets/current-draft/board.png` (1800x2000)
   - 14个棋子：`assets/current-draft/pieces/*.png` (512x512)
   - 生成脚本：
     - `tools/asset-generation/render_xiangqi_board.py`
     - `tools/asset-generation/render_xiangqi_pieces.py`
   - 设计风格：现代扁平、网页友好
   - 颜色：红方（#C62D26）、黑方（#342D2D）

3. **UI 设计预览图**
   - 预览图：`assets/ui-mockup-v4.png` (1920x1080)
   - 生成脚本：`tools/design/generate_ui_mockup_v4.py`
   - 布局：三栏（控制 + 棋盘 + 分析）

4. **文档**
   - `docs/ASSET_HANDOFF.md` - 资源设计说明
   - `docs/UI_DESIGN.md` - UI 设计文档
   - `docs/UI_MOCKUP.md` - UI 预览说明
   - `README.md` - 项目说明

---

## ⚠️ 已知问题

### 1. UI 预览图质量差
**问题描述**：
- 当前 `assets/ui-mockup-v4.png` 质量很差
- 字体渲染不清晰，有锯齿
- 整体视觉效果不专业

**原因分析**：
- PIL/Pillow 生成的 PNG 图像质量限制
- 字体抗锯齿效果不够好
- 可能需要更高分辨率或不同的渲染方法

**建议解决方案**：
1. **使用设计工具重做**
   - 使用 Figma / Sketch / Adobe XD 重新设计
   - 导出为高质量 PNG 或 SVG
   
2. **改用 Web 技术生成**
   - 用 HTML/CSS/Canvas 渲染
   - 使用 Puppeteer 截图生成高质量预览图
   
3. **提高当前脚本质量**
   - 增加输出分辨率（如 3840x2160）
   - 使用更好的字体渲染库
   - 导出为 SVG 而非 PNG

### 2. 棋子和棋盘视觉效果
**反馈**：用户认为棋盘和棋子设计"很丑"

**当前设计**：
- 扁平风格，简单渐变
- 颜色鲜艳但缺乏质感
- 缺少细节和精致感

**建议改进**：
- 参考专业象棋应用的设计
- 考虑使用更写实的风格
- 增加光影、纹理等细节
- 或者聘请专业设计师重新设计

---

## 🚀 下一步开发任务

### 1. 改进 UI 预览图（优先级：高）
- [ ] 使用专业设计工具重做 UI 预览图
- [ ] 确保字体清晰、布局美观
- [ ] 导出高质量资源

### 2. 前端开发（优先级：高）
- [ ] 选择前端框架（推荐 React 或 Vue 3）
- [ ] 实现棋盘组件
  - 棋盘渲染
  - 棋子拖拽
  - 合法移动高亮
  - 上一步移动显示
- [ ] 实现控制面板
  - 所有按钮功能
  - AI 强度滑块
  - 玩家模式切换
- [ ] 实现分析面板
  - 主变例显示
  - 推荐着法列表
  - 点击走棋功能

### 3. 后端/引擎接口（优先级：高）
- [ ] 实现 UCI 引擎通信
  - 启动/停止引擎
  - 发送位置和命令
  - 解析引擎输出
- [ ] 实现 API 接口
  - `/api/analyze` - 获取分析结果
  - `/api/move` - 执行着法
  - `/api/new-game` - 开始新局
- [ ] WebSocket 实时通信
  - 实时胜率更新
  - 主变例实时显示
  - AI 计算进度

### 4. 游戏逻辑（优先级：中）
- [ ] 象棋规则引擎
  - 合法移动判断
  - 将军/将死检测
  - 和棋判断
- [ ] 游戏状态管理
  - 棋局历史记录
  - 悔棋功能
  - 翻转棋盘
- [ ] 人机/人人对局模式

### 5. 资源改进（优先级：中）
- [ ] 重新设计棋盘和棋子
- [ ] 增加音效
- [ ] 增加动画效果

---

## 📂 项目结构

```
chinese_chess/
├── assets/
│   ├── current-draft/
│   │   ├── board.png              # 棋盘 (1800x2000)
│   │   └── pieces/                # 14个棋子 (512x512)
│   ├── reference-previews/
│   │   ├── pieces-preview.png     # 棋子预览表
│   │   └── start-position-preview.png  # 开局预览
│   └── ui-mockup-v4.png           # UI 预览图（质量差，需重做）
├── docs/
│   ├── ASSET_HANDOFF.md           # 资源交接文档
│   ├── UI_DESIGN.md               # UI 设计说明
│   └── UI_MOCKUP.md               # UI 预览说明
├── engines/
│   └── pikafish-avxvnni           # Pikafish 引擎
├── tools/
│   ├── asset-generation/
│   │   ├── render_xiangqi_board.py    # 生成棋盘
│   │   └── render_xiangqi_pieces.py   # 生成棋子
│   └── design/
│       └── generate_ui_mockup_v4.py   # 生成 UI 预览图
└── README.md
```

---

## 🔧 技术栈建议

### 前端
- **框架**：React 18 / Vue 3
- **UI 库**：Ant Design / Element Plus（可选）
- **状态管理**：Zustand / Pinia
- **棋盘渲染**：HTML Canvas / SVG
- **构建工具**：Vite

### 后端
- **语言**：Node.js / Python / Go
- **框架**：Express / FastAPI / Gin
- **通信**：WebSocket / Server-Sent Events
- **进程管理**：child_process (Node.js) / subprocess (Python)

### 部署
- **前端**：Vercel / Netlify / Nginx
- **后端**：Docker / PM2
- **引擎**：需要服务器端运行（CPU 密集型）

---

## 🎨 UI 功能需求

### 左侧控制面板
1. **开新局** - 重置棋盘到初始位置
2. **悔棋** - 撤销 1-2 步（人机对局撤销2步）
3. **翻转棋盘** - 旋转 180 度视角
4. **红方/黑方选择** - 人类 / AI 切换
5. **AI 强度设置** - 滑块调节搜索深度（1-20）
6. **本步 AI 走** - 强制 AI 立即走棋
7. **对局状态显示** - 回合、步数、用时

### 中央棋盘区
1. **胜率条** - 实时显示红/黑/和的概率
2. **棋盘显示** - 使用生成的棋盘和棋子资源
3. **交互**：
   - 点击选择棋子
   - 高亮可走位置
   - 拖拽移动棋子
   - 显示上一步移动

### 右侧分析面板
1. **主变例** - AI 计算的最佳着法序列（5-10步）
2. **推荐着法** - MultiPV 显示前 5 个选项
   - 显示着法、评分
   - 点击可直接走棋
   - 第一个标记"最佳"

---

## 🔌 Pikafish 引擎使用

### UCI 命令
```bash
# 初始化
echo "uci" | ./engines/pikafish-avxvnni

# 设置 MultiPV（获取多个推荐）
echo "setoption name MultiPV value 5"

# 设置位置（开局）
echo "position startpos"

# 设置位置（带着法）
echo "position startpos moves e2e4 e7e5"

# 开始搜索
echo "go depth 15"    # 固定深度
echo "go movetime 5000"  # 固定时间（毫秒）

# 停止搜索
echo "stop"

# 退出
echo "quit"
```

### 输出格式
```
info depth 15 score cp 176 pv h2e2 h9g7 h0g2
bestmove h2e2 ponder h9g7
```

- `score cp 176` - 评分（厘兵），正数=红方优势
- `pv` - 主变例（最佳着法序列）
- `bestmove` - 最佳着法
- `ponder` - 预测对手回应

### 坐标系统
- 文件（列）：a-i（左到右）
- 等级（行）：0-9（红方底部是 0）
- 示例：`h2e2` = 从 h2 到 e2（炮平移）

---

## 📝 资源生成

### 重新生成棋盘和棋子
```bash
# 生成棋盘
python3 tools/asset-generation/render_xiangqi_board.py

# 生成棋子和预览图
python3 tools/asset-generation/render_xiangqi_pieces.py
```

### 修改设计
编辑脚本中的颜色常量：
- `render_xiangqi_board.py` - 棋盘配色
- `render_xiangqi_pieces.py` - 棋子配色

---

## ⚡ 快速开始建议

### 第一步：改进 UI 预览图
使用 Figma 或其他专业工具重新设计 UI，参考当前布局但提高视觉质量。

### 第二步：搭建前端框架
```bash
# 使用 Vite + React
npm create vite@latest chinese-chess-frontend -- --template react-ts
cd chinese-chess-frontend
npm install
npm run dev
```

### 第三步：实现基础棋盘
- 渲染 9x10 棋盘网格
- 加载并显示棋子图片
- 实现点击选择和移动

### 第四步：引擎通信
- 创建后端 API
- 实现 UCI 引擎通信
- 返回 JSON 格式的分析结果

---

## 🤝 联系与协作

如有问题，请查看：
- `README.md` - 项目基本信息
- `docs/` - 详细文档
- GitHub Issues - 提问和反馈

---

## ⚠️ 重要提醒

1. **UI 预览图务必重做** - 当前质量不可用
2. **资源设计需改进** - 考虑聘请设计师或使用专业模板
3. **引擎通信已测试** - 可以直接使用
4. **前端是重点** - 用户体验最重要

---

**交接日期**：2026-07-02
**项目状态**：设计阶段，需要重做 UI 和前端开发
**优先级**：UI 改进 > 前端开发 > 引擎集成

祝下一位开发者顺利！🚀
