/* screens-premium.jsx — Dirección "Premium / Editorial" para reaccionar.
 * Romper con lo plano: gradient mesh, glass cards, tipografía editorial,
 * sombras cromáticas, data art generoso, color saturado.
 */

// ── PremiumFrame: contenedor visual rico ──────────────────────────────────────
function PremiumFrame({ title, subtitle, width = 1180, height = 760,
                        mesh = "indigo", children, kind = "suite" }) {
  const t = useTheme();
  // Mesh palettes (4 blobs cada una)
  const meshes = {
    indigo: [
      ["20% 15%", "rgba(99,102,241,.45)"],
      ["80% 20%", "rgba(20,184,166,.32)"],
      ["75% 85%", "rgba(168,85,247,.40)"],
      ["15% 80%", "rgba(99,210,255,.28)"],
    ],
    teal: [
      ["15% 20%", "rgba(20,184,166,.55)"],
      ["85% 15%", "rgba(99,102,241,.30)"],
      ["80% 80%", "rgba(34,211,238,.35)"],
      ["18% 78%", "rgba(168,85,247,.22)"],
    ],
    violet: [
      ["18% 22%", "rgba(168,85,247,.55)"],
      ["82% 18%", "rgba(99,102,241,.40)"],
      ["78% 82%", "rgba(20,184,166,.30)"],
      ["20% 78%", "rgba(217,119,6,.20)"],
    ],
    warm: [
      ["20% 18%", "rgba(251,191,36,.40)"],
      ["80% 20%", "rgba(244,114,182,.32)"],
      ["75% 80%", "rgba(168,85,247,.36)"],
      ["15% 78%", "rgba(20,184,166,.20)"],
    ],
  };
  const m = meshes[mesh] || meshes.indigo;
  const bgLayers = m.map(([pos, color]) =>
    `radial-gradient(circle at ${pos}, ${color}, transparent 50%)`
  ).join(", ");

  const isDark = t.mode === "dark";
  const baseBg = isDark ? "#0c1020" : "#f4f1eb";

  return (
    <div style={{
      width, height,
      borderRadius: 24,
      background: baseBg,
      boxShadow: `
        0 1px 2px rgba(0,0,0,.08),
        0 24px 56px -12px rgba(99,102,241,.18),
        0 48px 96px -32px rgba(168,85,247,.20),
        0 0 0 1px rgba(255,255,255,.04)
      `,
      overflow: "hidden",
      position: "relative",
      fontFamily: FONT.sans,
      color: isDark ? "#e8ecf5" : "#0a0e1a",
    }}>
      {/* Mesh background */}
      <div style={{
        position: "absolute", inset: 0,
        background: bgLayers,
        opacity: isDark ? .55 : .85,
        filter: "saturate(1.1)",
      }}/>
      {/* Subtle noise */}
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence baseFrequency='.9' /></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='.4'/></svg>\")",
        opacity: isDark ? .08 : .04,
        mixBlendMode: "overlay",
        pointerEvents: "none",
      }}/>
      {/* Title bar minimal */}
      <div style={{
        position: "relative",
        height: 42,
        padding: "0 20px",
        display: "flex",
        alignItems: "center",
        gap: 10,
      }}>
        <div style={{ display: "flex", gap: 6 }}>
          {["#ed6a5e","#f3bf48","#62c554"].map(c => (
            <span key={c} style={{ width: 11, height: 11, borderRadius: 999, background: c, opacity: .85 }}/>
          ))}
        </div>
        <div style={{
          marginLeft: "auto",
          fontSize: 11,
          color: isDark ? "rgba(232,236,245,.55)" : "rgba(10,14,26,.50)",
          fontWeight: 500,
          letterSpacing: ".03em",
        }}>{title}{subtitle && ` · ${subtitle}`}</div>
      </div>
      <div style={{ position: "relative", height: "calc(100% - 42px)" }}>
        {children}
      </div>
    </div>
  );
}

// ── Glass card helper ─────────────────────────────────────────────────────────
function Glass({ children, style = {}, padding = 24, blur = 24, tint = "neutral" }) {
  const t = useTheme();
  const isDark = t.mode === "dark";
  const tints = {
    neutral: isDark ? "rgba(15,21,40,.55)" : "rgba(255,255,255,.55)",
    accent:  isDark ? "rgba(48,52,120,.55)" : "rgba(238,240,254,.62)",
    teal:    isDark ? "rgba(20,60,58,.55)"  : "rgba(225,242,239,.65)",
    dark:    isDark ? "rgba(10,14,28,.72)"  : "rgba(15,23,42,.86)",
  };
  return (
    <div style={{
      background: tints[tint],
      backdropFilter: `blur(${blur}px) saturate(1.3)`,
      WebkitBackdropFilter: `blur(${blur}px) saturate(1.3)`,
      borderRadius: 20,
      border: `1px solid ${isDark ? "rgba(255,255,255,.08)" : "rgba(255,255,255,.7)"}`,
      boxShadow: `
        0 1px 0 ${isDark ? "rgba(255,255,255,.06)" : "rgba(255,255,255,.5)"} inset,
        0 12px 32px -8px rgba(15,23,42,.18),
        0 2px 8px -2px rgba(15,23,42,.08)
      `,
      padding,
      ...style,
    }}>
      {children}
    </div>
  );
}

// ── Editorial header con serif ────────────────────────────────────────────────
function Display({ children, size = 56, color, lineH = 1.05 }) {
  const t = useTheme();
  return (
    <div style={{
      fontFamily: FONT.serif,
      fontWeight: 500,
      fontSize: size,
      lineHeight: lineH,
      letterSpacing: "-.022em",
      color: color || (t.mode === "dark" ? "#f0eee8" : "#0a0e1a"),
    }}>{children}</div>
  );
}

// ── Tiny accent text ──────────────────────────────────────────────────────────
function Eyebrow({ children, color }) {
  const t = useTheme();
  return (
    <div style={{
      fontSize: 10, fontWeight: 700,
      letterSpacing: ".18em",
      textTransform: "uppercase",
      color: color || (t.mode === "dark" ? "#a5acc4" : "#475569"),
    }}>{children}</div>
  );
}

// ── Gradient pill (badge premium) ─────────────────────────────────────────────
function GradPill({ children, from = "#6366f1", to = "#a855f7", icon = null }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "5px 12px",
      borderRadius: 999,
      background: `linear-gradient(135deg, ${from}, ${to})`,
      color: "#fff",
      fontSize: 11, fontWeight: 700,
      letterSpacing: ".01em",
      boxShadow: `0 4px 14px -2px ${from}66, 0 1px 2px ${from}44`,
    }}>
      {icon}{children}
    </span>
  );
}

// ── Premium · Suite Home ──────────────────────────────────────────────────────
function PremiumHome() {
  const t = useTheme();
  const isDark = t.mode === "dark";
  return (
    <PremiumFrame title="NeuroMood Suite" subtitle="Paciente" mesh="indigo" width={1180} height={760}>
      <div style={{ height: "100%", padding: "8px 32px 28px", overflow: "hidden", display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 24 }}>
        {/* Left: hero */}
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28 }}>
              <NMLogo size={26}/>
              <div style={{ display: "flex", gap: 8 }}>
                <GradPill from="#f59e0b" to="#ef4444" icon={<span>🔥</span>}>5 días de racha</GradPill>
                <GradPill from="#6366f1" to="#14b8a6">Ana</GradPill>
              </div>
            </div>
            <Eyebrow>Jueves · 16 de mayo</Eyebrow>
            <Display size={62} lineH={1.0}>
              Buenos días,<br/>
              <span style={{ background: "linear-gradient(135deg, #6366f1, #14b8a6 60%, #a855f7)", WebkitBackgroundClip: "text", color: "transparent", fontStyle: "italic", letterSpacing: "-.025em" }}>Ana</span>
            </Display>
            <div style={{
              fontSize: 16, lineHeight: 1.55,
              color: isDark ? "rgba(232,236,245,.75)" : "rgba(10,14,26,.65)",
              marginTop: 16, maxWidth: 460,
            }}>
              Tu próximo aviso es <strong style={{ color: isDark ? "#f0eee8" : "#0a0e1a" }}>respiración 4-7-8</strong> a las 18:00.
              Llevás <strong>+0.8 puntos</strong> de ánimo esta semana.
            </div>
          </div>

          {/* Wave hero */}
          <Glass padding={24} style={{ marginTop: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 14 }}>
              <div>
                <Eyebrow>Tu semana</Eyebrow>
                <div style={{
                  fontSize: 44, fontWeight: 700,
                  fontFamily: FONT.serif, letterSpacing: "-.025em",
                  marginTop: 2,
                }}>
                  7.2<span style={{ fontSize: 22, color: isDark ? "rgba(232,236,245,.45)" : "rgba(10,14,26,.4)" }}>/10</span>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 11, color: isDark ? "rgba(232,236,245,.55)" : "rgba(10,14,26,.5)" }}>vs anterior</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: "#16a34a", fontFamily: FONT.serif }}>+0.8 ↗</div>
              </div>
            </div>
            <div style={{ height: 88, position: "relative" }}>
              <svg viewBox="0 0 400 88" preserveAspectRatio="none" style={{ width: "100%", height: "100%" }}>
                <defs>
                  <linearGradient id="moodGrad" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%"  stopColor="#6366f1"/>
                    <stop offset="50%" stopColor="#14b8a6"/>
                    <stop offset="100%" stopColor="#a855f7"/>
                  </linearGradient>
                  <linearGradient id="moodFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%"  stopColor="#14b8a6" stopOpacity=".35"/>
                    <stop offset="100%" stopColor="#14b8a6" stopOpacity="0"/>
                  </linearGradient>
                </defs>
                <path d="M0 55 C 50 48, 70 65, 110 45 S 180 25, 220 30 S 290 18, 340 14 S 380 12, 400 10 L 400 88 L 0 88 Z" fill="url(#moodFill)"/>
                <path d="M0 55 C 50 48, 70 65, 110 45 S 180 25, 220 30 S 290 18, 340 14 S 380 12, 400 10" stroke="url(#moodGrad)" strokeWidth="3" fill="none" strokeLinecap="round"/>
                {[[0,55],[110,45],[220,30],[340,14],[400,10]].map(([x,y], i) => (
                  <circle key={i} cx={x} cy={y} r="4" fill="#fff" stroke="#14b8a6" strokeWidth="2"/>
                ))}
              </svg>
            </div>
          </Glass>
        </div>

        {/* Right: modules as visual tiles */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, overflow: "hidden" }}>
          <Eyebrow>Hoy</Eyebrow>
          <Display size={28} lineH={1.1}>Tus módulos</Display>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 4 }}>
            {[
              { name: "Ánimo",       icon: "🌤", grad: ["#fbbf24","#f59e0b"], status: "7/10",     hot: true },
              { name: "Respiración", icon: "💨", grad: ["#22d3ee","#0d9488"], status: "3 ciclos" },
              { name: "TCC",         icon: "🧠", grad: ["#a855f7","#6366f1"], status: "Paso 1/4" },
              { name: "Rutina",      icon: "✓",  grad: ["#22c55e","#16a34a"], status: "8/10 · 80%" },
              { name: "Actividades", icon: "⚡", grad: ["#f97316","#ef4444"], status: "3 hoy" },
              { name: "Timer",       icon: "⏱", grad: ["#6366f1","#a855f7"], status: "Activo" },
            ].map((m, i) => (
              <div key={m.name} style={{
                position: "relative",
                borderRadius: 18,
                padding: 16,
                background: `linear-gradient(140deg, ${m.grad[0]}, ${m.grad[1]})`,
                color: "#fff",
                minHeight: 100,
                overflow: "hidden",
                cursor: "pointer",
                boxShadow: `0 12px 32px -10px ${m.grad[0]}88, 0 2px 6px ${m.grad[1]}44`,
              }}>
                <div style={{
                  position: "absolute", top: -30, right: -30,
                  width: 120, height: 120, borderRadius: 999,
                  background: "rgba(255,255,255,.18)",
                  filter: "blur(20px)",
                }}/>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", position: "relative" }}>
                  <div style={{ fontSize: 24 }}>{m.icon}</div>
                  {m.hot && (
                    <div style={{
                      padding: "2px 7px", borderRadius: 999,
                      background: "rgba(255,255,255,.25)",
                      fontSize: 9, fontWeight: 700,
                      letterSpacing: ".06em",
                      textTransform: "uppercase",
                    }}>en racha</div>
                  )}
                </div>
                <div style={{ marginTop: 18, position: "relative" }}>
                  <div style={{ fontSize: 16, fontWeight: 700, letterSpacing: "-.005em" }}>{m.name}</div>
                  <div style={{ fontSize: 11, marginTop: 2, opacity: .85, fontFamily: FONT.mono }}>{m.status}</div>
                </div>
              </div>
            ))}
          </div>
          {/* CTA Avisos */}
          <Glass padding={16} tint="dark" style={{ marginTop: "auto" }}>
            <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 12, alignItems: "center", color: "#fff" }}>
              <div style={{
                width: 38, height: 38, borderRadius: 12,
                background: "linear-gradient(135deg,#f59e0b,#ef4444)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 18,
              }}>🔔</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>Respiración 4-7-8 a las 18:00</div>
                <div style={{ fontSize: 11, opacity: .65 }}>En 2 horas 14 minutos</div>
              </div>
              <button style={{
                padding: "6px 12px", borderRadius: 999,
                border: "1px solid rgba(255,255,255,.2)",
                background: "rgba(255,255,255,.1)",
                color: "#fff", fontSize: 11, fontWeight: 600,
                cursor: "pointer",
              }}>Posponer</button>
            </div>
          </Glass>
        </div>
      </div>
    </PremiumFrame>
  );
}

// ── Premium · Ánimo ───────────────────────────────────────────────────────────
function PremiumAnimo() {
  const t = useTheme();
  const isDark = t.mode === "dark";
  return (
    <PremiumFrame title="NeuroMood Suite" subtitle="Registro de ánimo" mesh="teal" width={1180} height={760}>
      <div style={{ height: "100%", padding: "0 32px 28px", overflow: "hidden", display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 28 }}>
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", gap: 18 }}>
          <Eyebrow>Hoy · 16 de mayo</Eyebrow>
          <Display size={64}>¿Cómo te <span style={{ fontStyle: "italic", color: "#14b8a6" }}>sentís</span>?</Display>
          <div style={{ fontSize: 15, color: isDark ? "rgba(232,236,245,.65)" : "rgba(10,14,26,.55)", maxWidth: 480, lineHeight: 1.5 }}>
            Tomate un momento. Sin pensarlo demasiado, ¿qué número se acerca a este momento?
          </div>

          {/* Emoji grande con halo */}
          <div style={{ display: "flex", alignItems: "center", gap: 40, marginTop: 12 }}>
            <div style={{ position: "relative" }}>
              <div style={{
                position: "absolute", inset: -20,
                background: "radial-gradient(circle, rgba(20,184,166,.45) 0%, transparent 65%)",
                filter: "blur(10px)",
              }}/>
              <div style={{ fontSize: 140, lineHeight: 1, position: "relative" }}>😄</div>
            </div>
            <div>
              <div style={{
                fontSize: 96, fontFamily: FONT.serif, fontWeight: 500,
                color: "#14b8a6", lineHeight: 1, letterSpacing: "-.04em",
              }}>7<span style={{ fontSize: 32, color: isDark ? "rgba(232,236,245,.4)" : "rgba(10,14,26,.4)", fontFamily: FONT.sans, fontWeight: 700 }}>/10</span></div>
              <div style={{ fontSize: 14, color: "#14b8a6", fontWeight: 600, marginTop: 4 }}>Buen día</div>
            </div>
          </div>

          {/* Slider editorial */}
          <Glass padding={20} style={{ marginTop: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: isDark ? "rgba(232,236,245,.55)" : "rgba(10,14,26,.5)", fontFamily: FONT.mono, marginBottom: 10 }}>
              <span>1 · difícil</span><span>5 · neutro</span><span>10 · excelente</span>
            </div>
            <div style={{ position: "relative", height: 8 }}>
              <div style={{
                position: "absolute", inset: 0,
                background: "linear-gradient(90deg, #ef4444, #f59e0b 35%, #facc15 50%, #4ade80 65%, #14b8a6, #06b6d4)",
                borderRadius: 999,
              }}/>
              <div style={{
                position: "absolute", top: -10, left: "calc(70% - 14px)",
                width: 28, height: 28, borderRadius: 999,
                background: "#fff",
                border: "3px solid #14b8a6",
                boxShadow: "0 4px 12px rgba(20,184,166,.35)",
              }}/>
            </div>
          </Glass>
          <div style={{ display: "flex", gap: 12 }}>
            <button style={{
              padding: "14px 28px",
              borderRadius: 999,
              background: "linear-gradient(135deg, #14b8a6, #6366f1)",
              color: "#fff", border: "none",
              fontSize: 14, fontWeight: 700, cursor: "pointer",
              boxShadow: "0 8px 24px -4px rgba(20,184,166,.45)",
              fontFamily: FONT.sans,
            }}>Guardar registro</button>
            <button style={{
              padding: "14px 22px",
              borderRadius: 999,
              background: "transparent",
              color: isDark ? "rgba(232,236,245,.7)" : "rgba(10,14,26,.55)",
              border: `1px solid ${isDark ? "rgba(255,255,255,.15)" : "rgba(10,14,26,.12)"}`,
              fontSize: 13, fontWeight: 600, cursor: "pointer",
              fontFamily: FONT.sans,
            }}>+ Nota del día</button>
          </div>
        </div>

        {/* Right rail: history */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14, justifyContent: "center" }}>
          <Glass padding={22}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <Eyebrow>Últimos 30 días</Eyebrow>
              <GradPill from="#16a34a" to="#22d3ee">+12%</GradPill>
            </div>
            <div style={{ height: 180, position: "relative" }}>
              <svg viewBox="0 0 400 180" preserveAspectRatio="none" style={{ width: "100%", height: "100%" }}>
                <defs>
                  <linearGradient id="anFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#14b8a6" stopOpacity=".4"/>
                    <stop offset="100%" stopColor="#14b8a6" stopOpacity="0"/>
                  </linearGradient>
                  <linearGradient id="anLine" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%"  stopColor="#6366f1"/>
                    <stop offset="50%" stopColor="#14b8a6"/>
                    <stop offset="100%" stopColor="#a855f7"/>
                  </linearGradient>
                </defs>
                {[40,80,120,160].map(y => <line key={y} x1="0" y1={y} x2="400" y2={y} stroke={isDark ? "rgba(255,255,255,.05)" : "rgba(15,23,42,.06)"} strokeDasharray="2 4"/>)}
                <path d="M0 100 C 40 90, 60 120, 100 90 S 160 60, 200 70 S 280 50, 320 35 S 380 25, 400 20 L 400 180 L 0 180 Z" fill="url(#anFill)"/>
                <path d="M0 100 C 40 90, 60 120, 100 90 S 160 60, 200 70 S 280 50, 320 35 S 380 25, 400 20" stroke="url(#anLine)" strokeWidth="3" fill="none" strokeLinecap="round"/>
                {[[0,100],[100,90],[200,70],[320,35],[400,20]].map(([x,y], i) => (
                  <g key={i}>
                    <circle cx={x} cy={y} r="8" fill="#14b8a6" opacity=".15"/>
                    <circle cx={x} cy={y} r="4" fill="#fff" stroke="#14b8a6" strokeWidth="2"/>
                  </g>
                ))}
              </svg>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, fontFamily: FONT.mono, color: isDark ? "rgba(232,236,245,.4)" : "rgba(10,14,26,.35)", marginTop: 8 }}>
              <span>17 abr</span><span>24 abr</span><span>1 may</span><span>8 may</span><span>16 may</span>
            </div>
          </Glass>
          <Glass padding={18}>
            <Eyebrow>Hoy</Eyebrow>
            <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                ["09:15", "🙂", 7, "Buen día"],
                ["12:30", "😐", 5, "Reunión estresante"],
              ].map(([h, e, s, n], i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "auto auto 1fr auto", alignItems: "center", gap: 12, padding: "6px 4px" }}>
                  <span style={{ fontSize: 11, fontFamily: FONT.mono, color: isDark ? "rgba(232,236,245,.4)" : "rgba(10,14,26,.4)" }}>{h}</span>
                  <span style={{ fontSize: 22 }}>{e}</span>
                  <span style={{ fontSize: 12, color: isDark ? "rgba(232,236,245,.7)" : "rgba(10,14,26,.65)" }}>{n}</span>
                  <GradPill from={s >= 7 ? "#16a34a" : "#f59e0b"} to={s >= 7 ? "#22d3ee" : "#ef4444"}>{s}/10</GradPill>
                </div>
              ))}
            </div>
          </Glass>
        </div>
      </div>
    </PremiumFrame>
  );
}

// ── Premium · Hub Dashboard ───────────────────────────────────────────────────
function PremiumHubDash() {
  const t = useTheme();
  const isDark = t.mode === "dark";
  return (
    <PremiumFrame title="NeuroMood Hub" subtitle="Dashboard clínico" mesh="violet" width={1320} height={820}>
      <div style={{ height: "100%", display: "grid", gridTemplateColumns: "220px 1fr", overflow: "hidden" }}>
        {/* Glass sidebar */}
        <Glass padding={0} blur={32} tint="dark" style={{
          margin: 14, borderRadius: 20,
          display: "flex", flexDirection: "column",
        }}>
          <div style={{ padding: "20px 18px 14px", display: "flex", alignItems: "center", gap: 10, color: "#fff" }}>
            <NMGlyph size={26} tone="accent"/>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700 }}>NeuroMood</div>
              <div style={{ fontSize: 9, fontWeight: 700, color: "rgba(255,255,255,.5)", letterSpacing: ".15em" }}>HUB · v2.1</div>
            </div>
          </div>
          {[
            ["Pacientes", "👥", false],
            ["Dashboard", "📊", true],
            ["IA Asistente", "✦", false],
            ["Configuración", "⚙", false],
          ].map(([n, ic, a]) => (
            <div key={n} style={{
              padding: "12px 18px", margin: "2px 10px",
              borderRadius: 12,
              background: a ? "linear-gradient(135deg, rgba(99,102,241,.4), rgba(168,85,247,.4))" : "transparent",
              color: a ? "#fff" : "rgba(255,255,255,.65)",
              fontSize: 13, fontWeight: a ? 600 : 500,
              display: "flex", alignItems: "center", gap: 10,
              cursor: "pointer",
            }}>
              <span style={{ fontSize: 14 }}>{ic}</span>{n}
            </div>
          ))}
          <div style={{ marginTop: "auto", padding: 16, borderTop: "1px solid rgba(255,255,255,.08)", color: "rgba(255,255,255,.5)", fontSize: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: 999, background: "#22c55e" }}/>
              Sincronizado
            </div>
            <div style={{ marginTop: 4, fontFamily: FONT.mono }}>doctor@clinica.com</div>
          </div>
        </Glass>

        {/* Main */}
        <div style={{ padding: "12px 30px 28px", overflow: "hidden", display: "flex", flexDirection: "column", gap: 18 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
            <div>
              <Eyebrow>Vista clínica · 12 pacientes</Eyebrow>
              <Display size={42} lineH={1.05}>Resumen <span style={{ fontStyle: "italic", color: "#a855f7" }}>de hoy</span></Display>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <GradPill from="#22c55e" to="#14b8a6" icon={<span style={{ width: 5, height: 5, borderRadius: 999, background: "#fff", display: "inline-block" }}/>}>Todo sincronizado</GradPill>
              <GradPill from="#6366f1" to="#a855f7">Exportar resumen</GradPill>
            </div>
          </div>

          {/* Hero patient card */}
          <Glass padding={28} style={{ position: "relative", overflow: "hidden" }}>
            <div style={{
              position: "absolute", top: -80, right: -60, width: 280, height: 280,
              background: "radial-gradient(circle, rgba(20,184,166,.35), transparent 60%)",
            }}/>
            <div style={{
              position: "absolute", bottom: -100, right: 100, width: 240, height: 240,
              background: "radial-gradient(circle, rgba(168,85,247,.30), transparent 60%)",
            }}/>
            <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 28, alignItems: "center", position: "relative" }}>
              {/* Big ring */}
              <div style={{ position: "relative", width: 140, height: 140 }}>
                <svg width="140" height="140" viewBox="0 0 140 140">
                  <defs>
                    <linearGradient id="bigRing" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor="#6366f1"/>
                      <stop offset="50%" stopColor="#14b8a6"/>
                      <stop offset="100%" stopColor="#a855f7"/>
                    </linearGradient>
                  </defs>
                  <circle cx="70" cy="70" r="58" fill="none" stroke={isDark ? "rgba(255,255,255,.08)" : "rgba(15,23,42,.06)"} strokeWidth="10"/>
                  <circle cx="70" cy="70" r="58" fill="none" stroke="url(#bigRing)" strokeWidth="10"
                          strokeDasharray={`${.72 * 2 * Math.PI * 58} ${2 * Math.PI * 58}`}
                          strokeLinecap="round"
                          transform="rotate(-90 70 70)"/>
                </svg>
                <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                  <div style={{ fontFamily: FONT.serif, fontSize: 44, fontWeight: 500, letterSpacing: "-.02em" }}>7.2</div>
                  <div style={{ fontSize: 10, color: isDark ? "rgba(232,236,245,.55)" : "rgba(10,14,26,.5)", marginTop: -2 }}>ánimo prom</div>
                </div>
              </div>
              <div>
                <Eyebrow>Paciente destacado · Semana 12</Eyebrow>
                <Display size={32}>Ana Martínez</Display>
                <div style={{ fontSize: 13, color: isDark ? "rgba(232,236,245,.65)" : "rgba(10,14,26,.55)", marginTop: 6 }}>
                  Última sesión hace 2 días · 88% adherencia · 20 registros esta semana
                </div>
                <div style={{ display: "flex", gap: 6, marginTop: 12, flexWrap: "wrap" }}>
                  <GradPill from="#14b8a6" to="#0d9488">Ansiedad</GradPill>
                  <GradPill from="#6366f1" to="#4f46e5">TCC activo</GradPill>
                  <GradPill from="#a855f7" to="#7c3aed">Progreso alto</GradPill>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <Eyebrow>Δ semana</Eyebrow>
                <div style={{ fontFamily: FONT.serif, fontSize: 56, fontWeight: 500, color: "#16a34a", letterSpacing: "-.03em" }}>+0.8</div>
                <button style={{
                  padding: "10px 18px", borderRadius: 999,
                  background: "#0a0e1a", color: "#fff",
                  border: "none", fontSize: 12, fontWeight: 600,
                  marginTop: 8, cursor: "pointer", fontFamily: FONT.sans,
                  boxShadow: "0 8px 20px -4px rgba(10,14,26,.4)",
                }}>Abrir ficha →</button>
              </div>
            </div>
          </Glass>

          {/* Metrics row */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
            {[
              { label: "Ánimo",       v: 76, grad: ["#14b8a6","#22d3ee"] },
              { label: "Respiración", v: 62, grad: ["#22d3ee","#6366f1"] },
              { label: "TCC",         v: 48, grad: ["#6366f1","#a855f7"] },
              { label: "Rutina",      v: 84, grad: ["#a855f7","#ec4899"] },
            ].map(m => (
              <Glass key={m.label} padding={18}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <Eyebrow>{m.label}</Eyebrow>
                  <div style={{ fontSize: 9, fontWeight: 700, color: "#16a34a", letterSpacing: ".08em" }}>+{Math.floor(m.v/10)}%</div>
                </div>
                <div style={{
                  fontFamily: FONT.serif, fontSize: 38, fontWeight: 500,
                  letterSpacing: "-.02em", marginTop: 6, lineHeight: 1,
                }}>{m.v}<span style={{ fontSize: 14, color: isDark ? "rgba(232,236,245,.4)" : "rgba(10,14,26,.4)", fontFamily: FONT.sans }}>%</span></div>
                <div style={{ height: 6, background: isDark ? "rgba(255,255,255,.08)" : "rgba(15,23,42,.08)", borderRadius: 999, marginTop: 10, overflow: "hidden" }}>
                  <div style={{
                    width: `${m.v}%`, height: "100%",
                    background: `linear-gradient(90deg, ${m.grad[0]}, ${m.grad[1]})`,
                    borderRadius: 999,
                  }}/>
                </div>
                <div style={{ fontSize: 11, color: isDark ? "rgba(232,236,245,.5)" : "rgba(10,14,26,.45)", marginTop: 6 }}>actividad semanal</div>
              </Glass>
            ))}
          </div>

          {/* Bottom: activity feed + alerts */}
          <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 14, flex: 1, minHeight: 0 }}>
            <Glass padding={20} style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                <Eyebrow>Actividad reciente</Eyebrow>
                <span style={{ fontSize: 10, color: isDark ? "rgba(232,236,245,.4)" : "rgba(10,14,26,.4)" }}>últimas 24h</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10, overflow: "auto" }}>
                {[
                  ["AM", "10:32", "Ana Martínez",  "Respiración completada · 4-7-8 · 5 ciclos",       ["#14b8a6","#0d9488"]],
                  ["AM", "09:15", "Ana Martínez",  "Registro de ánimo · 7/10 \"Buen día\"",            ["#16a34a","#22c55e"]],
                  ["DR", "09:02", "Diego Rodríguez", "TCC · Paso 3 completado",                       ["#6366f1","#4f46e5"]],
                  ["SL", "08:45", "Sofía Loretti", "Rutina mañana completada (4/4)",                  ["#a855f7","#7c3aed"]],
                ].map(([init, h, who, msg, grad], i) => (
                  <div key={i} style={{ display: "grid", gridTemplateColumns: "auto auto 1fr auto", gap: 12, alignItems: "center" }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: 12,
                      background: `linear-gradient(135deg, ${grad[0]}, ${grad[1]})`,
                      color: "#fff", fontWeight: 700, fontSize: 12,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      boxShadow: `0 4px 12px -2px ${grad[0]}55`,
                    }}>{init}</div>
                    <span style={{ fontSize: 10, fontFamily: FONT.mono, color: isDark ? "rgba(232,236,245,.4)" : "rgba(10,14,26,.4)" }}>{h}</span>
                    <div style={{ fontSize: 12, color: isDark ? "rgba(232,236,245,.8)" : "rgba(10,14,26,.75)" }}>
                      <strong style={{ color: isDark ? "#f0eee8" : "#0a0e1a" }}>{who}</strong> · {msg}
                    </div>
                    <span style={{ fontSize: 10, color: isDark ? "rgba(232,236,245,.35)" : "rgba(10,14,26,.35)" }}>→</span>
                  </div>
                ))}
              </div>
            </Glass>
            <Glass padding={20}>
              <Eyebrow color="#ef4444">Requieren atención</Eyebrow>
              <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 10 }}>
                {[
                  ["Martín G.", "Sin registros · 3 días", ["#f59e0b","#ef4444"]],
                  ["Laura T.",  "Ánimo en baja · 4.2",    ["#ef4444","#dc2626"]],
                  ["Diego R.",  "Pidió cambio de horario", ["#a855f7","#6366f1"]],
                ].map(([n, msg, grad], i) => (
                  <div key={i} style={{
                    padding: 12, borderRadius: 14,
                    background: isDark ? "rgba(0,0,0,.2)" : "rgba(255,255,255,.55)",
                    border: `1px solid ${isDark ? "rgba(255,255,255,.06)" : "rgba(15,23,42,.06)"}`,
                    display: "grid", gridTemplateColumns: "auto 1fr", gap: 10, alignItems: "center",
                  }}>
                    <div style={{
                      width: 6, height: 38, borderRadius: 3,
                      background: `linear-gradient(180deg, ${grad[0]}, ${grad[1]})`,
                    }}/>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 700 }}>{n}</div>
                      <div style={{ fontSize: 11, color: isDark ? "rgba(232,236,245,.6)" : "rgba(10,14,26,.55)" }}>{msg}</div>
                    </div>
                  </div>
                ))}
              </div>
            </Glass>
          </div>
        </div>
      </div>
    </PremiumFrame>
  );
}

// ── Premium · Installer Welcome ───────────────────────────────────────────────
function PremiumInstaller() {
  const t = useTheme();
  const isDark = t.mode === "dark";
  return (
    <PremiumFrame title="Instalador Suite" subtitle="Bienvenida" mesh="warm" width={840} height={620}>
      <div style={{ height: "100%", padding: "20px 40px 28px", display: "flex", flexDirection: "column", gap: 14 }}>
        {/* Stepper minimal */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {["Bienvenida","Cuenta","Consentimiento","Instalar","Listo"].map((s, i) => (
            <React.Fragment key={s}>
              <div style={{
                padding: i === 0 ? "5px 12px" : "5px 10px",
                borderRadius: 999,
                background: i === 0 ? "linear-gradient(135deg, #6366f1, #a855f7)" : "transparent",
                color: i === 0 ? "#fff" : (isDark ? "rgba(232,236,245,.5)" : "rgba(10,14,26,.4)"),
                fontSize: 10, fontWeight: 700, letterSpacing: ".02em",
              }}>{s}</div>
              {i < 4 && <div style={{ flex: i === 0 ? 0 : 1, height: 1, background: isDark ? "rgba(255,255,255,.1)" : "rgba(15,23,42,.1)" }}/>}
            </React.Fragment>
          ))}
        </div>

        {/* Hero */}
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 30, alignItems: "center" }}>
          <div>
            <Eyebrow color="#a855f7">Bienvenida</Eyebrow>
            <Display size={50} lineH={1.05}>
              Una herramienta<br/>
              <span style={{ fontStyle: "italic", background: "linear-gradient(135deg, #6366f1, #14b8a6, #a855f7)", WebkitBackgroundClip: "text", color: "transparent" }}>para acompañarte</span>
            </Display>
            <div style={{ fontSize: 14, color: isDark ? "rgba(232,236,245,.7)" : "rgba(10,14,26,.65)", lineHeight: 1.55, marginTop: 14, maxWidth: 380 }}>
              <strong style={{ color: isDark ? "#f0eee8" : "#0a0e1a" }}>NeuroMood Suite</strong> es una herramienta digital complementaria de bienestar emocional. En los próximos pasos vas a crear tu cuenta y configurar la app.
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 18, flexWrap: "wrap" }}>
              <GradPill from="#22c55e" to="#14b8a6" icon={<span>✓</span>}>Windows 10/11</GradPill>
              <GradPill from="#6366f1" to="#a855f7" icon={<span>🔒</span>}>Datos cifrados</GradPill>
              <GradPill from="#f59e0b" to="#ef4444" icon={<span>⚡</span>}>~280 MB</GradPill>
            </div>
          </div>
          {/* Logo treatment */}
          <div style={{ position: "relative", height: 280, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{
              position: "absolute", inset: 0,
              background: "radial-gradient(circle at 50% 50%, rgba(168,85,247,.45) 0%, rgba(99,102,241,.30) 30%, transparent 70%)",
              filter: "blur(20px)",
            }}/>
            <Glass padding={36} style={{ position: "relative", textAlign: "center", borderRadius: 28 }}>
              <NMLogo size={64}/>
              <div style={{ marginTop: 18, fontSize: 11, fontWeight: 700, letterSpacing: ".2em", color: isDark ? "rgba(232,236,245,.6)" : "rgba(10,14,26,.55)" }}>SUITE PARA PACIENTES</div>
              <div style={{ marginTop: 6, fontSize: 10, fontFamily: FONT.mono, color: isDark ? "rgba(232,236,245,.4)" : "rgba(10,14,26,.4)" }}>v1.0.0 · build 2026-05-16</div>
            </Glass>
          </div>
        </div>

        {/* Footer CTA */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 14, borderTop: `1px solid ${isDark ? "rgba(255,255,255,.06)" : "rgba(15,23,42,.06)"}` }}>
          <div style={{ fontSize: 10, color: isDark ? "rgba(232,236,245,.45)" : "rgba(10,14,26,.4)", fontFamily: FONT.mono }}>
            Instalador Suite v1.0.0
          </div>
          <button style={{
            padding: "14px 28px",
            borderRadius: 999,
            background: "linear-gradient(135deg, #6366f1, #a855f7)",
            color: "#fff", border: "none",
            fontSize: 14, fontWeight: 700, cursor: "pointer",
            boxShadow: "0 12px 28px -6px rgba(99,102,241,.55)",
            fontFamily: FONT.sans, letterSpacing: ".01em",
          }}>Empezar →</button>
        </div>
      </div>
    </PremiumFrame>
  );
}

Object.assign(window, {
  PremiumFrame, Glass, Display, Eyebrow, GradPill,
  PremiumHome, PremiumAnimo, PremiumHubDash, PremiumInstaller,
});
