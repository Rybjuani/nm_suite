/* v3-installers.jsx — Instalador Suite (5 pasos) y Desinstalador Suite (3 pasos)
 * Dark theme por defecto.
 */

// ─── Installer Shell común ────────────────────────────────────────────────────
function V3InstallShell({ title, subtitle = null, steps, active, accent = "gradient",
                          children, footerPrimary, footerSecondary, height = 660, width = 820 }) {
  return (
    <V3Shell defaultMode="dark" width={width} height={height}>
      <V3InstallShellBody title={title} subtitle={subtitle} steps={steps} active={active} accent={accent}
                          footerPrimary={footerPrimary} footerSecondary={footerSecondary}>
        {children}
      </V3InstallShellBody>
    </V3Shell>
  );
}
function V3InstallShellBody({ title, subtitle, steps, active, accent,
                              children, footerPrimary, footerSecondary }) {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{ height: "100%", display: "grid", gridTemplateRows: "auto 1fr auto", overflow: "hidden" }}>
      {/* Header con logo + stepper compacto */}
      <div style={{ padding: "18px 30px 16px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
          <V3Logo size={26}/>
          <div style={{
            padding: "4px 10px", borderRadius: 999,
            background: c.elevated, border: `1px solid ${c.borderSoft}`,
            fontSize: 10, color: c.text3, fontFamily: V3_FONT.mono,
          }}>v1.0.0 · build 2026-05-16</div>
        </div>
        {/* Step pills */}
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {steps.map((s, i, arr) => {
            const done = i < active;
            const cur = i === active;
            const isDanger = accent === "danger";
            return (
              <React.Fragment key={s}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                  <div style={{
                    width: 26, height: 26, borderRadius: 999,
                    background: (done || cur)
                      ? (isDanger
                          ? `linear-gradient(135deg, ${c.danger}, ${c.warning})`
                          : `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`)
                      : c.elevated,
                    color: (done || cur) ? "#fff" : c.text3,
                    fontSize: 11, fontWeight: 700,
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    {done ? <NMIcon name="check" size={11} color="#fff" filled/> : (i + 1)}
                  </div>
                  <span style={{
                    fontSize: 11, fontWeight: cur ? 700 : 500,
                    color: cur ? c.text : (done ? c.text2 : c.text3),
                  }}>{s}</span>
                </div>
                {i < arr.length - 1 && (
                  <div style={{
                    flex: 1, height: 2, minWidth: 12,
                    background: done
                      ? (isDanger
                          ? `linear-gradient(90deg, ${c.danger}, ${c.warning})`
                          : `linear-gradient(90deg, ${c.gradFrom}, ${c.gradTo})`)
                      : c.elevated,
                    borderRadius: 2,
                  }}/>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
      <div style={{ padding: "8px 30px 16px", overflow: "auto" }}>
        {title && (
          <div style={{ marginBottom: 8 }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: c.text, letterSpacing: "-.015em" }}>{title}</div>
            {subtitle && <div style={{ fontSize: 13, color: c.text2, marginTop: 4 }}>{subtitle}</div>}
          </div>
        )}
        {children}
      </div>
      <div style={{
        padding: "14px 30px",
        borderTop: `1px solid ${c.borderSoft}`,
        background: c.bgAlt,
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <div style={{ fontSize: 10, color: c.text4, fontFamily: V3_FONT.mono }}>
          Instalador Suite · NeuroMood Suite v1.0.0
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {footerSecondary}
          {footerPrimary}
        </div>
      </div>
    </div>
  );
}

const V3_INSTALL_STEPS = ["Bienvenida", "Cuenta", "Consentimiento", "Instalación", "Finalizar"];

// ─── Paso 0: Bienvenida ───────────────────────────────────────────────────────
function V3InstBienvenida() {
  return (
    <V3InstallShell steps={V3_INSTALL_STEPS} active={0} height={660}
      footerPrimary={<V3Button gradient icon={<NMIcon name="arrowRight" size={14} color="#fff"/>}>Empezar</V3Button>}>
      <V3InstBienvenidaBody/>
    </V3InstallShell>
  );
}
function V3InstBienvenidaBody() {
  const { c, isDark } = useV3Theme();
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 30, alignItems: "center", padding: "20px 0" }}>
      <div>
        <div style={{
          fontSize: 11, fontWeight: 700, letterSpacing: ".18em",
          color: c.violet, textTransform: "uppercase",
        }}>Bienvenida</div>
        <div style={{ fontSize: 36, fontWeight: 700, color: c.text, letterSpacing: "-.02em", marginTop: 8, lineHeight: 1.1 }}>
          Una herramienta para<br/>
          <span style={{
            background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
            WebkitBackgroundClip: "text",
            color: "transparent",
          }}>acompañarte</span>
        </div>
        <div style={{ fontSize: 14, color: c.text2, lineHeight: 1.6, marginTop: 16, maxWidth: 400 }}>
          <strong style={{ color: c.text }}>NeuroMood Suite</strong> es una herramienta digital complementaria de bienestar emocional.
          En los próximos pasos vas a crear tu cuenta, aceptar el aviso legal y configurar la app.
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 22 }}>
          {[
            ["check",   c.success, "Compatible con Windows 10 y 11"],
            ["target",  c.teal,    "Datos cifrados localmente y sincronización opcional"],
            ["bolt",    c.warning, "Liviano: ~280 MB de espacio en disco"],
          ].map(([ic, col, txt]) => (
            <div key={txt} style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "10px 14px", borderRadius: 12,
              background: c.surface, border: `1px solid ${c.borderSoft}`,
            }}>
              <div style={{
                width: 28, height: 28, borderRadius: 8,
                background: col + "22", display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <NMIcon name={ic} size={14} color={col}/>
              </div>
              <span style={{ fontSize: 12, color: c.text }}>{txt}</span>
            </div>
          ))}
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "center" }}>
        <V3Card padding={32} glow style={{ textAlign: "center", borderRadius: 24 }}>
          <V3Logo size={72}/>
          <div style={{
            fontSize: 11, fontWeight: 700, letterSpacing: ".2em",
            color: c.text3, marginTop: 18,
          }}>SUITE PARA PACIENTES</div>
          <div style={{ fontSize: 10, fontFamily: V3_FONT.mono, color: c.text3, marginTop: 6 }}>
            v1.0.0 · build 2026-05-16
          </div>
        </V3Card>
      </div>
    </div>
  );
}

// ─── Paso 1: Cuenta ───────────────────────────────────────────────────────────
function V3InstCuenta() {
  return (
    <V3InstallShell steps={V3_INSTALL_STEPS} active={1} height={680}
      footerSecondary={<V3Button variant="secondary" icon={<NMIcon name="arrowLeft" size={14}/>}>Volver</V3Button>}
      footerPrimary={<V3Button gradient icon={<NMIcon name="arrowRight" size={14} color="#fff"/>}>Siguiente</V3Button>}>
      <V3InstCuentaBody/>
    </V3InstallShell>
  );
}
function V3InstCuentaBody() {
  const { c, isDark } = useV3Theme();
  return (
    <div>
      <div style={{ fontSize: 22, fontWeight: 700, color: c.text, letterSpacing: "-.015em" }}>Cuenta NeuroMood</div>
      <div style={{ fontSize: 13, color: c.text2, marginTop: 4, marginBottom: 18 }}>
        Iniciá sesión o creá tu cuenta para asociar tu instalación. Es necesario para sincronizar con tu profesional.
      </div>
      <V3Card padding={24}>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <div style={{ fontSize: 11, color: c.text3, fontWeight: 600, marginBottom: 6 }}>EMAIL</div>
            <div style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "12px 14px", borderRadius: 12,
              background: c.elevated, border: `1px solid ${c.border}`,
            }}>
              <NMIcon name="user" size={14} color={c.text3}/>
              <span style={{ flex: 1, fontSize: 13, color: c.text, fontWeight: 500 }}>ana.martinez@email.com</span>
              <span style={{ fontSize: 11, color: c.success, fontWeight: 600, display: "inline-flex", alignItems: "center", gap: 4 }}>
                <NMIcon name="check" size={12} color={c.success}/> verificado
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: c.text3, fontWeight: 600, marginBottom: 6 }}>CONTRASEÑA</div>
            <div style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "12px 14px", borderRadius: 12,
              background: c.elevated, border: `1px solid ${c.border}`,
            }}>
              <NMIcon name="cog" size={14} color={c.text3}/>
              <span style={{ flex: 1, fontSize: 13, color: c.text, fontWeight: 500, letterSpacing: ".2em" }}>••••••••••</span>
              <span style={{ fontSize: 11, color: c.teal, cursor: "pointer", fontWeight: 600 }}>mostrar</span>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 4 }}>
            <V3Button gradient fullWidth icon={<NMIcon name="check" size={14} color="#fff" filled/>}>Iniciar sesión</V3Button>
            <V3Button variant="secondary" fullWidth icon={<NMIcon name="plus" size={14}/>}>Crear cuenta nueva</V3Button>
          </div>
          <div style={{ fontSize: 11, color: c.teal, fontWeight: 600, cursor: "pointer", textAlign: "center", marginTop: 4 }}>
            ¿Olvidaste tu contraseña?
          </div>
        </div>
        <div style={{
          marginTop: 16, padding: 14, borderRadius: 12,
          background: c.successSoft, border: `1px solid ${c.success}33`,
          display: "flex", alignItems: "flex-start", gap: 10,
        }}>
          <div style={{
            width: 22, height: 22, borderRadius: 999,
            background: c.success, color: "#fff",
            display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 1,
          }}>
            <NMIcon name="check" size={12} color="#fff" filled/>
          </div>
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: c.success }}>Sesión iniciada correctamente</div>
            <div style={{ fontSize: 11, color: c.text2, marginTop: 2 }}>El siguiente paso requiere aceptar el aviso legal.</div>
          </div>
        </div>
      </V3Card>
      <div style={{ marginTop: 12, fontSize: 11, color: c.text3, display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ width: 6, height: 6, borderRadius: 999, background: c.success,
                       boxShadow: `0 0 0 4px ${c.success}22` }}/>
        Conectado a Supabase · auth.neuromood.app
      </div>
    </div>
  );
}

// ─── Paso 2: Consentimiento ───────────────────────────────────────────────────
function V3InstConsentimiento() {
  return (
    <V3InstallShell steps={V3_INSTALL_STEPS} active={2} height={780}
      footerSecondary={<V3Button variant="secondary" icon={<NMIcon name="arrowLeft" size={14}/>}>Volver</V3Button>}
      footerPrimary={<V3Button gradient icon={<NMIcon name="arrowRight" size={14} color="#fff"/>}>Continuar</V3Button>}>
      <V3InstConsBody/>
    </V3InstallShell>
  );
}
function V3InstConsBody() {
  const { c, isDark } = useV3Theme();
  const txt = `NeuroMood Suite es una herramienta digital complementaria de bienestar, registro emocional, organización de hábitos y apoyo personal. Su finalidad es facilitar el registro de estados de ánimo, rutinas, pensamientos, actividades, recordatorios y ejercicios de autorregulación.

NeuroMood Suite no realiza diagnósticos médicos, psicológicos ni psiquiátricos; no indica tratamientos; no reemplaza la evaluación, seguimiento, criterio ni intervención de profesionales de la salud habilitados.

NeuroMood Suite puede utilizarse como apoyo complementario dentro de un proceso acompañado por profesionales habilitados.

NeuroMood Suite no es un servicio de emergencias. En caso de crisis emocional intensa, riesgo de autolesión, ideación suicida o emergencia médica, comunicate inmediatamente con un servicio de emergencias o profesional de confianza.

NeuroMood Suite puede tratar datos personales y sensibles. El paciente acepta que NeuroMood Suite pueda almacenarlos localmente y sincronizarlos para revisión profesional desde NeuroMood Hub.

Cuando exista vinculación profesional, los registros podrán usarse en NeuroMood Hub mediante funciones asistidas por IA. La IA no realiza diagnósticos ni decisiones clínicas; todo contenido generado debe ser revisado y validado por el profesional.

Al continuar, el paciente declara haber leído, comprendido y aceptado este aviso legal, el consentimiento de uso, el tratamiento de datos personales y sensibles, y la generación de una constancia auditable de consentimiento.`;
  return (
    <div>
      <div style={{ fontSize: 22, fontWeight: 700, color: c.text, letterSpacing: "-.015em" }}>Aviso legal y consentimiento</div>
      <div style={{ fontSize: 13, color: c.text2, marginTop: 4, marginBottom: 16 }}>
        Obligatorio para asociar tu aceptación a tu cuenta antes de instalar NeuroMood Suite.
      </div>
      <V3Card padding={0}>
        <div style={{
          padding: "14px 18px", borderBottom: `1px solid ${c.borderSoft}`, background: c.bgAlt,
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
            <NMIcon name="report" size={16} color={c.teal}/>
            <span style={{ fontSize: 12, fontWeight: 700, color: c.text }}>Aviso legal · Consentimiento · Tratamiento de datos</span>
          </div>
          <span style={{ fontSize: 10, color: c.text3, fontFamily: V3_FONT.mono }}>v.legal-2026-05-16</span>
        </div>
        <div style={{
          padding: 18, maxHeight: 220, overflow: "auto",
          fontSize: 11.5, color: c.text2, lineHeight: 1.65,
          whiteSpace: "pre-line",
        }}>{txt}</div>
        <div style={{
          padding: "10px 18px", background: c.elevated,
          borderTop: `1px solid ${c.borderSoft}`,
          fontSize: 10, color: c.text3, fontFamily: V3_FONT.mono,
          display: "flex", justifyContent: "space-between",
        }}>
          <span>Hash: 8a4f...e29c</span>
          <span>Privacidad: privacy-2026-05-16</span>
        </div>
      </V3Card>

      <V3Card padding={16} style={{ marginTop: 14 }}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
          <NMCheckBox checked={true} color={c.teal}/>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: c.text, lineHeight: 1.5 }}>
              Leí y acepto el aviso legal, el consentimiento de uso y el tratamiento de datos personales y sensibles
            </div>
            <div style={{ display: "flex", gap: 14, marginTop: 8, fontSize: 11, color: c.text3 }}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                <NMIcon name="check" size={11} color={c.success}/> Constancia local en AppData
              </span>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                <NMIcon name="check" size={11} color={c.success}/> Constancia remota auditable en Supabase
              </span>
            </div>
          </div>
        </div>
      </V3Card>

      <div style={{
        marginTop: 12, padding: "12px 16px", borderRadius: 12,
        background: c.warningSoft, border: `1px solid ${c.warning}33`,
        display: "flex", gap: 10, alignItems: "flex-start",
      }}>
        <NMIcon name="warning" size={18} color={c.warning}/>
        <div style={{ fontSize: 12, color: c.text2, lineHeight: 1.55 }}>
          <strong style={{ color: c.warning }}>NeuroMood Suite no es un servicio de emergencias.</strong> En caso de crisis,
          comunicate con un servicio de emergencias o profesional de confianza inmediatamente.
        </div>
      </div>
    </div>
  );
}

// ─── Paso 3: Instalación ──────────────────────────────────────────────────────
function V3InstInstalacion() {
  return (
    <V3InstallShell steps={V3_INSTALL_STEPS} active={3} height={700}
      footerSecondary={<V3Button variant="secondary" disabled icon={<NMIcon name="arrowLeft" size={14}/>}>Volver</V3Button>}
      footerPrimary={<V3Button gradient disabled icon={<NMIcon name="refresh" size={14} color="#fff"/>}>Instalando…</V3Button>}>
      <V3InstInstBody/>
    </V3InstallShell>
  );
}
function V3InstInstBody() {
  const { c, isDark } = useV3Theme();
  return (
    <div>
      <div style={{ fontSize: 22, fontWeight: 700, color: c.text, letterSpacing: "-.015em" }}>Instalando NeuroMood Suite</div>
      <div style={{ fontSize: 13, color: c.text2, marginTop: 4, marginBottom: 16 }}>
        Configurando tu cuenta, descargando archivos y registrando accesos.
      </div>

      <div style={{ fontSize: 11, color: c.text3, fontWeight: 600, marginBottom: 6 }}>CARPETA DE INSTALACIÓN</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 10 }}>
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "12px 14px", borderRadius: 12,
          background: c.elevated, border: `1px solid ${c.border}`,
        }}>
          <NMIcon name="save" size={14} color={c.text3}/>
          <span style={{ fontSize: 12, color: c.text, fontFamily: V3_FONT.mono }}>C:\Users\Ana\NeuroMood</span>
        </div>
        <V3Button variant="secondary">Examinar</V3Button>
      </div>

      <V3Card padding={20} style={{ marginTop: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
          <span style={{ fontSize: 12, color: c.text2, fontWeight: 600 }}>Progreso</span>
          <span style={{ fontSize: 12, color: c.text, fontWeight: 700, fontFamily: V3_FONT.mono }}>72 %</span>
        </div>
        <div style={{ height: 8, background: c.elevated, borderRadius: 999, overflow: "hidden" }}>
          <div style={{
            width: "72%", height: "100%",
            background: `linear-gradient(90deg, ${c.gradFrom}, ${c.gradTo})`,
            borderRadius: 999,
            boxShadow: `0 0 12px ${c.teal}88`,
          }}/>
        </div>
        <div style={{ fontSize: 12, color: c.text2, marginTop: 10, display: "inline-flex", alignItems: "center", gap: 6 }}>
          <NMIcon name="refresh" size={12} color={c.warning}/>
          Registrando accesos directos…
        </div>
      </V3Card>

      <V3Card padding={0} style={{ marginTop: 14, overflow: "hidden" }}>
        <div style={{
          padding: "10px 16px",
          background: isDark ? "rgba(0,0,0,.4)" : c.elevated,
          borderBottom: `1px solid ${c.borderSoft}`,
          fontFamily: V3_FONT.mono, fontSize: 10, color: c.text3,
          letterSpacing: ".08em",
          display: "flex", justifyContent: "space-between",
        }}>
          <span>INSTALL LOG · NeuroMood Suite</span>
          <span>7 / 8 pasos</span>
        </div>
        <div style={{
          background: isDark ? "rgba(0,0,0,.3)" : c.elevated,
          padding: 16, fontFamily: V3_FONT.mono, fontSize: 11, lineHeight: 1.9,
          maxHeight: 200, overflow: "auto", color: c.text2,
        }}>
          {[
            ["check",   c.success, "Carpeta de instalación creada",     "C:\\Users\\Ana\\NeuroMood"],
            ["check",   c.success, "NeuroMood Suite copiado",            null],
            ["check",   c.success, "Identidad guardada",                 "patient_id=AM-7842"],
            ["check",   c.success, "Configuración de red copiada",       null],
            ["check",   c.success, "Paciente registrado en la nube",     null],
            ["check",   c.success, "Desinstalador Suite copiado",        null],
            ["refresh", c.warning, "Registrando accesos directos…",      null],
            ["target",  c.text3,   "Crear acceso al menú inicio",        "pendiente"],
          ].map(([ic, col, msg, det], i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <NMIcon name={ic} size={11} color={col}/>
              <span style={{ flex: 1 }}>{msg}</span>
              {det && <span style={{ color: c.text3 }}>{det}</span>}
            </div>
          ))}
        </div>
      </V3Card>
    </div>
  );
}

// ─── Paso 4: Finalizar ────────────────────────────────────────────────────────
function V3InstFinalizar() {
  return (
    <V3InstallShell steps={V3_INSTALL_STEPS} active={4} height={660}
      footerPrimary={<V3Button gradient icon={<NMIcon name="arrowRight" size={14} color="#fff"/>}>Finalizar y abrir NeuroMood</V3Button>}>
      <V3InstFinBody/>
    </V3InstallShell>
  );
}
function V3InstFinBody() {
  const { c, isDark } = useV3Theme();
  return (
    <div>
      <div style={{ textAlign: "center", padding: "12px 40px 0" }}>
        <div style={{ display: "inline-flex", position: "relative" }}>
          <div style={{
            width: 88, height: 88, borderRadius: 999,
            background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: `0 0 0 12px ${c.teal}15, 0 16px 32px -8px ${c.teal}55`,
          }}>
            <NMIcon name="check" size={40} color="#fff" filled/>
          </div>
        </div>
        <div style={{ fontSize: 11, fontWeight: 700, color: c.success, letterSpacing: ".2em", marginTop: 18 }}>LISTO</div>
        <div style={{ fontSize: 28, fontWeight: 700, color: c.text, letterSpacing: "-.02em", marginTop: 4 }}>Instalación completada</div>
        <div style={{ fontSize: 14, color: c.text2, lineHeight: 1.6, marginTop: 10, maxWidth: 460, margin: "10px auto 0" }}>
          NeuroMood Suite quedó instalado en tu equipo. Tu cuenta y consentimiento legal están registrados.
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 28 }}>
        {[
          ["save",   "Carpeta",         "C:\\Users\\Ana\\NeuroMood",       true],
          ["user",   "Cuenta",          "ana.martinez@email.com",          false],
          ["bookmark","Versión",        "NeuroMood Suite 1.0.0",           true],
          ["check",  "Consentimiento",  "Registrado · v.legal-2026-05-16", false],
        ].map(([ic, k, v, mono]) => (
          <V3Card key={k} padding={14}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: c.tealSoft, color: c.teal,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <NMIcon name={ic} size={16} color={c.teal}/>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: c.text3, letterSpacing: ".12em", textTransform: "uppercase" }}>{k}</div>
                <div style={{
                  fontSize: 12, color: c.text, marginTop: 2,
                  fontFamily: mono ? V3_FONT.mono : V3_FONT.sans,
                  fontWeight: 500,
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                }}>{v}</div>
              </div>
            </div>
          </V3Card>
        ))}
      </div>

      <div style={{
        marginTop: 16, padding: "12px 16px", borderRadius: 12,
        background: c.elevated, border: `1px solid ${c.borderSoft}`,
        display: "flex", alignItems: "flex-start", gap: 10,
      }}>
        <NMIcon name="info" size={16} color={c.cyan}/>
        <div style={{ fontSize: 12, color: c.text2, lineHeight: 1.55 }}>
          Se creó un acceso directo en el escritorio. Podés desinstalar la app desde "Agregar o quitar programas" o
          ejecutando <code style={{ fontFamily: V3_FONT.mono, color: c.text, padding: "1px 6px", background: c.surface, borderRadius: 4 }}>Desinstalador Suite</code>.
        </div>
      </div>
    </div>
  );
}

// ─── Desinstalador Suite ──────────────────────────────────────────────────────
const V3_UNINSTALL_STEPS = ["Confirmar", "Eliminando", "Finalizado"];

function V3UninstConfirmar() {
  return (
    <V3InstallShell steps={V3_UNINSTALL_STEPS} active={0} accent="danger" height={620} width={760}
      footerSecondary={<V3Button variant="ghost">Cancelar</V3Button>}
      footerPrimary={
        <button style={{
          padding: "10px 22px", borderRadius: 999,
          background: "linear-gradient(135deg, #ef4444, #f59e0b)",
          color: "#fff", border: "none",
          fontSize: 13, fontWeight: 700, cursor: "pointer",
          fontFamily: V3_FONT.sans,
          display: "inline-flex", alignItems: "center", gap: 8,
          boxShadow: "0 6px 16px -4px rgba(239,68,68,.5)",
        }}>
          <NMIcon name="close" size={14} color="#fff"/>
          Desinstalar
        </button>
      }>
      <V3UninstConfBody/>
    </V3InstallShell>
  );
}
function V3UninstConfBody() {
  const { c, isDark } = useV3Theme();
  return (
    <div>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 16, marginBottom: 18 }}>
        <div style={{
          width: 52, height: 52, borderRadius: 14,
          background: c.dangerSoft, color: c.danger,
          display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
        }}>
          <NMIcon name="warning" size={24} color={c.danger}/>
        </div>
        <div>
          <div style={{
            fontSize: 11, fontWeight: 700, letterSpacing: ".15em",
            color: c.danger, textTransform: "uppercase",
          }}>Desinstalación</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: c.text, letterSpacing: "-.015em", marginTop: 4 }}>
            ¿Desinstalar NeuroMood Suite?
          </div>
          <div style={{ fontSize: 13, color: c.text2, lineHeight: 1.55, marginTop: 6 }}>
            Se eliminarán los archivos de instalación de tu computadora.
          </div>
        </div>
      </div>

      <V3Card padding={16} style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: c.text3, letterSpacing: ".12em", textTransform: "uppercase" }}>
          Carpeta a eliminar
        </div>
        <div style={{ fontSize: 13, color: c.text, fontFamily: V3_FONT.mono, marginTop: 4 }}>C:\Users\Ana\NeuroMood</div>
      </V3Card>

      <V3Card padding={18}>
        <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 14, alignItems: "center" }}>
          <div style={{
            width: 44, height: 44, borderRadius: 12,
            background: c.tealSoft, color: c.teal,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <NMIcon name="save" size={20} color={c.teal}/>
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: c.text }}>Conservar mis datos</div>
            <div style={{ fontSize: 11, color: c.text3, marginTop: 2 }}>Registros, historial y configuración local de la app</div>
          </div>
          <NMToggle checked/>
        </div>
      </V3Card>

      <div style={{
        marginTop: 14, padding: "12px 16px", borderRadius: 12,
        background: c.elevated, border: `1px solid ${c.borderSoft}`,
        fontSize: 12, color: c.text2, lineHeight: 1.55,
        display: "flex", gap: 10,
      }}>
        <NMIcon name="info" size={16} color={c.cyan}/>
        <span>Al continuar se cerrarán todas las ventanas de NeuroMood Suite abiertas. Los accesos directos del escritorio
        y del menú inicio también serán eliminados.</span>
      </div>
    </div>
  );
}

function V3UninstEliminando() {
  return (
    <V3InstallShell steps={V3_UNINSTALL_STEPS} active={1} accent="danger" height={620} width={760}
      footerPrimary={
        <button disabled style={{
          padding: "10px 22px", borderRadius: 999,
          background: "linear-gradient(135deg, #ef4444, #f59e0b)",
          color: "#fff", border: "none",
          fontSize: 13, fontWeight: 700,
          fontFamily: V3_FONT.sans, opacity: .6,
          display: "inline-flex", alignItems: "center", gap: 8,
        }}><NMIcon name="refresh" size={14} color="#fff"/> Desinstalando…</button>
      }>
      <V3UninstElimBody/>
    </V3InstallShell>
  );
}
function V3UninstElimBody() {
  const { c, isDark } = useV3Theme();
  return (
    <div>
      <div style={{ fontSize: 22, fontWeight: 700, color: c.text, letterSpacing: "-.015em" }}>Desinstalando NeuroMood Suite</div>
      <div style={{ fontSize: 13, color: c.text2, marginTop: 4, marginBottom: 18 }}>
        Cerrando procesos, limpiando registro y eliminando archivos.
      </div>

      <V3Card padding={20}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
          <span style={{ fontSize: 12, color: c.text2, fontWeight: 600 }}>Progreso</span>
          <span style={{ fontSize: 12, color: c.danger, fontWeight: 700, fontFamily: V3_FONT.mono }}>72 %</span>
        </div>
        <div style={{ height: 8, background: c.elevated, borderRadius: 999, overflow: "hidden" }}>
          <div style={{
            width: "72%", height: "100%",
            background: `linear-gradient(90deg, ${c.danger}, ${c.warning})`,
            borderRadius: 999,
            boxShadow: `0 0 12px ${c.danger}88`,
          }}/>
        </div>
      </V3Card>

      <V3Card padding={0} style={{ marginTop: 14, overflow: "hidden" }}>
        <div style={{
          background: isDark ? "rgba(0,0,0,.3)" : c.elevated,
          padding: 16, fontFamily: V3_FONT.mono, fontSize: 11.5, lineHeight: 1.9,
          color: c.text2,
        }}>
          {[
            ["check",   c.success, "Cerrando aplicaciones..."],
            ["check",   c.success, "Eliminando accesos directos..."],
            ["check",   c.success, "Limpiando registro de Windows..."],
            ["check",   c.success, "Cerrando Explorer en la carpeta..."],
            ["refresh", c.warning, "Eliminando archivos de instalación..."],
            ["target",  c.text3,   "Conservando datos de usuario en AppData"],
          ].map(([ic, col, line], i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <NMIcon name={ic} size={11} color={col}/>
              <span>{line}</span>
            </div>
          ))}
        </div>
      </V3Card>
    </div>
  );
}

function V3UninstFinalizado() {
  return (
    <V3InstallShell steps={V3_UNINSTALL_STEPS} active={2} accent="danger" height={620} width={760}
      footerPrimary={<V3Button gradient icon={<NMIcon name="close" size={14} color="#fff"/>}>Cerrar</V3Button>}>
      <V3UninstFinBody/>
    </V3InstallShell>
  );
}
function V3UninstFinBody() {
  const { c } = useV3Theme();
  return (
    <div>
      <div style={{ textAlign: "center", padding: "8px 40px 0" }}>
        <div style={{ display: "inline-flex" }}>
          <div style={{
            width: 80, height: 80, borderRadius: 999,
            background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: `0 0 0 12px ${c.teal}15, 0 14px 28px -8px ${c.teal}55`,
          }}>
            <NMIcon name="check" size={36} color="#fff" filled/>
          </div>
        </div>
        <div style={{ fontSize: 11, fontWeight: 700, color: c.success, letterSpacing: ".2em", marginTop: 16 }}>LISTO</div>
        <div style={{ fontSize: 26, fontWeight: 700, color: c.text, letterSpacing: "-.02em", marginTop: 4 }}>Desinstalación completada</div>
        <div style={{ fontSize: 14, color: c.text2, lineHeight: 1.6, marginTop: 10, maxWidth: 440, margin: "10px auto 0" }}>
          NeuroMood Suite fue eliminado de este equipo. Tus datos personales se conservaron según la opción seleccionada.
        </div>
      </div>

      <V3Card padding={18} style={{ marginTop: 20 }}>
        <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 14, alignItems: "center" }}>
          <div style={{
            width: 44, height: 44, borderRadius: 12,
            background: c.tealSoft, color: c.teal,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <NMIcon name="save" size={20} color={c.teal}/>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: c.text }}>Datos conservados</div>
            <div style={{ fontSize: 11, color: c.text3, fontFamily: V3_FONT.mono }}>AppData\NeuroMood\nm_data.db · 2.4 MB</div>
          </div>
          <span style={{
            padding: "4px 12px", borderRadius: 999,
            background: c.successSoft, color: c.success,
            fontSize: 11, fontWeight: 700,
          }}>preservado</span>
        </div>
      </V3Card>

      <div style={{ marginTop: 12, fontSize: 11, color: c.text3, textAlign: "center" }}>
        Si en el futuro reinstalás NeuroMood Suite, podrás recuperar tu historial desde estos datos.
      </div>
    </div>
  );
}

Object.assign(window, {
  V3InstallShell, V3_INSTALL_STEPS, V3_UNINSTALL_STEPS,
  V3InstBienvenida, V3InstCuenta, V3InstConsentimiento, V3InstInstalacion, V3InstFinalizar,
  V3UninstConfirmar, V3UninstEliminando, V3UninstFinalizado,
});
