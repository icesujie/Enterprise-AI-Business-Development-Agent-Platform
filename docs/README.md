# 企业级 AI 商务拓展智能体平台文档

## Documentation Index / 文档索引

这套文档采用“英文技术基线 + 中文审阅指南”的方式维护：

- **英文技术文档**是后续开发、接口联调、数据库建模和架构验收的正式依据。
- **中文审阅指南**解释业务含义、关键设计决策、风险和需要确认的问题。
- 如果中英文理解存在冲突，以英文技术基线中的字段、状态、接口和约束为准；确认后的业务变更应先更新英文基线，再同步中文指南。

这种方式比逐段双语复制更容易维护，也更适合非纯技术人员参与评审。

## 建议阅读顺序

1. 先阅读 [中文架构审阅指南](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/review-guide.zh-CN.md>)。
2. 确认指南中的“需要业务方确认”事项。
3. 再按需查看以下英文技术细节：

| 文档 | 中文说明 | 适合谁审核 |
|---|---|---|
| [Technical Architecture](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/technical-architecture.md>) | 系统、前后端、AI、集成、部署和安全架构 | 产品负责人、技术负责人、安全和运维 |
| [Database Design](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/database-design.md>) | 实体关系、表、字段、关系和索引 | 后端、数据、产品和合规 |
| [API Design](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/api-design.md>) | REST API、接口清单、示例和认证 | 前后端、集成、自动化和安全 |

## 审核输出建议

审核时不需要逐字检查所有英文内容。建议把意见分成以下四类：

- **业务不符合：** 流程、角色、状态、审批条件与实际业务不一致。
- **范围调整：** 第一阶段不需要，或遗漏了必须上线的能力。
- **数据问题：** 字段缺失、数据不应保存、保存时间不合适。
- **技术风险：** 性能、安全、集成、部署或成本不可接受。

意见示例：

```text
文档：database-design.md
章节：5.5 opportunities
类型：业务不符合
意见：Sari Arta 的项目必须同时记录项目顾问和技术负责人，不能只有一个 owner。
```

