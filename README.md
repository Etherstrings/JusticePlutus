# JusticePlutus

## <a id="donate"></a>赞助支持

如果这个项目对你有帮助，欢迎赞助支持继续迭代。

- GitHub 页面右上角可直接点击 `Sponsor`
- 如果你更习惯国内付款方式，可以直接扫码赞助

<div>
  <img src="docs/assets/donate/alipay.jpg" alt="Alipay QR" width="260" />
  <img src="docs/assets/donate/wechat.jpg" alt="WeChat Pay QR" width="260" />
</div>

支持会优先用于数据源、模型调用和后续功能迭代。

## 1. 能力简介

`JusticePlutus` 是一个面向 A 股自选股的自动化分析流水线，覆盖：

- 行情数据获取（历史 + 实时 + 筹码）
- 搜索增强（新闻/舆情/业绩/行业）
- LLM 结构化分析（决策仪表盘 JSON）
- 单股与汇总报告生成
- 多通知渠道输出（Telegram 为主，其它可扩展）

核心目标是稳定跑通一条“输入股票 -> 分析 -> 产出 -> 推送”的可运维链路。

相关文档：

- [功能架构说明](docs/FUNCTION_ARCHITECTURE.md)
- [快速开始与分层架构](docs/QUICKSTART_ARCHITECTURE.md)
- [API 集成说明](docs/API_INTEGRATION_GUIDE.md)
- [合并说明：Feishu Workflow](docs/merge_notes/2026-03-30-feishu-workflow-merge.md)
- [合并说明：iFinD Enhancement](docs/merge_notes/2026-03-30-ifind-enhancement-merge.md)
- [OpenClaw / ClawHub Skill 页面](https://clawhub.ai/Etherstrings/justice-plutus)

---

## 2. 架构与技术

端到端主流程：

1. 读取输入股票（`workflow_dispatch.stocks` / `--stocks` / `STOCK_LIST`）
2. 拉取数据（历史/实时/筹码，按链路降级）
3. 拉取搜索增强（Bocha/Tavily/SerpAPI）
4. 生成结构化分析（LLM 主模型 + fallback）
5. 输出报告文件（单股 + 汇总）
6. 发送通知（按已配置通道）

技术栈概览：

- Runtime：Python 3.11+
- CLI：`python -m justice_plutus run`
- 核心编排：`src/core/pipeline.py`
- LLM 调用：LiteLLM（OpenAI-compatible/Gemini/Anthropic）
- 数据源：Tushare / Efinance / Akshare / YFinance / HSCloud / Wencai
- 搜索源：Bocha / Tavily / SerpAPI
- 通知：Telegram + 可扩展渠道

---

## 3. 信源方向（每个地方拿什么）

| 模块 | 主要来源 | 说明 |
|------|----------|------|
| 历史日线 | Tushare, Efinance, Akshare, Pytdx, Baostock, YFinance | 用于 MA/趋势与历史走势 |
| 实时行情 | `REALTIME_SOURCE_PRIORITY` 指定顺序（如 Tencent/Sina/Efinance/Akshare） | 获取价格、量比、换手率等 |
| 筹码分布 | HSCloud, Wencai, Akshare, Tushare, Efinance | 用于筹码结构分析 |
| 搜索增强 | Bocha, Tavily, SerpAPI | 风险、利好、业绩预期、行业信息 |
| LLM 分析 | AIHubMix(OpenAI-compatible), OpenAI, Gemini, Anthropic | 生成结构化决策仪表盘 |
| 通知出口 | Telegram, WeChat, Feishu, Email, Discord, Custom Webhook 等 | 由已配置通道决定实际发送 |

---

## 4. 降级策略（怎么降）

1. 日线降级：`Tushare -> Efinance -> Akshare -> Pytdx -> Baostock -> YFinance`
2. 实时降级：按 `REALTIME_SOURCE_PRIORITY` 逐个尝试；首源成功后继续补缺字段
3. 筹码降级：`HSCloud -> Wencai -> Akshare -> Tushare -> Efinance`
4. 搜索降级：单搜索源失败不阻断主流程，保留已有结果继续分析
5. LLM Key 降级：`AIHUBMIX_KEY` 优先，失败后 `OPENAI_API_KEY`
6. LLM 模型降级：`LITELLM_MODEL` 失败后 `LITELLM_FALLBACK_MODELS`
7. 输出降级：通知不可用时仍生成本地报告（`stocks/*.md|json` + `summary*`）

---

## 5. 输入 / 输出 / 出口

输入优先级（高 -> 低）：

1. `workflow_dispatch.stocks`
2. CLI 参数 `--stocks`
3. `.env` 的 `STOCK_LIST`
4. 环境变量 `STOCK_LIST`
5. 工作流默认兜底列表

输出文件：

- 单股：`reports/YYYY-MM-DD/stocks/<code>.md`
- 单股结构化：`reports/YYYY-MM-DD/stocks/<code>.json`
- 汇总：`reports/YYYY-MM-DD/summary.md`
- 汇总结构化：`reports/YYYY-MM-DD/summary.json`
- 运行元数据：`reports/YYYY-MM-DD/run_meta.json`

通知出口：

- 默认按已配置通道发送；未配置时仅落地本地报告

---

## 6. Key 与配置清单

### 6.1 LLM（至少配置一种可用路径）

- AIHubMix / OpenAI-compatible：
  - `AIHUBMIX_KEY`（推荐）
  - `OPENAI_API_KEY`（兼容/兜底）
  - `OPENAI_BASE_URL`（例如 `https://aihubmix.com/v1`）
  - `OPENAI_MODEL`（例如 `gemini-flash-lite-latest`）
  - `LITELLM_MODEL`（例如 `openai/gemini-flash-lite-latest`）
  - `LITELLM_FALLBACK_MODELS`（例如 `openai/gpt-4o-mini`）
- 其它官方直连（可选）：`GEMINI_API_KEY`、`ANTHROPIC_API_KEY`、`DEEPSEEK_API_KEY`

### 6.2 数据与搜索（按需）

- 数据增强：`TUSHARE_TOKEN`
- 筹码增强：`ENABLE_CHIP_DISTRIBUTION=true`，并配置：
  - `WENCAI_COOKIE`（建议）
  - `HSCLOUD_AUTH_TOKEN` 或 `HSCLOUD_APP_KEY + HSCLOUD_APP_SECRET`（可选优先源）
- 搜索增强：`BOCHA_API_KEYS`、`TAVILY_API_KEYS`、`SERPAPI_API_KEYS`
- iFinD 基本面增强（可选，默认关闭）：
  - `IFIND_REFRESH_TOKEN`
  - `ENABLE_IFIND=true`
  - `ENABLE_IFIND_ANALYSIS_ENHANCEMENT=true`
  - 建议本地通过 `./scripts/run_with_overlay_env.sh` 启动，让 `.env.local` 叠加在现有 `.env` 之上

### 6.2.1 iFinD 增强说明

iFinD 在当前项目中只做“增强”，不做基础依赖替换。

行为原则：

- 有 iFinD：给现有分析补充财报、估值、盈利预测等结构化数据
- 没有 iFinD：保持当前主流程不变
- iFinD 报错：自动跳过增强，不阻断历史行情、实时行情、筹码、搜索、LLM 和通知链路

当前增强内容：

- 新增可选配置：
  - `IFIND_REFRESH_TOKEN`
  - `ENABLE_IFIND`
  - `ENABLE_IFIND_ANALYSIS_ENHANCEMENT`
- 新增独立服务层：
  - `src/ifind/auth.py`
  - `src/ifind/client.py`
  - `src/ifind/mappers.py`
  - `src/ifind/schemas.py`
  - `src/ifind/service.py`
- 在分析上下文中按需注入：
  - `ifind_financials`
  - `ifind_valuation`
  - `ifind_forecast`
  - `ifind_quality_summary`
- 在 LLM prompt 中新增：
  - `基本面与估值增强`

当前注入给 LLM 的重点信息包括：

- 最新财报期
- 营业总收入 / 归母净利润 / 扣非净利润
- ROE / 毛利率 / 净利率 / 资产负债率 / 经营现金流
- PE / PB / 市值
- 一致预期净利润增速
- 财务质量摘要

无侵入保证：

- `ENABLE_IFIND=false` 时不初始化、不请求、不改 prompt
- 开关开启但没有 `IFIND_REFRESH_TOKEN` 时只记录 warning，直接回退到原有流程
- iFinD 子查询失败时只返回部分数据或直接跳过，不影响主分析结果

推荐本地配置方式：

```dotenv
IFIND_REFRESH_TOKEN=your_refresh_token_here
ENABLE_IFIND=true
ENABLE_IFIND_ANALYSIS_ENHANCEMENT=true
```

推荐运行方式：

```bash
./scripts/run_with_overlay_env.sh --stocks 600519 --no-notify
```

详细说明见：

- [docs/IFIND_ENHANCEMENT_GUIDE.md](docs/IFIND_ENHANCEMENT_GUIDE.md)

### 6.3 通知（按通道）

- Telegram：`TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`
- 飞书群机器人：`FEISHU_WEBHOOK_URL`
- 其它通道：见 [`.env.example`](.env.example)

飞书机器人最简配置示例：

```bash
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-token
FEISHU_MAX_BYTES=20000
WEBHOOK_VERIFY_SSL=true
```

说明：

- 这里使用的是飞书群里的“自定义机器人 Webhook”，不是飞书开放平台应用机器人
- JusticePlutus 会优先发送飞书卡片消息，失败时自动回退为普通文本
- 单条消息过长时会自动拆分多条发送，无需额外配置

---

## 7. 触发方式（本地 + GH）

### 7.1 本地触发

```bash
python -m justice_plutus run --stocks 000001,600519 --no-notify
```

如果本地把 iFinD token 放在 `.env.local`，推荐改用：

```bash
./scripts/run_with_overlay_env.sh --stocks 000001,600519 --no-notify
```

### 7.2 本地定时（任选）

- macOS `launchd`
- Linux `cron`
- Windows Task Scheduler

触发命令统一：

```bash
python -m justice_plutus run
```

### 7.3 远程触发（GitHub Actions）

- 手动触发：`workflow_dispatch`
- 可选定时触发：在 workflow 中配置 `schedule.cron`

工作流文件：

- `.github/workflows/justice_plutus_analysis.yml`

---

## 8. 快速验证

本地验证：

```bash
python -m justice_plutus run --stocks 000001,600519 --workers 1
```

如果只验证飞书机器人，确保 `.env` 至少配置了 `FEISHU_WEBHOOK_URL`，且未传 `--no-notify`。

远程验证：

```bash
gh workflow run justice_plutus_analysis.yml -f stocks='000001,600519'
gh run list --workflow justice_plutus_analysis.yml --limit 5
gh run watch <run-id> --exit-status
```

验收标准：

- Run 成功（`completed/success`）
- 报告文件完整生成
- 关键字段齐全（重要信息、核心结论、当日行情、数据透视、作战计划、检查清单）
