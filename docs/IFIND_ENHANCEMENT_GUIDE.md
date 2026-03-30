# iFinD 增强接入说明

## 目的

当前仓库中的 iFinD 接入只承担“增强”角色，不改变 JusticePlutus 原有主流程的基础依赖关系。

设计原则：

- 有 iFinD：在现有分析基础上补充财报、估值、盈利预测等结构化数据
- 没 iFinD：系统保持原有行为，不影响历史行情、实时行情、筹码、搜索、LLM 分析和通知
- iFinD 报错：跳过增强，不阻断主流程

## 当前增强了什么

### 1. 新增可选配置

新增配置项：

- `IFIND_REFRESH_TOKEN`
- `ENABLE_IFIND`
- `ENABLE_IFIND_ANALYSIS_ENHANCEMENT`

配置解析位置：

- [src/config.py](/Users/boyuewu/Projects/JusticePlutus/src/config.py)
- [.env.example](/Users/boyuewu/Projects/JusticePlutus/.env.example)

### 2. 新增 iFinD 服务层

新增目录：

- [src/ifind](/Users/boyuewu/Projects/JusticePlutus/src/ifind)

职责拆分：

- [auth.py](/Users/boyuewu/Projects/JusticePlutus/src/ifind/auth.py)
  - 用 `refresh_token` 换取 `access_token`
  - 做进程内 token 缓存
- [client.py](/Users/boyuewu/Projects/JusticePlutus/src/ifind/client.py)
  - 封装 iFinD HTTP 请求
- [mappers.py](/Users/boyuewu/Projects/JusticePlutus/src/ifind/mappers.py)
  - 把原始返回映射为项目内统一结构
- [schemas.py](/Users/boyuewu/Projects/JusticePlutus/src/ifind/schemas.py)
  - 定义财报包、估值包、预期包、质量摘要
- [service.py](/Users/boyuewu/Projects/JusticePlutus/src/ifind/service.py)
  - 对外暴露 `get_financial_pack()`

### 3. 增强了现有分析上下文

接入点：

- [src/core/pipeline.py](/Users/boyuewu/Projects/JusticePlutus/src/core/pipeline.py)

增强逻辑：

- 初始化时根据开关决定是否创建 iFinD service
- 单股分析时，如果增强开关开启，则拉取当前股票的 iFinD financial pack
- 将结果注入分析上下文：
  - `ifind_financials`
  - `ifind_valuation`
  - `ifind_forecast`
  - `ifind_quality_summary`

### 4. 增强了 LLM Prompt

接入点：

- [src/analyzer.py](/Users/boyuewu/Projects/JusticePlutus/src/analyzer.py)

新增 prompt 区块：

- `基本面与估值增强`

当前补充的信息包括：

- 最新财报期
- 营业总收入
- 归母净利润
- 扣非净利润
- ROE
- 毛利率 / 净利率
- 资产负债率
- 经营现金流
- PE / PB / 市值
- 一致预期净利润增速
- 财务质量摘要

## 无侵入保证

当前实现明确遵守以下约束：

### 1. 开关关闭时不生效

- `ENABLE_IFIND=false` 时，不初始化 iFinD service
- 不会发起 iFinD 请求
- 不会改动现有 prompt

### 2. 缺少 token 时自动跳过

- 即使 `ENABLE_IFIND=true`
- 如果没有 `IFIND_REFRESH_TOKEN`
- 系统只记录 warning，仍继续原有分析流程

### 3. iFinD 故障时自动降级

- token 换取失败：跳过增强
- 单个子查询失败：返回部分财务包
- 全部失败：不阻断主流程

### 4. 不改变原有主链路

以下能力不依赖 iFinD：

- 历史日线
- 实时行情
- 筹码分布
- 搜索增强
- LLM 主分析
- 报告生成
- 通知发送

## 如何配置

推荐把本地 token 放在 `.env.local`，不要改你现有 `.env`。

示例：

```dotenv
IFIND_REFRESH_TOKEN=your_refresh_token_here
ENABLE_IFIND=true
ENABLE_IFIND_ANALYSIS_ENHANCEMENT=true
```

推荐运行方式：

```bash
./scripts/run_with_overlay_env.sh --stocks 600519 --no-notify
```

这个脚本会：

- 先读取 `.env`
- 再叠加 `.env.local`
- 不覆盖你其他已有环境内容

## 当前验证状态

已完成的验证：

- iFinD 配置解析测试
- iFinD token 缓存与 service 测试
- pipeline 注入 / 跳过测试
- analyzer prompt 增强测试
- 本地单股全流程 smoke run

关键测试文件：

- [tests/test_config_llm_and_stock_overrides.py](/Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py)
- [tests/test_ifind_auth.py](/Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_auth.py)
- [tests/test_ifind_service.py](/Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_service.py)
- [tests/test_ifind_pipeline_integration.py](/Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_pipeline_integration.py)
- [tests/test_ifind_analyzer_prompt.py](/Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_analyzer_prompt.py)

## 当前局限

当前这版 iFinD 接入仍然只是“增强现有综合分析”，不是独立产品形态。

它适合：

- 让原有分析更稳
- 给 LLM 增加财报和估值依据

它还不适合：

- 单独体现 iFinD 的财报事件能力
- 形成独立财报体检推送
- 做公告 / 预期差 / 财报速读产品

这些能力建议在独立项目中继续展开。
