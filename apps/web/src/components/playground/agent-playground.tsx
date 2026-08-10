"use client";

import { useState, type FormEvent } from "react";

import {
  getPlaygroundRun,
  startPlaygroundRun,
} from "@/app/(workspace)/agent-playground/actions";
import { Button } from "@/components/ui/button";
import { FieldGroup, TextArea, TextField } from "@/components/ui/form";
import { StatusBadge } from "@/components/ui/status";
import type {
  CommercialKitchenPlaygroundInput,
  IvcPlaygroundInput,
  PlaygroundDomain,
  PlaygroundLocale,
  PlaygroundRequest,
  PlaygroundResult,
  PlaygroundRun,
} from "@/lib/agent-playground";

const commercialSample: CommercialKitchenPlaygroundInput = {
  project_type: "School central kitchen",
  location: "Jakarta, Indonesia",
  capacity: "2,000 meals per day",
  budget: "USD 500,000 indicative",
  timeline: "Target opening Q3 2027",
};

const ivcSample: IvcPlaygroundInput = {
  organization: "Synthetic Nusantara University",
  facility_type: "New laboratory animal facility",
  species_research: "Mouse and rat biomedical research",
  capacity: "2,400 mouse cages and 240 rat cages",
  technical_requirements:
    "Housing, procedure, quarantine, wash, sterilization, HVAC, pressure, exhaust and monitoring scope",
  timeline: "Design freeze Q1 2027; target operation Q1 2028",
};

type Copy = {
  demoNotice: string;
  agentLabel: string;
  kitchenName: string;
  kitchenDescription: string;
  ivcName: string;
  ivcDescription: string;
  language: string;
  inputTitle: string;
  optionalHint: string;
  run: string;
  running: string;
  loadSample: string;
  projectType: string;
  location: string;
  capacity: string;
  budget: string;
  timeline: string;
  organization: string;
  facilityType: string;
  speciesResearch: string;
  technicalRequirements: string;
  resultTitle: string;
  score: string;
  level: string;
  businessSummary: string;
  missingInformation: string;
  risks: string;
  nextActions: string;
  noMissing: string;
  provider: string;
  humanReview: string;
  emptyTitle: string;
  emptyDescription: string;
  failed: string;
  timeout: string;
};

const copyByLocale: Record<PlaygroundLocale, Copy> = {
  en: {
    demoNotice: "Demonstration only · No CRM write · No external action",
    agentLabel: "Select an agent",
    kitchenName: "Commercial Kitchen Agent",
    kitchenDescription: "Institutional kitchen opportunity qualification",
    ivcName: "IVC Facility Business Development Agent",
    ivcDescription: "Laboratory animal facility opportunity qualification",
    language: "Response language",
    inputTitle: "Structured project brief",
    optionalHint:
      "Leave fields blank to see how the agent handles missing evidence.",
    run: "Run qualification",
    running: "Agent is evaluating…",
    loadSample: "Reset sample",
    projectType: "Project type",
    location: "Location",
    capacity: "Capacity",
    budget: "Budget indication",
    timeline: "Timeline",
    organization: "Organization",
    facilityType: "Facility type",
    speciesResearch: "Species / research",
    technicalRequirements: "Technical requirements",
    resultTitle: "Qualification result",
    score: "Score",
    level: "Level",
    businessSummary: "Business summary",
    missingInformation: "Missing information",
    risks: "Risks and review gates",
    nextActions: "Recommended next actions",
    noMissing: "No missing fields detected in this demo brief.",
    provider: "Execution mode",
    humanReview: "AI-generated demo result · Human review required",
    emptyTitle: "Ready for a demonstration",
    emptyDescription:
      "Choose an agent, adjust the sample project, and run qualification.",
    failed: "The Agent Run failed safely.",
    timeout:
      "The run is taking longer than expected. Its durable status remains available.",
  },
  "zh-CN": {
    demoNotice: "仅用于演示 · 不写入 CRM · 不执行外部动作",
    agentLabel: "选择智能体",
    kitchenName: "商用厨房商务拓展智能体",
    kitchenDescription: "评估学校、医院、工厂和中央厨房项目机会",
    ivcName: "IVC 设施商务拓展智能体",
    ivcDescription: "评估实验动物设施与 IVC 项目机会",
    language: "结果语言",
    inputTitle: "结构化项目资料",
    optionalHint: "可以留空部分字段，查看智能体如何识别缺失信息。",
    run: "运行资格评估",
    running: "智能体正在评估…",
    loadSample: "恢复示例",
    projectType: "项目类型",
    location: "项目地点",
    capacity: "计划产能",
    budget: "预算信息",
    timeline: "时间计划",
    organization: "客户机构",
    facilityType: "设施类型",
    speciesResearch: "动物种类 / 研究方向",
    technicalRequirements: "技术需求",
    resultTitle: "资格评估结果",
    score: "评分",
    level: "等级",
    businessSummary: "业务摘要",
    missingInformation: "缺失信息",
    risks: "风险和审核要求",
    nextActions: "建议下一步",
    noMissing: "当前演示资料未发现缺失字段。",
    provider: "运行模式",
    humanReview: "AI 生成的演示结果 · 必须人工审核",
    emptyTitle: "可以开始演示",
    emptyDescription: "请选择智能体、调整示例项目，然后运行资格评估。",
    failed: "智能体运行已安全失败。",
    timeout: "运行时间超过预期，但持久化运行状态仍然保留。",
  },
  id: {
    demoNotice: "Hanya demo · Tidak menulis CRM · Tanpa tindakan eksternal",
    agentLabel: "Pilih agen",
    kitchenName: "Agen Dapur Komersial",
    kitchenDescription: "Kualifikasi peluang dapur institusional",
    ivcName: "Agen Pengembangan Bisnis Fasilitas IVC",
    ivcDescription: "Kualifikasi peluang fasilitas hewan laboratorium",
    language: "Bahasa respons",
    inputTitle: "Ringkasan proyek terstruktur",
    optionalHint:
      "Kosongkan beberapa bidang untuk melihat identifikasi informasi yang belum tersedia.",
    run: "Jalankan kualifikasi",
    running: "Agen sedang mengevaluasi…",
    loadSample: "Atur ulang contoh",
    projectType: "Jenis proyek",
    location: "Lokasi",
    capacity: "Kapasitas",
    budget: "Indikasi anggaran",
    timeline: "Jadwal",
    organization: "Organisasi",
    facilityType: "Jenis fasilitas",
    speciesResearch: "Spesies / riset",
    technicalRequirements: "Kebutuhan teknis",
    resultTitle: "Hasil kualifikasi",
    score: "Skor",
    level: "Level",
    businessSummary: "Ringkasan bisnis",
    missingInformation: "Informasi yang belum tersedia",
    risks: "Risiko dan gerbang tinjauan",
    nextActions: "Langkah berikutnya",
    noMissing: "Tidak ada bidang yang hilang dalam ringkasan demo ini.",
    provider: "Mode eksekusi",
    humanReview: "Hasil demo buatan AI · Tinjauan manusia wajib",
    emptyTitle: "Siap untuk demonstrasi",
    emptyDescription:
      "Pilih agen, sesuaikan contoh proyek, lalu jalankan kualifikasi.",
    failed: "Agent Run gagal dengan aman.",
    timeout:
      "Proses lebih lama dari perkiraan. Status tersimpan tetap tersedia.",
  },
};

export function AgentPlayground() {
  const [domain, setDomain] = useState<PlaygroundDomain>("commercial_kitchen");
  const [locale, setLocale] = useState<PlaygroundLocale>("en");
  const [commercial, setCommercial] = useState(commercialSample);
  const [ivc, setIvc] = useState(ivcSample);
  const [run, setRun] = useState<PlaygroundRun | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const copy = copyByLocale[locale];

  const selectDomain = (nextDomain: PlaygroundDomain) => {
    setDomain(nextDomain);
    setRun(null);
    setError(null);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsRunning(true);
    setError(null);
    setRun(null);
    const request: PlaygroundRequest =
      domain === "commercial_kitchen"
        ? { domain, response_locale: locale, commercial_kitchen: commercial }
        : { domain, response_locale: locale, laboratory_animal_facility: ivc };
    try {
      const started = await startPlaygroundRun(request);
      for (let attempt = 0; attempt < 45; attempt += 1) {
        await delay(attempt === 0 ? 250 : 800);
        const current = await getPlaygroundRun(started.run_id);
        setRun(current);
        if (["succeeded", "failed", "cancelled"].includes(current.status)) {
          if (current.status !== "succeeded") {
            setError(current.error_message || copy.failed);
          }
          return;
        }
      }
      setError(copy.timeout);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : copy.failed);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-[var(--color-info)]/20 bg-[var(--color-info-soft)] px-5 py-4">
        <p className="text-sm font-semibold text-[var(--color-info)]">
          {copy.demoNotice}
        </p>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.72fr)]">
        <form onSubmit={submit} className="card overflow-hidden">
          <div className="border-b border-[var(--color-line)] p-6 sm:p-7">
            <div className="flex flex-wrap items-end justify-between gap-5">
              <div className="min-w-0 flex-1">
                <p className="eyebrow">{copy.agentLabel}</p>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <AgentChoice
                    active={domain === "commercial_kitchen"}
                    badge="CK"
                    title={copy.kitchenName}
                    description={copy.kitchenDescription}
                    onClick={() => selectDomain("commercial_kitchen")}
                  />
                  <AgentChoice
                    active={domain === "laboratory_animal_facility"}
                    badge="IVC"
                    title={copy.ivcName}
                    description={copy.ivcDescription}
                    onClick={() => selectDomain("laboratory_animal_facility")}
                  />
                </div>
              </div>
              <label className="text-xs font-bold uppercase tracking-[0.13em] text-[var(--color-muted)]">
                {copy.language}
                <select
                  value={locale}
                  onChange={(event) => {
                    setLocale(event.target.value as PlaygroundLocale);
                    setRun(null);
                    setError(null);
                  }}
                  className="field mt-2 min-w-40 normal-case tracking-normal"
                  aria-label={copy.language}
                >
                  <option value="en">English</option>
                  <option value="zh-CN">中文</option>
                  <option value="id">Bahasa Indonesia</option>
                </select>
              </label>
            </div>
          </div>

          <div className="p-6 sm:p-7">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold">{copy.inputTitle}</h2>
                <p className="mt-2 text-sm text-[var(--color-muted)]">
                  {copy.optionalHint}
                </p>
              </div>
              <Button
                type="button"
                variant="tertiary"
                onClick={() =>
                  domain === "commercial_kitchen"
                    ? setCommercial(commercialSample)
                    : setIvc(ivcSample)
                }
              >
                {copy.loadSample}
              </Button>
            </div>

            {domain === "commercial_kitchen" ? (
              <CommercialForm
                copy={copy}
                value={commercial}
                onChange={setCommercial}
              />
            ) : (
              <IvcForm copy={copy} value={ivc} onChange={setIvc} />
            )}

            {error ? (
              <p
                role="alert"
                className="mt-5 rounded-xl bg-[var(--color-danger-soft)] p-4 text-sm text-[var(--color-danger)]"
              >
                {error}
              </p>
            ) : null}
            <Button
              type="submit"
              className="mt-6 w-full sm:w-auto"
              disabled={isRunning}
            >
              {isRunning ? copy.running : copy.run}
            </Button>
          </div>
        </form>

        <PlaygroundResultCard copy={copy} run={run} isRunning={isRunning} />
      </section>
    </div>
  );
}

function AgentChoice({
  active,
  badge,
  title,
  description,
  onClick,
}: {
  active: boolean;
  badge: string;
  title: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`flex min-h-28 items-start gap-4 rounded-xl border p-4 text-left transition ${active ? "border-[var(--color-brand)] bg-[var(--color-success-soft)] ring-2 ring-[var(--color-brand)]/10" : "border-[var(--color-line)] bg-white hover:border-[var(--color-brand)]/45"}`}
    >
      <span
        className={`grid h-10 min-w-10 place-items-center rounded-lg text-xs font-black ${active ? "bg-[var(--color-brand)] text-white" : "bg-[var(--color-surface-subtle)] text-[var(--color-brand)]"}`}
      >
        {badge}
      </span>
      <span>
        <span className="block text-sm font-bold leading-5">{title}</span>
        <span className="mt-1 block text-xs leading-5 text-[var(--color-muted)]">
          {description}
        </span>
      </span>
    </button>
  );
}

function CommercialForm({
  copy,
  value,
  onChange,
}: {
  copy: Copy;
  value: CommercialKitchenPlaygroundInput;
  onChange: (value: CommercialKitchenPlaygroundInput) => void;
}) {
  const update = (key: keyof CommercialKitchenPlaygroundInput, next: string) =>
    onChange({ ...value, [key]: next || null });
  return (
    <div className="mt-6 grid gap-5 sm:grid-cols-2">
      <FieldGroup label={copy.projectType}>
        <TextField
          value={value.project_type ?? ""}
          onChange={(event) => update("project_type", event.target.value)}
        />
      </FieldGroup>
      <FieldGroup label={copy.location}>
        <TextField
          value={value.location ?? ""}
          onChange={(event) => update("location", event.target.value)}
        />
      </FieldGroup>
      <FieldGroup label={copy.capacity}>
        <TextField
          value={value.capacity ?? ""}
          onChange={(event) => update("capacity", event.target.value)}
        />
      </FieldGroup>
      <FieldGroup label={copy.budget}>
        <TextField
          value={value.budget ?? ""}
          onChange={(event) => update("budget", event.target.value)}
        />
      </FieldGroup>
      <FieldGroup label={copy.timeline} className="sm:col-span-2">
        <TextField
          value={value.timeline ?? ""}
          onChange={(event) => update("timeline", event.target.value)}
        />
      </FieldGroup>
    </div>
  );
}

function IvcForm({
  copy,
  value,
  onChange,
}: {
  copy: Copy;
  value: IvcPlaygroundInput;
  onChange: (value: IvcPlaygroundInput) => void;
}) {
  const update = (key: keyof IvcPlaygroundInput, next: string) =>
    onChange({ ...value, [key]: next || null });
  return (
    <div className="mt-6 grid gap-5 sm:grid-cols-2">
      <FieldGroup label={copy.organization}>
        <TextField
          value={value.organization ?? ""}
          onChange={(event) => update("organization", event.target.value)}
        />
      </FieldGroup>
      <FieldGroup label={copy.facilityType}>
        <TextField
          value={value.facility_type ?? ""}
          onChange={(event) => update("facility_type", event.target.value)}
        />
      </FieldGroup>
      <FieldGroup label={copy.speciesResearch}>
        <TextField
          value={value.species_research ?? ""}
          onChange={(event) => update("species_research", event.target.value)}
        />
      </FieldGroup>
      <FieldGroup label={copy.capacity}>
        <TextField
          value={value.capacity ?? ""}
          onChange={(event) => update("capacity", event.target.value)}
        />
      </FieldGroup>
      <FieldGroup label={copy.technicalRequirements} className="sm:col-span-2">
        <TextArea
          rows={4}
          value={value.technical_requirements ?? ""}
          onChange={(event) =>
            update("technical_requirements", event.target.value)
          }
        />
      </FieldGroup>
      <FieldGroup label={copy.timeline} className="sm:col-span-2">
        <TextField
          value={value.timeline ?? ""}
          onChange={(event) => update("timeline", event.target.value)}
        />
      </FieldGroup>
    </div>
  );
}

function PlaygroundResultCard({
  copy,
  run,
  isRunning,
}: {
  copy: Copy;
  run: PlaygroundRun | null;
  isRunning: boolean;
}) {
  const result = run?.result;
  if (!result) {
    return (
      <section className="card grid min-h-[34rem] place-items-center p-8 text-center">
        <div className="max-w-sm">
          <div
            className={`mx-auto grid h-16 w-16 place-items-center rounded-full text-sm font-black ${isRunning ? "animate-pulse bg-[var(--color-info-soft)] text-[var(--color-info)]" : "bg-[var(--color-success-soft)] text-[var(--color-brand)]"}`}
          >
            AI
          </div>
          <h2 className="mt-5 text-xl font-semibold">
            {isRunning ? copy.running : copy.emptyTitle}
          </h2>
          <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
            {copy.emptyDescription}
          </p>
          {run ? (
            <p className="mt-4 text-xs uppercase tracking-[0.12em] text-[var(--color-muted)]">
              {run.status}
            </p>
          ) : null}
        </div>
      </section>
    );
  }
  return (
    <ResultContent copy={copy} result={result} provider={run.provider_type} />
  );
}

function ResultContent({
  copy,
  result,
  provider,
}: {
  copy: Copy;
  result: PlaygroundResult;
  provider: string | null;
}) {
  return (
    <section className="card overflow-hidden" aria-live="polite">
      <div className="bg-[var(--color-brand-strong)] p-6 text-white sm:p-7">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#d7a58e]">
          {copy.humanReview}
        </p>
        <div className="mt-5 flex items-end justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.14em] text-white/50">
              {copy.score}
            </p>
            <p className="mt-1 text-5xl font-semibold tabular-nums">
              {Math.round(result.qualification_score)}
              <span className="text-base text-white/45"> / 100</span>
            </p>
          </div>
          <StatusBadge tone={levelTone(result.qualification_level)}>
            {copy.level} {result.qualification_level}
          </StatusBadge>
        </div>
        <div
          className="mt-5 h-2 overflow-hidden rounded-full bg-white/12"
          role="progressbar"
          aria-valuenow={result.qualification_score}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full rounded-full bg-[#d18867]"
            style={{ width: `${result.qualification_score}%` }}
          />
        </div>
        <p className="mt-4 text-xs text-white/50">
          {copy.provider}:{" "}
          {provider === "mock" ? "Deterministic demo" : provider || "—"}
        </p>
      </div>
      <div className="space-y-7 p-6 sm:p-7">
        <ResultSection
          title={copy.businessSummary}
          text={result.business_summary}
        />
        <ResultList
          title={copy.missingInformation}
          items={result.missing_information}
          empty={copy.noMissing}
        />
        <ResultList title={copy.risks} items={result.risks} />
        <ResultList
          title={copy.nextActions}
          items={result.recommended_next_actions}
          numbered
        />
      </div>
    </section>
  );
}

function ResultSection({ title, text }: { title: string; text: string }) {
  return (
    <div>
      <p className="eyebrow">{title}</p>
      <p className="mt-3 text-sm leading-7">{text}</p>
    </div>
  );
}

function ResultList({
  title,
  items,
  empty,
  numbered = false,
}: {
  title: string;
  items: string[];
  empty?: string;
  numbered?: boolean;
}) {
  return (
    <div className="border-t border-[var(--color-line)] pt-6">
      <h3 className="text-sm font-semibold">{title}</h3>
      {items.length ? (
        <ol className="mt-3 space-y-2 text-sm leading-6 text-[var(--color-muted)]">
          {items.map((item, index) => (
            <li key={item} className="flex gap-3">
              <span className="font-bold text-[var(--color-accent)]">
                {numbered ? `${index + 1}.` : "•"}
              </span>
              <span>{item}</span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-3 text-sm text-[var(--color-muted)]">{empty}</p>
      )}
    </div>
  );
}

function levelTone(level: "A" | "B" | "C") {
  return level === "A" ? "success" : level === "B" ? "warning" : "danger";
}

function delay(milliseconds: number) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}
