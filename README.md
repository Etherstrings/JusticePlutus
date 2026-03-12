# JusticePlutus

从 `ZhuLinsen/daily_stock_analysis` 提取出来的独立项目，只保留“自选股分析 + 单股完成即推送”这条流水线。

## 特性

- 触发即执行，不做大盘复盘、不做交易日跳过判断
- 每只股票分析完成后，立刻保存 `stocks/<code>.md` 和 `stocks/<code>.json`
- 每只股票分析完成后，立刻推送到已配置通知渠道
- 运行结束后额外生成 `summary.md`、`summary.json`、`run_meta.json`
- 支持本地命令行和 GitHub Actions `workflow_dispatch`

## 本地运行

```bash
pip install -r requirements.txt
python -m daily_stock_pipeline run
python -m daily_stock_pipeline run --stocks 600519,000001
python -m daily_stock_pipeline run --no-notify
```

默认输出目录是 `reports/YYYY-MM-DD/`，也可以通过 `--output-dir` 指定。

## GitHub Actions

仓库内置 `.github/workflows/daily_analysis.yml`，发布到 GitHub 后可以直接在 Actions 页面手动触发。

- 默认读取仓库的 `STOCK_LIST`
- 也可以在触发时传入 `stocks` 临时覆盖
- 执行结束后会上传 `reports/` 和 `logs/` artifact

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
