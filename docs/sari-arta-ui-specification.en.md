# Sari Arta UI Specification

## Implementation-ready frontend baseline for M6

> Chinese translation: [sari-arta-ui-specification.zh-CN.md](sari-arta-ui-specification.zh-CN.md). This English document is the primary engineering baseline.

**Product:** Enterprise AI Business Development Agent Platform  
**Reference business:** Sari Arta, Indonesia commercial-kitchen engineering  
**Applications:** Public B2B website and internal AI business dashboard  
**Source documents:** `docs/ui-design.en.md`, `docs/design-reference.en.md`  
**Status:** Final UI specification; no frontend implementation  
**Version:** 1.0

## 0. Specification decisions

This document converts the approved UX direction into page, component, state, and responsive contracts suitable for implementation. When it differs from an exploratory option in the source documents, this document is the M6 frontend baseline.

The product uses one Next.js application with two visibly distinct experiences:

1. A public, editorial, proof-led website that creates structured project inquiries.
2. An authenticated, operational workspace that makes the next sales action obvious.

The shared experience principle is:

> Public pages reduce buyer uncertainty. Internal pages reduce sales-team uncertainty.

### 0.1 Non-negotiable product rules

- The public website sells an engineering and delivery capability, not a product catalogue.
- Sari Arta is positioned as **Indonesia Commercial Kitchen Engineering Partner**.
- Claims, cases, metrics, certifications, service areas, partner relationships, warranties, and images must be approved before publication.
- Missing evidence must produce an honest generic capability module or a clearly marked content placeholder in review environments; it must never produce a fabricated case or claim.
- The public primary CTA is `Request Project Consultation`.
- The internal workspace is organized around actionable queues, not decorative analytics.
- AI output is visibly labeled, versioned, reviewable, and never presented as the final commercial decision.
- Manual CRM work remains available when AI is unavailable.
- FastAPI remains the only business API. The frontend never accesses PostgreSQL directly.
- Existing authorization, idempotency, optimistic-concurrency, duplicate-detection, lead-conversion, and stage-transition rules must survive the redesign.
- English is the initial public content language. Layouts and content models must be ready for complete Bahasa Indonesia localization.
- Practical WCAG 2.1 AA is a release requirement.

### 0.2 Experience boundaries

| Concern | Public website | Internal workspace |
|---|---|---|
| Audience | Project owners, operations, facilities, procurement, consultants | Sari Arta owner and sales team |
| Navigation | Solutions, industries, proof, company, consultation | Dashboard, leads, opportunities, follow-up, companies, contacts |
| Density | Spacious and editorial | Compact and operational |
| Primary outcome | Submit a qualified project inquiry | Complete the next valid sales action |
| AI visibility | None | Explicit assessment and run status |
| Indexing | Indexable approved pages | `noindex`, authenticated |
| Evidence | Approved public evidence only | Authorized business records |

---

# 1. Public Website UI Specification

## 1.1 Public shell

### Purpose

Provide consistent navigation, brand presence, language selection, consultation access, metadata, and footer information across all public pages.

### Desktop layout

- Optional 32 px utility bar only when verified contact/service information exists.
- Main header: 72–80 px high, maximum content width 1280 px.
- Logo left; navigation centered/right; locale control and primary CTA at the end.
- Header uses a solid or lightly translucent limestone surface. Do not imitate the reference website’s transparent full-screen hero header.
- Main content uses a 12-column editorial grid with 24 px gutters.
- Standard content width: 1200–1280 px.
- Long-form reading width: 680–760 px.
- Footer uses a dark engineering-ink surface with four information groups.

### Header order

1. Sari Arta identity.
2. `Solutions`.
3. `Industries`.
4. `Projects`.
5. `About Us`.
6. `Contact`.
7. Locale selector.
8. `Request Consultation` primary button.

### Global public components

- `MarketingHeader`.
- `DesktopNavigation`.
- `MobileNavigationDrawer`.
- `LocaleSwitcher`.
- `MarketingFooter`.
- `Breadcrumbs` on inner pages.
- `ConsultationCTA`.
- `MobileConsultationBar`.
- `EvidenceDisclaimer` for preview/review environments only.

### Responsive behavior

- At widths below 1024 px, primary navigation collapses into a drawer.
- The locale control remains visible beside the menu trigger.
- At phone widths, the consultation action is inside the drawer and may also appear as a bottom sticky bar after the visitor passes the hero.
- The sticky action must respect safe-area insets and disappear while the consultation form or footer is in view.
- All navigation targets and controls are at least 44 × 44 CSS pixels.

## 1.2 Home

### Page purpose

Establish Sari Arta as a credible commercial-kitchen engineering partner, let a visitor recognize industry fit, explain the China–Indonesia delivery model, provide evidence, and initiate a project consultation.

### Page layout

- Asymmetric editorial hero followed by alternating light and dark full-width bands.
- Use a 12-column desktop grid.
- Hero copy occupies five columns; approved project/site media occupies seven.
- Primary content alternates between constrained text, process diagrams, and evidence cards.
- Do not use a carousel, autoplay video, fake chat widget, animated counters, or product-category wall.

### Section order

1. **Marketing header**.
2. **Engineering hero**.
3. **Industry-fit strip**.
4. **Complete-kitchen problem statement**.
5. **End-to-end capability rail**.
6. **China–Indonesia delivery model**.
7. **Featured project evidence**.
8. **Industry solution previews**.
9. **Project delivery process**.
10. **Technical confidence evidence**.
11. **Project-readiness checklist**.
12. **Consultation CTA band**.
13. **FAQ**.
14. **Footer**.

### Section requirements

#### Engineering hero

- Eyebrow: approved form of `Indonesia Commercial Kitchen Engineering Partner`.
- Outcome-led H1, no unsupported superlatives.
- One short supporting paragraph explaining engineering, manufacturing coordination, and Indonesia installation.
- One primary CTA: `Request Project Consultation`.
- One secondary text link: `Explore Our Delivery Approach`.
- One approved project, installation, factory, or engineering visual.
- Optional three-item proof rail only when every item is verifiable.

#### Industry-fit strip

- Four equal choices: School, Hospital, Factory & Corporate Cafeteria, Central Kitchen.
- Each choice links to its industry route and includes a one-line operational need.
- No client logos unless publication permission exists.

#### Complete-kitchen problem statement

- Explain that capacity, workflow, hygiene, utilities, equipment, installation, and service form one operating system.
- Include a simple annotated workflow diagram with a text alternative.

#### End-to-end capability rail

Show six steps:

1. Requirement discovery.
2. Workflow and capacity planning.
3. Equipment specification and engineering.
4. Manufacturing and quality coordination.
5. Indonesia logistics and installation.
6. Commissioning, training, and after-sales support.

Each step needs a short scope statement and a link to a relevant solution.

#### China–Indonesia delivery model

- Display two responsibility columns joined by shared quality gates.
- Explain what is handled with China manufacturing resources and what is delivered locally in Indonesia.
- Include ownership at engineering review, QC, logistics handover, site readiness, installation, and commissioning.
- Provide a linear text/table equivalent for accessibility and mobile.

#### Featured projects

- Show two or three approved `CaseStudyCard` items.
- Each card: industry, location, challenge, Sari Arta scope, and verified result.
- If fewer than two approved cases exist, replace the grid with `Typical Project Approach`; do not simulate cases.

#### Technical confidence

- Use document-style evidence cards for approved engineering deliverables, quality checkpoints, installation scope, or service method.
- Never use a generic badge wall.

#### Project readiness

- Show a practical checklist: facility type, location, capacity, menu/operation, floor-plan status, utilities, target date, known scope.
- Explicitly say incomplete information is acceptable.

### Component list

- `HeroProject`.
- `ProofRail`.
- `IndustryFitStrip`.
- `OperationalSystemDiagram`.
- `CapabilityRail`.
- `DeliveryResponsibilityMap`.
- `CaseStudyCard`.
- `IndustryPreviewCard`.
- `ProcessSteps`.
- `EvidenceCard`.
- `ReadinessChecklist`.
- `ConsultationCTA`.
- `FAQAccordion`.

### Required content

- Approved positioning and company description.
- One hero image with origin, permission, crop, caption, and alt text.
- Six capability descriptions.
- China/Indonesia responsibility wording.
- Two approved cases or approved fallback process content.
- Approved technical evidence.
- Service-area wording.
- Five to seven FAQs.
- Approved contact and privacy links.

### CTA placement

- Header: persistent primary CTA.
- Hero: primary plus one secondary link.
- After featured projects: contextual text link.
- Final CTA band: primary CTA plus readiness reassurance.
- Mobile: optional sticky CTA after hero.

### Responsive behavior

- Hero becomes copy first, image second at widths below 900 px.
- Proof rail wraps to two columns on tablet and one column on phone.
- Industry strip becomes a 2 × 2 grid, then stacked cards below 480 px.
- Capability rail and delivery map become numbered vertical sequences.
- Featured projects stack; do not hide essential cards behind a carousel.
- H1 targets 44–64 px desktop and 36–44 px phone with controlled line length.
- Decorative technical annotations are reduced or removed when they compete with content.

## 1.3 Solutions

### Page purpose

Explain Sari Arta’s responsibility across the kitchen-project lifecycle and help buyers understand inputs, deliverables, interfaces, and boundaries before a consultation.

### Page layout

- Index page: editorial introduction followed by lifecycle and capability-card grid.
- Detail template: 8/4 desktop split for main method content and a sticky contextual summary/CTA rail.
- Solution detail routes use the same template and typed content model.

### Section order — index

1. Header and breadcrumbs.
2. Solutions hero.
3. Project-lifecycle overview.
4. Capability cards.
5. Responsibility matrix.
6. Typical inputs and deliverables.
7. Related project evidence.
8. Consultation CTA.
9. Footer.

### Section order — detail template

1. Breadcrumbs and solution hero.
2. Buyer problem.
3. Sari Arta scope.
4. Required customer inputs.
5. Working method/process.
6. Expected deliverables.
7. Responsibility and project interfaces.
8. Verified evidence.
9. Limitations or exclusions where relevant.
10. Related industries and cases.
11. Contextual consultation CTA.

### Required solution content

The initial content model supports:

- Commercial kitchen planning and design.
- Equipment engineering and manufacturing coordination.
- Logistics and site-readiness coordination.
- Installation and commissioning.
- Training and approved after-sales support.

Each solution needs:

- Slug, title, summary, and buyer problem.
- Scope statements.
- Required inputs.
- Process steps.
- Deliverables.
- Responsibility boundaries.
- Approved evidence references.
- Related industry/case links.
- SEO title, description, locale, and review metadata.

### Component list

- `InnerPageHero`.
- `LifecycleDiagram`.
- `CapabilityCard`.
- `ResponsibilityMatrix`.
- `InputChecklist`.
- `DeliverablesList`.
- `ProcessSteps`.
- `EvidenceCard`.
- `RelatedContentGrid`.
- `ContextualConsultationCard`.

### CTA placement

- Index hero: `Discuss Your Project`.
- Each capability card: `View Capability`.
- Detail side rail: persistent desktop consultation card after the first viewport.
- Detail conclusion: `Review This Capability for Your Project` with the solution slug preserved in attribution.

### Responsive behavior

- Index capability cards: three columns desktop, two tablet, one phone.
- Lifecycle diagram becomes a vertical ordered list below 768 px.
- Detail side rail moves below the main introduction on tablet/phone and is no longer sticky.
- Responsibility tables allow horizontal scrolling only as a last resort; preferred phone view is labeled responsibility cards.
- Long technical terms wrap without truncation.

## 1.4 Industries

### Page purpose

Let buyers recognize Sari Arta’s understanding of their operating environment before discussing equipment or pricing.

### Page layout

- Index page uses four large industry cards and shared engineering principles.
- Industry detail template uses an editorial hero, operational-flow diagram, content bands, and relevant evidence.
- Industry pages are problem-led, not duplicated solution pages.

### Section order — index

1. Header and breadcrumbs.
2. Industries hero.
3. Four industry cards.
4. Shared engineering principles.
5. Sector evidence overview.
6. Consultation CTA.
7. Footer.

### Section order — detail template

1. Breadcrumbs and industry hero.
2. Operating context and stakeholders.
3. Operational challenges.
4. Typical kitchen zones/workflow.
5. Planning requirements checklist.
6. Relevant Sari Arta capabilities.
7. Approved project evidence.
8. Delivery/process summary.
9. Industry-specific consultation CTA.

### Required industry content

#### School kitchens

- Meal volume and service windows.
- Safe, maintainable workflow considerations.
- Receiving, storage, preparation, cooking, serving, and washing flow.
- Training and maintenance needs.

#### Hospital kitchen solutions

- Hygiene and separation considerations.
- Diet/meal-production workflow.
- Distribution, washing, reliability, and cleaning considerations.
- No clinical or regulatory guarantee without validated review.

#### Factory and corporate cafeterias

- Peak-shift throughput.
- Bulk preparation and service.
- Staff flow, durability, cleaning, maintenance, and expansion.

#### Central kitchens / commissaries

- High-volume production flow.
- Receiving, storage, preparation, cooking, chilling/holding, and dispatch.
- Repeatability, logistics, utilities, and expansion.

Each industry object also requires a slug, intro, stakeholders, challenges, requirement checklist, related solution IDs, approved case IDs, SEO metadata, and content-review metadata.

### Component list

- `IndustryCard`.
- `IndustryHero`.
- `StakeholderList`.
- `OperationalFlowDiagram`.
- `RequirementChecklist`.
- `RelatedSolutionCard`.
- `SectorEvidenceModule`.
- `IndustryConsultationCTA`.

### CTA placement

- Index hero: general consultation CTA.
- Industry cards: `Explore [Industry] Kitchens`.
- Detail page after requirements: relevant capability links.
- Detail conclusion: industry-specific CTA with `industry=<slug>` attribution.

### Responsive behavior

- Four-card index: 2 × 2 desktop/tablet and stacked phone.
- Operational-flow diagram becomes a labeled vertical flow below 768 px.
- Requirement lists use single column on phone.
- Contextual CTA wording remains visible; do not reduce it to an unexplained icon.

## 1.5 Projects / Case Studies

### Page purpose

Prove delivery capability with factual, permissioned project narratives and help a prospect find a comparable project.

### Page layout

- Index: featured case plus filterable card grid when enough cases exist.
- Detail: narrow evidence-led narrative with full-width image moments and a project fact rail.
- Case facts must be visually distinct from editorial interpretation.

### Section order — index

1. Header and breadcrumbs.
2. Projects hero.
3. Optional filters.
4. Featured approved case.
5. Case-study grid.
6. Delivery capability summary.
7. Consultation CTA.
8. Footer.

Filters appear only when there are enough approved cases to make them useful. Initial filters are industry, project type, and location.

### Section order — case detail

1. Breadcrumbs.
2. Case header and verified fact strip.
3. Project context.
4. Challenge and constraints.
5. Requirements summary.
6. Sari Arta responsibility.
7. Engineering and delivery approach.
8. China manufacturing and Indonesia installation roles when applicable.
9. Captioned project gallery.
10. Verified result.
11. Related solution and industry.
12. `Discuss a Similar Project` CTA.

### Component list

- `ProjectFilters`.
- `FeaturedCase`.
- `CaseStudyCard`.
- `ProjectFactStrip`.
- `CaseNarrativeSection`.
- `ResponsibilityMap`.
- `CaptionedGallery`.
- `RelatedContentGrid`.
- `CaseConsultationCTA`.

### Required content

- Customer type or approved customer name.
- Industry and location.
- Challenge and constraints.
- Verified capacity/scale only when approved.
- Sari Arta scope and boundaries.
- Delivery approach.
- Verified result.
- Permissioned images, captions, alt text, and display order.
- Publication permission and review date.

### CTA placement

- Index hero: consultation CTA.
- Each card: `View Project`.
- Case conclusion: `Discuss a Similar Project`, preserving `case_study=<slug>`.
- No pop-up form over the gallery.

### Responsive behavior

- Featured case changes from 7/5 split to stacked.
- Card grid: three columns desktop, two tablet, one phone.
- Filters collapse into an accessible disclosure/drawer on phone.
- Fact strip wraps into labeled pairs; no compressed table.
- Gallery uses stable responsive images. Swipe is optional, but every image remains reachable through buttons and keyboard.

## 1.6 About Us

### Page purpose

Explain Sari Arta’s identity, delivery philosophy, team responsibility, China–Indonesia operating model, and accountable local presence.

### Page layout

- Editorial company story with an operating-model diagram and evidence modules.
- Avoid a generic corporate timeline dominating the page.
- Use real team, office, project, and approved manufacturing imagery.

### Section order

1. Header and breadcrumbs.
2. Company-position hero.
3. Company story and verified milestones.
4. China–Indonesia operating model.
5. Team and responsibility profiles.
6. Quality and accountability process.
7. Approved credentials/partners/facilities.
8. Service-region explanation.
9. Project consultation CTA.
10. Footer.

### Component list

- `CompanyHero`.
- `CompanyTimeline`.
- `OperatingModelDiagram`.
- `TeamRoleCard`.
- `QualityGateSteps`.
- `CredentialCard`.
- `ServiceRegionMap` with text alternative.
- `ConsultationCTA`.

### Required content

- Legal and approved public company names.
- Approved company description and history.
- Verified milestones.
- Team roles and approved biographies/images.
- Accurate manufacturing-partner relationship wording.
- Quality-control and site-delivery responsibilities.
- Approved service regions.
- Credentials and partner logos with permission.

### CTA placement

- Hero secondary link: `See How We Deliver`.
- After operating model: relevant solution link.
- Final band: `Request Project Consultation`.

### Responsive behavior

- Timeline becomes a vertical chronological list.
- Team cards use two columns tablet and one phone.
- Operating model and service map include stacked text equivalents.
- Large decorative maps are removed when they reduce readability.

## 1.7 Contact / Request Consultation

### Page purpose

Convert a serious visitor into a structured lead, accept incomplete project information, explain the next human step, and protect privacy.

### Page layout

- `/contact` introduces contact choices and routes the visitor to the project brief.
- `/contact/request-consultation` contains the primary four-step form.
- Desktop form uses an 8/4 grid: form left, readiness/help card right.
- The right rail is sticky only when it does not obscure error navigation or consent.
- `/contact/request-consultation/received` is a separate private confirmation view.

### Section order — contact page

1. Header and breadcrumbs.
2. Contact hero.
3. Primary consultation route.
4. Approved company contact details.
5. Consultation expectations and privacy summary.
6. FAQ.
7. Footer.

### Section order — request consultation

1. Minimal header and breadcrumbs.
2. Low-friction reassurance.
3. Progress indicator.
4. Current form step.
5. Back/continue controls.
6. Readiness/help rail.
7. Review and consent.
8. Submission status.
9. Minimal footer/privacy links.

### Four-step form contract

#### Step 1 — Organization and contact

- Full name — required.
- Work email — required for the MVP unless the approved API permits phone-only contact.
- Phone/WhatsApp — optional or required according to final API contract; accept international format.
- Organization — required.
- Role/job title — optional in the short MVP form; required only after API support.
- Preferred language — English/Bahasa Indonesia.

#### Step 2 — Project context

- Industry — school, hospital, factory/corporate cafeteria, central kitchen, other.
- Project type — new kitchen, renovation, expansion, equipment replacement.
- Country — required.
- City — required.
- Estimated capacity/meals per period — optional, with unit/context.
- Target opening/timeline — optional.

#### Step 3 — Scope and readiness

- Project description — required.
- Known service/equipment scope — optional.
- Floor-plan status — available, in progress, not available.
- Budget range — optional and paired with currency if enabled.
- Preferred contact method — email, phone, WhatsApp, with no automatic outreach implied.

File upload is not part of Phase 1.

#### Step 4 — Review and consent

- Readable summary grouped by earlier steps.
- Edit links return to the selected step without losing safe values.
- Contact-purpose consent — required.
- Marketing consent — separate and optional.
- Privacy-policy link/version.
- Single submit action.

### Form interaction requirements

- Validate on blur where helpful and on continue/submit.
- Show field errors plus a focusable error summary.
- Preserve safe input after correctable validation and network errors.
- Do not save or claim resumable drafts in Phase 1.
- Disable duplicate clicks during submission and send an idempotency key.
- Map server errors to fields or a safe page-level error with correlation ID.
- Do not reveal duplicate detection, lead ID, owner, AI score, or internal workflow status.
- Store page/industry/solution/case and UTM attribution through the supported API fields.
- Do not collect fields that the API discards. If the API is not expanded before M6, use the supported short form.

### Confirmation-page requirements

- Success heading.
- Non-sensitive submission reference.
- Approved explanation of the next human step.
- Project-readiness checklist.
- Link back to relevant industry/solution or home.
- No unsupported response-time, price, design, or delivery promise.
- Confirmation route must not expose inquiry data in the URL and should be `noindex`.

### Required content

- Approved company name, office/service contact details, and contact ownership.
- Approved explanation of who should request a consultation and what happens next.
- Project-readiness guidance.
- API-supported field labels, options, help text, and validation messages in each released locale.
- Privacy notice, consent wording, policy version, and retention/contact-purpose explanation.
- Approved alternate contact route, if enabled.
- Confirmation and error copy that makes no unsupported response, price, design, or delivery commitment.

### Component list

- `ContactMethodCard`.
- `ProjectBriefStepper`.
- `FormProgress`.
- `FormSection`.
- `CountryField`.
- `InternationalPhoneField`.
- `CapacityField`.
- `MoneyField` when enabled.
- `ConsentFields`.
- `ErrorSummary`.
- `SubmissionStatus`.
- `ReadinessChecklist`.
- `ConfirmationPanel`.

### CTA placement

- Contact hero: `Start Your Project Brief`.
- Form: one state-specific button (`Continue`, then `Submit Project Brief`).
- Alternate contact is secondary and appears after the primary route.
- Do not add competing sales pop-ups.

### Responsive behavior

- Form becomes one column below 900 px.
- Help rail moves above Step 1 as a compact disclosure or below the form.
- Field pairs stack below 640 px.
- Progress uses short step labels and exposes full accessible names.
- Mobile sticky global CTA is disabled on form and confirmation routes.
- Form controls use appropriate mobile input modes without forcing local phone/date formats.

---

# 2. Internal AI Dashboard UI Specification

## 2.1 Workspace shell and dashboard layout

### Purpose

Provide a stable authenticated frame and make the highest-priority next sales actions visible immediately after sign-in.

### Desktop shell

- Fixed left navigation: 248 px.
- Compact top bar: 64 px.
- Main content padding: 24–32 px.
- Reading pages use a maximum width around 1280 px.
- Table and pipeline pages may expand to the available viewport.
- Navigation order: Dashboard, Leads, Opportunities, Follow-up, Companies, Contacts.
- Administration is permission-gated and anchored at the bottom.
- `Knowledge` is hidden until Phase 2 is enabled.
- Active route uses shape, text weight, and contrast; color alone is insufficient.

### Top bar

- Workspace label.
- `Create` action for lead, company, contact, or task where supported.
- Attention count derived from actionable queues, not a new notification center.
- User menu with language, profile, and logout.
- Global search is Phase 2 unless an existing endpoint can support a safe, bounded implementation.

### Dashboard section order

1. Page header with greeting/date and `Create Lead`.
2. Four actionable metric cards.
3. Attention queue.
4. Opportunity stage summary.
5. My next tasks.
6. Recent meaningful activity.

### Metric cards

- New or unassigned leads.
- AI assessments awaiting review.
- Overdue tasks.
- Open opportunity value.

Every card links to the corresponding filtered list. Currency totals remain separated by currency; never display a misleading combined amount.

### Attention queue priority

1. Urgent unassigned lead.
2. Overdue follow-up.
3. Pending AI review.
4. Qualified lead not converted.
5. Open opportunity without recent activity.

The ordering is deterministic in Phase 1. AI does not decide queue priority.

### Components

- `WorkspaceShell`.
- `WorkspaceSidebar`.
- `WorkspaceTopbar`.
- `PageHeader`.
- `MetricCard`.
- `AttentionQueue` and `AttentionRow`.
- `StageSummary`.
- `TaskList`.
- `ActivityTimeline`.
- Shared loading, empty, error, and permission states.

### Responsive behavior

- Desktop: fixed sidebar and two-column dashboard content.
- Tablet: collapsible navigation drawer; metrics use a 2 × 2 grid; lower sections stack as needed.
- Phone: drawer or bottom navigation prioritizing Dashboard, Leads, Opportunities, Follow-up; metric cards use two columns or one at 360 px; queues become cards.
- Phone supports quick review and follow-up, not dense analytics.

## 2.2 Lead management page

### Purpose

Operate a prioritized, searchable lead work queue and reach the correct record or creation action quickly.

### Layout and section order

1. Page header and `Create Lead`.
2. Saved/simple view tabs: My Leads, Unassigned, Needs Review, Qualified, All.
3. Search and filters.
4. Active filter chips and result count.
5. Lead table or responsive cards.
6. Cursor pagination.

### Desktop table columns

- Priority.
- Customer/project summary.
- Company.
- Status.
- AI score and review marker.
- Owner.
- Next task/due date.
- Created or last meaningful activity.

Sorting is offered only where the FastAPI contract supports it. Filters and pagination are stored in the URL.

### Filters

- Search.
- Status.
- Priority.
- Owner.
- Source.
- Created-date range when supported.

### Creation behavior

- Use a dedicated `/leads/new` page for Phase 1. This is simpler and more accessible than placing a full form above the list.
- On successful creation, navigate to the new lead detail.
- On conflict/duplicate warning, show the safe matching workflow defined by the API.

### Required states

- Loading skeleton with stable row geometry.
- First-use empty state with create and public-inquiry explanation.
- Filtered empty state with visible filters and `Clear Filters`.
- Safe error state with retry and correlation ID.
- Authorization state without leaking record existence.

### Responsive behavior

- Tablet hides low-priority columns before switching to cards.
- Phone cards show project, company, status, priority, owner, AI marker, and next due action.
- Filters open in a drawer on phone; active filters remain visible as removable chips.
- Row/card remains keyboard accessible and contains an explicit `View Lead` link.

## 2.3 Lead detail page

### Purpose

Create one decision surface for verifying project facts, reviewing AI qualification, scheduling follow-up, and converting a qualified lead.

### Layout

- Persistent `RecordSummary` header.
- Tabs represented in the URL: Overview, Qualification, Follow-up, Activity.
- Overview uses an 8/4 main/side-rail grid.
- Other tabs may use full reading width.

### Header content

- Project/inquiry summary.
- Company and primary contact.
- Status, priority, owner.
- Project location.
- Latest AI score/tier when available.
- One primary action chosen from lead state.
- Secondary actions in an overflow menu.

### State-driven primary action

| Lead state | Primary action |
|---|---|
| New | Assign and Start Qualification |
| Qualifying | Complete Missing Information or Run AI |
| AI awaiting review | Review Qualification |
| Qualified | Convert to Opportunity |
| Converted | Open Linked Opportunity |
| Disqualified | View Decision Record |

### Overview tab

Section order:

1. Next-action callout.
2. Project facts grouped by operation, location, capacity, scope, timeline, and budget/readiness.
3. Organization and contact summary.
4. Missing-information checklist.
5. Side rail with owner, status, priority, contact methods, and next task.

Editing occurs in grouped sections with explicit save/cancel. Do not switch the entire page into edit mode.

### Qualification tab

Section order:

1. Current AI assessment.
2. Human review controls.
3. Run status/details.
4. Assessment version history.

### Follow-up tab

Section order:

1. Next task.
2. Create task or note.
3. Open tasks.
4. Completed tasks.
5. Follow-up notes.

### Activity tab

- Append-only timeline grouped by date.
- Show business events, actor, timestamp, and concise change summary.
- Hide low-level technical events from ordinary users.

### Mutation behavior

- Await server confirmation before updating displayed canonical state.
- Send record version/`If-Match` for concurrency-sensitive updates.
- Show a conflict dialog with reload and safe preservation of unsaved text where possible.
- Conversion requires explicit confirmation and idempotency protection.
- Converted lead links to the specific opportunity, not the general list.

### Responsive behavior

- Tablet moves side rail below the summary or into a contextual drawer.
- Phone tabs scroll or use an accessible select without hiding routes.
- Primary action may use a safe sticky action bar.
- Facts become stacked definition groups.
- Long notes and activity data wrap; identifiers are not the primary display.

## 2.4 AI qualification display

### Purpose

Show a bounded, understandable AI recommendation with evidence gaps and human control.

### Display hierarchy

#### Layer 1 — Decision summary

- `AI-generated assessment` label.
- Score as an exact value such as `82 / 100`.
- Tier: Hot, Warm, or Cold.
- Confidence: High, Medium, or Low with explanatory text.
- Review status: Pending, Accepted, Rejected, or Superseded.
- Freshness timestamp.

Use a restrained horizontal score bar. Do not use a circular gauge or “magic” visual language.

#### Layer 2 — Qualification dimensions

- Need and project fit — 35%.
- Timeline — 25%.
- Budget — 20%.
- Authority — 20%.

Each dimension displays its contribution/status, concise evidence from saved fields, and `Unknown` when evidence is missing.

#### Layer 3 — Actionable result

- Need summary.
- Recommended next action.
- Missing-information checklist.
- No automatic task creation in Phase 1 unless the user confirms and the API supports it.

#### Layer 4 — Human review

- `Accept Assessment`.
- `Reject Assessment` with optional/required reason according to the current contract.
- `Run Again` creates a new version and preserves history.
- Explain that acceptance does not automatically qualify, convert, price, or contact the lead.

### Run-state behavior

| State | Required UI |
|---|---|
| Not run | Explain purpose and show `Run Qualification` |
| Queued | Compact progress, safe navigation-away message |
| Running | Safe stage and elapsed time; never expose hidden reasoning |
| Succeeded | Structured result and review controls |
| Failed | Safe reason, correlation ID, retry when eligible, manual fallback |
| Cancelled | Neutral terminal state with rerun option |

### Components

- `QualificationCard`.
- `AISourceLabel`.
- `ScoreBar`.
- `ConfidenceBadge`.
- `QualificationDimensionRow`.
- `MissingInformationList`.
- `AgentRunStatus`.
- `AssessmentReviewActions`.
- `AssessmentHistory`.

### Accessibility and responsive behavior

- Score meaning is available as text, not color/width alone.
- Status changes use a polite live region.
- Review buttons remain adjacent to the content being reviewed.
- On phone, dimensions stack and actions become full-width without covering evidence.

## 2.5 Project pipeline

### Purpose

Show current opportunities by valid sales stage, identify stalled work, and allow controlled stage progression.

### Views

- `Pipeline` view for visual stage distribution.
- `List` view for scanning, filtering, and accessibility.
- Both views use the same URL-based filter state.

### Pipeline layout

- Open columns: Discovery, Requirements Confirmed, Proposal, Negotiation.
- Won and Lost are terminal filters or compact closed columns.
- Column header shows count and values separated by currency.
- Card fields: opportunity, company, owner, value/currency, probability, expected close, next task, inactivity warning.
- Phase 1 uses explicit `Move Stage` actions, not drag-and-drop.

### Opportunity detail

Header:

- Opportunity and company.
- Stage and status.
- Owner.
- Value/currency.
- Probability.
- Expected close.
- Source lead link.

Tabs:

1. Overview.
2. Follow-up.
3. Activity.
4. Proposal — Phase 1 displays stage/readiness information only; no proposal generator.

### Stage interaction

- Display current progress in `StageStepper`.
- `Move Stage` offers only server-approved valid transitions.
- Wait for server confirmation and send record version.
- `Mark Won` and `Mark Lost` require confirmation.
- `Mark Lost` requires a reason.
- Conflicts offer reload rather than silently overwriting newer state.

### Components

- `PipelineToolbar`.
- `PipelineColumn`.
- `OpportunityCard`.
- `OpportunityTable`.
- `StageStepper`.
- `MoveStageDialog`.
- `CloseOpportunityDialog`.
- `InactivityWarning`.

### Responsive behavior

- Desktop shows horizontally arranged open-stage columns.
- Tablet may horizontally scroll by stage with a persistent stage selector.
- Phone shows one selected stage at a time and makes List view easy to reach.
- Opportunity cards retain readable width; never compress six columns into the viewport.
- Every stage action has a keyboard-accessible alternative.

## 2.6 Follow-up workflow

### Purpose

Create a unified action queue for tasks and contextual follow-up, ensuring leads and opportunities do not lose their next step.

### Page layout and order

1. Page header with `Create Task`.
2. View tabs: Overdue, Today, Upcoming, Completed, All.
3. Optional assignee/related-record filters.
4. Task queue.
5. Records-without-next-task exception queue when supported.

### Task row fields

- Due date/time in the user’s locale.
- Priority.
- Task title.
- Related lead, opportunity, or company.
- Assignee.
- Status.
- Quick `Start` or `Complete` action when valid.

### Workflow behavior

- Task creation from a record pre-fills the related record and current owner where appropriate.
- All quick changes wait for the server.
- Dates are entered/displayed in the user’s timezone and stored by the API in UTC.
- Overdue is derived from deterministic time/status rules.
- Completing a task may offer `Create Next Task`, but does not create one automatically.
- AI recommendations never create or send follow-up without explicit human action.

### Components

- `FollowUpTabs`.
- `TaskFilters`.
- `TaskRow`.
- `TaskCard`.
- `TaskForm`.
- `QuickCompleteButton`.
- `NoNextTaskQueue`.

### Responsive behavior

- Desktop uses a compact task list grouped by due date.
- Tablet reduces secondary fields.
- Phone uses cards with due time, title, relation, and one valid action.
- Task editor is a full page or full-height drawer on phone, never a cramped modal.

## 2.7 Internal shared states

Every internal page must implement:

- Auth/session loading.
- Data loading.
- First-use empty.
- Filtered empty where relevant.
- Permission denied without data leakage.
- Recoverable API error with retry and correlation ID.
- Validation error.
- Mutation pending.
- Success feedback.
- Optimistic-concurrency conflict where relevant.
- AI-provider unavailable without blocking manual CRM.

Use toasts only for short confirmations. Persistent or consequential errors remain inline near the affected content.

---

# 3. Frontend Architecture Recommendation

## 3.1 Next.js route structure

Use one App Router application with separate route groups and layouts. Route groups do not appear in URLs.

```text
apps/web/src/app/
├── (marketing)/
│   ├── layout.tsx
│   ├── page.tsx                              # /
│   ├── solutions/
│   │   ├── page.tsx                         # /solutions
│   │   └── [slug]/page.tsx                  # /solutions/:slug
│   ├── industries/
│   │   ├── page.tsx                         # /industries
│   │   └── [slug]/page.tsx                  # /industries/:slug
│   ├── projects/
│   │   ├── page.tsx                         # /projects
│   │   └── [slug]/page.tsx                  # /projects/:slug
│   ├── about/page.tsx                       # /about
│   ├── contact/
│   │   ├── page.tsx                         # /contact
│   │   └── request-consultation/
│   │       ├── page.tsx                     # /contact/request-consultation
│   │       └── received/page.tsx            # confirmation
│   └── privacy/page.tsx                     # /privacy
├── (auth)/
│   └── login/page.tsx                       # /login
├── (workspace)/
│   ├── layout.tsx
│   ├── dashboard/page.tsx                   # /dashboard
│   ├── leads/
│   │   ├── page.tsx                         # /leads
│   │   ├── new/page.tsx                     # /leads/new
│   │   └── [id]/page.tsx                    # tab via ?tab=
│   ├── opportunities/
│   │   ├── page.tsx                         # /opportunities
│   │   └── [id]/page.tsx
│   ├── follow-up/page.tsx                   # /follow-up
│   ├── companies/
│   │   ├── page.tsx
│   │   └── [id]/page.tsx
│   ├── contacts/
│   │   ├── page.tsx
│   │   └── [id]/page.tsx
│   └── admin/page.tsx
├── error.tsx
├── not-found.tsx
├── globals.css
└── layout.tsx
```

### Compatibility routes

- Redirect existing `/organizations` to `/companies` after the company route is implemented.
- Redirect existing `/tasks` to `/follow-up` after the unified page is implemented.
- Redirect existing `/inquiry` to `/contact/request-consultation` only after the new form supports the existing public lead contract.
- Preserve query parameters needed for filters and attribution during redirects.
- Do not remove old routes in the same release that introduces the replacement unless tests cover inbound links.

### Route-state conventions

- List filters, search, view, cursor, and pipeline stage live in query parameters.
- Lead/opportunity detail tab uses `?tab=overview|qualification|follow-up|activity` for the MVP.
- Invalid query values fall back safely and do not trigger server errors.
- Confirmation state is not encoded as PII in the URL.

## 3.2 Component and module structure

```text
apps/web/src/
├── components/
│   ├── ui/                  # owned primitives
│   ├── feedback/            # errors, empty, skeleton, status
│   ├── forms/               # shared field and validation patterns
│   ├── marketing/           # public editorial modules
│   └── workspace/           # shell, tables, business status patterns
├── features/
│   ├── dashboard/
│   ├── leads/
│   ├── qualification/
│   ├── opportunities/
│   ├── follow-up/
│   ├── companies/
│   ├── contacts/
│   └── inquiry/
├── content/
│   ├── solutions/
│   ├── industries/
│   ├── projects/
│   └── shared/
├── lib/
│   ├── api/
│   ├── auth/
│   ├── format/
│   ├── i18n/
│   └── validation/
└── styles/
    └── tokens.css
```

### Ownership rules

- `components/ui` knows no business status codes or API shapes.
- `features` owns business mapping, server actions/queries, feature schemas, and composed components.
- Route files compose features and metadata; they do not contain large UI implementations.
- Public content begins as typed, repository-managed data. A CMS is not part of Phase 1.
- API response types remain separate from view models; features map snake_case contracts into display-ready structures.
- Server data is not copied into a global client store.

## 3.3 Rendering and data strategy

- Use React Server Components for public pages, initial authenticated reads, and metadata.
- Use client components only for disclosures, filters, dialogs, progressive forms, async run refresh, and stage interaction.
- FastAPI is called through a single server-aware API client that preserves session, correlation IDs, ETags, and structured errors.
- Use Server Actions only as a thin UI transport when they call the FastAPI boundary; do not recreate business rules in Next.js.
- Keep canonical filters and selected tabs in the URL.
- Use time-bound polling for queued/running AI jobs in Phase 1; stop on terminal state, navigation, or visibility loss. Do not add WebSockets solely for M6.
- Mutations display pending state and wait for canonical server results.
- Generate or maintain TypeScript API types from FastAPI OpenAPI. Do not maintain conflicting hand-written contracts.

## 3.4 UI library recommendation

Use a small repository-owned design system built on the existing Tailwind CSS v4 setup.

### Recommended foundation

- **Tailwind CSS v4:** layout and token-backed utilities already present in the project.
- **CSS custom properties:** semantic color, spacing, radius, typography, elevation, and motion tokens.
- **Radix UI primitives, selectively:** dialog, dropdown menu, popover, tabs, tooltip, and accessible select where native HTML is insufficient.
- **shadcn/ui approach, not a wholesale theme:** use selected source-owned component patterns as implementation scaffolding, then apply the Sari Arta tokens and behavior contracts.
- **Lucide React:** consistent outlined icons; every non-decorative icon receives a label or accessible name.
- **React Hook Form + Zod:** recommended for the multi-step public brief and substantial grouped edit forms, while FastAPI remains authoritative.

Do not install a large opinionated visual framework such as Material UI or Ant Design for M6. It would accelerate generic screens but make the original editorial brand and compact workspace harder to unify.

Dependencies are recommendations only. Their installation occurs during approved M6 implementation and must remain limited to components actually used.

## 3.5 Design system

### Color tokens

| Semantic token | Initial value | Primary use |
|---|---:|---|
| `--color-ink` | `#17201C` | Text, dark surfaces |
| `--color-brand` | `#173A2A` | Primary actions, active navigation |
| `--color-accent` | `#B4512B` | Editorial accent, selected highlights |
| `--color-canvas` | `#F3F1EA` | Public background |
| `--color-surface` | `#FFFFFF` | Cards and workspace surfaces |
| `--color-muted` | `#66716B` | Secondary text |
| `--color-line` | `#D8DED8` | Borders and dividers |
| `--color-info` | `#315F78` | AI and neutral information |
| `--color-success` | `#287052` | Confirmed/success |
| `--color-warning` | `#A76619` | Due/risk |
| `--color-danger` | `#A23A34` | Error/urgent/terminal warning |

Every foreground/background pairing requires contrast verification. AI uses information styling plus a text label, not a separate purple brand.

### Typography

- Public display: Source Serif 4 or an approved equivalent for selected H1/H2 text.
- Interface/body: Inter or an approved equivalent.
- Workspace uses sans serif throughout.
- Tabular numerals for values, scores, dates, and metrics.
- Self-host fonts or use a privacy-appropriate Next.js font strategy.
- Minimum ordinary body size: 16 px public, 14–16 px workspace.
- Avoid uppercase body copy.

### Spacing and layout

- Base unit: 4 px.
- Common spacing: 4, 8, 12, 16, 24, 32, 48, 64, 96.
- Public section padding: 64–112 px desktop, 48–72 px tablet, 40–56 px phone.
- Workspace page gap: 16–24 px.
- Public card radius: 12–16 px; workspace controls/cards: 8–12 px.
- Shadows are restrained; borders and surface contrast carry most hierarchy.

### Control hierarchy

- Primary button: brand green filled.
- Secondary button: surface with border.
- Tertiary action: text/link.
- Destructive action: danger styling and confirmation when consequential.
- One primary action per page context.
- Minimum target size: 44 × 44 px.

### Status patterns

- Status is always text plus semantic color and, where useful, an icon.
- Priority includes a written level.
- AI run status is distinct from business review status.
- Unknown values display `Unknown` or `Not provided`, never a misleading zero.
- Skeletons match final geometry; spinners are reserved for compact controls.

### Motion

- Controls and state transitions: 120–220 ms.
- Respect `prefers-reduced-motion`.
- Avoid parallax, autoplay media, pulsing AI objects, and decorative counters.

## 3.6 Responsive strategy

### Review widths

| Range | Required review |
|---|---|
| 360–479 px | Small phone |
| 480–767 px | Large phone |
| 768–1023 px | Tablet |
| 1024–1439 px | Laptop/desktop |
| 1440 px+ | Large desktop |

### Implementation principles

- Use content-driven container queries or breakpoints rather than device detection.
- Public pages are mobile-first but preserve an editorial desktop composition.
- Workspace is desktop-first for dense editing and pipeline analysis, with phone support for review, notes, tasks, and status changes.
- Tables progressively remove secondary columns, then become semantic cards.
- Pipeline uses one selected stage on phone.
- Diagrams always have linear text/table equivalents.
- Do not hide essential content behind hover.
- Preserve keyboard order when visual order changes.
- Test English and expanded Bahasa strings at every review width.

## 3.7 Accessibility, performance, and quality gates

### Accessibility

- Semantic landmarks and heading order.
- Skip links for both shells.
- Visible focus and full keyboard operation.
- 4.5:1 contrast for ordinary text.
- Proper form labels, field grouping, descriptions, and error summary.
- Dialog focus trapping and return focus.
- Polite live regions for form and AI-run status.
- Text alternatives for charts, maps, and diagrams.
- No status communicated by color alone.

### Public performance

- Server-rendered/indexable core content.
- Responsive images with reserved dimensions.
- Limit client JavaScript and third-party scripts.
- No autoplay hero media.
- Unique metadata, canonical URL, language alternates, and structured data supported by visible content.

### Workspace performance

- Server-render first useful data.
- Cursor-paginate growing lists.
- Cancel or ignore stale searches.
- Do not block CRM views on AI or analytics.
- Poll AI status only while necessary.

### Required test coverage during implementation

- Loading, empty, error, success, pending, disabled, permission, and conflict states.
- Keyboard behavior for navigation, tabs, dialogs, filters, form steps, and stage actions.
- Public form validation, idempotent double-submit, rate limit, safe confirmation, and attribution.
- Dashboard metric-to-filter links.
- Lead review → AI review → conversion path.
- Valid and invalid opportunity stage transitions.
- Responsive screenshots at required widths.
- Public metadata and performance smoke checks.
- Synthetic data only.

---

# 4. MVP Frontend Scope

## 4.1 Phase 1 — Required for demo

Phase 1 demonstrates one coherent story:

```text
Visitor understands Sari Arta
→ submits a project inquiry
→ sales sees the lead
→ AI structures qualification evidence and gaps
→ a human reviews it
→ sales schedules follow-up
→ qualified lead converts to an opportunity
→ opportunity moves through a controlled pipeline
```

### Shared foundation

- Sari Arta semantic tokens, typography, spacing, buttons, form fields, status, feedback, and focus styles.
- Distinct marketing and workspace shells.
- Responsive navigation.
- Loading, empty, error, permission, and conflict patterns.
- English content architecture with localization-ready strings.
- FastAPI client behavior preserving authentication, idempotency, correlation IDs, and concurrency controls.

### Public website

- Home page with approved or honest fallback content.
- Solutions index and at least the two launch-critical details: planning/design and installation/commissioning.
- Industries index plus School, Hospital, Factory/Corporate Cafeteria, and Central Kitchen pages.
- Projects index and approved case details when evidence exists; otherwise a transparent delivery-approach presentation.
- About Us.
- Contact page.
- API-aligned Request Consultation form and private confirmation page.
- Privacy link/notice required by the approved form policy.
- Page metadata, sitemap/robots behavior, responsive images, and basic structured data.

### Internal workspace

- Redesigned authenticated shell.
- Actionable M6 dashboard.
- Lead list, filters, creation, detail tabs, and all existing M3–M5 behavior.
- AI qualification run/result/review experience with manual fallback.
- Follow-up task views and contextual task/note workflow supported by current APIs.
- Opportunity pipeline/list, detail, controlled stage change, and direct source-lead relationship.
- Companies and contacts remain accessible; visual refinement may use the shared patterns without adding new business scope.

### Demo content

- Synthetic school, hospital, corporate cafeteria, and central-kitchen scenarios.
- At least one lead demonstrating missing information and one completed AI assessment.
- At least one converted opportunity in each meaningful open stage.
- No real customer PII, unapproved case claims, or AI-generated fake project evidence.

### Phase 1 exclusions

- File upload.
- Public CMS.
- Global search if no bounded backend support exists.
- Drag-and-drop pipeline.
- Real-time WebSockets.
- Automatic AI qualification on inquiry submission.
- Automatic task creation or customer communication.
- WhatsApp/email/social synchronization.
- Proposal generation.
- Knowledge ingestion or knowledge assistant.
- Multi-agent UI or model selector.
- Advanced analytics and personalization.

## 4.2 Phase 2 — Future enhancement

### Public website

- Full Bahasa Indonesia content after native business review.
- Secure floor-plan/document upload.
- Governed CMS workflow and preview.
- Expanded case library and useful project filters.
- Approved downloadable planning guides.
- Privacy-minimized conversion analytics and experimentation.
- Approved WhatsApp/direct-contact routing.
- Additional insight content based on real search demand.

### Internal workspace

- Knowledge library, document processing/review, and cited knowledge assistant.
- Content generation and proposal-assistant interfaces.
- Secure document preview and upload lifecycle.
- Global cross-entity search.
- Richer opportunity follow-up and proposal artifacts.
- Accessible drag-and-drop only if it adds real value.
- Saved custom views, team workload, and deeper reporting.
- Real-time event updates only when operational need justifies them.
- Additional approved AI providers behind backend policy; no frontend arbitrary-model selector by default.

## 4.3 Recommended M6 implementation order after approval

1. **UI foundation:** tokens, fonts, primitives, feedback states, accessibility baseline.
2. **Application shells:** marketing shell, workspace shell, responsive navigation.
3. **M6 dashboard:** metrics, attention queue, tasks, stage summary, activity.
4. **Lead workflow:** list, filters, new lead, detail tabs, AI assessment, follow-up.
5. **Opportunity workflow:** pipeline/list, detail, guarded stage controls.
6. **Public content pages:** Home, Solutions, Industries, Projects, About, Contact.
7. **Consultation flow:** API-aligned stepper, attribution, consent, confirmation.
8. **Hardening:** responsive, accessibility, metadata, test coverage, performance.

This order keeps the roadmap priority on M6 while producing a complete public-to-internal portfolio demonstration.

## 4.4 Definition of UI-ready

M6 implementation may begin when:

- This specification is approved.
- Current FastAPI contracts and frontend routes are inspected before editing.
- The dashboard aggregate/attention contract is available or its UI sections are explicitly mapped to existing endpoints.
- The consultation form uses only API-supported fields or the API expansion is included in the approved M6 slice.
- Public claims, images, projects, service coverage, contact details, and privacy wording are approved or replaced with non-fabricated review placeholders.
- Any selected new UI dependencies are limited, documented, and installed only during implementation.

No frontend application code is created or modified by this specification.
