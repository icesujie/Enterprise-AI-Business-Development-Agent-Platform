# 企业人工智能业务发展智能体平台

## REST API 设计

> 英文工程基线：[api-design.en.md](api-design.en.md)。中文版本用于内部审核；如有冲突，以英文版本为准。

**参考业务：** 印度尼西亚商用厨房工程，Sari Arta **后端：** FastAPI **基本路径：** `/api/v1` **合同格式：** OpenAPI 3.1 **文档版本：** 1.0

> 中文审阅入口：[中文架构审阅指南](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/review-guide.zh-CN.md>)。重点参考其中“API 设计怎么审核”、术语对照和审核清单。

## Phase 2.5 API 补充

已实现的 `/api/v1/knowledge` 接口支持租户范围的来源、精确领域/智能体绑定、Multipart 文档
上传、不可逆的批准/拒绝、持久化摄取状态、重试和带引用的向量检索。
`knowledge:manage` 仅限管理员；`knowledge:retrieve` 可供授权管理员和销售人员使用，但仍须
满足已启用的租户智能体知识策略。检索返回证据候选或 `insufficient_evidence`，不是对话式
回答接口。完整合同和安全条件参见 `docs/knowledge-foundation-design.zh-CN.md`。

## 1. API 目标

该 API 是 Next.js 应用程序、工作者、AI 智能体工具、n8n 和外部渠道的唯一支持的业务接口。它提供租户隔离、一致的授权、幂等操作、异步工作流程状态、可审计的审批以及稳定合同，这些合同不会暴露数据库或提供商的内部信息。

这是一个以资源为中心的 REST API。 命令仅在操作能够产生有意义的状态转换时使用，例如，确认潜在客户、批准提案或取消智能体运行。

## 2. 国际标准

### 2.1 URL 和媒体类型

- 生产示例：`https://api.example.com/api/v1`
- JSON 媒体类型：`application/json`
- 整个使用 UTF-8 编码。
- 资源名称是复数名词，路径不使用小写字母和连字符。
- JSON 字段名称使用 `snake_case`。
- UUIDs 是不透明的字符串。
- 时间戳采用 RFC 3339 格式，以 UTC 为单位，例如 `2026-08-07T09:30:00Z`。
- 日期使用 `YYYY-MM-DD`。
- 国家使用 ISO 3166-1 alpha-2；货币使用 ISO 4217。
- 电话号码采用 E.164 格式。

### 2.2 必需和标准标题

| 标题 | 使用 |
|---|---|
| `Authorization: Bearer <token>` | 必需，除非是公共捕获、健康和提供者 Webhook |
| `X-Tenant-Id: <uuid>` | 必需用于多租户用户会话；与令牌成员资格进行验证 |
| `X-Request-Id` | 可选客户端关联ID；即使不存在，服务器也会返回一个 |
| `Idempotency-Key` | 适用于需要重试的创建/命令操作 |
| `If-Match: "<version>"` | 必需用于对并发敏感的更新 |
| `Accept-Language` | 支持时，响应本地化偏好 |
| `Traceparent` | W3C 分布式跟踪传播 |

`X-Tenant-Id` 选择调用者授权的其中一个成员；它不授予租户访问权限。

### 2.3 状态码

| 代码 | 含义 |
|---|---|
| `200` | 成功读取、更新或同步命令 |
| `201` | 资源已创建 |
| `202` | 接受异步工作 |
| `204` | 成功执行，但没有返回正文 |
| `400` | 格式错误或语义无效的请求 |
| `401` | 缺少、无效或已过期的身份验证 |
| `403` | 已验证，但未授权 |
| `404` | 资源在租户边界内缺失或故意隐藏 |
| `409` | 状态冲突、重复或幂等性不匹配 |
| `412` | `If-Match` 版本不匹配 |
| `413` | 请求或上传的文件过大 |
| `415` | 不支持的媒体类型 |
| `422` | 字段验证失败 |
| `429` | 速率或配额超额 |
| `503` | 暂时不可用的依赖项或已禁用的功能 |

### 2.4 标准资源元数据

可变资源通常包括：

```json
{
  "id": "8cc724a7-4991-41da-a2d0-52157be1d7d5",
  "created_at": "2026-08-07T09:30:00Z",
  "updated_at": "2026-08-07T09:42:10Z",
  "version": 3
}
```

对于具有版本控制且可变资源的响应，返回 `ETag: "3"`。

### 2.5 分页、过滤和排序

光标分页是默认设置：

```http
GET /api/v1/leads?status=new&limit=50&sort=-created_at&cursor=opaque_value
```

```json
{
  "data": [],
  "page": {
    "next_cursor": "opaque_value_or_null",
    "has_more": false,
    "limit": 50
  }
}
```

- 默认`limit`：25；最大值：100。
- 光标值是不可见的，并且与过滤/排序上下文绑定。
- 排序字段按端点进行允许列表；前缀 `-` 表示降序。
- 过滤器使用重复的参数来处理多个值，在适用时这样做。
- 全文搜索使用 `q`；客户端应进行延迟处理。
- 日期范围使用 `created_from`、`created_to`，或特定领域的名称。

### 2.6 稀疏字段集和扩展

避免任意的 GraphQL 风格的投影。 选定的端点可能支持：

- `include=organization,primary_contact`
- `fields=id,name,status,owner`

允许列表扩展功能可以防止无限连接和数据泄露。 默认响应包括稳定的核心字段和链接/引用 ID。

### 2.7 错误格式

错误遵循 RFC 9457 兼容的 Problem Details 结构：

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Request validation failed",
  "status": 422,
  "detail": "One or more fields are invalid.",
  "instance": "/api/v1/leads",
  "code": "validation_error",
  "request_id": "req_01J4R5K9X2",
  "errors": [
    {
      "field": "estimated_value",
      "code": "greater_than_or_equal",
      "message": "Value must be greater than or equal to 0."
    }
  ]
}
```

消息对用户是安全的。内部堆栈跟踪、SQL错误、原始提供者响应、提示和密钥永远不会返回。

### 2.8 幂等性

`Idempotency-Key` 是必需的，用于：

- 公开提交主导。
- 当提供商 ID 不可用时，对传入事件的重放。
- 创建智能体运行。
- 潜在客户转化。
- 提案制作/发布。
- 审批决定。
- 发送外部消息。
- 批量导入。

服务器根据租户和已验证的身份验证者，对请求进行哈希处理，并保留至少 24 小时的成功响应。 使用不同内容的重用密钥会返回 `409 idempotency_key_reused`。

### 2.9 乐观并发

`PATCH` 请求和材料状态转换需要 `If-Match`，尤其是在同时编辑时。如果返回的是过时的值，则返回：

```json
{
  "type": "https://api.example.com/problems/version-conflict",
  "title": "Resource version conflict",
  "status": 412,
  "detail": "The resource changed after it was loaded.",
  "code": "version_conflict",
  "request_id": "req_01J4R5K9X2",
  "current_version": 4
}
```

## 3. 身份验证设计

### 3.1 人类用户

使用外部 OIDC 身份提供程序，采用授权码流程和 PKCE。

对于 Next.js 浏览器应用程序，建议使用后端-前端会话模式：

1. Next.js 启动 OIDC 登录。
2. 身份提供商验证用户，并强制实施多因素身份验证。
3. Next.js 将会话存储在一个安全的、`HttpOnly`、`Secure`、`SameSite` 的 Cookie 中。
4. 服务器端 Next.js 获取或将一个短期的访问令牌发送给 FastAPI。
5. 浏览器 JavaScript 不会存储长期有效的 bearer 或刷新令牌。

FastAPI 验证签名、颁发方、目标对象、到期时间、不早于时间以及令牌类型。 成员身份和敏感权限从服务器控制的数据中进行解析； 令牌声明可以短暂地缓存，但对撤销敏感的操作会重新检查当前状态。

### 3.2 服务账户

n8n 和内部工作者使用 OAuth 2.0 客户端凭据或工作负载身份 federation。 每个服务账户都有：

- 一个环境和工作负载的所有者。
- 明确的租户或允许的租户范围。
- 限制权限范围。
- 短效访问令牌。
- 在无法避免使用静态客户端密钥时，应旋转凭证。
- 无人工用户界面访问。

在同一信任边界内的工作人员应继续携带工作负载身份和租户上下文，而不是依赖网络位置。

### 3.3 提供者 Webhooks

提供者 Webhook 端点不使用 bearer 身份验证。它们需要提供者特定的 HMAC/签名验证、原始数据验证、时间戳/重放检查、账户查找、有效负载大小限制以及事件去重。

网站公共的潜在客户收集功能使用表单令牌或站点密钥、来源策略、机器人控制、速率限制和同意字段。它不得暴露内部租户ID。

### 3.4 授权模型

RBAC 提供粗粒度的权限；应用程序策略强制执行租户、对象、所有权、状态和值的阈值。

代表范围：

| 范围 | 目的 |
|---|---|
| `crm:read`, `crm:write` | 读取/更新允许的 CRM 记录 |
| `leads:assign`, `leads:qualify`, `leads:convert` | 主命令 |
| `opportunities:manage` | 管道操作 |
| `conversations:read`, `messages:draft`, `messages:send` | 消息传递 |
| `knowledge:read`, `knowledge:manage` | 检索与整理 |
| `agents:run`, `agents:inspect`, `agents:admin` | 开始，检查，配置智能体工作流程 |
| `models:read`, `models:manage` | 检查已批准的部署，或管理提供商/路由配置 |
| `proposals:read`, `proposals:write`, `proposals:approve`, `proposals:issue` | 提案生命周期 |
| `content:write`, `content:approve`, `content:publish` | 内容生命周期 |
| `integrations:manage` | 连接器管理 |
| `audit:read`, `exports:create` | 对敏感审计/导出操作 |

一个智能体工具接收发起方和服务器生成的权限集。它无法扩展其权限范围。

### 3.5 CSRF、CORS 和速率限制

- 使用Cookie进行身份验证的调用需要进行CSRF保护。
- CORS 是一种显式的生产源允许列表；不支持通配符和凭据。
- 速率限制适用于每个 IP 地址、用户/服务账户、租户、端点以及公共表单/提供商账户。
- 敏感命令和AI的使用也会强制执行租户配额。
- `429` 返回 `Retry-After` 以及机器可读的配额元数据。

## 4. 终端目录

该目录描述了第一套企业级API基线。 管理端点可能在核心CRM工作流程之后发布，但仍保留这些资源合同。

### 4.1 会话和租户上下文

| 方法 | 路径 | 目的 | 范围 |
|---|---|---|---|
| `GET` | `/me` | 当前身份、会员、角色、权限 | 已验证 |
| `GET` | `/tenants/{tenant_id}` | 租户资料/设置仅对会员可见 | 已验证的成员 |
| `PATCH` | `/tenants/{tenant_id}` | 更新租户默认/策略 | `tenant:admin` |
| `GET` | `/memberships` | 列出租户成员 | `memberships:read` |
| `POST` | `/memberships/invitations` | 邀请用户 | `memberships:manage` |
| `PATCH` | `/memberships/{membership_id}` | 暂停/更新会员资格 | `memberships:manage` |
| `PUT` | `/memberships/{membership_id}/roles` | 替换已分配的角色 | `roles:assign` |
| `GET` | `/roles` | 列出角色和权限 | `roles:read` |

### 4.2 组织和联系人

| 方法 | 路径 | 目的 |
|---|---|---|
| `GET`, `POST` | `/organizations` | 搜索/列出或创建组织 |
| `GET`, `PATCH`, `DELETE` | `/organizations/{organization_id}` | 读取、更新或软删除 |
| `GET` | `/organizations/{organization_id}/timeline` | 综合活动时间表 |
| `POST` | `/organizations/{organization_id}/research-runs` | 启动客户研究智能体运行 |
| `POST` | `/organizations/{organization_id}/research-verifications` | 验证所选的研究事实 |
| `GET`, `POST` | `/contacts` | 搜索/列出或创建联系人 |
| `GET`, `PATCH`, `DELETE` | `/contacts/{contact_id}` | 读取、更新或软删除 |
| `GET` | `/contacts/{contact_id}/timeline` | 联系活动时间线 |
| `POST` | `/contacts/{contact_id}/consents` | 记录授权/撤回同意 |

范围是用于读取的`crm:read`，以及用于突变的`crm:write`；同意记录可能需要`consent:manage`。

### 4.3 导线

| 方法 | 路径 | 目的 | 注释 |
|---|---|---|---|
| `POST` | `/public/lead-submissions` | 公共网站潜在客户获取 | 站点令牌、速率限制、幂等性 |
| `GET`, `POST` | `/leads` | 列出/创建潜在客户 | 手动创建需要 `crm:write` |
| `GET`, `PATCH`, `DELETE` | `/leads/{lead_id}` | 读取/更新/归档 | `If-Match` 在更新时 |
| `POST` | `/leads/{lead_id}/assignments` | 分配或取消所有权 | `leads:assign` |
| `POST` | `/leads/{lead_id}/qualification-runs` | 开始人工智能资格认证 | `leads:qualify`，返回 `202` |
| `GET` | `/leads/{lead_id}/assessments` | 资质历史 | `crm:read` |
| `POST` | `/leads/{lead_id}/assessments/{assessment_id}/reviews` | 批准/拒绝评估 | `leads:qualify` |
| `POST` | `/leads/{lead_id}/conversions` | 原子地创建机会 | `leads:convert`, 幂等 |
| `POST` | `/leads/{lead_id}/disqualifications` | 取消资格，并说明原因 | `leads:qualify` |

### 4.4 机会、活动和任务

| 方法 | 路径 | 目的 |
|---|---|---|
| `GET`, `POST` | `/opportunities` | 管道列表/创建 |
| `GET`, `PATCH` | `/opportunities/{opportunity_id}` | 读取/更新 |
| `POST` | `/opportunities/{opportunity_id}/stage-transitions` | 已验证的阶段变更 |
| `POST` | `/opportunities/{opportunity_id}/close-won` | 马克凭借提供所需信息获胜 |
| `POST` | `/opportunities/{opportunity_id}/close-lost` | 马克丢失，原因未知 |
| `GET`, `POST` | `/activities` | 过滤或记录活动 |
| `GET`, `POST` | `/tasks` | 列出/创建任务 |
| `GET`, `PATCH`, `DELETE` | `/tasks/{task_id}` | 读取/更新/软删除 |
| `POST` | `/tasks/{task_id}/completion` | 完整地实现幂等性 |

阶段过渡使用命令，因为服务器会验证允许的过渡、权限、必需字段、审计数据以及下游事件。

### 4.5 对话和消息

| 方法 | 路径 | 目的 |
|---|---|---|
| `GET` | `/conversations` | 收件/搜索 |
| `POST` | `/conversations` | 创建手动/内部对话 |
| `GET`, `PATCH` | `/conversations/{conversation_id}` | 读取/更新任务/状态 |
| `GET` | `/conversations/{conversation_id}/messages` | 基于光标分页的消息 |
| `POST` | `/conversations/{conversation_id}/message-drafts` | 保存人工或AI辅助的草稿 |
| `POST` | `/conversations/{conversation_id}/messages` | 排队发送外部消息 |
| `POST` | `/messages/{message_id}/delivery-retries` | 在审查后，明确重试 |
| `POST` | `/webhooks/{provider}/{account_key}` | 提供者 Webhook 接入 |

创建一条向外发送的消息需要 `messages:send`、幂等性、当前同意/政策检查，以及如果消息被生成或具有商业影响，则需要批准。

### 4.6 文件

| 方法 | 路径 | 目的 |
|---|---|---|
| `POST` | `/files/upload-intents` | 验证元数据并返回预签上传 |
| `POST` | `/files/{file_id}/completion` | 确认上传、校验和，并开始扫描 |
| `GET` | `/files/{file_id}` | 读取元数据 |
| `POST` | `/files/{file_id}/download-intents` | 返回授权下载，有效期短 |
| `DELETE` | `/files/{file_id}` | 请求有控制的删除 |

未扫描的文件无法被普通用户导入、渲染、下载或发送给 AI 提供商。

### 4.7 知识库

| 方法 | 路径 | 目的 |
|---|---|---|
| `GET`, `POST` | `/knowledge/sources` | 列表/创建源 |
| `GET`, `PATCH` | `/knowledge/sources/{source_id}` | 读取/更新源 |
| `POST` | `/knowledge/sources/{source_id}/sync-runs` | 开始导入/同步 |
| `GET`, `POST` | `/knowledge/documents` | 搜索/创建文档元数据 |
| `GET`, `PATCH` | `/knowledge/documents/{document_id}` | 读取/更新文档 |
| `POST` | `/knowledge/documents/{document_id}/versions` | 从干净的文件或文本创建版本 |
| `GET` | `/knowledge/documents/{document_id}/versions` | 版本历史 |
| `POST` | `/knowledge/document-versions/{version_id}/approvals` | 批准检索 |
| `POST` | `/knowledge/search` | 授权混合搜索/调试 |
| `POST` | `/knowledge/answer-runs` | 启动接地知识型智能体 |

原始数据块搜索仅限于知识管理人员和诊断用户。普通用户只能获得引用过的答案或已批准的文档结果，而不能访问不受限制的向量存储。

### 4.8 智能体运行和审批

| 方法 | 路径 | 目的 |
|---|---|---|
| `POST` | `/agent-runs` | 以通用方式启动允许的工作流程 |
| `GET` | `/agent-runs` | 过滤运行历史 |
| `GET` | `/agent-runs/{run_id}` | 运行状态和允许的结果 |
| `GET` | `/agent-runs/{run_id}/events` | SSE 进度流 |
| `GET` | `/agent-runs/{run_id}/steps` | 已删除的检查步骤（仅限授权人员） |
| `POST` | `/agent-runs/{run_id}/cancellations` | 请求取消 |
| `POST` | `/agent-runs/{run_id}/retries` | 重试符合条件的已失败的运行，作为新的运行 |
| `GET` | `/approvals` | 当前用户的审批队列 |
| `GET` | `/approvals/{approval_id}` | 审批详情和操作预览 |
| `POST` | `/approvals/{approval_id}/decisions` | 批准或拒绝 |

通用 `/agent-runs` 端点接受已授权的 `workflow_type`，而不是任意提示、工具、系统指令或模型 ID。 针对特定领域的启动端点更可取，因为它们提供更清晰的授权和输入模式。

### 4.9 建模提供商和路由

| 方法 | 路径 | 目的 |
|---|---|---|
| `GET` | `/model-providers` | 授权管理员可见的提供者元数据列表 |
| `POST` | `/model-providers` | 注册 OpenAI、Qwen、兼容云或本地提供商的元数据 |
| `GET`, `PATCH` | `/model-providers/{provider_id}` | 检查或更新提供商状态和非密钥设置 |
| `POST` | `/model-providers/{provider_id}/connection-tests` | 验证凭证、端点、协议和安全能力探测 |
| `GET`, `POST` | `/model-deployments` | 列出或注册已批准的模型部署 |
| `GET`, `PATCH` | `/model-deployments/{deployment_id}` | 检查/更新状态、功能、限制和数据策略 |
| `POST` | `/model-deployments/{deployment_id}/evaluation-runs` | 在激活之前，运行工作流程评估套件 |
| `POST` | `/model-deployments/{deployment_id}/health-checks` | 执行授权的健康/能力检查 |
| `GET`, `POST` | `/model-routing-policies` | 列出或创建具有版本号的租户/工作流程路由策略 |
| `POST` | `/model-routing-policies/{policy_id}/activations` | 激活已评估的策略版本 |
| `POST` | `/model-routing-policies/{policy_id}/retirements` | 退回一个保单版本 |

提供方 API 永远不会返回凭据、原始密钥引用或不受限制的私有端点信息。普通智能体调用者无法直接选择提供方或模型。服务器使用工作流程要求、租户数据策略、部署健康状况、评估状态、预算和备用规则来解析活动路由策略。

注册一个与 OpenAI 兼容的端点，并不会自动将工具调用、结构化输出、跟踪等功能标记为已支持。这些功能只有在经过有控制的测试和特定工作流程的评估后才会生效。

### 4.10 建议

| 方法 | 路径 | 目的 |
|---|---|---|
| `GET`, `POST` | `/proposals` | 列出/创建提案模板 |
| `GET`, `PATCH` | `/proposals/{proposal_id}` | 读取/更新提案元数据 |
| `GET` | `/proposals/{proposal_id}/versions` | 版本历史 |
| `POST` | `/proposals/{proposal_id}/generation-runs` | 生成由人工智能辅助生成的草稿版本 |
| `POST` | `/proposals/{proposal_id}/versions` | 创建人工编辑的不可变版本 |
| `GET` | `/proposal-versions/{version_id}` | 读取一个版本 |
| `POST` | `/proposal-versions/{version_id}/render-runs` | 异步渲染 PDF/DOCX 资源 |
| `POST` | `/proposal-versions/{version_id}/review-requests` | 请求批准 |
| `POST` | `/proposals/{proposal_id}/issuances` | 已批准的版本 |
| `POST` | `/proposals/{proposal_id}/acceptances` | 已验证接受 |

提案发布检查确保所选版本已获得批准、有效、未过期、完整呈现，并且与批准摘要保持一致。

### 4.11 营销内容

| 方法 | 路径 | 目的 |
|---|---|---|
| `GET`, `POST` | `/content-items` | 列出/创建内容项 |
| `GET`, `PATCH` | `/content-items/{content_id}` | 读取/更新元数据 |
| `GET` | `/content-items/{content_id}/versions` | 版本历史 |
| `POST` | `/content-items/{content_id}/generation-runs` | 生成草稿 |
| `POST` | `/content-items/{content_id}/versions` | 创建修改后的版本 |
| `POST` | `/content-versions/{version_id}/review-requests` | 请求批准 |
| `POST` | `/content-items/{content_id}/schedules` | 批准的内容安排 |
| `POST` | `/content-items/{content_id}/publications` | 通过已批准的连接器发布 |

### 4.12 集成与自动化

| 方法 | 路径 | 目的 |
|---|---|---|
| `GET`, `POST` | `/integrations` | 列出/创建集成设置 |
| `GET`, `PATCH`, `DELETE` | `/integrations/{integration_id}` | 读取/更新/禁用 |
| `POST` | `/integrations/{integration_id}/connection-tests` | 测试凭证/权限 |
| `POST` | `/integrations/{integration_id}/secret-rotations` | 开始受控秘密旋转 |
| `GET` | `/automation-executions` | 检查租户 n8n 工作流程状态 |
| `GET` | `/automation-executions/{execution_id}` | 执行细节 |
| `POST` | `/internal/events/{event_type}` | 服务账户 n8n 事件回调 |

集成响应永远不会返回凭据值。 密钥创建接受一次性值（通过 TLS）或密钥管理器引用，然后只返回元数据。

### 4.13 审计、出口和运营

| 方法 | 路径 | 目的 |
|---|---|---|
| `GET` | `/audit-events` | 过滤租户审计事件 |
| `POST` | `/imports` | 开始验证或应用已确认的导入 |
| `GET` | `/imports/{import_id}` | 导入验证/应用状态 |
| `POST` | `/exports` | 开始受控的数据/报告导出 |
| `GET` | `/exports/{export_id}` | 导出状态 |
| `POST` | `/data-subject-requests` | 创建隐私请求 |
| `GET` | `/data-subject-requests/{request_id}` | 跟踪隐私请求 |
| `GET` | `/health/live` | 过程生命性；无依赖细节 |
| `GET` | `/health/ready` | 协调器准备状态 |
| `GET` | `/version` | 安全构建/版本元数据 |

健康端点显示，没有租户、拓扑、依赖地址或秘密信息。

## 5. 请求和响应示例

### 5.1 公共主导提交

```http
POST /api/v1/public/lead-submissions
Content-Type: application/json
Idempotency-Key: site-8f87f04a-09de-4e12-b98a-a98d461caf42
X-Site-Token: public_site_token
```

```json
{
  "contact": {
    "first_name": "Andi",
    "last_name": "Pratama",
    "email": "andi@example.co.id",
    "phone_e164": "+6281234567890",
    "preferred_language": "id"
  },
  "organization": {
    "name": "Nusantara Hospitality Group",
    "website_url": "https://example.co.id",
    "country_code": "ID"
  },
  "inquiry": {
    "message": "We need a central kitchen for a new hotel in Surabaya.",
    "project_country_code": "ID",
    "project_city": "Surabaya",
    "target_timeline": "Q1 2027"
  },
  "attribution": {
    "source": "website",
    "campaign": "hotel-kitchen-2026"
  },
  "consent": {
    "privacy_policy_version": "2026-07",
    "contact_consent": true,
    "marketing_consent": false
  },
  "captcha_token": "provider_token"
}
```

```json
{
  "submission_id": "83871747-3b7b-4b38-af5a-b87f5bdf0875",
  "status": "accepted",
  "message": "Your inquiry has been received."
}
```

返回 `202 Accepted`。请勿透露内部潜在客户评分、销售人员、租户配置或重复匹配结果。

### 5.2 创建内部负责人

```http
POST /api/v1/leads
Authorization: Bearer eyJ...
X-Tenant-Id: 9af036aa-5708-497d-b1af-f2b3d3ff42a2
Idempotency-Key: 01J4R75D5AV3DNHZQBA91K6PX0
```

```json
{
  "contact_id": "c58757cb-2960-4c4a-a886-12e9a3bd6e53",
  "organization_id": "391d4c1b-bd8a-4081-a1b7-29b34d848a3c",
  "source_channel": "manual",
  "source_detail": "Trade show Jakarta",
  "inquiry_summary": "Hotel group planning a 2,000-meal-per-day central kitchen.",
  "priority": "high",
  "project_country_code": "ID",
  "estimated_value": "1250000000.0000",
  "currency": "IDR"
}
```

```json
{
  "id": "06057e69-7b5f-4d32-b2ad-6c39470a2664",
  "status": "new",
  "priority": "high",
  "contact_id": "c58757cb-2960-4c4a-a886-12e9a3bd6e53",
  "organization_id": "391d4c1b-bd8a-4081-a1b7-29b34d848a3c",
  "source_channel": "manual",
  "inquiry_summary": "Hotel group planning a 2,000-meal-per-day central kitchen.",
  "estimated_value": {
    "amount": "1250000000.0000",
    "currency": "IDR"
  },
  "owner": null,
  "created_at": "2026-08-07T09:30:00Z",
  "updated_at": "2026-08-07T09:30:00Z",
  "version": 1
}
```

### 5.3 安全更新主线

```http
PATCH /api/v1/leads/06057e69-7b5f-4d32-b2ad-6c39470a2664
If-Match: "1"
Content-Type: application/merge-patch+json
```

```json
{
  "priority": "urgent",
  "target_timeline": "Tender closes 2026-09-15"
}
```

响应返回完整的更新后的表示形式和 `ETag: "2"`。 JSON Merge Patch 的语义区分省略的字段和明确的 `null`。

### 5.4 开始筛选潜在客户

```http
POST /api/v1/leads/06057e69-7b5f-4d32-b2ad-6c39470a2664/qualification-runs
Idempotency-Key: 01J4R7H4QK7B0PZ5E02DSZYKE3
```

```json
{
  "rubric_key": "commercial_kitchen_project_v1",
  "language": "en",
  "force_human_review": false
}
```

```json
{
  "run_id": "22f27424-2e37-4237-96bf-a4014425725f",
  "workflow_type": "lead_qualification",
  "status": "queued",
  "status_url": "/api/v1/agent-runs/22f27424-2e37-4237-96bf-a4014425725f",
  "events_url": "/api/v1/agent-runs/22f27424-2e37-4237-96bf-a4014425725f/events",
  "created_at": "2026-08-07T09:35:00Z"
}
```

返回 `202 Accepted` 和 `Location`，指向正在运行的进程。

### 5.5 已完成的资格认证结果

```json
{
  "id": "22f27424-2e37-4237-96bf-a4014425725f",
  "workflow_type": "lead_qualification",
  "status": "succeeded",
  "subject": {
    "type": "lead",
    "id": "06057e69-7b5f-4d32-b2ad-6c39470a2664"
  },
  "result": {
    "assessment_id": "14fd9a1b-8732-4465-8a32-bb7bce687606",
    "score": 82.5,
    "tier": "hot",
    "need_summary": "A high-capacity central kitchen for a hotel group in Surabaya.",
    "qualification": {
      "budget_status": "unknown",
      "authority_status": "partial",
      "need_status": "confirmed",
      "timeline_status": "confirmed"
    },
    "missing_information": [
      "Approved budget range",
      "Decision-making committee",
      "Available floor plan and utility loads"
    ],
    "recommended_action": "Schedule a discovery call and request the floor plan.",
    "confidence": 0.84,
    "review_status": "pending"
  },
  "usage": {
    "input_tokens": 3450,
    "output_tokens": 620
  },
  "model": {
    "provider_type": "qwen_cloud",
    "deployment_key": "qwen-business-prod-id",
    "model_id": "approved-qwen-model",
    "fallback_used": false
  },
  "started_at": "2026-08-07T09:35:02Z",
  "completed_at": "2026-08-07T09:35:18Z"
}
```

使用和成本的可视化可能受到角色限制。原始的推理过程永远不会返回。

### 5.6 将潜在客户转化为商机

```http
POST /api/v1/leads/06057e69-7b5f-4d32-b2ad-6c39470a2664/conversions
Idempotency-Key: 01J4R8CBP7DX6WETKG4TZ7C68V
If-Match: "4"
```

```json
{
  "opportunity": {
    "name": "Nusantara Surabaya Central Kitchen",
    "stage": "discovery",
    "estimated_value": "1250000000.0000",
    "currency": "IDR",
    "expected_close_date": "2026-12-15",
    "owner_membership_id": "68246334-142f-44c7-9525-9fb5f8796042"
  },
  "create_follow_up_task": true
}
```

```json
{
  "lead": {
    "id": "06057e69-7b5f-4d32-b2ad-6c39470a2664",
    "status": "converted",
    "version": 5
  },
  "opportunity": {
    "id": "d74ec8ac-bd19-4baa-a080-42e78bec2e84",
    "name": "Nusantara Surabaya Central Kitchen",
    "stage": "discovery",
    "status": "open",
    "version": 1
  },
  "task_id": "fc8f8d60-0efb-47da-b928-92b3e33f3d3e"
}
```

主状态、机会、任务、审计记录和“已发送”事件均以原子方式提交。

### 5.7 基础知识解答

```http
POST /api/v1/knowledge/answer-runs
Idempotency-Key: 01J4R8STZGJ6FH3SQSQDW9B16K
```

```json
{
  "question": "What Sari Arta capabilities are relevant for a 2,000-meal-per-day hotel central kitchen?",
  "context": {
    "opportunity_id": "d74ec8ac-bd19-4baa-a080-42e78bec2e84"
  },
  "language": "en"
}
```

完成结果：

```json
{
  "run_id": "32e5fc94-6e96-43fd-af62-362cc5fcf649",
  "status": "succeeded",
  "answer": "The approved knowledge base supports planning, engineering, equipment selection, installation, and after-sales service for commercial-kitchen projects. Capacity-specific suitability still requires discovery and engineering validation.",
  "citations": [
    {
      "citation_id": "cit_01J4R9A2",
      "document_id": "f41c1edb-8942-4775-83cf-bfd8ee7b11ea",
      "document_version": 3,
      "title": "Sari Arta Company Capabilities",
      "section": "Engineering and Installation",
      "page": 5
    }
  ],
  "uncertainties": [
    "The source does not establish capacity for this specific site."
  ]
}
```

### 5.8 开始生成提案

```http
POST /api/v1/proposals/1604c5a1-4b91-4329-8fa6-c1f8272023b2/generation-runs
Idempotency-Key: 01J4R9F54GJZDCDNQ0C2H5YSK1
```

```json
{
  "opportunity_version": 7,
  "template_id": "0fcf1058-4ee4-418b-91e0-48ca8c673266",
  "language": "en",
  "currency": "IDR",
  "sections": [
    "executive_summary",
    "understanding_of_requirements",
    "proposed_solution",
    "delivery_approach",
    "assumptions_and_exclusions"
  ],
  "pricing_source": "approved_opportunity_lines"
}
```

结果是一个新的不可变提案版本，在`draft`中；它不会自动发布。

### 5.9 审批决定

```http
POST /api/v1/approvals/bfe120bd-10a2-44b7-b741-f90193db9131/decisions
Idempotency-Key: 01J4R9VN4GKCM7V2XFFXGZ1R1Q
If-Match: "1"
```

```json
{
  "decision": "approved",
  "action_digest": "sha256:86ab8e8f...",
  "comment": "Commercial and technical sections reviewed."
}
```

```json
{
  "id": "bfe120bd-10a2-44b7-b741-f90193db9131",
  "status": "approved",
  "decided_by": {
    "user_id": "6682068f-c8dc-4278-83e2-16837893d25c",
    "display_name": "Sales Manager"
  },
  "decided_at": "2026-08-07T10:05:00Z",
  "version": 2
}
```

如果底层预览不再与 `action_digest` 匹配，则返回 `409 approval_subject_changed`。

### 5.10 排队发送一条消息

```http
POST /api/v1/conversations/25f9bd1f-156b-426b-b78e-36ff5f114a76/messages
Idempotency-Key: 01J4RA6K3Z0SP62EV6P8DPQFA6
```

```json
{
  "draft_message_id": "e809659e-b2ef-4882-b5e1-3863973ace67",
  "channel": "whatsapp",
  "recipient_contact_id": "c58757cb-2960-4c4a-a886-12e9a3bd6e53",
  "approved_template_key": "discovery_call_follow_up",
  "scheduled_at": null
}
```

```json
{
  "id": "5b1bbb85-c49d-4a7b-976e-48877f36ec96",
  "conversation_id": "25f9bd1f-156b-426b-b78e-36ff5f114a76",
  "direction": "outbound",
  "delivery_status": "queued",
  "created_at": "2026-08-07T10:10:00Z"
}
```

返回 `202`。 供应商的接受和交付是异步进行的。

## 6. 智能体进度实时流式传输

`GET /agent-runs/{run_id}/events` 使用服务器端事件：

```text
event: run.status
id: 12
data: {"run_id":"22f27424-2e37-4237-96bf-a4014425725f","status":"running"}

event: run.progress
id: 13
data: {"stage":"retrieving_knowledge","message":"Reviewing approved product and capability sources."}

event: run.completed
id: 14
data: {"status":"succeeded","result_url":"/api/v1/agent-runs/22f27424-2e37-4237-96bf-a4014425725f"}
```

规则：

- 在打开流之前进行身份验证，并重新检查租户/运行的访问权限。
- 支持`Last-Event-ID`的短连接恢复窗口。
- 事件包含状态和安全摘要，但不包含隐藏的推理、秘密或不受限制的工具负载。
- 发送心跳信号并关闭，在终端状态后。
- 客户端会回退到使用条件请求进行轮询。

## 7. Webhook 协议

### 7.1 进货供应商

仅在`/webhooks/{provider}/{account_key}`条件下，接受提供者特定的负载。 目标地址：

1. 读取原始内容，并严格限制大小。
2. 验证提供商的签名和时间戳。
3. 从不透明的`account_key`中解析集成账户。
4. 通过提供者事件 ID 或报文哈希，以及时间窗口进行去重。
5. 保留一个受限制的 webhook 记录。
6. 返回提供方所需的确认。
7. 异步处理事件。

未支持的事件可能会被确认并记录为 `ignored`，以防止无限次提供方重试。

### 7.2 向外平台 Webhooks

如果提供租户 Webhooks，则事件使用一种基于 CloudEvents 的结构：

```json
{
  "specversion": "1.0",
  "id": "evt_01J4RAN2K3",
  "type": "opportunity.stage_changed.v1",
  "source": "bd-platform",
  "subject": "opportunities/d74ec8ac-bd19-4baa-a080-42e78bec2e84",
  "time": "2026-08-07T10:15:00Z",
  "tenant_id": "9af036aa-5708-497d-b1af-f2b3d3ff42a2",
  "data": {
    "opportunity_id": "d74ec8ac-bd19-4baa-a080-42e78bec2e84",
    "previous_stage": "discovery",
    "stage": "solution_design",
    "version": 8
  }
}
```

使用带有版本号的 HMAC 标头精确地对消息进行签名，包含时间戳，至少重试一次，采用指数退避策略，公开传递状态，并允许在重叠验证的情况下进行密钥轮换。

## 8. 大批量操作和导出

批量导入和导出始终是异步操作。

`POST /imports` 接受一个干净上传的文件引用、映射、重复策略和“模拟运行”标志。 它返回一个作业资源。 验证结果可以在不进行任何修改的情况下下载。 导入操作需要明确确认，并与“模拟运行”摘要进行比较。

`POST /exports` 需要指定资源类型、过滤器、字段白名单、目的和格式。 大量/敏感的导出可能需要审批。 结果文件使用临时的下载意图、在适当情况下添加水印、审计事件和有限的保留期。

不要提供通用的、任意的 SQL/报告端点。

## 9. 版本管理和兼容性

- 主要版本在 URL 中：`/api/v1`。
- 在不进行主要版本更新的情况下，可以添加向后兼容的字段。
- 现有的字段含义和类型在主要版本内不会改变。
- 客户端忽略未知的响应字段。
- 引入重大变更时，会提供迁移指南、弃用提示、Telemetry 审查以及宣布停止使用。
- 事件类型和智能体输入/输出的模式具有独立的版本。
- OpenAPI 文档在 CI 中生成，并进行差异比较以检测重大变更。

示例弃用标题：

```http
Deprecation: true
Sunset: Sat, 01 Aug 2027 00:00:00 GMT
Link: <https://docs.example.com/migrations/v1-old-endpoint>; rel="deprecation"
```

## 10. API 安全要求

- 在每个基于ID的端点上强制执行对象级别的授权。
- 使用参数化数据库访问。
- 验证所有请求和提供者模式，并在适当情况下，采用严格的额外字段策略。
- 将最大深度/长度/计数约束应用于 JSON 和字符串。
- 永远不要接受任意的对象存储键或 URL 用于服务器上的数据获取；请使用已颁发的的文件 ID 和出口允许列表。
- 对富文本进行清理，并防止存储型 XSS 攻击。
- 在使用前，请检查文件是否存在恶意软件。
- 在日志、错误、跟踪和审计摘要中，删除敏感属性。
- 记录与安全相关的拒绝，同时避免泄露目标的存在。
- 智能体端接受业务意图和有限选项，而不是系统提示或任意工具。
- 智能体调用者不能覆盖模型路由。 管理员模型配置是版本化的、经过评估的、权限控制的，并且经过审计。
- 模型路由必须在分发之前，强制执行经过租户批准的提供商、区域、保留策略、网络边界和最大数据分类策略。
- 后续操作在执行时重新检查权限、状态、同意、策略、审批摘要以及资源版本。

## 11. 可观测性和操作行为

每个响应都包含 `X-Request-Id`。 异步资源相关联：

- `request_id`
- `job_id`
- `agent_run_id`
- `automation_execution_id`
- `trace_id`
- 业务资源 ID

指标包括端点延迟/错误率、授权拒绝、幂等重试、速率限制拒绝、队列确认时间、智能体完成/成本、提供商交付以及 Webhook 的年龄。

该API没有公开的指标端点。操作的 telemetry 信息可以通过受保护的 observability 平台访问。

## 12. OpenAPI 和合同治理

由FastAPI生成的OpenAPI被视为产品合同，而不是被视为次要输出。

- 操作ID稳定且易于阅读。
- 每个端点都记录权限、幂等性、并发、速率限制和错误代码。
- 请求和响应的模式包含示例和字段描述。
- 为 Next.js 应用程序生成 TypeScript 类型/客户端。
- n8n 使用一个受限的服务 API 规范，其中仅包含其批准的端点。
- 合同测试验证客户端是否符合规范。
- 安全测试涵盖跨租户ID、过时的版本、重复执行的命令、已过期的批准、恶意上传以及类似提示的内容。
- 提供方合同测试验证 Qwen 和本地部署是否符合已声明的结构化输出、工具调用、流式传输、超时、使用和错误规范化功能。
- 在 CI 中，API 变更会进行向后兼容性检查。

## 13. 初始终点交付订单

1. 身份验证上下文、租户、成员、健康状况和审计基础。
2. 组织、联系人、潜在客户、活动、任务和潜在客户转化。
3. 对话、消息、网站/电子邮件 Webhook 捕获以及文件生命周期。
4. 知识获取、搜索和基于知识的答案运行。
5. 资格评估和销售代表运行/审批检查。
6. 机会和提案的生成/审查/发布。
7. 客户调研、营销内容、额外的渠道集成，以及 n8n 自动化。
8. 隐私工作流程、高级导出功能和租户管理。

每个发布都需要进行 OpenAPI 审查、授权矩阵测试、租户隔离测试、幂等性/并发性测试，以及在发布到生产环境之前，需要创建运营仪表盘。
