# Revisica — TODO

**Last updated:** 2026-04-11

Full plan: `~/.claude/plans/immutable-dazzling-mochi.md`
Spec: `docs/specs/desktop-app.md`

---

## Step 1: Profiles + Ingestion ✅

### Profiles (`src/revisica/profiles/`) ✅

- [x] **`profiles/config.py`** — `ReviewMode`, `ReviewConfig`, `FocusRequest`
- [x] **`profiles/presets.py`** — Polish 和 Review 预设
- [x] **CLI `--mode polish|review`** — 已加到 `review` 子命令

### Ingestion (`src/revisica/ingestion/`) ✅

- [x] **`ingestion/types.py`** — `RevisicaDocument`, `DocumentSection`, `DocumentMetadata`
- [x] **`ingestion/base.py`** — `BaseParser` ABC
- [x] **`ingestion/normalize.py`** — section tree 提取 + metadata 解析
- [x] **`ingestion/pandoc_parser.py`** — Pandoc subprocess（需安装 pandoc）
- [x] **`ingestion/tex_parser.py`** — 额外增加：无依赖的 .tex 基础解析器（regex），作为 pandoc 不可用时的 fallback
- [x] **`ingestion/registry.py`** — `parse_document()` 入口 + 自动检测
- [x] **CLI `revisica ingest`** — 独立测试子命令，输出 JSON
- [ ] **`ingestion/mathpix_parser.py`** — Mathpix API（需要 API key，延后到有 key 时实现）
- [ ] **`ingestion/mineru_parser.py`** — MinerU 本地（需要 GPU，延后）
- [ ] **`ingestion/marker_parser.py`** — Marker 本地（延后）
- [ ] **接入 review pipeline** — 延后到 Step 5 (LangGraph graphs) 时一起做

### 验证 ✅

- [x] `revisica ingest examples/minimal_paper.tex` → 正确提取 title、3 个 section（nested）
- [ ] `revisica ingest paper.pdf --parser mathpix` → 延后（需 API key）

---

## Step 2: Provider Package ✅

- [x] **`providers/base.py`** — `BaseProvider` ABC
- [x] **`providers/tools.py`** — 本地工具实现（Read, Glob, Grep）+ `execute_tool()` dispatcher
- [x] **`providers/subprocess_env.py`** — 共享 subprocess 环境配置
- [x] **`providers/cli_codex.py`** — `CodexCliProvider(BaseProvider)` — 从 review.py 提取
- [x] **`providers/cli_claude.py`** — `ClaudeCliProvider(BaseProvider)` — 从 review.py 提取
- [x] **`providers/__init__.py`** — `ProviderRegistry` + `get_provider()` + 别名（codex→codex-cli, claude→claude-cli）
- [x] **`providers/provider_config.py`** — `~/.revisica/config.json` + env var override
- [x] **重构 `review.py`** — `_run_provider()`/`_run_provider_agent()` 改为 registry 调用，删除旧实现（636行→371行）
- [ ] **重构 `bootstrap.py`** — 延后（当前的 `detect_platforms()` 仍可工作，bootstrap.py 重构等 graphs 时一起做）

---

## Step 3: API Providers ✅

- [x] **`providers/api_anthropic.py`** — `AnthropicApiProvider` + Messages API tool-use agent loop（最多 20 轮）
- [x] **`providers/api_openai.py`** — `OpenAiApiProvider` + function calling agent loop（最多 20 轮）
- [x] **更新 `model_router.py`** — 新增 `anthropic-api` 和 `openai-api` 路由表 + 别名
- [x] **更新 `pyproject.toml`** — 可选依赖 `[api]`（anthropic, openai）、`[serve]`（fastapi, uvicorn）、`[all]`

### 验证（需要 API key 时才能跑）

- [ ] `ANTHROPIC_API_KEY=... revisica review --reviewer-a anthropic-api` → 延后验证
- [ ] `OPENAI_API_KEY=... revisica review --reviewer-a openai-api` → 延后验证

---

## Step 4: Agent Definitions ✅

- [x] **`agents/types.py`** — `AgentDefinition` frozen dataclass (name, role, description, system_prompt, tools, output_format, categories, temperature)
- [x] **`agents/definitions/`** — 11 个 agent 定义文件，每个导出一个 `AGENT` 实例：writing_basic, writing_structure, writing_venue, writing_judge, proof_reviewer, proof_self_checker, proof_adjudicator, claim_verifier, notation_tracker, formula_cross_checker, polish_agent（新增）
- [x] **`agents/registry.py`** — `get_agent(name)` + `list_agents()`，11 个 agent 全部注册
- [ ] **`agents/translators/`** — 延后到 graphs 接入时再做（当前 `AgentSpec` 仍作为桥接）

---

## Step 5: LangGraph Graphs

最大的重构步骤。orchestration 从 ThreadPoolExecutor 迁移到 LangGraph。

### 前置：LangGraph bundle size spike test

- [ ] **Spike test** — 在开始前测试：`pip install langgraph langchain-anthropic langchain-openai && pyinstaller --onefile`，测量打包大小和冷启动时间。如果过大，研究 lazy import 或 trim 方案。

### Graph 实现 (`src/revisica/graphs/`)

- [ ] **`graphs/state.py`** — 定义 `UnifiedState`、`WritingState`、`MathState` TypedDict。包含 `RevisicaDocument`、`ReviewConfig`、`focus_results`、`user_feedback` 字段。

- [ ] **`graphs/nodes/`** — 复用现有纯逻辑代码作为节点函数。每个文件一个节点或一组相关节点（≤300行）。从 `math_extraction.py`、`math_deterministic.py`、`section_combiner.py`、`claim_extractor.py` 等直接 import。

- [ ] **`graphs/polish.py`** — 最简图：单个 writing agent 节点 → write report → END。用来验证 LangGraph 框架能正常工作。

- [ ] **`graphs/math.py`** — Math 子图：extract → deterministic checks → conditional LLM review → self-check → adjudicate → write report。复用 `math_extraction.py`、`math_deterministic.py`、`math_llm_review.py` 作为节点。

- [ ] **`graphs/writing.py`** — Writing 子图：extract sections → parallel fan-out（roles + section combos + claim verify）→ collect → self-check → judge → write report。最复杂的图，替代 `writing_review.py` 的 ThreadPoolExecutor(12)。

- [ ] **`graphs/unified.py`** — 顶层图：ingest → mode routing（Polish vs Review）→ parallel [writing | math] → merge → report → INTERRUPT → optional Focus loop → END。

- [ ] **`graphs/focus.py`** — Focus 子图：load section → parallel [focused writing + focused math] → merge → append to report。由 HITL interrupt 触发，接收 `FocusRequest`。

- [ ] **重新接线公共 API** — `review_unified()`、`review_writing_file()`、`review_math_file()` 内部改为运行 graph。函数签名不变，输出格式不变。CLI 和 benchmark 零改动。

- [ ] **添加 `langgraph` 依赖** — `pyproject.toml` 添加 `langgraph>=1.0`。

### 验证

- [ ] `revisica review --mode polish examples/minimal_paper.tex` → Polish 模式工作
- [ ] `revisica math-review examples/minimal_paper.tex` → 与重构前输出一致
- [ ] `revisica writing-review examples/minimal_paper.tex` → 与重构前输出一致
- [ ] `revisica review examples/minimal_paper.tex` → 完整 review 与重构前一致
- [ ] `revisica benchmark-run --suite math-cases --mode deterministic-only` → 通过
- [ ] Focus 子图可以编程触发：给定 section_id + instruction，产出定向分析

---

## Step 6: HITL + Streaming

让 graph 可以暂停等待用户交互，并把进度实时推送到前端。

- [ ] **`interrupt_before` 节点** — 在 writing 和 math 子图的 HITL gate 处加 `interrupt_before`。graph 执行到此暂停，状态持久化。

- [ ] **`SqliteSaver` checkpointer** — 配置 `~/.revisica/checkpoints.db`。graph 状态在进程重启后可恢复。Desktop app 打包时随 app 一起。

- [ ] **SSE streaming endpoint** — FastAPI 端点消费 `graph.astream_events()`。Electron 前端通过 `EventSource` 订阅。替代之前计划的自定义 `ProgressEvent`。

### 验证

- [ ] graph 在 interrupt 节点暂停，用户发送 FocusRequest 后恢复执行
- [ ] 重启进程后可以从 checkpoint 恢复
- [ ] SSE endpoint 实时推送节点执行状态

---

## Step 7: Desktop App

FastAPI + Electron + React + renderer。

### API Server

- [ ] **`api.py`** — FastAPI server，包装 graph 执行。端点：review（启动）、status（轮询）、results（获取）、providers（配置）、ingest（解析）。`revisica serve` 子命令启动。

### Electron Shell

- [ ] **Electron main process** — 启动时 spawn Python sidecar（dev: `python -m revisica.api`；prod: PyInstaller binary）。轮询 `/api/health` 等待就绪。退出时 SIGTERM → 5s 后 SIGKILL。

### React Frontend

- [ ] **Home 页** — 拖放文件 / 文件选择器（PDF/.tex）、mode 选择器（Polish/Review）、venue profile 下拉、provider 状态 badge、custom instructions 输入框、Start 按钮。

- [ ] **Progress 页** — 轮询 `/api/status`（或 SSE），显示每个 lane/task 的实时状态（pending/running/done/failed），完成后自动跳转 Results。

- [ ] **Results 页** — 渲染论文 HTML（左侧主体 + 右侧批注栏）。Tab 切换 Summary/Writing/Math。Findings 作为 margin notes 锚定到 section。每个 section 有 "深挖" 按钮触发 Focus。

- [ ] **Settings 页** — Provider 列表（状态 + 配置）、API key 输入（遮掩显示）、Mathpix key 配置、"Test Connection" 按钮、版本信息。

### Renderer (`desktop/src/renderer/`)

- [ ] **论文渲染组件** — `RevisicaDocument.markdown` → HTML：用 `react-markdown` + `remark-math` + MathJax（或 `mathpix-markdown-it`）。数学公式继承衬线字体。

- [ ] **Design theme** — Claude Code 暖色调 + 复古论文风格。背景 `#FAF6F0`（温暖羊皮纸色）、文字 `#2C2825`（暖炭色）、衬线字体 Source Serif 4、Findings 用 amber/orange/red 分级。Dark mode 自动跟随系统。

- [ ] **批注系统** — Findings 作为右侧 margin notes 显示。点击高亮对应文本。颜色编码：amber（建议）、deep orange（警告）、warm red（错误）、muted green（已验证）。

### Packaging

- [ ] **PyInstaller spec** — 冻结 Python backend 为单文件或目录。输出到 `desktop/resources/python-backend`。

- [ ] **electron-builder 配置** — macOS DMG 输出。code signing + notarization。注意：Python `.so` 文件必须显式列在签名配置中。

- [ ] **GitHub Actions CI** — 构建 Python sidecar → 构建 Electron → 签名 → 公证 → 上传 DMG。

### 验证

- [ ] `revisica serve` 启动 → `curl /api/health` 返回 200
- [ ] `npm run dev` 在 `desktop/` 中打开 Electron 窗口，能配置 provider、触发并查看完整 review
- [ ] `npm run build:mac` 产出可启动的 `.app` bundle

---

## Step 8: Module Extraction（可选，重构优化）

Spec 列出的独立模块中有两个是从现有代码提取：

- [ ] **`math_check/` 模块提取** — 把 `math_deterministic.py`、`math_extraction.py`、`math_types.py`、`math_artifacts.py` 移到 `src/revisica/math_check/` 包中。形成独立可测试模块：输入 LaTeX → 输出 `list[MathIssue]`。纯 SymPy，零 LLM。

- [ ] **`eval/` 模块提取** — 把 `benchmark_framework.py`、`benchmark_refine.py`、`benchmark_math.py`、`benchmark_writing.py`、`benchmark_provenance.py`、`benchmark_history.py` 移到 `src/revisica/eval/` 包中。形成独立评估框架：输入 review output + ground truth → 输出 metrics。

---

## Paused: Refine.ink Recall Gap

**状态：** 暂停（desktop app 基础搭好后继续）
**当前：** 83.3% recall on targeting-interventions (5/6, LLM judge)

- [ ] **Proof-statement consistency checker** — 见 `docs/specs/proof-statement-checker.md`
- [ ] **全量 benchmark 重跑** — 4 个 case 全部 `--use-llm-judge`
- [ ] **Algorithm reviewer agent** — 分析伪代码/算法块
- [ ] **自适应 section combination budget** — 根据论文长度动态调整（当前固定 30）
- [ ] **Cross-provider benchmark** — `--reviewer-a claude --reviewer-b codex`

### 已完成 (2026-04-07)

- [x] 大规模并行 — ThreadPoolExecutor, 10-12 workers
- [x] Section combination generator — `section_combiner.py`
- [x] Writing self-check layer
- [x] Task-model auto-routing — `model_router.py`
- [x] Refine.ink benchmark runner — `benchmark_refine.py`
- [x] `benchmark-refine` CLI command
- [x] Claim-by-claim verifier — `claim_extractor.py`。Recall: 67% → 83%。
