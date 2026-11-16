# Trinity Risk Guard — 最终技术复核清单

## A. R/Python 迁移（必须真实运行）

- [ ] 在装有 `Rscript` 的机器上执行 `python run_pipeline.py --require-r`。
- [ ] `outputs/r_execution_provenance.json` 含 `returncode: 0` 以及 R/输入/输出 SHA256。
- [ ] `outputs/parity_report.json` 中 `status: PASS`、`n_rows: 1600`、风险等级一致、版本一致，误差不超过 `1e-10`。
- [ ] 如失败，检查 `outputs/parity_comparison.csv`，**绝不**用 Python 生成“R 参考输出”。

## B. Performance / Stability / Fairness

- [ ] `outputs/metrics.json` 与 `outputs/validation_report.md` 数字一致。
- [ ] 披露 AUC、Brier、PSI 是合成数据的指标；没有真实银行验证。
- [ ] SIM_A / SIM_B 为虚构随机标签；组间 TPR/FPR 等指标仅用于公平性测试方法演示。
- [ ] 检查异常标记，以及人类复核点；不称为批准、合规证明。

## C. AI Agent（必须有真实调用才能称完成）

- [ ] 在安全环境配置 `TRG_API_KEY` / `TRG_MODEL`（不要提交密钥）。
- [ ] 运行 `python documentation_agent.py`。
- [ ] 查看 `outputs/agent_status.json`: `LIVE_EXECUTED_DRAFT_PENDING_REVIEW`。
- [ ] `outputs/agent_trace.json` 记录实际工具调用，且 `outputs/agent_documentation_draft.json` 为待人工审核。
- [ ] 四人检查 Agent 对变量、系数、模型局限的解释；纠正幻觉。

## D. 交付

- [ ] 更新 README 里的实际测试结果和工具披露。
- [ ] GitHub 仓库代码可供他人复现（不包括 API Key）。
- [ ] Solution Deck、Architecture Diagram、Responsible AI Note、≤3 分钟 Demo 单独准备并与真实程序一致。
- [ ] 学校官方模板的提交渠道与早期邮件要求可能不同：核实表单与邮件。
