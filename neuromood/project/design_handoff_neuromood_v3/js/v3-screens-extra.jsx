/* v3-screens-extra.jsx — Pantallas restantes en sistema v3:
 * Suite: TCC, Rutina, Actividades, Timer
 * Hub: Detalle paciente (con tabs), IA full, Configuración
 * Installers: Instalador Suite (5 pasos), Desinstalador Suite (3 pasos)
 */

// ─── Suite · TCC ──────────────────────────────────────────────────────────────
function V3SuiteTCC({ mode = "light" }) {
  return (
    <V3Shell defaultMode={mode} sidebar={<V3Sidebar active="tcc"/>} width={1320} height={860}>
      <V3TCCBody mode={mode}/>
    </V3Shell>
  );
}
function V3TCCBody({ mode }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", overflow: "auto" }}>
      <V3Header
        title="Registro TCC"
        subtitle="Identificá pensamientos y reestructurá tu respuesta emocional."
        mode={mode}
        actions={<div style={{
          padding: "6px 14px", borderRadius: 999,
          background: c.violetSoft, color: c.violet,
          fontSize: 12, fontWeight: 700,
        }}>Paso 2 de 4</div>}
      />
      <div style={{ padding: "0 28px 28px", display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Stepper */}
        <V3Card padding={20}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {[
              ["1", "Situación",        "done"],
              ["2", "Emoción",          "active"],
              ["3", "Pensamiento",      "todo"],
              ["4", "Reestructuración", "todo"],
            ].map(([n, t1, st], i, arr) => (
              <React.Fragment key={n}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: 999,
                    background: st !== "todo" ? `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})` : c.elevated,
                    color: st === "todo" ? c.text3 : "#fff",
                    fontSize: 13, fontWeight: 700,
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>{st === "done" ? <NMIcon name="check" size={14} color="#fff" filled/> : n}</div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: st === "todo" ? c.text3 : c.text }}>{t1}</div>
                </div>
                {i < arr.length - 1 && (
                  <div style={{
                    flex: 1, height: 3, borderRadius: 999,
                    background: arr[i+1][2] !== "todo" ? `linear-gradient(90deg, ${c.gradFrom}, ${c.gradTo})` : c.elevated,
                  }}/>
                )}
              </React.Fragment>
            ))}
          </div>
        </V3Card>

        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 16 }}>
          {/* Step 2: Emoción */}
          <V3Card padding={24}>
            <V3SectionTitle sub="Identificá la emoción principal que sentís ahora">
              ¿Qué emoción estás sintiendo?
            </V3SectionTitle>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginTop: 14 }}>
              {[
                ["Ansiedad",  "lungs",  c.cyan,   true],
                ["Tristeza",  "moon",   c.cyan,   false],
                ["Enojo",     "flame",  c.danger, false],
                ["Miedo",     "warning",c.warning,false],
                ["Culpa",     "heart",  c.violet, false],
                ["Vergüenza", "user",   c.warning,false],
                ["Soledad",   "user",   c.cyan,   false],
                ["Otro",      "bulb",   c.text3,  false],
              ].map(([n, ic, col, sel]) => (
                <div key={n} style={{
                  padding: "14px 10px",
                  borderRadius: 14,
                  background: sel ? (isDark ? `${col}22` : col + "1a") : c.elevated,
                  border: `1.5px solid ${sel ? col : c.borderSoft}`,
                  textAlign: "center",
                  cursor: "pointer",
                  boxShadow: sel ? `0 4px 12px -2px ${col}44` : "none",
                  transition: "all .2s ease",
                }}>
                  <NMIcon name={ic} size={26} color={sel ? col : c.text2}/>
                  <div style={{
                    fontSize: 12, fontWeight: sel ? 700 : 500,
                    color: sel ? col : c.text2, marginTop: 6,
                  }}>{n}</div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: 22 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontSize: 12, color: c.text2 }}>Intensidad</span>
                <span style={{ fontSize: 18, fontWeight: 700, color: c.cyan, fontFamily: V3_FONT.mono }}>7/10</span>
              </div>
              {/* Slashbar fría → caliente */}
              <div style={{ position: "relative", height: 24 }}>
                <div style={{
                  position: "absolute", top: 9, left: 0, right: 0, height: 6,
                  borderRadius: 999,
                  background: "linear-gradient(90deg, #5b8ed0, #fbbf24, #ef4444)",
                  opacity: .85,
                }}/>
                <div style={{
                  position: "absolute", top: 0, left: "calc(70% - 12px)",
                  width: 24, height: 24, borderRadius: 999,
                  background: "#fff",
                  border: `3px solid ${c.cyan}`,
                  boxShadow: `0 4px 12px ${c.cyan}55`,
                }}/>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: c.text3, marginTop: 4, fontFamily: V3_FONT.mono }}>
                <span>fría</span><span>tibia</span><span>caliente</span>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 24, gap: 10 }}>
              <V3Button variant="secondary" icon={<NMIcon name="arrowLeft" size={14}/>}>Volver</V3Button>
              <V3Button gradient icon={<NMIcon name="arrowRight" size={14} color="#fff"/>}>Continuar</V3Button>
            </div>
          </V3Card>

          {/* Right: resumen + tip */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <V3Card padding={20}>
              <V3SectionTitle sub="Tu registro hasta ahora">Resumen</V3SectionTitle>
              <div style={{ marginTop: 4 }}>
                <div style={{ fontSize: 10, color: c.text3, fontWeight: 700, letterSpacing: ".1em", textTransform: "uppercase" }}>Situación</div>
                <div style={{ fontSize: 13, color: c.text, marginTop: 4, lineHeight: 1.5 }}>
                  "Reunión laboral en la que sentí que me evaluaban."
                </div>
              </div>
              <div style={{ height: 1, background: c.borderSoft, margin: "14px 0" }}/>
              <div style={{ opacity: .55 }}>
                <div style={{ fontSize: 10, color: c.text3, fontWeight: 700, letterSpacing: ".1em", textTransform: "uppercase" }}>Pensamiento</div>
                <div style={{ fontSize: 12, color: c.text3, marginTop: 4 }}>— pendiente —</div>
              </div>
              <div style={{ height: 1, background: c.borderSoft, margin: "14px 0" }}/>
              <div style={{ opacity: .55 }}>
                <div style={{ fontSize: 10, color: c.text3, fontWeight: 700, letterSpacing: ".1em", textTransform: "uppercase" }}>Reestructuración</div>
                <div style={{ fontSize: 12, color: c.text3, marginTop: 4 }}>— pendiente —</div>
              </div>
            </V3Card>
            <V3Card padding={20}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <NMIcon name="bulb" size={18} color={c.violet}/>
                <div style={{ fontSize: 13, fontWeight: 700, color: c.text }}>Tip terapéutico</div>
              </div>
              <div style={{ fontSize: 12, color: c.text2, lineHeight: 1.6 }}>
                Nombrar la emoción con precisión reduce su intensidad. Si dudás entre dos, marcá la principal y agregá la secundaria en la nota.
              </div>
            </V3Card>
          </div>
        </div>

        {/* Historial reciente */}
        <V3Card padding={20}>
          <V3SectionTitle action={<span style={{ fontSize: 12, color: c.teal, fontWeight: 600 }}>Ver todos</span>}>
            Registros anteriores
          </V3SectionTitle>
          <div style={{ display: "grid", gridTemplateColumns: "auto auto 1fr auto auto", gap: 14, padding: "12px 0",
                        borderBottom: `1px solid ${c.borderSoft}`, fontSize: 10, fontWeight: 700,
                        color: c.text3, letterSpacing: ".1em", textTransform: "uppercase" }}>
            <span style={{ width: 60 }}>Fecha</span>
            <span style={{ width: 100 }}>Emoción</span>
            <span>Pensamiento</span>
            <span>Intensidad</span>
            <span>Estado</span>
          </div>
          {[
            ["Hoy",     "Ansiedad",  "Reunión laboral · sentí evaluación", 7, "En progreso", c.cyan],
            ["Ayer",    "Tristeza",  "Discusión familiar · no me sentí escuchada", 6, "Completo", c.success],
            ["14 may",  "Enojo",     "Tráfico · llegué tarde", 8, "Completo", c.success],
            ["12 may",  "Miedo",     "Resultado médico pendiente", 9, "Completo", c.success],
          ].map(([d, em, txt, int, st, col], i) => (
            <div key={i} style={{
              display: "grid", gridTemplateColumns: "auto auto 1fr auto auto",
              gap: 14, padding: "12px 0",
              borderBottom: i < 3 ? `1px solid ${c.borderSoft}` : "none",
              alignItems: "center",
            }}>
              <span style={{ width: 60, fontSize: 11, color: c.text3, fontFamily: V3_FONT.mono }}>{d}</span>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, color: c.text, fontWeight: 500, width: 100 }}>
                <span style={{ width: 6, height: 6, borderRadius: 999, background: col }}/>
                {em}
              </span>
              <span style={{ fontSize: 12, color: c.text2 }}>{txt}</span>
              <span style={{ fontSize: 12, color: c.text, fontFamily: V3_FONT.mono, fontWeight: 700 }}>{int}/10</span>
              <span style={{
                padding: "3px 9px", borderRadius: 999,
                background: col + "22", color: col,
                fontSize: 11, fontWeight: 600,
              }}>{st}</span>
            </div>
          ))}
        </V3Card>
      </div>
    </div>
  );
}

// ─── Suite · Rutina ───────────────────────────────────────────────────────────
function V3SuiteRutina({ mode = "light" }) {
  return (
    <V3Shell defaultMode={mode} sidebar={<V3Sidebar active="rutina"/>} width={1320} height={860}>
      <V3RutinaBody mode={mode}/>
    </V3Shell>
  );
}
function V3RutinaBody({ mode }) {
  const { c, isDark } = useV3Theme();
  const sections = [
    { id: "manana", title: "Mañana", icon: "sun", color: c.warning, items: [
      ["Hidratarme al despertar", true],
      ["10 min de respiración", true],
      ["Desayuno completo", true],
      ["Salir a caminar", false],
    ]},
    { id: "tarde",  title: "Tarde",  icon: "sun", color: c.cyan, items: [
      ["Pausa activa 15:00", true],
      ["Llamar a un familiar", false],
      ["Lectura 20 min", false],
    ]},
    { id: "noche",  title: "Noche",  icon: "moon", color: c.violet, items: [
      ["Diario de gratitud", true],
      ["Apagar pantallas 22:30", false],
      ["Estiramiento ligero", false],
    ]},
  ];
  const total = sections.reduce((a, s) => a + s.items.length, 0);
  const done = sections.reduce((a, s) => a + s.items.filter(([_, d]) => d).length, 0);
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", overflow: "auto" }}>
      <V3Header
        title="Rutina del día"
        subtitle={`${done} de ${total} tareas completadas · ${Math.round(done/total*100)}% del día`}
        streak={12}
        mode={mode}
      />
      <div style={{ padding: "0 28px 28px", display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Top progress */}
        <V3Card padding={22}>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 24, alignItems: "center" }}>
            <V3Ring pct={(done/total)*100} size={100} stroke={9} value={`${done}/${total}`}/>
            <div>
              <div style={{ fontSize: 11, color: c.text3, fontWeight: 700, letterSpacing: ".1em", textTransform: "uppercase" }}>Progreso de hoy</div>
              <div style={{ fontSize: 26, fontWeight: 700, color: c.text, letterSpacing: "-.015em", marginTop: 4 }}>
                {Math.round(done/total*100)}% completado
              </div>
              <div style={{ fontSize: 12, color: c.text2, marginTop: 4 }}>Llevás un buen ritmo. Quedan {total - done} tareas para cerrar el día.</div>
            </div>
            <V3Button gradient icon={<NMIcon name="plus" size={14} color="#fff" filled/>}>Nueva tarea</V3Button>
          </div>
        </V3Card>

        {/* 3 secciones */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
          {sections.map(sec => {
            const secDone = sec.items.filter(([_,d]) => d).length;
            return (
              <V3Card key={sec.id} padding={20}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: 12,
                    background: sec.color + "22", color: sec.color,
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    <NMIcon name={sec.icon} size={18} color={sec.color}/>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 15, fontWeight: 700, color: c.text }}>{sec.title}</div>
                    <div style={{ fontSize: 11, color: c.text3 }}>{secDone} de {sec.items.length} tareas</div>
                  </div>
                  <V3Ring pct={(secDone/sec.items.length)*100} size={36} stroke={4}/>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {sec.items.map(([txt, d], i) => (
                    <div key={i} style={{
                      display: "grid", gridTemplateColumns: "auto 1fr",
                      alignItems: "center", gap: 10,
                      padding: "10px 12px",
                      borderRadius: 10,
                      background: d ? c.elevated : "transparent",
                      border: d ? `1px solid ${c.borderSoft}` : `1px dashed ${c.borderSoft}`,
                    }}>
                      <NMCheckBox checked={d} color={sec.color}/>
                      <div style={{
                        fontSize: 13,
                        color: d ? c.text3 : c.text,
                        textDecoration: d ? "line-through" : "none",
                      }}>{txt}</div>
                    </div>
                  ))}
                </div>
                <V3Button variant="ghost" size="sm" fullWidth icon={<NMIcon name="plus" size={12}/>} style={{ marginTop: 12 }}>Agregar tarea</V3Button>
              </V3Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Helper: checkbox SVG bonito
function NMCheckBox({ checked, color }) {
  const { c } = useV3Theme();
  return (
    <div style={{
      width: 20, height: 20, borderRadius: 6,
      border: `1.5px solid ${checked ? color : c.borderStrong}`,
      background: checked ? color : "transparent",
      display: "flex", alignItems: "center", justifyContent: "center",
      transition: "all .15s ease",
      flexShrink: 0,
    }}>
      {checked && <NMIcon name="check" size={12} color="#fff"/>}
    </div>
  );
}

// ─── Suite · Actividades ──────────────────────────────────────────────────────
function V3SuiteActividades({ mode = "light" }) {
  return (
    <V3Shell defaultMode={mode} sidebar={<V3Sidebar active="actividades"/>} width={1320} height={860}>
      <V3ActividadesBody mode={mode}/>
    </V3Shell>
  );
}
function V3ActividadesBody({ mode }) {
  const { c, isDark } = useV3Theme();
  const cats = [
    { name: "Autocuidado", color: c.success, icon: "heart",   count: 8 },
    { name: "Física",      color: c.teal,    icon: "run",     count: 6 },
    { name: "Cognitiva",   color: c.cyan,    icon: "brain",   count: 4 },
    { name: "Placer",      color: c.violet,  icon: "sparkle", count: 7 },
    { name: "Social",      color: c.warning, icon: "users",   count: 5 },
    { name: "Maestría",    color: c.teal,    icon: "trophy",  count: 3 },
  ];
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", overflow: "auto" }}>
      <V3Header
        title="Activación conductual"
        subtitle="Actividades recomendadas según tu estado de ánimo actual."
        mode={mode}
        actions={<V3Button variant="secondary" icon={<NMIcon name="plus" size={14}/>}>Crear actividad</V3Button>}
      />
      <div style={{ padding: "0 28px 28px", display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Filtros por categoría */}
        <V3Card padding={16}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <div style={{
              padding: "8px 16px", borderRadius: 999,
              background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
              color: "#fff", fontSize: 12, fontWeight: 700,
              boxShadow: `0 4px 12px -2px ${c.teal}55`,
            }}>Todas · 33</div>
            {cats.map(cat => (
              <div key={cat.name} style={{
                padding: "8px 14px", borderRadius: 999,
                background: c.elevated, border: `1px solid ${c.borderSoft}`,
                color: c.text2, fontSize: 12, fontWeight: 500,
                display: "inline-flex", alignItems: "center", gap: 6,
              }}>
                <NMIcon name={cat.icon} size={12} color={cat.color}/>
                {cat.name} · {cat.count}
              </div>
            ))}
          </div>
        </V3Card>

        {/* Sugeridas para ti */}
        <V3SectionTitle
          sub="3 actividades para tu ánimo de hoy (7/10)"
          action={<span style={{ fontSize: 12, color: c.teal, fontWeight: 600, cursor: "pointer" }}>Ver banco completo</span>}
        >Sugeridas para ti</V3SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
          {[
            { name: "Caminata de 30 minutos", cat: "Física",      duration: "30 min", intensity: "alta",  icon: "run",   color: c.teal },
            { name: "Llamar a un amigo",      cat: "Social",      duration: "15 min", intensity: "media", icon: "users", color: c.warning },
            { name: "Cocinar receta nueva",   cat: "Placer",      duration: "45 min", intensity: "alta",  icon: "sparkle", color: c.violet },
          ].map((a, i) => (
            <V3Card key={i} padding={20}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div style={{
                  padding: "4px 10px", borderRadius: 999,
                  background: a.color + "22", color: a.color,
                  fontSize: 10, fontWeight: 700, letterSpacing: ".05em",
                }}>{a.cat.toUpperCase()}</div>
                <div style={{ display: "flex", gap: 3 }}>
                  {[1,2,3].map(n => (
                    <span key={n} style={{
                      width: 5, height: 5, borderRadius: 999,
                      background: (a.intensity === "alta") || (a.intensity === "media" && n <= 2) || (a.intensity === "baja" && n <= 1)
                                  ? a.color : c.borderSoft,
                    }}/>
                  ))}
                </div>
              </div>
              <NMIcon name={a.icon} size={32} color={a.color}/>
              <div style={{ fontSize: 16, fontWeight: 700, color: c.text, marginTop: 12, letterSpacing: "-.005em" }}>{a.name}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 8, fontSize: 11, color: c.text3 }}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <NMIcon name="clock" size={11} color={c.text3}/>{a.duration}
                </span>
                <span>·</span>
                <span>ánimo 6–8</span>
              </div>
              <V3Button gradient fullWidth size="sm" icon={<NMIcon name="check" size={12} color="#fff"/>} style={{ marginTop: 16 }}>Iniciar actividad</V3Button>
            </V3Card>
          ))}
        </div>

        {/* Banco completo (list) */}
        <V3SectionTitle sub="33 actividades en tu banco">Otras opciones disponibles</V3SectionTitle>
        <V3Card padding={0}>
          {[
            ["Meditación guiada",    "Autocuidado", "leaf",   c.success, "10 min", "ánimo 1–10"],
            ["Lectura ficción",      "Cognitiva",   "book",   c.cyan,    "20 min", "ánimo 4–8"],
            ["Bañarme con calma",    "Autocuidado", "water",  c.success, "15 min", "ánimo 1–8"],
            ["Tocar guitarra",       "Maestría",    "trophy", c.teal,    "30 min", "ánimo 5–10"],
            ["Salir a la naturaleza","Placer",      "leaf",   c.violet,  "60 min", "ánimo 4–10"],
          ].map(([n, cat, ic, col, dur, range], i, arr) => (
            <div key={i} style={{
              display: "grid", gridTemplateColumns: "auto 1fr auto auto auto",
              alignItems: "center", gap: 16, padding: "14px 20px",
              borderBottom: i < arr.length - 1 ? `1px solid ${c.borderSoft}` : "none",
            }}>
              <NMIcon name={ic} size={20} color={col}/>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: c.text }}>{n}</div>
                <div style={{ fontSize: 11, color: c.text3 }}>{cat} · {dur}</div>
              </div>
              <span style={{
                padding: "3px 8px", borderRadius: 999,
                background: c.elevated, color: c.text2,
                fontSize: 10, fontWeight: 600,
              }}>{range}</span>
              <V3Button variant="ghost" size="sm" icon={<NMIcon name="play" size={11} filled color={c.teal}/>}>Iniciar</V3Button>
              <NMIcon name="dots" size={16} color={c.text3}/>
            </div>
          ))}
        </V3Card>
      </div>
    </div>
  );
}

// ─── Suite · Timer ────────────────────────────────────────────────────────────
function V3SuiteTimer({ mode = "dark" }) {
  return (
    <V3Shell defaultMode={mode} sidebar={<V3Sidebar active="timer"/>} width={1320} height={860}>
      <V3TimerBody mode={mode}/>
    </V3Shell>
  );
}
function V3TimerBody({ mode }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", overflow: "auto" }}>
      <V3Header
        title="Timer de enfoque"
        subtitle="Sesiones cortas con descanso. Mantené tu atención sin agotarte."
        mode={mode}
        actions={
          <div style={{
            padding: "8px 14px", borderRadius: 14,
            background: c.surface, border: `1px solid ${c.borderSoft}`,
            fontSize: 12, color: c.text, fontWeight: 600,
            display: "flex", alignItems: "center", gap: 6,
          }}>Pomodoro · 25/5 <NMIcon name="chevronDown" size={10} color={c.text2}/></div>
        }
      />
      <div style={{ padding: "0 28px 28px", display: "grid", gridTemplateColumns: "1fr 320px", gap: 16, alignItems: "start" }}>
        <V3Card padding={28} glow>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            {/* Big timer ring */}
            <div style={{ position: "relative", width: 340, height: 340, margin: "12px 0" }}>
              <V3Ring pct={58} size={340} stroke={14} value="14:32" sub="de 25:00"/>
            </div>
            {/* Status row */}
            <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 4 }}>
              <span style={{
                padding: "4px 12px", borderRadius: 999,
                background: c.tealSoft, color: c.teal,
                fontSize: 11, fontWeight: 700,
                display: "inline-flex", alignItems: "center", gap: 6,
              }}>
                <span style={{ width: 7, height: 7, borderRadius: 999, background: c.teal,
                               boxShadow: `0 0 0 4px ${c.teal}22` }}/>
                Sesión en curso
              </span>
              <span style={{ fontSize: 12, color: c.text3 }}>Sesión 2 de 4 · descanso de 5 min al completar</span>
            </div>
            {/* Controls row — 3 botones circulares */}
            <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 24 }}>
              <NMPlayButton icon="skip" size={48}/>
              <NMPlayButton icon="pause" size={64}/>
              <NMPlayButton icon="refresh" size={48}/>
            </div>
          </div>
        </V3Card>

        {/* Sidebar derecho */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <V3Card padding={20}>
            <V3SectionTitle>Esta sesión</V3SectionTitle>
            <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 6 }}>
              {[
                ["Nombre",     "Estudio · Capítulo 3"],
                ["Categoría",  "Cognitiva"],
                ["Foco",       "25 min"],
                ["Descanso",   "5 min"],
                ["Ciclos",     "4"],
              ].map(([k, v]) => (
                <div key={k} style={{
                  display: "flex", justifyContent: "space-between",
                  fontSize: 12, paddingBottom: 8,
                  borderBottom: `1px solid ${c.borderSoft}`,
                }}>
                  <span style={{ color: c.text3 }}>{k}</span>
                  <span style={{ color: c.text, fontWeight: 600 }}>{v}</span>
                </div>
              ))}
            </div>
          </V3Card>
          <V3Card padding={20}>
            <V3SectionTitle sub="Hoy">Sesiones</V3SectionTitle>
            <div style={{ marginTop: 4 }}>
              {[
                ["08:30", "Lectura · 25 min",  "completa", c.success],
                ["10:15", "Estudio · 25 min",  "completa", c.success],
                ["14:00", "Estudio · 14 min",  "activa",   c.teal],
              ].map(([h, n, st, col], i, arr) => (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "auto 1fr auto",
                  gap: 10, padding: "10px 0", alignItems: "center",
                  borderBottom: i < arr.length - 1 ? `1px solid ${c.borderSoft}` : "none",
                }}>
                  <span style={{ fontSize: 11, color: c.text3, fontFamily: V3_FONT.mono }}>{h}</span>
                  <span style={{ fontSize: 12, color: c.text }}>{n}</span>
                  <span style={{
                    padding: "3px 9px", borderRadius: 999,
                    background: col + "22", color: col,
                    fontSize: 11, fontWeight: 600,
                  }}>{st}</span>
                </div>
              ))}
            </div>
          </V3Card>
        </div>
      </div>
    </div>
  );
}

// ─── Hub · Detalle paciente (con tabs) ───────────────────────────────────────
function V3HubDetalle({ mode = "dark" }) {
  return (
    <V3Shell defaultMode={mode} width={1360} height={920}
      sidebar={<V3Sidebar active="pacientes" appName="NeuroMood" role="Hub Pro" items={V3HubNavItems()}/>}>
      <V3HubDetalleBody mode={mode}/>
    </V3Shell>
  );
}
function V3HubNavItems() {
  return [
    { id: "dashboard",  label: "Dashboard" },
    { id: "pacientes",  label: "Pacientes" },
    { id: "ia",         label: "IA Asistente" },
    { id: "avisos",     label: "Recordatorios" },
    { id: "respiracion",label: "Respiración" },
    { id: "mood",       label: "Mood Tracker" },
    { id: "therapy",    label: "Terapias" },
    { id: "actividades",label: "Actividades" },
    { id: "reportes",   label: "Reportes" },
    { id: "download",   label: "Exportar" },
    { id: "config",     label: "Configuración" },
  ];
}
function V3HubDetalleBody({ mode }) {
  const { c, isDark } = useV3Theme();
  const [tab, setTab] = React.useState("Registros");
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", overflow: "auto" }}>
      {/* Top breadcrumb + actions */}
      <div style={{ padding: "20px 28px 14px", display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 16, alignItems: "center" }}>
        <V3Button variant="ghost" size="sm" icon={<NMIcon name="arrowLeft" size={14}/>}>Pacientes</V3Button>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 999,
            background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
            color: "#fff", fontSize: 20, fontWeight: 700,
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: `0 0 0 4px ${isDark ? c.surfaceSolid : c.surface}`,
            position: "relative",
          }}>AM
            <span style={{
              position: "absolute", bottom: -2, right: -2,
              width: 16, height: 16, borderRadius: 999,
              background: c.success,
              border: `3px solid ${isDark ? c.surfaceSolid : c.surface}`,
            }}/>
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700, color: c.text, letterSpacing: "-.01em" }}>Ana Martínez</div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 2, fontSize: 11, color: c.text3 }}>
              <span style={{ fontFamily: V3_FONT.mono }}>NM-2024-0158</span>
              <span>·</span>
              <span>Semana 12 · Ansiedad</span>
              <span>·</span>
              <span style={{ color: c.success }}>Activa</span>
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <V3Button variant="secondary" size="sm" icon={<NMIcon name="download" size={14}/>}>Exportar PDF</V3Button>
          <V3Button gradient size="sm" icon={<NMIcon name="plus" size={14} color="#fff" filled/>}>Nueva sesión</V3Button>
        </div>
      </div>

      <div style={{ padding: "0 28px 14px" }}>
        <V3Tabs items={["Registros", "Asignar", "Banco", "IA"]} active={tab} onChange={setTab}/>
      </div>

      <div style={{ padding: "0 28px 28px" }}>
        {tab === "Registros" && (
          <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 16 }}>
            <V3Card padding={22}>
              <V3SectionTitle
                action={<span style={{
                  padding: "4px 10px", borderRadius: 999,
                  background: c.successSoft, color: c.success,
                  fontSize: 11, fontWeight: 700,
                }}>Promedio 7.2/10</span>}
                sub="Últimos 30 días"
              >Evolución de ánimo</V3SectionTitle>
              <V3WaveChart
                data={[5, 6, 5.5, 7, 6.5, 7.5, 7.2, 8, 7.8, 8.5]}
                labels={["S1","S2","S3","S4","S5","S6","S7","S8","S9","S10"]}
                height={220} highlight={9} glow
              />
            </V3Card>
            <V3Card padding={22}>
              <V3SectionTitle sub="Últimos 7 días">Adherencia por módulo</V3SectionTitle>
              {[
                ["Ánimo",       90],
                ["Respiración", 72],
                ["TCC",         50],
                ["Rutina",      84],
                ["Actividades", 60],
              ].map(([n, v], i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "100px 1fr 40px", alignItems: "center", gap: 12, marginTop: 12 }}>
                  <span style={{ fontSize: 12, color: c.text2 }}>{n}</span>
                  <div style={{ height: 7, background: c.elevated, borderRadius: 999, overflow: "hidden" }}>
                    <div style={{
                      width: `${v}%`, height: "100%",
                      background: `linear-gradient(90deg, ${c.gradFrom}, ${c.gradTo})`,
                      borderRadius: 999,
                    }}/>
                  </div>
                  <span style={{ fontSize: 11, fontFamily: V3_FONT.mono, color: c.text2, textAlign: "right" }}>{v}%</span>
                </div>
              ))}
            </V3Card>
            <V3Card padding={0} style={{ gridColumn: "span 2" }}>
              <div style={{
                display: "grid", gridTemplateColumns: "100px 110px 1fr 120px 80px",
                padding: "14px 20px",
                borderBottom: `1px solid ${c.borderSoft}`,
                background: c.elevated,
                fontSize: 10, fontWeight: 700, color: c.text3, letterSpacing: ".1em", textTransform: "uppercase",
              }}>
                <div>Fecha</div><div>Módulo</div><div>Detalle</div><div>Métrica</div><div>Acción</div>
              </div>
              {[
                ["Hoy 09:15", "Ánimo",       "leaf",   c.teal,    "Buen día — desayuné en familia", "7/10"],
                ["Hoy 10:32", "Respiración", "lungs",  c.cyan,    "4-7-8 · 5 ciclos · 3 min", "completa"],
                ["Ayer 21:30","TCC",         "bulb",   c.violet,  "Reunión laboral · Ansiedad 7", "Paso 3/4"],
                ["Ayer 18:00","Actividades", "run",    c.success, "Caminata 20 min · Física", "completa"],
                ["Ayer 09:05","Rutina",      "routine",c.warning, "Mañana 4/4 · Tarde 2/3 · Noche 0/3", "75%"],
              ].map(([d, m, ic, col, det, val], i, arr) => (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "100px 110px 1fr 120px 80px",
                  padding: "14px 20px", alignItems: "center",
                  borderBottom: i < arr.length - 1 ? `1px solid ${c.borderSoft}` : "none",
                }}>
                  <span style={{ fontSize: 11, color: c.text3, fontFamily: V3_FONT.mono }}>{d}</span>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, color: col, fontWeight: 600 }}>
                    <NMIcon name={ic} size={14} color={col}/> {m}
                  </span>
                  <span style={{ fontSize: 12, color: c.text }}>{det}</span>
                  <span style={{ fontSize: 12, color: c.text2, fontFamily: V3_FONT.mono, fontWeight: 600 }}>{val}</span>
                  <V3Button variant="ghost" size="sm" icon={<NMIcon name="chevronRight" size={12}/>}/>
                </div>
              ))}
            </V3Card>
          </div>
        )}
        {tab === "Asignar" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <V3Card padding={22}>
              <V3SectionTitle sub="Crear una tarea para Ana en su rutina diaria">Asignar tarea</V3SectionTitle>
              <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 12 }}>
                <NMField label="Descripción" value="Hidratarme antes del desayuno"/>
                <div>
                  <div style={{ fontSize: 11, color: c.text3, fontWeight: 600, marginBottom: 8 }}>Sección del día</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                    {[["Mañana", true], ["Tarde", false], ["Noche", false]].map(([s, sel]) => (
                      <div key={s} style={{
                        padding: 12, borderRadius: 12,
                        background: sel ? c.tealSoft : c.surface,
                        border: `1.5px solid ${sel ? c.teal : c.borderSoft}`,
                        textAlign: "center", fontSize: 13, fontWeight: 600,
                        color: sel ? c.teal : c.text2,
                        cursor: "pointer",
                      }}>{s}</div>
                    ))}
                  </div>
                </div>
                <V3Button gradient icon={<NMIcon name="check" size={14} color="#fff"/>}>Asignar tarea</V3Button>
              </div>
            </V3Card>
            <V3Card padding={22}>
              <V3SectionTitle sub="Mensaje que aparecerá como push y en la app">Enviar recordatorio</V3SectionTitle>
              <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 12 }}>
                <NMField label="Mensaje" value="Acordate de tu pausa de respiración"/>
                <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 10 }}>
                  <NMField label="Hora" value="22:00" mono/>
                  <div>
                    <div style={{ fontSize: 11, color: c.text3, fontWeight: 600, marginBottom: 8 }}>Días</div>
                    <div style={{ display: "flex", gap: 5 }}>
                      {["L","M","M","J","V","S","D"].map((d, i) => (
                        <div key={i} style={{
                          flex: 1, height: 36, borderRadius: 10,
                          background: i < 5 ? c.tealSoft : c.elevated,
                          color: i < 5 ? c.teal : c.text3,
                          fontSize: 12, fontWeight: 700,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          border: `1px solid ${i < 5 ? c.teal + "44" : c.borderSoft}`,
                        }}>{d}</div>
                      ))}
                    </div>
                  </div>
                </div>
                <V3Button gradient icon={<NMIcon name="send" size={14} color="#fff"/>}>Enviar recordatorio</V3Button>
              </div>
            </V3Card>
            <V3Card padding={0} style={{ gridColumn: "span 2" }}>
              <div style={{ padding: 20, borderBottom: `1px solid ${c.borderSoft}` }}>
                <V3SectionTitle sub="Activos · 3 tareas y 2 recordatorios">Asignaciones vigentes</V3SectionTitle>
              </div>
              {[
                ["Pausa respiración", "Todos los días · 18:00",   "lungs",   c.teal,    "vigente", c.success],
                ["Diario gratitud",   "Lun a Vie · 21:30",        "note",    c.violet,  "vigente", c.success],
                ["Caminata 20 min",   "Lun · Mié · Vie variable", "run",     c.teal,    "pausada", c.warning],
              ].map(([n, sch, ic, col, st, stCol], i, arr) => (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "auto 1fr auto auto auto",
                  gap: 14, alignItems: "center", padding: "14px 20px",
                  borderBottom: i < arr.length - 1 ? `1px solid ${c.borderSoft}` : "none",
                }}>
                  <NMIcon name={ic} size={18} color={col}/>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: c.text }}>{n}</div>
                    <div style={{ fontSize: 11, color: c.text3 }}>{sch}</div>
                  </div>
                  <span style={{
                    padding: "3px 9px", borderRadius: 999,
                    background: stCol + "22", color: stCol,
                    fontSize: 11, fontWeight: 600,
                  }}>{st}</span>
                  <V3Button variant="ghost" size="sm" icon={<NMIcon name="edit" size={12}/>}>Editar</V3Button>
                  <NMIcon name="dots" size={16} color={c.text3}/>
                </div>
              ))}
            </V3Card>
          </div>
        )}
        {tab === "Banco" && (
          <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 16 }}>
            <V3Card padding={22}>
              <V3SectionTitle sub="Agregá una nueva actividad al banco de Ana">Nueva actividad</V3SectionTitle>
              <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 12 }}>
                <NMField label="Nombre" value="Yoga matinal"/>
                <NMField label="Descripción breve" value="15 min de yoga suave antes del desayuno"/>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  <NMField label="Categoría" value="Física" select/>
                  <NMField label="Ánimo objetivo" value="4 – 7 medio" select/>
                </div>
                <div style={{ display: "flex", gap: 10 }}>
                  <V3Button variant="secondary" icon={<NMIcon name="sparkle" size={14} color={c.violet}/>}>IA · completar descripción</V3Button>
                  <V3Button gradient icon={<NMIcon name="plus" size={14} color="#fff" filled/>} style={{ marginLeft: "auto" }}>Agregar al banco</V3Button>
                </div>
              </div>
            </V3Card>
            <V3Card padding={20}>
              <V3SectionTitle sub="33 actividades activas">Banco actual</V3SectionTitle>
              <div style={{ maxHeight: 340, overflow: "auto" }}>
                {[
                  ["Caminata 30 min",    "Física",      "run",     c.teal,    "ánimo 4–9"],
                  ["Llamar a familiar",  "Social",      "users",   c.warning, "ánimo 3–8"],
                  ["Lectura ficción",    "Cognitiva",   "book",    c.cyan,    "ánimo 4–8"],
                  ["Bañarse con calma",  "Autocuidado", "water",   c.success, "ánimo 1–8"],
                  ["Tocar guitarra",     "Maestría",    "trophy",  c.teal,    "ánimo 5–10"],
                  ["Salir a la naturaleza","Placer",    "leaf",    c.violet,  "ánimo 4–10"],
                ].map(([n, cat, ic, col, range], i, arr) => (
                  <div key={i} style={{
                    display: "grid", gridTemplateColumns: "auto 1fr auto",
                    gap: 10, padding: "10px 0", alignItems: "center",
                    borderBottom: i < arr.length - 1 ? `1px solid ${c.borderSoft}` : "none",
                  }}>
                    <NMIcon name={ic} size={16} color={col}/>
                    <div>
                      <div style={{ fontSize: 12, color: c.text, fontWeight: 600 }}>{n}</div>
                      <div style={{ fontSize: 10, color: c.text3 }}>{cat} · {range}</div>
                    </div>
                    <NMIcon name="dots" size={14} color={c.text3}/>
                  </div>
                ))}
              </div>
            </V3Card>
          </div>
        )}
        {tab === "IA" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <V3Card padding={22} glow>
              <V3SectionTitle
                action={<span style={{
                  padding: "4px 10px", borderRadius: 999,
                  background: c.violetSoft, color: c.violet,
                  fontSize: 10, fontWeight: 700, display: "inline-flex", alignItems: "center", gap: 4,
                }}><NMIcon name="sparkle" size={10} color={c.violet}/> Groq · llama3</span>}
                sub="Análisis automático de las últimas 2 semanas"
              >Resumen IA · Evolución de Ana</V3SectionTitle>
              <div style={{
                marginTop: 12, padding: 16, borderRadius: 14,
                background: c.elevated, border: `1px solid ${c.borderSoft}`,
                fontSize: 13, color: c.text2, lineHeight: 1.65,
              }}>
                En las últimas <strong style={{ color: c.text }}>2 semanas</strong> el promedio de ánimo subió de
                <strong style={{ color: c.text }}> 6.4 a 7.2/10</strong> (+12.5%). La adherencia a respiración es del
                <strong style={{ color: c.teal }}> 72%</strong>, con registros concentrados en la mañana (08–10h).
                El módulo TCC quedó pausado en el paso 3 hace 4 días.
                <div style={{ marginTop: 12 }}>
                  <strong style={{ color: c.text }}>Sugerencias:</strong> retomar TCC con sesión breve y revisar
                  disparadores del horario laboral (13–15h, donde el ánimo cae).
                </div>
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
                <V3Button variant="ghost" size="sm" icon={<NMIcon name="refresh" size={12}/>}>Regenerar</V3Button>
                <V3Button variant="secondary" size="sm" icon={<NMIcon name="save" size={12}/>}>Copiar</V3Button>
                <V3Button gradient size="sm" icon={<NMIcon name="arrowRight" size={12} color="#fff"/>} style={{ marginLeft: "auto" }}>Generar acciones</V3Button>
              </div>
            </V3Card>
            <V3Card padding={22}>
              <V3SectionTitle sub="3 propuestas concretas para tu próxima sesión">Acciones sugeridas</V3SectionTitle>
              <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
                {[
                  ["Retomar TCC",              "Sesión breve de 10 min · paso 3 reestructuración", "bulb",  c.violet],
                  ["Pausa en horario crítico", "Recordatorio 13:30 con respiración 4-7-8",         "lungs", c.teal],
                  ["Actividad social",         "Sugerir café con un amigo este fin de semana",     "users", c.warning],
                ].map(([n, d, ic, col], i) => (
                  <div key={i} style={{
                    padding: 14, borderRadius: 14,
                    background: col + "12",
                    border: `1px solid ${col}33`,
                    display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 12, alignItems: "center",
                  }}>
                    <NMIcon name={ic} size={20} color={col}/>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: c.text }}>{n}</div>
                      <div style={{ fontSize: 11, color: c.text2, marginTop: 2 }}>{d}</div>
                    </div>
                    <V3Button gradient size="sm" icon={<NMIcon name="check" size={11} color="#fff"/>}>Aplicar</V3Button>
                  </div>
                ))}
              </div>
            </V3Card>
          </div>
        )}
      </div>
    </div>
  );
}

// Helper: field con label
function NMField({ label, value, mono = false, select = false }) {
  const { c } = useV3Theme();
  return (
    <div>
      <div style={{ fontSize: 11, color: c.text3, fontWeight: 600, marginBottom: 6 }}>{label}</div>
      <div style={{
        display: "flex", alignItems: "center",
        padding: "10px 14px", borderRadius: 12,
        background: c.surface, border: `1px solid ${c.border}`,
        fontSize: 13, color: c.text,
        fontFamily: mono ? V3_FONT.mono : V3_FONT.sans,
        fontWeight: 500,
      }}>
        <span style={{ flex: 1 }}>{value}</span>
        {select && <NMIcon name="chevronDown" size={12} color={c.text3}/>}
      </div>
    </div>
  );
}

// ─── Hub · IA Asistente full ──────────────────────────────────────────────────
function V3HubIA({ mode = "dark" }) {
  return (
    <V3Shell defaultMode={mode} width={1360} height={920}
      sidebar={<V3Sidebar active="ia" appName="NeuroMood" role="Hub Pro" items={V3HubNavItems()}/>}>
      <V3HubIABody mode={mode}/>
    </V3Shell>
  );
}
function V3HubIABody({ mode }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{ height: "100%", display: "grid", gridTemplateColumns: "1fr 320px", overflow: "hidden" }}>
      <div style={{ display: "flex", flexDirection: "column", padding: "20px 28px 20px", overflow: "hidden" }}>
        <V3Header
          title="IA Asistente clínico"
          subtitle="Análisis y sugerencias basadas en los datos cargados del paciente seleccionado."
          mode={mode}
          actions={
            <span style={{
              padding: "8px 14px", borderRadius: 14,
              background: c.surface, border: `1px solid ${c.borderSoft}`,
              fontSize: 12, color: c.text, fontWeight: 600,
              display: "inline-flex", alignItems: "center", gap: 8,
            }}>
              <span style={{ width: 7, height: 7, borderRadius: 999, background: c.success,
                             boxShadow: `0 0 0 4px ${c.success}22` }}/>
              Groq · llama3-70b
              <NMIcon name="chevronDown" size={10} color={c.text2}/>
            </span>
          }
        />
        {/* Chat */}
        <div style={{ flex: 1, overflow: "auto", padding: "0 0 12px", display: "flex", flexDirection: "column", gap: 14 }}>
          <V3ChatBubble who="ia">
            Hola, Dr. López. Analicé los datos de <strong>Ana Martínez</strong> de las últimas 2 semanas.
            ¿Querés un resumen ejecutivo o tenés una pregunta específica?
          </V3ChatBubble>
          <V3ChatBubble who="user">¿Cómo estuvo su ánimo esta semana comparado con la anterior?</V3ChatBubble>
          <V3ChatBubble who="ia">
            El promedio fue <strong>7.2/10</strong> esta semana vs <strong>6.4/10</strong> la anterior — tendencia positiva (+12.5%).
            Los días con mayor puntaje (8, 8.5) coinciden con sesiones de respiración registradas a la mañana.
            <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              <V3MiniStat label="Esta semana" value="7.2" tone="success"/>
              <V3MiniStat label="Anterior"    value="6.4" tone="default"/>
              <V3MiniStat label="Δ"           value="+0.8" tone="success"/>
            </div>
          </V3ChatBubble>
          <V3ChatBubble who="user">¿Qué intervención concreta podrías sugerir para sostener la mejora?</V3ChatBubble>
          <V3ChatBubble who="ia">
            Para Ana sugiero <strong>3 acciones</strong> que mantienen la lógica clínica actual y aprovechan los horarios donde su adherencia es más alta:
            <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                ["bulb",  c.violet, "Retomar TCC paso 3", "10 min · reestructuración"],
                ["lungs", c.teal,   "Pausa de respiración a las 13:30", "Recordatorio diario"],
                ["users", c.warning,"Sugerir actividad social fin de semana", "Café con un amigo"],
              ].map(([ic, col, n, d], i) => (
                <div key={i} style={{
                  padding: 10, borderRadius: 10,
                  background: col + "15", border: `1px solid ${col}33`,
                  display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 10, alignItems: "center",
                }}>
                  <NMIcon name={ic} size={16} color={col}/>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: c.text }}>{n}</div>
                    <div style={{ fontSize: 11, color: c.text2 }}>{d}</div>
                  </div>
                  <V3Button variant="ghost" size="sm" icon={<NMIcon name="check" size={11} color={col}/>}>Aplicar</V3Button>
                </div>
              ))}
            </div>
          </V3ChatBubble>
          <V3ChatBubble who="ia" typing/>
        </div>
        {/* Quick prompts */}
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          {[
            ["Analizar ánimo",     "chart"],
            ["Proponer actividades","sparkle"],
            ["Revisar distorsiones","bulb"],
            ["Generar informe",     "report"],
          ].map(([t2, ic]) => (
            <div key={t2} style={{
              padding: "8px 14px", borderRadius: 999,
              background: c.elevated, border: `1px solid ${c.borderSoft}`,
              fontSize: 11, color: c.text2, cursor: "pointer", fontWeight: 600,
              display: "inline-flex", alignItems: "center", gap: 6,
            }}>
              <NMIcon name={ic} size={12} color={c.teal}/>
              {t2}
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: 10, marginTop: 12, alignItems: "center" }}>
          <div style={{
            flex: 1, display: "flex", alignItems: "center", gap: 10,
            padding: "10px 14px",
            borderRadius: 16,
            background: c.surface, border: `1px solid ${c.border}`,
          }}>
            <NMIcon name="edit" size={14} color={c.text3}/>
            <span style={{ flex: 1, fontSize: 13, color: c.text3 }}>Escribí tu consulta clínica…</span>
            <NMIcon name="sparkle" size={14} color={c.violet}/>
          </div>
          <V3Button gradient icon={<NMIcon name="send" size={14} color="#fff"/>}>Enviar</V3Button>
        </div>
        <div style={{ fontSize: 10, color: c.text3, marginTop: 6, textAlign: "center" }}>
          IA puede cometer errores. Las sugerencias no reemplazan criterio clínico profesional.
        </div>
      </div>

      {/* Right rail: contexto */}
      <div style={{ background: c.bgAlt, borderLeft: `1px solid ${c.borderSoft}`, padding: 20, overflow: "auto" }}>
        <V3SectionTitle>Contexto del paciente</V3SectionTitle>
        <V3Card padding={16}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 44, height: 44, borderRadius: 999,
              background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
              color: "#fff", fontWeight: 700, fontSize: 13,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>AM</div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: c.text }}>Ana Martínez</div>
              <div style={{ fontSize: 11, color: c.text3 }}>Semana 12 · Ansiedad</div>
            </div>
          </div>
        </V3Card>
        <div style={{ fontSize: 11, color: c.text3, lineHeight: 1.6, marginTop: 14 }}>
          La IA tiene acceso a los registros cargados. No realiza diagnóstico ni reemplaza criterio profesional.
        </div>
        <div style={{ height: 1, background: c.borderSoft, margin: "16px 0" }}/>
        <V3SectionTitle>Datos cargados</V3SectionTitle>
        {[
          ["Ánimo",       "20 registros",  "leaf",   c.teal],
          ["Respiración", "15 sesiones",   "lungs",  c.cyan],
          ["TCC",         "8 entradas",    "bulb",   c.violet],
          ["Rutina",      "84% adherencia","routine",c.warning],
        ].map(([k, v, ic, col], i, arr) => (
          <div key={k} style={{
            display: "grid", gridTemplateColumns: "auto 1fr auto",
            gap: 10, padding: "10px 0", alignItems: "center",
            borderBottom: i < arr.length - 1 ? `1px solid ${c.borderSoft}` : "none",
          }}>
            <NMIcon name={ic} size={16} color={col}/>
            <span style={{ fontSize: 12, color: c.text2 }}>{k}</span>
            <span style={{ fontSize: 11, color: c.text, fontWeight: 600, fontFamily: V3_FONT.mono }}>{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function V3ChatBubble({ who, children, typing = false }) {
  const { c, isDark } = useV3Theme();
  const isUser = who === "user";
  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
    }}>
      <div style={{
        maxWidth: "78%",
        padding: "14px 18px",
        borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
        background: isUser ? `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})` : c.surface,
        color: isUser ? "#fff" : c.text,
        fontSize: 13,
        lineHeight: 1.6,
        border: isUser ? "none" : `1px solid ${c.borderSoft}`,
        boxShadow: isUser
          ? `0 8px 20px -6px ${c.teal}55`
          : (isDark ? "0 1px 2px rgba(0,0,0,.3)" : "0 1px 3px rgba(15,23,42,.05)"),
      }}>
        {typing ? (
          <span style={{ display: "inline-flex", gap: 4, padding: "2px 0" }}>
            {[0, 1, 2].map(i => (
              <span key={i} style={{
                width: 8, height: 8, borderRadius: 999,
                background: c.text3,
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

function V3MiniStat({ label, value, tone }) {
  const { c } = useV3Theme();
  const bg = tone === "success" ? c.successSoft : c.elevated;
  const fg = tone === "success" ? c.success : c.text;
  return (
    <div style={{
      padding: 10, borderRadius: 10,
      background: bg, textAlign: "center",
    }}>
      <div style={{ fontSize: 10, color: c.text3, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: fg, fontFamily: V3_FONT.mono }}>{value}</div>
    </div>
  );
}

// ─── Hub · Configuración ──────────────────────────────────────────────────────
function V3HubConfig({ mode = "light" }) {
  return (
    <V3Shell defaultMode={mode} width={1360} height={920}
      sidebar={<V3Sidebar active="config" appName="NeuroMood" role="Hub Pro" items={V3HubNavItems()}/>}>
      <V3HubConfigBody mode={mode}/>
    </V3Shell>
  );
}
function V3HubConfigBody({ mode }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", overflow: "auto" }}>
      <V3Header title="Configuración" subtitle="Cuenta, sincronización, IA y apariencia." mode={mode}/>
      <div style={{ padding: "0 28px 28px", display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Sync status hero */}
        <V3Card padding={22}>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 16, alignItems: "center" }}>
            <div style={{
              width: 52, height: 52, borderRadius: 16,
              background: c.successSoft, color: c.success,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <NMIcon name="check" size={24} color={c.success}/>
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: c.text }}>Sincronizado con Supabase</div>
              <div style={{ fontSize: 12, color: c.text3, marginTop: 2 }}>Última verificación: hoy 14:23 · 12 pacientes activos · 482 registros</div>
            </div>
            <V3Button variant="secondary" icon={<NMIcon name="refresh" size={14}/>}>Sincronizar ahora</V3Button>
          </div>
        </V3Card>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          {/* Conexión */}
          <V3Card padding={20}>
            <V3SectionTitle sub="Cuenta y credenciales remotas">Conexión Supabase</V3SectionTitle>
            <NMConfigRow k="URL" v="https://xyz.supabase.co" mono/>
            <NMConfigRow k="API Key" v="••••••••••4f3a" mono/>
            <NMConfigRow k="Auto-sync" right={<NMToggle checked/>}/>
            <NMConfigRow k="Backup local" right={<NMToggle checked/>}/>
            <NMConfigRow k="Última verificación" v="hoy 14:23"/>
          </V3Card>

          {/* Apariencia */}
          <V3Card padding={20}>
            <V3SectionTitle sub="Tema, densidad e idioma">Apariencia</V3SectionTitle>
            <NMConfigRow k="Tema" right={
              <div style={{ display: "flex", gap: 4, padding: 3, background: c.elevated, borderRadius: 10 }}>
                {[["Claro", !isDark], ["Oscuro", isDark], ["Sistema", false]].map(([n, a]) => (
                  <span key={n} style={{
                    padding: "5px 12px", fontSize: 11, fontWeight: 600,
                    background: a ? c.surface : "transparent",
                    color: a ? c.text : c.text3,
                    borderRadius: 8,
                    boxShadow: a ? (isDark ? "0 0 0 1px rgba(94,234,212,.2)" : "0 1px 3px rgba(15,23,42,.06)") : "none",
                  }}>{n}</span>
                ))}
              </div>
            }/>
            <NMConfigRow k="Densidad" right={
              <div style={{ display: "flex", gap: 4, padding: 3, background: c.elevated, borderRadius: 10 }}>
                {[["Compacta", false], ["Normal", true], ["Cómoda", false]].map(([n, a]) => (
                  <span key={n} style={{
                    padding: "5px 12px", fontSize: 11, fontWeight: 600,
                    background: a ? c.surface : "transparent",
                    color: a ? c.text : c.text3,
                    borderRadius: 8,
                  }}>{n}</span>
                ))}
              </div>
            }/>
            <NMConfigRow k="Idioma" v="Español (Argentina)"/>
            <NMConfigRow k="Proveedor IA" v="Groq · llama3-70b" mono/>
          </V3Card>

          {/* Seguridad */}
          <V3Card padding={20}>
            <V3SectionTitle sub="Acceso, datos y permisos">Seguridad</V3SectionTitle>
            <NMConfigRow k="Bloqueo automático" v="5 min de inactividad"/>
            <NMConfigRow k="2FA" right={<NMToggle checked/>}/>
            <NMConfigRow k="Cifrado en reposo" right={
              <span style={{
                padding: "3px 10px", borderRadius: 999,
                background: c.successSoft, color: c.success,
                fontSize: 11, fontWeight: 700,
              }}>AES-256</span>
            }/>
            <NMConfigRow k="Logs auditables" right={<NMToggle checked/>}/>
            <NMConfigRow k="Retención de datos" v="365 días"/>
          </V3Card>

          {/* Log */}
          <V3Card padding={20}>
            <V3SectionTitle sub="Últimos eventos de sincronización">Log de sincronización</V3SectionTitle>
            <div style={{
              fontFamily: V3_FONT.mono, fontSize: 11,
              lineHeight: 1.85, color: c.text2,
              padding: 14, borderRadius: 12,
              background: isDark ? "rgba(0,0,0,.3)" : c.elevated,
              marginTop: 6,
            }}>
              {[
                ["check",  c.success, "14:23:01 — Sync completada · 12 pacientes"],
                ["refresh",c.teal,    "14:23:00 — Conectando a Supabase…"],
                ["check",  c.success, "14:10:44 — Backup local generado"],
                ["warning",c.warning, "13:12:08 — Timeout (reintentado ok)"],
                ["check",  c.success, "13:10:00 — Sync completada · 12 pacientes"],
              ].map(([ic, col, line], i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <NMIcon name={ic} size={11} color={col}/>
                  <span>{line}</span>
                </div>
              ))}
            </div>
          </V3Card>
        </div>
      </div>
    </div>
  );
}

function NMConfigRow({ k, v, right, mono = false }) {
  const { c } = useV3Theme();
  return (
    <div style={{
      display: "flex", justifyContent: "space-between",
      padding: "12px 0", alignItems: "center",
      borderBottom: `1px solid ${c.borderSoft}`,
      fontSize: 13,
    }}>
      <span style={{ color: c.text3 }}>{k}</span>
      {right ? right : (
        <span style={{
          color: c.text, fontWeight: 500,
          fontFamily: mono ? V3_FONT.mono : V3_FONT.sans,
        }}>{v}</span>
      )}
    </div>
  );
}

function NMToggle({ checked }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{
      width: 42, height: 24, borderRadius: 999,
      background: checked ? `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})` : c.elevated,
      border: `1px solid ${checked ? "transparent" : c.borderStrong}`,
      position: "relative",
      boxShadow: checked ? `0 4px 10px -2px ${c.teal}66` : "none",
      transition: "all .2s ease",
    }}>
      <div style={{
        position: "absolute", top: 2, left: checked ? 20 : 2,
        width: 18, height: 18, borderRadius: 999,
        background: "#fff",
        boxShadow: "0 1px 3px rgba(0,0,0,.25)",
        transition: "left .2s ease",
      }}/>
    </div>
  );
}

Object.assign(window, {
  V3SuiteTCC, V3SuiteRutina, V3SuiteActividades, V3SuiteTimer,
  V3HubDetalle, V3HubIA, V3HubConfig,
  NMCheckBox, NMField, V3ChatBubble, V3MiniStat, NMConfigRow, NMToggle,
  V3HubNavItems,
});
