/* v3-screens.jsx — Pantallas en el sistema final.
 * Suite: Inicio, Ánimo, Respiración, Avisos.
 * Hub: Dashboard.
 * Alineado a las 5 referencias del usuario.
 */

// ── Suite · Inicio (Home) ─────────────────────────────────────────────────────
function V3SuiteInicio({ mode = "light" }) {
  return (
    <V3Shell defaultMode={mode} sidebar={<V3Sidebar active="inicio"/>} width={1320} height={860}>
      <V3InicioBody mode={mode}/>
    </V3Shell>
  );
}

function V3InicioBody({ mode }) {
  const { c, isDark } = useV3Theme();
  const setMode = () => {}; // captured by tweaks panel, no-op here
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", overflow: "auto" }}>
      <V3Header
        title="¡Hola, Ana!"
        subtitle="Estás haciendo un gran trabajo cuidando tu bienestar."
        streak={12}
        mode={mode}
      />
      <div style={{ padding: "0 28px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Top hero: bienestar hoy */}
        <V3Card padding={24}>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr 280px", gap: 28, alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <V3Ring pct={78} size={120} stroke={9} value="78" sub="de 100"/>
              <div>
                <div style={{ fontSize: 12, color: c.text3 }}>Bienestar general</div>
                <div style={{
                  fontSize: 26, fontWeight: 700, color: c.text,
                  background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
                  WebkitBackgroundClip: "text",
                  color: "transparent",
                  letterSpacing: "-.015em",
                }}>Muy bien</div>
                <div style={{ fontSize: 12, color: c.text2, marginTop: 4, lineHeight: 1.45, maxWidth: 180 }}>
                  Sigue así, cada pequeño paso cuenta.
                </div>
              </div>
            </div>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <div style={{ fontSize: 13, color: c.text2 }}>Evolución de tu ánimo</div>
                <div style={{
                  padding: "4px 10px", borderRadius: 999,
                  background: c.elevated, border: `1px solid ${c.borderSoft}`,
                  fontSize: 11, color: c.text2, fontWeight: 500,
                  display: "flex", alignItems: "center", gap: 6,
                }}>7 días ▾</div>
              </div>
              <V3WaveChart data={[3, 6, 4, 7, 5, 8, 9]}
                            labels={["Lun","Mar","Mié","Jue","Vie","Sáb","Hoy"]}
                            height={170}/>
            </div>
            <div>
              <div style={{ fontSize: 12, color: c.text2, marginBottom: 12, fontWeight: 600 }}>Tu progreso esta semana</div>
              {[
                ["Sesiones completadas", "4 de 6", 67, "check"],
                ["Minutos de respiración", "82 de 120 min", 68, "timer"],
                ["Actividades realizadas", "5 de 7", 71, "sparkle"],
              ].map(([label, val, pct, ic]) => (
                <div key={label} style={{ marginBottom: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontSize: 11, color: c.text2, display: "flex", alignItems: "center", gap: 5 }}>
                      <NMIcon name={ic} size={14} color={c.teal}/>
                      {label}
                    </span>
                    <span style={{ fontSize: 11, color: c.text, fontWeight: 600 }}>{val}</span>
                  </div>
                  <div style={{ height: 6, background: c.elevated, borderRadius: 999, overflow: "hidden" }}>
                    <div style={{
                      width: `${pct}%`, height: "100%",
                      background: `linear-gradient(90deg, ${c.gradFrom}, ${c.gradTo})`,
                      borderRadius: 999,
                    }}/>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </V3Card>

        {/* 4 module cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
          {[
            { name: "Ánimo",       chip: "Hoy",       iconName: "mood",   tone: "cyan",
              status: "Buen ánimo", sub: "Último registro · Hoy, 09:30", cta: "Registrar ánimo" },
            { name: "Respiración", chip: "4-7-8",     iconName: "breath", tone: "teal",
              status: "Sesión rápida", sub: "7 minutos", cta: "Iniciar sesión" },
            { name: "TCC",         chip: "Ejercicios", iconName: "bulb",  tone: "violet",
              status: "Pensamientos", sub: "3 ejercicios pendientes", cta: "Continuar" },
            { name: "Rutina",      chip: "Hoy",       iconName: "routine", tone: "teal",
              status: "2 de 4 tareas", sub: "Sigue tu plan diario", cta: "Ver rutina" },
          ].map((m, i) => (
            <V3Card key={m.name} padding={18}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: c.text }}>{m.name}</div>
                <div style={{
                  padding: "3px 9px", borderRadius: 999,
                  background: c.elevated, color: c.text2,
                  fontSize: 10, fontWeight: 600,
                }}>{m.chip}</div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 14 }}>
                <NMIcon name={m.iconName} size={48} color={c[m.tone] || c.teal} strokeWidth={2.4}/>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: c.text }}>{m.status}</div>
                  <div style={{ fontSize: 11, color: c.text3, marginTop: 2 }}>{m.sub}</div>
                </div>
              </div>
              <V3Button gradient fullWidth size="sm">{m.cta}</V3Button>
            </V3Card>
          ))}
        </div>

        {/* Bottom 3-col: actividades + respiración + avisos */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
          {/* Actividades recomendadas */}
          <V3Card padding={20}>
            <V3SectionTitle action={<span style={{ fontSize: 11, color: c.teal, fontWeight: 600 }}>Para ti</span>}>
              Actividades recomendadas
            </V3SectionTitle>
            {[
              ["leaf", "Meditación guiada", "10 min · Relajación", c.violet],
              ["note", "Diario de gratitud", "5 min · Bienestar",  c.teal],
              ["heart", "Ejercicio de autocompasión", "15 min · Crecimiento personal", c.cyan],
            ].map(([ic, n, d, col], i) => (
              <div key={i} style={{
                display: "grid", gridTemplateColumns: "auto 1fr auto",
                gap: 12, padding: "10px 12px",
                borderRadius: 12,
                background: c.elevated,
                marginBottom: 8,
                alignItems: "center",
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10,
                  background: col + "22", color: col,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 16,
                }}><NMIcon name={ic} size={16} color="currentColor"/></div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: c.text }}>{n}</div>
                  <div style={{ fontSize: 11, color: c.text3 }}>{d}</div>
                </div>
                <NMPlayButton icon="play" size={32}/>
              </div>
            ))}
            <div style={{ textAlign: "center", marginTop: 8, fontSize: 12, color: c.teal, fontWeight: 600, cursor: "pointer" }}>
              Ver todas las actividades
            </div>
          </V3Card>

          {/* Sesión rápida (breathing ring) */}
          <V3Card padding={20}>
            <V3SectionTitle sub="Respiración 4-7-8">Sesión rápida</V3SectionTitle>
            <div style={{ display: "flex", justifyContent: "center", marginTop: 8 }}>
              <div style={{ position: "relative", width: 160, height: 160 }}>
                <V3Ring pct={65} size={160} stroke={11}/>
                <div style={{
                  position: "absolute", inset: 0,
                  display: "flex", flexDirection: "column",
                  alignItems: "center", justifyContent: "center",
                }}>
                  <NMPlayButton icon="play" size={56}/>
                  <div style={{ fontSize: 11, color: c.text2, marginTop: 8, fontWeight: 600 }}>Iniciar</div>
                </div>
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6, marginTop: 14 }}>
              {[["Inhala","4 seg"], ["Mantén","7 seg"], ["Exhala","8 seg"]].map(([k, v]) => (
                <div key={k} style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 10, color: c.text3 }}>{k}</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: c.text, fontFamily: V3_FONT.mono }}>{v}</div>
                </div>
              ))}
            </div>
          </V3Card>

          {/* Avisos y agenda */}
          <V3Card padding={20}>
            <V3SectionTitle action={<span style={{ fontSize: 11, color: c.teal, fontWeight: 600 }}>Ver todo</span>}>
              Avisos y agenda
            </V3SectionTitle>
            {[
              ["water", "Tomar medicación", "10:00 AM", "Hoy", c.cyan, "warning"],
              ["sparkle", "Sesión con terapeuta", "Miércoles, 15 de mayo", "4:00 PM", c.violet, "default"],
              ["leaf", "Respiración diaria", "Todos los días", "9:00 AM", c.teal, "default"],
            ].map(([ic, n, sched, time, col, badge], i) => (
              <div key={i} style={{
                display: "grid", gridTemplateColumns: "auto 1fr auto",
                gap: 12, padding: "10px 12px",
                borderRadius: 12,
                background: c.elevated,
                marginBottom: 8,
                alignItems: "center",
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10,
                  background: col + "22", color: col,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 16,
                }}><NMIcon name={ic} size={16} color="currentColor"/></div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: c.text }}>{n}</div>
                  <div style={{ fontSize: 11, color: c.text3 }}>{sched}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: c.text }}>{time}</div>
                </div>
              </div>
            ))}
            <V3Button variant="secondary" fullWidth size="sm" style={{ marginTop: 4 }}>+ Nuevo aviso</V3Button>
          </V3Card>
        </div>

        {/* Footer reminder */}
        <V3Card padding={18}>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 14, alignItems: "center" }}>
            <div style={{
              width: 40, height: 40, borderRadius: 12,
              background: c.violetSoft, color: c.violet,
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
            }}><NMIcon name="heart" size={18} color="currentColor"/></div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: c.text }}>Recuerda: Tu bienestar es una prioridad, no una recompensa.</div>
              <div style={{ fontSize: 11, color: c.text3, marginTop: 2 }}>Pequeñas acciones diarias crean grandes cambios.</div>
            </div>
            <V3Button gradient size="md" icon={<NMIcon name="sparkle" size={14} color="currentColor" />}>Comenzar sesión guiada</V3Button>
          </div>
        </V3Card>
      </div>
    </div>
  );
}

// ── Suite · Ánimo / Mood Tracker ──────────────────────────────────────────────
function V3SuiteAnimo({ mode = "light" }) {
  return (
    <V3Shell defaultMode={mode} sidebar={<V3Sidebar active="animo"/>} width={1320} height={860}>
      <V3AnimoBody mode={mode}/>
    </V3Shell>
  );
}

function V3AnimoBody({ mode }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", overflow: "auto" }}>
      <V3Header
        title="Mood Tracker"
        subtitle="Registra tu estado de ánimo y descubre tus patrones emocionales."
        mode={mode}
        actions={
          <>
            <div style={{
              padding: "10px 14px",
              borderRadius: 14,
              background: c.surface,
              border: `1px solid ${c.borderSoft}`,
              display: "flex", alignItems: "center", gap: 8,
              fontSize: 12, color: c.text, fontWeight: 600,
            }}>
              12 – 18 de mayo
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M2 4l3 3 3-3" stroke={c.text2} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div style={{
              width: 40, height: 40, borderRadius: 14,
              background: c.surface, border: `1px solid ${c.borderSoft}`,
              display: "flex", alignItems: "center", justifyContent: "center",
              color: c.text2,
            }}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <rect x="2" y="6" width="3" height="8" rx=".5" fill="currentColor"/>
                <rect x="6.5" y="2" width="3" height="12" rx=".5" fill="currentColor"/>
                <rect x="11" y="8" width="3" height="6" rx=".5" fill="currentColor"/>
              </svg>
            </div>
            <div style={{
              width: 40, height: 40, borderRadius: 14,
              background: c.surface, border: `1px solid ${c.borderSoft}`,
              display: "flex", alignItems: "center", justifyContent: "center",
              color: c.text2,
            }}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 1v9m-4-4l4 4 4-4M1 12h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </>
        }
      />
      <div style={{ padding: "0 28px 28px", display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Big chart */}
        <V3Card padding={24}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: c.text }}>Evolución de tu ánimo</div>
            <div style={{
              padding: "5px 12px", borderRadius: 999,
              background: c.elevated, border: `1px solid ${c.borderSoft}`,
              fontSize: 11, color: c.text2, fontWeight: 600,
            }}>7 días ▾</div>
          </div>
          <div style={{ position: "relative" }}>
            <V3WaveChart
              data={[3, 6, 4, 7, 5, 8, 9]}
              labels={["Lun 12","Mar 13","Mié 14","Jue 15","Vie 16","Sáb 17","Hoy 18"]}
              height={280}
              highlight={3}
            />
            {/* tooltip */}
            <div style={{
              position: "absolute",
              top: 30,
              left: "calc(50% - 60px)",
              padding: "10px 14px",
              borderRadius: 14,
              background: c.surface,
              border: `1px solid ${c.borderSoft}`,
              boxShadow: isDark ? "0 4px 16px rgba(94,234,212,.15)" : "0 8px 20px rgba(15,23,42,.10)",
              display: "flex", alignItems: "center", gap: 10,
              minWidth: 180,
            }}>
              <NMMoodChip level={7} size={36}/>
              <div>
                <div style={{ fontSize: 11, color: c.text3 }}>Jueves 15 de mayo</div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                  <span style={{ fontSize: 18, fontWeight: 700, color: c.teal }}>7</span>
                  <span style={{ fontSize: 13, color: c.text }}>Feliz</span>
                </div>
              </div>
            </div>
          </div>
        </V3Card>

        {/* ¿Cómo te sientes hoy? — slashbar 1-10 con emoji dinámico */}
        <V3Card padding={28}>
          <V3MoodSlider initial={7}/>
        </V3Card>

        {/* Nota del día + Insights */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.3fr", gap: 16 }}>
          <V3Card padding={22}>
            <div style={{ fontSize: 16, fontWeight: 700, color: c.text, marginBottom: 4 }}>Nota del día</div>
            <div style={{ fontSize: 12, color: c.text3, marginBottom: 14 }}>Escribe cómo te sientes, qué pasó o qué agradeces hoy.</div>
            <div style={{
              padding: 14,
              borderRadius: 12,
              background: c.elevated,
              border: `1px solid ${c.borderSoft}`,
              minHeight: 100,
              fontSize: 13, lineHeight: 1.55,
              color: c.text2,
            }}>
              Tuve una reunión muy productiva en el trabajo y terminé el día con una caminata al aire libre. Me siento agradecida.
              <div style={{
                position: "relative", bottom: -40,
                textAlign: "right",
                fontSize: 10, color: c.text4, fontFamily: V3_FONT.mono,
              }}>103/500</div>
            </div>
            <V3Button gradient icon={<NMIcon name="save" size={14} color="currentColor" />} style={{ marginTop: 14 }}>Guardar nota</V3Button>
          </V3Card>
          <V3Card padding={22}>
            <div style={{ fontSize: 16, fontWeight: 700, color: c.text, marginBottom: 14 }}>Insights de esta semana</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
              {/* Promedio */}
              <div style={{
                padding: 16, borderRadius: 14,
                background: c.elevated,
                border: `1px solid ${c.borderSoft}`,
                textAlign: "center",
              }}>
                <div style={{ fontSize: 11, color: c.text3, marginBottom: 10 }}>Promedio de ánimo</div>
                <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>
                  <V3Ring pct={66} size={70} stroke={7} value="6.6" sub="Feliz"/>
                </div>
                <div style={{ fontSize: 10, color: c.success, fontWeight: 600 }}>↑ 1.2 vs semana anterior</div>
              </div>
              {/* Racha */}
              <div style={{
                padding: 16, borderRadius: 14,
                background: c.elevated,
                border: `1px solid ${c.borderSoft}`,
                textAlign: "center",
              }}>
                <div style={{ fontSize: 11, color: c.text3, marginBottom: 10 }}>Racha actual</div>
                <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>
                  <V3Ring pct={42} size={70} stroke={6} value="5" sub="días"/>
                </div>
                <div style={{ fontSize: 10, color: c.text3 }}>¡Sigue así!</div>
                <div style={{ fontSize: 10, color: c.text3 }}>Mejor: 12 días</div>
              </div>
              {/* Progreso */}
              <div style={{
                padding: 16, borderRadius: 14,
                background: c.elevated,
                border: `1px solid ${c.borderSoft}`,
                textAlign: "center",
              }}>
                <div style={{ fontSize: 11, color: c.text3, marginBottom: 10 }}>Progreso semanal</div>
                <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>
                  <V3Ring pct={18} size={70} stroke={6} value="18%"/>
                </div>
                <div style={{ fontSize: 10, color: c.text3 }}>Mejora vs semana anterior</div>
              </div>
            </div>
          </V3Card>
        </div>
      </div>
    </div>
  );
}

// ── Suite · Respiración (DARK) ────────────────────────────────────────────────
function V3SuiteRespiracion({ mode = "dark" }) {
  return (
    <V3Shell defaultMode={mode} sidebar={<V3Sidebar active="respiracion"/>} width={1320} height={860}>
      <V3RespBody mode={mode}/>
    </V3Shell>
  );
}

function V3RespBody({ mode }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", overflow: "auto" }}>
      <V3Header
        title="Respiración Guiada 4-7-8"
        subtitle="Encuentra calma y regula tu sistema nervioso."
        mode={mode}
        actions={
          <>
            <NMPlayButton icon="play" size={40} color="#fff"/>
            <NMPlayButton icon="pause" size={40}/>
            <div style={{
              padding: "10px 14px",
              borderRadius: 14,
              background: c.surface, border: `1px solid ${c.borderSoft}`,
              fontSize: 12, color: c.text, fontWeight: 600,
              display: "flex", alignItems: "center", gap: 6,
            }}>
              Técnica 4-7-8
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M2 4l3 3 3-3" stroke={c.text2} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </>
        }
      />
      <div style={{ padding: "0 28px 28px", display: "grid", gridTemplateColumns: "1fr 280px", gap: 16 }}>
        {/* main col */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Big breathing ring */}
          <V3Card padding={28} glow>
            <div style={{ display: "grid", gridTemplateColumns: "200px 1fr 200px", gap: 28, alignItems: "center" }}>
              <V3Card padding={18} style={{ background: c.elevated }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12 }}>
                  <NMIcon name="leaf" size={16} color={c.teal}/>
                  <div style={{ fontSize: 14, fontWeight: 700, color: c.text }}>Técnica 4-7-8</div>
                </div>
                <div style={{ fontSize: 12, color: c.text2, marginBottom: 4 }}>Inhala 4s</div>
                <div style={{ fontSize: 12, color: c.text2, marginBottom: 4 }}>Mantén 7s</div>
                <div style={{ fontSize: 12, color: c.text2, marginBottom: 14 }}>Exhala 8s</div>
                <V3Button variant="secondary" size="sm" fullWidth icon={<span>📖</span>}>Ver guía</V3Button>
              </V3Card>
              {/* Huge ring */}
              <div style={{ display: "flex", justifyContent: "center", alignItems: "center", position: "relative" }}>
                <div style={{ position: "relative", width: 320, height: 320 }}>
                  <svg width="320" height="320" viewBox="0 0 320 320">
                    <defs>
                      <linearGradient id="breathBig" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%"  stopColor={c.gradFrom}/>
                        <stop offset="50%" stopColor={c.gradMid}/>
                        <stop offset="100%" stopColor={c.gradTo}/>
                      </linearGradient>
                      <filter id="breathGlow">
                        <feGaussianBlur stdDeviation="5"/>
                        <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
                      </filter>
                    </defs>
                    <circle cx="160" cy="160" r="140" fill="none"
                            stroke={isDark ? "rgba(94,234,212,.10)" : "#e8edf5"}
                            strokeWidth="6"/>
                    <circle cx="160" cy="160" r="140" fill="none"
                            stroke="url(#breathBig)" strokeWidth="6"
                            strokeDasharray={`${2 * Math.PI * 140}`}
                            strokeLinecap="round"
                            transform="rotate(-90 160 160)"
                            filter="url(#breathGlow)"/>
                    {/* Dot on top */}
                    <circle cx="160" cy="20" r="12" fill="#fff" stroke={c.gradFrom} strokeWidth="3"/>
                  </svg>
                  <div style={{
                    position: "absolute", inset: 0,
                    display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center",
                  }}>
                    <div style={{ fontSize: 24, color: c.text2, fontWeight: 500, marginBottom: 6 }}>Inhala</div>
                    <div style={{
                      fontSize: 96, fontWeight: 300, color: c.text,
                      lineHeight: 1, letterSpacing: "-.04em",
                    }}>4</div>
                    <div style={{ fontSize: 16, color: c.text3, marginTop: 4 }}>segundos</div>
                  </div>
                </div>
              </div>
              {/* Tip */}
              <V3Card padding={18} style={{ background: c.elevated }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
                  <NMIcon name="sparkle" size={14} color={c.warning}/>
                  <div style={{ fontSize: 13, fontWeight: 700, color: c.text }}>Consejo</div>
                </div>
                <div style={{ fontSize: 11, color: c.text2, lineHeight: 1.55, marginBottom: 8 }}>
                  La práctica constante mejora tu capacidad para manejar el estrés y la ansiedad.
                </div>
                <div style={{ fontSize: 11, color: c.teal, fontWeight: 600, cursor: "pointer" }}>Saber más</div>
              </V3Card>
            </div>
            <div style={{ textAlign: "center", marginTop: 18, fontSize: 12, color: c.text2 }}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}><NMIcon name="heart" size={14} color={c.violet}/> Ritmo actual estable <span style={{ width: 6, height: 6, borderRadius: 999, background: c.success, display: "inline-block", marginLeft: 4 }}/></span>
            </div>
          </V3Card>

          {/* 3 step cards */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
            {[
              { label: "Inhala durante", time: "4", desc: "Respira lenta y profundamente por la nariz.", color: c.teal, icon: "↑" },
              { label: "Mantén durante", time: "7", desc: "Retén el aire y mantén la calma.",            color: c.cyan, icon: "pause" },
              { label: "Exhala durante", time: "8", desc: "Exhala lentamente por la boca y suelta la tensión.", color: c.violet, icon: "↓" },
            ].map((s, i) => (
              <V3Card key={i} padding={20}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr auto", alignItems: "center", marginBottom: 4 }}>
                  <div style={{ fontSize: 13, color: c.text3 }}>{s.label}</div>
                  <div style={{
                    width: 40, height: 40, borderRadius: 999,
                    background: `linear-gradient(135deg, ${s.color}, ${s.color}aa)`,
                    color: "#fff", fontSize: 18, fontWeight: 700,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    boxShadow: `0 4px 12px ${s.color}55`,
                  }}>{s.icon}</div>
                </div>
                <div style={{
                  fontSize: 56, fontWeight: 300,
                  color: c.text, lineHeight: 1, letterSpacing: "-.03em",
                }}>{s.time}</div>
                <div style={{ fontSize: 12, color: c.text3, marginTop: -4 }}>segundos</div>
                <div style={{ fontSize: 12, color: c.text2, marginTop: 14, lineHeight: 1.5 }}>{s.desc}</div>
                <div style={{
                  marginTop: 12, height: 3, borderRadius: 999,
                  background: `linear-gradient(90deg, ${s.color}, ${s.color}33)`,
                  width: i === 0 ? "60%" : i === 1 ? "30%" : "10%",
                }}/>
              </V3Card>
            ))}
          </div>

          {/* History + plant card */}
          <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14 }}>
            <V3Card padding={20}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: c.text }}>Historial de sesiones</div>
                <div style={{ fontSize: 11, color: c.teal, fontWeight: 600, cursor: "pointer" }}>Ver todo</div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
                {[
                  ["Hoy",    "9:15 AM",  "07:12", "Calma", 80],
                  ["Ayer",   "8:30 PM",  "06:28", "Calma", 75],
                  ["14 may", "9:05 AM",  "05:01", "Calma", 68],
                  ["13 may", "7:40 PM",  "04:36", "Calma", 66],
                ].map(([d, h, t2, lbl, ring], i) => (
                  <div key={i} style={{
                    padding: 12, borderRadius: 12,
                    background: c.elevated, border: `1px solid ${c.borderSoft}`,
                  }}>
                    <div style={{ fontSize: 11, color: c.text2, fontWeight: 600 }}>{d}</div>
                    <div style={{ fontSize: 9, color: c.text3, fontFamily: V3_FONT.mono, marginBottom: 8 }}>{h}</div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <div style={{ fontSize: 16, fontFamily: V3_FONT.mono, fontWeight: 700, color: c.text }}>{t2}</div>
                        <div style={{ fontSize: 9, color: c.text3, fontFamily: V3_FONT.mono }}>min</div>
                      </div>
                      <V3Ring pct={ring} size={32} stroke={3}/>
                    </div>
                  </div>
                ))}
              </div>
            </V3Card>
            <V3Card padding={20} glow>
              <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 12, alignItems: "center" }}>
                <div>
                  <div style={{
                    fontSize: 16, fontWeight: 700, color: c.text,
                    marginBottom: 6, letterSpacing: "-.01em",
                  }}>Estás cuidando de ti, y eso importa.</div>
                  <div style={{ fontSize: 12, color: c.text2, lineHeight: 1.5 }}>
                    Cada respiración consciente es un paso hacia tu bienestar.
                  </div>
                </div>
                <div style={{ fontSize: 48 }}><NMIcon name="leaf" size={36} color="currentColor"/></div>
              </div>
            </V3Card>
          </div>
        </div>

        {/* Right rail: sesión stats */}
        <V3Card padding={22}>
          <div style={{ fontSize: 15, fontWeight: 700, color: c.text, marginBottom: 16 }}>Sesión</div>
          <div style={{ marginBottom: 18 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
              <NMIcon name="timer" size={14} color={c.teal}/>
              <span style={{ fontSize: 11, color: c.text2 }}>Tiempo en sesión</span>
            </div>
            <div style={{ fontSize: 32, fontWeight: 700, color: c.text, fontFamily: V3_FONT.mono, letterSpacing: "-.02em" }}>
              05:42 <span style={{ fontSize: 12, color: c.text3, fontFamily: V3_FONT.sans, fontWeight: 500 }}>min</span>
            </div>
          </div>
          <div style={{ height: 1, background: c.borderSoft, margin: "16px 0" }}/>
          <div style={{ marginBottom: 18 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
              <NMIcon name="heart" size={14} color={c.danger}/>
              <span style={{ fontSize: 11, color: c.text2 }}>Ritmo cardíaco</span>
            </div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
              <span style={{ fontSize: 32, fontWeight: 700, color: c.text, fontFamily: V3_FONT.mono, letterSpacing: "-.02em" }}>68</span>
              <span style={{ fontSize: 12, color: c.text3 }}>lpm</span>
              <span style={{
                marginLeft: "auto",
                padding: "3px 8px", borderRadius: 999,
                background: c.successSoft, color: c.success,
                fontSize: 10, fontWeight: 700,
              }}>Estable</span>
            </div>
            <svg viewBox="0 0 200 30" style={{ width: "100%", height: 30, marginTop: 8 }}>
              <path d="M0 15 L 20 12 L 30 18 L 40 8 L 50 22 L 60 14 L 80 15 L 100 10 L 120 18 L 140 13 L 160 17 L 180 12 L 200 15"
                    stroke={c.teal} strokeWidth="1.5" fill="none" strokeLinecap="round"/>
            </svg>
          </div>
          <div style={{ height: 1, background: c.borderSoft, margin: "16px 0" }}/>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
              <NMIcon name="leaf" size={14} color={c.violet}/>
              <span style={{ fontSize: 11, color: c.text2 }}>Calma</span>
            </div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
              <span style={{ fontSize: 32, fontWeight: 700, color: c.text, fontFamily: V3_FONT.mono, letterSpacing: "-.02em" }}>78</span>
              <span style={{ fontSize: 12, color: c.text3 }}>de 100</span>
            </div>
            <div style={{ fontSize: 11, color: c.teal, fontWeight: 600, marginTop: 4 }}>Buen nivel</div>
            <div style={{ height: 6, background: c.elevated, borderRadius: 999, marginTop: 8, overflow: "hidden" }}>
              <div style={{
                width: "78%", height: "100%",
                background: `linear-gradient(90deg, ${c.gradFrom}, ${c.gradTo})`,
                borderRadius: 999,
              }}/>
            </div>
          </div>
        </V3Card>
      </div>
    </div>
  );
}

// ── Suite · Avisos (Recordatorios) ────────────────────────────────────────────
function V3SuiteAvisos({ mode = "light" }) {
  return (
    <V3Shell defaultMode={mode} sidebar={<V3Sidebar active="avisos"/>} width={1320} height={860}>
      <V3AvisosBody mode={mode}/>
    </V3Shell>
  );
}

function V3AvisosBody({ mode }) {
  const { c, isDark } = useV3Theme();
  const [tab, setTab] = React.useState("Todos");
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", overflow: "auto" }}>
      <V3Header
        title="Recordatorios de Bienestar / Avisos"
        subtitle="Pequeñas acciones diarias, grandes cambios."
        streak={12}
        mode={mode}
      />
      <div style={{ padding: "0 28px 28px", display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Stepper */}
        <V3Card padding={20}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {[
              ["1", "Tus recordatorios", "Organiza tus hábitos", "done"],
              ["2", "Frecuencia",        "Elige cuándo ocurren", "active"],
              ["3", "Listo",             "Recibe avisos y progresa", "todo"],
            ].map(([n, t1, t2, st], i) => (
              <React.Fragment key={n}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 999,
                    background: st === "active" || st === "done"
                      ? `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`
                      : c.elevated,
                    color: st === "todo" ? c.text3 : "#fff",
                    fontSize: 14, fontWeight: 700,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    boxShadow: st !== "todo" ? `0 4px 12px -2px ${c.teal}44` : "none",
                  }}>{n}</div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: c.text }}>{t1}</div>
                    <div style={{ fontSize: 11, color: c.text3 }}>{t2}</div>
                  </div>
                </div>
                {i < 2 && (
                  <div style={{
                    flex: 1, height: 3,
                    background: st === "done"
                      ? `linear-gradient(90deg, ${c.gradFrom}, ${c.gradTo})`
                      : c.elevated,
                    borderRadius: 999,
                  }}/>
                )}
              </React.Fragment>
            ))}
          </div>
        </V3Card>

        {/* Search + tabs */}
        <V3Card padding={16}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: 14, alignItems: "center" }}>
            <div style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "10px 14px",
              borderRadius: 12,
              background: c.elevated,
              border: `1px solid ${c.borderSoft}`,
            }}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="6" cy="6" r="4" stroke={c.text3} strokeWidth="1.4"/>
                <path d="M9 9l3 3" stroke={c.text3} strokeWidth="1.4" strokeLinecap="round"/>
              </svg>
              <span style={{ fontSize: 13, color: c.text3 }}>Buscar recordatorios...</span>
            </div>
            <V3Tabs items={["Todos", "Hoy", "Próximos", "Completados"]} active={tab} onChange={setTab}/>
            <div style={{ display: "flex", gap: 6 }}>
              <div style={{
                padding: "6px 12px", borderRadius: 999,
                background: c.elevated, border: `1px solid ${c.borderSoft}`,
                fontSize: 12, color: c.text2, fontWeight: 500,
                display: "flex", alignItems: "center", gap: 4,
              }}>Categoría ▾</div>
              <div style={{ display: "flex", gap: 4, background: c.elevated, borderRadius: 999, padding: 4 }}>
                <div style={{ width: 28, height: 24, borderRadius: 999, background: c.surface, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 3h8M2 6h8M2 9h8" stroke={c.text2} strokeWidth="1.5" strokeLinecap="round"/></svg>
                </div>
                <div style={{ width: 28, height: 24, borderRadius: 999, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <rect x="2" y="2" width="3.5" height="3.5" rx=".5" stroke={c.text3} strokeWidth="1.3" fill="none"/>
                    <rect x="6.5" y="2" width="3.5" height="3.5" rx=".5" stroke={c.text3} strokeWidth="1.3" fill="none"/>
                    <rect x="2" y="6.5" width="3.5" height="3.5" rx=".5" stroke={c.text3} strokeWidth="1.3" fill="none"/>
                    <rect x="6.5" y="6.5" width="3.5" height="3.5" rx=".5" stroke={c.text3} strokeWidth="1.3" fill="none"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </V3Card>

        {/* Grid of reminders */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
          {[
            { icon: "medicine", cat: "Salud",      name: "Tomar medicación",   desc: "No olvides tu medicación diaria.",      time: "08:00 AM", freq: "Todos los días", status: "completed", highlight: true },
            { icon: "water", cat: "Hidratación", name: "Beber agua",         desc: "Mantente hidratado durante el día.",     time: "10:00 AM", freq: "Todos los días", status: "pending" },
            { icon: "run", cat: "Ejercicio",   name: "Haz ejercicio",      desc: "Tu cuerpo y mente lo agradecerán.",     time: "06:00 PM", freq: "Lun, Mié, Vie", status: "pending" },
            { icon: "brain", cat: "Terapia",     name: "Sesión con terapeuta", desc: "Tu espacio para crecer y sanar.",      time: "04:00 PM", freq: "Miércoles, 15 de mayo", status: "scheduled" },
            { icon: "leaf", cat: "Bienestar",   name: "Meditación guiada",  desc: "Encuentra calma en pocos minutos.",      time: "09:00 AM", freq: "Todos los días", status: "pending" },
            { icon: "note", cat: "Reflexión",   name: "Diario de gratitud", desc: "Escribe 3 cosas por las que estás agradecida.", time: "09:30 PM", freq: "Todos los días", status: "pending" },
          ].map((r, i) => {
            const isHigh = r.highlight;
            const statusBadge = {
              completed: { label: "Completado", bg: c.successSoft, fg: c.success, icon: "check" },
              pending:   { label: "Pendiente",  bg: c.warningSoft, fg: c.warning, icon: "clock" },
              scheduled: { label: "Programado", bg: c.violetSoft,  fg: c.violet,  icon: "calendar" },
            }[r.status];
            return (
              <V3Card key={i} padding={20} style={{
                ...(isHigh && {
                  background: isDark
                    ? "linear-gradient(135deg, rgba(20,184,166,.25), rgba(168,85,247,.18))"
                    : `linear-gradient(135deg, ${c.tealSoft}, ${c.violetSoft})`,
                  border: `1.5px solid ${c.teal}`,
                  boxShadow: `0 0 0 4px ${c.teal}15, 0 8px 24px -4px ${c.teal}44`,
                }),
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{
                      width: 44, height: 44, borderRadius: 12,
                      background: isHigh ? c.tealSoft : c.violetSoft,
                      color: isHigh ? c.teal : c.violet,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 20,
                    }}><NMIcon name={r.icon} size={20} color="currentColor"/></div>
                    <div style={{ fontSize: 12, color: c.text3, fontWeight: 600 }}>{r.cat}</div>
                  </div>
                  <span style={{ color: c.text3, fontSize: 14, cursor: "pointer" }}>⋮</span>
                </div>
                <div style={{ fontSize: 17, fontWeight: 700, color: c.text, marginBottom: 4 }}>{r.name}</div>
                <div style={{ fontSize: 12, color: c.text2, marginBottom: 14 }}>{r.desc}</div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 600, color: c.text, marginBottom: 6 }}>
                  <NMIcon name="clock" size={14} color="currentColor"/>{r.time}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: c.text3, marginBottom: 16 }}>
                  <NMIcon name="calendar" size={12} color="currentColor"/>{r.freq}
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{
                    display: "inline-flex", alignItems: "center", gap: 4,
                    padding: "4px 10px", borderRadius: 999,
                    background: statusBadge.bg,
                    color: statusBadge.fg,
                    fontSize: 11, fontWeight: 600,
                  }}><NMIcon name={statusBadge.icon} size={12} color={statusBadge.fg} filled={statusBadge.icon==="check"}/> {statusBadge.label}</span>
                  <V3Button gradient size="sm" icon={<NMIcon name="check" size={14} color="currentColor" filled/>}>Completar</V3Button>
                </div>
              </V3Card>
            );
          })}
        </div>

        {/* Footer progress */}
        <V3Card padding={18}>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 16, alignItems: "center" }}>
            <div style={{
              width: 44, height: 44, borderRadius: 999,
              background: c.tealSoft, color: c.teal,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 22,
            }}><NMIcon name="check" size={22} color="currentColor"/></div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: c.text }}>3 de 6 completados hoy</div>
              <div style={{ fontSize: 11, color: c.text3, marginBottom: 6 }}>¡Vas por un excelente camino!</div>
              <div style={{ height: 6, background: c.elevated, borderRadius: 999, overflow: "hidden" }}>
                <div style={{
                  width: "50%", height: "100%",
                  background: `linear-gradient(90deg, ${c.gradFrom}, ${c.gradTo})`,
                  borderRadius: 999,
                }}/>
              </div>
            </div>
            <V3Button gradient icon={<span>+</span>}>Agregar recordatorio</V3Button>
          </div>
        </V3Card>
      </div>
    </div>
  );
}

// ── Hub · Dashboard (DARK) ────────────────────────────────────────────────────
function V3HubDashboard({ mode = "dark" }) {
  const hubItems = [
    { id: "dashboard",  label: "Dashboard" },
    { id: "pacientes",  label: "Pacientes" },
    { id: "ia",         label: "IA Asistente" },
    { id: "avisos",     label: "Recordatorios" },
    { id: "respiracion",label: "Respiración" },
    { id: "mood",       label: "Mood Tracker" },
    { id: "terapias",   label: "Terapias" },
    { id: "actividades",label: "Actividades" },
    { id: "reportes",   label: "Reportes" },
    { id: "exportar",   label: "Exportar" },
    { id: "config",     label: "Configuración" },
  ];
  return (
    <V3Shell defaultMode={mode} width={1360} height={920}
      sidebar={<V3Sidebar active="dashboard" appName="NeuroMood" role="Hub Pro" items={hubItems}/>}>
      <V3HubBody mode={mode}/>
    </V3Shell>
  );
}

function V3HubBody({ mode }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", overflow: "auto" }}>
      {/* Top: search + theme + notifs + profile (different from suite) */}
      <div style={{
        padding: "18px 28px 16px",
        display: "grid",
        gridTemplateColumns: "320px 1fr auto",
        gap: 16, alignItems: "center",
      }}>
        <div style={{
          padding: "10px 14px",
          borderRadius: 14,
          background: c.surface,
          border: `1px solid ${c.borderSoft}`,
          display: "flex", alignItems: "center", gap: 10,
        }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="6" cy="6" r="4" stroke={c.text3} strokeWidth="1.4"/>
            <path d="M9 9l3 3" stroke={c.text3} strokeWidth="1.4" strokeLinecap="round"/>
          </svg>
          <span style={{ fontSize: 13, color: c.text3, flex: 1 }}>Buscar pacientes...</span>
          <div style={{
            padding: "2px 6px", borderRadius: 4,
            background: c.elevated, fontSize: 10, color: c.text3, fontFamily: V3_FONT.mono,
            border: `1px solid ${c.borderSoft}`,
          }}>Ctrl + K</div>
        </div>
        <div/>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 12, color: c.text2 }}>Tema</span>
          <ThemeToggle mode={mode}/>
          <div style={{
            position: "relative",
            width: 40, height: 40, borderRadius: 14,
            background: c.surface, border: `1px solid ${c.borderSoft}`,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M4.5 7a4.5 4.5 0 0 1 9 0c0 4 1.5 5 1.5 5h-12s1.5-1 1.5-5z" stroke={c.text2} strokeWidth="1.4" fill="none"/>
              <path d="M7 14.5a2 2 0 0 0 4 0" stroke={c.text2} strokeWidth="1.4"/>
            </svg>
            <span style={{
              position: "absolute", top: -4, right: -4,
              width: 18, height: 18, borderRadius: 999,
              background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
              color: "#fff", fontSize: 9, fontWeight: 700,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>3</span>
          </div>
          <div style={{
            padding: "8px 14px 8px 8px",
            borderRadius: 14,
            background: c.surface, border: `1px solid ${c.borderSoft}`,
            display: "flex", alignItems: "center", gap: 10,
          }}>
            <div style={{
              width: 36, height: 36, borderRadius: 999,
              background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
              color: "#fff", fontWeight: 700, fontSize: 13,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>AL</div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: c.text }}>Dr. Andrés López</div>
              <div style={{ fontSize: 10, color: c.text3 }}>Terapeuta</div>
            </div>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M3 4.5L6 7.5L9 4.5" stroke={c.text3} strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </div>
      </div>

      <div style={{ padding: "0 28px 28px", display: "grid", gridTemplateColumns: "1fr 320px", gap: 16 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Featured patient + stats */}
          <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 14 }}>
            <V3Card padding={20} glow>
              <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 16, alignItems: "center" }}>
                <div style={{ position: "relative" }}>
                  <div style={{
                    width: 88, height: 88, borderRadius: 999,
                    background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
                    color: "#fff", fontSize: 26, fontWeight: 700,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    boxShadow: `0 0 0 4px ${isDark ? c.surfaceSolid : c.surface}, 0 8px 24px -4px ${c.teal}66`,
                  }}>AG</div>
                  <span style={{
                    position: "absolute", bottom: 4, right: 4,
                    width: 18, height: 18, borderRadius: 999,
                    background: c.success,
                    border: `3px solid ${isDark ? c.surfaceSolid : c.surface}`,
                  }}/>
                </div>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: c.text, letterSpacing: "-.01em" }}>Ana García Morales</div>
                    <span style={{
                      padding: "3px 10px", borderRadius: 999,
                      background: c.successSoft, color: c.success,
                      fontSize: 10, fontWeight: 700,
                    }}>Activo</span>
                  </div>
                  <div style={{ fontSize: 12, color: c.text3, marginBottom: 8 }}>ID: NM-2024-0158 · 32 años · Femenino</div>
                  <div style={{ display: "flex", gap: 6 }}>
                    {["Ansiedad", "Insomnio", "+1"].map(t => (
                      <span key={t} style={{
                        padding: "4px 10px", borderRadius: 999,
                        background: c.elevated, color: c.text2,
                        fontSize: 11, fontWeight: 500,
                        border: `1px solid ${c.borderSoft}`,
                      }}>{t}</span>
                    ))}
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  <V3Button gradient size="sm" icon={<NMIcon name="user" size={14} color="currentColor" />}>Ir a perfil</V3Button>
                  <V3Button variant="secondary" size="sm" icon={<NMIcon name="calendar" size={14} color="currentColor" />}>Nueva sesión</V3Button>
                </div>
              </div>
            </V3Card>
            <V3Card padding={20}>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
                {[
                  ["Sesiones",  "24", "Completadas", 60],
                  ["Progreso",  "68", "Global · %",  68],
                  ["Racha",     "12", "días",        40],
                  ["Plan",      "8",  "sem activa",  80],
                ].map(([label, val, sub, pct]) => (
                  <div key={label} style={{ textAlign: "center" }}>
                    <div style={{ display: "flex", justifyContent: "center", marginBottom: 6 }}>
                      <V3Ring pct={pct} size={56} stroke={5} value={val}/>
                    </div>
                    <div style={{ fontSize: 11, color: c.text3 }}>{label}</div>
                    <div style={{ fontSize: 10, color: c.text3 }}>{sub}</div>
                  </div>
                ))}
              </div>
            </V3Card>
          </div>

          {/* Resumen del paciente: 3 sub-cards */}
          <V3SectionTitle>Resumen del paciente</V3SectionTitle>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1.4fr", gap: 14 }}>
            <V3Card padding={20}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: c.text }}>Estado emocional</span>
                <span style={{ fontSize: 10, color: c.text3, padding: "2px 8px", borderRadius: 999, background: c.elevated }}>Hoy ▾</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <V3Ring pct={73} size={100} stroke={7} value="73" sub="de 100"/>
                <div>
                  <div style={{ fontSize: 11, color: c.text3 }}>Bienestar general</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: c.teal }}>Bien</div>
                  <div style={{ fontSize: 11, color: c.success, marginTop: 2 }}>+8 vs. ayer</div>
                  <div style={{ fontSize: 10, color: c.text3, marginTop: 6, lineHeight: 1.4, maxWidth: 120 }}>
                    Sigue así, cada pequeño paso cuenta.
                  </div>
                </div>
              </div>
            </V3Card>
            <V3Card padding={20}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: c.text }}>Módulos completados</span>
                <span style={{ fontSize: 10, color: c.text3, padding: "2px 8px", borderRadius: 999, background: c.elevated }}>Esta semana ▾</span>
              </div>
              {[
                [{nm:"leaf",label:"Respiración"}, 4, 7, c.teal],
                [{nm:"brain",label:"Mindfulness"}, 3, 6, c.violet],
                [{nm:"moon",label:"Sueño"},       2, 5, c.cyan],
                [{nm:"sparkle",label:"Cognitivo"},   1, 6, c.warning],
              ].map(([nObj, d, t2, col], i) => (
                <div key={i} style={{ marginBottom: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: 12, color: c.text2, display: "inline-flex", alignItems: "center", gap: 6 }}>
                      <NMIcon name={nObj.nm} size={14} color={col}/>
                      {nObj.label}
                    </span>
                    <span style={{ fontSize: 11, color: c.text, fontWeight: 600 }}>{d} de {t2}</span>
                  </div>
                  <div style={{ height: 5, background: c.elevated, borderRadius: 999, overflow: "hidden" }}>
                    <div style={{
                      width: `${(d/t2)*100}%`, height: "100%",
                      background: `linear-gradient(90deg, ${col}, ${col}aa)`,
                      borderRadius: 999,
                    }}/>
                  </div>
                </div>
              ))}
            </V3Card>
            <V3Card padding={20}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: c.text }}>Evolución del bienestar</span>
                <span style={{ fontSize: 10, color: c.text3, padding: "2px 8px", borderRadius: 999, background: c.elevated }}>7 días ▾</span>
              </div>
              <V3WaveChart
                data={[3, 5, 4, 6, 5, 7, 8]}
                labels={["Lun","Mar","Mié","Jue","Vie","Sáb","Hoy"]}
                height={180}
                glow
              />
            </V3Card>
          </div>

          {/* Actividad reciente + Insights clínicos */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <V3Card padding={20}>
              <V3SectionTitle>Actividad reciente</V3SectionTitle>
              {[
                ["leaf", "Sesión de respiración", "7 min · Coherencia",    "Hoy, 09:15"],
                ["brain", "Mindfulness guiado",    "10 min · Atención plena", "Ayer, 20:30"],
                ["😊", "Registro de estado de ánimo", "Bien · 73/100",    "Ayer, 19:45"],
                ["sparkle", "Ejercicio cognitivo",   "15 min · Reestructuración", "Ayer, 17:10"],
                ["book", "Diario de gratitud",    "3 min · Reflexión",       "14 May, 21:20"],
              ].map(([ic, n, d, time], i) => (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "auto 1fr auto auto",
                  gap: 12, padding: "10px 0",
                  borderBottom: i < 4 ? `1px solid ${c.borderSoft}` : "none",
                  alignItems: "center",
                }}>
                  <div style={{
                    width: 34, height: 34, borderRadius: 10,
                    background: c.elevated,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 14,
                  }}><NMIcon name={ic} size={14} color="currentColor"/></div>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: c.text }}>{n}</div>
                    <div style={{ fontSize: 10, color: c.text3 }}>{d}</div>
                  </div>
                  <div style={{ fontSize: 10, color: c.text3, fontFamily: V3_FONT.mono }}>{time}</div>
                  <div style={{
                    width: 20, height: 20, borderRadius: 999,
                    background: c.success, color: "#fff",
                    fontSize: 11, fontWeight: 700,
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}><NMIcon name="check" size={11} color="#fff" filled/></div>
                </div>
              ))}
              <div style={{ textAlign: "center", marginTop: 10 }}>
                <V3Button variant="secondary" size="sm" fullWidth icon={<NMIcon name="arrowRight" size={14} color="currentColor" filled/>}>Ver todas las actividades</V3Button>
              </div>
            </V3Card>
            <V3Card padding={20}>
              <V3SectionTitle action={<span style={{ fontSize: 10, padding: "3px 8px", borderRadius: 999, background: c.violetSoft, color: c.violet, fontWeight: 700, display: "inline-flex", alignItems: "center", gap: 4 }}><NMIcon name="sparkle" size={10} color={c.violet}/> IA</span>}>
                Insights clínicos
              </V3SectionTitle>
              {[
                ["chart", c.success, "Mejora consistente en los últimos 7 días", "El bienestar general ha aumentado 14 puntos desde la semana pasada."],
                ["brain", c.violet,  "Patrón de ansiedad detectado",            "Los niveles de ansiedad tienden a aumentar los domingos por la noche."],
                ["moon", c.cyan,    "Sueño irregular",                          "Se recomienda reforzar la higiene del sueño y rutinas nocturnas."],
              ].map(([ic, col, n, d], i) => (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "auto 1fr",
                  gap: 12, padding: "10px 0",
                  borderBottom: i < 2 ? `1px solid ${c.borderSoft}` : "none",
                }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: 12,
                    background: col + "22", color: col,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 16,
                  }}><NMIcon name={ic} size={16} color="currentColor"/></div>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: c.text }}>{n}</div>
                    <div style={{ fontSize: 11, color: c.text2, marginTop: 4, lineHeight: 1.45 }}>{d}</div>
                  </div>
                </div>
              ))}
              <div style={{ textAlign: "center", marginTop: 10 }}>
                <V3Button variant="secondary" size="sm" fullWidth icon={<NMIcon name="arrowRight" size={14} color="currentColor" filled/>}>Ver recomendaciones</V3Button>
              </div>
            </V3Card>
          </div>

          {/* Tip terapéutico */}
          <V3Card padding={18} glow>
            <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 14, alignItems: "center" }}>
              <div style={{
                width: 44, height: 44, borderRadius: 12,
                background: c.violetSoft, color: c.violet,
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22,
              }}><NMIcon name="brain" size={22} color="currentColor"/></div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: c.text }}>Tip terapéutico del día</div>
                <div style={{ fontSize: 12, color: c.text2, marginTop: 2 }}>Pequeñas acciones repetidas generan grandes cambios. La constancia es tu mejor aliada.</div>
              </div>
              <V3Button variant="secondary" size="sm" icon={<NMIcon name="sparkle" size={14} color="currentColor" />}>Personalizar tip</V3Button>
            </div>
          </V3Card>
        </div>

        {/* Right rail: IA Asistente chat */}
        <V3Card padding={20} glow style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <NMIcon name="sparkle" size={16} color={c.violet}/>
              <div style={{ fontSize: 14, fontWeight: 700, color: c.text }}>IA Asistente</div>
            </div>
            <span style={{
              padding: "3px 9px", borderRadius: 999,
              background: c.successSoft, color: c.success,
              fontSize: 10, fontWeight: 700,
              display: "flex", alignItems: "center", gap: 4,
            }}>● En línea ▾</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 14 }}>
            <div style={{
              padding: 12, borderRadius: "14px 14px 14px 4px",
              background: c.elevated, fontSize: 12, color: c.text2, lineHeight: 1.5,
            }}>
              Hola, Dr. López<br/>
              ¿En qué puedo ayudarte hoy con Ana o con tus pacientes?
            </div>
            <div style={{
              padding: 12, borderRadius: "14px 14px 4px 14px",
              background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
              color: "#fff", fontSize: 12, lineHeight: 1.5,
              alignSelf: "flex-end", maxWidth: "85%",
            }}>
              ¿Cómo ha sido su progreso esta semana en ansiedad?
              <div style={{ fontSize: 9, color: "rgba(255,255,255,.7)", marginTop: 4, textAlign: "right" }}>10:24</div>
            </div>
            <div style={{
              padding: 12, borderRadius: "14px 14px 14px 4px",
              background: c.elevated, fontSize: 12, color: c.text2, lineHeight: 1.5,
            }}>
              Su ansiedad ha disminuido un <strong style={{ color: c.text }}>18%</strong> esta semana. Ha completado <strong style={{ color: c.text }}>4 ejercicios de respiración</strong> y <strong style={{ color: c.text }}>2 sesiones de mindfulness</strong>.
              <div style={{ fontSize: 9, color: c.text3, marginTop: 4 }}>10:24</div>
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 14 }}>
            {[
              ["barchart", "Resumen semanal de Ana", c.teal],
              ["sparkle", "Sugerir próxima actividad", c.violet],
              ["note", "Generar informe", c.cyan],
              ["warning", "Detectar riesgos", c.danger],
            ].map(([ic, n, col]) => (
              <div key={n} style={{
                display: "grid", gridTemplateColumns: "auto 1fr auto",
                gap: 10, padding: "10px 12px",
                borderRadius: 12,
                background: c.elevated, border: `1px solid ${c.borderSoft}`,
                alignItems: "center", cursor: "pointer",
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: 8,
                  background: col + "22", color: col,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 13,
                }}><NMIcon name={ic} size={14} color="currentColor"/></div>
                <span style={{ fontSize: 12, color: c.text, fontWeight: 500 }}>{n}</span>
                <NMIcon name="chevronRight" size={14} color={c.text3}/>
              </div>
            ))}
          </div>
          <div style={{
            display: "flex", alignItems: "center", gap: 8,
            padding: "8px 12px",
            borderRadius: 14,
            background: c.elevated, border: `1px solid ${c.borderSoft}`,
            marginTop: "auto",
          }}>
            <input
              type="text"
              placeholder="Escribe un mensaje..."
              style={{
                flex: 1, border: "none", outline: "none",
                background: "transparent", color: c.text,
                fontSize: 12, fontFamily: V3_FONT.sans,
              }}
              readOnly
            />
            <div style={{
              width: 34, height: 34, borderRadius: 10,
              background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
              color: "#fff",
              display: "flex", alignItems: "center", justifyContent: "center",
              cursor: "pointer",
              boxShadow: `0 4px 10px -2px ${c.teal}55`,
            }}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 7l10-5-3 12-3-5-4-2z" fill="#fff"/>
              </svg>
            </div>
          </div>
          <div style={{ fontSize: 9, color: c.text3, marginTop: 6, textAlign: "center" }}>
            IA puede cometer errores. Verifica la información.
          </div>
        </V3Card>
      </div>
    </div>
  );
}

Object.assign(window, {
  V3SuiteInicio, V3SuiteAnimo, V3SuiteRespiracion, V3SuiteAvisos, V3HubDashboard,
});
