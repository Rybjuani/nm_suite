# Plan de coherencia visual — NeuroMood Suite + Hub

## Regla Anti Alfombra

Este documento no puede volver a resumirse perdiendo deuda. Los puntos S01–S21 y H01–H21 son el inventario canónico hasta que una captura claro/oscuro y una revisión visual los marquen como cerrados.

Todo plan derivado debe conservar una matriz de cobertura con cuatro estados posibles: `abierto`, `parcial`, `cerrado` o `descartado con evidencia`. Si una fase corrige solo tokens/componentes compartidos, no puede declararse como cierre de las pantallas consumidoras. Si una captura técnica pasa pero la pantalla sigue visualmente rota, el estado sigue siendo `parcial` o `abierto`.

Regla operativa: ninguna respuesta puede decir “plan implementado” sin enumerar qué S/H quedaron cerrados y cuáles siguen abiertos.

## Estado de cobertura actual

Este estado evita confundir una pasada sistémica con cierre total:

- `parcial`: sistema compartido de botones, tabs/filtros, badges, scrollbars, diálogos PIN, TCC, Timer, Activación, Avisos, Plan terapéutico, IA, Resumen, Registros, Dashboard, Pacientes, Personalización y editores.
- `abierto`: tipografía canónica completa, familia total de cards/paneles, eliminación real de todos los nested scrolls, Home, Respiración, Rutina, Evolución, recuperación de acceso S17, todos los estados vacíos Suite, Registros Hub en todas sus variantes y cierre pantalla por pantalla S01–S21/H01–H21.
- `cerrado`: no declarar cierre global todavía. Solo pueden cerrarse puntos individuales cuando una captura claro/oscuro y revisión manual lo acrediten.

## Alcance actual

Este documento es autónomo y está preparado para el repositorio limpio de NeuroMood. No depende de documentación anterior, sistemas de agentes, memorias, referencias visuales eliminadas ni artefactos históricos.

El alcance funcional actual se conserva. El trabajo debe concentrarse en la coherencia visual de las dos aplicaciones PyQt6:

- **NeuroMood Suite:** aplicación para pacientes y usuarios.
- **NeuroMood Hub:** aplicación para profesionales y equipos.

El agente debe inspeccionar el repositorio actual y localizar por sí mismo las fuentes vigentes del sistema visual, los componentes compartidos, sus consumidores y las herramientas de QA. El plan no fija rutas ni estructuras internas: deben comprobarse contra el árbol actual antes de modificar código.

Los hallazgos S01–S21 y H01–H21 son un inventario de deuda visual a comprobar contra el código actual y capturas frescas. Ningún punto puede cerrarse por el nombre de un componente, por comentarios del código ni por asumir que algo ya es canónico: debe verificarse su comportamiento real.

## Objetivo

Eliminar la sensación de producto ensamblado por piezas mediante un sistema compartido pequeño, consistente y comprobable. Primero deben corregirse tokens y componentes reutilizables; después, sus consumidores. No se deben introducir cambios funcionales, de navegación, persistencia, seguridad, autenticación, base de datos o sincronización salvo que sean imprescindibles para corregir un defecto visual directo.

## Veredicto global

El proyecto no está visualmente destruido ni requiere empezar de cero. El problema principal es que **conviven demasiadas reglas locales**: cada pantalla parece haber resuelto botones, cards, estados, densidad, scroll, jerarquía y espaciado por separado. El resultado es un producto reconocible como NeuroMood, pero con sensación de ensamblaje por piezas.

La incoherencia no proviene principalmente de los colores. Proviene de cinco fracturas:

1. **Densidad opuesta:** Suite tiene superficies demasiado grandes y vacías; Hub concentra demasiados controles y textos pequeños.
2. **Componentes equivalentes no equivalentes:** acciones, pills, tabs, inputs, cards y estados cambian de tamaño, borde, relleno y efecto según la pantalla.
3. **Jerarquía inestable:** títulos, subtítulos, labels, mensajes y métricas no conservan una escala constante.
4. **Scroll y recorte sin estrategia:** aparecen scrollbars demasiado visibles, varias dentro de una misma pantalla, contenido pegado al borde o secciones comprimidas.
5. **Estados interactivos sin canon:** algunos elementos tienen sombra, glow, hover o gradiente; otros equivalentes son texto plano o cajas sin reacción.

No conviene seguir corrigiendo pantalla por pantalla. Primero hay que cerrar un sistema visual pequeño y obligatorio; luego sustituir las variantes locales.

---

# Gaps visuales transversales

## 1. Botones

- Existen botones lavanda llenos, lavanda con gradiente, teal llenos, outline oscuro, ghost, texto sin caja e iconos circulares; no siempre cambia la importancia de la acción.
- La misma jerarquía primaria usa alturas y anchos diferentes según la pantalla.
- `Guardar`, `Siguiente`, `Agregar`, `Aplicar`, `Completar` y `Verificar` no comparten una presencia común.
- Algunas acciones secundarias parecen enlaces; otras, botones completos.
- Hay botones habilitados visualmente antes de completar formularios.
- Los botones de icono carecen de una superficie y tamaño de interacción uniformes.
- Los efectos de hover, sombra y glow aparecen en unos controles y desaparecen en otros.

**Reparación:** definir únicamente cuatro familias: Primario, Secundario, Ghost y Peligro; tres tamaños; una altura canónica por tamaño; mismos estados hover, pressed, focus y disabled.

## 2. Pills, chips, badges y tabs

- Categorías, filtros, estados clínicos, tabs, contadores y acciones comparten formas de cápsula muy similares.
- El usuario no puede distinguir con rapidez qué se pulsa, qué informa y qué representa un estado.
- Los activos cambian entre fondo lavanda, fondo teal, borde fino, texto coloreado o gradiente.
- En Hub se acumulan tabs principales, subtabs y badges en la misma zona.
- Las pills pequeñas tienen texto demasiado reducido y áreas de clic estrechas.

**Reparación:** separar visualmente cuatro roles: tabs de navegación, filtros, badges de estado y chips seleccionables. Nunca reutilizar exactamente la misma apariencia para los cuatro.

## 3. Cards

- Conviven cards grandes redondeadas, paneles rectos, paneles laterales oscuros, cards anidadas y filas con borde.
- Algunas tienen sombra y elevación; otras equivalentes solo borde; otras ninguna separación.
- Los radios y paddings cambian demasiado.
- En Suite las cards suelen ser demasiado altas; en Hub demasiado densas.
- Hay muchas “cajas dentro de cajas”, especialmente en Ajustes, Personalización y Plan terapéutico.

**Reparación:** limitar a tres tipos: card de contenido, card interactiva y panel de formulario. Misma esquina, borde, sombra y padding por tipo.

## 4. Campos de texto y formularios

- Inputs de login, PIN, Timer, Personalización y Plan terapéutico tienen anchos, alturas y radios distintos.
- Algunos usan borde brillante al foco; otros casi no muestran foco.
- Los placeholders hacen de label en varias pantallas y desaparecen al escribir.
- Textareas muy pequeñas ocupan cards enormes.
- Contadores de caracteres cambian de ubicación y formato.
- Formularios del Hub usan controles diminutos dentro de paneles amplios.

**Reparación:** labels permanentes, altura única de input, dos alturas de textarea, foco canónico y contador siempre en el mismo lugar.

## 5. Tipografía

- Newsreader/serif aparece en títulos clínicos, métricas y algunos subtítulos, pero no sigue una regla completamente predecible.
- Hay pantallas con título serif prominente y otras con el mismo nivel jerárquico en sans pequeño.
- Los textos secundarios, estados, ejes y ayudas son demasiado pequeños.
- El peso semibold se usa tanto en títulos como en microetiquetas, aplanando la jerarquía.
- Se mezclan mayúsculas, sentence case, voseo y tuteo.
- Nombres propios aparecen en minúscula.

**Reparación:** cinco estilos canónicos: Display, Título de página, Título de card, Body y Caption. No crear tamaños intermedios locales.

## 6. Alineación y espaciado

- Las líneas izquierdas de títulos, inputs, cards y botones no siempre coinciden.
- Hay márgenes externos diferentes entre módulos de la Suite.
- Botones de pie se anclan unas veces a la derecha, otras al centro y otras quedan flotando.
- Suite desperdicia espacio vertical; Hub comprime demasiado.
- Varias pantallas tienen contenido solo en el tercio superior y un vacío enorme debajo.

**Reparación:** una grilla base de 8 px y presupuestos de padding cerrados: 16, 24 y 32. Prohibir valores locales arbitrarios salvo excepción documentada.

## 7. Scrollbars

- Son uno de los elementos que más abaratan la percepción del producto.
- Se ven barras claras o tramadas, muy pegadas al borde, con contraste excesivo.
- Hay scrollbars internas dentro de panels que ya viven en una vista desplazable.
- En Hub aparecen varias zonas desplazables simultáneas.
- Algunas barras sugieren que el contenido está cortado aunque apenas falten unos píxeles.

**Reparación:** una sola scrollbar vertical por vista siempre que sea posible; ancho discreto, thumb suave, track transparente y margen interno. Evitar nested scroll.

## 8. Efectos y movimiento

- Home usa elevación y hover en cards; listas, paneles y módulos similares son completamente planos.
- Algunos focos tienen halo fuerte, otros apenas borde.
- Lavanda, teal y glow se usan sin una jerarquía consistente.
- Animaciones y pulsos aparecen en bloqueo, respiración, timer y home sin una configuración común.

**Reparación:** canon de interacción único: hover leve, pressed corto, focus visible, transición 120–160 ms y reducción de movimiento.

## 9. Colores y semántica

- Teal sirve como marca, enlace, éxito, categoría y estado activo.
- Lavanda sirve como acción primaria, selección, tab y decoración.
- Amarillo aparece como estado, categoría y advertencia.
- El mismo color puede significar cosas diferentes en pantallas vecinas.

**Reparación:** reservar Primary para acción/selección, Teal para información positiva o marca secundaria, Success para éxito confirmado, Warning para advertencia real y Danger para error.

## 10. Suite vs. Hub

- Suite intenta ser calma y respirada, pero termina vacía y con texto diminuto.
- Hub intenta ser eficiente, pero termina apretado y con demasiadas capas de navegación.
- Ambos comparten paleta, pero no una densidad ni una gramática de componentes suficientemente coherente.

**Reparación:** misma familia visual, con dos densidades deliberadas: Patient Comfortable y Professional Compact. No dos sistemas distintos.

---

# Suite — auditoría por pantalla

## S01 — Configuración inicial / Acceso

- Ventana mucho más angosta que el resto de la Suite; parece otra aplicación.
- Logo, título serif/itálico y campos sans generan tres voces visuales.
- El bloque legal es excesivamente denso y la scrollbar clara rompe completamente la estética.
- Los tres controles inferiores tienen jerarquías incompatibles: link teal, botón outline y botón lavanda.
- El contenido queda apretado verticalmente y pegado al borde inferior.
- Checkbox y texto legal no poseen suficiente aire.

## S02 — Inicio sin registros

- Hero demasiado alto para la cantidad de información.
- `Sin registro hoy` y `Registrar` quedan diminutos y aislados en la esquina.
- Cards muy altas con dos líneas pequeñas arriba y un vacío grande debajo.
- Estado inferior no aparece de manera uniforme en los ocho módulos.
- Chips de categoría parecen acciones clickeables.
- La sombra/elevación de estas cards no se repite en componentes interactivos equivalentes de otros módulos.

## S03 — Termómetro emocional

- El hero y las dos columnas tienen demasiados estilos simultáneos: badge, score, mensaje, gráfico, stats y chips.
- El valor inicial `0` parece un punto real de la escala.
- El gráfico vacío conserva una card grande.
- Las estadísticas derechas son muy bajas y comprimidas frente a la card de entrada izquierda.
- Textos de ejes, leyenda y ayudas son demasiado pequeños.
- Los chips emocionales parecen campos rectangulares y no opciones seleccionables.

## S04 — Guía de respiración

- El panel lateral de historial es recto y rígido, mientras todo el resto usa cards redondeadas.
- Divide la pantalla en dos productos visuales distintos.
- La card principal es enorme y el ejercicio queda concentrado en el centro.
- Los controles inferiores son pequeños comparados con el foco visual.
- Las tres métricas inferiores compiten con la sesión sin aportar jerarquía clara.
- `BPM` parece información biométrica real y visualmente adquiere demasiado peso.

## S05 — TCC: Situación

- Card casi vacía con textarea demasiado baja.
- Botón `Siguiente` flotando en el extremo inferior derecho.
- `Anterior` deshabilitado parece texto perdido.
- Barra de pasos demasiado fina y desconectada del formulario.
- `Registros previos` crea una segunda barra inferior que compite con la navegación.

## S06 — TCC: Emoción

- Tiles de emoción y barra de intensidad pertenecen a dos lenguajes visuales diferentes.
- Preservar una única lectura de intensidad en formato `/10`; no reintroducir porcentajes duplicados.
- Slider demasiado largo y pegado a los bordes de la card.
- Botón `Siguiente` sigue pareciendo disponible antes de elegir.
- Gran vacío inferior sin función.

## S07 — TCC: Pensamiento

- Textarea muy baja y gran área muerta debajo.
- La card del tip terapéutico introduce otro tipo de borde, icono y jerarquía.
- `Posibles distorsiones` queda como microtexto perdido.
- Contador alineado a la izquierda aquí, pero a la derecha en otras pantallas.
- Botón y barra inferior repiten los problemas de S05/S06.

## S08 — TCC: Respuesta

- Campo opcional no está marcado como opcional.
- Card prácticamente vacía.
- `Guardar` ocupa la misma apariencia que `Siguiente`, aunque es una acción final.
- No hay resumen visual previo a confirmar.
- El layout parece una plantilla incompleta, no una etapa final.

## S09 — Checklist sin rutina

- Dos estados vacíos simultáneos dicen esencialmente lo mismo.
- El bloque superior de progreso no aporta valor cuando no hay tareas.
- El mensaje central y la card bloqueada de nota compiten por explicar la ausencia.
- La card inferior ocupa demasiado alto para una única frase.
- El candado introduce una semántica de seguridad en algo que solo está deshabilitado.

## S10 — Activación conductual sin sugerencias

- Desaparecen filtros y estructura que sí existen cuando hay actividades; el módulo cambia demasiado entre estados.
- El estado vacío queda aislado en una superficie completamente desnuda.
- No existe card contenedora ni explicación suficiente.
- Parece una pantalla sin cargar, no un estado deliberado.

## S11 — Temporizador

- Ring grande, controles diminutos y presets todavía más pequeños: escala interna incoherente.
- Campo de actividad, input `min` y botón `OK` no parecen parte del mismo formulario.
- El botón `OK` es mucho más estrecho que cualquier otro botón del sistema.
- Los iconos de control carecen de etiquetas y superficie coherente.
- Historial inferior es una card grande para una sola línea de estado.
- Mucho vacío alrededor del temporizador y apretujamiento en la fila inferior.

## S12 — Recordatorios sin asignaciones

- Filtros permanecen activos aunque no haya contenido.
- El estado vacío flota sobre el fondo, sin card ni relación con filtros.
- La pantalla usa una composición distinta del resto de módulos vacíos.
- No hay indicador visual de notificaciones, sincronización o próxima acción.

## S13 — Evolución sin datos

- Card de gráfico enorme para un mensaje de dos líneas.
- Tabs muy prominentes frente a contenido inexistente.
- Tres cards estadísticas diminutas y comprimidas abajo.
- La jerarquía del título dentro del gráfico es distinta de otros módulos.
- El estado vacío debería reducir la altura del chart y dar prioridad a la explicación.

## S14 — Ajustes

- Demasiadas cajas anidadas para dos opciones.
- `Inicio con Windows` se repite como sección y fila.
- Botón de PIN parece una tercera jerarquía de botón distinta.
- Cierre demasiado pequeño.
- Versión con contraste muy bajo.
- El modal no comparte estructura visual con los diálogos de PIN y recuperación.

## S15 — Nuevo PIN

- Diálogo usa otra escala de espaciado y otra distribución que Ajustes.
- Campo enfocado muestra un halo/borde mucho más fuerte que otros inputs.
- Campos demasiado estrechos para el ancho total.
- Gran vacío antes de las acciones.
- `Cancelar` parece texto y `Guardar PIN` un botón grande; la relación visual es demasiado extrema.
- Botón principal parece activo aun con formulario vacío.

## S16 — Desbloqueo

- Card central tiene otra familia de tamaño, radio y sombras.
- Logo muy pequeño dentro de un halo grande.
- Seis círculos rígidos aunque el PIN pueda variar.
- Falta teclado numérico o un input visible.
- CTA demasiado ancho respecto al resto del contenido.
- Nombre propio sin capitalización.

## S17 — Recuperar acceso

- Es la pantalla menos coherente con el resto de la Suite.
- Ventana demasiado baja y contenido apretado.
- Título, párrafo, input y acciones casi se tocan.
- Botón teal lleno introduce un primario distinto al lavanda del producto.
- `Cancelar` queda flotando sin superficie.
- Falta espacio para errores, carga o mensajes de red.

## S18 y S20 — Activación conductual con sugerencias

- Filtros, cards, chips de categoría, puntos, texto `No pude` y botón `Hice` acumulan demasiados estilos.
- Cards demasiado bajas para su contenido; texto pequeño y aire insuficiente.
- `No pude` es texto plano mientras `Hice` es botón, aunque son dos respuestas del mismo nivel.
- Los tres puntos no explican qué significan.
- Tres cards concentradas arriba y una superficie enorme vacía debajo.
- Historial inferior parece una barra de navegación, no una sección desplegable.

## S19 — Checklist con tareas

- Tres columnas comprimen demasiado títulos, contadores, iconos y checkbox.
- `+ Agregar tarea` es diminuto y se pierde al fondo de cada card.
- Cards internas y card exterior usan bordes muy similares; jerarquía poco clara.
- La nota inferior queda reducida a una franja apretada.
- Botón `Guardar` es mucho más pequeño que otros primarios.
- El conjunto parece dashboard profesional más que pantalla cómoda para paciente.

## S21 — Recordatorios con contenido

- Una única fila ocupa muy poco, dejando casi toda la pantalla vacía.
- `Completar` parece texto, no botón claramente interactivo.
- Badge `Hoy`, metadatos y acción tienen poca separación.
- Card de silencio queda pegada abajo, desconectada del recordatorio.
- Horarios y `Aplicar` son controles demasiado pequeños.
- Se necesita una composición que se adapte a una lista corta sin parecer incompleta.

---

# Hub — auditoría por pantalla

## H01 — Inicio profesional

- Sidebar activa demasiado grande y brillante frente al contenido.
- Cards KPI muy altas para un solo número.
- Card de actividad global y card de uso por módulo tienen densidades opuestas.
- Barras de progreso usan el mismo lavanda sin ayudar a distinguir módulos.
- Textos de módulos y porcentajes son demasiado pequeños.
- El dashboard mezcla tono emocional del saludo con estructura administrativa muy compacta.

## H02 — Pacientes

- Buscador, filtros, contadores y encabezado de tabla están excesivamente juntos.
- Pills de filtro se confunden con badges de estado usados en otras pantallas.
- Tabla tiene texto pequeño y demasiado espacio vertical sin contenido.
- Emails largos quedan visualmente apretados.
- Iconos de acción al final no explican su función.
- Filas y encabezados tienen contraste insuficiente.

## H03 — Personalización global: listado

- Card principal muy grande con filas diminutas.
- Enlaces `Editar textos` casi desaparecen.
- Separadores muy finos y repetitivos generan apariencia de panel técnico antiguo.
- Mucho vacío a la derecha de cada fila.
- Falta una jerarquía más visual por módulo o categoría.

## H04 a H11 — Editores de textos

Problemas repetidos en todas las variantes:

- Panel izquierdo casi negro rompe la continuidad con las cards del Hub.
- Selección teal dentro del panel contradice el lavanda usado como selección global.
- `Volver` aparece como pequeña pill, no como navegación clara.
- Panel derecho enorme para uno o dos campos.
- Inputs y textarea demasiado bajos.
- Contadores son microscópicos.
- `Guardar cambios` queda flotando a media altura, lejos del campo.
- `Restablecer por defecto` parece texto deshabilitado.
- La altura del panel izquierdo cambia según la cantidad de opciones, creando pantallas visualmente inestables.
- Hay demasiadas capas: sidebar global, breadcrumb/titlebar, volver, lista local y editor.

## H12 — Resumen de paciente sin datos

- Header de paciente acumula botón Volver, avatar, rol y tres pills de estado.
- Tabs principales compiten con la navegación lateral.
- Card de gráfico vacío es enorme.
- Cards derechas tienen alturas distintas y contenidos desbalanceados.
- El emoji junto al ánimo rompe el lenguaje iconográfico.
- Datos legales aparecen como bloque técnico y demasiado pequeño.
- Muchas cards con bordes similares sin un foco principal claro.

## H13 — Registros: gráfico

- Scrollbar interna clara y demasiado visible.
- Gráfico queda comprimido dentro de una card que ya está dentro de la vista.
- Leyenda, ejes y resumen usan texto diminuto.
- Botones `Actualizar datos` y `Exportar PDF` no comparten jerarquía clara.
- Indicador circular de porcentaje flota sin suficiente explicación.
- El contenido inferior aparece cortado, dando sensación de viewport mal calculado.

## H14 — Registros: lista emocional

- Fecha de grupo, filas, badges y horas quedan demasiado juntos.
- Cards de registro usan bordes muy leves y parecen filas flotantes.
- Scrollbar nuevamente domina el borde derecho.
- Pills de resultado tienen colores y tamaños distintos a estados similares del resto del Hub.
- El encabezado de fecha no tiene suficiente separación con las filas.

## H15 — Registros de temporizador

- Repite estructura de H14 pero con otra familia de badges verdes.
- Duraciones parecen botones por su forma de pill.
- Filas muy altas para poca información.
- Contenido queda cortado por el scroll interno.
- No existe una columna o grilla clara; todo se lee como texto disperso.

## H16 — Plan terapéutico: recordatorios

- Acumulación máxima de navegación: sidebar, tabs de paciente y subtabs de plan.
- Dos paneles paralelos con campos, previews, botones y enlaces generan sobrecarga.
- Scrollbar interna visible desde el inicio.
- Los botones `Agregar mensaje`, `Asignar alerta` y `Restablecer` no tienen una jerarquía común.
- Labels, placeholders y ayudas son demasiado pequeños.
- Preview de Suite parece una card más y no una previsualización diferenciada.

## H17 — Plan terapéutico: temporizadores

- Panel izquierdo estrecho y formulario apretado; panel derecho enorme y vacío.
- Campos de texto no tienen labels persistentes claros.
- Botón `Agregar` pequeño y aislado.
- Mensaje vacío del panel derecho no ocupa una composición deliberada.
- Scrollbar aparece aunque hay muy poco contenido útil.

## H18 — Plan terapéutico: checklist

- Repite el desequilibrio entre formulario estrecho y panel derecho vacío.
- `Descripción de la tarea`, momento y botón no se alinean con otros formularios.
- Preview inferior comprime texto y añade otra card anidada.
- `Restablecer por defecto` queda perdido arriba a la derecha.
- Las cards asignadas no disponen de una presentación visible en el estado vacío.

## H19 — IA: resumen y acciones

- Banner amarillo introduce un lenguaje visual muy diferente y domina la pantalla.
- Textareas grandes, títulos, botones y cards quedan apilados sin respiración suficiente.
- Scrollbar constante y contenido cortado abajo.
- Botones cambian de ancho y alineación según cada bloque.
- La vista mezcla advertencia, generación, edición y acciones sin una jerarquía de flujo.

## H20 — IA: asignaciones

- Cards y formularios continúan fuera del viewport y obligan a scroll inmediato.
- Selector y botón `Generar borrador` quedan en una fila apretada.
- Botones aparecen en posiciones distintas en cada bloque.
- Mucho borde y poca separación jerárquica.
- La pantalla se siente como un formulario de herramientas internas, no parte del producto terminado.

## H21 — Resumen de paciente con datos

- La vista completa entra con demasiada densidad y scrollbar visible.
- Gráfico, perfil, ánimo, nota, actividad y legal compiten simultáneamente.
- Card legal queda cortada en el borde inferior.
- El gráfico se comprime horizontalmente por la columna derecha.
- Chips del header siguen ocupando demasiado espacio.
- El contenido importante no tiene un orden de lectura suficientemente claro.

---

# Elementos que más producen sensación “Frankenstein”

1. **Teal y lavanda alternándose como selección primaria.**
2. **Botón teal de recuperación frente a primarios lavanda del resto.**
3. **Paneles laterales negros en editores del Hub.**
4. **Scrollbars claras y tramadas dentro de cards oscuras.**
5. **Textareas diminutas dentro de superficies enormes.**
6. **Suite vacía y Hub comprimido, sin densidad intermedia.**
7. **Acciones equivalentes presentadas como botón, link o texto plano.**
8. **Tabs, pills, chips y badges casi indistinguibles.**
9. **Cards con radios, elevación y padding variables.**
10. **Modales que no parecen de la misma familia.**
11. **Microtipografía en demasiados elementos importantes.**
12. **Múltiples scrolls y contenido cortado en vistas del Hub.**

---

# Orden de ejecución

## Fase 1 — Sistema compartido

Trabajar primero sobre las fuentes vigentes del sistema visual compartido y, solo cuando sea necesario, sobre el layout adaptativo.

Cerrar:

1. Cinco roles tipográficos: Display, Título de página, Título de card, Body y Caption.
2. Cuatro familias de botón: Primario, Secundario, Ghost y Peligro.
3. Tres tamaños de botón realmente distintos.
4. Inputs, textareas, labels, foco y contador.
5. Roles visuales separados para navegación, filtros, badges y chips seleccionables.
6. Tres familias de superficie: card de contenido, card interactiva y panel de formulario.
7. Espaciado base de 8 px con 16, 24 y 32 como valores principales.
8. Estados hover, pressed, focus y disabled.
9. Semántica estable de colores.
10. Dos densidades deliberadas: Suite cómoda y Hub compacta.
11. Una scrollbar compartida, discreta y sin nested scroll innecesario.

No agregar un segundo sistema visual ni duplicar componentes equivalentes.

## Fase 2 — Suite S01–S21

Migrar las pantallas de Suite al sistema compartido. Resolver primero componentes reutilizados por varias vistas y después excepciones locales inevitables.

Prioridad:

1. Acceso, onboarding y familia de modales.
2. Home y estados vacíos.
3. Ánimo, Respiración y Timer.
4. Flujo TCC completo.
5. Checklist, Activación, Recordatorios y Evolución.
6. Ajustes, PIN, bloqueo y recuperación.

Preservar el comportamiento funcional vigente, incluida la lectura única de intensidad TCC en formato `/10`.

## Fase 3 — Hub H01–H21

Migrar Hub al mismo sistema con densidad profesional compacta.

Prioridad:

1. Scrollbars, viewport y contenido recortado.
2. Dashboard y Pacientes.
3. Personalización y editores.
4. Resumen y Registros.
5. Plan terapéutico.
6. IA y asignaciones.
7. Modales y estados vacíos.

## Fase 4 — Regresión y evidencia

Usar el harness de capturas vigente para generar evidencia fresca de las pantallas afectadas. Cuando una interacción no pueda demostrarse con captura estática, usar la comprobación runtime vigente o una verificación manual reproducible.

Toda modificación visual debe demostrar:

- captura a 960×600;
- tema claro y oscuro;
- estados activos, seleccionados, disabled y focus cuando correspondan;
- ninguna nueva scrollbar sin justificación;
- ninguna superposición, corte ni contenido fuera del viewport;
- ausencia de nuevos estilos locales equivalentes a componentes compartidos;
- comparación de las pantallas vecinas que consuman el mismo componente;
- pruebas existentes sin regresiones.

Una captura técnica no equivale por sí sola a aprobación visual. El resultado debe abrirse e inspeccionarse.

---

# Prioridades P0 visuales

1. Eliminar nested scroll y scrollbars visualmente invasivas del Hub.
2. Corregir contenido cortado en Registros, Plan terapéutico, IA y Resumen de paciente.
3. Unificar botones, inputs y estados seleccionados.
4. Corregir S17 Recuperar acceso y unificar la familia de modales.
5. Reducir vacíos extremos de TCC, Activación, Recordatorios y Evolución.
6. Subir tamaño y contraste de microtexto.
7. Separar visualmente tabs, filtros, badges y chips.
8. Preservar la intensidad TCC en una única representación `/10`.

# Criterios de cierre

Una fase solo puede considerarse terminada cuando:

- todos sus puntos fueron comprobados contra el código actual;
- los cambios visuales están centralizados siempre que exista más de un consumidor;
- no se introdujeron QSS, tamaños, colores o radios locales equivalentes a reglas compartidas;
- las capturas frescas muestran el resultado correcto en claro y oscuro a 960×600;
- se inspeccionaron visualmente las capturas;
- `py_compile` pasa para todo Python modificado;
- Ruff pasa sobre los archivos modificados;
- la suite de tests existente pasa;
- no hay recortes, superposiciones ni nuevas barras innecesarias;
- no se mezclaron cambios funcionales ajenos al alcance.

No declarar que el producto completo quedó resuelto al cerrar una sola fase.

# Conclusión

La deuda es amplia, pero **es repetitiva**, y eso es una ventaja: no son cientos de problemas independientes. La mayoría nace de unas pocas piezas sin canon. Si se corrigen globalmente botones, inputs, cards, pills/tabs, tipografía, scroll y densidad, una gran parte de las 42 pantallas mejora sin rediseñarlas desde cero.

El mayor riesgo es continuar permitiendo que cada agente “embellezca” una pantalla con soluciones locales. El camino de cierre es el contrario: menos libertad por pantalla, más componentes compartidos y gates visuales estrictos.
