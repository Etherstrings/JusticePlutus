# JusticePlutus

用于自选股分析与单股即时推送的独立项目。

## 文档

- [快速开始与分层架构](docs/QUICKSTART_ARCHITECTURE.md)
- [API 集成与 OpenClaw 交接说明](docs/API_INTEGRATION_GUIDE.md)

## 特性

- 触发即执行，不做大盘复盘、不做交易日跳过判断
- 每只股票分析完成后，立刻保存 `stocks/<code>.md` 和 `stocks/<code>.json`
- 每只股票分析完成后，立刻推送到已配置通知渠道
- 运行结束后额外生成 `summary.md`、`summary.json`、`run_meta.json`
- 支持本地命令行、GitHub Actions `workflow_dispatch`，以及工作日自动定时触发

## 回退与降级

- 日线数据会按 `Tushare -> Efinance -> Akshare -> Pytdx -> Baostock -> YFinance` 串行回退
- 实时行情按 `REALTIME_SOURCE_PRIORITY` 逐源尝试；拿到第一份可用报价后，还会从后续源补齐量比、换手率、PE/PB 等字段
- 搜索增强当前已接入 `Bocha`、`Tavily`、`SerpAPI`；单个搜索维度失败不会阻断整只股票分析
- LLM 层代码支持主模型加 fallback models，但当前线上主路由是 `AIHubMix -> gemini-flash-lite-latest`
- Telegram 发送带重试和纯文本回退；多股模式下会先发单股详情，最后补发 1 条批次总览

## 本地运行

```bash
pip install -r requirements.txt
python -m daily_stock_pipeline run
python -m daily_stock_pipeline run --stocks 600519,000001
python -m daily_stock_pipeline run --no-notify
```

默认输出目录是 `reports/YYYY-MM-DD/`，也可以通过 `--output-dir` 指定。

## GitHub Actions

仓库内置 `.github/workflows/daily_analysis.yml`，发布到 GitHub 后可以直接在 Actions 页面手动触发，也会在工作日自动运行。

- 默认读取仓库的 `STOCK_LIST`
- 也可以在触发时传入 `stocks` 临时覆盖
- 执行结束后会上传 `reports/` 和 `logs/` artifact
- 当前默认定时：工作日北京时间 `09:35` 自动执行一次

## 修改股票与触发方式

### 修改默认股票

修改 GitHub 仓库 Variables 中的 `STOCK_LIST`。

示例：

```text
600519,000001,300750
```

### 临时覆盖本次运行股票

在 `Run workflow` 面板里填写 `stocks`，会临时覆盖默认 `STOCK_LIST`，不会改仓库变量。

### 手动触发

进入 `.github/workflows/daily_analysis.yml` 对应的 Actions 页面，点击 `Run workflow`。

### 定时触发

当前默认同时启用：

- `workflow_dispatch`
- `schedule`：工作日北京时间 `09:35` 自动执行

GitHub Actions 的 `schedule` 使用 UTC。当前配置等价于：

```yaml
schedule:
  - cron: "35 1 * * 1-5"
```

即工作日 `01:35 UTC`，对应北京时间 `09:35`。

如果要在本地机器定时运行，可以使用 Windows 任务计划程序定时执行：

```powershell
python -m daily_stock_pipeline run
```

## 目录结构

```text
reports/YYYY-MM-DD/
  summary.md
  summary.json
  run_meta.json
  stocks/
    600519.md
    600519.json
```
