/* v3-kit.jsx — Sistema "NeuroMood Final" alineado a las referencias del usuario
 * - Gradiente firma teal→violet
 * - Light: blancos cool con sombras suaves
 * - Dark: navy profundo con glow cyan/violet
 * - Logo N estilizado en curvas
 */

// ── Tokens v3 ────────────────────────────────────────────────────────────────
const V3_LIGHT = {
  bg: "#eef2f8",
  bgAlt: "#e6ecf5",
  bgSidebar: "#ffffff",
  surface: "#ffffff",
  elevated: "#f5f7fb",
  border: "#e3e9f1",
  borderSoft: "#eef1f6",
  borderStrong: "#cdd5e2",
  text: "#0f172a",
  text2: "#475569",
  text3: "#94a3b8",
  text4: "#cbd5e1",
  // Brand signature
  gradFrom: "#2dd4bf",
  gradMid:  "#5eead4",
  gradTo:   "#a855f7",
  moodGradFrom: "#2dd4bf",
  moodGradMid:  "#5eead4",
  moodGradTo:   "#a855f7",
  teal: "#14b8a6",
  tealSoft: "#d3f5ef",
  violet: "#a855f7",
  violetSoft: "#ede5fc",
  cyan: "#06b6d4",
  cyanSoft: "#cef3f9",
  // Semantic
  success: "#10b981",
  successSoft: "#d1fae5",
  warning: "#f59e0b",
  warningSoft: "#fef3c7",
  danger: "#ef4444",
  dangerSoft: "#fee2e2",
  // Mood face colors
  moodLow:   "#60a5fa", // muy triste
  moodMid:   "#fbbf24", // neutral
  moodHigh:  "#34d399", // feliz
  moodSuper: "#a78bfa", // muy feliz
  // Streak
  streak: "#f97316",
  streakSoft: "#ffedd5",
};

const V3_DARK = {
  bg: "#060912",
  bgAlt: "#0a0f1f",
  bgSidebar: "#0a0f1f",
  surface: "rgba(18, 25, 45, 0.7)",
  surfaceSolid: "#121c2d",
  elevated: "rgba(30, 41, 65, 0.6)",
  border: "rgba(94, 234, 212, 0.10)",
  borderSoft: "rgba(255, 255, 255, 0.06)",
  borderStrong: "rgba(94, 234, 212, 0.25)",
  text: "#f1f5f9",
  text2: "#94a3b8",
  text3: "#64748b",
  text4: "#475569",
  gradFrom: "#22d3ee",
  gradMid:  "#5eead4",
  gradTo:   "#c084fc",
  // Mood slashbar conserva la paleta original también en dark
  moodGradFrom: "#22d3ee",
  moodGradMid:  "#5eead4",
  moodGradTo:   "#c084fc",
  teal: "#5eead4",
  tealSoft: "rgba(20, 184, 166, 0.18)",
  violet: "#c084fc",
  violetSoft: "rgba(168, 85, 247, 0.20)",
  cyan: "#22d3ee",
  cyanSoft: "rgba(6, 182, 212, 0.18)",
  success: "#34d399",
  successSoft: "rgba(16, 185, 129, 0.20)",
  warning: "#fbbf24",
  warningSoft: "rgba(245, 158, 11, 0.20)",
  danger: "#f87171",
  dangerSoft: "rgba(239, 68, 68, 0.20)",
  moodLow:   "#60a5fa",
  moodMid:   "#fbbf24",
  moodHigh:  "#34d399",
  moodSuper: "#a78bfa",
  streak: "#fb923c",
  streakSoft: "rgba(249, 115, 22, 0.18)",
};

const V3_FONT = {
  sans: "'Plus Jakarta Sans', 'DM Sans', system-ui, sans-serif",
  display: "'Plus Jakarta Sans', 'DM Sans', system-ui, sans-serif",
  mono: "'JetBrains Mono', ui-monospace, monospace",
};

function useV3(mode) {
  return mode === "dark" ? V3_DARK : V3_LIGHT;
}

// Convenience hook → returns { c, mode, isDark }
const V3Context = React.createContext({ c: V3_LIGHT, mode: "light", isDark: false });
const useV3Theme = () => React.useContext(V3Context);

function V3Provider({ mode, children }) {
  const value = React.useMemo(() => ({
    c: useV3(mode),
    mode,
    isDark: mode === "dark",
  }), [mode]);
  return <V3Context.Provider value={value}>{children}</V3Context.Provider>;
}

// ── Logo: usa LOGO.png con glow filter en dark ────────────────────────────────
function V3Logo({ size = 32, withWordmark = true, asIcon = false }) {
  const { c, isDark } = useV3Theme();
  // Asset paths
  const fullSrc = isDark ? "assets/logos-dark.png" : "assets/logos-light.png";
  const iconSrc = isDark ? "assets/logos-icon-dark.png" : "assets/logos-icon-light.png";
  // Glow filter: light suave, dark con doble glow teal+violet
  const filterLight = "drop-shadow(0 2px 4px rgba(15,23,42,.10))";
  const filterDark  = "drop-shadow(0 0 8px rgba(94,234,212,.45)) drop-shadow(0 0 14px rgba(168,85,247,.30))";
  if (asIcon) {
    return (
      <img src={iconSrc} alt="NeuroMood"
           style={{
             height: size, width: size, display: "block",
             objectFit: "contain",
             filter: isDark ? filterDark : filterLight,
             transition: "filter .35s ease",
           }}/>
    );
  }
  return (
    <img src={fullSrc} alt="NeuroMood"
         style={{
           height: size, width: "auto", display: "block",
           filter: isDark ? filterDark : filterLight,
           transition: "filter .35s ease",
         }}/>
  );
}

// ── AppShell: window con sidebar + main ───────────────────────────────────────
function V3Shell({ children, sidebar, width = 1280, height = 820, mode = "light",
                   defaultMode = null, ambient = "teal-violet" }) {
  // Si defaultMode se setea, el shell es stateful (toggle interno funciona).
  // Si no, queda fijo al `mode` prop (para mostrar light+dark side-by-side).
  const [internalMode, setInternalMode] = React.useState(defaultMode || mode);
  const isStateful = defaultMode !== null;
  const currentMode = isStateful ? internalMode : mode;
  const setMode = isStateful ? setInternalMode : null;
  return (
    <V3Provider mode={currentMode}>
      <V3ShellInner width={width} height={height} sidebar={sidebar}
                    mode={currentMode} setMode={setMode} ambient={ambient}>
        {children}
      </V3ShellInner>
    </V3Provider>
  );
}

function V3ShellInner({ children, sidebar, width, height, mode, setMode, ambient }) {
  const { c, isDark } = useV3Theme();
  // Ambient glow positions per palette
  const glows = {
    "teal-violet": [
      ["15% 12%", c.teal,   isDark ? .25 : .12],
      ["85% 18%", c.violet, isDark ? .22 : .10],
      ["50% 85%", c.cyan,   isDark ? .18 : .06],
    ],
    "warm": [
      ["20% 15%", "#fbbf24", isDark ? .20 : .10],
      ["80% 85%", c.violet,  isDark ? .18 : .08],
    ],
  };
  const bgLayers = (glows[ambient] || glows["teal-violet"])
    .map(([pos, col, op]) => `radial-gradient(circle at ${pos}, ${col}${Math.round(op*255).toString(16).padStart(2,"0")}, transparent 50%)`)
    .join(", ");
  return (
    <div style={{
      width, height,
      borderRadius: 16,
      background: isDark
        ? "linear-gradient(135deg, #0a0d1a 0%, #060912 100%)"
        : "linear-gradient(135deg, #f5f8fc 0%, #e8eef7 100%)",
      boxShadow: isDark
        ? "0 30px 80px -20px rgba(0,0,0,.6), 0 0 0 1px rgba(94,234,212,.08)"
        : "0 30px 80px -20px rgba(15,23,42,.15), 0 0 0 1px rgba(15,23,42,.04)",
      border: isDark ? "1px solid rgba(94,234,212,.08)" : "1px solid rgba(15,23,42,.04)",
      overflow: "hidden",
      display: "grid",
      gridTemplateRows: "auto 1fr",
      fontFamily: V3_FONT.sans,
      color: c.text,
      position: "relative",
      transition: "background .35s ease, color .35s ease, border-color .35s ease, box-shadow .35s ease",
    }}>
      {/* Ambient bg glow blobs */}
      <div style={{
        position: "absolute", inset: 0,
        background: bgLayers,
        pointerEvents: "none",
        transition: "opacity .35s ease",
      }}/>
      {/* Window titlebar (compact, minimal — Win11 style) */}
      <div style={{
        height: 44,
        padding: "0 12px 0 16px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "relative",
      }}>
        <V3Logo size={20} asIcon withWordmark={false}/>
        <div style={{ display: "flex", gap: 4 }}>
          {[
            <path key="m" d="M2 7h10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>,
            <rect key="x" x="2.5" y="2.5" width="9" height="9" rx="1" stroke="currentColor" strokeWidth="1.3" fill="none"/>,
            <path key="c" d="M3 3l8 8M11 3l-8 8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>,
          ].map((p, i) => (
            <div key={i} style={{
              width: 32, height: 28, borderRadius: 4,
              display: "flex", alignItems: "center", justifyContent: "center",
              color: c.text3,
              background: "transparent",
            }}>
              <svg width="14" height="14" viewBox="0 0 14 14">{p}</svg>
            </div>
          ))}
        </div>
      </div>
      <div style={{
        display: "grid",
        gridTemplateColumns: sidebar ? "240px 1fr" : "1fr",
        height: "100%",
        overflow: "hidden",
        position: "relative",
      }}>
        {sidebar && (
          <div style={{
            background: c.bgSidebar,
            borderRight: isDark ? "1px solid rgba(94,234,212,.08)" : "1px solid #e8edf5",
            overflow: "hidden",
            display: "flex",
            flexDirection: "column",
            position: "relative",
            transition: "background .35s ease, border-color .35s ease",
          }}>
            {/* pasamos setMode al sidebar/header vía context */}
            <V3ModeContext.Provider value={{ mode, setMode }}>
              {sidebar}
            </V3ModeContext.Provider>
          </div>
        )}
        <div style={{ overflow: "hidden", position: "relative" }}>
          <V3ModeContext.Provider value={{ mode, setMode }}>
            {children}
          </V3ModeContext.Provider>
        </div>
      </div>
    </div>
  );
}

// Context para que ThemeToggle interno acceda al setMode del shell
const V3ModeContext = React.createContext({ mode: "light", setMode: null });

// ── Sidebar nav ──────────────────────────────────────────────────────────────
function V3Sidebar({ active = "inicio", appName = "NeuroMood", role = null, proCard = true,
                     items = null }) {
  const { c, isDark } = useV3Theme();
  const navIcon = (name, color) => {
    const props = { width: 18, height: 18, viewBox: "0 0 18 18", fill: "none",
                    stroke: color, strokeWidth: 1.6, strokeLinecap: "round", strokeLinejoin: "round" };
    switch (name) {
      case "inicio":      return <svg {...props}><path d="M3 8l6-5 6 5v7a1 1 0 0 1-1 1h-3v-5h-4v5H4a1 1 0 0 1-1-1V8z"/></svg>;
      case "animo":       return <svg {...props}><circle cx="9" cy="9" r="6.5"/><circle cx="6.5" cy="7.5" r=".5" fill={color}/><circle cx="11.5" cy="7.5" r=".5" fill={color}/><path d="M6 11.5c1.5 1.5 4.5 1.5 6 0"/></svg>;
      case "respiracion": return <svg {...props}><path d="M3 8c2 0 3-2 3-3M9 9c0-3-2-5-5-5M15 8c-2 0-3-2-3-3M9 9c0-3 2-5 5-5M9 9c0 3-2 5-5 5M9 9c0 3 2 5 5 5"/></svg>;
      case "tcc":         return <svg {...props}><path d="M6 3a3 3 0 0 0-3 3v2c0 1.5 1 2.5 1 4v2a2 2 0 0 0 2 2"/><path d="M12 3a3 3 0 0 1 3 3v2c0 1.5-1 2.5-1 4v2a2 2 0 0 1-2 2"/><path d="M7 7c1 0 2 .5 2 2c0-1.5 1-2 2-2"/></svg>;
      case "rutina":      return <svg {...props}><rect x="3" y="4" width="12" height="11" rx="1.5"/><path d="M6 2v4M12 2v4M3 8h12"/><path d="M6 11l1.5 1.5L11 9"/></svg>;
      case "actividades": return <svg {...props}><path d="M9 2l1.8 4 4.2.4-3.2 2.8 1 4.4L9 11.5l-3.8 2.1 1-4.4L3 6.4 7.2 6z"/></svg>;
      case "timer":       return <svg {...props}><circle cx="9" cy="10" r="6"/><path d="M9 10V6.5M7 2.5h4"/></svg>;
      case "avisos":      return <svg {...props}><path d="M4.5 7a4.5 4.5 0 0 1 9 0c0 4 1.5 5 1.5 5h-12s1.5-1 1.5-5z"/><path d="M7 14.5a2 2 0 0 0 4 0"/></svg>;
      case "perfil":      return <svg {...props}><circle cx="9" cy="6.5" r="3"/><path d="M3 15c0-3 2.5-5 6-5s6 2 6 5"/></svg>;
      case "config":      return <svg {...props}><circle cx="9" cy="9" r="2.5"/><path d="M9 1.5v2M9 14.5v2M1.5 9h2M14.5 9h2M3.5 3.5l1.4 1.4M13.1 13.1l1.4 1.4M3.5 14.5l1.4-1.4M13.1 4.9l1.4-1.4"/></svg>;
      case "dashboard":   return <svg {...props}><rect x="2.5" y="2.5" width="6" height="7" rx="1"/><rect x="2.5" y="11" width="6" height="4.5" rx="1"/><rect x="9.5" y="2.5" width="6" height="4.5" rx="1"/><rect x="9.5" y="9" width="6" height="6.5" rx="1"/></svg>;
      case "pacientes":   return <svg {...props}><circle cx="7" cy="6.5" r="2.5"/><path d="M2.5 15c0-2.5 2-4.5 4.5-4.5s4.5 2 4.5 4.5"/><circle cx="13" cy="8" r="2"/><path d="M11.5 15c0-1.5 1.5-3 3-3"/></svg>;
      case "ia":          return <svg {...props}><path d="M4 4h10v6H8l-3 2.5V10H4V4z"/><circle cx="6.5" cy="7" r=".7" fill={color}/><circle cx="11.5" cy="7" r=".7" fill={color}/></svg>;
      case "terapias":    return <svg {...props}><path d="M9 2 L3 5 L9 8 L15 5 Z"/><path d="M3 9 L9 12 L15 9"/><path d="M3 13 L9 16 L15 13"/></svg>;
      case "reportes":    return <svg {...props}><rect x="3" y="2" width="12" height="14" rx="1.5"/><path d="M6 6h6M6 9h6M6 12h4"/></svg>;
      case "exportar":    return <svg {...props}><path d="M9 2v9M5 8l4 4 4-4M3 14h12"/></svg>;
      case "mood":        return <svg {...props}><circle cx="9" cy="9" r="6.5"/><circle cx="6.5" cy="7.5" r=".5" fill={color}/><circle cx="11.5" cy="7.5" r=".5" fill={color}/><path d="M6 11.5c1.5 1.5 4.5 1.5 6 0"/></svg>;
    }
    return <svg {...props}><circle cx="9" cy="9" r="3"/></svg>;
  };

  const def = items || [
    { id: "inicio",      label: "Inicio" },
    { id: "animo",       label: "Ánimo" },
    { id: "respiracion", label: "Respiración" },
    { id: "tcc",         label: "TCC" },
    { id: "rutina",      label: "Rutina" },
    { id: "actividades", label: "Actividades" },
    { id: "timer",       label: "Timer" },
    { id: "avisos",      label: "Avisos" },
    { id: "perfil",      label: "Perfil" },
    { id: "config",      label: "Configuración" },
  ];

  return (
    <>
      {/* Logo header — sin fondo neuronal, icono grande limpio */}
      <div style={{ padding: "16px 16px 14px", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <V3Logo size={48}/>
      </div>
      {role && (
        <div style={{ padding: "0 24px 12px", textAlign: "center" }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: c.text3, letterSpacing: ".15em", textTransform: "uppercase" }}>
            {role}
          </span>
        </div>
      )}

      {/* Nav */}
      <div style={{ padding: "0 12px", flex: 1, overflow: "auto" }}>
        {def.map(it => {
          const a = it.id === active;
          return (
            <div key={it.id} style={{
              display: "flex", alignItems: "center", gap: 12,
              padding: "11px 14px",
              borderRadius: 12,
              background: a ? (isDark ? c.tealSoft : c.tealSoft) : "transparent",
              color: a ? (isDark ? c.teal : c.teal) : c.text2,
              fontSize: 14, fontWeight: a ? 600 : 500,
              marginBottom: 2,
              cursor: "pointer",
              position: "relative",
              border: a && isDark ? `1px solid ${c.borderStrong}` : "1px solid transparent",
            }}>
              {navIcon(it.id, a ? c.teal : c.text2)}
              <span>{it.label}</span>
            </div>
          );
        })}
      </div>

      {/* Pro upsell */}
      {proCard && (
        <div style={{ padding: 14 }}>
          <div style={{
            padding: 16, borderRadius: 16,
            background: isDark
              ? "linear-gradient(135deg, rgba(34,211,238,.15), rgba(168,85,247,.15))"
              : "linear-gradient(135deg, rgba(94,234,212,.18), rgba(168,85,247,.12))",
            border: `1px solid ${isDark ? "rgba(94,234,212,.25)" : "rgba(168,85,247,.18)"}`,
            position: "relative",
            overflow: "hidden",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 1l2 4 5 .5-3.5 3.5L13 14l-5-3-5 3 1.5-5L1 5.5 6 5z"
                      fill="url(#proGrad)"/>
                <defs>
                  <linearGradient id="proGrad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor={c.teal}/>
                    <stop offset="100%" stopColor={c.violet}/>
                  </linearGradient>
                </defs>
              </svg>
              <span style={{ fontSize: 13, fontWeight: 700, color: c.text }}>{appName} Pro</span>
            </div>
            <div style={{ fontSize: 11, color: c.text2, lineHeight: 1.5, marginBottom: 12 }}>
              Desbloquea todas las herramientas y contenidos premium.
            </div>
            <V3Button size="sm" fullWidth gradient>Mejorar ahora</V3Button>
          </div>
        </div>
      )}
    </>
  );
}

// ── Header con título + chip racha + theme toggle + perfil ───────────────────
function V3Header({ title, subtitle, streak = null, mode, onToggleMode,
                    name = "Ana García", role = "Paciente", avatar = null,
                    actions = null }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{
      padding: "22px 28px 14px",
      display: "grid",
      gridTemplateColumns: "1fr auto",
      alignItems: "center",
      gap: 16,
    }}>
      <div>
        <div style={{
          fontSize: 30, fontWeight: 700,
          letterSpacing: "-.02em",
          color: c.text,
          lineHeight: 1.15,
          display: "flex", alignItems: "center", gap: 10,
        }}>
          {title}
        </div>
        {subtitle && (
          <div style={{ fontSize: 13, color: c.text2, marginTop: 4 }}>{subtitle}</div>
        )}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {actions}
        {streak !== null && (
          <div style={{
            padding: "10px 14px",
            borderRadius: 14,
            background: c.surface,
            border: `1px solid ${c.borderSoft}`,
            display: "flex", alignItems: "center", gap: 10,
            boxShadow: isDark ? "0 0 0 1px rgba(94,234,212,.05)" : "0 2px 8px rgba(15,23,42,.04)",
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: 999,
              background: c.streakSoft,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 16,
            }}>🔥</div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: c.text }}>{streak} días</div>
              <div style={{ fontSize: 10, color: c.text3 }}>Racha actual</div>
            </div>
          </div>
        )}
        <ThemeToggle mode={mode} onToggleMode={onToggleMode}/>
        <div style={{
          padding: "8px 14px 8px 8px",
          borderRadius: 14,
          background: c.surface,
          border: `1px solid ${c.borderSoft}`,
          display: "flex", alignItems: "center", gap: 10,
          boxShadow: isDark ? "0 0 0 1px rgba(94,234,212,.05)" : "0 2px 8px rgba(15,23,42,.04)",
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: 999,
            background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
            color: "#fff", fontWeight: 700, fontSize: 13,
            display: "flex", alignItems: "center", justifyContent: "center",
            position: "relative",
          }}>
            {avatar || name.split(" ").map(n => n[0]).slice(0, 2).join("")}
            <span style={{
              position: "absolute", bottom: 0, right: 0,
              width: 10, height: 10, borderRadius: 999,
              background: c.success,
              border: `2px solid ${c.surface}`,
            }}/>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: c.text }}>{name}</div>
            <div style={{ fontSize: 10, color: c.text3 }}>{role}</div>
          </div>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M3 4.5L6 7.5L9 4.5" stroke={c.text3} strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>
    </div>
  );
}

function ThemeToggle({ mode, onToggleMode }) {
  const { c, isDark } = useV3Theme();
  // Si no se pasa onToggleMode, usar el del V3ModeContext (toggle interno del shell)
  const ctx = React.useContext(V3ModeContext);
  const toggle = onToggleMode || (() => ctx.setMode && ctx.setMode(ctx.mode === "dark" ? "light" : "dark"));
  return (
    <div onClick={toggle} style={{
      padding: "8px 12px",
      borderRadius: 14,
      background: c.surface,
      border: `1px solid ${c.borderSoft}`,
      display: "flex", alignItems: "center", gap: 8,
      cursor: "pointer",
      boxShadow: isDark ? "0 0 0 1px rgba(94,234,212,.05)" : "0 2px 8px rgba(15,23,42,.04)",
      transition: "background .35s ease, border-color .35s ease, box-shadow .35s ease",
    }}>
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ transition: "transform .35s ease" }}>
        {isDark ? (
          <path d="M11.5 8.5A4.5 4.5 0 0 1 5.5 2.5a5 5 0 1 0 6 6z" fill={c.teal} opacity=".9"/>
        ) : (
          <>
            <circle cx="7" cy="7" r="3" stroke={c.text2} strokeWidth="1.3"/>
            {[0,45,90,135,180,225,270,315].map(a => (
              <line key={a} x1="7" y1="1.5" x2="7" y2="2.8" stroke={c.text2} strokeWidth="1.3" strokeLinecap="round" transform={`rotate(${a} 7 7)`}/>
            ))}
          </>
        )}
      </svg>
      <div style={{
        width: 36, height: 20, borderRadius: 999,
        background: isDark ? `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})` : "#cbd5e1",
        position: "relative",
        transition: "background .35s ease",
      }}>
        <div style={{
          position: "absolute",
          top: 2, left: isDark ? 18 : 2,
          width: 16, height: 16, borderRadius: 999,
          background: "#fff",
          boxShadow: "0 1px 3px rgba(0,0,0,.2)",
          transition: "left .35s ease",
        }}/>
      </div>
    </div>
  );
}

// ── V3 Card ──────────────────────────────────────────────────────────────────
function V3Card({ children, padding = 22, style = {}, glow = false, interactive = false }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{
      background: isDark ? c.surfaceSolid : c.surface,
      borderRadius: 18,
      border: `1px solid ${c.borderSoft}`,
      padding,
      boxShadow: isDark
        ? (glow ? "0 0 0 1px rgba(94,234,212,.15), 0 0 40px -10px rgba(94,234,212,.18)" : "0 0 0 1px rgba(255,255,255,.03)")
        : "0 1px 3px rgba(15,23,42,.04), 0 4px 16px -4px rgba(15,23,42,.06)",
      position: "relative",
      transition: "background .35s ease, border-color .35s ease, box-shadow .35s ease, color .35s ease",
      ...(isDark && {
        backdropFilter: "blur(10px) saturate(1.2)",
        background: glow
          ? "linear-gradient(135deg, rgba(20,28,48,.85), rgba(15,22,40,.75))"
          : "rgba(18,28,45,.7)",
      }),
      ...style,
    }}>
      {children}
    </div>
  );
}

// ── V3 Button (gradient pill style) ───────────────────────────────────────────
function V3Button({ children, gradient = false, variant = "secondary", size = "md",
                    fullWidth = false, icon = null, onClick, style = {} }) {
  const { c, isDark } = useV3Theme();
  const sizes = {
    sm: { px: 14, h: 32, fs: 12 },
    md: { px: 18, h: 40, fs: 13 },
    lg: { px: 24, h: 48, fs: 14 },
  };
  const s = sizes[size];
  const baseStyle = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    width: fullWidth ? "100%" : "auto",
    height: s.h,
    padding: `0 ${s.px}px`,
    borderRadius: 999,
    fontSize: s.fs,
    fontWeight: 600,
    fontFamily: V3_FONT.sans,
    cursor: "pointer",
    border: "none",
    transition: "all .15s ease",
    letterSpacing: ".005em",
    ...style,
  };
  if (gradient) {
    Object.assign(baseStyle, {
      background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
      color: "#fff",
      boxShadow: `0 8px 20px -6px ${c.teal}66, 0 4px 12px -2px ${c.violet}44`,
    });
  } else if (variant === "primary") {
    Object.assign(baseStyle, {
      background: c.teal,
      color: "#fff",
      boxShadow: `0 4px 12px -2px ${c.teal}55`,
    });
  } else if (variant === "secondary") {
    Object.assign(baseStyle, {
      background: c.surface,
      color: c.text,
      border: `1px solid ${c.border}`,
      boxShadow: isDark ? "none" : "0 1px 2px rgba(15,23,42,.04)",
    });
  } else if (variant === "ghost") {
    Object.assign(baseStyle, {
      background: "transparent",
      color: c.text2,
    });
  }
  return (
    <button onClick={onClick} style={baseStyle}>
      {icon}
      {children}
    </button>
  );
}

// ── V3 Ring (gradient progress) ──────────────────────────────────────────────
function V3Ring({ pct = 0, size = 120, stroke = 10, value = null, sub = null,
                  showGlow = false }) {
  const { c, isDark } = useV3Theme();
  const r = (size - stroke) / 2;
  const C = 2 * Math.PI * r;
  const dash = (pct / 100) * C;
  const id = `ring${Math.random().toString(36).slice(2, 7)}`;
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: "rotate(-90deg)" }}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%"   stopColor={c.gradFrom}/>
            <stop offset="50%"  stopColor={c.gradMid}/>
            <stop offset="100%" stopColor={c.gradTo}/>
          </linearGradient>
          {(isDark || showGlow) && (
            <filter id={`${id}-glow`}>
              <feGaussianBlur stdDeviation="3" result="blur"/>
              <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          )}
        </defs>
        <circle cx={size/2} cy={size/2} r={r}
                stroke={isDark ? "rgba(255,255,255,.06)" : "#e8edf5"}
                strokeWidth={stroke} fill="none"/>
        <circle cx={size/2} cy={size/2} r={r}
                stroke={`url(#${id})`}
                strokeWidth={stroke} fill="none"
                strokeDasharray={`${dash} ${C}`}
                strokeLinecap="round"
                filter={(isDark || showGlow) ? `url(#${id}-glow)` : undefined}/>
      </svg>
      {(value !== null || sub) && (
        <div style={{
          position: "absolute", inset: 0,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          fontFamily: V3_FONT.sans,
        }}>
          {value !== null && (
            <div style={{ fontSize: size * 0.34, fontWeight: 700, color: c.text, lineHeight: 1, letterSpacing: "-.02em" }}>
              {value}
            </div>
          )}
          {sub && (
            <div style={{ fontSize: size * 0.10, color: c.text3, marginTop: 4 }}>
              {sub}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── V3 Wave Chart (smooth gradient) ──────────────────────────────────────────
function V3WaveChart({ data = [3, 6, 4, 7, 5, 8, 9], labels = null, height = 200,
                       highlight = null, glow = false }) {
  const { c, isDark } = useV3Theme();
  const id = `wave${Math.random().toString(36).slice(2, 7)}`;
  const w = 600, h = height;
  const padding = { top: 30, right: 30, bottom: 30, left: 30 };
  const innerW = w - padding.left - padding.right;
  const innerH = h - padding.top - padding.bottom;
  const max = 10, min = 0;
  const px = i => padding.left + (i / (data.length - 1)) * innerW;
  const py = v => padding.top + (1 - (v - min) / (max - min)) * innerH;
  // smooth path
  const pts = data.map((v, i) => [px(i), py(v)]);
  let d = `M ${pts[0][0]} ${pts[0][1]}`;
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1];
    const [x1, y1] = pts[i];
    const cx0 = x0 + (x1 - x0) / 2;
    const cx1 = x0 + (x1 - x0) / 2;
    d += ` C ${cx0} ${y0} ${cx1} ${y1} ${x1} ${y1}`;
  }
  const fillD = d + ` L ${pts[pts.length-1][0]} ${h - padding.bottom} L ${pts[0][0]} ${h - padding.bottom} Z`;

  return (
    <div style={{ width: "100%", height, position: "relative" }}>
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ width: "100%", height: "100%" }}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%"   stopColor={c.gradFrom}/>
            <stop offset="50%"  stopColor={c.gradMid}/>
            <stop offset="100%" stopColor={c.gradTo}/>
          </linearGradient>
          <linearGradient id={`${id}-fill`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor={c.teal} stopOpacity={isDark ? ".25" : ".18"}/>
            <stop offset="50%"  stopColor={c.violet} stopOpacity={isDark ? ".12" : ".10"}/>
            <stop offset="100%" stopColor={c.violet} stopOpacity="0"/>
          </linearGradient>
          {(isDark || glow) && (
            <filter id={`${id}-glow`}>
              <feGaussianBlur stdDeviation="2.5" result="blur"/>
              <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          )}
        </defs>
        {/* gridlines */}
        {[0, 0.25, 0.5, 0.75, 1].map(t => {
          const y = padding.top + t * innerH;
          return (
            <line key={t} x1={padding.left} y1={y} x2={w - padding.right} y2={y}
                  stroke={isDark ? "rgba(255,255,255,.05)" : "#e8edf5"}
                  strokeDasharray="3 4"/>
          );
        })}
        {/* y-axis values */}
        {[10, 8, 6, 4, 2, 0].map(v => (
          <text key={v} x={padding.left - 8} y={py(v) + 3}
                fill={c.text3} fontSize="9" textAnchor="end"
                fontFamily={V3_FONT.sans}>{v}</text>
        ))}
        {/* area */}
        <path d={fillD} fill={`url(#${id}-fill)`}/>
        {/* line */}
        <path d={d} stroke={`url(#${id})`} strokeWidth="3" fill="none" strokeLinecap="round"
              filter={(isDark || glow) ? `url(#${id}-glow)` : undefined}/>
        {/* points */}
        {pts.map(([x, y], i) => {
          const isHi = highlight === i;
          return (
            <g key={i}>
              <circle cx={x} cy={y} r={isHi ? "8" : "5"}
                      fill={isDark ? "#0a0d1a" : "#fff"}
                      stroke={isHi ? c.violet : c.teal}
                      strokeWidth={isHi ? "3" : "2"}/>
              {isHi && (
                <circle cx={x} cy={y} r="14" fill={c.violet} opacity=".15"/>
              )}
            </g>
          );
        })}
        {/* dashed vertical at highlight */}
        {highlight !== null && highlight !== undefined && (
          <line x1={pts[highlight][0]} y1={padding.top}
                x2={pts[highlight][0]} y2={h - padding.bottom}
                stroke={c.violet} strokeWidth="1.5"
                strokeDasharray="3 3" opacity=".4"/>
        )}
      </svg>
      {/* x-axis labels */}
      {labels && (
        <div style={{
          position: "absolute", bottom: 4, left: 0, right: 0,
          display: "flex", justifyContent: "space-between",
          padding: "0 30px",
          fontSize: 10, color: c.text3, fontWeight: 500,
        }}>
          {labels.map((l, i) => (
            <span key={i} style={{
              color: highlight === i ? c.violet : c.text3,
              fontWeight: highlight === i ? 700 : 500,
            }}>{l}</span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── V3 Tab Pill ──────────────────────────────────────────────────────────────
function V3Tabs({ items, active, onChange }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{ display: "flex", gap: 6 }}>
      {items.map(it => {
        const a = it === active;
        return (
          <button key={it} onClick={() => onChange && onChange(it)} style={{
            padding: "8px 18px",
            borderRadius: 999,
            background: a ? c.teal : "transparent",
            color: a ? "#fff" : c.text2,
            border: a ? "none" : `1px solid ${c.borderSoft}`,
            fontSize: 12, fontWeight: 600,
            fontFamily: V3_FONT.sans,
            cursor: "pointer",
            boxShadow: a ? `0 4px 12px -2px ${c.teal}55` : "none",
          }}>{it}</button>
        );
      })}
    </div>
  );
}

// ── V3 Eyebrow + Big Title ───────────────────────────────────────────────────
function V3SectionTitle({ children, sub = null, action = null }) {
  const { c } = useV3Theme();
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
      <div>
        <div style={{ fontSize: 18, fontWeight: 700, color: c.text, letterSpacing: "-.01em" }}>
          {children}
        </div>
        {sub && <div style={{ fontSize: 12, color: c.text2, marginTop: 2 }}>{sub}</div>}
      </div>
      {action}
    </div>
  );
}

Object.assign(window, {
  V3_LIGHT, V3_DARK, V3_FONT,
  useV3, useV3Theme, V3Provider, V3ModeContext,
  V3Logo, V3Shell, V3ShellInner, V3Sidebar, V3Header, ThemeToggle,
  V3Card, V3Button, V3Ring, V3WaveChart, V3Tabs, V3SectionTitle,
});
