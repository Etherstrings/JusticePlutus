# JusticePlutus

## 1. README 简介

`JusticePlutus` 是一个面向 A 股自选股的“分析 + 报告 + 推送”流水线项目。  
它聚焦一个稳定主路径：给定股票列表，自动拉取数据、生成单股结论，并按当前配置推送。

当前主路径特征：

- 单一运行模式（不拆多套推送模式）
- 支持本地触发和 GitHub Actions 触发
- LLM 主链路：`AIHubMix(OpenAI-compatible) -> Gemini`，失败后模型/Key 降级
- 筹码链路：`HSCloud -> Wencai -> Akshare -> Tushare -> Efinance`（可按配置自动跳过未启用源）

相关文档：

- [功能架构说明](docs/FUNCTION_ARCHITECTURE.md)
- [快速开始与分层架构（历史）](docs/QUICKSTART_ARCHITECTURE.md)
- [API 集成说明](docs/API_INTEGRATION_GUIDE.md)

---

## 2. 功能架构介绍

端到端流程（简版）：

1. 读取股票输入（`workflow_dispatch.stocks` / `--stocks` / `STOCK_LIST`）
2. 拉取行情与技术指标（带数据源回退）
3. 拉取搜索与资讯增强（Bocha/Tavily/SerpAPI）
4. 调用 LLM 生成结构化结论（主模型+fallback）
5. 输出单股报告 + 批次汇总
6. 发送通知（当前主用 Telegram）

关键降级链：

- 日线：`Tushare -> Efinance -> Akshare -> Pytdx -> Baostock -> YFinance`
- 实时：按 `REALTIME_SOURCE_PRIORITY` 顺序，首个可用报价后继续补字段
- 筹码：`HSCloud -> Wencai -> Akshare -> Tushare -> Efinance`
- LLM Key：`AIHUBMIX_KEY` 优先，失败后 `OPENAI_API_KEY`
- LLM 模型：`LITELLM_MODEL` 失败后 `LITELLM_FALLBACK_MODELS`

更详细分层、时序图和模块职责见：

- [docs/FUNCTION_ARCHITECTURE.md](docs/FUNCTION_ARCHITECTURE.md)

---

## 3. 快速开始配置

### 3.1 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

最小可运行配置（`.env`）：

```env
STOCK_LIST=000001,600519

AIHUBMIX_KEY=your_aihubmix_key
OPENAI_BASE_URL=https://aihubmix.com/v1
OPENAI_MODEL=gemini-flash-lite-latest
LITELLM_MODEL=openai/gemini-flash-lite-latest
LITELLM_FALLBACK_MODELS=openai/gpt-4o-mini

ENABLE_CHIP_DISTRIBUTION=true
WENCAI_COOKIE=your_wencai_cookie
# 可选：HSCloud 优先源（二选一）
# HSCLOUD_AUTH_TOKEN=...
# HSCLOUD_COOKIE=...
# 或 app_key + app_secret 自动换 token：
# HSCLOUD_APP_KEY=...
# HSCLOUD_APP_SECRET=...
```

### 3.2 GitHub Actions 配置

工作流文件：

- `.github/workflows/justice_plutus_analysis.yml`

必配（建议）：

- `vars.STOCK_LIST`
- `secrets.AIHUBMIX_KEY`（至少和 `OPENAI_API_KEY` 配一个）
- `secrets.OPENAI_API_KEY`（建议与 AIHubMix 同时配）
- `vars.OPENAI_BASE_URL`（AIHubMix 用 `https://aihubmix.com/v1`）
- `vars.OPENAI_MODEL`（建议 `gemini-flash-lite-latest`）
- `vars.ENABLE_CHIP_DISTRIBUTION`（`true/false`）
- `secrets.WENCAI_COOKIE`、`secrets.HSCLOUD_*`（启用筹码增强时）
- 通知相关 Token（如 Telegram）

股票覆盖优先级（高 -> 低）：

1. `workflow_dispatch` 的 `stocks`
2. CLI `--stocks`
3. `.env` 的 `STOCK_LIST`
4. 环境变量 `STOCK_LIST`
5. 默认兜底

---

## 4. 测试本地触发与远程触发（上 GH）

### 4.1 本地触发

```bash
# 仅验证链路，不推送通知
python -m justice_plutus run --stocks 000001,600519 --no-notify
```

检查点：

- 控制台无致命报错
- 生成 `reports/YYYY-MM-DD/stocks/*.md|*.json`
- 生成 `summary.md` / `summary.json` / `run_meta.json`

### 4.2 远程触发（GitHub）

```bash
# 手动触发 workflow_dispatch
gh workflow run justice_plutus_analysis.yml -f stocks='000001,600519'

# 查看最近运行
gh run list --workflow justice_plutus_analysis.yml --limit 5

# 追踪日志（替换 <run-id>）
gh run watch <run-id> --exit-status
```

检查点：

- Run 状态为 `completed` 且 `conclusion=success`
- Artifacts 含 `reports/`、`logs/`
- 报告字段包含单股模板关键块（重要信息、核心结论、当日行情、数据透视、作战计划、检查清单）
