# 企业级 AI 商务拓展智能体平台文档

## Documentation Index / 文档索引

这套文档采用“英文技术基线 + 中文说明”的方式维护：

- **英文技术文档**是后续开发、接口联调、数据库建模和架构验收的正式依据。
- **中文说明**用于解释业务含义和设计结果。
- 技术方案、MVP 取舍和开发顺序由 AI 工程代理负责决定并验证。
- 如果中英文理解存在冲突，以英文技术基线中的字段、状态、接口和约束为准。

你不需要逐份审核这些技术文档。

## 你只需要看什么

如果想了解项目，直接看：

1. [Project Roadmap](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/roadmap.md>)：项目分几期、目前做到哪里。
2. [MVP Scope](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/mvp-scope.md>)：第一版具体做什么。
3. [Phase 1 Tasks](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/phase-1-tasks.md>)：第一阶段任务、依赖和验收标准。
4. [中文架构说明](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/review-guide.zh-CN.md>)：系统整体如何工作。
5. [UI/UX Design](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/ui-design.md>)：官网和内部销售工作台的产品体验与视觉设计基线。

其余文档主要供开发使用：

| 文档 | 用途 |
|---|---|---|
| [Technical Architecture](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/technical-architecture.md>) | 系统、前后端、AI、集成、部署和安全架构 |
| [Database Design](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/database-design.md>) | 实体关系、表、字段、关系和索引 |
| [API Design](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/api-design.md>) | REST API、接口清单、示例和认证 |
| [UI/UX Design](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/ui-design.md>) | 官网、内部工作台、组件、视觉、响应式和实施建议 |
| [Project Rules](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/AGENTS.md>) | AI 工程代理必须遵守的开发规则 |
| [Local Development](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/development.md>) | 本地安装、运行、验证和故障排查 |

## 什么时候需要你确认

AI 工程代理会自行决定技术实现。只有以下情况会请你确认：

- 使用真实客户数据。
- 向真实客户发送邮件、WhatsApp、提案或营销内容。
- 对价格、折扣、交期、技术保证或合同作出商业承诺。
- 购买付费服务或产生明显费用。
- 部署到正式生产环境。
- 执行不可恢复的数据删除或高风险变更。
- 现有设计与 Sari Arta 的真实业务事实明显冲突。

其他技术选择、页面结构、数据库字段、API、测试和开发顺序由 AI 工程代理自行完成。
