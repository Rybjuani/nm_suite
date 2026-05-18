/* screens-hub.jsx — NeuroMood Hub (profesional)
 * Pantallas: Dashboard, Pacientes, Detalle, IA Asistente, Config
 */

// ── Sidebar Hub ───────────────────────────────────────────────────────────────
function HubSidebar({ active = "pacientes" }) {
  const t = useTheme();
  const items = [
    { id: "pacientes", label: "Pacientes",   icon: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="6" cy="6" r="2.5" stroke="currentColor" strokeWidth="1.4"/><path d="M2 14c0-2.2 1.8-4 4-4s4 1.8 4 4M11 7c1.4 0 2.5-1.1 2.5-2.5S12.4 2 11 2M14 14c0-2-1.5-3.5-3-3.8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg> },
    { id: "dashboard", label: "Dashboard",   icon: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="5" height="6" rx="1" stroke="currentColor" strokeWidth="1.4"/><rect x="2" y="10" width="5" height="4" rx="1" stroke="currentColor" strokeWidth="1.4"/><rect x="9" y="2" width="5" height="4" rx="1" stroke="currentColor" strokeWidth="1.4"/><rect x="9" y="8" width="5" height="6" rx="1" stroke="currentColor" strokeWidth="1.4"/></svg> },
    { id: "ia",        label: "IA Asistente", icon: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M4 4h8v6H8l-3 2.5V10H4V4z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/><circle cx="6" cy="7" r=".7" fill="currentColor"/><circle cx="10" cy="7" r=".7" fill="currentColor"/></svg> },
    { id: "config",    label: "Configuración", icon: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.4"/><path d="M8 2v1M8 13v1M2 8h1M13 8h1M3.5 3.5l.7.7M11.8 11.8l.7.7M3.5 12.5l.7-.7M11.8 4.2l.7-.7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg> },
  ];
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "18px 18px 14px", display: "flex", alignItems: "center", gap: 10 }}>
        <NMLogo size={22}/>
        <span style={{ fontSize: 10, fontWeight: 700, color: t.c.text3, letterSpacing: ".15em", textTransform: "uppercase", marginLeft: -4 }}>Hub</span>
      </div>
      <div style={{ padding: "6px 10px" }}>
        {items.map(it => {
          const a = it.id === active;
          return (
            <div key={it.id} style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "10px 12px",
              borderRadius: 10,
              background: a ? t.c.accentSoft : "transparent",
              color: a ? t.c.accent : t.c.text2,
              fontSize: 13, fontWeight: a ? 600 : 500,
              marginBottom: 2,
              cursor: "pointer",
              position: "relative",
            }}>
              {a && <div style={{ position: "absolute", left: -10, top: 8, bottom: 8, width: 3, borderRadius: 3, background: t.c.accent }}/>}
              {it.icon}
              <span>{it.label}</span>
            </div>
          );
        })}
      </div>
      <div style={{ marginTop: "auto", padding: 14, borderTop: `1px solid ${t.c.borderSoft}` }}>
        <SyncOrb state="ok"/>
        <div style={{ fontSize: 10, color: t.c.text4, marginTop: 6, fontFamily: FONT.mono }}>
          v2.1.0 · doctor@clinica.com
        </div>
      </div>
    </div>
  );
}

// ── Hub – Dashboard ──────────────────────────────────────────────────────────
function HubDashboard() {
  const t = useTheme();
  return (
    <AppWindow title="NeuroMood Hub" subtitle="Dashboard" width={1280} height={780}
      sidebar={{ content: <HubSidebar active="dashboard"/>, width: 200 }}>
      <div style={{ padding: "20px 28px 28px", height: "100%", overflow: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
          <SectionTitle eyebrow="Resumen" size="lg">Dashboard clínico</SectionTitle>
          <NMBadge tone="default">12 pacientes vinculados</NMBadge>
        </div>

        {/* Featured Card (paciente destacado) */}
        <NMCard padding={24} style={{ marginTop: 16, position: "relative", overflow: "hidden" }}>
          <div style={{
            position: "absolute", top: -50, right: -40, width: 200, height: 200,
            background: `radial-gradient(circle, ${t.c.tealSoft} 0%, transparent 70%)`,
            pointerEvents: "none",
          }}/>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 24, alignItems: "center" }}>
            <NMRing pct={72} size={92} stroke={7} tone="teal" value="7.2" label="ánimo prom"/>
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".12em", color: t.c.text3, textTransform: "uppercase" }}>
                Paciente destacado
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: t.c.text, marginTop: 4, letterSpacing: "-.015em" }}>
                Ana Martínez · Semana 12
              </div>
              <div style={{ fontSize: 13, color: t.c.text2, marginTop: 4 }}>
                12 semanas en programa · Última sesión: hace 2 días
              </div>
              <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
                <NMBadge tone="teal">Ansiedad</NMBadge>
                <NMBadge tone="accent">TCC</NMBadge>
                <NMBadge tone="violet">Progreso alto</NMBadge>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 10, color: t.c.text3, fontWeight: 600, letterSpacing: ".1em" }}>VS SEMANA ANT.</div>
              <div style={{ fontSize: 24, color: t.c.success, fontWeight: 700, marginTop: 4 }}>+0.8</div>
              <div style={{ fontSize: 11, color: t.c.text3, marginTop: 2 }}>tendencia positiva</div>
              <NMButton variant="primary" size="sm" style={{ marginTop: 12 }}>Abrir ficha →</NMButton>
            </div>
          </div>
        </NMCard>

        {/* Métricas */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginTop: 18 }}>
          {[
            { label: "Ánimo", v: 76, tone: "teal" },
            { label: "Respiración", v: 62, tone: "teal" },
            { label: "TCC", v: 48, tone: "accent" },
            { label: "Rutina", v: 84, tone: "violet" },
          ].map((m, i) => (
            <NMCard key={i} padding={16} style={{ display: "flex", gap: 14, alignItems: "center" }}>
              <NMRing pct={m.v} size={52} stroke={5} tone={m.tone} value={`${m.v}%`}/>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: t.c.text }}>{m.label}</div>
                <div style={{ fontSize: 11, color: t.c.text3, marginTop: 2 }}>actividad semanal</div>
              </div>
            </NMCard>
          ))}
        </div>

        {/* Actividad reciente + Riesgo */}
        <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 14, marginTop: 18 }}>
          <NMCard padding={20}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
              <SectionTitle eyebrow="Actividad" size="sm">Reciente en toda la clínica</SectionTitle>
              <NMBadge tone="default">últimas 24h</NMBadge>
            </div>
            {[
              ["10:32", "Ana M.", "Respiración completada · 4-7-8 · 5 ciclos", "teal"],
              ["09:15", "Ana M.", "Registro de ánimo · 7/10 \"Buen día\"",       "success"],
              ["09:02", "Diego R.", "TCC · Paso 3 completado",                   "accent"],
              ["08:45", "Sofía L.", "Rutina mañana completada (4/4)",            "violet"],
              ["yes.", "Martín G.", "Sin registros en 3 días",                   "warning"],
            ].map(([h, who, msg, tone], i) => (
              <div key={i} style={{
                display: "grid", gridTemplateColumns: "auto auto 1fr",
                gap: 12, padding: "10px 0",
                borderBottom: i < 4 ? `1px solid ${t.c.borderSoft}` : "none",
                alignItems: "center",
              }}>
                <div style={{ fontSize: 10, color: t.c.text3, fontFamily: FONT.mono, width: 48 }}>{h}</div>
                <span style={{ width: 6, height: 6, borderRadius: 999, background: t.c[tone] }}/>
                <div>
                  <div style={{ fontSize: 12, color: t.c.text }}>
                    <span style={{ fontWeight: 600 }}>{who}</span> · {msg}
                  </div>
                </div>
              </div>
            ))}
          </NMCard>
          <NMCard padding={20}>
            <SectionTitle eyebrow="Atención" size="sm">Requiere revisión</SectionTitle>
            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 4 }}>
              {[
                ["Martín G.", "Sin registros · 3 días",  "warning"],
                ["Laura T.",  "Ánimo en baja · 4.2 prom", "danger"],
                ["Diego R.",  "Pidió cambio de horario", "accent"],
              ].map(([n, msg, tone], i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 10,
                  padding: 10, borderRadius: 10,
                  background: t.c[`${tone}Soft`],
                  border: `1px solid ${t.c[tone]}22`,
                }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 999,
                    background: t.c.surface, color: t.c[tone],
                    fontWeight: 700, fontSize: 12,
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>{n.charAt(0)}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: t.c.text }}>{n}</div>
                    <div style={{ fontSize: 10, color: t.c.text2 }}>{msg}</div>
                  </div>
                  <NMButton variant="ghost" size="sm">Ver</NMButton>
                </div>
              ))}
            </div>
          </NMCard>
        </div>
      </div>
    </AppWindow>
  );
}

// ── Hub – Pacientes (lista) ──────────────────────────────────────────────────
function HubPacientes() {
  const t = useTheme();
  const patients = [
    { name: "Ana Martínez",   id: "AM-7842", mood: 7.2, adherence: 88, last: "hace 2h",  active: true, tag: "Ansiedad" },
    { name: "Diego Rodríguez", id: "DR-1199", mood: 6.4, adherence: 72, last: "hoy 09:02", tag: "TCC" },
    { name: "Sofía Loretti",   id: "SL-3320", mood: 8.1, adherence: 94, last: "hoy 08:45", tag: "Depresión leve" },
    { name: "Martín García",   id: "MG-4421", mood: null, adherence: 18, last: "hace 3d",  tag: "Adicción", warn: true },
    { name: "Laura Torres",    id: "LT-9012", mood: 4.2, adherence: 64, last: "ayer 21:30", tag: "Trastorno bipolar", warn: true },
    { name: "Pablo Núñez",     id: "PN-5530", mood: 6.8, adherence: 81, last: "ayer 18:00", tag: "Ansiedad" },
    { name: "Camila Ríos",     id: "CR-2003", mood: 7.5, adherence: 90, last: "hoy 07:10", tag: "Burnout" },
  ];
  return (
    <AppWindow title="NeuroMood Hub" subtitle="Pacientes" width={1280} height={780}
      sidebar={{ content: <HubSidebar active="pacientes"/>, width: 200 }}>
      <div style={{ padding: "20px 28px 28px", height: "100%", overflow: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <SectionTitle eyebrow={`${patients.length} vinculados`} size="lg">Pacientes</SectionTitle>
          <div style={{ display: "flex", gap: 8 }}>
            <NMButton variant="secondary" icon={<span>↻</span>}>Sincronizar</NMButton>
            <NMButton variant="primary" icon={<span>+</span>}>Nuevo paciente</NMButton>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 12, marginBottom: 14 }}>
          <NMInput placeholder="Buscar por nombre o ID..." icon={<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="6" cy="6" r="4" stroke="currentColor" strokeWidth="1.4"/><path d="M9 9l3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg>}/>
          <div style={{ display: "flex", gap: 6 }}>
            <NMBadge tone="accent">Todos · 7</NMBadge>
            <NMBadge tone="default">Alta actividad · 4</NMBadge>
            <NMBadge tone="warning">Sin registros · 1</NMBadge>
            <NMBadge tone="danger">Atención · 2</NMBadge>
          </div>
        </div>

        <NMCard padding={0}>
          <div style={{
            display: "grid",
            gridTemplateColumns: "1.7fr .9fr .8fr 1fr .9fr auto",
            gap: 14, padding: "12px 20px",
            borderBottom: `1px solid ${t.c.borderSoft}`,
            background: t.c.bgAlt,
            fontSize: 10, fontWeight: 700, letterSpacing: ".1em",
            color: t.c.text3, textTransform: "uppercase",
          }}>
            <div>Paciente</div>
            <div>Etiqueta</div>
            <div>Ánimo</div>
            <div>Adherencia</div>
            <div>Última sesión</div>
            <div></div>
          </div>
          {patients.map((p, i) => (
            <div key={p.id} style={{
              display: "grid",
              gridTemplateColumns: "1.7fr .9fr .8fr 1fr .9fr auto",
              gap: 14, padding: "14px 20px",
              borderBottom: i < patients.length - 1 ? `1px solid ${t.c.borderSoft}` : "none",
              background: p.active ? t.c.accentSoft + "40" : "transparent",
              alignItems: "center",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 999,
                  background: `linear-gradient(135deg, ${t.c.accent}, ${t.c.teal})`,
                  color: "#fff", fontSize: 12, fontWeight: 700,
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>{p.name.split(" ").map(n => n[0]).slice(0,2).join("")}</div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: t.c.text }}>{p.name}</div>
                  <div style={{ fontSize: 10, color: t.c.text3, fontFamily: FONT.mono }}>{p.id}</div>
                </div>
              </div>
              <NMBadge tone="default">{p.tag}</NMBadge>
              <div style={{
                fontSize: 14, fontWeight: 700,
                color: p.mood === null ? t.c.text3 : (p.mood >= 7 ? t.c.success : p.mood >= 4 ? t.c.warning : t.c.danger),
                fontFamily: FONT.mono,
              }}>{p.mood?.toFixed(1) ?? "—"}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ flex: 1, height: 6, borderRadius: 3, background: t.c.elevated, overflow: "hidden" }}>
                  <div style={{
                    width: `${p.adherence}%`, height: "100%",
                    background: p.adherence >= 70 ? t.c.success : p.adherence >= 40 ? t.c.warning : t.c.danger,
                    borderRadius: 3,
                  }}/>
                </div>
                <span style={{ fontSize: 11, color: t.c.text2, fontFamily: FONT.mono, width: 30 }}>{p.adherence}%</span>
              </div>
              <div style={{ fontSize: 11, color: t.c.text2 }}>{p.last}</div>
              <NMButton variant={p.active ? "primary" : "ghost"} size="sm">{p.active ? "Abrir" : "Ver"}</NMButton>
            </div>
          ))}
        </NMCard>
      </div>
    </AppWindow>
  );
}

// ── Hub – Detalle paciente ───────────────────────────────────────────────────
function HubDetalle() {
  const t = useTheme();
  const [tab, setTab] = React.useState("registros");
  const tabs = ["registros", "asignar", "banco", "ia"];
  const labels = { registros: "Registros", asignar: "Asignar", banco: "Banco", ia: "IA" };

  return (
    <AppWindow title="NeuroMood Hub" subtitle="Ana Martínez" width={1280} height={780}
      sidebar={{ content: <HubSidebar active="pacientes"/>, width: 200 }}>
      <div style={{ padding: "20px 28px 28px", height: "100%", overflow: "auto" }}>
        {/* Patient header */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "auto 1fr auto",
          gap: 18, alignItems: "center",
          marginBottom: 16,
        }}>
          <NMButton variant="ghost" size="sm">← Pacientes</NMButton>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{
              width: 56, height: 56, borderRadius: 999,
              background: `linear-gradient(135deg, ${t.c.accent}, ${t.c.teal})`,
              color: "#fff", fontSize: 20, fontWeight: 700,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>AM</div>
            <div>
              <div style={{ fontSize: 20, fontWeight: 700, color: t.c.text, letterSpacing: "-.01em" }}>
                Ana Martínez
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 4, fontSize: 11, color: t.c.text3 }}>
                <span style={{ fontFamily: FONT.mono }}>ID: AM-7842</span>
                <span>·</span>
                <span>Semana 12 en programa</span>
                <span>·</span>
                <span style={{ color: t.c.success }}>● Activa</span>
              </div>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <NMButton variant="secondary" size="sm">Exportar PDF</NMButton>
            <NMButton variant="primary" size="sm">Sesión nueva</NMButton>
          </div>
        </div>

        {/* Tabs */}
        <div style={{
          display: "flex", gap: 4, padding: 4,
          background: t.c.elevated, borderRadius: RADIUS.md,
          width: "fit-content",
        }}>
          {tabs.map(tk => (
            <div key={tk} onClick={() => setTab(tk)} style={{
              padding: "8px 18px", borderRadius: 8,
              background: tab === tk ? t.c.surface : "transparent",
              boxShadow: tab === tk ? t.s.sm : "none",
              fontSize: 12, fontWeight: 600,
              color: tab === tk ? t.c.text : t.c.text2,
              cursor: "pointer",
            }}>{labels[tk]}</div>
          ))}
        </div>

        {/* Content */}
        <div style={{ marginTop: 18 }}>
          {tab === "registros" && (
            <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 16 }}>
              <NMCard padding={22}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
                  <SectionTitle eyebrow="Evolución" size="md">Ánimo · últimos 30 días</SectionTitle>
                  <NMBadge tone="success">Promedio 7.2/10</NMBadge>
                </div>
                <div style={{ height: 220, marginTop: 12, position: "relative" }}>
                  <svg viewBox="0 0 600 220" preserveAspectRatio="none" style={{ width: "100%", height: "100%" }}>
                    <defs>
                      <linearGradient id="hubAnimo" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={t.c.teal} stopOpacity=".22"/>
                        <stop offset="100%" stopColor={t.c.teal} stopOpacity="0"/>
                      </linearGradient>
                    </defs>
                    {/* gridlines */}
                    {[40, 90, 140, 190].map(y => (
                      <line key={y} x1="30" y1={y} x2="595" y2={y} stroke={t.c.borderSoft} strokeWidth="1" strokeDasharray="2 4"/>
                    ))}
                    {/* y-axis labels */}
                    {[[40, "10"], [90, "7"], [140, "5"], [190, "2"]].map(([y, l]) => (
                      <text key={l} x="20" y={Number(y) + 4} fill={t.c.text3} fontSize="9" textAnchor="end" fontFamily="JetBrains Mono">{l}</text>
                    ))}
                    {/* area */}
                    <path d="M30 130 C 80 120, 110 145, 160 110 S 240 70, 290 80 S 380 60, 430 50 S 520 40, 595 35 L 595 220 L 30 220 Z" fill="url(#hubAnimo)"/>
                    {/* line */}
                    <path d="M30 130 C 80 120, 110 145, 160 110 S 240 70, 290 80 S 380 60, 430 50 S 520 40, 595 35" fill="none" stroke={t.c.teal} strokeWidth="2.2"/>
                    {/* avg line */}
                    <line x1="30" y1="68" x2="595" y2="68" stroke={t.c.teal} strokeWidth="1" strokeDasharray="4 4" opacity=".5"/>
                    <text x="555" y="62" fill={t.c.teal} fontSize="9" fontFamily="JetBrains Mono">prom 7.2</text>
                    {/* points */}
                    {[[30,130],[160,110],[290,80],[430,50],[595,35]].map(([x,y]) => (
                      <circle key={x} cx={x} cy={y} r="3" fill={t.c.surface} stroke={t.c.teal} strokeWidth="1.5"/>
                    ))}
                  </svg>
                </div>
              </NMCard>
              <NMCard padding={20}>
                <SectionTitle eyebrow="Adherencia" size="sm">Por módulo (7 días)</SectionTitle>
                {[
                  ["Ánimo", 90, "teal"],
                  ["Respiración", 72, "teal"],
                  ["TCC", 50, "accent"],
                  ["Rutina", 84, "violet"],
                  ["Actividades", 60, "success"],
                ].map(([n, v, tone], i) => (
                  <div key={i} style={{ display: "grid", gridTemplateColumns: "84px 1fr 38px", alignItems: "center", gap: 10, marginTop: 10 }}>
                    <span style={{ fontSize: 12, color: t.c.text2 }}>{n}</span>
                    <div style={{ height: 7, borderRadius: 4, background: t.c.elevated, overflow: "hidden" }}>
                      <div style={{ width: `${v}%`, height: "100%", background: t.c[tone], borderRadius: 4 }}/>
                    </div>
                    <span style={{ fontSize: 11, fontFamily: FONT.mono, color: t.c.text2, textAlign: "right" }}>{v}%</span>
                  </div>
                ))}
              </NMCard>
              <NMCard padding={0} style={{ gridColumn: "span 2" }}>
                <div style={{
                  display: "grid", gridTemplateColumns: "80px 110px 1fr 110px",
                  padding: "12px 20px",
                  borderBottom: `1px solid ${t.c.borderSoft}`,
                  background: t.c.bgAlt,
                  fontSize: 10, fontWeight: 700, color: t.c.text3, letterSpacing: ".1em", textTransform: "uppercase",
                }}>
                  <div>Fecha</div><div>Módulo</div><div>Detalle</div><div>Métrica</div>
                </div>
                {[
                  ["hoy 09:15", "Ánimo",       "Buen día — desayuné en familia", "7/10", "success"],
                  ["hoy 10:32", "Respiración", "4-7-8 · 5 ciclos · 3 min",     "completa", "teal"],
                  ["ayer 21:30","TCC",         "Reunión laboral · Ansiedad 7",  "Paso 3/4", "accent"],
                  ["ayer 18:00","Actividades", "Caminata 20 min · Física",      "completa", "success"],
                ].map(([d, m, det, val, tone], i) => (
                  <div key={i} style={{
                    display: "grid", gridTemplateColumns: "80px 110px 1fr 110px",
                    padding: "12px 20px", alignItems: "center",
                    borderBottom: i < 3 ? `1px solid ${t.c.borderSoft}` : "none",
                  }}>
                    <span style={{ fontSize: 11, color: t.c.text3, fontFamily: FONT.mono }}>{d}</span>
                    <NMBadge tone={tone}>{m}</NMBadge>
                    <span style={{ fontSize: 12, color: t.c.text }}>{det}</span>
                    <span style={{ fontSize: 12, color: t.c.text2, fontFamily: FONT.mono, textAlign: "right" }}>{val}</span>
                  </div>
                ))}
              </NMCard>
            </div>
          )}

          {tab === "asignar" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <NMCard padding={22}>
                <SectionTitle eyebrow="Tarea de rutina" size="md">Asignar nueva tarea</SectionTitle>
                <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 14 }}>
                  <NMInput placeholder="Descripción de la tarea…" value="Hidratarme antes del desayuno"/>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                    {["Mañana", "Tarde", "Noche"].map((s, i) => (
                      <div key={s} style={{
                        padding: 10, borderRadius: 10,
                        background: i === 0 ? t.c.accentSoft : t.c.surface,
                        border: `1px solid ${i === 0 ? t.c.accent : t.c.border}`,
                        textAlign: "center", fontSize: 12, fontWeight: 600,
                        color: i === 0 ? t.c.accent : t.c.text2,
                      }}>{s}</div>
                    ))}
                  </div>
                  <NMButton variant="primary" fullWidth>Asignar tarea</NMButton>
                </div>
              </NMCard>
              <NMCard padding={22}>
                <SectionTitle eyebrow="Recordatorio remoto" size="md">Enviar recordatorio</SectionTitle>
                <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 14 }}>
                  <NMInput placeholder="Mensaje…" value="Acordate de tu pausa de respiración 🌬"/>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 10 }}>
                    <NMInput placeholder="22:00" value="22:00" icon={<span style={{ fontSize: 11 }}>⏰</span>}/>
                    <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                      {["L","M","M","J","V","S","D"].map((d, i) => (
                        <div key={i} style={{
                          flex: 1, height: 32, borderRadius: 8,
                          background: i < 5 ? t.c.accentSoft : t.c.elevated,
                          color: i < 5 ? t.c.accent : t.c.text3,
                          fontSize: 11, fontWeight: 700,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          border: i < 5 ? `1px solid ${t.c.accent}33` : `1px solid ${t.c.borderSoft}`,
                        }}>{d}</div>
                      ))}
                    </div>
                  </div>
                  <NMButton variant="primary" fullWidth>Enviar recordatorio</NMButton>
                </div>
              </NMCard>
              <NMCard padding={20} style={{ gridColumn: "span 2" }}>
                <SectionTitle eyebrow="Asignadas" size="sm">Tareas y recordatorios vigentes</SectionTitle>
                <div style={{ marginTop: 8 }}>
                  {[
                    ["Pausa respiración", "Todos los días · 18:00", "warning", "vigente"],
                    ["Diario gratitud",   "Lun a Vie · 21:30",      "violet",  "vigente"],
                    ["Caminata 20 min",   "L M V · variable",       "success", "pausada"],
                  ].map(([n, sch, tone, st], i) => (
                    <div key={i} style={{
                      display: "grid", gridTemplateColumns: "auto 1fr auto auto",
                      gap: 14, alignItems: "center",
                      padding: "10px 0",
                      borderBottom: i < 2 ? `1px solid ${t.c.borderSoft}` : "none",
                    }}>
                      <span style={{ width: 6, height: 6, borderRadius: 999, background: t.c[tone] }}/>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 500, color: t.c.text }}>{n}</div>
                        <div style={{ fontSize: 11, color: t.c.text3 }}>{sch}</div>
                      </div>
                      <NMBadge tone={st === "vigente" ? "success" : "default"}>{st}</NMBadge>
                      <NMButton variant="ghost" size="sm">Editar</NMButton>
                    </div>
                  ))}
                </div>
              </NMCard>
            </div>
          )}

          {tab === "banco" && (
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 16 }}>
              <NMCard padding={22}>
                <SectionTitle eyebrow="Nueva actividad" size="md">Agregar al banco</SectionTitle>
                <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 14 }}>
                  <NMInput placeholder="Nombre de la actividad…" value="Yoga matinal"/>
                  <NMInput placeholder="Descripción breve…" value="15 min de yoga suave antes del desayuno"/>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                    <NMInput placeholder="Categoría" value="Física" suffix="▾"/>
                    <NMInput placeholder="Ánimo" value="4–7 medio" suffix="▾"/>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <NMButton variant="secondary" icon={<span>✦</span>}>IA: completar descripción</NMButton>
                    <NMButton variant="primary" style={{ marginLeft: "auto" }}>Agregar</NMButton>
                  </div>
                </div>
              </NMCard>
              <NMCard padding={20}>
                <SectionTitle eyebrow="Banco activo" size="sm">33 actividades</SectionTitle>
                <div style={{ maxHeight: 320, overflow: "auto" }}>
                  {[
                    ["Caminata 30 min", "Física", t.c.teal],
                    ["Llamar a familiar", "Social", t.c.warning],
                    ["Lectura ficción", "Cognitiva", t.c.info],
                    ["Bañarse con calma", "Autocuidado", t.c.success],
                    ["Tocar guitarra", "Maestría", t.c.accent],
                    ["Salir a la naturaleza", "Placer", t.c.violet],
                  ].map(([n, c, color], i) => (
                    <div key={i} style={{
                      display: "grid", gridTemplateColumns: "auto 1fr auto",
                      gap: 10, padding: "8px 0",
                      borderBottom: i < 5 ? `1px solid ${t.c.borderSoft}` : "none",
                      alignItems: "center",
                    }}>
                      <span style={{ width: 6, height: 6, borderRadius: 999, background: color }}/>
                      <span style={{ fontSize: 12, color: t.c.text }}>{n}</span>
                      <span style={{ fontSize: 10, color: t.c.text3, fontFamily: FONT.mono }}>{c}</span>
                    </div>
                  ))}
                </div>
              </NMCard>
            </div>
          )}

          {tab === "ia" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <NMCard padding={22}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <SectionTitle eyebrow="Resumen IA" size="md">Evolución de Ana</SectionTitle>
                  <NMBadge tone="success" icon={<span style={{ width: 6, height: 6, borderRadius: 999, background: t.c.success, display: "inline-block" }}/>}>Groq · llama3-70b</NMBadge>
                </div>
                <div style={{
                  marginTop: 14, padding: 16, borderRadius: 12,
                  background: t.c.elevated,
                  border: `1px solid ${t.c.borderSoft}`,
                  fontSize: 12, color: t.c.text2, lineHeight: 1.65,
                }}>
                  <p style={{ margin: 0 }}>
                    En las últimas <strong style={{ color: t.c.text }}>2 semanas</strong> el promedio de ánimo subió de <strong style={{ color: t.c.text }}>6.4 a 7.2/10</strong> (+12.5%). La adherencia a respiración es del <strong style={{ color: t.c.teal }}>72%</strong>, con los registros concentrados en la mañana (08–10h). El módulo TCC quedó pausado en el paso 3 hace 4 días.
                  </p>
                  <p style={{ margin: "10px 0 0" }}>
                    <strong style={{ color: t.c.text }}>Sugerencias:</strong> retomar TCC con una sesión breve y revisar disparadores en el horario laboral (13–15h, donde el ánimo cae).
                  </p>
                </div>
                <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                  <NMButton variant="ghost" size="sm">Regenerar</NMButton>
                  <NMButton variant="secondary" size="sm">Copiar</NMButton>
                  <NMButton variant="primary" size="sm" style={{ marginLeft: "auto" }}>Generar acciones →</NMButton>
                </div>
              </NMCard>
              <NMCard padding={22}>
                <SectionTitle eyebrow="Acciones sugeridas" size="md">3 propuestas concretas</SectionTitle>
                <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 14 }}>
                  {[
                    ["Retomar TCC", "Sesión breve de 10 min · paso 3 (reestructuración)", "accent"],
                    ["Pausa en horario crítico", "Recordatorio a las 13:30 con respiración 4-7-8", "teal"],
                    ["Actividad social", "Sugerir café con un amigo este fin de semana", "warning"],
                  ].map(([n, d, tone], i) => (
                    <div key={i} style={{
                      padding: 12, borderRadius: 10,
                      background: t.c[`${tone}Soft`],
                      border: `1px solid ${t.c[tone]}22`,
                      display: "grid", gridTemplateColumns: "1fr auto", gap: 8, alignItems: "center",
                    }}>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: t.c.text }}>{n}</div>
                        <div style={{ fontSize: 11, color: t.c.text2, marginTop: 2 }}>{d}</div>
                      </div>
                      <NMButton variant="soft" size="sm">Aplicar</NMButton>
                    </div>
                  ))}
                </div>
              </NMCard>
            </div>
          )}
        </div>
      </div>
    </AppWindow>
  );
}

// ── Hub – IA Asistente (chat) ────────────────────────────────────────────────
function HubIA() {
  const t = useTheme();
  return (
    <AppWindow title="NeuroMood Hub" subtitle="IA Asistente" width={1280} height={780}
      sidebar={{ content: <HubSidebar active="ia"/>, width: 200 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", height: "100%" }}>
        <div style={{ display: "grid", gridTemplateRows: "auto 1fr auto auto", padding: "20px 28px 20px", overflow: "hidden" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <SectionTitle eyebrow="Conversación clínica" size="lg">IA Asistente</SectionTitle>
            <NMBadge tone="success" icon={<span style={{ width: 6, height: 6, borderRadius: 999, background: t.c.success, display: "inline-block" }}/>}>
              Groq · llama3-70b
            </NMBadge>
          </div>
          <div style={{ overflow: "auto", display: "flex", flexDirection: "column", gap: 12, paddingRight: 6 }}>
            <ChatBubble who="ia">
              Hola, Dr. García. Analicé los datos de <strong>Ana Martínez</strong> de las últimas 2 semanas.<br/>
              ¿Querés un resumen ejecutivo o una pregunta específica sobre adherencia, ánimo o TCC?
            </ChatBubble>
            <ChatBubble who="user">¿Cómo estuvo su ánimo esta semana comparado con la anterior?</ChatBubble>
            <ChatBubble who="ia">
              El promedio fue <strong>7.2/10</strong> esta semana vs <strong>6.4/10</strong> la anterior — tendencia positiva (+12.5%).
              Los días con mayor puntaje (8, 8.5) coinciden con sesiones de respiración registradas a la mañana.
              <div style={{ marginTop: 10, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                <MiniStat label="Esta semana" value="7.2" tone="success"/>
                <MiniStat label="Anterior"    value="6.4" tone="default"/>
                <MiniStat label="Δ"           value="+0.8" tone="success"/>
              </div>
            </ChatBubble>
            <ChatBubble who="user">¿Qué intervención concreta podría sugerir?</ChatBubble>
            <ChatBubble who="ia" typing/>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
            {["Analizar ánimo reciente", "Proponer actividades", "Revisar distorsiones"].map(t2 => (
              <div key={t2} style={{
                padding: "6px 12px", borderRadius: 999,
                background: t.c.elevated, border: `1px solid ${t.c.borderSoft}`,
                fontSize: 11, color: t.c.text2, cursor: "pointer", fontWeight: 500,
              }}>{t2}</div>
            ))}
          </div>
          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
            <NMInput placeholder="Escribí tu consulta…" style={{ flex: 1 }}/>
            <NMButton variant="primary" icon={<span>↑</span>}>Enviar</NMButton>
          </div>
        </div>
        <div style={{ background: t.c.bgAlt, borderLeft: `1px solid ${t.c.borderSoft}`, padding: 20 }}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: ".12em", color: t.c.text3, textTransform: "uppercase" }}>Contexto activo</div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 10 }}>
            <div style={{
              width: 42, height: 42, borderRadius: 999,
              background: `linear-gradient(135deg, ${t.c.accent}, ${t.c.teal})`,
              color: "#fff", fontSize: 14, fontWeight: 700,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>AM</div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: t.c.text }}>Ana Martínez</div>
              <div style={{ fontSize: 11, color: t.c.text3 }}>Semana 12 · Ansiedad</div>
            </div>
          </div>
          <div style={{ marginTop: 16, fontSize: 11, color: t.c.text3, lineHeight: 1.6 }}>
            La IA tiene acceso a los registros cargados (ánimo, respiración, TCC, rutina) y la información clínica que vos compartas. No realiza diagnóstico ni reemplaza criterio profesional.
          </div>
          <div style={{ height: 1, background: t.c.borderSoft, margin: "16px 0" }}/>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: ".12em", color: t.c.text3, textTransform: "uppercase", marginBottom: 8 }}>Datos cargados</div>
          {[
            ["Ánimo", "20 registros"],
            ["Respiración", "15 sesiones"],
            ["TCC", "8 entradas"],
            ["Rutina", "84% adherencia"],
          ].map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 11, padding: "4px 0" }}>
              <span style={{ color: t.c.text2 }}>{k}</span>
              <span style={{ color: t.c.text, fontWeight: 500 }}>{v}</span>
            </div>
          ))}
        </div>
      </div>
    </AppWindow>
  );
}

function ChatBubble({ who, children, typing = false }) {
  const t = useTheme();
  const isUser = who === "user";
  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
    }}>
      <div style={{
        maxWidth: "75%",
        padding: "12px 16px",
        borderRadius: isUser ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
        background: isUser ? t.c.accent : t.c.surface,
        color: isUser ? "#fff" : t.c.text,
        fontSize: 13,
        lineHeight: 1.55,
        border: isUser ? "none" : `1px solid ${t.c.borderSoft}`,
        boxShadow: t.s.sm,
      }}>
        {typing ? (
          <span style={{ display: "inline-flex", gap: 4, padding: "2px 0" }}>
            {[0, 1, 2].map(i => (
              <span key={i} style={{
                width: 6, height: 6, borderRadius: 999,
                background: t.c.text3,
                animation: `nmTyp 1.2s ${i*0.15}s infinite ease-in-out`,
              }}/>
            ))}
            <style>{`@keyframes nmTyp { 0%, 80%, 100% { transform: translateY(0); opacity: .35 } 40% { transform: translateY(-4px); opacity: 1 } }`}</style>
          </span>
        ) : children}
      </div>
    </div>
  );
}

function MiniStat({ label, value, tone }) {
  const t = useTheme();
  return (
    <div style={{
      padding: 8, borderRadius: 8,
      background: t.c[`${tone}Soft`] || t.c.elevated,
      textAlign: "center",
    }}>
      <div style={{ fontSize: 10, color: t.c.text3, marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 700, color: t.c[tone] || t.c.text, fontFamily: FONT.mono }}>{value}</div>
    </div>
  );
}

// ── Hub – Config ──────────────────────────────────────────────────────────────
function HubConfig() {
  const t = useTheme();
  return (
    <AppWindow title="NeuroMood Hub" subtitle="Configuración" width={1280} height={780}
      sidebar={{ content: <HubSidebar active="config"/>, width: 200 }}>
      <div style={{ padding: "20px 28px 28px", height: "100%", overflow: "auto" }}>
        <SectionTitle eyebrow="Preferencias" size="lg">Configuración</SectionTitle>
        <NMCard padding={20} style={{ marginTop: 14, display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 14, alignItems: "center" }}>
          <SyncOrb state="ok" size={14}/>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: t.c.text }}>Sincronizado con Supabase</div>
            <div style={{ fontSize: 11, color: t.c.text3, marginTop: 2 }}>Última verificación: hoy 14:23 · 12 pacientes</div>
          </div>
          <NMButton variant="secondary" size="sm">Sincronizar ahora</NMButton>
        </NMCard>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
          <NMCard padding={20}>
            <SectionTitle eyebrow="Conexión" size="md">Supabase</SectionTitle>
            <ConfigRow k="URL" v="https://xyz.supabase.co" mono/>
            <ConfigRow k="API Key" v="••••••••••4f3a" mono/>
            <ConfigRow k="Auto-sync" right={<NMToggle checked={true}/>}/>
            <ConfigRow k="Backup local" right={<NMToggle checked={true}/>}/>
            <ConfigRow k="Última verificación" v="hoy 14:23"/>
          </NMCard>
          <NMCard padding={20}>
            <SectionTitle eyebrow="Apariencia" size="md">Tema y tipografía</SectionTitle>
            <ConfigRow k="Tema" right={
              <div style={{ display: "flex", gap: 4, padding: 3, background: t.c.elevated, borderRadius: 8 }}>
                <span style={{ padding: "4px 10px", fontSize: 11, fontWeight: 600, background: t.c.surface, borderRadius: 6, color: t.c.text, boxShadow: t.s.sm }}>Claro</span>
                <span style={{ padding: "4px 10px", fontSize: 11, color: t.c.text3 }}>Oscuro</span>
                <span style={{ padding: "4px 10px", fontSize: 11, color: t.c.text3 }}>Sistema</span>
              </div>
            }/>
            <ConfigRow k="Densidad" right={
              <div style={{ display: "flex", gap: 4, padding: 3, background: t.c.elevated, borderRadius: 8 }}>
                <span style={{ padding: "4px 10px", fontSize: 11, color: t.c.text3 }}>Compacta</span>
                <span style={{ padding: "4px 10px", fontSize: 11, fontWeight: 600, background: t.c.surface, borderRadius: 6, color: t.c.text, boxShadow: t.s.sm }}>Normal</span>
                <span style={{ padding: "4px 10px", fontSize: 11, color: t.c.text3 }}>Cómoda</span>
              </div>
            }/>
            <ConfigRow k="Proveedor IA" v="Groq · llama3-70b"/>
            <ConfigRow k="Modelo embeddings" v="text-embedding-3-small"/>
          </NMCard>
          <NMCard padding={20}>
            <SectionTitle eyebrow="Seguridad" size="md">Acceso y datos</SectionTitle>
            <ConfigRow k="Bloqueo automático" v="5 min de inactividad"/>
            <ConfigRow k="2FA" right={<NMToggle checked={true}/>}/>
            <ConfigRow k="Cifrado en reposo" right={<NMBadge tone="success">AES-256</NMBadge>}/>
            <ConfigRow k="Logs auditables" right={<NMToggle checked={true}/>}/>
            <ConfigRow k="Retención datos" v="365 días"/>
          </NMCard>
          <NMCard padding={20}>
            <SectionTitle eyebrow="Log" size="md">Sincronización reciente</SectionTitle>
            <div style={{ fontFamily: FONT.mono, fontSize: 11, lineHeight: 1.8, color: t.c.text2, marginTop: 10 }}>
              <div><span style={{ color: t.c.success }}>✓</span> 14:23:01 — Sync completada · 12 pacientes</div>
              <div><span style={{ color: t.c.teal }}>↻</span> 14:23:00 — Conectando a Supabase…</div>
              <div><span style={{ color: t.c.success }}>✓</span> 14:10:44 — Backup local generado</div>
              <div><span style={{ color: t.c.warning }}>⚠</span> 13:12:08 — Timeout (reintentado ok)</div>
              <div><span style={{ color: t.c.success }}>✓</span> 13:10:00 — Sync completada · 12 pacientes</div>
            </div>
          </NMCard>
        </div>
      </div>
    </AppWindow>
  );
}

function ConfigRow({ k, v, right = null, mono = false }) {
  const t = useTheme();
  return (
    <div style={{
      display: "flex", justifyContent: "space-between",
      padding: "10px 0", alignItems: "center",
      borderBottom: `1px solid ${t.c.borderSoft}`,
      fontSize: 12,
    }}>
      <span style={{ color: t.c.text3 }}>{k}</span>
      {right ? right : (
        <span style={{
          color: t.c.text, fontWeight: 500,
          fontFamily: mono ? FONT.mono : FONT.sans,
        }}>{v}</span>
      )}
    </div>
  );
}

Object.assign(window, {
  HubSidebar, HubDashboard, HubPacientes, HubDetalle, HubIA, HubConfig,
  ChatBubble, MiniStat, ConfigRow,
});
