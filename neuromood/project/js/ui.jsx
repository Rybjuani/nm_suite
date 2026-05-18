/* ui.jsx — Primitivos NeuroMood Refined
 * Componentes base reusables en todas las pantallas.
 * Asume window.useTheme + window.NMLogo cargados.
 */

// ── AppWindow: chrome de ventana de escritorio (sin emular SO) ────────────────
// Marco neutro con titlebar, usado para todas las pantallas en el canvas.
function AppWindow({ title, subtitle, sidebar = null, accent = "accent",
                    children, width = 1080, height = 720, kind = "patient" }) {
  const t = useTheme();
  const accentColor = t.c[accent] || t.c.accent;
  return (
    <div style={{
      width, height,
      borderRadius: 18,
      background: t.c.bgAlt,
      border: `1px solid ${t.c.border}`,
      boxShadow: t.s.lg,
      overflow: "hidden",
      display: "grid",
      gridTemplateRows: "auto 1fr",
      fontFamily: FONT.sans,
      color: t.c.text,
    }}>
      {/* Titlebar */}
      <div style={{
        height: 38,
        background: t.c.surface,
        borderBottom: `1px solid ${t.c.borderSoft}`,
        display: "grid",
        gridTemplateColumns: "auto 1fr auto",
        alignItems: "center",
        padding: "0 14px",
        gap: 12,
      }}>
        <div style={{ display: "flex", gap: 6 }}>
          {["#ed6a5e","#f3bf48","#62c554"].map(c => (
            <span key={c} style={{
              width: 11, height: 11, borderRadius: 999,
              background: c, opacity: t.mode === "dark" ? .55 : 1,
            }}/>
          ))}
        </div>
        <div style={{
          textAlign: "center",
          fontSize: 12, color: t.c.text3, fontWeight: 500,
          letterSpacing: ".02em",
        }}>
          {title}
          {subtitle && <span style={{ color: t.c.text4 }}> · {subtitle}</span>}
        </div>
        <div style={{ width: 33 }}/>
      </div>

      {/* Body */}
      <div style={{
        display: "grid",
        gridTemplateColumns: sidebar ? `${sidebar.width || 220}px 1fr` : "1fr",
        height: "100%",
        overflow: "hidden",
        background: t.c.bg,
      }}>
        {sidebar && (
          <div style={{
            background: t.c.bgAlt,
            borderRight: `1px solid ${t.c.borderSoft}`,
            overflow: "hidden",
          }}>
            {sidebar.content}
          </div>
        )}
        <div style={{ overflow: "hidden", position: "relative" }}>
          {children}
        </div>
      </div>
    </div>
  );
}

// ── NMCard ────────────────────────────────────────────────────────────────────
function NMCard({ children, padding = 20, accent = null, hover = false,
                  interactive = false, style = {}, onClick }) {
  const t = useTheme();
  const [h, setH] = React.useState(false);
  return (
    <div
      onMouseEnter={() => interactive && setH(true)}
      onMouseLeave={() => setH(false)}
      onClick={onClick}
      style={{
        background: t.c.surface,
        borderRadius: RADIUS.lg,
        border: `1px solid ${h ? t.c.borderStrong : t.c.borderSoft}`,
        padding,
        boxShadow: h ? t.s.md : t.s.sm,
        position: "relative",
        cursor: interactive ? "pointer" : "default",
        transition: "all .18s ease",
        ...style,
      }}>
      {accent && (
        <div style={{
          position: "absolute", left: 0, top: 16, bottom: 16,
          width: 3, background: t.c[accent] || accent,
          borderRadius: 2,
        }}/>
      )}
      {children}
    </div>
  );
}

// ── NMButton ──────────────────────────────────────────────────────────────────
function NMButton({ children, variant = "primary", size = "md", icon = null,
                    fullWidth = false, disabled = false, danger = false,
                    onClick, style = {} }) {
  const t = useTheme();
  const [h, setH] = React.useState(false);

  const sizes = {
    sm: { px: 12, py: 6,  fs: 12, h: 28 },
    md: { px: 16, py: 9,  fs: 13, h: 36 },
    lg: { px: 22, py: 12, fs: 14, h: 44 },
  };
  const s = sizes[size];

  let bg, color, border;
  if (variant === "primary") {
    bg = danger ? t.c.danger : t.c.accent;
    color = "#fff";
    border = "transparent";
  } else if (variant === "secondary") {
    bg = h ? t.c.elevated : t.c.surface;
    color = t.c.text;
    border = t.c.border;
  } else if (variant === "ghost") {
    bg = h ? t.c.elevated : "transparent";
    color = t.c.text2;
    border = "transparent";
  } else if (variant === "soft") {
    bg = danger ? t.c.dangerSoft : t.c.accentSoft;
    color = danger ? t.c.danger : t.c.accent;
    border = "transparent";
  }

  return (
    <button
      onMouseEnter={() => setH(true)}
      onMouseLeave={() => setH(false)}
      onClick={onClick}
      disabled={disabled}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        width: fullWidth ? "100%" : "auto",
        height: s.h,
        padding: `0 ${s.px}px`,
        background: bg,
        color: color,
        border: `1px solid ${border}`,
        borderRadius: RADIUS.md,
        fontFamily: FONT.sans,
        fontSize: s.fs,
        fontWeight: 600,
        letterSpacing: ".005em",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? .5 : 1,
        transition: "all .15s ease",
        boxShadow: variant === "primary" && h ? t.s.md : "none",
        transform: variant === "primary" && h ? "translateY(-1px)" : "none",
        ...style,
      }}>
      {icon && <span style={{ display: "inline-flex" }}>{icon}</span>}
      {children}
    </button>
  );
}

// ── NMBadge / NMPill ─────────────────────────────────────────────────────────
function NMBadge({ children, tone = "default", icon = null, style = {} }) {
  const t = useTheme();
  const tones = {
    default: { bg: t.c.elevated, fg: t.c.text2, bd: t.c.borderSoft },
    success: { bg: t.c.successSoft, fg: t.c.success, bd: "transparent" },
    warning: { bg: t.c.warningSoft, fg: t.c.warning, bd: "transparent" },
    danger:  { bg: t.c.dangerSoft,  fg: t.c.danger,  bd: "transparent" },
    accent:  { bg: t.c.accentSoft,  fg: t.c.accent,  bd: "transparent" },
    teal:    { bg: t.c.tealSoft,    fg: t.c.teal,    bd: "transparent" },
    violet:  { bg: t.c.violetSoft,  fg: t.c.violet,  bd: "transparent" },
    streak:  { bg: t.c.streakSoft,  fg: t.c.streak,  bd: "transparent" },
  };
  const s = tones[tone] || tones.default;
  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 4,
      padding: "3px 9px",
      borderRadius: RADIUS.pill,
      background: s.bg,
      color: s.fg,
      border: `1px solid ${s.bd}`,
      fontSize: 11,
      fontWeight: 600,
      letterSpacing: ".01em",
      lineHeight: 1.4,
      ...style,
    }}>
      {icon}
      {children}
    </span>
  );
}

// ── NMRing — anillo de progreso ──────────────────────────────────────────────
function NMRing({ pct = 0, size = 48, stroke = 4, tone = "accent",
                  label = null, sublabel = null, value = null }) {
  const t = useTheme();
  const color = t.c[tone] || t.c.accent;
  const r = (size - stroke) / 2;
  const C = 2 * Math.PI * r;
  const dash = (pct / 100) * C;
  return (
    <div style={{ position: "relative", width: size, height: size, display: "inline-block" }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size/2} cy={size/2} r={r}
                stroke={t.c.borderSoft} strokeWidth={stroke} fill="none"/>
        <circle cx={size/2} cy={size/2} r={r}
                stroke={color} strokeWidth={stroke} fill="none"
                strokeDasharray={`${dash} ${C}`}
                strokeLinecap="round"
                style={{ transition: "stroke-dasharray .5s ease" }}/>
      </svg>
      {(value !== null || label) && (
        <div style={{
          position: "absolute", inset: 0,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          fontFamily: FONT.sans,
        }}>
          {value !== null && (
            <div style={{ fontSize: size * 0.28, fontWeight: 700, color: t.c.text }}>
              {value}
            </div>
          )}
          {label && (
            <div style={{ fontSize: 9, color: t.c.text3, marginTop: -2 }}>
              {label}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── NMInput / NMTextarea ─────────────────────────────────────────────────────
function NMInput({ placeholder, value, onChange, type = "text", icon = null,
                   suffix = null, style = {} }) {
  const t = useTheme();
  const [f, setF] = React.useState(false);
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 8,
      height: 38,
      padding: "0 12px",
      background: t.c.surface,
      borderRadius: RADIUS.md,
      border: `1px solid ${f ? t.c.accent : t.c.border}`,
      boxShadow: f ? t.s.glow : "none",
      transition: "all .15s ease",
      ...style,
    }}>
      {icon && <span style={{ color: t.c.text3, display: "inline-flex" }}>{icon}</span>}
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={e => onChange && onChange(e.target.value)}
        onFocus={() => setF(true)}
        onBlur={() => setF(false)}
        style={{
          flex: 1, minWidth: 0,
          background: "transparent",
          border: "none", outline: "none",
          fontFamily: FONT.sans,
          fontSize: 13,
          color: t.c.text,
        }}
        readOnly={!onChange}
      />
      {suffix && <span style={{ color: t.c.text3, fontSize: 12 }}>{suffix}</span>}
    </div>
  );
}

// ── NMSlider ──────────────────────────────────────────────────────────────────
function NMSlider({ value, min = 0, max = 100, tone = "accent" }) {
  const t = useTheme();
  const pct = ((value - min) / (max - min)) * 100;
  const color = t.c[tone] || t.c.accent;
  return (
    <div style={{ position: "relative", height: 24 }}>
      <div style={{
        position: "absolute", top: 10, left: 0, right: 0, height: 4,
        background: t.c.elevated, borderRadius: 4,
      }}/>
      <div style={{
        position: "absolute", top: 10, left: 0, width: `${pct}%`, height: 4,
        background: color, borderRadius: 4,
      }}/>
      <div style={{
        position: "absolute", top: 4, left: `calc(${pct}% - 8px)`,
        width: 16, height: 16, borderRadius: 999,
        background: t.c.surface,
        border: `2px solid ${color}`,
        boxShadow: t.s.sm,
      }}/>
    </div>
  );
}

// ── NMToggle (switch) ────────────────────────────────────────────────────────
function NMToggle({ checked = false, tone = "accent" }) {
  const t = useTheme();
  const color = t.c[tone] || t.c.accent;
  return (
    <div style={{
      width: 38, height: 22, borderRadius: 999,
      background: checked ? color : t.c.elevated,
      border: `1px solid ${checked ? color : t.c.border}`,
      position: "relative",
      transition: "all .2s ease",
    }}>
      <div style={{
        position: "absolute",
        top: 2, left: checked ? 18 : 2,
        width: 16, height: 16, borderRadius: 999,
        background: checked ? "#fff" : t.c.surface,
        boxShadow: t.s.sm,
        transition: "left .2s ease",
      }}/>
    </div>
  );
}

// ── NMCheck ───────────────────────────────────────────────────────────────────
function NMCheck({ checked = false, label = null, size = 18 }) {
  const t = useTheme();
  return (
    <label style={{ display: "inline-flex", alignItems: "center", gap: 10, fontSize: 13, color: t.c.text }}>
      <span style={{
        width: size, height: size,
        borderRadius: 5,
        border: `1.5px solid ${checked ? t.c.accent : t.c.borderStrong}`,
        background: checked ? t.c.accent : t.c.surface,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "all .15s ease",
      }}>
        {checked && (
          <svg width="11" height="9" viewBox="0 0 11 9" fill="none">
            <path d="M1 4.5 L4 7.5 L10 1.5" stroke="#fff" strokeWidth="1.8"
                  strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
      </span>
      {label}
    </label>
  );
}

// ── NMHeader (Suite paciente) ────────────────────────────────────────────────
function NMHeader({ left = null, center = null, right = null,
                    onBack = null, mode, onToggleMode }) {
  const t = useTheme();
  return (
    <div style={{
      height: 56,
      padding: "0 20px",
      background: t.c.surface,
      borderBottom: `1px solid ${t.c.borderSoft}`,
      display: "grid",
      gridTemplateColumns: "1fr auto 1fr",
      alignItems: "center",
      gap: 12,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {onBack && (
          <NMButton variant="ghost" size="sm" icon={
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M9 2 L4 7 L9 12" stroke="currentColor" strokeWidth="1.8"
                    strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          }>Atrás</NMButton>
        )}
        {left}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {center || <NMLogo size={22}/>}
      </div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 8 }}>
        {right}
        {onToggleMode && (
          <button onClick={onToggleMode} style={{
            width: 32, height: 32, borderRadius: 999,
            background: t.c.elevated, border: `1px solid ${t.c.borderSoft}`,
            color: t.c.text2, cursor: "pointer",
            display: "inline-flex", alignItems: "center", justifyContent: "center",
          }}>
            {mode === "dark" ? (
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="3" stroke="currentColor" strokeWidth="1.4"/>
                {[0,45,90,135,180,225,270,315].map(a => (
                  <line key={a} x1="7" y1="1.5" x2="7" y2="2.8"
                        stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"
                        transform={`rotate(${a} 7 7)`}/>
                ))}
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M11 8a4.5 4.5 0 0 1-5-5 4.5 4.5 0 1 0 5 5z"
                      fill="currentColor"/>
              </svg>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

// ── SectionTitle ──────────────────────────────────────────────────────────────
function SectionTitle({ children, eyebrow = null, action = null, size = "md" }) {
  const t = useTheme();
  const sizes = {
    sm: { fs: 13, w: 600 },
    md: { fs: 16, w: 600 },
    lg: { fs: 22, w: 700 },
    xl: { fs: 28, w: 700 },
  };
  const s = sizes[size];
  return (
    <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 8 }}>
      <div>
        {eyebrow && (
          <div style={{
            fontSize: 10, fontWeight: 700,
            letterSpacing: ".12em",
            color: t.c.text3,
            textTransform: "uppercase",
            marginBottom: 4,
          }}>{eyebrow}</div>
        )}
        <div style={{
          fontSize: s.fs, fontWeight: s.w,
          color: t.c.text, letterSpacing: "-.005em",
        }}>{children}</div>
      </div>
      {action}
    </div>
  );
}

// ── Stepper (Installer) ───────────────────────────────────────────────────────
function NMStepper({ steps, active, tone = "accent" }) {
  const t = useTheme();
  const color = t.c[tone] || t.c.accent;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      {steps.map((s, i) => {
        const done = i < active;
        const cur = i === active;
        return (
          <React.Fragment key={i}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{
                width: 24, height: 24, borderRadius: 999,
                background: done ? color : (cur ? t.c.surface : t.c.elevated),
                border: `1.5px solid ${done || cur ? color : t.c.borderSoft}`,
                color: done ? "#fff" : (cur ? color : t.c.text3),
                fontSize: 11, fontWeight: 700,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {done ? "✓" : (i + 1)}
              </div>
              <div style={{
                fontSize: 12, fontWeight: cur ? 600 : 500,
                color: cur ? t.c.text : (done ? t.c.text2 : t.c.text3),
                letterSpacing: ".01em",
              }}>{s}</div>
            </div>
            {i < steps.length - 1 && (
              <div style={{
                flex: 1, height: 1, minWidth: 16,
                background: done ? color : t.c.borderSoft,
              }}/>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ── ProgressBar ───────────────────────────────────────────────────────────────
function NMProgress({ value = 0, tone = "accent", height = 6, label = null }) {
  const t = useTheme();
  const color = t.c[tone] || t.c.accent;
  return (
    <div>
      {label && (
        <div style={{
          display: "flex", justifyContent: "space-between",
          fontSize: 11, color: t.c.text3, marginBottom: 6,
        }}>
          <span>{label}</span>
          <span style={{ fontFamily: FONT.mono, color: t.c.text2 }}>{Math.round(value)}%</span>
        </div>
      )}
      <div style={{
        height, background: t.c.elevated,
        borderRadius: height, overflow: "hidden",
      }}>
        <div style={{
          width: `${value}%`, height: "100%",
          background: color,
          borderRadius: height,
          transition: "width .4s ease",
        }}/>
      </div>
    </div>
  );
}

// ── ImagePlaceholder ──────────────────────────────────────────────────────────
function ImgPH({ width = "100%", height = 120, label = "imagen", style = {} }) {
  const t = useTheme();
  return (
    <div style={{
      width, height,
      borderRadius: RADIUS.md,
      background: `repeating-linear-gradient(45deg, ${t.c.elevated}, ${t.c.elevated} 8px, ${t.c.bgAlt} 8px, ${t.c.bgAlt} 16px)`,
      border: `1px dashed ${t.c.border}`,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: t.c.text3,
      fontSize: 10,
      fontFamily: FONT.mono,
      letterSpacing: ".05em",
      ...style,
    }}>
      {label}
    </div>
  );
}

// ── SyncOrb (Hub/Config) ──────────────────────────────────────────────────────
function SyncOrb({ state = "ok", size = 10 }) {
  const t = useTheme();
  const states = {
    ok:      { c: t.c.success, label: "Sincronizado" },
    syncing: { c: t.c.warning, label: "Sincronizando…" },
    error:   { c: t.c.danger,  label: "Sin conexión" },
  };
  const s = states[state];
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      <span style={{
        position: "relative",
        width: size, height: size, borderRadius: 999,
        background: s.c,
        boxShadow: `0 0 0 4px ${s.c}22`,
      }}>
        {state === "syncing" && (
          <span style={{
            position: "absolute", inset: -3,
            borderRadius: 999,
            border: `1.5px solid ${s.c}55`,
            animation: "nmOrb 1.4s ease-out infinite",
          }}/>
        )}
      </span>
      <span style={{ fontSize: 11, color: t.c.text2, fontWeight: 500 }}>{s.label}</span>
      <style>{`@keyframes nmOrb { 0%{transform:scale(1);opacity:.7} 100%{transform:scale(1.6);opacity:0} }`}</style>
    </div>
  );
}

Object.assign(window, {
  AppWindow, NMCard, NMButton, NMBadge, NMRing, NMInput,
  NMSlider, NMToggle, NMCheck, NMHeader, SectionTitle,
  NMStepper, NMProgress, ImgPH, SyncOrb,
});
