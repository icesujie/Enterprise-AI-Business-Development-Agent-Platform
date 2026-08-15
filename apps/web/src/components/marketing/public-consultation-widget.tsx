"use client";

import { useState, type FormEvent } from "react";

import {
  createConsultationLead,
  processConsultationTurn,
  type ConsultationField,
  type ConsultationLanguage,
} from "@/app/(marketing)/public-consultation-actions";
import { Button } from "@/components/ui/button";

type Message = { role: "assistant" | "visitor"; text: string };

const firstField: ConsultationField = "facility_type";
const emptyValues: Record<ConsultationField, string> = {
  facility_type: "",
  project_type: "",
  location: "",
  capacity: "",
  timeline: "",
  budget_range: "",
  contact_name: "",
  company: "",
  email: "",
};

export function PublicConsultationWidget({
  initialLanguage,
}: {
  initialLanguage: ConsultationLanguage;
}) {
  const [open, setOpen] = useState(false);
  const [language, setLanguage] = useState(initialLanguage);
  const [field, setField] = useState<ConsultationField | null>(firstField);
  const [values, setValues] = useState(emptyValues);
  const [answer, setAnswer] = useState("");
  const [messages, setMessages] = useState<Message[]>(() =>
    greeting(initialLanguage),
  );
  const [consent, setConsent] = useState(false);
  const [marketingConsent, setMarketingConsent] = useState(false);
  const [pending, setPending] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [duplicate, setDuplicate] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const copy = language === "zh-CN" ? zh : en;

  function changeLanguage(next: ConsultationLanguage) {
    setLanguage(next);
    if (!Object.values(values).some(Boolean)) setMessages(greeting(next));
  }

  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!field || !answer.trim()) return;
    setPending(true);
    setError(null);
    try {
      const response = await processConsultationTurn({
        language,
        field,
        answer: answer.trim(),
      });
      setValues((current) => ({
        ...current,
        [field]: response.accepted_value,
      }));
      setMessages((current) => [
        ...current,
        { role: "visitor", text: answer.trim() },
        { role: "assistant", text: response.assistant_message },
      ]);
      setField(response.next_field);
      setAnswer("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : copy.failed);
    } finally {
      setPending(false);
    }
  }

  async function submitLead() {
    if (!consent) return;
    setPending(true);
    setError(null);
    try {
      const result = await createConsultationLead({
        language,
        values,
        contactConsent: consent,
        marketingConsent,
      });
      setDuplicate(Boolean(result.duplicate));
      setSubmitted(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : copy.failed);
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      {open ? (
        <section
          aria-label={copy.title}
          aria-modal="false"
          className="fixed inset-x-2 bottom-2 top-[84px] z-[70] flex flex-col overflow-hidden rounded-2xl border border-[var(--color-line)] bg-white shadow-2xl sm:inset-x-auto sm:right-5 sm:top-auto sm:h-[min(680px,calc(100vh-110px))] sm:w-[410px]"
          role="dialog"
        >
          <header className="flex items-center justify-between bg-[var(--color-brand-strong)] px-5 py-4 text-white">
            <div>
              <p className="text-[0.63rem] font-bold uppercase tracking-[0.16em] text-white/55">
                {copy.eyebrow}
              </p>
              <h2 className="mt-1 font-semibold">{copy.title}</h2>
            </div>
            <button
              aria-label={copy.close}
              className="grid h-9 w-9 place-items-center rounded-full border border-white/20 text-xl"
              onClick={() => setOpen(false)}
              type="button"
            >
              ×
            </button>
          </header>

          <div className="min-h-0 flex-1 overflow-y-auto bg-[var(--color-surface-subtle)] p-4">
            <div className="mb-4 flex justify-end">
              <select
                aria-label={copy.language}
                className="rounded-lg border border-[var(--color-line)] bg-white px-3 py-2 text-xs font-semibold"
                value={language}
                onChange={(event) =>
                  changeLanguage(event.target.value as ConsultationLanguage)
                }
              >
                <option value="en">English</option>
                <option value="zh-CN">中文</option>
              </select>
            </div>

            {!submitted ? (
              <div className="space-y-3" aria-live="polite">
                {messages.map((message, index) => (
                  <p
                    className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                      message.role === "visitor"
                        ? "ml-auto bg-[var(--color-brand)] text-white"
                        : "bg-white text-[var(--color-ink)] shadow-sm"
                    }`}
                    key={`${message.role}-${index}`}
                  >
                    {message.text}
                  </p>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl bg-[var(--color-success-soft)] p-5 text-sm leading-6 text-[var(--color-success)]">
                <h3 className="font-bold">
                  {duplicate ? copy.duplicateTitle : copy.successTitle}
                </h3>
                <p className="mt-2">
                  {duplicate ? copy.duplicateBody : copy.successBody}
                </p>
              </div>
            )}

            {!field && !submitted ? (
              <div className="mt-4 rounded-2xl bg-white p-4 shadow-sm">
                <h3 className="font-bold">{copy.review}</h3>
                <dl className="mt-3 space-y-2 text-xs">
                  {summaryRows(copy, values).map(([label, value]) => (
                    <div
                      className="grid grid-cols-[7rem_1fr] gap-2"
                      key={label}
                    >
                      <dt className="text-[var(--color-muted)]">{label}</dt>
                      <dd className="font-semibold">{value || "—"}</dd>
                    </div>
                  ))}
                </dl>
                <label className="mt-4 flex items-start gap-3 text-xs leading-5">
                  <input
                    checked={consent}
                    className="mt-1"
                    onChange={(event) => setConsent(event.target.checked)}
                    type="checkbox"
                  />
                  {copy.consent}
                </label>
                <label className="mt-3 flex items-start gap-3 text-xs leading-5 text-[var(--color-muted)]">
                  <input
                    checked={marketingConsent}
                    className="mt-1"
                    onChange={(event) =>
                      setMarketingConsent(event.target.checked)
                    }
                    type="checkbox"
                  />
                  {copy.marketing}
                </label>
                <Button
                  className="mt-4 w-full"
                  disabled={!consent || pending}
                  onClick={submitLead}
                >
                  {pending ? copy.submitting : copy.createInquiry}
                </Button>
              </div>
            ) : null}
            {error ? (
              <p
                className="mt-4 rounded-xl bg-[var(--color-danger-soft)] p-3 text-sm text-[var(--color-danger)]"
                role="alert"
              >
                {error}
              </p>
            ) : null}
          </div>

          {field && !submitted ? (
            <form
              className="border-t border-[var(--color-line)] bg-white p-4"
              onSubmit={send}
            >
              <label className="sr-only" htmlFor="public-consultation-answer">
                {copy.answer}
              </label>
              <div className="flex gap-2">
                <input
                  autoComplete={field === "email" ? "email" : "off"}
                  className="field min-w-0 flex-1"
                  id="public-consultation-answer"
                  maxLength={500}
                  placeholder={
                    field === "budget_range" ? copy.optional : copy.answer
                  }
                  type={field === "email" ? "email" : "text"}
                  value={answer}
                  onChange={(event) => setAnswer(event.target.value)}
                />
                <Button disabled={pending || !answer.trim()} type="submit">
                  {pending ? "…" : copy.send}
                </Button>
              </div>
              <p className="mt-2 text-[0.68rem] text-[var(--color-muted)]">
                {copy.boundary}
              </p>
            </form>
          ) : null}
        </section>
      ) : null}

      <button
        aria-expanded={open}
        aria-label={copy.open}
        className="fixed bottom-5 right-4 z-[71] flex items-center gap-2 rounded-full bg-[var(--color-accent)] px-5 py-3 text-sm font-bold text-white shadow-[0_16px_45px_rgb(180_81_43/35%)] transition hover:-translate-y-1 sm:right-6"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        <span aria-hidden="true">✦</span>
        {copy.button}
      </button>
    </>
  );
}

function greeting(language: ConsultationLanguage): Message[] {
  const copy = language === "zh-CN" ? zh : en;
  return [
    { role: "assistant", text: copy.greeting },
    { role: "assistant", text: copy.firstQuestion },
  ];
}

const en = {
  eyebrow: "Public project consultation",
  title: "Commercial Kitchen Consultation Agent",
  button: "Project consultation",
  open: "Open Commercial Kitchen Consultation Agent",
  close: "Close consultation assistant",
  language: "Consultation language",
  greeting:
    "Hello. I can help organize your commercial-kitchen project requirements for human review.",
  firstQuestion:
    "What type of facility is this for, such as a school, hospital, factory, or central kitchen?",
  answer: "Type your answer",
  optional: "Budget range or Skip",
  send: "Send",
  boundary:
    "Public information only. No price, delivery, or technical commitment is made here.",
  review: "Review your project brief",
  consent:
    "I consent to Sari Arta using these details to contact me about this project.",
  marketing:
    "I also agree to receive relevant marketing information (optional).",
  createInquiry: "Create project inquiry",
  submitting: "Submitting…",
  successTitle: "Inquiry received",
  successBody:
    "A sales team member can now review your project brief and decide the appropriate follow-up.",
  duplicateTitle: "Inquiry already received",
  duplicateBody:
    "We found the same recent inquiry and did not create a duplicate lead.",
  failed: "We could not process this request. Please try again.",
  labels: [
    "Facility",
    "Project type",
    "Location",
    "Capacity",
    "Timeline",
    "Budget",
    "Contact",
    "Company",
    "Email",
  ],
};

const zh: typeof en = {
  eyebrow: "公开项目咨询",
  title: "商用厨房项目咨询智能体",
  button: "项目智能咨询",
  open: "打开商用厨房项目咨询智能体",
  close: "关闭项目咨询助手",
  language: "咨询语言",
  greeting: "您好，我可以帮助整理商用厨房项目需求，并提交给业务人员审核。",
  firstQuestion: "这个项目属于哪类设施，例如学校、医院、工厂食堂或中央厨房？",
  answer: "请输入回答",
  optional: "预算范围或输入“跳过”",
  send: "发送",
  boundary: "仅使用公开信息；这里不会承诺价格、交期或技术条件。",
  review: "检查项目摘要",
  consent: "我同意 Sari Arta 使用这些信息就本项目与我联系。",
  marketing: "我也同意接收相关市场信息（可选）。",
  createInquiry: "创建项目询盘",
  submitting: "正在提交……",
  successTitle: "询盘已收到",
  successBody: "销售人员现在可以审核项目摘要，并决定适当的后续跟进。",
  duplicateTitle: "询盘已经收到",
  duplicateBody: "系统发现相同的近期询盘，因此没有重复创建销售线索。",
  failed: "当前无法处理该请求，请稍后重试。",
  labels: [
    "设施",
    "项目类型",
    "地点",
    "规模",
    "时间",
    "预算",
    "联系人",
    "公司",
    "邮箱",
  ],
};

function summaryRows(
  copy: typeof en,
  values: Record<ConsultationField, string>,
) {
  return copy.labels.map(
    (label, index) => [label, Object.values(values)[index]] as const,
  );
}
