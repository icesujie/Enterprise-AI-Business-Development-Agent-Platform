# Enterprise AI Business Development Agent Platform Documentation

## Documentation standard / 文档标准

Design documents are maintained as complete bilingual pairs:

- `*.en.md` is the primary engineering baseline.
- `*.zh-CN.md` is the complete Simplified Chinese translation for internal review.
- Headings, diagrams, tables, code blocks, identifiers, API paths, database fields, and terminology are preserved across both versions.
- If the two versions conflict, the English engineering baseline controls implementation.

设计文档采用完整的中英文双语配对：

- `*.en.md` 是正式工程基线。
- `*.zh-CN.md` 是供内部审核使用的完整简体中文译本。
- 两个版本保持标题、图表、表格、代码块、标识符、API 路径、数据库字段和术语一致。
- 如两个版本存在冲突，以英文工程基线为准。

## Bilingual design documents / 双语设计文档

| Design area / 设计领域 | English engineering baseline | 中文完整译本 |
|---|---|---|
| Technical architecture / 技术架构 | [technical-architecture.en.md](technical-architecture.en.md) | [technical-architecture.zh-CN.md](technical-architecture.zh-CN.md) |
| REST API design / REST API 设计 | [api-design.en.md](api-design.en.md) | [api-design.zh-CN.md](api-design.zh-CN.md) |
| Database design / 数据库设计 | [database-design.en.md](database-design.en.md) | [database-design.zh-CN.md](database-design.zh-CN.md) |
| Phase 2 agent framework / Phase 2 智能体框架 | [phase-2-agent-framework-design.en.md](phase-2-agent-framework-design.en.md) | [phase-2-agent-framework-design.zh-CN.md](phase-2-agent-framework-design.zh-CN.md) |
| Multi-tenant security / 多租户安全 | [multi-tenant-security-design.en.md](multi-tenant-security-design.en.md) | [multi-tenant-security-design.zh-CN.md](multi-tenant-security-design.zh-CN.md) |
| Frontend UI/UX / 前端 UI/UX | [ui-design.en.md](ui-design.en.md) | [ui-design.zh-CN.md](ui-design.zh-CN.md) |
| Website design reference / 网站设计参考 | [design-reference.en.md](design-reference.en.md) | [design-reference.zh-CN.md](design-reference.zh-CN.md) |
| Sari Arta UI specification / Sari Arta UI 规格 | [sari-arta-ui-specification.en.md](sari-arta-ui-specification.en.md) | [sari-arta-ui-specification.zh-CN.md](sari-arta-ui-specification.zh-CN.md) |
| IVC domain package / IVC 领域包 | [laboratory-animal-facility.en.md](domain-packages/laboratory-animal-facility.en.md) | [laboratory-animal-facility.zh-CN.md](domain-packages/laboratory-animal-facility.zh-CN.md) |
| Knowledge foundation / 知识基础 | [knowledge-foundation-design.en.md](knowledge-foundation-design.en.md) | [knowledge-foundation-design.zh-CN.md](knowledge-foundation-design.zh-CN.md) |
| Enterprise knowledge management / 企业知识管理 | [enterprise-knowledge-management-design.en.md](enterprise-knowledge-management-design.en.md) | [enterprise-knowledge-management-design.zh-CN.md](enterprise-knowledge-management-design.zh-CN.md) |

## Project and operational documents / 项目与运行文档

These documents are not currently classified as design baselines and retain their existing filenames:

| Document / 文档 | Purpose / 用途 |
|---|---|
| [roadmap.md](roadmap.md) | Delivery phases and current project status / 交付阶段和当前状态 |
| [mvp-scope.md](mvp-scope.md) | MVP scope and implementation priorities / MVP 范围和实施优先级 |
| [phase-1-tasks.md](phase-1-tasks.md) | Phase 1 milestones and acceptance criteria / 第一阶段任务和验收标准 |
| [demo-script.md](demo-script.md) | Synthetic five-minute product demonstration / 合成数据五分钟演示 |
| [production-readiness-checklist.md](production-readiness-checklist.md) | Production acceptance controls / 生产验收控制项 |
| [development.md](development.md) | Local development and validation / 本地开发与验证 |
| [agent-playground.md](agent-playground.md) | Multi-domain demonstration-layer behavior / 多领域演示层说明 |
| [review-guide.zh-CN.md](review-guide.zh-CN.md) | Chinese business review guide / 中文业务审核指南 |

Project-wide autonomous engineering and approval rules are defined in [AGENTS.md](../AGENTS.md).
