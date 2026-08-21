import { interpolate, useCurrentFrame } from "remotion";
import { C, EASE_OUT } from "./theme";
import { MONO, SANS } from "../shared/fonts";
import { Composer } from "./ComposerBar";

export const WIN_W = 1600;
export const WIN_H = 1000;

const Spinner: React.FC<{ size: number }> = ({ size }) => {
  const frame = useCurrentFrame();
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      style={{ transform: `rotate(${frame * 9}deg)` }}
    >
      <title>Working</title>
      {Array.from({ length: 8 }, (_, i) => (
        <rect
          key={i}
          x="11.2"
          y="2"
          width="1.6"
          height="5.4"
          rx="0.8"
          fill={C.fg}
          opacity={0.18 + (i / 8) * 0.82}
          transform={`rotate(${i * 45} 12 12)`}
        />
      ))}
    </svg>
  );
};

const Tick: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <title>Done</title>
    <circle cx="12" cy="12" r="9" stroke={C.dim} strokeWidth={1.6} />
    <path d="m8 12.2 2.8 2.8L16.2 9.6" stroke={C.dim} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

/** Queued work is an empty ring — it must not read as already finished. */
const Pending: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <title>Queued</title>
    <circle cx="12" cy="12" r="9" stroke={C.faint} strokeWidth={1.6} strokeDasharray="3 3.4" />
  </svg>
);

const TaskRow: React.FC<{
  title: string;
  sub: string;
  state: "done" | "active" | "queued";
  diff?: string;
}> = ({ title, sub, state, diff }) => (
  <div
    style={{
      display: "flex",
      gap: 14,
      alignItems: "flex-start",
      padding: "14px 18px",
      backgroundColor: state === "active" ? "rgba(255,255,255,0.055)" : "transparent",
      borderLeft: `2px solid ${state === "active" ? C.fg : "transparent"}`,
    }}
  >
    <div style={{ paddingTop: 2 }}>
      {state === "active" ? (
        <Spinner size={20} />
      ) : state === "done" ? (
        <Tick size={20} />
      ) : (
        <Pending size={20} />
      )}
    </div>
    <div style={{ minWidth: 0, flex: 1 }}>
      <div
        style={{
          fontFamily: SANS,
          fontSize: 21,
          fontWeight: 500,
          color: state === "queued" ? C.dim : C.fg,
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {title}
      </div>
      <div style={{ fontFamily: SANS, fontSize: 17, color: C.faint, marginTop: 4 }}>
        {diff ? (
          <>
            <span style={{ color: "#5BC98B" }}>+{diff.split("/")[0]}</span>{" "}
            <span style={{ color: "#D4675E" }}>−{diff.split("/")[1]}</span>
            <span> · </span>
          </>
        ) : null}
        {sub}
      </div>
    </div>
  </div>
);

const FileChip: React.FC<{ name: string; add: number }> = ({ name, add }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 10,
      padding: "11px 14px",
      borderRadius: 10,
      border: `1px solid ${C.border}`,
      backgroundColor: "rgba(255,255,255,0.03)",
    }}
  >
    <svg width={17} height={17} viewBox="0 0 24 24" fill="none">
      <title>File</title>
      <path d="M14 3H7a1.5 1.5 0 0 0-1.5 1.5v15A1.5 1.5 0 0 0 7 21h10a1.5 1.5 0 0 0 1.5-1.5V7.5L14 3Z" stroke={C.dim} strokeWidth={1.5} strokeLinejoin="round" />
    </svg>
    <div style={{ flex: 1, fontFamily: SANS, fontSize: 18, color: C.fg }}>{name}</div>
    <div style={{ fontFamily: MONO, fontSize: 15, color: "#5BC98B" }}>+{add}</div>
    <div style={{ fontFamily: MONO, fontSize: 15, color: C.faint }}>−0</div>
  </div>
);

const CODE: [string, string][][] = [
  [["import", "kw"], [" { Mark } ", "pl"], ["from", "kw"], [' "@/components/Mark"', "str"]],
  [],
  [["export default function", "kw"], [" Home", "fn"], ["() {", "pl"]],
  [["  return", "kw"], [" (", "pl"]],
  [["    <main", "tag"], [" className", "attr"], ["=", "pl"], ['"min-h-screen flex flex-col"', "str"], [">", "tag"]],
  [["      <Mark", "tag"], [" className", "attr"], ["=", "pl"], ['"h-12 w-12"', "str"], [" />", "tag"]],
  [["      <h1", "tag"], [" className", "attr"], ["=", "pl"], ['"text-[4rem] leading-[0.95]"', "str"], [">", "tag"]],
  [["        We give teams the upper hand.", "hl"]],
  [["      </h1>", "tag"]],
  [["    </main>", "tag"]],
  [["  )", "pl"]],
  [["}", "pl"]],
];

const TONE: Record<string, string> = {
  kw: "#C58AF9",
  fn: "#79B8FF",
  tag: "#6FA8DC",
  attr: "#E5C07B",
  str: "#98C379",
  pl: "#B6B6BE",
  hl: "#FFE9A8",
};

const CodePane: React.FC = () => (
  <div style={{ padding: "22px 26px", fontFamily: MONO, fontSize: 18, lineHeight: 1.72 }}>
    {CODE.map((line, i) => (
      <div key={i} style={{ whiteSpace: "pre", minHeight: 31 }}>
        {line.map(([text, tone], j) => (
          <span
            key={j}
            style={{
              color: TONE[tone],
              backgroundColor: tone === "hl" ? "rgba(255,180,60,0.12)" : undefined,
            }}
          >
            {text}
          </span>
        ))}
      </div>
    ))}
  </div>
);

/**
 * A generic AI-coding-agent IDE: task rail, agent transcript, editor. Built
 * from scratch rather than screen-recorded, so the camera can push into it at
 * any magnification without turning to mush.
 *
 * `local` is frames since the shot began; the transcript fills in over it.
 */
export const IdeWindow: React.FC<{ local: number; menu?: number }> = ({
  local,
  menu = 0,
}) => {
  const step = (at: number) =>
    interpolate(local, [at, at + 12], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: EASE_OUT,
    });

  return (
    <div
      style={{
        width: WIN_W,
        height: WIN_H,
        borderRadius: 18,
        overflow: "hidden",
        backgroundColor: C.ink,
        border: `1px solid ${C.border}`,
        display: "flex",
        flexDirection: "column",
        boxShadow: "0 60px 160px rgba(0,0,0,0.8)",
      }}
    >
      <div
        style={{
          height: 46,
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          padding: "0 18px",
          gap: 9,
          borderBottom: `1px solid ${C.border}`,
          backgroundColor: C.panel,
        }}
      >
        {["#3F3F45", "#3F3F45", "#3F3F45"].map((c, i) => (
          <div key={i} style={{ width: 12, height: 12, borderRadius: 999, backgroundColor: c }} />
        ))}
        <div
          style={{
            flex: 1,
            textAlign: "center",
            fontFamily: SANS,
            fontSize: 17,
            color: C.faint,
          }}
        >
          the upper hand — landing
        </div>
        <div style={{ width: 60 }} />
      </div>

      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        {/* Task rail */}
        <div
          style={{
            width: 440,
            flexShrink: 0,
            borderRight: `1px solid ${C.border}`,
            backgroundColor: "rgba(255,255,255,0.012)",
            paddingTop: 10,
          }}
        >
          <div style={{ opacity: step(0) }}>
            <TaskRow title="Bioinformatics Tools" sub="Bioinformatics Tools" state="done" diff="143/21" />
          </div>
          <div
            style={{
              fontFamily: SANS,
              fontSize: 15,
              letterSpacing: "0.16em",
              color: C.faint,
              padding: "18px 20px 8px",
            }}
          >
            IN PROGRESS 1
          </div>
          <div style={{ opacity: step(10) }}>
            <TaskRow title="Plan Mission Control" sub="Generating plan" state="active" />
          </div>
          <div style={{ opacity: step(26) }}>
            <TaskRow title="Analyze Tab vs Agent Usage…" sub="Fetching data" state="queued" />
          </div>
          <div style={{ opacity: step(38) }}>
            <TaskRow title="Build Landing Page" sub="Reading docs" state="queued" />
          </div>
        </div>

        {/* Agent transcript */}
        <div
          style={{
            width: 520,
            flexShrink: 0,
            borderRight: `1px solid ${C.border}`,
            display: "flex",
            flexDirection: "column",
            padding: 22,
            gap: 16,
          }}
        >
          <div
            style={{
              padding: "16px 18px",
              borderRadius: 12,
              border: `1px solid ${C.border}`,
              backgroundColor: "rgba(255,255,255,0.035)",
              fontFamily: SANS,
              fontSize: 19,
              lineHeight: 1.5,
              color: C.fg,
              opacity: step(4),
            }}
          >
            make a landing page from the attached docs explaining what the upper
            hand does
          </div>

          <div style={{ fontFamily: SANS, fontSize: 18, color: C.faint, opacity: step(18) }}>
            Read <span style={{ color: C.dim }}>brand-voice.md</span>
            <br />
            Read <span style={{ color: C.dim }}>ux-guidelines.pdf</span>
            <br />
            Thought <span style={{ color: C.dim }}>61s</span>
          </div>

          <div
            style={{
              fontFamily: SANS,
              fontSize: 19,
              lineHeight: 1.55,
              color: C.fg,
              opacity: step(30),
            }}
          >
            I&rsquo;ll build a minimal, type-led landing page that matches your
            brand voice.
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10, opacity: step(42) }}>
            <FileChip name="app/page.tsx" add={52} />
            <FileChip name="app/globals.css" add={18} />
          </div>

          <div
            style={{
              fontFamily: SANS,
              fontSize: 18,
              lineHeight: 1.55,
              color: C.dim,
              opacity: step(56),
            }}
          >
            Done. Fonts preload in the head, critical CSS is inlined, and I added
            a <span style={{ color: C.faint }}>color-scheme</span> hint.
          </div>

          <div style={{ flex: 1 }} />
          <Composer width={476} menu={menu} chips={0} height={192} />
        </div>

        {/* Editor */}
        <div style={{ flex: 1, minWidth: 0, backgroundColor: "rgba(255,255,255,0.008)", opacity: step(22) }}>
          <CodePane />
        </div>
      </div>
    </div>
  );
};
