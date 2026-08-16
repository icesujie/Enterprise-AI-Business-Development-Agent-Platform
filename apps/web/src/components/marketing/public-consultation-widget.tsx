"use client";

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";

import {
  createConsultationLead,
  processConsultationTurn,
  type ConsultationField,
  type ConsultationLanguage,
} from "@/app/(marketing)/public-consultation-actions";
import { Button } from "@/components/ui/button";
import { captureAcquisitionAttribution } from "@/lib/acquisition-attribution";

type Message = { role: "assistant" | "visitor"; text: string };
type Point = { x: number; y: number };
type DragListenerOptions = {
  origin: Point;
  pointerX: number;
  pointerY: number;
  element: HTMLElement | null;
  onMove: (next: Point, distance: number) => void;
  onFinish: (next: Point) => void;
};

const launcherStorageKey = "sari-arta-public-consultation-launcher-position";
const panelStorageKey = "sari-arta-public-consultation-panel-position";

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
  const launcherRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLElement>(null);
  const stopLauncherDrag = useRef<(() => void) | null>(null);
  const stopPanelDrag = useRef<(() => void) | null>(null);
  const launcherMoved = useRef(false);
  const [launcherPosition, setLauncherPosition] = useState<Point | null>(null);
  const [panelPosition, setPanelPosition] = useState<Point | null>(null);
  const copy = language === "zh-CN" ? zh : en;

  useEffect(() => {
    setLauncherPosition(
      restorePosition(launcherStorageKey, launcherRef.current),
    );
    const keepInsideViewport = () => {
      setLauncherPosition((current) =>
        current ? clampToViewport(current, launcherRef.current) : current,
      );
      setPanelPosition((current) =>
        current ? clampToViewport(current, panelRef.current) : current,
      );
    };
    window.addEventListener("resize", keepInsideViewport);
    return () => {
      window.removeEventListener("resize", keepInsideViewport);
      stopLauncherDrag.current?.();
      stopPanelDrag.current?.();
    };
  }, []);

  useEffect(() => {
    if (!open || panelPosition) return;
    const frame = window.requestAnimationFrame(() => {
      setPanelPosition(restorePosition(panelStorageKey, panelRef.current));
    });
    return () => window.cancelAnimationFrame(frame);
  }, [open, panelPosition]);

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
        attribution: captureAcquisitionAttribution(),
      });
      setDuplicate(Boolean(result.duplicate));
      setSubmitted(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : copy.failed);
    } finally {
      setPending(false);
    }
  }

  function startLauncherDrag(event: ReactPointerEvent<HTMLButtonElement>) {
    if (event.button !== 0) return;
    event.preventDefault();
    const origin = currentPosition(event.currentTarget, launcherPosition);
    launcherMoved.current = false;
    stopLauncherDrag.current?.();
    stopLauncherDrag.current = listenForDrag({
      origin,
      pointerX: event.clientX,
      pointerY: event.clientY,
      element: launcherRef.current,
      onMove: (next, distance) => {
        if (distance > 4) launcherMoved.current = true;
        setLauncherPosition(next);
      },
      onFinish: (next) => {
        setLauncherPosition(next);
        savePosition(launcherStorageKey, next);
        stopLauncherDrag.current = null;
      },
    });
  }

  function startPanelDrag(event: ReactPointerEvent<HTMLElement>) {
    if (event.button !== 0) return;
    if ((event.target as HTMLElement).closest("button, input, select")) return;
    event.preventDefault();
    const origin = currentPosition(panelRef.current, panelPosition);
    stopPanelDrag.current?.();
    stopPanelDrag.current = listenForDrag({
      origin,
      pointerX: event.clientX,
      pointerY: event.clientY,
      element: panelRef.current,
      onMove: setPanelPosition,
      onFinish: (next) => {
        setPanelPosition(next);
        savePosition(panelStorageKey, next);
        stopPanelDrag.current = null;
      },
    });
  }

  return (
    <>
      {open ? (
        <section
          aria-label={copy.title}
          aria-modal="false"
          className={`fixed z-[70] flex h-[calc(100vh-92px)] w-[calc(100vw-16px)] flex-col overflow-hidden rounded-2xl border border-[var(--color-line)] bg-white shadow-2xl sm:h-[min(680px,calc(100vh-110px))] sm:w-[410px] ${panelPosition ? "" : "bottom-2 left-2 sm:bottom-5 sm:left-auto sm:right-5"}`}
          ref={panelRef}
          role="dialog"
          style={
            panelPosition
              ? { left: panelPosition.x, top: panelPosition.y }
              : undefined
          }
        >
          <header
            aria-label={copy.dragWindow}
            className="flex touch-none select-none items-center justify-between bg-[var(--color-brand-strong)] px-5 py-4 text-white sm:cursor-grab sm:active:cursor-grabbing"
            onPointerDown={startPanelDrag}
          >
            <div>
              <p className="text-[0.63rem] font-bold uppercase tracking-[0.16em] text-white/55">
                {copy.eyebrow}
              </p>
              <h2 className="mt-1 font-semibold">{copy.title}</h2>
              <p className="mt-1 hidden text-[0.65rem] text-white/55 sm:block">
                {copy.dragHint}
              </p>
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

      {!open ? (
        <button
          aria-expanded="false"
          aria-label={copy.open}
          className={`fixed z-[71] flex touch-none select-none items-center gap-2 rounded-full bg-[var(--color-accent)] px-5 py-3 text-sm font-bold text-white shadow-[0_16px_45px_rgb(180_81_43/35%)] transition hover:-translate-y-1 active:cursor-grabbing ${launcherPosition ? "" : "bottom-5 right-4 sm:right-6"}`}
          onClick={() => {
            if (launcherMoved.current) {
              launcherMoved.current = false;
              return;
            }
            setOpen(true);
          }}
          onPointerDown={startLauncherDrag}
          ref={launcherRef}
          style={
            launcherPosition
              ? { left: launcherPosition.x, top: launcherPosition.y }
              : undefined
          }
          title={copy.dragLauncher}
          type="button"
        >
          <span aria-hidden="true">✦</span>
          {copy.button}
        </button>
      ) : null}
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
  dragLauncher: "Drag to reposition; click to open",
  dragWindow: "Drag consultation window",
  dragHint: "Drag this header to reposition",
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
  dragLauncher: "拖动可调整位置，点击可打开",
  dragWindow: "拖动项目咨询窗口",
  dragHint: "拖动此标题栏可调整位置",
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

function listenForDrag(options: DragListenerOptions): () => void {
  let last = options.origin;
  let finished = false;

  const move = (clientX: number, clientY: number) => {
    const raw = {
      x: options.origin.x + clientX - options.pointerX,
      y: options.origin.y + clientY - options.pointerY,
    };
    last = clampToViewport(raw, options.element);
    options.onMove(
      last,
      Math.hypot(raw.x - options.origin.x, raw.y - options.origin.y),
    );
  };
  const onPointerMove = (event: PointerEvent) => {
    event.preventDefault();
    move(event.clientX, event.clientY);
  };
  const onMouseMove = (event: MouseEvent) => {
    event.preventDefault();
    move(event.clientX, event.clientY);
  };
  const cleanup = () => {
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", finish);
    window.removeEventListener("pointercancel", finish);
    window.removeEventListener("mousemove", onMouseMove);
    window.removeEventListener("mouseup", finish);
  };
  const finish = () => {
    if (finished) return;
    finished = true;
    cleanup();
    options.onFinish(last);
  };

  window.addEventListener("pointermove", onPointerMove, { passive: false });
  window.addEventListener("pointerup", finish);
  window.addEventListener("pointercancel", finish);
  window.addEventListener("mousemove", onMouseMove, { passive: false });
  window.addEventListener("mouseup", finish);
  return cleanup;
}

function currentPosition(
  element: HTMLElement | null,
  position: Point | null,
): Point {
  if (position) return position;
  const bounds = element?.getBoundingClientRect();
  return { x: bounds?.left ?? 0, y: bounds?.top ?? 0 };
}

function clampToViewport(point: Point, element: HTMLElement | null): Point {
  const bounds = element?.getBoundingClientRect();
  const width = bounds?.width ?? 0;
  const height = bounds?.height ?? 0;
  const margin = 8;
  return {
    x: Math.min(
      Math.max(point.x, margin),
      Math.max(margin, window.innerWidth - width - margin),
    ),
    y: Math.min(
      Math.max(point.y, margin),
      Math.max(margin, window.innerHeight - height - margin),
    ),
  };
}

function restorePosition(
  storageKey: string,
  element: HTMLElement | null,
): Point {
  try {
    const stored = window.localStorage.getItem(storageKey);
    if (stored) {
      const point = JSON.parse(stored) as Partial<Point>;
      if (typeof point.x === "number" && typeof point.y === "number") {
        return clampToViewport({ x: point.x, y: point.y }, element);
      }
    }
  } catch {
    window.localStorage.removeItem(storageKey);
  }
  const bounds = element?.getBoundingClientRect();
  return clampToViewport(
    { x: bounds?.left ?? 8, y: bounds?.top ?? 8 },
    element,
  );
}

function savePosition(storageKey: string, position: Point | null) {
  if (!position) return;
  window.localStorage.setItem(storageKey, JSON.stringify(position));
}

function summaryRows(
  copy: typeof en,
  values: Record<ConsultationField, string>,
) {
  return copy.labels.map(
    (label, index) => [label, Object.values(values)[index]] as const,
  );
}
