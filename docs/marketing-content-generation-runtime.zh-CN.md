# 受治理的营销内容生成运行时

## 1. 状态与范围

Phase 3.2.3.4 使 Sari Arta 营销内容智能体能够依据已批准的公开营销知识创建受治理草稿。开发环境激活已启用；生产激活仍为 `pending`，灰度比例为 0%。

运行时不发布、不排期、不发送、不修改 CRM 数据、不批准内容，也不开放 IVC 营销生成。

## 2. 运行流程

```text
内容请求
→ RBAC 与租户授权
→ Agent Registry 开发环境激活
→ public_marketing_v1 策略
→ 已批准公开知识检索
→ 证据验证
→ 强类型生成提供方
→ 输出与引用验证
→ 不可变 AI 内容版本
→ Generated
→ 人工审核
```

API 在排队前执行授权，Worker 在嵌入、检索或模型调用前再次授权。权限被撤销或范围不匹配时默认拒绝。

## 3. 模型提供方边界

`MarketingContentProvider` 定义与提供方无关的 `generate(request, evidence)` 契约。

- `mock`：用于开发和测试的确定性、有依据输出。
- `openai`：使用 OpenAI Agents SDK 的无工具适配器，具备强类型输出和受限执行。
- 未来 Qwen 或经批准的私有/本地适配器可以实现相同契约，无需改变治理和持久化。

配置：

```env
MARKETING_CONTENT_PROVIDER=mock
MARKETING_CONTENT_MODEL=gpt-5-mini
MARKETING_CONTENT_TOP_K=5
```

使用 `openai` 必须配置 `OPENAI_API_KEY`。Mock 仍是安全默认值。

## 4. 结构化内容契约

| 类型 | 必需结构 |
|---|---|
| 网站文章 | 标题、摘要、章节、CTA、引用 |
| TikTok 脚本 | 标题、Hook、场景、旁白、屏幕文字、CTA、引用 |
| Instagram Reel 脚本 | 标题、Hook、场景、说明文字、CTA、引用 |
| Facebook 帖子 | 标题、正文、CTA、Hashtag、引用 |
| 邮件草稿 | 主题、预览、问候、正文段落、CTA、结尾、引用 |

支持英文和中文。每条引用必须指向已检索分块。应用验证会拒绝内容类型不匹配、未知分块、缺少引用，以及无依据的价格、产能、认证、质保或交付等受保护声明。

## 5. 知识与证据边界

检索复用现有受治理 pgvector 实现。正式证据必须同时满足：

- 同一租户、商用厨房领域和准确的营销智能体；
- 开发环境已激活且具备生成能力；
- 使用 `public_marketing_v1` 策略；
- 集合可见性为 `public_marketing`；
- 属于允许的公开知识类别；
- 文档和版本已批准；
- 已发布和已启用指针指向同一准确版本；
- 准确智能体绑定已启用且处理已完成；
- 语言、嵌入模型和相似度达到要求。

涉及价格、折扣、供应商、质保、保证或对应中文术语的请求，会在嵌入或模型调用前返回 `insufficient_evidence`。证据较弱或冲突时同样不生成草稿。

## 6. 持久化与治理

异步流程使用 `agent_runs` 和 `content_generation_runs`。后者关联请求、智能体配置、提供方/模型、证据状态、分块引用、验证摘要、耗时和准确输出版本。

成功运行会创建：

- 一个状态为 `generated` 的 `content_asset`；
- 一个来源为 `ai_generated` 的不可变 `content_version`；
- 完整安全的引用元数据，审计日志不复制来源正文；
- 请求和 Agent Run 完成状态；
- 一条不可追加后修改的生成审计事件。

请求生成的人员仍作为内容所有者/创建人承担责任。智能体身份由资产和生成运行记录承载。智能体没有审核、批准、归档、发布、沟通、排期或 CRM 写入权限。

## 7. API 与界面

- `POST /api/v1/content/requests/{request_id}/generate`：幂等 `202` 启动；需要 `content:generate`。
- `GET /api/v1/content/generation-runs/{run_id}`：租户范围的状态和结果。
- `/marketing-content/new`：受治理 AI 请求表单和人工备用流程。
- `/marketing-content/generation/{run_id}`：自动刷新运行状态、证据、引用、证据不足和错误显示。
- `/marketing-content/{asset_id}`：现有人工审核和批准流程。

## 8. 评估基线

可重复的合成评估样例覆盖有依据的网站文章、TikTok、Facebook、中英文配对生成、证据不足、禁止价格、虚构案例防护和内部知识拒绝。确定性基线的有依据正确率、引用完整率、证据不足处理率、结构有效率和双语引用一致率均为 100%，不受支持声明率为 0%。

该基线验证契约和安全控制；生产发布仍需要批准真实公开知识，并由人员单独作出发布决定。

## 9. 本地演示

执行迁移并加载可重复的合成演示知识：

```bash
make services-up
make migrate
make demo-seed
```

`make demo-seed` 会为营销内容智能体创建三个合成 `public_marketing` 知识集合，并使用当前配置的嵌入提供方完成处理。这些记录均明确标记为合成数据，不可用于真实业务。

打开 `http://localhost:3000/marketing-content/new`，选择五种内容类型之一，填写英文或中文请求，然后选择**生成受治理 AI 草稿**。默认 Mock 提供方不需要 API Key。结果页会显示证据状态、模型/提供方、Correlation ID、耗时、完整引用和准确的不可变生成版本。之后可进入内容详情页，继续使用现有人工审核流程。

如需在受控开发环境验证真实提供方适配器，请设置：

```env
MARKETING_CONTENT_PROVIDER=openai
MARKETING_CONTENT_MODEL=gpt-5-mini
OPENAI_API_KEY=...
```

然后重启 API Worker。这不会激活生产环境，也不会授予发布权限。
