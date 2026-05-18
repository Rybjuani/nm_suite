/* app.jsx — Canvas final con todas las pantallas v3 */

function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const { mode } = tweaks;
  return (
    <ThemeProvider palette="refined" mode={mode}>
      <DesignCanvas>
        <DCSection id="suite" title="01 · NeuroMood Suite (paciente)"
          subtitle="Inicio + 7 módulos. Tweak global cambia el tema por defecto de cada artboard; el toggle del header funciona individualmente.">
          <DCArtboard id="s-inicio"      label="Inicio"                width={1320} height={860}><V3SuiteInicio mode={mode}/></DCArtboard>
          <DCArtboard id="s-animo"       label="Mood Tracker"          width={1320} height={860}><V3SuiteAnimo mode={mode}/></DCArtboard>
          <DCArtboard id="s-resp"        label="Respiración 4-7-8"     width={1320} height={860}><V3SuiteRespiracion mode={mode}/></DCArtboard>
          <DCArtboard id="s-tcc"         label="Registro TCC"          width={1320} height={860}><V3SuiteTCC mode={mode}/></DCArtboard>
          <DCArtboard id="s-rutina"      label="Rutina del día"        width={1320} height={860}><V3SuiteRutina mode={mode}/></DCArtboard>
          <DCArtboard id="s-act"         label="Activación conductual" width={1320} height={860}><V3SuiteActividades mode={mode}/></DCArtboard>
          <DCArtboard id="s-timer"       label="Timer de enfoque"      width={1320} height={860}><V3SuiteTimer mode={mode}/></DCArtboard>
          <DCArtboard id="s-avisos"      label="Recordatorios"         width={1320} height={860}><V3SuiteAvisos mode={mode}/></DCArtboard>
        </DCSection>

        <DCSection id="hub" title="02 · NeuroMood Hub (profesional)"
          subtitle="Dashboard, Pacientes, Detalle, IA Asistente y Configuración.">
          <DCArtboard id="h-pac"         label="Pacientes"             width={1360} height={920}><V3HubDashboard mode={mode}/></DCArtboard>
          <DCArtboard id="h-detalle"     label="Detalle paciente"      width={1360} height={920}><V3HubDetalle mode={mode}/></DCArtboard>
          <DCArtboard id="h-ia"          label="IA Asistente clínico"  width={1360} height={920}><V3HubIA mode={mode}/></DCArtboard>
          <DCArtboard id="h-config"      label="Configuración"         width={1360} height={920}><V3HubConfig mode={mode}/></DCArtboard>
        </DCSection>

        <DCSection id="installer" title="03 · Instalador Suite"
          subtitle="Wizard de 5 pasos para pacientes.">
          <DCArtboard id="i-0" label="01 · Bienvenida"     width={820} height={660}><V3InstBienvenida/></DCArtboard>
          <DCArtboard id="i-1" label="02 · Cuenta"         width={820} height={680}><V3InstCuenta/></DCArtboard>
          <DCArtboard id="i-2" label="03 · Consentimiento" width={820} height={780}><V3InstConsentimiento/></DCArtboard>
          <DCArtboard id="i-3" label="04 · Instalación"    width={820} height={700}><V3InstInstalacion/></DCArtboard>
          <DCArtboard id="i-4" label="05 · Finalizar"      width={820} height={660}><V3InstFinalizar/></DCArtboard>
        </DCSection>

        <DCSection id="uninstaller" title="04 · Desinstalador Suite"
          subtitle="Wizard destructivo de 3 pasos. Dark theme por defecto.">
          <DCArtboard id="u-0" label="01 · Confirmar"   width={760} height={620}><V3UninstConfirmar/></DCArtboard>
          <DCArtboard id="u-1" label="02 · Eliminando"  width={760} height={620}><V3UninstEliminando/></DCArtboard>
          <DCArtboard id="u-2" label="03 · Finalizado"  width={760} height={620}><V3UninstFinalizado/></DCArtboard>
        </DCSection>
      </DesignCanvas>

      <TweaksPanel>
        <TweakSection label="Tema global">
          <TweakRadio
            label="Modo por defecto"
            value={mode}
            options={["light", "dark"]}
            onChange={v => setTweak("mode", v)}
          />
        </TweakSection>
      </TweaksPanel>
    </ThemeProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
