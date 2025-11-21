# v3 开发计划（进行中）

> 基于 `v3_architecture_spec.md` 的落地计划，按优先级推进，完成后勾选。

## P0（安全护栏 & 可靠性，优先完成）
- [x] 移植 v2 状态管理/超时/紧急停止到 `main_v3.py`，统一使用 `state_manager.py` 和 `logger.py`。
- [x] 修复 Executor ReAct 历史上下文累积，避免只保留最新 Observation。
- [x] 强化工具安全：`run_command` 增加超时/白名单/工作目录限制，所有工具统一异常处理与输入校验。
- [x] 循环/成本防护：步数/深度/时间/费用预算的集中配置与超限停止提示。

## P1（核心能力升级，v3.1 目标）
- [x] Persona 引擎增强：支持动态切换/注入，Planner 可请求 Persona；新增配置入口。
- [x] Researcher 代理：统一检索→摘要→引用链；接 Tavily 或可替换的搜索 Provider。
- [x] 观测性：结构化事件流（trace/iteration_id），成本/延迟/失败率指标；日志可视化基础。
- [x] 配置安全：权限/超时/预算集中化配置并验证，避免硬编码。

## P2（自进化 & 子代理，v3.2 方向）
- [ ] Tool Builder MVP：AST 黑名单/依赖审计→沙箱运行→合成单测→热加载与回滚。
- [ ] Sub-Agent Swarm：任务分派给 Coder/QA/Research 等子代理，定义合并与冲突解决策略。
- [ ] Prompt/Persona 治理：模板版本化、注入检测、降级策略；Prompt 评测与回归测试。
