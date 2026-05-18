/* v3-neural.jsx — Neural background BEHIND THE LOGO + Play button utility
 * - NMLogoNeural: pequeño widget que envuelve al logo con conexiones neuronales
 *   sutiles detrás. Reemplaza al full-bleed anterior.
 * - NMPlayButton: control circular pequeño con fondo neutro, borde sutil, sombra
 *   suave e ícono play minimal. Diseñado para centrarse dentro de un anillo.
 */

// ── NMLogoNeural: aura + trazas detrás del logo ───────────────────────────────
function NMLogoNeural({ size = 220, logoSize = 100, asIcon = false, padding = 24 }) {
  const { c, isDark } = useV3Theme();
  const id = `lneu${Math.random().toString(36).slice(2, 7)}`;
  return (
    <div style={{
      position: "relative",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: size,
      height: size * 0.6,
      padding,
    }}>
      {/* Neural traces background, contained */}
      <svg
        width="100%" height="100%"
        viewBox="0 0 400 240"
        preserveAspectRatio="xMidYMid slice"
        style={{
          position: "absolute", inset: 0,
          pointerEvents: "none",
          opacity: isDark ? .85 : .55,
          transition: "opacity .35s ease",
        }}>
        <defs>
          <filter id={`${id}-glow`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation={isDark ? "2.5" : "1"} result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
          <linearGradient id={`${id}-line`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%"   stopColor={isDark ? "#5eead4" : "#14b8a6"} stopOpacity={isDark ? .7 : .45}/>
            <stop offset="50%"  stopColor={isDark ? "#22d3ee" : "#06b6d4"} stopOpacity={isDark ? .55 : .35}/>
            <stop offset="100%" stopColor={isDark ? "#c084fc" : "#a855f7"} stopOpacity={isDark ? .7 : .45}/>
          </linearGradient>
          <radialGradient id={`${id}-halo`} cx="50%" cy="50%" r="55%">
            <stop offset="0%"  stopColor={isDark ? "#5eead4" : "#14b8a6"} stopOpacity={isDark ? .22 : .08}/>
            <stop offset="60%" stopColor={isDark ? "#a78bfa" : "#a855f7"} stopOpacity={isDark ? .15 : .06}/>
            <stop offset="100%" stopColor="transparent" stopOpacity="0"/>
          </radialGradient>
        </defs>
        {/* Halo behind */}
        <rect width="400" height="240" fill={`url(#${id}-halo)`}/>
        {/* PCB-style traces */}
        <g stroke={`url(#${id}-line)`} strokeWidth="1.4" fill="none" filter={`url(#${id}-glow)`} strokeLinecap="round">
          <path d="M -10 50 L 80 50 L 110 30 L 170 30 L 195 55 L 240 55"/>
          <path d="M 160 60 L 240 60 L 270 85 L 340 85 L 370 60 L 410 60"/>
          <path d="M -10 110 L 60 110 L 90 135 L 160 135"/>
          <path d="M 240 130 L 290 130 L 320 105 L 410 105"/>
          <path d="M -10 175 L 90 175 L 115 200 L 200 200"/>
          <path d="M 220 180 L 280 180 L 310 205 L 410 205"/>
          <path d="M 180 30 L 180 5"/>
          <path d="M 330 85 L 330 50 L 330 20"/>
          <path d="M 90 135 L 90 175"/>
          <path d="M 290 130 L 290 175"/>
        </g>
        {/* Glowing nodes */}
        <g filter={`url(#${id}-glow)`}>
          {[
            [80, 50, "#5eead4"], [110, 30, "#22d3ee"], [170, 30, "#c084fc"],
            [195, 55, "#5eead4"], [270, 85, "#22d3ee"], [330, 85, "#c084fc"],
            [60, 110, "#22d3ee"], [90, 135, "#5eead4"], [290, 130, "#c084fc"],
            [320, 105, "#5eead4"], [90, 175, "#c084fc"], [115, 200, "#5eead4"],
            [280, 180, "#22d3ee"], [310, 205, "#c084fc"], [180, 30, "#5eead4"],
            [330, 50, "#22d3ee"], [290, 175, "#5eead4"], [240, 130, "#c084fc"],
          ].map(([x, y, col], i) => {
            const dark = isDark;
            return (
              <g key={i}>
                <circle cx={x} cy={y} r={dark ? "6" : "4"} fill={col} opacity={dark ? .35 : .18}/>
                <circle cx={x} cy={y} r="2" fill={col}/>
              </g>
            );
          })}
        </g>
      </svg>
      {/* Logo on top */}
      <div style={{ position: "relative", zIndex: 1 }}>
        <V3Logo size={logoSize} asIcon={asIcon}/>
      </div>
    </div>
  );
}

// ── NMPlayButton: control circular minimal ───────────────────────────────────
// Fondo neutro acorde al tema, borde sutil, sombra suave, ícono play/pause minimal.
// Cuando se le pasa `color`, el play se rellena de ese color (para gradient bg context).
function NMPlayButton({ icon = "play", size = 56, onClick, color = null }) {
  const { c, isDark } = useV3Theme();
  const fg = color || c.text;
  // En contexto con fondo gradient (player de actividades), permitimos override de fondo
  const useNeutralBg = !color || color === c.text;
  return (
    <button onClick={onClick} style={{
      width: size, height: size,
      borderRadius: 999,
      background: useNeutralBg
        ? (isDark ? "rgba(30, 41, 65, .85)" : "#ffffff")
        : "rgba(255,255,255,.18)",
      border: `1px solid ${
        useNeutralBg
          ? (isDark ? "rgba(94,234,212,.20)" : "rgba(15,23,42,.08)")
          : "rgba(255,255,255,.3)"
      }`,
      boxShadow: isDark
        ? "0 0 0 4px rgba(94,234,212,.06), 0 8px 18px -6px rgba(0,0,0,.5)"
        : "0 1px 2px rgba(15,23,42,.08), 0 6px 14px -4px rgba(15,23,42,.10)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      cursor: "pointer",
      color: fg,
      transition: "all .2s ease",
      padding: 0,
    }}>
      <div style={{ marginLeft: icon === "play" ? size * 0.04 : 0, display: "inline-flex" }}>
        <NMIcon name={icon} size={Math.round(size * 0.42)} color={fg} filled/>
      </div>
    </button>
  );
}

// ── NMRingWithPlay: combina ring grande + play button centrado ───────────────
// Helper para usar en pantallas con sesión (respiración, timer, mini-sesión).
function NMRingWithPlay({ pct = 65, size = 200, stroke = null, ringTone = "gradient",
                          playIcon = "play", onPlay, label = null, sublabel = null }) {
  const { c, isDark } = useV3Theme();
  const strokeW = stroke || Math.max(6, Math.round(size / 24));
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <V3Ring pct={pct} size={size} stroke={strokeW}/>
      {/* Play button centered */}
      <div style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        gap: 6,
      }}>
        <NMPlayButton icon={playIcon} size={Math.round(size * 0.32)} onClick={onPlay}/>
        {label && (
          <div style={{ fontSize: 11, fontWeight: 600, color: c.text2, marginTop: 4 }}>{label}</div>
        )}
        {sublabel && (
          <div style={{ fontSize: 10, color: c.text3 }}>{sublabel}</div>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { NMLogoNeural, NMPlayButton, NMRingWithPlay });
