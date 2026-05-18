/* screens-suite.jsx — NeuroMood Suite (paciente)
 * Pantallas: Home, Ánimo, Respiración, TCC, Rutina, Actividades, Timer, Avisos
 */

// ── Datos de módulos (paralelos al MODULES_CONFIG real) ──────────────────────
const SUITE_MODULES = [
  { id: "animo",       title: "Ánimo",       desc: "Registro emocional diario", tone: "teal",    progress: 70, status: { tone: "warning", text: "🔥 5 días" } },
  { id: "respiracion", title: "Respiración", desc: "Técnicas de calma",          tone: "teal",    progress: 60, status: { tone: "teal",    text: "3 ciclos" } },
  { id: "tcc",         title: "TCC",         desc: "Pensamientos automáticos",   tone: "accent",  progress: 25, status: { tone: "accent",  text: "Paso 1/4" } },
  { id: "rutina",      title: "Rutina",      desc: "Checklist del día",          tone: "violet",  progress: 80, status: { tone: "success", text: "8/10 · 80%" } },
  { id: "actividades", title: "Actividades", desc: "Activación conductual",      tone: "success", progress: 100, status: { tone: "success", text: "3 hoy" } },
  { id: "timer",       title: "Timer",       desc: "Sesiones de enfoque",        tone: "accent",  progress: 40, status: { tone: "accent",  text: "Activo" } },
  { id: "avisos",      title: "Avisos",      desc: "Recordatorios del día",      tone: "warning", progress: 40, status: { tone: "warning", text: "2/5" } },
];

// ── ModuleCard ────────────────────────────────────────────────────────────────
function ModuleCard({ mod }) {
  const t = useTheme();
  const iconFor = (id) => {
    const s = 18;
    const stroke = t.c[mod.tone] || t.c.accent;
    const props = { width: s, height: s, viewBox: "0 0 24 24", fill: "none", stroke, strokeWidth: 1.6, strokeLinecap: "round", strokeLinejoin: "round" };
    switch (id) {
      case "animo":       return <svg {...props}><path d="M21 8.5c0-3-2.4-5-5-5-1.6 0-3 .8-4 2-1-1.2-2.4-2-4-2-2.6 0-5 2-5 5 0 6 9 11 9 11s9-5 9-11z"/></svg>;
      case "respiracion": return <svg {...props}><path d="M3 12h4l2-3 4 6 2-3h6"/></svg>;
      case "tcc":         return <svg {...props}><path d="M9 3a4 4 0 0 0-4 4v3a4 4 0 0 0 1 2.6V18a3 3 0 0 0 3 3 3 3 0 0 0 3-3v-1"/><path d="M15 3a4 4 0 0 1 4 4v3a4 4 0 0 1-1 2.6V18a3 3 0 0 1-3 3 3 3 0 0 1-3-3v-1"/></svg>;
      case "rutina":      return <svg {...props}><circle cx="6" cy="6" r="2"/><path d="M11 6h9"/><circle cx="6" cy="12" r="2"/><path d="M11 12h9"/><circle cx="6" cy="18" r="2"/><path d="M11 18h9"/></svg>;
      case "actividades": return <svg {...props}><circle cx="12" cy="5" r="2"/><path d="M9 22l3-7 3 7M8 12l4-2 4 2-2 3h-4l-2-3z"/></svg>;
      case "timer":       return <svg {...props}><circle cx="12" cy="13" r="8"/><path d="M12 13V9M9 2h6"/></svg>;
      case "avisos":      return <svg {...props}><path d="M6 9a6 6 0 0 1 12 0c0 6 2 7 2 7H4s2-1 2-7z"/><path d="M10 20a2 2 0 0 0 4 0"/></svg>;
    }
  };
  return (
    <NMCard interactive accent={mod.tone} padding={16} style={{ minHeight: 120 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10,
          background: t.c[`${mod.tone}Soft`] || t.c.elevated,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>{iconFor(mod.id)}</div>
        <NMRing pct={mod.progress} size={32} stroke={2.5} tone={mod.tone}
                value={`${mod.progress}%`}/>
      </div>
      <div style={{ marginTop: 12, fontSize: 15, fontWeight: 600, color: t.c.text, letterSpacing: "-.01em" }}>
        {mod.title}
      </div>
      <div style={{ fontSize: 12, color: t.c.text3, marginTop: 2 }}>
        {mod.desc}
      </div>
      <div style={{ marginTop: 12 }}>
        <NMBadge tone={mod.status.tone}>{mod.status.text}</NMBadge>
      </div>
    </NMCard>
  );
}

// ── Suite – Home ──────────────────────────────────────────────────────────────
function SuiteHome({ name = "Ana" }) {
  const t = useTheme();
  return (
    <AppWindow title="NeuroMood Suite" subtitle="Paciente" width={1080} height={720}>
      <NMHeader
        center={<NMLogo size={22}/>}
        right={<>
          <NMBadge tone="streak" icon={<span>🔥</span>}>5 días</NMBadge>
          <NMBadge tone="default">{name}</NMBadge>
        </>}
        mode={t.mode}
      />
      <div style={{ padding: "24px 28px", overflow: "auto", height: "calc(100% - 56px)" }}>
        <div style={{ marginBottom: 4 }}>
          <div style={{ fontSize: 12, color: t.c.text3, letterSpacing: ".02em" }}>
            Buenos días
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, color: t.c.text, letterSpacing: "-.015em", marginTop: 2 }}>
            Hola, {name}
          </div>
          <div style={{ fontSize: 13, color: t.c.text2, marginTop: 6 }}>
            Hoy es jueves 16 de mayo · Tu próximo aviso: respiración 4-7-8 a las 18:00
          </div>
        </div>

        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 14,
          marginTop: 22,
        }}>
          {SUITE_MODULES.slice(0, 6).map(m => <ModuleCard key={m.id} mod={m}/>)}
        </div>
        <div style={{ display: "flex", justifyContent: "center", marginTop: 14 }}>
          <div style={{ width: "32%" }}>
            <ModuleCard mod={SUITE_MODULES[6]}/>
          </div>
        </div>
      </div>
    </AppWindow>
  );
}

// ── Suite – Ánimo ────────────────────────────────────────────────────────────
function SuiteAnimo() {
  const t = useTheme();
  const score = 7;
  const moodColor = score >= 7 ? t.c.success : score >= 4 ? t.c.warning : t.c.danger;
  return (
    <AppWindow title="NeuroMood Suite" subtitle="Ánimo" width={1080} height={720}>
      <NMHeader
        onBack={true}
        left={<div style={{ fontSize: 14, fontWeight: 600, color: t.c.text }}>Registro de ánimo</div>}
        center={null}
        right={<NMBadge tone="success">Hoy: 7/10</NMBadge>}
        mode={t.mode}
      />
      <div style={{ padding: "24px 28px", overflow: "auto", height: "calc(100% - 56px)", display: "grid", gridTemplateColumns: "1.2fr .9fr", gap: 20 }}>
        <div>
          <NMCard padding={28}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 64, lineHeight: 1, marginBottom: 8 }}>😄</div>
              <div style={{ fontSize: 48, fontWeight: 700, color: moodColor, letterSpacing: "-.02em" }}>{score}<span style={{ fontSize: 22, color: t.c.text3, fontWeight: 500 }}>/10</span></div>
              <div style={{ fontSize: 13, color: t.c.text2, marginTop: 4 }}>Buen día</div>
            </div>
            <div style={{ marginTop: 28, padding: "0 16px" }}>
              <NMSlider value={score * 10} tone="teal"/>
              <div style={{
                display: "flex", justifyContent: "space-between",
                fontSize: 10, color: t.c.text3, marginTop: 6,
                fontFamily: FONT.mono,
              }}>
                <span>1 · Difícil</span>
                <span>5 · Neutro</span>
                <span>10 · Excelente</span>
              </div>
            </div>
            <div style={{ marginTop: 24 }}>
              <div style={{ fontSize: 12, color: t.c.text3, marginBottom: 6 }}>Nota del día (opcional)</div>
              <div style={{
                padding: 14, borderRadius: 10,
                background: t.c.elevated,
                border: `1px solid ${t.c.borderSoft}`,
                fontSize: 13, color: t.c.text2, lineHeight: 1.5,
                minHeight: 76,
              }}>
                Almorcé con la familia y eso me ayudó. Aún algo cansada por el sueño cortado.
              </div>
            </div>
            <div style={{ display: "flex", gap: 10, marginTop: 18, justifyContent: "flex-end" }}>
              <NMButton variant="secondary">Borrar</NMButton>
              <NMButton variant="primary">Guardar registro</NMButton>
            </div>
          </NMCard>
        </div>
        <div>
          <SectionTitle eyebrow="Historial" size="sm">Últimos 7 días</SectionTitle>
          <NMCard padding={20}>
            <div style={{ height: 140, position: "relative" }}>
              <svg viewBox="0 0 200 100" preserveAspectRatio="none" style={{ width: "100%", height: "100%" }}>
                <defs>
                  <linearGradient id="moodFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={t.c.teal} stopOpacity=".25"/>
                    <stop offset="100%" stopColor={t.c.teal} stopOpacity="0"/>
                  </linearGradient>
                </defs>
                <path d="M0 70 C 30 60, 40 80, 60 55 S 100 30, 130 38 S 170 25, 200 20 L 200 100 L 0 100 Z"
                      fill="url(#moodFill)"/>
                <path d="M0 70 C 30 60, 40 80, 60 55 S 100 30, 130 38 S 170 25, 200 20"
                      stroke={t.c.teal} strokeWidth="2" fill="none"/>
                {[[0,70],[30,62],[60,55],[90,42],[130,38],[170,30],[200,20]].map(([x,y]) => (
                  <circle key={x} cx={x} cy={y} r="2.5" fill={t.c.surface} stroke={t.c.teal} strokeWidth="1.5"/>
                ))}
              </svg>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: t.c.text3, fontFamily: FONT.mono, marginTop: 8 }}>
              {["10/5","11/5","12/5","13/5","14/5","15/5","16/5"].map(d => <span key={d}>{d}</span>)}
            </div>
            <div style={{ marginTop: 14, display: "flex", gap: 12, alignItems: "center" }}>
              <NMRing pct={72} size={48} stroke={5} tone="teal" value="7.2" label="prom"/>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: t.c.text }}>+0.8 vs semana anterior</div>
                <div style={{ fontSize: 11, color: t.c.text3 }}>Tendencia positiva</div>
              </div>
            </div>
          </NMCard>
          <div style={{ marginTop: 18 }}>
            <SectionTitle eyebrow="Hoy" size="sm">Registros previos</SectionTitle>
            <NMCard padding={0}>
              {[
                ["09:15", "🙂", 7, "Buen día"],
                ["12:30", "😐", 5, "Reunión estresante"],
              ].map(([h, e, s, t2], i) => (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "auto auto 1fr auto",
                  alignItems: "center", gap: 12,
                  padding: "12px 16px",
                  borderBottom: i === 0 ? `1px solid ${t.c.borderSoft}` : "none",
                }}>
                  <div style={{ fontSize: 11, color: t.c.text3, fontFamily: FONT.mono }}>{h}</div>
                  <div style={{ fontSize: 18 }}>{e}</div>
                  <div style={{ fontSize: 12, color: t.c.text2 }}>{t2}</div>
                  <NMBadge tone={s >= 7 ? "success" : s >= 4 ? "warning" : "danger"}>{s}/10</NMBadge>
                </div>
              ))}
            </NMCard>
          </div>
        </div>
      </div>
    </AppWindow>
  );
}

// ── Suite – Respiración ──────────────────────────────────────────────────────
function SuiteRespiracion() {
  const t = useTheme();
  const techniques = [
    { id: "4-7-8", name: "4-7-8", desc: "Relajación profunda", min: "3 min", active: true },
    { id: "box",   name: "Caja",  desc: "Concentración",       min: "4 min", active: false },
    { id: "coh",   name: "Coherencia", desc: "5-5", min: "5 min", active: false },
    { id: "wim",   name: "Energizante", desc: "Wim Hof", min: "8 min", active: false },
  ];
  return (
    <AppWindow title="NeuroMood Suite" subtitle="Respiración" width={1080} height={720}>
      <NMHeader
        onBack
        left={<div style={{ fontSize: 14, fontWeight: 600, color: t.c.text }}>Respiración guiada</div>}
        right={<NMBadge tone="teal">Ciclo 2 / 5</NMBadge>}
        mode={t.mode}
      />
      <div style={{ padding: "24px 28px", display: "grid", gridTemplateColumns: "280px 1fr", gap: 24, height: "calc(100% - 56px)", overflow: "auto" }}>
        <div>
          <SectionTitle eyebrow="Técnica" size="sm">Elegir patrón</SectionTitle>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {techniques.map(tc => (
              <NMCard key={tc.id} interactive padding={14}
                style={{
                  borderColor: tc.active ? t.c.teal : t.c.borderSoft,
                  background: tc.active ? t.c.tealSoft : t.c.surface,
                }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: tc.active ? t.c.teal : t.c.text }}>{tc.name}</div>
                    <div style={{ fontSize: 11, color: t.c.text3, marginTop: 2 }}>{tc.desc}</div>
                  </div>
                  <div style={{ fontSize: 10, color: t.c.text3, fontFamily: FONT.mono }}>{tc.min}</div>
                </div>
              </NMCard>
            ))}
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center" }}>
          <div style={{
            fontSize: 11, fontWeight: 700, letterSpacing: ".18em",
            color: t.c.teal, textTransform: "uppercase", marginBottom: 18,
          }}>Inhala</div>
          <div style={{ position: "relative", width: 280, height: 280 }}>
            <svg width="280" height="280" viewBox="0 0 280 280">
              <defs>
                <radialGradient id="breathGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor={t.c.teal} stopOpacity=".25"/>
                  <stop offset="70%" stopColor={t.c.teal} stopOpacity=".08"/>
                  <stop offset="100%" stopColor={t.c.teal} stopOpacity="0"/>
                </radialGradient>
              </defs>
              <circle cx="140" cy="140" r="135" fill="url(#breathGlow)"/>
              <circle cx="140" cy="140" r="100" fill="none" stroke={t.c.borderSoft} strokeWidth="2"/>
              <circle cx="140" cy="140" r="100" fill="none" stroke={t.c.teal} strokeWidth="3"
                      strokeDasharray={`${0.62 * 2 * Math.PI * 100} ${2 * Math.PI * 100}`}
                      strokeDashoffset={Math.PI * 50}
                      strokeLinecap="round"
                      transform="rotate(-90 140 140)"/>
            </svg>
            <div style={{
              position: "absolute", inset: 0,
              display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center",
            }}>
              <div style={{ fontSize: 56, fontWeight: 700, color: t.c.text, fontFamily: FONT.mono, letterSpacing: "-.02em" }}>04</div>
              <div style={{ fontSize: 12, color: t.c.text3, marginTop: 4 }}>segundos</div>
            </div>
          </div>
          <div style={{ marginTop: 28, display: "flex", gap: 10 }}>
            <NMButton variant="secondary">Pausar</NMButton>
            <NMButton variant="primary">Comenzar sesión</NMButton>
            <NMButton variant="ghost">Saltar</NMButton>
          </div>
          <div style={{ marginTop: 18, fontSize: 12, color: t.c.text3 }}>
            Inhala 4s · Mantén 7s · Exhala 8s
          </div>
        </div>
      </div>
    </AppWindow>
  );
}

// ── Suite – TCC ───────────────────────────────────────────────────────────────
function SuiteTCC() {
  const t = useTheme();
  return (
    <AppWindow title="NeuroMood Suite" subtitle="Registro TCC" width={1080} height={720}>
      <NMHeader
        onBack
        left={<div style={{ fontSize: 14, fontWeight: 600, color: t.c.text }}>Registro TCC</div>}
        right={<NMBadge tone="accent">Paso 2 de 4</NMBadge>}
        mode={t.mode}
      />
      <div style={{ padding: "24px 28px", overflow: "auto", height: "calc(100% - 56px)" }}>
        <NMStepper steps={["Situación","Emoción","Pensamiento","Reestructuración"]} active={1}/>
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr .8fr", gap: 24, marginTop: 24 }}>
          <NMCard padding={24}>
            <SectionTitle eyebrow="Paso 2" size="md">¿Qué emoción identificás?</SectionTitle>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginTop: 16 }}>
              {[
                ["Ansiedad", "🥵", true],
                ["Tristeza", "😢", false],
                ["Enojo",    "😠", false],
                ["Miedo",    "😨", false],
                ["Culpa",    "😔", false],
                ["Vergüenza","😳", false],
                ["Soledad",  "🥺", false],
                ["Otro",     "💭", false],
              ].map(([n, e, a]) => (
                <div key={n} style={{
                  padding: 12, borderRadius: 12,
                  background: a ? t.c.accentSoft : t.c.elevated,
                  border: `1px solid ${a ? t.c.accent : t.c.borderSoft}`,
                  textAlign: "center", cursor: "pointer",
                }}>
                  <div style={{ fontSize: 22 }}>{e}</div>
                  <div style={{ fontSize: 11, fontWeight: 600, marginTop: 4, color: a ? t.c.accent : t.c.text2 }}>{n}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 22 }}>
              <div style={{ fontSize: 12, color: t.c.text3, marginBottom: 8 }}>Intensidad</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 14, alignItems: "center" }}>
                <NMSlider value={70} tone="accent"/>
                <div style={{ fontSize: 18, fontWeight: 700, fontFamily: FONT.mono, color: t.c.accent, minWidth: 40, textAlign: "right" }}>7</div>
              </div>
              <div style={{
                marginTop: 8, height: 6, borderRadius: 3,
                background: `linear-gradient(90deg, ${t.c.info}, ${t.c.warning}, ${t.c.danger})`,
                opacity: .25,
              }}/>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: t.c.text3, marginTop: 4, fontFamily: FONT.mono }}>
                <span>fría</span><span>tibia</span><span>caliente</span>
              </div>
            </div>
            <div style={{ display: "flex", gap: 10, marginTop: 24, justifyContent: "space-between" }}>
              <NMButton variant="secondary">← Volver</NMButton>
              <NMButton variant="primary">Continuar →</NMButton>
            </div>
          </NMCard>
          <div>
            <NMCard padding={20}>
              <SectionTitle eyebrow="Resumen" size="sm">Tu registro hasta ahora</SectionTitle>
              <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 12 }}>
                <div>
                  <div style={{ fontSize: 10, color: t.c.text3, fontWeight: 700, letterSpacing: ".1em", textTransform: "uppercase" }}>Situación</div>
                  <div style={{ fontSize: 13, color: t.c.text, marginTop: 4 }}>
                    "Reunión laboral en la que sentí que me evaluaban."
                  </div>
                </div>
                <div style={{ height: 1, background: t.c.borderSoft }}/>
                <div style={{ opacity: .5 }}>
                  <div style={{ fontSize: 10, color: t.c.text3, fontWeight: 700, letterSpacing: ".1em", textTransform: "uppercase" }}>Pensamiento</div>
                  <div style={{ fontSize: 12, color: t.c.text3, marginTop: 4 }}>— pendiente —</div>
                </div>
              </div>
            </NMCard>
            <NMCard padding={20} style={{ marginTop: 16 }}>
              <SectionTitle eyebrow="Tip" size="sm">Identificar la emoción</SectionTitle>
              <div style={{ fontSize: 12, color: t.c.text2, lineHeight: 1.6, marginTop: 4 }}>
                Nombrar la emoción con precisión reduce su intensidad. Si dudás entre dos, podés marcar la principal y agregar la secundaria en la nota.
              </div>
            </NMCard>
          </div>
        </div>
      </div>
    </AppWindow>
  );
}

// ── Suite – Rutina ────────────────────────────────────────────────────────────
function SuiteRutina() {
  const t = useTheme();
  const sections = [
    { id: "manana", tone: "warning", title: "Mañana", icon: "☀", items: [
      ["Hidratarme al despertar", true],
      ["10 min de respiración", true],
      ["Desayuno completo", true],
      ["Salir a caminar", false],
    ]},
    { id: "tarde", tone: "accent", title: "Tarde", icon: "🌤", items: [
      ["Pausa activa 15:00", true],
      ["Llamar a un familiar", false],
      ["Lectura 20 min", false],
    ]},
    { id: "noche", tone: "violet", title: "Noche", icon: "🌙", items: [
      ["Diario de gratitud", true],
      ["Apagar pantallas 22:30", false],
      ["Estiramiento ligero", false],
    ]},
  ];
  const total = sections.reduce((a, s) => a + s.items.length, 0);
  const done = sections.reduce((a, s) => a + s.items.filter(([_, d]) => d).length, 0);
  return (
    <AppWindow title="NeuroMood Suite" subtitle="Rutina" width={1080} height={720}>
      <NMHeader
        onBack
        left={<div style={{ fontSize: 14, fontWeight: 600, color: t.c.text }}>Rutina del día</div>}
        right={<NMBadge tone="success">{done}/{total} · {Math.round(done/total*100)}%</NMBadge>}
        mode={t.mode}
      />
      <div style={{ padding: "24px 28px", overflow: "auto", height: "calc(100% - 56px)" }}>
        <NMCard padding={18}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
            <div style={{ fontSize: 13, color: t.c.text2 }}>Progreso del día</div>
            <div style={{ fontSize: 13, color: t.c.text, fontWeight: 600 }}>{done} de {total} tareas</div>
          </div>
          <NMProgress value={(done/total)*100} tone="success" height={6}/>
        </NMCard>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginTop: 18 }}>
          {sections.map(sec => (
            <NMCard key={sec.id} accent={sec.tone} padding={18}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: 8,
                  background: t.c[`${sec.tone}Soft`],
                  color: t.c[sec.tone],
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 14,
                }}>{sec.icon}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: t.c.text }}>{sec.title}</div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {sec.items.map(([txt, d], i) => (
                  <div key={i} style={{
                    display: "grid", gridTemplateColumns: "auto 1fr",
                    alignItems: "center", gap: 10,
                    padding: "8px 10px",
                    borderRadius: 8,
                    background: d ? t.c.elevated : "transparent",
                  }}>
                    <NMCheck checked={d} size={16}/>
                    <div style={{
                      fontSize: 12,
                      color: d ? t.c.text3 : t.c.text,
                      textDecoration: d ? "line-through" : "none",
                    }}>{txt}</div>
                  </div>
                ))}
              </div>
              <NMButton variant="ghost" size="sm" fullWidth style={{ marginTop: 8 }}>+ Agregar tarea</NMButton>
            </NMCard>
          ))}
        </div>
      </div>
    </AppWindow>
  );
}

// ── Suite – Actividades ──────────────────────────────────────────────────────
function SuiteActividades() {
  const t = useTheme();
  const cats = [
    { name: "Autocuidado", color: t.c.success, count: 8 },
    { name: "Física",      color: t.c.teal,    count: 6 },
    { name: "Cognitiva",   color: t.c.info,    count: 4 },
    { name: "Placer",      color: t.c.violet,  count: 7 },
    { name: "Social",      color: t.c.warning, count: 5 },
    { name: "Maestría",    color: t.c.accent,  count: 3 },
  ];
  const acts = [
    ["Caminar 30 min", "Física", "alto"],
    ["Llamar a un amigo", "Social", "medio"],
    ["Cocinar receta nueva", "Placer", "alto"],
    ["Lectura ficción", "Cognitiva", "medio"],
    ["Bañarme con calma", "Autocuidado", "bajo"],
    ["Tocar guitarra", "Maestría", "alto"],
  ];
  return (
    <AppWindow title="NeuroMood Suite" subtitle="Actividades" width={1080} height={720}>
      <NMHeader
        onBack
        left={<div style={{ fontSize: 14, fontWeight: 600, color: t.c.text }}>Activación conductual</div>}
        right={<NMBadge tone="success">3 hoy</NMBadge>}
        mode={t.mode}
      />
      <div style={{ padding: "24px 28px", overflow: "auto", height: "calc(100% - 56px)" }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 18 }}>
          <NMBadge tone="accent">Todas · 33</NMBadge>
          {cats.map(c => (
            <NMBadge key={c.name} tone="default">
              <span style={{ width: 8, height: 8, borderRadius: 999, background: c.color, marginRight: 4, display: "inline-block" }}/>
              {c.name} · {c.count}
            </NMBadge>
          ))}
        </div>
        <SectionTitle eyebrow="Sugeridas hoy" size="md" action={<NMButton variant="ghost" size="sm">Ver banco completo</NMButton>}>
          Tres actividades para tu ánimo de hoy
        </SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
          {acts.slice(0, 3).map(([name, cat, intensity], i) => {
            const catColor = cats.find(c => c.name === cat)?.color;
            return (
              <NMCard key={i} interactive padding={18}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <span style={{
                    fontSize: 10, fontWeight: 700, padding: "3px 8px",
                    borderRadius: 999,
                    background: catColor + "22", color: catColor,
                    textTransform: "uppercase", letterSpacing: ".08em",
                  }}>{cat}</span>
                  <div style={{ display: "flex", gap: 2 }}>
                    {[1,2,3].map(n => (
                      <div key={n} style={{
                        width: 5, height: 5, borderRadius: 999,
                        background: intensity === "alto" ? catColor : intensity === "medio" && n <= 2 ? catColor : intensity === "bajo" && n <= 1 ? catColor : t.c.borderSoft,
                      }}/>
                    ))}
                  </div>
                </div>
                <div style={{ fontSize: 15, fontWeight: 600, color: t.c.text, letterSpacing: "-.005em" }}>{name}</div>
                <div style={{ fontSize: 11, color: t.c.text3, marginTop: 4 }}>Recomendada para ánimo 6–8</div>
                <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
                  <NMButton variant="soft" size="sm" fullWidth>Marcar como hecha</NMButton>
                </div>
              </NMCard>
            );
          })}
        </div>
        <div style={{ marginTop: 22 }}>
          <SectionTitle eyebrow="Banco" size="sm">Otras actividades disponibles</SectionTitle>
          <NMCard padding={0}>
            {acts.slice(3).map(([name, cat, intensity], i) => {
              const catColor = cats.find(c => c.name === cat)?.color;
              return (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "auto 1fr auto auto",
                  alignItems: "center", gap: 14,
                  padding: "12px 18px",
                  borderBottom: i < acts.length - 4 ? `1px solid ${t.c.borderSoft}` : "none",
                }}>
                  <span style={{ width: 8, height: 8, borderRadius: 999, background: catColor }}/>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: t.c.text }}>{name}</div>
                    <div style={{ fontSize: 11, color: t.c.text3 }}>{cat} · intensidad {intensity}</div>
                  </div>
                  <NMBadge tone="default">ánimo 4–7</NMBadge>
                  <NMButton variant="ghost" size="sm">Iniciar</NMButton>
                </div>
              );
            })}
          </NMCard>
        </div>
      </div>
    </AppWindow>
  );
}

// ── Suite – Timer ─────────────────────────────────────────────────────────────
function SuiteTimer() {
  const t = useTheme();
  return (
    <AppWindow title="NeuroMood Suite" subtitle="Timer de enfoque" width={1080} height={720}>
      <NMHeader
        onBack
        left={<div style={{ fontSize: 14, fontWeight: 600, color: t.c.text }}>Sesión de enfoque</div>}
        right={<NMBadge tone="accent">Activo</NMBadge>}
        mode={t.mode}
      />
      <div style={{ padding: "24px 28px", height: "calc(100% - 56px)", display: "grid", gridTemplateColumns: "1fr 300px", gap: 24 }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <div style={{ position: "relative", width: 320, height: 320 }}>
            <svg width="320" height="320" viewBox="0 0 320 320">
              <circle cx="160" cy="160" r="140" fill="none" stroke={t.c.borderSoft} strokeWidth="6"/>
              <circle cx="160" cy="160" r="140" fill="none" stroke={t.c.accent} strokeWidth="6"
                      strokeDasharray={`${0.62 * 2 * Math.PI * 140} ${2 * Math.PI * 140}`}
                      strokeLinecap="round"
                      transform="rotate(-90 160 160)"/>
            </svg>
            <div style={{
              position: "absolute", inset: 0,
              display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center",
            }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".2em", color: t.c.text3, textTransform: "uppercase" }}>Enfoque</div>
              <div style={{ fontSize: 72, fontWeight: 700, color: t.c.text, fontFamily: FONT.mono, letterSpacing: "-.04em", marginTop: 4 }}>14:32</div>
              <div style={{ fontSize: 12, color: t.c.text2, marginTop: 4 }}>de 25:00 · sesión 2 de 4</div>
            </div>
          </div>
          <div style={{ marginTop: 28, display: "flex", gap: 10 }}>
            <NMButton variant="secondary" icon={<span>⏸</span>}>Pausar</NMButton>
            <NMButton variant="primary" size="lg">Continuar</NMButton>
            <NMButton variant="ghost">Reiniciar</NMButton>
          </div>
        </div>
        <div>
          <SectionTitle eyebrow="Configuración" size="sm">Esta sesión</SectionTitle>
          <NMCard padding={18}>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {[
                ["Nombre", "Estudio - Capítulo 3"],
                ["Categoría", "Cognitiva"],
                ["Duración", "25 min"],
                ["Descanso", "5 min"],
                ["Ciclos", "4"],
              ].map(([k, v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                  <span style={{ color: t.c.text3 }}>{k}</span>
                  <span style={{ color: t.c.text, fontWeight: 500 }}>{v}</span>
                </div>
              ))}
            </div>
          </NMCard>
          <SectionTitle eyebrow="Hoy" size="sm" style={{ marginTop: 20 }}>Sesiones</SectionTitle>
          <NMCard padding={0}>
            {[["08:30","Lectura","25 min","completa"],["10:15","Estudio","25 min","completa"],["14:00","Estudio","14 min","activa"]].map(([h, n, d, st], i) => (
              <div key={i} style={{
                display: "grid", gridTemplateColumns: "auto 1fr auto",
                gap: 10, padding: "10px 14px",
                borderBottom: i < 2 ? `1px solid ${t.c.borderSoft}` : "none",
                alignItems: "center",
              }}>
                <div style={{ fontSize: 10, color: t.c.text3, fontFamily: FONT.mono }}>{h}</div>
                <div>
                  <div style={{ fontSize: 12, color: t.c.text, fontWeight: 500 }}>{n}</div>
                  <div style={{ fontSize: 10, color: t.c.text3 }}>{d}</div>
                </div>
                <NMBadge tone={st === "completa" ? "success" : "accent"}>{st}</NMBadge>
              </div>
            ))}
          </NMCard>
        </div>
      </div>
    </AppWindow>
  );
}

// ── Suite – Avisos ────────────────────────────────────────────────────────────
function SuiteAvisos() {
  const t = useTheme();
  const items = [
    { h: "08:00", title: "Tomar medicación", days: "L M M J V", active: true, days_arr: [1,1,1,1,1,0,0] },
    { h: "12:30", title: "Pausa de respiración", days: "Todos los días", active: true, days_arr: [1,1,1,1,1,1,1] },
    { h: "18:00", title: "Caminar 20 min", days: "L M V", active: false, days_arr: [1,0,1,0,1,0,0] },
    { h: "21:30", title: "Diario de gratitud", days: "Todos los días", active: true, days_arr: [1,1,1,1,1,1,1] },
    { h: "22:30", title: "Apagar pantallas", days: "L–V", active: true, days_arr: [1,1,1,1,1,0,0] },
  ];
  return (
    <AppWindow title="NeuroMood Suite" subtitle="Avisos" width={1080} height={720}>
      <NMHeader
        onBack
        left={<div style={{ fontSize: 14, fontWeight: 600, color: t.c.text }}>Recordatorios</div>}
        right={<NMButton variant="primary" size="sm" icon={<span>+</span>}>Nuevo aviso</NMButton>}
        mode={t.mode}
      />
      <div style={{ padding: "24px 28px", overflow: "auto", height: "calc(100% - 56px)" }}>
        <NMCard padding={18} style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 14, alignItems: "center" }}>
          <div style={{
            width: 44, height: 44, borderRadius: 12,
            background: t.c.warningSoft, color: t.c.warning,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 20,
          }}>🔔</div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: t.c.text }}>Próximo: Pausa de respiración</div>
            <div style={{ fontSize: 12, color: t.c.text3 }}>Hoy a las 18:00 · en 2 horas 14 min</div>
          </div>
          <NMButton variant="soft" size="sm">Posponer 30 min</NMButton>
        </NMCard>

        <SectionTitle eyebrow={`${items.filter(i => i.active).length} de ${items.length} activos`} size="sm" style={{ marginTop: 22 }}>
          Todos los avisos
        </SectionTitle>
        <NMCard padding={0}>
          {items.map((it, i) => (
            <div key={i} style={{
              display: "grid",
              gridTemplateColumns: "70px 1fr auto auto",
              alignItems: "center",
              gap: 16, padding: "14px 18px",
              borderBottom: i < items.length - 1 ? `1px solid ${t.c.borderSoft}` : "none",
              opacity: it.active ? 1 : .55,
            }}>
              <div style={{
                fontSize: 20, fontWeight: 700,
                color: t.c.text, fontFamily: FONT.mono,
                letterSpacing: "-.02em",
              }}>{it.h}</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: t.c.text }}>{it.title}</div>
                <div style={{ fontSize: 11, color: t.c.text3, marginTop: 2 }}>{it.days}</div>
              </div>
              <div style={{ display: "flex", gap: 3 }}>
                {["L","M","M","J","V","S","D"].map((d, j) => (
                  <div key={j} style={{
                    width: 18, height: 18, borderRadius: 999,
                    background: it.days_arr[j] ? t.c.accentSoft : t.c.elevated,
                    color: it.days_arr[j] ? t.c.accent : t.c.text4,
                    fontSize: 9, fontWeight: 700,
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>{d}</div>
                ))}
              </div>
              <NMToggle checked={it.active}/>
            </div>
          ))}
        </NMCard>
      </div>
    </AppWindow>
  );
}

Object.assign(window, {
  SUITE_MODULES, ModuleCard, SuiteHome, SuiteAnimo, SuiteRespiracion,
  SuiteTCC, SuiteRutina, SuiteActividades, SuiteTimer, SuiteAvisos,
});
