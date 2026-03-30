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
eval "$(
  python3 - <<'PY'
from pathlib import Path
from dotenv import dotenv_values
import shlex

root = Path('.').resolve()
merged = {}
for name in ('.env', '.env.local'):
    path = root / name
    if path.exists():
        for k, v in dotenv_values(path).items():
            if v is not None:
                merged[k] = v

for k, v in merged.items():
    print(f"export {k}={shlex.quote(v)}")
PY
)" && ./.venv/bin/python -m justice_plutus run --stocks 600519 --no-notify
```

这个方式会：

- 先读取 `.env`
- 再叠加 `.env.local`
- 不覆盖你其他已有环境内容
- 适配当前 `main` 分支的实际仓库结构

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

## 真实跑数对比

为了避免“只接了能力、没有看到效果”的情况，这里补一组真实单股实跑对比。

对比条件：

- 股票：`600519` / 贵州茅台
- 日期：`2026-03-31`
- 模型：`openai/gemini-flash-lite-latest`
- 运行方式：同一台本地环境、同一天数据，各跑一次
- 唯一区别：
  - 未接入：`ENABLE_IFIND=false`、`ENABLE_IFIND_ANALYSIS_ENHANCEMENT=false`
  - 接入后：`ENABLE_IFIND=true`、`ENABLE_IFIND_ANALYSIS_ENHANCEMENT=true`

### 1. 流程层证据

本次实跑日志里能看到非常明确的差异：

- 未接入时：
  - `iFinD 数据增强未启用`
  - `Prompt 长度: 5333 字符`
- 接入后：
  - `iFinD 数据增强已初始化`
  - `贵州茅台(600519) iFinD financial pack injected`
  - `Prompt 长度: 5798 字符`

结论：

- iFinD 不是停留在“配置存在”，而是实际把财报包注入到了 LLM 分析上下文
- 本次 prompt 增加了 `465` 个字符，约 `+8.7%`

### 2. 输出层对比

两次结果的最终操作建议都还是“观望”，这一点很重要：

- 说明 iFinD 接入不会强行把原有策略结论改成另一个方向
- 它更像是在原有结论之上，给模型增加更完整的财报、估值、盈利预期依据

但在这次真实输出里，仍然能看到几类明显增强。

| 维度 | 未接入 iFinD | 接入 iFinD | 观察到的增强 |
|------|--------------|------------|--------------|
| 流程证据 | 仅基础行情、搜索、筹码进入 prompt | 日志明确出现 `financial pack injected` | 证明增强真的被喂给了模型 |
| Prompt 长度 | 5333 | 5798 | 财报、估值、预期摘要被加入分析上下文 |
| 评分 | 75 | 55 | 接入后这次结果更保守，说明模型会把基本面与技术面一起重新权衡 |
| 业绩预期表述 | “未来几个季度利润显著增厚” | “对2026年及以后业绩产生正面影响，但需观察市场消化情况” | 接入后表述更收敛、更贴近时间维度 |
| 风险提示 | 泛化为“非多头排列，不宜追高” | 明确到“若继续盘整或跌破 MA20，则应离场观望” | 风控条件更具体 |
| 作战计划 | 给出 `1411` 理想买点、`1500` 目标位 | 直接把 `ideal_buy` 改为 `N/A`，目标位收敛到 `1450` | 接入后更谨慎，不会只因为利好就放松技术约束 |
| 基本面表述 | 只概括为“估值低、提价利好” | 明确强调“基本面强劲、盈利预期抬升、估值处于合理偏低区间” | 基本面段落更稳定、更像财务驱动而不是新闻驱动 |

### 3. 这次实跑里最值得关注的变化

本次对比最有价值的，不是“接入后一定更看多”，而是下面这几点：

- 接入前，模型更容易把“涨价利好 + 低乖离率”解释成偏积极信号
- 接入后，模型虽然仍认可利好，但会更明确地保留“趋势未修复”的约束
- 接入后，`earnings_outlook`、`fundamental_analysis`、`risk_warning`、`battle_plan` 这些字段的表达更像“财务数据驱动的审慎判断”

这符合当前接入定位：

- 它不是替代原有技术面策略
- 它是给原策略增加财报、估值、盈利预测依据，让输出更稳、更具体

### 4. 怎么理解这次结果

需要说明的是，LLM 输出本身存在一定随机性，所以单次跑数不代表每次都会出现完全相同的分数变化。

但这次实跑已经能证明两件事：

1. iFinD 数据确实进入了分析链路，而不是“开关开了但没生效”
2. 接入后最明显的收益，不是机械改变买卖结论，而是增强了基本面解释、业绩预期和风险约束

如果你的目标是“更全面的数据体现”，那 iFinD 在当前主流程里最适合承担的角色就是：

- 给综合分析补财报、估值、一致预期
- 让 LLM 在最终结论里少一点空泛判断，多一点结构化依据
- 在利好消息很强时，仍然保留对趋势和风控的纪律性

## 适用范围

当前这版 iFinD 接入的定位，是在原有分析流程上补充更完整的基本面信息。

它当前最适合的使用方式：

- 在综合分析中补充财报、估值和一致预期
- 让结论不仅基于行情和新闻，也能结合财务质量做判断
- 在保持原有技术面纪律的前提下，提高分析内容的完整度和可信度

如果后续要进一步扩展，也可以在这个基础上继续加入更深一层的专题能力，例如：

- 财报速读
- 公告影响拆解
- 预期差跟踪
- 财务体检与经营质量对比
