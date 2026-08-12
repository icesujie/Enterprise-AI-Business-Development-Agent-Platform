# 实验室动物设施/IVC 领域包

> 英文工程基线：[laboratory-animal-facility.en.md](laboratory-animal-facility.en.md)。中文版本用于内部审核；如有冲突，以英文版本为准。

## 状态

第二阶段 2.2 功能演示智能体。资格工作流程仅适用于已配置的开发租户。它支持确定性的模拟执行和可选的 OpenAI 智能体 SDK 执行。人工审核是强制性的。知识检索和外部操作保持禁用。

## 身份

| 项目 | 值 |
|---|---|
| 领域 | `laboratory_animal_facility` |
| 智能体 | `laboratory_animal_facility.ivc_business_development` |
| 显示名称 | IVC 设施业务发展智能体 |
| 包版本 | `1.0.0` |
| 工作流程 | `ivc_facility_qualification` |
| 输入模式 | `ivc_qualification_input_v1` |
| 输出模式 | `ivc_qualification_output_v1` |
| 语言 | `en`, `zh-CN`, `id` |
| 开发激活 | 启用 |
| 生产激活 | 未创建 |
| 知识检索 | 计划中，可选，已禁用 |
| 外部工具/操作 | 无 |

## 业务资格工作流程

```text
Select a synthetic case or submit structured project data
→ validate customer, project, technical, budget, and timeline fields
→ create a durable Agent Run
→ execute through the shared Redis Worker
→ return schema-validated A/B/C output in the requested language
→ persist the IVC assessment
→ require a human to approve or reject the exact result
```

该工作流程是商业发现，而不是科学或设施设计批准。智能体可以总结证据并推荐发现行动。它不得声明符合法规、科学适用性、动物福利、HVAC 性能、价格或交货日期。

## 资格输入

请求分为五个业务部分：

1. `customer_profile`：组织、组织类型、国家/城市、联系角色和决策
   利益相关者。
2. `project`：新设施、扩建、改造、更换或可行性项目；地点；
   项目摘要。
3. `technical_requirements`：研究项目/物种、计划容量、房间和工作流程、
   遏制/生物安全背景、HVAC/环境、设计信息、验证期望和生命周期服务范围。
4. `budget_indicators`：预估预算、货币、资金状态和采购背景。
5. `timeline`：目标里程碑和当前项目阶段。

所有输入在运行之前进行验证。原始结构化快照已保存到 PostgreSQL，以便稍后审查者可以准确地看到智能体评估的内容。

## 资格标准

| 类别 | 分数 | 审查证据 |
|---|---|---|
| 客户资料 | 10 | 组织背景和负责联系人 |
| 项目定义 | 15 | 项目类型、地点和定义范围 |
| 技术要求 | 35 | 容量、工作流程、生物安全、HVAC、设计和验证证据 |
| 预算和采购 | 20 | 预算/货币、资金和采购路径 |
| 时间表 | 15 | 目标里程碑和当前阶段 |
| 决策利益相关者 | 5 | 业主、科学、兽医、设施、工程和采购角色 |

- 等级 A：75–100
- 等级 B：45–74.99
- 等级 C：0–44.99

缺失的数据会降低分数，并明确返回。分数不会自动创建、转换、拒绝或联系 CRM 负责人。

## 结构化输出

保存的结果仅包含面向业务的字段：

- 资格分数和 A/B/C 等级。
- 语言本地化的业务摘要。
- 六个可见的资格因素及其证据状态。
- 缺失的信息。
- 风险标志。
- 推荐的下一步行动。
- 信心。
- 强制专家审核标记和审核状态。

隐藏的思考链既未请求，也未暴露。稳定的模式键和枚举值保持为英语；面向人类的文本将以请求的语言返回。

## 提示模板

版本化的实现模板是：

`apps/api/src/sari_api/adapters/ivc_qualification_provider.py:IVC_QUALIFICATION_INSTRUCTIONS`

它固定了标准和语言合同，禁止虚构的事实和承诺，要求经过合格审查，并不允许使用工具。 OpenAI 模式使用 `IvcQualificationOutput` 作为结构化输出模式。模拟模式在不使用 API 密钥的情况下，确定性地应用相同的业务合同。

## 模拟演示案例

所有名称、联系人、地点、金额和项目描述都是合成的。

| 案例 | 场景 | 模拟结果 |
|---|---|---|
| `university_animal_facility` | 资助的新大学小鼠/大鼠设施，具有成熟的设计证据 | 100 / A |
| `pharmaceutical_research_facility` | 药物研究扩建，资金正在审核中 | 97 / A |
| `laboratory_upgrade` | 早期架更换查询，存在大量证据差距 | 44 / C |

相同的底层事实会产生英语、中文或印尼语的业务解释，而数字结果保持稳定。

## API 表面

| 方法 | 端点 | 目的 |
|---|---|---|
| `GET` | `/api/v1/ivc/demo-cases?locale=zh-CN` | 列出本地化的合成案例 |
| `GET` | `/api/v1/ivc/demo-cases/{case_key}` | 读取完整的结构化演示输入 |
| `POST` | `/api/v1/ivc/qualification-runs` | 队列演示案例或调用方提供的结构化项目 |
| `GET` | `/api/v1/agent-runs/{run_id}` | 轮询持久状态和结果 |
| `POST` | `/api/v1/agent-runs/{run_id}/cancellations` | 取消已排队/正在运行的运行 |
| `GET` | `/api/v1/ivc/qualification-assessments` | 列出已保存的 IVC 评估 |
| `POST` | `/api/v1/ivc/qualification-assessments/{id}/reviews` | 人工批准/拒绝 |

运行创建需要 `leads:qualify` 和 `Idempotency-Key`。共享的运行时提供有限的重试、安全的失败消息、相关 ID、结构化日志记录、取消、恢复和审计事件。

## 数据库更改

迁移 `4a68c3d2f901`：

- 添加了租户隔离的 `ivc_qualification_assessments`，包含分数、级别、语言、结构化因素、缺失信息、风险、下一步行动和信心。
- 强制在新的表中启用 PostgreSQL 的行级安全。
- 标记 IVC 领域、智能体和版本 1 配置为开发可用/启用。
- 为已配置的工作区创建了开发级别的租户激活。
- 保持 `approved_knowledge_retrieval` 为可选和计划。
- 保留了 Sari Arta 配置 ID、`lead_qualification` 键、工作流程、表和 API 不变。

## 知识边界

该领域分类仍然定义了 IVC 系统、设施工作流程、环境控制、生物安全、安装/验证、生命周期服务和批准的能力/案例。这些仅是类别定义。在第二阶段 2.2 中，没有批准的文档、块、嵌入、引用或检索工具。

生产激活需要领域专家审查、批准的来源治理、AI 数据处理批准、评估阈值和单独的生产激活记录。
