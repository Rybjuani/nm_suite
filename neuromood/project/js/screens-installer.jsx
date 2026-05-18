/* screens-installer.jsx — Instalador Suite + Desinstalador Suite + Design System + Auditoría
 */

// ── Shell común Installer (titlebar + stepper + body + footer) ───────────────
function InstallerShell({ title = "Instalador Suite", steps, active, accent = "accent",
                          children, footerPrimary, footerSecondary, height = 600 }) {
  const t = useTheme();
  return (
    <AppWindow title={title} subtitle={steps[active]} width={760} height={height}>
      <div style={{ height: "100%", display: "grid", gridTemplateRows: "auto 1fr auto" }}>
        <div style={{
          padding: "18px 28px 12px",
          background: t.c.bgAlt,
          borderBottom: `1px solid ${t.c.borderSoft}`,
        }}>
          <NMStepper steps={steps} active={active} tone={accent}/>
        </div>
        <div style={{ padding: "26px 32px 20px", overflow: "auto" }}>
          {children}
        </div>
        <div style={{
          padding: "14px 28px",
          background: t.c.surface,
          borderTop: `1px solid ${t.c.borderSoft}`,
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <div style={{ fontSize: 10, color: t.c.text4, fontFamily: FONT.mono }}>
            Instalador Suite v1.0.0 · NeuroMood Suite v1.0.0
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            {footerSecondary}
            {footerPrimary}
          </div>
        </div>
      </div>
    </AppWindow>
  );
}

const INSTALL_STEPS = ["Bienvenida", "Cuenta", "Consentimiento", "Instalación", "Finalizar"];

// ── Installer Step 0: Bienvenida ─────────────────────────────────────────────
function InstallerBienvenida() {
  const t = useTheme();
  return (
    <InstallerShell steps={INSTALL_STEPS} active={0}
      footerPrimary={<NMButton variant="primary" size="lg">Siguiente →</NMButton>}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
        <div style={{ fontSize: 12, color: t.c.text3, letterSpacing: ".02em" }}>Bienvenido a</div>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 4 }}>
          <NMLogo size={42}/>
          <div style={{
            fontSize: 11, fontWeight: 700, letterSpacing: ".15em",
            color: t.c.accent, padding: "3px 8px",
            background: t.c.accentSoft, borderRadius: 6,
          }}>SUITE PARA PACIENTES</div>
        </div>
        <div style={{ width: 60, height: 3, background: t.c.accent, borderRadius: 3, marginTop: 18 }}/>
        <div style={{ fontSize: 14, color: t.c.text2, lineHeight: 1.65, marginTop: 22, maxWidth: 520 }}>
          Este instalador configurará en tu computadora <strong style={{ color: t.c.text }}>NeuroMood Suite</strong>, una herramienta digital complementaria diseñada para acompañar tu bienestar emocional.
        </div>
        <div style={{ fontSize: 13, color: t.c.text3, lineHeight: 1.65, marginTop: 12, maxWidth: 520 }}>
          En los siguientes pasos vas a crear tu cuenta, aceptar el aviso legal y elegir dónde instalar la aplicación.
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginTop: 28, width: "100%" }}>
          {[
            { i: "🔒", t: "Tus datos en tu equipo", d: "Almacenamiento local cifrado con sync opcional" },
            { i: "👤", t: "Cuenta personal", d: "Email + contraseña vía Supabase Auth" },
            { i: "📋", t: "Consentimiento auditable", d: "Constancia legal local y remota con hash" },
          ].map((x, i) => (
            <NMCard key={i} padding={14}>
              <div style={{ fontSize: 20, marginBottom: 6 }}>{x.i}</div>
              <div style={{ fontSize: 12, fontWeight: 600, color: t.c.text }}>{x.t}</div>
              <div style={{ fontSize: 11, color: t.c.text3, marginTop: 4, lineHeight: 1.45 }}>{x.d}</div>
            </NMCard>
          ))}
        </div>

        <NMCard padding={12} style={{ marginTop: 22, width: "100%", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 24, height: 24, borderRadius: 999,
            background: t.c.successSoft, color: t.c.success,
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12,
          }}>✓</div>
          <div style={{ fontSize: 12, color: t.c.text2 }}>Compatible con Windows 10 y Windows 11 · Requiere ~ 280 MB libres</div>
        </NMCard>
      </div>
    </InstallerShell>
  );
}

// ── Installer Step 1: Cuenta ─────────────────────────────────────────────────
function InstallerCuenta() {
  const t = useTheme();
  return (
    <InstallerShell steps={INSTALL_STEPS} active={1}
      footerSecondary={<NMButton variant="secondary">← Volver</NMButton>}
      footerPrimary={<NMButton variant="primary" size="lg">Siguiente →</NMButton>}>
      <div style={{ marginBottom: 10 }}>
        <SectionTitle eyebrow="Paso 2" size="lg">Cuenta NeuroMood</SectionTitle>
      </div>
      <div style={{ fontSize: 13, color: t.c.text3, marginBottom: 18 }}>
        Iniciá sesión o creá tu cuenta para asociar tu instalación. Es necesario para sincronizar con tu profesional.
      </div>

      <NMCard padding={22}>
        <div style={{ marginBottom: 6, fontSize: 12, fontWeight: 600, color: t.c.text2 }}>Email</div>
        <NMInput placeholder="tu@email.com" value="ana.martinez@email.com" icon={<span style={{ fontSize: 11 }}>📧</span>}/>
        <div style={{ marginTop: 14, marginBottom: 6, fontSize: 12, fontWeight: 600, color: t.c.text2 }}>Contraseña</div>
        <NMInput type="password" placeholder="Mínimo 6 caracteres" value="••••••••••" icon={<span style={{ fontSize: 11 }}>🔒</span>} suffix={<span style={{ fontSize: 10, color: t.c.accent, cursor: "pointer" }}>mostrar</span>}/>

        <div style={{ display: "flex", gap: 10, marginTop: 18 }}>
          <NMButton variant="primary" fullWidth>Iniciar sesión</NMButton>
          <NMButton variant="secondary" fullWidth>Crear cuenta nueva</NMButton>
        </div>
        <div style={{ marginTop: 12, fontSize: 11, color: t.c.accent, cursor: "pointer" }}>¿Olvidaste tu contraseña?</div>

        <div style={{
          marginTop: 18, padding: 12, borderRadius: 10,
          background: t.c.successSoft, border: `1px solid ${t.c.success}22`,
          display: "flex", gap: 10, alignItems: "flex-start",
        }}>
          <div style={{
            width: 20, height: 20, borderRadius: 999,
            background: t.c.success, color: "#fff",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 11, fontWeight: 700, flexShrink: 0, marginTop: 1,
          }}>✓</div>
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, color: t.c.success }}>Sesión iniciada correctamente</div>
            <div style={{ fontSize: 11, color: t.c.text2, marginTop: 2 }}>El siguiente paso requiere aceptar el aviso legal.</div>
          </div>
        </div>
      </NMCard>

      <div style={{ marginTop: 14, fontSize: 11, color: t.c.text3, display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ width: 6, height: 6, borderRadius: 999, background: t.c.success }}/>
        Conectado a Supabase · auth.neuromood.app
      </div>
    </InstallerShell>
  );
}

// ── Installer Step 2: Consentimiento ─────────────────────────────────────────
function InstallerConsentimiento() {
  const t = useTheme();
  const disclaimerExcerpt = `NeuroMood Suite es una herramienta digital complementaria de bienestar, registro emocional, organización de hábitos y apoyo personal. Su finalidad es facilitar el registro de estados de ánimo, rutinas, pensamientos, actividades, recordatorios y ejercicios de autorregulación.

NeuroMood Suite no realiza diagnósticos médicos, psicológicos ni psiquiátricos; no indica tratamientos; no reemplaza la evaluación, seguimiento, criterio ni intervención de profesionales de la salud habilitados; y no debe utilizarse como único medio para tomar decisiones sobre la salud física o mental.

NeuroMood Suite puede utilizarse como apoyo complementario dentro de un proceso acompañado por profesionales habilitados.

NeuroMood Suite no es un servicio de emergencias. En caso de crisis emocional intensa, riesgo de autolesión, ideación suicida o emergencia médica, comunicate inmediatamente con un servicio de emergencias o un profesional de confianza.

NeuroMood Suite puede tratar datos personales y sensibles. El paciente acepta que NeuroMood Suite pueda almacenarlos localmente y sincronizarlos para revisión profesional desde NeuroMood Hub.

Cuando exista vinculación profesional, los registros podrán usarse en NeuroMood Hub mediante funciones asistidas por IA. La IA no realiza diagnósticos ni decisiones clínicas; todo contenido generado debe ser revisado y validado por el profesional.

Al continuar, el paciente declara haber leído, comprendido y aceptado este aviso legal, el consentimiento de uso, el tratamiento de datos personales y sensibles, y la generación de una constancia auditable de consentimiento.`;

  return (
    <InstallerShell steps={INSTALL_STEPS} active={2} height={680}
      footerSecondary={<NMButton variant="secondary">← Volver</NMButton>}
      footerPrimary={<NMButton variant="primary" size="lg">Continuar</NMButton>}>
      <SectionTitle eyebrow="Paso 3" size="lg">Aviso legal y consentimiento</SectionTitle>
      <div style={{ fontSize: 13, color: t.c.text3, marginTop: 4, marginBottom: 16 }}>
        Obligatorio para asociar tu aceptación a tu cuenta antes de instalar NeuroMood Suite.
      </div>

      <NMCard padding={0} style={{ overflow: "hidden" }}>
        <div style={{
          padding: "14px 18px",
          borderBottom: `1px solid ${t.c.borderSoft}`,
          background: t.c.bgAlt,
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: t.c.text }}>
            Aviso legal · Consentimiento de uso · Tratamiento de datos
          </div>
          <div style={{ fontSize: 10, color: t.c.text3, fontFamily: FONT.mono }}>
            v.legal-2026-05-16
          </div>
        </div>
        <div style={{
          padding: 18, maxHeight: 240, overflow: "auto",
          fontSize: 11, color: t.c.text2, lineHeight: 1.6,
          whiteSpace: "pre-line",
        }}>
          {disclaimerExcerpt}
        </div>
        <div style={{
          padding: "10px 18px", background: t.c.elevated,
          borderTop: `1px solid ${t.c.borderSoft}`,
          fontSize: 10, color: t.c.text3, fontFamily: FONT.mono,
        }}>
          Hash: 8a4f...e29c · Privacidad: privacy-2026-05-16
        </div>
      </NMCard>

      <NMCard padding={16} style={{ marginTop: 14 }}>
        <NMCheck checked={true} label={<span style={{ color: t.c.text, fontWeight: 500 }}>Leí y acepto el aviso legal, el consentimiento de uso y el tratamiento de datos personales y sensibles</span>}/>
        <div style={{ display: "flex", gap: 10, marginTop: 12, fontSize: 11, color: t.c.text3, paddingLeft: 28 }}>
          <span>• Constancia local en AppData/NeuroMood</span>
          <span>•</span>
          <span>• Constancia remota auditable en Supabase</span>
        </div>
      </NMCard>

      <div style={{
        marginTop: 12, padding: "10px 14px",
        background: t.c.warningSoft, borderRadius: 10,
        border: `1px solid ${t.c.warning}22`,
        fontSize: 11, color: t.c.text2, lineHeight: 1.5,
        display: "flex", gap: 8,
      }}>
        <span style={{ color: t.c.warning }}>⚠</span>
        <div>
          <strong style={{ color: t.c.warning }}>NeuroMood Suite no es un servicio de emergencias.</strong> En caso de crisis, comunicate con un servicio de emergencias o profesional de confianza inmediatamente.
        </div>
      </div>
    </InstallerShell>
  );
}

// ── Installer Step 3: Instalación ────────────────────────────────────────────
function InstallerInstalacion() {
  const t = useTheme();
  const lines = [
    ["Carpeta creada", "C:\\Users\\Ana\\NeuroMood", "success"],
    ["NeuroMood Suite copiado", null, "success"],
    ["Identidad guardada", "patient_id=AM-7842", "success"],
    ["Configuración de red copiada", null, "success"],
    ["Paciente registrado en la nube", null, "success"],
    ["Desinstalador Suite copiado", null, "success"],
    ["Registrando accesos directos…", null, "syncing"],
  ];
  return (
    <InstallerShell steps={INSTALL_STEPS} active={3} height={640}
      footerSecondary={<NMButton variant="secondary" disabled>← Volver</NMButton>}
      footerPrimary={<NMButton variant="primary" size="lg" disabled>Instalando...</NMButton>}>
      <SectionTitle eyebrow="Paso 4" size="lg">Instalando NeuroMood Suite</SectionTitle>

      <div style={{ marginTop: 16, marginBottom: 6, fontSize: 12, color: t.c.text2 }}>Carpeta de instalación</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8 }}>
        <NMInput value="C:\\Users\\Ana\\NeuroMood" icon={<span style={{ fontSize: 11 }}>📁</span>}/>
        <NMButton variant="secondary">Examinar</NMButton>
      </div>

      <NMCard padding={20} style={{ marginTop: 18 }}>
        <NMProgress value={72} tone="accent" height={8} label="Progreso de instalación"/>
        <div style={{ fontSize: 12, color: t.c.text2, marginTop: 8 }}>Registrando accesos directos…</div>
      </NMCard>

      <NMCard padding={0} style={{ marginTop: 14, overflow: "hidden" }}>
        <div style={{
          padding: "10px 16px",
          background: "#0a0e1a",
          borderBottom: `1px solid ${t.c.borderSoft}`,
          fontFamily: FONT.mono, fontSize: 10, color: "#7d8aa3",
          letterSpacing: ".08em",
        }}>
          INSTALL LOG · NeuroMood Suite
        </div>
        <div style={{ background: "#0a0e1a", padding: 16, fontFamily: FONT.mono, fontSize: 11, lineHeight: 1.8, maxHeight: 200, overflow: "auto" }}>
          {lines.map(([msg, det, st], i) => (
            <div key={i} style={{ color: "#cbd3e1", display: "flex", gap: 10 }}>
              <span style={{
                color: st === "success" ? "#4ade80" : st === "syncing" ? "#fbbf24" : "#7d8aa3",
                width: 14,
              }}>{st === "success" ? "✓" : st === "syncing" ? "↻" : "·"}</span>
              <span style={{ flex: 1 }}>{msg}</span>
              {det && <span style={{ color: "#7d8aa3" }}>{det}</span>}
            </div>
          ))}
        </div>
      </NMCard>
    </InstallerShell>
  );
}

// ── Installer Step 4: Finalizar ──────────────────────────────────────────────
function InstallerFinalizar() {
  const t = useTheme();
  return (
    <InstallerShell steps={INSTALL_STEPS} active={4}
      footerPrimary={<NMButton variant="primary" size="lg">Finalizar y abrir NeuroMood</NMButton>}>
      <div style={{ textAlign: "center", padding: "20px 40px 0" }}>
        <div style={{
          width: 80, height: 80, borderRadius: 999,
          background: t.c.successSoft, color: t.c.success,
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          fontSize: 36, marginBottom: 18,
          boxShadow: `0 0 0 10px ${t.c.success}11`,
        }}>✓</div>
        <SectionTitle eyebrow="Listo" size="xl">Instalación completada</SectionTitle>
        <div style={{ fontSize: 14, color: t.c.text2, lineHeight: 1.6, marginTop: 10, maxWidth: 460, margin: "10px auto 0" }}>
          NeuroMood Suite quedó instalado en tu equipo. Tu cuenta y el consentimiento legal están registrados.
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 26 }}>
        <NMCard padding={14}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: ".12em", color: t.c.text3, textTransform: "uppercase" }}>Carpeta</div>
          <div style={{ fontSize: 12, color: t.c.text, fontFamily: FONT.mono, marginTop: 4 }}>C:\\Users\\Ana\\NeuroMood</div>
        </NMCard>
        <NMCard padding={14}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: ".12em", color: t.c.text3, textTransform: "uppercase" }}>Cuenta</div>
          <div style={{ fontSize: 12, color: t.c.text, marginTop: 4 }}>ana.martinez@email.com</div>
        </NMCard>
        <NMCard padding={14}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: ".12em", color: t.c.text3, textTransform: "uppercase" }}>Versión</div>
          <div style={{ fontSize: 12, color: t.c.text, fontFamily: FONT.mono, marginTop: 4 }}>NeuroMood Suite 1.0.0</div>
        </NMCard>
        <NMCard padding={14}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: ".12em", color: t.c.text3, textTransform: "uppercase" }}>Consentimiento</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 4 }}>
            <span style={{ width: 6, height: 6, borderRadius: 999, background: t.c.success }}/>
            <span style={{ fontSize: 12, color: t.c.text }}>Registrado · v.legal-2026-05-16</span>
          </div>
        </NMCard>
      </div>

      <div style={{ marginTop: 16, padding: "10px 14px", borderRadius: 10, background: t.c.elevated, fontSize: 11, color: t.c.text3, display: "flex", gap: 8 }}>
        <span>ℹ</span>
        <div>Se creó un acceso directo en el escritorio. Podés desinstalar la app desde "Agregar o quitar programas" o ejecutando <code style={{ fontFamily: FONT.mono, color: t.c.text2 }}>Desinstalador Suite</code>.</div>
      </div>
    </InstallerShell>
  );
}

// ── Desinstalador ─────────────────────────────────────────────────────────────

const UNINSTALL_STEPS = ["Confirmar", "Eliminando", "Finalizado"];

function UninstallerConfirmar() {
  const t = useTheme();
  return (
    <InstallerShell title="Desinstalador Suite" steps={UNINSTALL_STEPS} active={0} accent="danger"
      footerSecondary={<NMButton variant="ghost">Cancelar</NMButton>}
      footerPrimary={<NMButton variant="primary" danger>Desinstalar</NMButton>}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 16 }}>
        <div style={{
          width: 56, height: 56, borderRadius: 14,
          background: t.c.dangerSoft, color: t.c.danger,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 24, flexShrink: 0,
        }}>⚠</div>
        <div>
          <SectionTitle eyebrow="Desinstalación" size="lg">¿Desinstalar NeuroMood Suite?</SectionTitle>
          <div style={{ fontSize: 13, color: t.c.text2, lineHeight: 1.6, marginTop: 6 }}>
            Se eliminarán los archivos de instalación de tu computadora.
          </div>
        </div>
      </div>

      <NMCard padding={14} style={{ marginTop: 20 }}>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: ".12em", color: t.c.text3, textTransform: "uppercase" }}>Carpeta a eliminar</div>
        <div style={{ fontSize: 12, color: t.c.text, fontFamily: FONT.mono, marginTop: 4 }}>C:\\Users\\Ana\\NeuroMood</div>
      </NMCard>

      <NMCard padding={18} style={{ marginTop: 14, display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 14, alignItems: "center" }}>
        <div style={{
          width: 40, height: 40, borderRadius: 10,
          background: t.c.tealSoft, color: t.c.teal,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 18,
        }}>💾</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: t.c.text }}>Conservar mis datos</div>
          <div style={{ fontSize: 11, color: t.c.text3, marginTop: 2 }}>Registros, historial y configuración local de la app</div>
        </div>
        <NMToggle checked={true} tone="teal"/>
      </NMCard>

      <div style={{
        marginTop: 14, padding: "10px 14px", borderRadius: 10,
        background: t.c.elevated, fontSize: 11, color: t.c.text3,
        lineHeight: 1.5,
      }}>
        Al continuar se cerrarán todas las ventanas de NeuroMood Suite abiertas. Los accesos directos del escritorio y del menú inicio también serán eliminados.
      </div>
    </InstallerShell>
  );
}

function UninstallerEliminando() {
  const t = useTheme();
  return (
    <InstallerShell title="Desinstalador Suite" steps={UNINSTALL_STEPS} active={1} accent="danger"
      footerPrimary={<NMButton variant="primary" danger disabled>Desinstalando...</NMButton>}>
      <SectionTitle eyebrow="Paso 2" size="lg">Desinstalando NeuroMood Suite</SectionTitle>
      <NMProgress value={72} tone="danger" height={8} label="Progreso" />

      <NMCard padding={0} style={{ marginTop: 18, overflow: "hidden" }}>
        <div style={{ background: "#0a0e1a", padding: 16, fontFamily: FONT.mono, fontSize: 11, lineHeight: 1.8 }}>
          {[
            ["Cerrando aplicaciones...",           "success"],
            ["Eliminando accesos directos...",     "success"],
            ["Limpiando registro de Windows...",   "success"],
            ["Cerrando Explorer en la carpeta...", "success"],
            ["Eliminando archivos de instalación...", "syncing"],
            ["Conservando datos de usuario en AppData", "pending"],
          ].map(([msg, st], i) => (
            <div key={i} style={{ color: "#cbd3e1", display: "flex", gap: 10 }}>
              <span style={{
                color: st === "success" ? "#4ade80" : st === "syncing" ? "#fbbf24" : "#7d8aa3",
                width: 14,
              }}>{st === "success" ? "✓" : st === "syncing" ? "↻" : "○"}</span>
              <span>{msg}</span>
            </div>
          ))}
        </div>
      </NMCard>
    </InstallerShell>
  );
}

function UninstallerFinalizado() {
  const t = useTheme();
  return (
    <InstallerShell title="Desinstalador Suite" steps={UNINSTALL_STEPS} active={2} accent="success"
      footerPrimary={<NMButton variant="primary">Cerrar</NMButton>}>
      <div style={{ textAlign: "center", padding: "10px 40px 0" }}>
        <div style={{
          width: 72, height: 72, borderRadius: 999,
          background: t.c.successSoft, color: t.c.success,
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          fontSize: 32, marginBottom: 16,
          boxShadow: `0 0 0 10px ${t.c.success}11`,
        }}>✓</div>
        <SectionTitle eyebrow="Listo" size="xl">Desinstalación completada</SectionTitle>
        <div style={{ fontSize: 14, color: t.c.text2, lineHeight: 1.6, marginTop: 10, maxWidth: 460, margin: "10px auto 0" }}>
          NeuroMood Suite fue eliminado de este equipo. Tus datos personales se conservaron según la opción seleccionada.
        </div>
      </div>

      <NMCard padding={18} style={{ marginTop: 22, display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 14, alignItems: "center" }}>
        <div style={{
          width: 40, height: 40, borderRadius: 10,
          background: t.c.tealSoft, color: t.c.teal,
          display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
        }}>💾</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: t.c.text }}>Datos conservados</div>
          <div style={{ fontSize: 11, color: t.c.text3 }}>AppData\\NeuroMood\\nm_data.db · 2.4 MB</div>
        </div>
        <NMBadge tone="success">preservado</NMBadge>
      </NMCard>

      <div style={{ marginTop: 14, fontSize: 11, color: t.c.text3, textAlign: "center" }}>
        Si en el futuro reinstalás NeuroMood Suite, podrás recuperar tu historial desde estos datos.
      </div>
    </InstallerShell>
  );
}

// ── Design System (overview) ──────────────────────────────────────────────────
function DesignSystem() {
  const t = useTheme();
  return (
    <div style={{
      width: 1280, padding: "32px 40px",
      background: t.c.surface,
      borderRadius: 18,
      border: `1px solid ${t.c.borderSoft}`,
      boxShadow: t.s.lg,
      fontFamily: FONT.sans, color: t.c.text,
    }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".14em", color: t.c.accent, textTransform: "uppercase" }}>
            Sistema de diseño · NeuroMood Refined v3
          </div>
          <div style={{ fontSize: 32, fontWeight: 700, letterSpacing: "-.02em", marginTop: 6 }}>
            Identidad visual unificada
          </div>
          <div style={{ fontSize: 14, color: t.c.text2, marginTop: 6, maxWidth: 640, lineHeight: 1.55 }}>
            Refinamiento del sistema actual: indigo / teal / violet en tonos más sobrios, mayor aire, sombras suaves y un solo lenguaje de cards / pills / rings consistente en Suite, Hub, Instalador y Desinstalador.
          </div>
        </div>
        <NMLogo size={48}/>
      </div>

      {/* Tipografía */}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 1fr 1fr",
        gap: 18, marginBottom: 28,
      }}>
        <NMCard padding={22}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: ".14em", color: t.c.text3, textTransform: "uppercase" }}>Tipografía principal</div>
          <div style={{ fontSize: 40, fontWeight: 700, letterSpacing: "-.02em", marginTop: 12, lineHeight: 1 }}>DM Sans</div>
          <div style={{ fontSize: 11, color: t.c.text3, marginTop: 6 }}>Geométrica humanista · Google Fonts</div>
          <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 6 }}>
            {[
              ["Display 28", 28, 700],
              ["Heading 22", 22, 600],
              ["Body 13", 13, 400],
              ["Caption 11", 11, 500],
            ].map(([n, s, w]) => (
              <div key={n} style={{ fontSize: s, fontWeight: w, color: t.c.text }}>{n}</div>
            ))}
          </div>
        </NMCard>
        <NMCard padding={22}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: ".14em", color: t.c.text3, textTransform: "uppercase" }}>Mono · datos y código</div>
          <div style={{ fontSize: 36, fontWeight: 700, fontFamily: FONT.mono, marginTop: 12, lineHeight: 1, letterSpacing: "-.04em" }}>14:32</div>
          <div style={{ fontSize: 11, color: t.c.text3, marginTop: 6 }}>JetBrains Mono · timers, IDs, fechas, hashes, logs</div>
          <div style={{ marginTop: 16, fontFamily: FONT.mono, fontSize: 11, color: t.c.text2, lineHeight: 1.8 }}>
            <div>id=AM-7842</div>
            <div>fecha=2026-05-16</div>
            <div>hash=8a4f...e29c</div>
          </div>
        </NMCard>
        <NMCard padding={22}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: ".14em", color: t.c.text3, textTransform: "uppercase" }}>Jerarquía</div>
          <div style={{ marginTop: 14 }}>
            <div style={{ fontSize: 10, color: t.c.text3, fontWeight: 700, letterSpacing: ".12em", textTransform: "uppercase" }}>Eyebrow</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: t.c.text, marginTop: 4, letterSpacing: "-.01em" }}>Título de sección</div>
            <div style={{ fontSize: 13, color: t.c.text2, marginTop: 4, lineHeight: 1.55 }}>
              Descripción que apoya al título. Reservar tamaños grandes para títulos principales; nunca menos de 11px en cuerpo.
            </div>
          </div>
        </NMCard>
      </div>

      {/* Colores */}
      <SectionTitle eyebrow="Color tokens" size="md">Paleta clínica</SectionTitle>
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(8, 1fr)",
        gap: 10, marginTop: 12, marginBottom: 28,
      }}>
        {[
          ["accent", "Indigo · Brand"],
          ["teal", "Teal · Bienestar"],
          ["violet", "Violet · Acento"],
          ["success", "Success"],
          ["warning", "Warning"],
          ["danger", "Danger"],
          ["info", "Info"],
          ["streak", "Streak"],
        ].map(([k, label]) => (
          <NMCard key={k} padding={0} style={{ overflow: "hidden" }}>
            <div style={{ height: 64, background: t.c[k] }}/>
            <div style={{ padding: "10px 12px" }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: t.c.text }}>{label}</div>
              <div style={{ fontSize: 10, color: t.c.text3, fontFamily: FONT.mono, marginTop: 2 }}>{t.c[k]}</div>
            </div>
          </NMCard>
        ))}
      </div>

      {/* Componentes */}
      <SectionTitle eyebrow="Componentes" size="md">Núcleo del kit</SectionTitle>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginTop: 12 }}>
        <NMCard padding={20}>
          <div style={{ fontSize: 11, fontWeight: 700, color: t.c.text3, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 12 }}>Botones</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <NMButton variant="primary">Primario</NMButton>
            <NMButton variant="secondary">Secundario</NMButton>
            <NMButton variant="ghost">Ghost</NMButton>
            <NMButton variant="soft">Soft</NMButton>
            <NMButton variant="primary" danger>Destructivo</NMButton>
          </div>
        </NMCard>
        <NMCard padding={20}>
          <div style={{ fontSize: 11, fontWeight: 700, color: t.c.text3, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 12 }}>Badges</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            <NMBadge tone="default">Default</NMBadge>
            <NMBadge tone="accent">Accent</NMBadge>
            <NMBadge tone="teal">Teal</NMBadge>
            <NMBadge tone="violet">Violet</NMBadge>
            <NMBadge tone="success">Completo</NMBadge>
            <NMBadge tone="warning">2/5</NMBadge>
            <NMBadge tone="danger">Atención</NMBadge>
            <NMBadge tone="streak" icon={<span>🔥</span>}>5 días</NMBadge>
          </div>
        </NMCard>
        <NMCard padding={20}>
          <div style={{ fontSize: 11, fontWeight: 700, color: t.c.text3, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 12 }}>Rings de progreso</div>
          <div style={{ display: "flex", gap: 16, alignItems: "center", justifyContent: "space-around" }}>
            <NMRing pct={30}  size={56} stroke={5} tone="accent" value="30%"/>
            <NMRing pct={65}  size={56} stroke={5} tone="teal"   value="65%"/>
            <NMRing pct={100} size={56} stroke={5} tone="success" value="100%"/>
          </div>
        </NMCard>
        <NMCard padding={20}>
          <div style={{ fontSize: 11, fontWeight: 700, color: t.c.text3, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 12 }}>Inputs</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <NMInput placeholder="Buscar paciente..." icon={<span style={{ fontSize: 11 }}>🔍</span>}/>
            <NMInput value="ana.martinez@email.com"/>
            <div style={{ display: "flex", gap: 10 }}>
              <NMCheck checked={true} label="Aceptar"/>
              <NMToggle checked={true}/>
            </div>
          </div>
        </NMCard>
        <NMCard padding={20}>
          <div style={{ fontSize: 11, fontWeight: 700, color: t.c.text3, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 12 }}>Cards</div>
          <NMCard accent="accent" padding={12} style={{ marginBottom: 8 }}>
            <div style={{ fontSize: 12, fontWeight: 600 }}>Card con accent</div>
            <div style={{ fontSize: 11, color: t.c.text3, marginTop: 2 }}>Barra izquierda 3px</div>
          </NMCard>
          <NMCard padding={12}>
            <div style={{ fontSize: 12, fontWeight: 600 }}>Card neutra</div>
            <div style={{ fontSize: 11, color: t.c.text3, marginTop: 2 }}>Sin acento lateral</div>
          </NMCard>
        </NMCard>
        <NMCard padding={20}>
          <div style={{ fontSize: 11, fontWeight: 700, color: t.c.text3, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 12 }}>Estados de sync</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <SyncOrb state="ok"/>
            <SyncOrb state="syncing"/>
            <SyncOrb state="error"/>
          </div>
        </NMCard>
      </div>

      {/* Spacing & Radius */}
      <SectionTitle eyebrow="Layout tokens" size="md" style={{ marginTop: 28 }}>Espaciado y radios</SectionTitle>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 12 }}>
        <NMCard padding={20}>
          <div style={{ fontSize: 11, color: t.c.text3, marginBottom: 10 }}>Spacing scale · base 4px</div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 8 }}>
            {[["xs",4],["sm",8],["md",12],["lg",16],["xl",24],["xxl",32],["xxxl",48]].map(([k, v]) => (
              <div key={k} style={{ textAlign: "center" }}>
                <div style={{ width: 26, height: v, background: t.c.accent, borderRadius: 4, opacity: .8 }}/>
                <div style={{ fontSize: 9, color: t.c.text3, marginTop: 4, fontFamily: FONT.mono }}>{k}/{v}</div>
              </div>
            ))}
          </div>
        </NMCard>
        <NMCard padding={20}>
          <div style={{ fontSize: 11, color: t.c.text3, marginBottom: 10 }}>Radius scale</div>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            {[["sm",6],["md",10],["lg",14],["xl",20],["pill",999]].map(([k,v]) => (
              <div key={k} style={{ textAlign: "center" }}>
                <div style={{ width: 56, height: 56, background: t.c.accent, borderRadius: v, opacity: .85 }}/>
                <div style={{ fontSize: 9, color: t.c.text3, marginTop: 4, fontFamily: FONT.mono }}>{k}</div>
              </div>
            ))}
          </div>
        </NMCard>
      </div>
    </div>
  );
}

// ── Auditoría visual ──────────────────────────────────────────────────────────
function VisualAudit() {
  const t = useTheme();
  const findings = [
    {
      cat: "Pantallas inconsistentes",
      icon: "⚠",
      tone: "warning",
      items: [
        "Home (Suite) usa emojis grandes en cards, Hub usa iconos FontAwesome → unificar a iconos de línea SVG.",
        "Hub Dashboard tiene aura radial fuerte indigo/violet; resto de la app no → reducir a 6% opacity o quitar.",
        "Detalle de paciente usa tabs estilo pill; instalador usa stepper distinto → adoptar tab-segmented uniforme.",
        "TCC slider tiene gradiente caliente; Ánimo usa color sólido teal → consolidar lenguaje de scales.",
      ],
    },
    {
      cat: "Componentes que no respetan identidad",
      icon: "✕",
      tone: "danger",
      items: [
        "NMCard tiene barra izquierda gradient teal→violet en algunos sitios y barra sólida en otros → fijar barra sólida 3px.",
        "Glow de hover sobre cards en dark mode con radio 15px → exagerado para clínico, bajar a 4px shadow suave.",
        "Stepper de installer pintaba pasos completados con check verde + texto blanco grueso → simplificar a check + número.",
        "Pacientes vista (visual_qa) tenía chips con borde grueso; Hub config chips usaba toggle visual → unificar.",
      ],
    },
    {
      cat: "Partes que se ven viejas",
      icon: "🕰",
      tone: "default",
      items: [
        "Headers de módulos Suite con QGraphicsDropShadow blur=28 + offset(0,8) → reemplazar por borde inferior 1px + sombra de 4px.",
        "ScrollBars con gradiente teal→accent → adoptar scrollbar nativa fina (6px, opacity 30%).",
        "NoiseOverlay con opacidad .04 en cards → eliminar, no aporta y rinde menos en escalado HiDPI.",
        "Saludo del Home concatenaba 👋 emoji al texto → mover a un slot dedicado o quitar.",
      ],
    },
    {
      cat: "Para 100% unificación",
      icon: "✓",
      tone: "success",
      items: [
        "Single source of truth de iconos: librería propia 24/16px stroke 1.6, no mezclar QtAwesome + emoji.",
        "Tabular consistente: t fonts mono solo para datos (timer, ids, hashes, %); nunca para títulos de UI.",
        "AppFrame común para Suite / Hub / Installer / Uninstaller con misma titlebar y radius (no Captionbar Win DWM en Hub si Suite no lo aplica).",
        "Sistema de estados (badge tones) único: success / warning / danger / accent / teal / violet / streak — sin colores hex sueltos.",
        "Texto de empty-state estandarizado: icono 48px + título 16px + sub 12px (ya implementado en NMEmptyState; replicar en Hub Pacientes vacío).",
      ],
    },
  ];
  return (
    <div style={{
      width: 1280, padding: "32px 40px",
      background: t.c.surface,
      borderRadius: 18,
      border: `1px solid ${t.c.borderSoft}`,
      boxShadow: t.s.lg,
      fontFamily: FONT.sans, color: t.c.text,
    }}>
      <div style={{ marginBottom: 22 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".14em", color: t.c.warning, textTransform: "uppercase" }}>
          Auditoría visual breve
        </div>
        <div style={{ fontSize: 32, fontWeight: 700, letterSpacing: "-.02em", marginTop: 6 }}>
          Qué cambiar para que todo se sienta del mismo producto
        </div>
        <div style={{ fontSize: 13, color: t.c.text2, marginTop: 6, maxWidth: 760 }}>
          Análisis sobre el código real (PyQt6) y mockups previos. Cada bloque sugiere fixes accionables que mantienen la lógica intacta — son cambios visuales.
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {findings.map(f => (
          <NMCard key={f.cat} padding={20}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
              <div style={{
                width: 34, height: 34, borderRadius: 10,
                background: t.c[`${f.tone}Soft`], color: t.c[f.tone],
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 16,
              }}>{f.icon}</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: t.c.text, letterSpacing: "-.005em" }}>
                {f.cat}
              </div>
            </div>
            <ol style={{ margin: 0, paddingLeft: 20, display: "flex", flexDirection: "column", gap: 8 }}>
              {f.items.map((it, i) => (
                <li key={i} style={{
                  fontSize: 12, color: t.c.text2, lineHeight: 1.6,
                }}>{it}</li>
              ))}
            </ol>
          </NMCard>
        ))}
      </div>

      <div style={{ marginTop: 22, padding: 16, borderRadius: 12, background: t.c.accentSoft, border: `1px solid ${t.c.accent}22` }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: t.c.accent, letterSpacing: ".12em", textTransform: "uppercase" }}>Próximo paso recomendado</div>
        <div style={{ fontSize: 13, color: t.c.text, marginTop: 6, lineHeight: 1.6 }}>
          Aplicar el nuevo <strong>theme_qt.py</strong> con tokens refinados (accent desaturado, sombras suaves, glow off) y migrar <strong>NMCard / NMButton / NMBadge / NMRing</strong> al lenguaje de este mockup. Estimación: ~2 días de trabajo visual, sin tocar lógica de DB / sync / módulos.
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  InstallerShell, INSTALL_STEPS, UNINSTALL_STEPS,
  InstallerBienvenida, InstallerCuenta, InstallerConsentimiento,
  InstallerInstalacion, InstallerFinalizar,
  UninstallerConfirmar, UninstallerEliminando, UninstallerFinalizado,
  DesignSystem, VisualAudit,
});
