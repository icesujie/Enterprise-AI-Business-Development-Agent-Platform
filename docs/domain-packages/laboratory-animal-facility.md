# Laboratory Animal Facility / IVC Domain Package

## Status / 状态 / Status

**English:** Phase 2.2 functional demonstration agent. The qualification workflow is active only
for the seeded development tenant. It supports deterministic mock execution and optional OpenAI
Agents SDK execution. Human review is mandatory. Knowledge retrieval and external actions remain
disabled.

**中文：** Phase 2.2 功能演示智能体。资格评估工作流只在预置开发租户中激活，可使用确定性
Mock 模式，也可选择 OpenAI Agents SDK 实模式。结果必须人工审核；知识检索和外部动作仍未启用。

**Bahasa Indonesia:** Agen demo fungsional Phase 2.2. Alur kualifikasi hanya aktif untuk tenant
pengembangan bawaan. Eksekusi mendukung mode mock deterministik dan OpenAI Agents SDK opsional.
Tinjauan manusia wajib; pengambilan pengetahuan dan tindakan eksternal tetap dinonaktifkan.

## Identity

| Item | Value |
|---|---|
| Domain | `laboratory_animal_facility` |
| Agent | `laboratory_animal_facility.ivc_business_development` |
| Display name | IVC Facility Business Development Agent |
| Package version | `1.0.0` |
| Workflow | `ivc_facility_qualification` |
| Input schema | `ivc_qualification_input_v1` |
| Output schema | `ivc_qualification_output_v1` |
| Locales | `en`, `zh-CN`, `id` |
| Development activation | Active |
| Production activation | Not created |
| Knowledge retrieval | Planned, optional, and disabled |
| External tools/actions | None |

## Business qualification workflow / 业务资格评估流程

```text
Select a synthetic case or submit structured project data
→ validate customer, project, technical, budget, and timeline fields
→ create a durable Agent Run
→ execute through the shared Redis Worker
→ return schema-validated A/B/C output in the requested language
→ persist the IVC assessment
→ require a human to approve or reject the exact result
```

The workflow is commercial discovery, not a scientific or facility-design approval. The agent may
summarize evidence and recommend discovery actions. It must not declare regulatory compliance,
scientific suitability, animal-welfare suitability, HVAC performance, price, or delivery dates.

该流程用于商务需求发现，不等同于科研或设施设计审批。智能体可以总结现有信息并建议下一步，但
不得自行认定法规合规性、科研适用性、动物福利适用性、HVAC 性能、价格或交期。

## Qualification input / 资格评估输入

The request is divided into five business sections:

1. `customer_profile`: organization, organization type, country/city, contact role, and decision
   stakeholders.
2. `project`: new facility, expansion, retrofit, replacement, or feasibility project; location;
   project summary.
3. `technical_requirements`: research program/species, planned capacity, rooms and workflows,
   containment/biosafety context, HVAC/environment, design information, validation expectations,
   and lifecycle service scope.
4. `budget_indicators`: indicative budget, currency, funding status, and procurement context.
5. `timeline`: target milestones and current project stage.

All input is validated before the run is queued. The original structured snapshot is saved in
PostgreSQL so a later reviewer can see exactly what the agent evaluated.

## Qualification rubric / 评分规则

| Category | Points | Evidence reviewed |
|---|---:|---|
| Customer profile | 10 | Organization context and responsible contact |
| Project definition | 15 | Project type, location, and defined scope |
| Technical requirements | 35 | Capacity, workflow, biosafety, HVAC, design and validation evidence |
| Budget and procurement | 20 | Budget/currency, funding and procurement path |
| Timeline | 15 | Target milestones and current stage |
| Decision stakeholders | 5 | Owner, scientific, veterinary, facility, engineering and procurement roles |

- Level A: 75–100
- Level B: 45–74.99
- Level C: 0–44.99

Missing data reduces the score and is returned explicitly. The score does not automatically create,
convert, reject, or contact a CRM lead.

## Structured output / 结构化输出

The saved result contains only business-facing fields:

- Qualification score and A/B/C level.
- Localized business summary.
- Six visible qualification factors and their evidence status.
- Missing information.
- Risk flags.
- Recommended next actions.
- Confidence.
- Mandatory expert-review marker and review status.

Hidden chain-of-thought is neither requested nor exposed. Stable schema keys and enum values remain
in English; human-facing text is returned in the requested locale.

## Prompt template / 提示模板

The versioned implementation template is:

`apps/api/src/sari_api/adapters/ivc_qualification_provider.py:IVC_QUALIFICATION_INSTRUCTIONS`

It fixes the rubric and language contract, prohibits invented facts and commitments, requires
qualified review, and allows no tools. OpenAI mode uses `IvcQualificationOutput` as the structured
output schema. Mock mode applies the same business contract deterministically without an API key.

## Synthetic demo cases / 合成演示案例

All names, contacts, locations, amounts, and project descriptions are synthetic.

| Case | Scenario | Mock result |
|---|---|---:|
| `university_animal_facility` | Funded new university mouse/rat facility with mature design evidence | 100 / A |
| `pharmaceutical_research_facility` | Pharmaceutical research expansion with funding under review | 97 / A |
| `laboratory_upgrade` | Early rack-replacement inquiry with major evidence gaps | 44 / C |

The same underlying facts produce English, Chinese, or Bahasa Indonesia business explanations while
the numeric result remains stable.

## API surface

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/ivc/demo-cases?locale=zh-CN` | List localized synthetic cases |
| `GET` | `/api/v1/ivc/demo-cases/{case_key}` | Read a complete structured demo input |
| `POST` | `/api/v1/ivc/qualification-runs` | Queue a demo case or caller-supplied structured project |
| `GET` | `/api/v1/agent-runs/{run_id}` | Poll durable status and result |
| `POST` | `/api/v1/agent-runs/{run_id}/cancellations` | Cancel a queued/running run |
| `GET` | `/api/v1/ivc/qualification-assessments` | List saved IVC assessments |
| `POST` | `/api/v1/ivc/qualification-assessments/{id}/reviews` | Human approve/reject |

Run creation requires `leads:qualify` and an `Idempotency-Key`. The shared runtime supplies bounded
retry, safe failure messages, correlation IDs, structured logging, cancellation, recovery, and audit
events.

## Database changes / 数据库变更

Migration `4a68c3d2f901`:

- Adds tenant-isolated `ivc_qualification_assessments` with score, level, locale, structured factors,
  missing information, risks, next actions, confidence, and human-review fields.
- Forces PostgreSQL Row-Level Security on the new table.
- Marks the IVC domain, agent, and version 1 configuration available/active for development.
- Adds a development-only tenant activation for the seeded workspace.
- Keeps `approved_knowledge_retrieval` optional and planned.
- Leaves the Sari Arta configuration ID, `lead_qualification` key, workflow, tables, and APIs unchanged.

## Knowledge boundary / 知识边界

The domain taxonomy still defines IVC systems, facility workflow, environmental control, biosafety,
installation/validation, lifecycle service, and approved capabilities/cases. These are category
definitions only. There are no approved documents, chunks, embeddings, citations, or retrieval
tools in Phase 2.2.

Production activation requires domain-expert review, approved source governance, AI data-processing
approval, evaluation thresholds, and a separate production activation record.
