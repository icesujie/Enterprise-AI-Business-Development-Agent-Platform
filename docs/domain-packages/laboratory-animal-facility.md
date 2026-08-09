# Laboratory Animal Facility / IVC Domain Package

## Status / 状态

**English:** Framework-validation package only. The agent is registered as a draft, is not activated, cannot execute, and has no knowledge base.

**中文：** 仅用于验证多领域框架。该智能体以草稿登记，未激活、不可执行，也没有接入知识库。

**Bahasa Indonesia:** Paket ini hanya untuk validasi kerangka. Agen terdaftar sebagai draf, belum diaktifkan, tidak dapat dijalankan, dan belum memiliki basis pengetahuan.

## Identity

| Item | Value |
|---|---|
| Domain | `laboratory_animal_facility` |
| Agent | `laboratory_animal_facility.ivc_business_development` |
| Display name | IVC Facility Business Development Agent |
| Package version | `1.0.0` |
| Locales | `en`, `zh-CN`, `id` |
| Runtime | Disabled |
| Knowledge retrieval | Planned, not implemented |

## Business objectives / 业务目标

- Identify potentially qualified IVC and laboratory-animal-facility opportunities for specialist review. / 识别值得专家审核的 IVC 与实验动物设施机会。
- Collect project scope, species, capacity, biosafety, environmental, stakeholder, budget, and timeline evidence. / 收集范围、动物种类、容量、生物安全、环境、决策人、预算和时间信息。
- Recommend a safe commercial next step without making scientific, regulatory, veterinary, engineering, or pricing commitments. / 在不替代科研、法规、兽医、工程或价格审批的前提下建议下一步。

## Qualification structure / 资格字段

The package defines structured fields for project type and location; research program and species; planned capacity; containment and biosafety context; environmental/HVAC requirements; room and workflow scope; available design information; validation expectations; procurement authority; budget; target timeline; and lifecycle service scope.

领域包定义了项目类型与地点、研究方向与动物种类、计划容量、生物安全背景、环境与 HVAC 要求、房间及流程、现有设计资料、验证要求、采购决策、预算、时间和全生命周期服务等结构化字段。

## Knowledge categories / 知识分类

- IVC systems and approved components / IVC 系统与批准部件
- Facility planning and workflow / 设施规划与流程
- Environmental control and HVAC / 环境控制与 HVAC
- Biosafety, biosecurity, and animal welfare references / 生物安全与动物福利参考
- Installation, commissioning, and validation / 安装、调试与验证
- Service, parts, and consumables / 服务、备件与耗材
- Approved organizational capabilities and cases / 经批准的企业能力和案例

These are taxonomy definitions only. No source, document, chunk, embedding, or retrieval index has been created.

以上仅为分类定义，尚未创建知识来源、文档、分块、Embedding 或检索索引。

## Required capabilities / 所需能力

`lead_qualification`, `structured_output`, `localized_response`, and `human_review` are registered as available framework capabilities. `approved_knowledge_retrieval` is required by the future IVC agent but deliberately remains `planned`, which prevents activation readiness.

框架已登记线索资格评估、结构化输出、本地化响应和人工审核能力。未来 IVC Agent 必须具备批准知识检索能力，但该能力当前保持 `planned`，因此本领域包不满足激活条件。

## Localization contract / 多语言约定

The caller may request `en`, `zh-CN`, or `id`. The runtime must return structured fields in the requested locale, preserve identifiers and citations unchanged, and fall back to the tenant default and then English when localized text is unavailable. Localization must never translate product codes, standards identifiers, measurements, or source citations in a way that changes their meaning.

调用方可以请求 `en`、`zh-CN` 或 `id`。运行时应以请求语言返回结构化业务说明；标识符和引用保持不变；缺少对应翻译时先回退到企业默认语言，再回退到英文。产品编码、标准编号、测量值和来源引用不得因翻译而改变含义。

## Activation gates / 激活门槛

Before this package can execute, it needs subject-matter review, approved knowledge sources, prompt and structured-output implementation, evaluation cases, provider/data-region approval, tool and permission review, and an explicit tenant activation. None of those gates is implied by registration.

正式执行前必须完成领域专家审核、知识来源批准、Prompt 与结构输出实现、评测集、模型与数据地区批准、工具权限审核和企业级显式激活。完成登记并不代表通过以上门槛。
