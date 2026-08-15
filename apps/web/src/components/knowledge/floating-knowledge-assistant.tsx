"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";

import { KnowledgeAssistant } from "@/components/knowledge/knowledge-assistant";

type Language = "en" | "zh-CN";

const POSITION_KEY = "sari-arta-knowledge-assistant-y";

export function FloatingKnowledgeAssistant({
  initialLanguage,
}: {
  initialLanguage: Language;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [positionY, setPositionY] = useState(420);
  const drag = useRef({ startY: 0, originalY: 0, moved: false });

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      const stored = Number(window.localStorage.getItem(POSITION_KEY));
      setPositionY(
        clampPosition(Number.isFinite(stored) && stored > 0 ? stored : 420),
      );
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    function keepVisible() {
      setPositionY((current) => clampPosition(current));
    }
    window.addEventListener("resize", keepVisible);
    return () => window.removeEventListener("resize", keepVisible);
  }, []);

  if (pathname === "/knowledge/assistant") return null;

  function startDrag(event: ReactPointerEvent<HTMLButtonElement>) {
    drag.current = {
      startY: event.clientY,
      originalY: positionY,
      moved: false,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function moveDrag(event: ReactPointerEvent<HTMLButtonElement>) {
    if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
    const distance = event.clientY - drag.current.startY;
    if (Math.abs(distance) > 4) drag.current.moved = true;
    setPositionY(clampPosition(drag.current.originalY + distance));
  }

  function endDrag(event: ReactPointerEvent<HTMLButtonElement>) {
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    const finalPosition = clampPosition(
      drag.current.originalY + event.clientY - drag.current.startY,
    );
    setPositionY(finalPosition);
    window.localStorage.setItem(POSITION_KEY, String(finalPosition));
  }

  function toggle() {
    if (drag.current.moved) {
      drag.current.moved = false;
      return;
    }
    setOpen((current) => !current);
  }

  const zh = initialLanguage === "zh-CN";
  return (
    <>
      {open ? (
        <section
          aria-label={zh ? "企业知识助手" : "Enterprise Knowledge Assistant"}
          aria-modal="false"
          className="fixed inset-x-2 bottom-2 top-[76px] z-[70] flex flex-col overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] shadow-2xl sm:inset-x-auto sm:right-5 sm:w-[430px] lg:top-[92px]"
          role="dialog"
        >
          <header className="flex items-center justify-between gap-4 border-b border-[var(--color-line)] bg-[var(--color-brand-strong)] px-5 py-4 text-white">
            <div>
              <p className="text-[0.65rem] font-bold uppercase tracking-[0.16em] text-white/55">
                {zh ? "只读 · 企业知识" : "Read-only · Enterprise knowledge"}
              </p>
              <h2 className="mt-1 font-semibold">
                {zh ? "企业知识助手" : "Knowledge Assistant"}
              </h2>
            </div>
            <button
              aria-label={zh ? "关闭知识助手" : "Close Knowledge Assistant"}
              className="grid h-9 w-9 place-items-center rounded-full border border-white/20 text-xl text-white/80 transition hover:bg-white/10 hover:text-white"
              onClick={() => setOpen(false)}
              type="button"
            >
              ×
            </button>
          </header>
          <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-5">
            <KnowledgeAssistant initialLanguage={initialLanguage} compact />
          </div>
          <footer className="border-t border-[var(--color-line)] bg-[var(--color-surface-subtle)] px-5 py-3 text-right">
            <Link
              className="text-xs font-bold text-[var(--color-brand)] hover:underline"
              href="/knowledge/assistant"
            >
              {zh ? "打开完整页面 →" : "Open full page →"}
            </Link>
          </footer>
        </section>
      ) : null}

      <button
        aria-expanded={open}
        aria-label={
          zh
            ? "打开企业知识助手，可上下拖动"
            : "Open Knowledge Assistant, draggable vertically"
        }
        className="fixed right-3 z-[71] flex touch-none select-none items-center gap-2 rounded-full bg-[var(--color-brand-strong)] px-4 py-3 text-sm font-bold text-white shadow-[0_14px_40px_rgb(16_45_32/35%)] transition hover:-translate-x-1 hover:bg-[var(--color-brand)] sm:right-5"
        onClick={toggle}
        onPointerDown={startDrag}
        onPointerMove={moveDrag}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        style={{ top: positionY, transform: "translateY(-50%)" }}
        type="button"
      >
        <span aria-hidden="true" className="text-lg">
          ✦
        </span>
        <span className="hidden sm:inline">
          {zh ? "知识助手" : "Ask knowledge"}
        </span>
      </button>
    </>
  );
}

function clampPosition(value: number) {
  if (typeof window === "undefined") return value;
  return Math.min(Math.max(value, 92), Math.max(92, window.innerHeight - 72));
}
