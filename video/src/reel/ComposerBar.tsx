import { interpolate } from "remotion";
import { C, EASE_OUT } from "./theme";
import { MONO, SANS } from "../shared/fonts";

/**
 * Design ported from 21st.dev's `AiPromptInput` by @senommu ("Premium AI prompt
 * composer with rotating placeholders, floating toolbar, and Cursor-style model
 * selector").
 *
 * The original is ~2600 lines of framer-motion: spring presets, `AnimatePresence`,
 * `useReducedMotion`, controlled React state for every open/close. None of that
 * survives a Remotion render, where each frame is rasterised in isolation. What
 * carries over is the *layout and surface language* — the heavy `rounded-[1.75rem]`
 * two-pixel-bordered shell, the removable tool chips above the field, the toolbar
 * fenced off by a top border with icon buttons left and send right, and the model
 * pill that splits a model name from its modifiers ("Opus 4.5" · "High" · "Fast").
 * Every open/close here is instead a 0→1 number the caller derives from the frame.
 *
 * Drawn at a fixed intrinsic width so one design serves both shots; callers scale
 * it with `Composer`, below.
 */
export const INTRINSIC = 1000;

const Plus: React.FC<{ s: number; c: string }> = ({ s, c }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <title>Add context</title>
    <path d="M12 5v14M5 12h14" stroke={c} strokeWidth={2} strokeLinecap="round" />
  </svg>
);

const Telescope: React.FC<{ s: number; c: string }> = ({ s, c }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <title>Deep research</title>
    <path
      d="m3.5 13.5 12-7.5 3 4.5-12 7.5-3-4.5ZM10 16.5 8.5 21M14 14l2.5 4.5"
      stroke={c}
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const Globe: React.FC<{ s: number; c: string }> = ({ s, c }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <title>Web search</title>
    <circle cx="12" cy="12" r="8.5" stroke={c} strokeWidth={1.7} />
    <path d="M3.5 12h17M12 3.5c2.2 2.4 3.2 5.4 3.2 8.5s-1 6.1-3.2 8.5c-2.2-2.4-3.2-5.4-3.2-8.5S9.8 5.9 12 3.5Z" stroke={c} strokeWidth={1.7} />
  </svg>
);

const Mic: React.FC<{ s: number; c: string }> = ({ s, c }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <title>Dictate</title>
    <rect x="9" y="3" width="6" height="11" rx="3" stroke={c} strokeWidth={1.8} />
    <path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3" stroke={c} strokeWidth={1.8} strokeLinecap="round" />
  </svg>
);

const ArrowUp: React.FC<{ s: number; c: string }> = ({ s, c }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <title>Send</title>
    <path d="M12 20V5m0 0-6.5 6.5M12 5l6.5 6.5" stroke={c} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const Check: React.FC<{ s: number; c: string }> = ({ s, c }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <title>Selected</title>
    <path d="m5 12.5 4.5 4.5L19 7" stroke={c} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

/** Trimmed from the component's `DEFAULT_AI_MODELS`. */
const MODELS = [
  { label: "Opus 4.5", desc: "Powerful reasoning for complex agentic work.", ctx: "200K" },
  { label: "Cursor Grok 4.5", desc: "Fast, tuned for coding workflows.", ctx: "128K" },
  { label: "GPT-5", desc: "General reasoning, strong code generation.", ctx: "400K" },
  { label: "Gemini 2.5", desc: "Long context for large repositories.", ctx: "1M" },
];

/** A removable tool chip — `CHIP_SURFACE_CLASS` in the original. */
const ToolChip: React.FC<{
  label: string;
  Icon: React.FC<{ s: number; c: string }>;
  t: number;
}> = ({ label, Icon, t }) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 9,
      height: 40,
      padding: "0 16px",
      borderRadius: 999,
      backgroundColor: "rgba(255,255,255,0.07)",
      boxShadow: "inset 0 0 0 1px rgba(123,123,123,0.20)",
      opacity: t,
      transform: `scale(${interpolate(t, [0, 1], [0.86, 1])})`,
      transformOrigin: "left center",
    }}
  >
    <Icon s={19} c={C.dim} />
    <div style={{ fontFamily: SANS, fontSize: 19, fontWeight: 500, color: C.fg }}>{label}</div>
  </div>
);

/** `TOOLBAR_BTN_CLASS` — a 36px square in the original, scaled up here. */
const ToolBtn: React.FC<{
  Icon: React.FC<{ s: number; c: string }>;
  active?: boolean;
}> = ({ Icon, active = false }) => (
  <div
    style={{
      width: 48,
      height: 48,
      borderRadius: 15,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      backgroundColor: active ? "rgba(255,255,255,0.08)" : "transparent",
    }}
  >
    <Icon s={23} c={active ? C.fg : C.dim} />
  </div>
);

export const ComposerBar: React.FC<{
  /** 0 = model menu closed, 1 = fully open. */
  menu?: number;
  /** Which model row the cursor rests on as the menu opens. */
  hovered?: number;
  /** Prompt text; empty renders the placeholder instead. */
  prompt?: string;
  /** 0→1 reveal for the tool chips above the field. */
  chips?: number;
}> = ({ menu = 0, hovered = 0, prompt = "", chips = 1 }) => {
  const rowH = 76;

  return (
    <div style={{ position: "relative", width: INTRINSIC }}>
      {/* Model selector, opening upward — `<ModelSelectorContent side="top" />`. */}
      {menu > 0.001 ? (
        <div
          style={{
            position: "absolute",
            left: 18,
            bottom: "100%",
            marginBottom: 14,
            width: 520,
            padding: 8,
            borderRadius: 24,
            backgroundColor: "rgba(24,24,27,0.98)",
            border: `2px solid ${C.border}`,
            boxShadow: "0 8px 40px -8px rgba(0,0,0,0.75), 0 2px 10px -2px rgba(0,0,0,0.5)",
            transformOrigin: "left bottom",
            opacity: interpolate(menu, [0, 0.3], [0, 1], { extrapolateRight: "clamp" }),
            transform: `translateY(${interpolate(menu, [0, 1], [16, 0])}px) scale(${interpolate(
              menu,
              [0, 1],
              [0.93, 1],
            )})`,
          }}
        >
          {MODELS.map((m, i) => {
            const reveal = interpolate(menu, [0.12 + i * 0.11, 0.44 + i * 0.11], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: EASE_OUT,
            });
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
                  borderRadius: 15,
                  opacity: reveal,
                  backgroundColor: on ? "rgba(255,255,255,0.07)" : "transparent",
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: SANS, fontSize: 21, fontWeight: 500, color: on ? C.fg : C.dim }}>
                    {m.label}
                  </div>
                  <div
                    style={{
                      fontFamily: SANS,
                      fontSize: 16,
                      color: C.faint,
                      marginTop: 3,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {m.desc}
                  </div>
                </div>
                <div style={{ fontFamily: MONO, fontSize: 15, color: C.faint }}>{m.ctx}</div>
                {i === 0 ? <Check s={19} c={C.fg} /> : <div style={{ width: 19 }} />}
              </div>
            );
          })}
        </div>
      ) : null}

      {/* Shell — `rounded-[1.75rem] border-2 p-4`. */}
      <div
        style={{
          borderRadius: 34,
          border: `2px solid ${C.border}`,
          background: "linear-gradient(180deg, rgba(255,255,255,0.085), rgba(255,255,255,0.028))",
          padding: 26,
          boxShadow: "0 2px 8px rgba(0,0,0,0.28), 0 18px 52px -12px rgba(0,0,0,0.6)",
        }}
      >
        {chips > 0.001 ? (
          <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
            <ToolChip label="Deep research" Icon={Telescope} t={chips} />
            <ToolChip
              label="Web search"
              Icon={Globe}
              t={interpolate(chips, [0.25, 1], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })}
            />
          </div>
        ) : null}

        <div
          style={{
            fontFamily: SANS,
            fontSize: 30,
            lineHeight: 1.5,
            color: prompt.length > 0 ? C.fg : C.faint,
            minHeight: 46,
          }}
        >
          {prompt.length > 0 ? prompt : "Ask anything…"}
        </div>

        {/* Toolbar, fenced by a top border — `border-t mt-3.5 pt-3`. */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            marginTop: 24,
            paddingTop: 22,
            borderTop: `1px solid ${C.border}`,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 4, minWidth: 0 }}>
            <ToolBtn Icon={Plus} />
            <ToolBtn Icon={Telescope} active />
            <ToolBtn Icon={Globe} active />

            {/* Model pill: name, then muted modifiers — `ModelLabelParts`. */}
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: 10,
                height: 48,
                padding: "0 16px",
                marginLeft: 6,
                borderRadius: 15,
                backgroundColor: menu > 0.02 ? "rgba(255,255,255,0.09)" : "transparent",
              }}
            >
              <span style={{ fontFamily: SANS, fontSize: 21, fontWeight: 500, color: C.fg, alignSelf: "center" }}>
                Opus 4.5
              </span>
              <span style={{ fontFamily: SANS, fontSize: 19, fontWeight: 500, color: C.faint, alignSelf: "center" }}>
                High
              </span>
              <span style={{ fontFamily: SANS, fontSize: 19, fontWeight: 500, color: C.faint, alignSelf: "center" }}>
                Fast
              </span>
              <svg
                width={15}
                height={15}
                viewBox="0 0 24 24"
                fill="none"
                style={{ alignSelf: "center", transform: `rotate(${menu * 180}deg)` }}
              >
                <title>Choose model</title>
                <path d="m6 15 6-6 6 6" stroke={C.dim} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
            <ToolBtn Icon={Mic} />
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 15,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: C.fg,
              }}
            >
              <ArrowUp s={23} c={C.ink} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Scales the fixed-width composer to whatever a shot needs, reserving the right
 * layout height so it can sit in a flex column. Both shots therefore show the
 * same object at two distances rather than two separately-tuned designs.
 */
export const Composer: React.FC<{
  width: number;
  menu?: number;
  hovered?: number;
  prompt?: string;
  chips?: number;
  /** Intrinsic height, measured once; used to reserve space after scaling. */
  height?: number;
}> = ({ width, height = 250, ...rest }) => {
  const s = width / INTRINSIC;
  return (
    <div style={{ width, height: height * s, position: "relative" }}>
      <div style={{ transform: `scale(${s})`, transformOrigin: "top left", position: "absolute", top: 0, left: 0 }}>
        <ComposerBar {...rest} />
      </div>
    </div>
  );
};
