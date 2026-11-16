# Trinity Risk Guard | 模型设计、数据假设与迁移说明（组内解读文件）

版本：SC-CREDIT-1.1 · 2026-11-13 · Challenge 04 技术原型

## 0. 先读这三点

1. **Logistic/Sigmoid 是标准数学方法**：PD=1/(1+exp(-z))。但是四个系数、截距、风险阈值与合成分布，是团队的**透明模拟假设**，不是某家银行已发布的实证参数，也没有用公开信贷数据拟合。不能表述为“准确的真实银行 PD 模型”。
2. **旧系统来源**：`models/legacy_credit_score.R` 是本项目从零编写的模拟 R 旧模型，非 EXL 样例源码。我们把它固定为基准版本以检验迁移，不以 Python 重新训练取代它。
3. **迁移已准备，真实一致性待检验**：Python 端已测试；只有执行真实的 `Rscript` 并跑 `validate_parity.py` 才能宣布跨语言 parity 通过。

## 1. 为什么叫 Trinity Risk Guard？

`Trinity Risk Guard` 只是 ChatGPT 为团队提出的**可修改的产品/项目名称**，EXL 官方挑战名称仍为 **Challenge 04 — Agentic Model Risk Factory**。最终封面可写 `Trinity Risk Guard | Challenge 04`。没有要求使用这个词。

## 2. 为什么用 Logistic Scorecard？

目标是清晰呈现一个可以逐记录对比的传统可解释风险评分函数，而不是开发最强的违约预测算法。用四个数值输入避免 R/Python 在复杂编码、依赖库和缺失值处理上失控：

    z = -2.98 + 1.65*utilization + 1.13*dti - 0.0041*income_k + 0.62*late_payments_12m
    PD = 1 / (1 + exp(-z))

变量与解释：

| 输入字段 | 含义 / 取值范围（模拟限定） | 预期方向 |
|---|---|---|
| `utilization` | 信用额度已使用比例，0–1（0%=0, 100%=1） | 高 → 高 PD |
| `dti` | 总债务支出/收入比，0–0.85 | 高 → 高 PD |
| `income_k` | 年收入，千欧元，18–180 | 高 → 低 PD |
| `late_payments_12m` | 过去 12 个月逾期次数，整数 0–4 | 高 → 高 PD |

**重要：** 该方向符合常见的风险直觉，但并不能证明因果关系或预测效力。收入和债务收入比的口径在真实银行模型中需要定义明确（是否税后、哪类债务等）。

### 系数是如何选择的（可解释，但不是实证估计）

通过 log-odds 解释，设置如下**假设性**赔率变化：

- `utilization` 增加 **10 个百分点**，违约赔率乘以 exp(1.65×0.1)=**1.179**。
- `dti` 增加 **10 个百分点**，赔率乘以 exp(1.13×0.1)=**1.120**。
- `income_k` 增加 **10**（即年收入增加 €10,000），赔率乘以 exp(-0.0041×10)=**0.960**。
- `late_payments_12m` 增加 **1 次**，赔率乘以 exp(0.62)=**1.859**。

设定截距 -2.98，使得基准人群配置（U=.30、DTI=.32、收入 €50k、无逾期）时 PD 约为 **8.88%**。这是为了建立可理解的场景锚点，并非观察到的银行真实违约率。

不同宏观条件、借款人类型和产品可能完全改变实际系数；真实统计“准确性”只能通过合法取得的历史贷款和违约标签，用 R `glm(..., family=binomial)` 或等价方法拟合，分层/分期验证和校准后才能声称。

### LOW / MEDIUM / HIGH 也只是示意阈值

`PD < 8%` → LOW；`8% ≤ PD < 18%` → MEDIUM；`PD ≥ 18%` → HIGH。它不是银行信贷审批规则，也不应作为真正放贷决策。

## 3. 为什么是 1,600 条？可以随便生成吗？

**1,600 并不是 EXL 的官方要求，也没有经过样本量/功效计算。** 它只是一个可以快速重跑且足够展示 800/800 两个时期对比的工程折衷。模型/程序支持修改为其他偶数样本量，如 400、2,000、5,000；结果会不同。

**不能无约束地随机生成。** 我们采用固定 `seed=2026` 并设计输入范围及依赖：

- `income_k`：截断对数正态（模拟右偏收入），€18k–€180k。
- `utilization`：Beta 分布，约 0.01–0.99，当前期人为加 +0.07 后截断，模拟压力变化。
- `dti`：与利用率、低收入情况相关，再加入随机扰动，截断在 0.05–0.82。
- `late_payments_12m`：与利用率/DTI 相关的低频 Poisson 逾期次数，限制 0–4。
- `loan_amount_eur`、`age_years_audit_only`、`simulated_audit_group`：只作背景/示范分组，**年龄和虚拟群组均不进入模型评分公式**。
- `defaulted`：依据假设风险公式、未观察因素和非线性扰动生成的模拟二元结果，不是实际违约数据。

这样使合成数据**内在一致、范围受控、可复现**，但依然**不能称为符合真实爱尔兰/英国信贷客户分布**。需要真实分布时，应取得批准的历史数据或清楚许可的公开数据，并注明来源、时间、地域、口径与偏差。UCI 两个公开数据集可作后续研究参考，本版**没有使用它们的数据**。

两时期 reference/current 存在故意设置的漂移，因此 PSI 可以检验监控机制。不能由此声称发现了实际经济周期冲击。

## 4. R → Python 是如何迁移的？

- R 文件：`models/legacy_credit_score.R`，只用 base R，可以直接读取 CSV，验证四个数值输入、计算 z 和 PD、生成风险档位，并导出 `customer_id/r_probability/r_risk_band/model_version`。
- Python 文件：`scorecard_port.py`，使用 NumPy/Pandas 实现相同输入限制、相同常数、相同概率和档位判定。
- 对账文件：`validate_parity.py`，对同一份合成数据由两个语言各自运行；按 `customer_id` 完整一对一连接，要求每条概率误差 ≤ `1e-10` 且风险档位与版本完全相同。
- 输出：`outputs/legacy_R_predictions.csv`（**只能由 Rscript 实际生成**）、`outputs/parity_report.json`、`outputs/parity_comparison.csv`。

**Parity ≠ Accuracy。** 完全一致只说明 Python 复现旧计算逻辑；它不证明旧模型能预测真实违约、没有偏差或符合监管要求。

## 5. 小组只需按以下指令运行并审核

要求 Python 3.10+、R（`Rscript`），以及 Python 包 NumPy/Pandas/Scikit-learn/Pytest：

```bash
python -m pip install -r requirements.txt
python generate_data.py
Rscript models/legacy_credit_score.R synthetic_credit_data.csv outputs/legacy_R_predictions.csv
python validate_parity.py
python run_demo.py
python -m pytest tests -q
```

检查 `outputs/parity_report.json` 中 `status` 是否 `PASS`、`n_rows` 是否 `1600`、`risk_bands_equal` 是否 true。若 R 未执行，该报告不会凭空生成，`run_demo.py` 中也只会写 `NOT TESTED`。

## 6. 实际运行过什么；还缺什么

截至本版：Python 自动测试 **15/15 通过**；合成数据共 **1,600** 条、两期各 **800** 条。对应计算结果（仅模拟）：AUC **0.6295**，Brier **0.1039**，utilization PSI **0.2692**，观察到的模拟 default rate **12.125%**。AUC 不高，不能包装成一个成熟有效的预测系统；验证结果也不能当成独立模型审查。缺少 R 实际执行与正式 LLM Agent，后续需要小组电脑/模型 API 环境运行。

## 7. 与 EXL Challenge 04 三个 Task 对应

- **Task 1:** 三个模拟模型的 Inventory (`models/model_inventory.json`)；自动 LLM 文档解析目前仍是后续需要接入的环节。
- **Task 2:** R 模型 + Python 迁移 + 对账测试程序已备齐；真正对账结果待执行 R 环境。
- **Task 3:** Python 实现 Performance(AUC/Brier) / Stability(PSI) / Simulated Group Diagnostics，但这**不是**真实受保护群体的公平性评估。

若时间不足，优先顺序：真实 R parity → 可运行 Documentation Agent → 补全/审核验证结论 → 更新官方 6 页模板、视频及责任说明。代码和合成假设需在提交时披露 ChatGPT 辅助。

## 8. 可用公开参考（未用于拟合）

1. EXL × Trinity Data & AI Hackathon 2026，官方 Challenge 04（用户上传的赛事说明，第 9 页）。
2. UCI Machine Learning Repository, *Default of Credit Card Clients* (30,000 条、2005 年台湾信用卡数据): https://archive.ics.uci.edu/dataset/350/default%2Bof%2Bcredit%2Bcard%2Bclients
3. UCI Machine Learning Repository, *Statlog German Credit Data*（1,000 条历史样本）: https://archive.ics.uci.edu/dataset/144/statlog-german-credit-data

以上为方法和可能的未来数据来源，仅供讨论，不可写成“本模型的参数来自 UCI”。


## 9. v3 新增的严格证据链（2026-11-13）

- `run_pipeline.py`：清理旧的 Parity/Agent 证据，重新生成固定种子的 1,600 条数据；如存在 Rscript，则运行原始 R 文件并记录进程退出码、源码/输入数据/输出文件 SHA256；随后按 customer_id 调用 Python 对账。无 Rscript 则只能标为 `NOT_RUN`，不能报 PASS。
- `validation_engine.py`：新增加 Average Precision、分期 Brier、TPR/FPR/混淆矩阵、四个特征及预测 PD 的 PSI、虚构群组差异和异常提示。所有异常阈值为团队演示假设，未获银行确认。
- `documentation_agent.py`：已编写真正使用 Chat Completions Tool Calling 的 Agent。它可自行选择 `list_inventory`, `read_model_source`, `get_validation_evidence`, `submit_documentation_draft` 四个安全工具，生成结构化待审核文档并保留调用记录。需要外部模型 API / 本地模型；目前无真实调用结果，不能说已经展示 Agent 成功。
- `notebooks/Trinity_Risk_Guard_Colab.ipynb`：以 Colab 按顺序安装/运行 R、Python 和 Agent，并用自定义输入查看预测输出。

**正式运行方式：** `python run_pipeline.py --require-r`；`python documentation_agent.py`（需要环境变量 `TRG_API_KEY` 和 `TRG_MODEL`）。如果需要一键执行 Agent，可执行 `python run_pipeline.py --require-r --agent`。

**当前经过本环境真实验证的状态：** Python `pytest` 测试 15 项通过；Python 模拟结果 AUC=0.6295、Brier=0.1039；R 运行状态 `NOT_RUN`（本环境未安装 R），真实 LLM Agent `NOT_RUN`（本环境无模型 API 配置）。
