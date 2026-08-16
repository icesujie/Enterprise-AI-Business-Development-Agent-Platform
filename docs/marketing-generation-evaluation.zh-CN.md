# 营销内容生成评估与 UX 验证

**状态：** Phase 3.2.3.5 已实现确定性开发评估；业务验收为有条件通过  
**基线：** `marketing_generation_baseline.mock.v1.json`  
**边界：** 仅限内部评估和人工审核；不包含发布、发送、排期、CRM 写入或外部自动化

## 1. 目的

本阶段评估受治理营销内容智能体的输出是否适合 B2B 营销审核，而不只是 Schema 有效。新增可重复业务数据集、明确质量指标、不可变人工反馈、渠道专用预览和只读内部评估投影。自动评分只用于辅助审核，绝不是审批决定；系统不保存或展示模型隐藏推理。

## 2. 评估流程

```text
合成业务场景
→ 已批准公开证据样例
→ 受治理营销模型提供方
→ Schema / 声明 / 引用验证
→ 业务质量评估
→ 渠道预览
→ 人工反馈
→ 准确版本审批
→ 存在批准版本时计算人工编辑距离
```

## 3. 版本化业务数据集

`marketing_generation_cases.v1.json` 包含十个合成案例：五个场景，每个场景配有英文和中文版本。

| 场景 | 内容类型 | 受众 / 渠道 |
|---|---|---|
| 印度尼西亚学校厨房项目 | 网站文章 | 学校 / 网站 |
| 学校食堂改造 | TikTok 脚本 | 学校 / TikTok |
| 工厂食堂 | Instagram Reel 脚本 | 工厂 / Instagram |
| 医院 / 机构厨房 | Facebook 帖子 | 医院 / Facebook |
| 中央厨房产能规划 | 邮件草稿 | 中央厨房 / 邮件 |

所有事实均为合成公开营销样例，不包含真实客户身份信息。

## 4. 质量指标

每个成功草稿都会获得确定性投影，并保存在 `content_generation_runs.validation_summary.quality_evaluation`。

| 指标 | 含义 |
|---|---|
| 品牌契合 | 是否恰当使用已批准的 Sari Arta 身份和定位 |
| 受众契合 | 是否适合目标机构受众 |
| 渠道契合 | 是否符合所选渠道结构 |
| 清晰度 | 内容长度和结构是否便于审核 |
| CTA 质量 | 是否有明确下一步行动 |
| 事实依据 | 模型引用是否映射到检索 Citation Chunk |
| 不受支持声明 | 证据/引用边界失败；越低越好 |
| 重复控制 | 对重复审核片段扣分 |
| 内容实用性 | 面向审核的综合实用性 |
| 人工编辑距离 | 从 AI 文本到准确人工批准版本的标准化差异；`0` 未修改，`1` 完全不同 |

评分不能决定法律、商业、技术或最终品牌审批。

## 5. 确定性基线

| 指标 | 结果 |
|---|---:|
| 品牌契合 | 90.0 |
| 受众契合 | 90.0 |
| 渠道契合 | 95.0 |
| 清晰度 | 80.0 |
| CTA 质量 | 95.0 |
| 事实依据 | 100.0 |
| 不受支持声明 | 0.0 |
| 重复控制 | 74.9 |
| 内容实用性 | 91.5 |
| 综合评分 | 90.71 |
| 结构有效率 | 100% |
| 引用完整率 | 100% |

未来 Prompt、模型、检索阈值、知识集合或内容 Schema 改变时，必须与版本化 Mock 基线比较。每次运行记录延迟，但延迟不是固定回归断言。

## 6. 人工反馈治理

`content_review_feedback` 保存人工编写的反馈，并绑定准确版本和 SHA-256 校验和。类别包括 `useful`、`too_generic`、`brand_tone_issue`、`weak_cta`、`insufficient_evidence`、`too_long` 和 `channel_mismatch`。

提交需要 `content:review`。记录受租户隔离、强制 PostgreSQL RLS、仅追加和审计关联保护。系统没有更新/删除 API。营销智能体没有审核身份或权限，无法编辑或删除反馈。

## 7. 内部 UX

内容详情页提供渠道专用预览：

- 网站文章：标题、摘要、章节、CTA、引用。
- TikTok / Reel：Hook、场景、画面方向、旁白、屏幕文字、CTA，以及适用的 Caption。
- Facebook：标题、正文、CTA、Hashtag、引用。
- 邮件：主题、预览文字、问候、正文、CTA、结尾、引用。

内部评估视图显示结果、证据、提供方/模型、评分、反馈、引用、延迟、Correlation ID、用量/成本可用性和人工编辑距离。它不能发布或模拟发送。

## 8. API 与持久化

- `POST /api/v1/content/assets/{asset_id}/feedback`：幂等准确版本反馈；需要 `content:review`。
- `GET /api/v1/content/assets/{asset_id}/evaluation`：租户范围内部投影；需要 `content:read`。
- `content_review_feedback`：不可变、受 RLS 保护的反馈。
- `content_generation_runs.validation_summary`：不含隐藏推理的质量投影。

只有准确批准版本是从 AI 生成源版本派生的人工后继版本时，才返回人工编辑距离。响应还会标识 AI 生成版本和人工批准版本。直接批准 AI 版本、批准回滚版本或缺少人工批准时均不返回指标。

固定的 Phase 3.2 业务验收流程和最终 GO 标准在 `marketing-content-business-acceptance.zh-CN.md` 中定义。

## 9. 可选真实提供方验证

常规测试使用 Mock，不产生模型费用。真实提供方运行必须明确触发，每次最多两个案例：

```bash
cd apps/api
MARKETING_CONTENT_PROVIDER=openai \
OPENAI_API_KEY=... \
PYTHONPATH=src .venv/bin/python -m sari_api.marketing_generation_eval \
  --allow-paid-provider --max-cases 2
```

输出比较质量、依据、结构和延迟。当前提供方契约不能可靠返回 Token/成本，因此报告 `not_available_from_current_provider_contract`，不会虚构成本。系统绝不自动运行付费评估。

## 10. 安全边界

租户隔离、强制 RLS、RBAC、准确营销智能体绑定、`public_marketing_v1`、已批准/已发布/已启用公开知识、生产激活 pending，以及禁止 AI 审批、CRM 写入、发布、排期、私有知识和外部动作的规则全部保持不变。

## 11. 建议

**CONDITIONAL GO（有条件通过）。** 平台已经可以进行受控人工业务验收，但尚不能用于生产营销，也不应进入下一项自主或外发能力。

必须完成的改进：

1. Sari Arta 审核人员对每种内容类型至少审核一份英文和一份中文草稿，并记录反馈。
2. 创建人工批准后继版本，使人工编辑距离反映真实工作。
3. 最多运行两个受控 OpenAI 案例，并比较质量、依据、结构和延迟。
4. 检查 74.9 的重复控制评分，并按照已批准品牌指南验证最终语气。

系统不会自动启动后续阶段。
