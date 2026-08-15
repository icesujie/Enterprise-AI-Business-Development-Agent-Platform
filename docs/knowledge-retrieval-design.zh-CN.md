# 知识检索设计

## 1. 目的和边界

Phase 2.6.1 为已批准的企业知识提供受治理的向量相似度搜索 API。它向获得授权的智能体返回证据分块和准确来源引用。

本阶段**不**实现对话式知识助手、答案生成、Prompt 组装、自主工具调用或外部通信。CRM、Agent Playground、资格评估流程和知识治理转换保持不变。

## 2. 检索架构

```mermaid
flowchart LR
    Caller["获得授权的用户或智能体运行时"] --> API["POST /api/v1/knowledge/search"]
    API --> Tenant["租户身份检查"]
    Tenant --> Agent["智能体启用和能力检查"]
    Agent --> Embed["配置的嵌入提供商"]
    Embed --> Search["受治理的 pgvector 搜索"]
    Search --> Filters["生命周期、版本、绑定和语言过滤"]
    Filters --> Results["证据分块和准确引用"]
```

系统在把查询发送给外部嵌入提供商之前完成授权。这样可以防止未授权智能体请求传输查询内容或产生提供商成本。

## 3. API 合同

### 3.1 端点

```http
POST /api/v1/knowledge/search
Content-Type: application/json
Authorization: Bearer <token>
X-Tenant-Id: <tenant-id>
```

调用者需要 `knowledge:retrieve`。

### 3.2 请求

```json
{
  "tenant_id": "10000000-0000-4000-8000-000000000001",
  "agent_id": "61000000-0000-4000-8000-000000000001",
  "query": "commercial kitchen ventilation exhaust airflow",
  "language": "en",
  "top_k": 5
}
```

| 字段 | 规则 |
|---|---|
| `tenant_id` | 必须与认证工作区租户完全一致 |
| `agent_id` | 必须是拥有已批准检索能力的已启用租户智能体 |
| `query` | 3–2,000 个字符 |
| `language` | `en`、`zh-CN` 或 `id`；准确匹配分块语言 |
| `top_k` | 1–20，默认 5 |

服务器应用 `KNOWLEDGE_RETRIEVAL_MIN_SIMILARITY`，默认值为 `0.15`。普通调用者不能降低证据阈值。

### 3.3 响应

```json
{
  "evidence_status": "sufficient_candidates",
  "tenant_id": "10000000-0000-4000-8000-000000000001",
  "agent_id": "61000000-0000-4000-8000-000000000001",
  "language": "en",
  "results": [
    {
      "document_name": "Commercial Kitchen Ventilation Guide",
      "document_version": 3,
      "chunk_content": "The exhaust airflow must follow the engineered design...",
      "page_number": 7,
      "section": "Ventilation design",
      "metadata": {
        "document_type": "technical_reference",
        "language": "en",
        "chunk_index": 4
      },
      "similarity_score": 0.824531,
      "citation": {
        "document_id": "11111111-1111-4111-8111-111111111111",
        "document_name": "Commercial Kitchen Ventilation Guide",
        "document_version_id": "22222222-2222-4222-8222-222222222222",
        "document_version": 3,
        "chunk_id": "33333333-3333-4333-8333-333333333333",
        "page_number": 7,
        "section": "Ventilation design",
        "content_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
      }
    }
  ]
}
```

没有符合条件的结果时返回 HTTP `200`、`evidence_status = insufficient_evidence` 和空 `results` 列表。这是有效结果，不是系统故障。

## 4. 资格过滤

只有在以下条件全部满足时才会返回分块：

1. `managed_knowledge_chunks.tenant_id` 与认证租户一致。
2. 请求智能体具有已启用的租户激活、活动配置、`knowledge_enabled = true` 和可用的 `approved_knowledge_retrieval` 能力。
3. 分块是为请求的 `agent_id` 创建的。
4. 已启用的 `knowledge_document_agent_bindings` 行连接准确文档和智能体。
5. 集合处于启用状态。
6. 文档生命周期为 `active`，审批状态为 `approved`。
7. 分块版本同时等于 `published_version_id` 和 `active_version_id`。
8. 准确版本审核状态为已批准，版本状态为已生效。
9. 处理运行已经完成。
10. 语言、嵌入提供商、嵌入模型和最低相似度匹配。

搜索不会根据文档元数据或引用 JSON 推断授权。所有安全条件都使用关系列和强制关联。

## 5. 租户和智能体隔离

- 请求 `tenant_id` 必须等于从访问 Token 和 `X-Tenant-Id` 上下文解析出的租户。
- Repository 查询在每张租户数据表上重复明确租户条件。
- PostgreSQL 强制 RLS 继续应用于集合、文档、版本、绑定、处理运行和分块。
- 生产数据库角色不得是超级用户，也不得拥有 `BYPASSRLS`。
- 未知、草稿、暂停或未启用检索的智能体收到 `403`，不会暴露跨租户文档是否存在。
- 禁用文档—智能体绑定会立即让该文档全部分块失去检索资格，但不会删除历史。

IVC 智能体在本阶段仍未启用检索，因为其配置和能力绑定仍是草稿或计划状态。

## 6. 相似度搜索

配置的嵌入抽象使用处理分块记录的相同提供商、模型和 1,536 维度生成一个查询向量。PostgreSQL pgvector 计算余弦距离，并在查询规划器认为有利时使用已有 HNSW `vector_cosine_ops` 索引。

结果按余弦距离升序排列并转换为：

```text
similarity_score = 1 - cosine_distance
```

数据库在 `top_k` 之前应用服务器控制的相似度阈值。准确语言过滤避免静默混合语言；未来的本地化回退需要单独批准的策略。

## 7. 引用和证据边界

每个结果都包含以下稳定标识：

- 逻辑来源文档；
- 不可变文档版本；
- 准确分块；
- 版本号；
- 提取流程能够提供时的页码；
- 提取流程能够提供时的章节标题；
- 分块内容 SHA-256。

结果元数据是证据上下文，不是已验证客户或商业事实。未来知识助手必须引用这些标识，并把空结果视为证据不足。它不得引用不同的当前版本，也不得根据文档名称重新构造引用。

## 8. 失败行为

| 条件 | 结果 |
|---|---|
| 身份认证无效或缺失 | 身份层返回 `401` 或 `403` |
| 请求租户与认证租户不同 | `403 Workspace access denied` |
| 智能体未启用检索 | `403` |
| 语言、`top_k`、查询或额外字段无效 | `422` |
| 没有符合条件或足够相似的证据 | `200 insufficient_evidence` |
| 嵌入提供商不可用 | 安全服务器错误；不返回部分证据 |

响应不会暴露 SQL、对象存储键、向量、系统 Prompt 或提供商凭据。

## 9. 验证覆盖

自动化集成测试验证：

- 正确的相似度检索和完整引用字段；
- 排除未生效、未发布、未绑定、错误语言和无关分块；
- 拒绝跨租户请求；
- 拒绝未启用检索的智能体；
- 禁用绑定后立即撤销资格；
- `managed_knowledge_chunks` 强制执行 RLS，其他租户范围为空。

## 10. 未来知识助手集成

未来助手可以通过窄类型工具调用该端点，并把返回分块作为证据。它必须单独增加答案生成护栏、引用渲染、Prompt 注入防护、Token 预算、评估和人工审核。这些行为明确不属于 Phase 2.6.1。

