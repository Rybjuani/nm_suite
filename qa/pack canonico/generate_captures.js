/*
 * generate_captures.js — NeuroMood · generador de capturas canónicas v3
 * ====================================================================
 *
 * Genera EXACTAMENTE 86 PNG canónicas (43 vistas × 2 temas) con nombres y
 * tamaños fijos.
 *
 * Uso:
 *   node ./generate_captures.js ./neuromood-mockup_reparado.html ./capturas_test
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const CHROMIUM_PATH = process.env.PUPPETEER_EXECUTABLE_PATH || '/usr/bin/chromium';

/* ---------------------------------------------------------------------------
 * 1) Catálogo de las 43 vistas
 * ------------------------------------------------------------------------ */

const SIZE_WINDOW  = '960x600';
const SIZE_NARROW  = '520x600';
const SIZE_MODAL   = '480x325';
const SIZE_MODAL_L = '960x600';

const VIEWS = [
  // ---------- Hub · Pacientes ----------
  { name: 'hub-pacientes',                  screen: 'pacientes', state: 'list',  size: SIZE_WINDOW },
  { name: 'hub-pacientes-empty',            screen: 'pacientes', state: 'empty', size: SIZE_WINDOW },

  // ---------- Hub · Detalle (4 tabs + 1 modal) ----------
  { name: 'hub-detalle',                    screen: 'detalle', hubTab: 'recordatorios', size: SIZE_WINDOW },
  { name: 'hub-detalle-plan-timer',         screen: 'detalle', hubTab: 'timer',         size: SIZE_WINDOW },
  { name: 'hub-detalle-plan-rutina',        screen: 'detalle', hubTab: 'rutina',        size: SIZE_WINDOW },
  { name: 'hub-detalle-plan-activacion',    screen: 'detalle', hubTab: 'activacion',    size: SIZE_WINDOW },
  { name: 'hub-detalle-resumen-ia-0',       screen: 'detalle', hubTab: 'recordatorios',
    openModalSel: '[data-ia-summary]', captureSel: '.modal', size: SIZE_MODAL },

  // ---------- Hub · Configuración ----------
  { name: 'hub-textos-globales',            screen: 'textos', size: SIZE_WINDOW },

  // ---------- Suite · Inicio ----------
  { name: 'suite-home',                     screen: 'home', state: 'score',   size: SIZE_WINDOW },
  { name: 'suite-home-no-score',            screen: 'home', state: 'noscore', size: SIZE_WINDOW },

  // ---------- Suite · Bienestar ----------
  { name: 'suite-animo',                    screen: 'animo', size: SIZE_WINDOW },
  { name: 'suite-respiracion',              screen: 'respiracion', state: 'idle',    size: SIZE_WINDOW },
  { name: 'suite-respiracion-running',      screen: 'respiracion', state: 'running', size: SIZE_WINDOW },
  { name: 'suite-respiracion-paused',       screen: 'respiracion', state: 'paused',  size: SIZE_WINDOW },

  // ---------- Suite · Hábitos ----------
  { name: 'suite-timer',                    screen: 'timer', state: 'idle',    size: SIZE_WINDOW },
  { name: 'suite-timer-running',            screen: 'timer', state: 'running', size: SIZE_WINDOW },
  { name: 'suite-timer-paused',             screen: 'timer', state: 'paused',  size: SIZE_WINDOW },
  { name: 'suite-timer-empty',              screen: 'timer', state: 'empty',   size: SIZE_WINDOW },
  { name: 'suite-rutina',                   screen: 'rutina', state: 'default', size: SIZE_WINDOW },
  { name: 'suite-rutina-add-task',          screen: 'rutina', state: 'add',     size: SIZE_WINDOW },
  { name: 'suite-rutina-all-completed',     screen: 'rutina', state: 'done',    size: SIZE_WINDOW },
  { name: 'suite-rutina-empty',             screen: 'rutina', state: 'empty',   size: SIZE_WINDOW },
  { name: 'suite-avisos',                   screen: 'avisos', state: 'all',     size: SIZE_WINDOW },
  { name: 'suite-avisos-filter-activos',    screen: 'avisos', state: 'active',  size: SIZE_WINDOW },
  { name: 'suite-avisos-today',             screen: 'avisos', state: 'today',   size: SIZE_WINDOW },
  { name: 'suite-avisos-search',            screen: 'avisos', state: 'search',  size: SIZE_WINDOW },
  { name: 'suite-avisos-empty',             screen: 'avisos', state: 'empty',   size: SIZE_WINDOW },

  // ---------- Suite · Cognitivo ----------
  { name: 'suite-actividades',              screen: 'actividades', state: 'default',  size: SIZE_WINDOW },
  { name: 'suite-actividades-filtered',     screen: 'actividades', state: 'filtered', size: SIZE_WINDOW },
  { name: 'suite-actividades-marked-hice',  screen: 'actividades', state: 'marked',   size: SIZE_WINDOW },
  { name: 'suite-actividades-empty',        screen: 'actividades', state: 'empty',    size: SIZE_WINDOW },
  { name: 'suite-registro',                 screen: 'registro', state: 's0',     size: SIZE_WINDOW },
  { name: 'suite-registro-step1-emotion',        screen: 'registro', state: 's1',     size: SIZE_WINDOW },
  { name: 'suite-registro-step1-emotion-otro',   screen: 'registro', state: 's1otro', size: SIZE_WINDOW },
  { name: 'suite-registro-step2-distortions',    screen: 'registro', state: 's2',     size: SIZE_WINDOW },
  { name: 'suite-registro-step3-filled',         screen: 'registro', state: 's3',     size: SIZE_WINDOW },
  { name: 'suite-registro-success',               screen: 'registro', state: 'ok',     size: SIZE_WINDOW },

  // ---------- Suite · Habilidades DBT ----------
  { name: 'suite-dbt-now',                  screen: 'dbtnow', size: SIZE_WINDOW },
  { name: 'suite-dbt-library',              screen: 'dbtlib', size: SIZE_WINDOW },
  { name: 'suite-dbt-practice-stop',        screen: 'dbtlib',
    openModalSel: '.dbt-card[data-skill="Tolerancia"]', afterOpenClickSel: '#dbtNext', captureSel: '.window', size: SIZE_WINDOW },

  // ---------- Suite · Acceso ----------
  { name: 'suite-onboarding',               screen: 'onboarding', state: 'normal', size: SIZE_NARROW },
  { name: 'suite-onboarding-error',         screen: 'onboarding', state: 'error',  size: SIZE_NARROW },
  { name: 'suite-recuperar-acceso',         screen: 'recuperar',                   size: SIZE_NARROW },
];

const THEMES = ['light', 'dark'];

if (VIEWS.length !== 43) {
  console.error(`ERROR: VIEWS.length=${VIEWS.length}, se esperaba 43`);
  process.exit(2);
}

/* ---------------------------------------------------------------------------
 * 2) Helpers
 * ------------------------------------------------------------------------ */

function sha256(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function pngDims(filePath) {
  const buf = fs.readFileSync(filePath);
  if (buf.length < 24) return { w: 0, h: 0 };
  if (buf[0] !== 0x89 || buf[1] !== 0x50) return { w: 0, h: 0 };
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function parseSize(s) {
  const [w, h] = s.split('x').map(Number);
  return { w, h };
}

/* ---------------------------------------------------------------------------
 * 3) Flujo de captura por vista
 * ------------------------------------------------------------------------ */

async function captureView(page, view, theme, outDir) {
  // 3.1 — Tema
  await page.evaluate((t) => {
    document.documentElement.dataset.theme = t;
  }, theme);

  // 3.2 — Navegación principal
  await page.evaluate((v) => {
    if (typeof window.go !== 'function') {
      throw new Error('window.go no esta definida en el mockup');
    }
    window.go(v.screen, v.state || null);
  }, view);

  // 3.3 — Esperar que la ventana este en el DOM
  await page.waitForSelector('.window');
  await sleep(550);  // transiciones winIn/scrnIn

  // 3.4 — Tabs de detalle
  if (view.hubTab) {
    await page.evaluate((tab) => {
      const btn = document.querySelector(`[data-tab="${tab}"]`);
      if (!btn) throw new Error(`No se encontro [data-tab="${tab}"]`);
      btn.click();
    }, view.hubTab);
    await sleep(220);
  }

  // 3.5 — Abrir modal si corresponde
  let isModal = !!view.captureSel && view.captureSel === '.modal';
  if (view.openModalSel) {
    await page.evaluate((sel) => {
      const btn = document.querySelector(sel);
      if (!btn) throw new Error(`No se encontro boton de modal con selector ${sel}`);
      btn.click();
    }, view.openModalSel);
    await page.waitForSelector('.modal-bg.show');
    await sleep(380);
    await page.waitForSelector('.modal');
  }

  // 3.5b — Acciones dentro del modal antes de capturar.
  // DBT "practice-stop" es un estado intermedio: la app PyQt y el contrato de
  // test capturan Paso 2, por eso el mockup canónico debe avanzar una vez.
  if (view.afterOpenClickSel) {
    const clicks = view.afterOpenClickCount || 1;
    for (let i = 0; i < clicks; i++) {
      await page.evaluate((sel) => {
        const btn = document.querySelector(sel);
        if (!btn) throw new Error(`No se encontro accion post-modal ${sel}`);
        btn.click();
      }, view.afterOpenClickSel);
      await sleep(220);
      await page.waitForSelector('.modal');
    }
  }

  if (view.name === 'suite-dbt-practice-stop') {
    await page.evaluate(() => {
      const win = document.querySelector('.window');
      const titlebar = win ? win.querySelector('.titlebar') : null;
      const bg = document.querySelector('.modal-bg');
      const modal = document.querySelector('.modal');
      if (!win || !bg || !modal) return;
      const wb = win.getBoundingClientRect();
      const tb = titlebar ? titlebar.getBoundingClientRect() : { height: 47 };
      bg.style.position = 'fixed';
      bg.style.left = `${wb.left}px`;
      bg.style.top = `${wb.top + tb.height}px`;
      bg.style.width = `${wb.width}px`;
      bg.style.height = `${wb.height - tb.height}px`;
      modal.style.position = '';
      modal.style.left = '';
      modal.style.top = '';
    });
    await sleep(80);
  }

  // 3.6 — Fuentes listas
  await page.evaluate(() => document.fonts.ready);
  await sleep(80);

  // 3.7 — Reset scroll interno a 0
  await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (el) {
      const screen = el.querySelector('.screen');
      if (screen) screen.scrollTop = 0;
      el.scrollTop = 0;
    }
  }, view.captureSel || '.window');

  // 3.8 — Mouse fuera del viewport para limpiar :hover
  await page.mouse.move(-100, -100);
  await sleep(140);

  // 3.9 — Capturar elemento .window o .modal
  const captureSel = view.captureSel || '.window';
  const handle = await page.$(captureSel);
  if (!handle) throw new Error(`No se encontro elemento para capturar: ${captureSel}`);

  const expected = parseSize(view.size);
  const fileName = `${view.name}-${theme}-${view.size}.png`;
  const filePath = path.join(outDir, fileName);

  const box = await handle.boundingBox();
  if (!box) throw new Error(`boundingBox vacio para ${captureSel}`);
  await page.screenshot({
    path: filePath,
    clip: {
      x: Math.round(box.x),
      y: Math.round(box.y),
      width: expected.w,
      height: expected.h,
    },
  });

  // 3.10 — Cerrar modal si quedo abierto
  if (isModal) {
    await page.evaluate(() => {
      if (typeof window.closeModal === 'function') window.closeModal();
      const bg = document.querySelector('.modal-bg');
      if (bg) bg.classList.remove('show');
      const m = document.querySelector('.modal');
      if (m) m.classList.remove('large');
    });
    await sleep(150);
  }

  // 3.11 — Medidas reales + sha256
  const dims = pngDims(filePath);
  const sh = sha256(filePath);
  const sizeMatch = (dims.w === expected.w && dims.h === expected.h);

  return {
    file: fileName,
    view: view.name,
    screen: view.screen,
    state: view.state || view.hubTab || '',
    surface: isModal ? 'modal' : (view.size === SIZE_NARROW ? 'narrow' : 'window'),
    theme,
    real_w: dims.w,
    real_h: dims.h,
    expected_w: expected.w,
    expected_h: expected.h,
    size_match: sizeMatch,
    sha256: sh,
    bytes: fs.statSync(filePath).size,
  };
}

/* ---------------------------------------------------------------------------
 * 4) Main
 * ------------------------------------------------------------------------ */

(async () => {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error('Uso: node generate_captures.js <mockup.html> <out_dir>');
    process.exit(2);
  }
  const htmlPath = path.resolve(args[0]);
  const outDir = path.resolve(args[1]);
  if (!fs.existsSync(htmlPath)) {
    console.error(`No existe el mockup: ${htmlPath}`);
    process.exit(2);
  }
  fs.mkdirSync(outDir, { recursive: true });

  console.log(`Mockup : ${htmlPath}`);
  console.log(`Salida : ${outDir}`);
  console.log(`Vistas : ${VIEWS.length} × ${THEMES.length} temas = ${VIEWS.length * THEMES.length} PNG`);
  console.log(`Chromium: ${CHROMIUM_PATH}`);

  const browser = await puppeteer.launch({
    executablePath: CHROMIUM_PATH,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1400, height: 900, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();

  page.on('console', (msg) => {
    if (msg.type() === 'error') console.warn('  [console.error]', msg.text());
  });
  page.on('pageerror', (err) => console.warn('  [pageerror]', err.message));

  await page.goto('file://' + htmlPath, { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => { document.documentElement.dataset.theme = 'light'; });
  await sleep(300);

  const records = [];
  let i = 0;
  const total = VIEWS.length * THEMES.length;
  for (const view of VIEWS) {
    for (const theme of THEMES) {
      i++;
      try {
        const r = await captureView(page, view, theme, outDir);
        records.push(r);
        const flag = r.size_match ? 'OK ' : 'BAD';
        console.log(`[${String(i).padStart(2)}/${total}] ${flag}  ${r.file}  ${r.real_w}x${r.real_h}`);
      } catch (err) {
        console.error(`[FAIL] ${view.name}-${theme}: ${err.message}`);
        records.push({
          file: `${view.name}-${theme}-${view.size}.png`,
          view: view.name, screen: view.screen,
          state: view.state || view.hubTab || '',
          surface: 'error', theme,
          real_w: 0, real_h: 0,
          expected_w: parseSize(view.size).w, expected_h: parseSize(view.size).h,
          size_match: false, sha256: '', bytes: 0,
          error: err.message,
        });
      }
    }
  }

  await browser.close();

  // ---- INDICE_CAPTURAS.csv ----
  const csvPath = path.join(outDir, 'INDICE_CAPTURAS.csv');
  const csvLines = [
    'file,view,screen,state,surface,theme,real_w,real_h,expected_w,expected_h,size_match,sha256,bytes',
  ];
  for (const r of records) {
    csvLines.push([
      r.file, r.view, r.screen, r.state, r.surface, r.theme,
      r.real_w, r.real_h, r.expected_w, r.expected_h,
      r.size_match ? 'yes' : 'no',
      r.sha256, r.bytes,
    ].join(','));
  }
  fs.writeFileSync(csvPath, csvLines.join('\n') + '\n', 'utf8');
  console.log(`\nINDICE_CAPTURAS.csv -> ${csvPath}`);

  // ---- MANIFEST.json ----
  const expected = VIEWS.length * THEMES.length;
  const manifest = {
    generator: 'generate_captures.js',
    mockup: path.basename(htmlPath),
    total_captures: records.length,
    expected_captures: expected,
    all_captured: records.length === expected && records.every(r => r.bytes > 0),
    all_sizes_match: records.every(r => r.size_match),
    themes: THEMES,
    surfaces: {
      window: records.filter(r => r.surface === 'window').length,
      narrow: records.filter(r => r.surface === 'narrow').length,
      modal:  records.filter(r => r.surface === 'modal').length,
    },
    size_mismatches: records.filter(r => !r.size_match).map(r => ({
      file: r.file, real_w: r.real_w, real_h: r.real_h,
      expected_w: r.expected_w, expected_h: r.expected_h,
    })),
    captures: records,
  };
  const manifestPath = path.join(outDir, 'MANIFEST.json');
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf8');
  console.log(`MANIFEST.json -> ${manifestPath}`);

  // ---- Resumen final ----
  const ok = records.filter(r => r.bytes > 0).length;
  const fail = records.length - ok;
  const mismatches = manifest.size_mismatches.length;
  console.log('\n=========== RESUMEN ===========');
  console.log(`Capturas OK : ${ok}/${records.length}`);
  console.log(`Fallos      : ${fail}`);
  console.log(`Tamano OK   : ${records.length - mismatches}/${records.length}`);
  if (mismatches > 0) {
    for (const m of manifest.size_mismatches) {
      console.log(`  BAD  ${m.file}  real=${m.real_w}x${m.real_h}  expected=${m.expected_w}x${m.expected_h}`);
    }
  }
  console.log('===============================');
  if (fail > 0 || mismatches > 0) process.exit(1);
})().catch((err) => {
  console.error('Error fatal:', err);
  process.exit(1);
});
