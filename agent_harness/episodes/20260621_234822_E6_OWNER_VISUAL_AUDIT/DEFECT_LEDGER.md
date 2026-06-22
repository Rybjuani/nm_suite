# Defect Ledger - UI V2 Owner Visual Audit

Baseline read-only sobre `main` @ `85d8f48386e55ffdbfb2a90ddc2a02cd64bf844e`.
Fuente inicial: listado owner adjunto `pasted-text.txt`.

E5 (`c0c692e`) no se revierte: queda registrado como cierre tecnico exitoso pero cierre
visual fallido. El error del gate fue aceptar existencia de capturas/tests verdes como
aprobacion compositiva.

## Severidad

- **P0:** solape, corte, contenido ilegible, pantalla revivida contra decision owner o gate invalido.
- **P1:** jerarquia/densidad/gramatica visual incorrecta con impacto claro.
- **P2:** refinamiento premium, balance, contraste o consistencia menor.

## Defectos

| ID | Pantalla / estado / tema | Severidad | Evidencia | Causa visual probable | Cluster asignado | Criterio de aceptacion visual |
|---|---|---|---|---|---|---|
| V2-P0-001 | DBT Biblioteca / library / dark+light | P0 | owner: barras pisan titulos de `Observar y describir`, `Mente sabia`, `STOP`, `Autocalma`, `Verificar`, `DEAR MAN` | z-order/layout interno de `_SkillCard`; barra horizontal no reserva altura antes del titulo | C2-SUITE-CRITICAL | Ninguna barra toca texto; titulo completo legible en todas las cards y temas. |
| V2-P0-002 | Registro TCC / step1 emotion / dark+light | P0 | owner: iconos superpuestos con textos en Ansiedad, Culpa, Verguenza, Soledad y Otro | grid/card de emociones sin separacion icono-label; sizing fijo o padding insuficiente | C2-SUITE-CRITICAL | Icono y label tienen cajas separadas; ningun pixel del icono invade texto en hover/selected/default. |
| V2-P0-003 | Onboarding / default+error / dark+light | P0 | owner: `Privacidad y consentimiento` corta texto legal | card legal con alto insuficiente; input/footer consumen alto en 520x600 | C2-SUITE-CRITICAL | Texto legal real visible/legible sin corte roto; si hay scroll local, debe ser deliberado y claro. |
| V2-P0-004 | Hub Pacientes / list / dark+light | P0 | owner: ultima fila `Laura Gomez` parcialmente fuera de card/viewport | altura/densidad de filas y viewport interno mal calculados | C4-HUB-CRITICAL | Todas las filas visibles dentro del panel o scroll con corte limpio; no hay fila parcialmente recortada. |
| V2-P0-005 | DBT / history tab / dark+light | P0 | owner: DBT Historial revivido y pantalla empty innecesaria | decision owner actual contradice V2 anterior; tab extra aumenta superficie rota | C2-SUITE-CRITICAL | Tab/pantalla Historial eliminados del flujo UI V2, recetas/targets/tests alineados. |
| V2-P0-006 | Gate E5 / all screens / both | P0 | owner: E5 declaro `sin deuda accionable` con defectos visibles | gate confundio captura tecnica con aprobacion visual; checklist humano no trazado | C0-GATE-HARNESS | Cierre visual requiere checklist trazado; tests/probe/capture solo son soporte tecnico. |
| V2-P1-001 | Hub Detalle Activacion / plan activacion / dark+light | P1 | owner: `Exportar PDF` parece ghost/dark, no primary/brand | variante de boton incorrecta para accion principal | C4-HUB-CRITICAL | `Exportar PDF` tiene jerarquia primary/brand clara sin romper copy ni seam PDF. |
| V2-P1-002 | Hub Detalle Activacion / plan activacion / dark+light | P1 | owner: `Resumen IA` sin icono visible y peso raro | accion IA usa pill generica sin iconografia/jerarquia | C4-HUB-CRITICAL | Accion IA muestra icono y peso visual secundario claro, integrado al toolbar. |
| V2-P1-003 | Hub Detalle Activacion / plan tabs / dark+light | P1 | owner: tab activo demasiado dominante y labels chicos/apretados | tabs/subtabs no usan densidad Hub compact refinada | C4-HUB-CRITICAL | Tabs legibles, compactos, con activo visible pero no dominante. |
| V2-P1-004 | Hub Detalle Activacion / form left / dark+light | P1 | owner: placeholders truncados, inputs angostos, selects grandes, CTA pegado | grid/form de Activacion no distribuye ancho/alto | C4-HUB-CRITICAL | Formulario no trunca placeholders clave; controles alineados y con aire consistente. |
| V2-P1-005 | Hub Detalle Activacion / IA autofill / dark+light | P1 | owner: `Completar con IA` parece ghost barato/desconectado | boton fuera de flujo y sin agrupacion visual | C4-HUB-CRITICAL | CTA IA queda integrado al formulario con rol secundario reconocible. |
| V2-P1-006 | Hub Detalle Activacion / right empty panel / dark+light | P1 | owner: `Sin actividades personalizadas aun.` flota sin empty state | empty state no usa primitiva/sistema comun | C4-HUB-CRITICAL | Empty panel con icono, titulo/copy y jerarquia consistente con sistema. |
| V2-P1-007 | Hub Detalle Activacion / cards / dark+light | P1 | owner: cards Hub con radio/sombra diferentes | panel/form usan estilos locales divergentes | C4-HUB-CRITICAL | Cards del cluster comparten radio, sombra, borde y densidad con Hub. |
| V2-P1-008 | Hub Pacientes / header badge / dark+light | P1 | owner: badge `5 pacientes` rectangular, no pill canonica | badge/list counter no usa NMBadge/pill | C4-HUB-CRITICAL | Badge tiene radio pill, padding y tono suave canonico. |
| V2-P1-009 | Hub Pacientes / list scroll / dark+light | P1 | owner: scroll interno visible/agresivo y lista cortada | scrollbar visible por overflow/densidad no resuelta | C4-HUB-CRITICAL | Scrollbar no domina la card; si aparece, no corta filas ni rompe composicion. |
| V2-P1-010 | Hub Pacientes / columns / dark+light | P1 | owner: mail, animo 7d y uso no alinean con headers | columnas sin grid fijo/alineacion visual | C4-HUB-CRITICAL | Headers y celdas alinean por columna; lectura escaneable. |
| V2-P1-011 | Hub Pacientes / rows / dark+light | P1 | owner: mucho aire y aun corta abajo | densidad vertical inconsistente | C4-HUB-CRITICAL | Filas compactas sin recorte, ritmo vertical estable. |
| V2-P2-001 | Hub Pacientes / avatars / dark+light | P2 | owner: avatares cromaticamente inconsistentes | colores de avatar fuera de paleta/tokens | C4-HUB-CRITICAL | Avatares usan paleta ADN y no compiten con datos. |
| V2-P1-012 | Hub Pacientes / header action / dark+light | P1 | owner: `Textos globales` flota en header | accion secundaria no esta jerarquizada | C4-HUB-CRITICAL | Accion secundaria queda alineada al header con peso y posicion claros. |
| V2-P1-013 | Hub Pacientes / usage rings / dark+light | P1 | owner: circulos de uso demasiado pesados | ring size/stroke compite con tabla | C4-HUB-CRITICAL | Rings integrados a columna, menor peso visual que identidad/nombre. |
| V2-P1-014 | Actividades / filters / dark+light | P1 | owner: filtros de categoria rectangulares, no pills/fchips | filtros usan tabs/cuadrados legacy | C3-SUITE-MODULES | Filtros son fchips/pills canonicos en default/selected/hover. |
| V2-P1-015 | Actividades / cards / dark+light | P1 | owner: cards desbalanceadas en alturas/paddings | card layout no normaliza tracks internos | C3-SUITE-MODULES | Cards con altura, padding y posiciones internas uniformes. |
| V2-P1-016 | Actividades / category badges / dark+light | P1 | owner: badges `Fisica`, `Placer`, `Social`, `Maestria` rectangulares | badge local no usa forma/peso canonico | C3-SUITE-MODULES | Badges con forma pill y tono del sistema. |
| V2-P1-017 | Actividades / done action / dark+light | P1 | owner: botones `Hecho` no coinciden con mockup | boton pegado al borde y no pill | C3-SUITE-MODULES | `Hecho` parece accion pill/badge integrada, no bloque rectangular. |
| V2-P1-018 | Actividades / result buttons / dark+light | P1 | owner: `No pude / Hice` no respetan jerarquia | variantes/tamanos desbalanceados | C3-SUITE-MODULES | `Hice` y `No pude` tienen jerarquia clara y alineacion consistente. |
| V2-P2-002 | Actividades / footer / dark+light | P2 | owner: `4 actividades sugeridas` pegado al borde inferior | padding inferior insuficiente | C3-SUITE-MODULES | Footer respira y no queda en borde de card/viewport. |
| V2-P2-003 | Actividades / card icons / dark+light | P2 | owner: iconos de cards chicos y sueltos | icon chips sin tamano/contorno consistente | C3-SUITE-MODULES | Iconos se sienten como chips consistentes con card. |
| V2-P1-019 | DBT Biblioteca / top tabs / dark+light | P1 | owner: `Ahora / Biblioteca / Historial` enormes y pesados | tab bar usa escala/altura excesiva | C2-SUITE-CRITICAL | Navegacion DBT compacta/refinada; sin Historial si se elimina. |
| V2-P1-020 | DBT Biblioteca / category filters / dark+light | P1 | owner: categorias DBT rectangulares, no pills | filtros familiares no usan fchips | C2-SUITE-CRITICAL | Categorias son fchips/pills legibles y consistentes. |
| V2-P1-021 | DBT Biblioteca / grid / dark+light | P1 | owner: grid irregular, tercera columna incompleta, scrollbar visible | grid tracks/scroll area no resueltos | C2-SUITE-CRITICAL | Grid regular sin scrollbar agresivo ni columna incompleta perceptual. |
| V2-P2-004 | DBT Biblioteca / descriptions / dark | P2 | owner: descripcion con bajo contraste en dark | color de texto secundario demasiado apagado | C2-SUITE-CRITICAL | Descripcion legible en dark sin volverse primaria. |
| V2-P2-005 | DBT Biblioteca / meta row / dark+light | P2 | owner: `2 min / Practica guiada` demasiado pegada | spacing y alineacion de meta insuficientes | C2-SUITE-CRITICAL | Meta row con aire y alineacion fina en todas las cards. |
| V2-P1-022 | DBT Cierre / modal / dark+light | P1 | owner: modal funcional pero no premium | matriz y controles no usan escala visual refinada | C2-SUITE-CRITICAL | Modal conserva funcion, con escala/padding/jerarquia premium coherente. |
| V2-P1-023 | DBT Cierre / 0-10 ratings / dark+light | P1 | owner: circulos 0-10 grandes y pesados | botones de rating sobredimensionados | C2-SUITE-CRITICAL | Ratings caben sin dominar la modal y mantienen click targets razonables. |
| V2-P1-024 | DBT Cierre / result buttons / dark+light | P1 | owner: botones de evaluacion compiten con CTA | variantes/tamanos sin jerarquia | C2-SUITE-CRITICAL | Evaluacion secundaria no compite con `Guardar practica`. |
| V2-P2-006 | DBT Cierre / overlay / dark+light | P2 | owner: overlay oscurece demasiado | scrim opacity demasiado fuerte | C2-SUITE-CRITICAL | Fondo se atenue sin endurecer visualmente la pantalla. |
| V2-P1-025 | Onboarding / checkbox / dark+light | P1 | owner: checkbox barato/desalineado; check no visible en light | checkbox no usa contrato visual/refinado | C2-SUITE-CRITICAL | Checkbox visible, alineado e integrado a card legal. |
| V2-P1-026 | Onboarding / checkbox row / dark+light | P1 | owner: fila de checkbox pegoteada fuera de card | agrupacion visual incorrecta | C2-SUITE-CRITICAL | Fila legal/checkbox pertenece visualmente al bloque de consentimiento. |
| V2-P1-027 | Onboarding / footer / dark+light | P1 | owner: footer comprimido y cerca de botones | layout vertical de 520x600 mal distribuido | C2-SUITE-CRITICAL | Footer y acciones no se solapan ni se sienten comprimidos. |
| V2-P1-028 | Onboarding / bottom buttons / dark+light | P1 | owner: jerarquia confusa entre Crear cuenta/Iniciar sesion | variantes primary/secondary no diferenciadas | C2-SUITE-CRITICAL | Accion primaria y secundaria se distinguen sin competir. |
| V2-P1-029 | Onboarding / inputs / dark+light | P1 | owner: inputs demasiado grandes fuerzan compresion | control height/spacing no adaptado a 520x600 | C2-SUITE-CRITICAL | Inputs conservan legibilidad sin sacrificar consentimiento/footer. |
| V2-P2-007 | Onboarding / focus / dark | P2 | owner: focus ring visible sin intencion clara | estado inicial enfocado parece error/activo | C2-SUITE-CRITICAL | Estado inicial no comunica error ni focus accidental. |
| V2-P2-008 | Onboarding / brand lockup / dark+light | P2 | owner: marca no igualmente refinada entre temas | spacing/contraste lockup inconsistente | C2-SUITE-CRITICAL | Lockup se integra con igual calidad en ambos temas. |
| V2-P1-030 | Registro TCC / top spacing / dark+light | P1 | owner: stepper deja demasiado vacio arriba | vertical rhythm entre chrome y card | C2-SUITE-CRITICAL | Top spacing equilibrado; card principal sube sin aplastar contenido. |
| V2-P1-031 | Registro TCC / emotion grid / dark+light | P1 | owner: grid rigido, cajas grandes | grid options no usa gramatica clinica refinada | C2-SUITE-CRITICAL | Opciones se sienten cards/pills refinadas, no cajas rigidas. |
| V2-P1-032 | Registro TCC / selected emotion / dark+light | P1 | owner: Ansiedad selected con linea vertical rara | selected state local inconsistente | C2-SUITE-CRITICAL | Selected state coherente con sistema, sin artefactos verticales raros. |
| V2-P1-033 | Registro TCC / intensity slider / dark+light | P1 | owner: slider ocupa ancho excesivo y domina | ancho maximo/jerarquia del slider sin control | C2-SUITE-CRITICAL | Slider visible pero subordinado al flujo, con ancho contenido. |
| V2-P2-009 | Registro TCC / next button / dark+light | P2 | owner: `Siguiente` demasiado ancho/pesado | CTA width/variant poco refinado | C2-SUITE-CRITICAL | CTA mantiene jerarquia sin parecer app basica. |
| V2-P1-034 | Rutina / checkboxes / dark+light | P1 | owner: checkboxes baratos, no `.rt-cb` refinado | checkbox local/generic | C3-SUITE-MODULES | Checks se ven como componente de rutina refinado y alineado. |
| V2-P1-035 | Rutina / new task input+add / dark+light | P1 | owner: boton agregar parece blob circular/cuadrado | add button no usa boton/icon button canonico | C3-SUITE-MODULES | Input y add button forman control integrado y canonico. |
| V2-P1-036 | Rutina / time-section cards / dark+light | P1 | owner: alturas inconsistentes; Noche distinta | layout por franja sin constraints uniformes | C3-SUITE-MODULES | Franjas tienen gramatica y alturas consistentes segun contenido. |
| V2-P1-037 | Rutina / progress header / dark+light | P1 | owner: header de progreso alto y pesado | hero/header sobredimensionado | C3-SUITE-MODULES | Header comunica progreso sin consumir viewport excesivo. |
| V2-P1-038 | Rutina / completed rows / dark+light | P1 | owner: tachados/checkboxes no alinean | baseline/alineacion de row states | C3-SUITE-MODULES | Texto, checkbox y tachado alinean en Mañana/Tarde/Noche. |
| V2-P1-039 | Rutina empty / empty light / light | P1 | owner: empty demasiado arriba, vacio inferior enorme | empty state sin centrado optico | C3-SUITE-MODULES | Empty state centrado visualmente con composicion final estable. |
| V2-P1-040 | Timer / normal / dark+light | P1 | owner: gigantismo, card y ring dominan viewport | ring/card escala excesiva | C3-SUITE-MODULES | Timer mantiene foco sin ocupar casi todo el viewport. |
| V2-P1-041 | Timer / presets / dark+light | P1 | owner: presets `5/25/45 min` no comparten gramatica | chips/presets usan estilo propio | C3-SUITE-MODULES | Presets usan gramatica chip/pill consistente. |
| V2-P1-042 | Timer / category chips / dark+light | P1 | owner: `Lectura` parece CTA principal; chips sobredimensionados | filtros/categorias usan variante equivocada | C3-SUITE-MODULES | Categorias se leen como filtros/presets, no CTA primary. |
| V2-P1-043 | Timer empty / empty light / light | P1 | owner: empty usa card gigante; incoherente con Rutina/Avisos | empty states no comparten patron | C3-SUITE-MODULES | Empty Timer usa patron comun; copy producto permitido si layout correcto. |
| V2-P1-044 | Avisos empty / tabs / dark+light | P1 | owner: tabs `Todos/Activos/Hoy` rectangulares | tabs/fchips legacy | C3-SUITE-MODULES | Tabs son pills/tabs redondeadas del sistema. |
| V2-P1-045 | Avisos empty / search+tabs / dark+light | P1 | owner: search no integrado con tabs | toolbar/list header no agrupado | C3-SUITE-MODULES | Search y tabs forman header coherente. |
| V2-P1-046 | Avisos empty / empty copy/layout / dark+light | P1 | owner: empty rigido; copy difiere del mockup | empty state sin patron comun; copy producto puede conservarse | C3-SUITE-MODULES | Empty visual consistente; copy de producto aceptado si composicion coincide. |
| V2-P2-010 | Avisos empty / icon/spacing / dark+light | P2 | owner: icon correcto en intencion pero espaciado/tamano inconsistente | icon/spacing no normalizado | C3-SUITE-MODULES | Icon y spacing empatan con empty states comunes. |
| V2-P1-047 | Sistema / buttons / all affected | P1 | owner: al menos tres familias de botones | variantes locales duplicadas y badges usados como botones | C1-PRIMITIVES-SYSTEM | Botones convergen en variantes canonicas; excepciones documentadas por pantalla. |
| V2-P1-048 | Sistema / tabs chips / all affected | P1 | owner: al menos tres familias de tabs/chips | tabs/fchips/segmented divergentes | C1-PRIMITIVES-SYSTEM | Tabs/chips usan gramatica unica por rol: tabs, fchips, badges. |
| V2-P1-049 | Sistema / cards / all affected | P1 | owner: cards no comparten densidad | padding/radius/shadow locales divergentes | C1-PRIMITIVES-SYSTEM | Cards por densidad Suite/Hub comparten radio, shadow, padding base. |
| V2-P1-050 | Sistema / empty states / all affected | P1 | owner: empty states sin patron unico | algunos con card, otros sin card; centrado/texto/iconos divergentes | C1-PRIMITIVES-SYSTEM | Empty states tienen patron comun y variantes documentadas. |
| V2-P1-051 | Sistema / theme quality / light+dark | P1 | owner: dark mas consistente; light empties baratos/vacios | composicion light con lienzo crema sin estructura | C1-PRIMITIVES-SYSTEM | Light/dark comparten calidad compositiva; sin lienzo vacio accidental. |
| V2-P0-007 | QA harness / visual closure / all | P0 | owner: tests midieron existencia/estructura, no composicion visual | contratos de bajo nivel no cubren solape/proporcion/percepcion | C0-GATE-HARNESS | Ningun cluster cierra con tests verdes solamente; checklist visual requerido. |
| V2-P0-008 | QA harness / final review / all | P0 | owner: `barrido visual tecnico` subjetivo y no verificable | falta evidencia trazada de revision humana | C0-GATE-HARNESS | Revision visual final produce checklist auditable por pantalla/tema/estado. |

## Pantallas no mencionadas por owner pero pendientes de auditoria C5

No se registran como defectos hasta tener evidencia focal. `C5-MISSING-SCREENS-AUDIT`
debe revisar al menos: Home, Animo, Respiracion, DBT Ahora, DBT STOP, Registro TCC pasos
2/3/success, Onboarding error/recuperar acceso, Hub Detalle resumen/registros/timer/rutina,
Textos globales, Actividades estados filtered/empty/marked, Rutina add/all-completed,
Timer running/paused/presets, Avisos activos/search/completed.

## Estado

Todos los defectos estan **Open** al cierre de este episodio read-only.
