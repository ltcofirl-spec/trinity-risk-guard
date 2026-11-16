# Trinity Risk Guard v3 — 给组员的最短运行说明

**比赛：EXL × Trinity Challenge 04；项目名 Trinity Risk Guard（团队自选）。**

## 先检查 Python / R

1. 将技术 ZIP 解压。
2. 在该文件夹执行：

```bash
python -m pip install -r requirements.txt
python run_pipeline.py --require-r
python -m pytest tests -q
```

如果第二行提示没有 `Rscript`，需安装 base R 后重试，或者使用 `notebooks/Trinity_Risk_Guard_Colab.ipynb`。**不要把 `NOT_RUN` 当 PASS。**

成功时，截图：`outputs/parity_report.json` 的 PASS 和 1600 行、`outputs/r_execution_provenance.json` 的 Rscript 运行信息、`outputs/validation_report.md` 的结果，以及 tests 全通过。

## 再测试真实 Agent

需要有权使用的真实模型接口；例如在 Colab 第五步用隐藏式输入配置 API Key。命令行方式：

```bash
export TRG_API_KEY='YOUR_API_KEY'
export TRG_MODEL='gpt-4.1-mini'
python documentation_agent.py
```

成功时检查 `outputs/agent_status.json` 为 `LIVE_EXECUTED_DRAFT_PENDING_REVIEW`，并审核 `outputs/agent_trace.json` / `outputs/agent_documentation_draft.json`。没有密钥时不要伪造 Agent 结果。API Key 不要写进公开仓库。

## 看到的指标是什么意思？

- AUC ≈ 0.6295；Brier ≈ 0.1039。只反映模拟数据。
- PSI 比较模拟参考期与当前期的分布；差异是特意设置的。
- SIM_A/SIM_B 仅是随机虚构分组；分组 TPR/FPR 不代表真实公平性验证。
- Parity 完全一致只能说明代码迁移一致，不能说明模型质量高。

## 当前作者端验证状态

Python `pytest` **15/15 通过**；真正的 Rscript 运行 **NOT_RUN**；真实 LLM Agent 调用 **NOT_RUN**。需要你们完成最后两项的实际运行验证，才能将它们写成已实现成果。
