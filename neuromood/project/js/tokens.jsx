/* tokens.jsx — Sistema unificado NeuroMood Refined
 * Toma la identidad existente (indigo/teal/violet + DM Sans) y la refina:
 *   - Saturación accent reducida ~15% para tono clínico
 *   - Borders y shadows mucho más sutiles
 *   - Tipografía con tracking ligeramente cerrado para títulos
 *   - Spacing scale 4/8/12/16/24/32/48 (mantiene compatibilidad)
 */

// ── PALETAS ──────────────────────────────────────────────────────────────────
// Paleta principal: "Refined" — versión madurada de la actual (indigo/teal/violet)
// Paleta alterna:   "Editorial" — opción 4 que elegiste (slate + dorado cálido)

const PALETTES = {
  refined: {
    light: {
      bg: "#fbfcfd",
      bgAlt: "#f4f6fa",
      surface: "#ffffff",
      elevated: "#f8fafc",
      border: "#e7ebf2",
      borderSoft: "#eef1f6",
      borderStrong: "#d8dee8",
      text: "#0b1220",
      text2: "#475569",
      text3: "#8a96a8",
      text4: "#b6c0cd",
      // Brand — desaturados respecto del original
      accent: "#5358e8",     // indigo
      accentSoft: "#eef0fe",
      teal: "#1a9f95",       // teal clínico
      tealSoft: "#e6f5f3",
      violet: "#8b5cf6",     // sparing
      violetSoft: "#f1ecfe",
      // Semánticos
      success: "#16a34a",
      successSoft: "#e7f6ec",
      warning: "#c2761a",
      warningSoft: "#fcf1df",
      danger: "#dc2626",
      dangerSoft: "#fde9e9",
      info: "#2563eb",
      // Streak (subtle)
      streak: "#d97706",
      streakSoft: "#fef4e6",
    },
    dark: {
      bg: "#0d1320",
      bgAlt: "#0b1020",
      surface: "#161d2e",
      elevated: "#1d2538",
      border: "#262e44",
      borderSoft: "#1d2538",
      borderStrong: "#33405c",
      text: "#e9edf4",
      text2: "#9aa6b8",
      text3: "#6b7791",
      text4: "#4d5670",
      accent: "#7c83ff",
      accentSoft: "#1f2240",
      teal: "#34bdb1",
      tealSoft: "#0f2c2a",
      violet: "#a87dff",
      violetSoft: "#241a3d",
      success: "#34d27a",
      successSoft: "#0f2818",
      warning: "#e8a247",
      warningSoft: "#2a1f0d",
      danger: "#f06868",
      dangerSoft: "#2a1212",
      info: "#5fa1ff",
      streak: "#f5a64a",
      streakSoft: "#2a1808",
    },
  },
  editorial: {
    light: {
      bg: "#fafaf6",
      bgAlt: "#f1efe8",
      surface: "#ffffff",
      elevated: "#f7f5ee",
      border: "#e6e2d6",
      borderSoft: "#efece2",
      borderStrong: "#d4cebd",
      text: "#1c1d22",
      text2: "#5a5c63",
      text3: "#8a8c95",
      text4: "#b7b8bf",
      accent: "#a07028",     // warm bronze
      accentSoft: "#f5ecd9",
      teal: "#3f6e62",       // sage
      tealSoft: "#e8efe9",
      violet: "#7c5d8a",
      violetSoft: "#f0ebf2",
      success: "#3f6e3f",
      successSoft: "#e8efe5",
      warning: "#a86c1a",
      warningSoft: "#f9efd6",
      danger: "#a8401f",
      dangerSoft: "#f6e3d8",
      info: "#3a5f8a",
      streak: "#a86c1a",
      streakSoft: "#f9efd6",
    },
    dark: {
      bg: "#16140f",
      bgAlt: "#100e0a",
      surface: "#1f1c15",
      elevated: "#28241b",
      border: "#3a3528",
      borderSoft: "#2b2820",
      borderStrong: "#4b4533",
      text: "#ecead8",
      text2: "#a8a48f",
      text3: "#7a7561",
      text4: "#5a5546",
      accent: "#d8a55c",
      accentSoft: "#2a2010",
      teal: "#7ba893",
      tealSoft: "#162420",
      violet: "#b698c4",
      violetSoft: "#241b2a",
      success: "#7aa07a",
      successSoft: "#16210f",
      warning: "#d8a55c",
      warningSoft: "#2a2010",
      danger: "#d6694e",
      dangerSoft: "#2a1812",
      info: "#7a9bc0",
      streak: "#d8a55c",
      streakSoft: "#2a2010",
    },
  },
};

// ── SPACING / RADIUS / SHADOWS ───────────────────────────────────────────────

const SPACE = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 };
const RADIUS = { xs: 4, sm: 6, md: 10, lg: 14, xl: 20, pill: 999 };
const SHADOW = {
  light: {
    sm:  "0 1px 2px rgba(15,23,42,.04), 0 1px 1px rgba(15,23,42,.03)",
    md:  "0 4px 12px rgba(15,23,42,.05), 0 2px 4px rgba(15,23,42,.03)",
    lg:  "0 12px 28px rgba(15,23,42,.06), 0 4px 10px rgba(15,23,42,.04)",
    glow:"0 0 0 4px rgba(83,88,232,.10)",
    inset: "inset 0 1px 0 rgba(255,255,255,.7)",
  },
  dark: {
    sm:  "0 1px 2px rgba(0,0,0,.5), 0 1px 1px rgba(0,0,0,.35)",
    md:  "0 4px 14px rgba(0,0,0,.5), 0 2px 4px rgba(0,0,0,.3)",
    lg:  "0 14px 34px rgba(0,0,0,.55), 0 6px 14px rgba(0,0,0,.35)",
    glow:"0 0 0 4px rgba(124,131,255,.18)",
    inset: "inset 0 1px 0 rgba(255,255,255,.05)",
  },
};

// ── TYPOGRAPHY ────────────────────────────────────────────────────────────────

const FONT = {
  sans: "'DM Sans', system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
  mono: "'JetBrains Mono', ui-monospace, Menlo, Consolas, monospace",
  serif: "'Fraunces', Georgia, serif", // editorial alternativa
};

// ── DEFAULT TWEAKS ────────────────────────────────────────────────────────────

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "palette": "refined",
  "mode": "light",
  "density": "normal",
  "logoStyle": "color",
  "showAudit": true
}/*EDITMODE-END*/;

// ── HELPERS ───────────────────────────────────────────────────────────────────

function getTokens(palette, mode) {
  const p = PALETTES[palette] || PALETTES.refined;
  const c = p[mode] || p.light;
  const s = SHADOW[mode] || SHADOW.light;
  return { c, s, palette, mode, SPACE, RADIUS, FONT };
}

// ── ThemeContext (React) ──────────────────────────────────────────────────────

const ThemeContext = React.createContext(getTokens("refined", "light"));
const useTheme = () => React.useContext(ThemeContext);

function ThemeProvider({ palette, mode, children }) {
  const value = React.useMemo(() => getTokens(palette, mode), [palette, mode]);
  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

// ── NM Logo (usa LOGO.png con tratamiento light en oscuro) ────────────────────
// El logo tiene un brain multicolor + wordmark "Mood" en teal.
// Para versiones claras, aplico filter: brightness para acentuar contraste.

function NMLogo({ size = 28, withWordmark = true, style: extraStyle = {} }) {
  const t = useTheme();
  const isDark = t.mode === "dark";
  const filter = isDark
    ? "brightness(1.18) saturate(.85) contrast(1.05)"
    : "none";
  return (
    <div style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 8,
      ...extraStyle,
    }}>
      <img
        src="assets/LOGO.png"
        alt="NeuroMood"
        style={{
          height: size,
          width: "auto",
          filter,
          imageRendering: "auto",
        }}
      />
    </div>
  );
}

// Mini-glifo (solo brain, sin wordmark) — para favicons, app icons en UI
function NMGlyph({ size = 24, tone = "accent" }) {
  const t = useTheme();
  const color = t.c[tone] || t.c.accent;
  // Brain abstracto reducido a dots+lines en SVG (simple, geométrico)
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" style={{ display: "block" }}>
      <circle cx="9" cy="11" r="1.8" fill={color} />
      <circle cx="16" cy="7"  r="1.8" fill={color} opacity=".85"/>
      <circle cx="23" cy="11" r="1.8" fill={color} />
      <circle cx="11" cy="20" r="1.8" fill={color} opacity=".7"/>
      <circle cx="21" cy="20" r="1.8" fill={color} opacity=".7"/>
      <circle cx="16" cy="25" r="1.8" fill={color} opacity=".55"/>
      <path d="M9 11 L16 7 L23 11 M9 11 L11 20 L16 25 L21 20 L23 11 M16 7 L16 25"
            stroke={color} strokeWidth="1.2" fill="none" strokeLinecap="round"
            opacity=".55"/>
    </svg>
  );
}

// Expose to other scripts
Object.assign(window, {
  PALETTES, SPACE, RADIUS, SHADOW, FONT, TWEAK_DEFAULTS,
  getTokens, ThemeContext, useTheme, ThemeProvider, NMLogo, NMGlyph,
});
