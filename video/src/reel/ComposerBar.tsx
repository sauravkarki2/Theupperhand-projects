import { interpolate } from "remotion";
import { C, EASE_OUT } from "./theme";
import { SANS } from "../shared/fonts";

const Infinity8: React.FC<{ s: number; c: string }> = ({ s, c }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <title>Agent</title>
    <path
      d="M8.5 9.2a3.8 3.8 0 1 0 0 5.6c1.6-1.5 2.1-2 3.5-2.8 1.4.8 1.9 1.3 3.5 2.8a3.8 3.8 0 1 0 0-5.6c-1.6 1.5-2.1 2-3.5 2.8-1.4-.8-1.9-1.3-3.5-2.8Z"
      stroke={c}
      strokeWidth={1.7}
    />
  </svg>
);

const ListIcon: React.FC<{ s: number; c: string }> = ({ s, c }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <title>Plan</title>
    <circle cx="5" cy="7" r="1.9" stroke={c} strokeWidth={1.7} />
    <circle cx="5" cy="17" r="1.9" stroke={c} strokeWidth={1.7} />
    <path d="M11 7h9M11 17h9" stroke={c} strokeWidth={1.7} strokeLinecap="round" />
  </svg>
);

const BugIcon: React.FC<{ s: number; c: string }> = ({ s, c }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <title>Debug</title>
    <rect x="7.5" y="8" width="9" height="11" rx="4.5" stroke={c} strokeWidth={1.7} />
    <path
      d="M9.5 6.5 8 5M14.5 6.5 16 5M7.5 12H4M16.5 12H20M7.8 16.5 5 18M16.2 16.5 19 18"
      stroke={c}
      strokeWidth={1.7}
      strokeLinecap="round"
    />
  </svg>
);

const AskIcon: React.FC<{ s: number; c: string }> = ({ s, c }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <title>Ask</title>
    <path
      d="M4.5 6.5A2 2 0 0 1 6.5 4.5h11a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H10l-4 3.5v-3.5H6.5a2 2 0 0 1-2-2v-7Z"
      stroke={c}
      strokeWidth={1.7}
      strokeLinejoin="round"
    />
  </svg>
);

const Check: React.FC<{ s: number; c: string }> = ({ s, c }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <title>Selected</title>
    <path d="m5 12.5 4.5 4.5L19 7" stroke={c} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const MODES = [
  { label: "Agent", Icon: Infinity8 },
  { label: "Plan", Icon: ListIcon },
  { label: "Debug", Icon: BugIcon },
  { label: "Ask", Icon: AskIcon },
];

/**
 * The prompt bar plus its mode menu. Shared between the wide IDE shot (where it
 * sits at the foot of the agent pane) and the close-up shot, so the two are
 * guaranteed to be the same object seen at two distances.
 */
export const ComposerBar: React.FC<{
  width: number;
  /** 0 = closed, 1 = fully open. */
  menu?: number;
  /** Which row the cursor is resting on as the menu opens. */
  hovered?: number;
  placeholder?: string;
}> = ({ width, menu = 0, hovered = 0, placeholder = "Plan the mission interface" }) => {
  const rowH = 46;
  const menuH = MODES.length * rowH + 16;

  return (
    <div style={{ position: "relative", width }}>
      {menu > 0.001 ? (
        <div
          style={{
            position: "absolute",
            left: 12,
            bottom: "100%",
            marginBottom: 10,
            width: 250,
            padding: "8px 0",
            borderRadius: 14,
            backgroundColor: "rgba(30,30,34,0.98)",
            border: `1px solid ${C.border}`,
            boxShadow: "0 30px 60px rgba(0,0,0,0.65)",
            transformOrigin: "left bottom",
            opacity: interpolate(menu, [0, 0.35], [0, 1], {
              extrapolateRight: "clamp",
            }),
            transform: `translateY(${interpolate(menu, [0, 1], [14, 0])}px) scale(${interpolate(
              menu,
              [0, 1],
              [0.94, 1],
            )})`,
            height: menuH,
            overflow: "hidden",
          }}
        >
          {MODES.map((m, i) => {
            const reveal = interpolate(
              menu,
              [0.15 + i * 0.12, 0.45 + i * 0.12],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE_OUT },
            );
            const on = i === hovered;
            return (
              <div
                key={m.label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  height: rowH,
                  padding: "0 16px",
                  opacity: reveal,
                  backgroundColor: on ? "rgba(255,255,255,0.06)" : "transparent",
                }}
              >
                <m.Icon s={20} c={on ? C.fg : C.dim} />
                <div
                  style={{
                    flex: 1,
                    fontFamily: SANS,
                    fontWeight: 400,
                    fontSize: 20,
                    color: on ? C.fg : C.dim,
                  }}
                >
                  {m.label}
                </div>
                {i === 0 ? <Check s={18} c={C.fg} /> : null}
              </div>
            );
          })}
        </div>
      ) : null}

      <div
        style={{
          borderRadius: 16,
          border: `1px solid ${C.border}`,
          background: "linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.035))",
          padding: "18px 18px 14px",
        }}
      >
        <div
          style={{
            fontFamily: SANS,
            fontSize: 20,
            color: C.dim,
            marginBottom: 18,
          }}
        >
          {placeholder}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "7px 12px",
              borderRadius: 999,
              backgroundColor: menu > 0.02 ? "rgba(255,255,255,0.10)" : "rgba(255,255,255,0.05)",
              border: `1px solid ${C.border}`,
            }}
          >
            <Infinity8 s={18} c={C.fg} />
            <div style={{ fontFamily: SANS, fontSize: 18, color: C.fg }}>Agent</div>
            <svg width={13} height={13} viewBox="0 0 24 24" fill="none" style={{ transform: `rotate(${menu * 180}deg)` }}>
              <title>Toggle modes</title>
              <path d="m6 15 6-6 6 6" stroke={C.fg} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ fontFamily: SANS, fontSize: 18, color: C.faint }}>Composer 1.5</div>
            <svg width={13} height={13} viewBox="0 0 24 24" fill="none">
              <title>Model</title>
              <path d="m6 9 6 6 6-6" stroke={C.faint} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
