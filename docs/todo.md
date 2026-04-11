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

## Step 5: LangGraph Graphs ✅ (phase 1 — graph structure)

所有 5 个图编译通过。当前采用渐进策略：graph 结构就绪，内部仍调用现有函数（保持行为不变）。下一步将逐步分解为更细粒度的节点。

- [x] **`graphs/state.py`** — `UnifiedState`, `WritingState`, `MathState`, `PolishState` TypedDict
- [x] **`graphs/polish.py`** — 3 节点：read_paper → run_polish_agent → write_polish_report
- [x] **`graphs/math.py`** — 4 节点：read_and_extract → run_deterministic_checks → (conditional) run_llm_review → write_math_report
- [x] **`graphs/writing.py`** — 1 节点包装（wraps `review_writing_file()`，内部 ThreadPoolExecutor 保留）。后续迭代将分解为 parallel fan-out 节点。
- [x] **`graphs/unified.py`** — 3 节点 + mode routing：route_by_mode → run_polish | run_full_review → write_unified_summary
- [x] **`graphs/focus.py`** — 3 节点：run_focused_writing → run_focused_math → merge_focused_findings
- [ ] **重新接线公共 API** — 延后到 HITL 阶段。当前公共 API 不变，graph 可以独立调用。
- [ ] **添加 `langgraph` 到 pyproject.toml** — 已安装但还未加到 deps（需确认版本锁定）

### 待后续迭代

- [ ] 分解 `graphs/writing.py` 为细粒度节点（parallel fan-out roles, self-check, judge）
- [ ] 分解 `graphs/unified.py` 的 `run_full_review` 为真正的 parallel branches
- [ ] 添加 HITL interrupt 节点

---

## Step 6: HITL + Streaming + FastAPI ✅ (phase 1 — API server)

- [x] **`api.py`** — FastAPI server（281 行），8 个端点全部工作。TestClient 验证通过。
- [x] **CLI `revisica serve`** — `--host` + `--port` 参数
- [x] **背景线程执行** — review 在 daemon thread 中运行，通过 `GET /api/status` 轮询

### 待后续迭代（HITL + streaming）

- [ ] **`interrupt_before` 节点** — 在 writing 和 math 子图的 HITL gate 处加 `interrupt_before`
- [ ] **`SqliteSaver` checkpointer** — `~/.revisica/checkpoints.db`
- [ ] **SSE streaming** — FastAPI SSE 端点消费 `graph.astream_events()`
- [ ] **Focus endpoint** — `POST /api/focus/{run_id}` 发送 FocusRequest 恢复中断的 graph

---

## Step 7: Desktop App

Electron + React + renderer。API server 已就绪。

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
