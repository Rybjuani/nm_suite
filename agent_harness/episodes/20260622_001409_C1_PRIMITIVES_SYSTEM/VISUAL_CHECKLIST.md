# Visual Checklist - C1-PRIMITIVES-SYSTEM

Decision: `PASS_FOR_CLUSTER_SCOPE`

## Checklist

| Item | Before | After | Resultado visual |
|---|---|---|---|
| Tabs `pill` no usan CTA verde para navegacion secundaria | `qa/_captures_c1_primitives_before/suite-dbt-library-light-960x600.png` | `qa/_captures_c1_primitives_after/suite-dbt-library-light-960x600.png` | PASS: familias DBT se ven como chips, no barras primarias. |
| Tabs `seg` conservan seleccion visible sin bloquear como CTA | `qa/_captures_c1_primitives_before/suite-dbt-library-dark-960x600.png` | `qa/_captures_c1_primitives_after/suite-dbt-library-dark-960x600.png` | PASS: Biblioteca queda activa con superficie/borde, no bloque solido. |
| Filtro local Avisos converge con gramatica `seg` | `qa/_captures_c1_primitives_before/suite-avisos-light-960x600.png` | `qa/_captures_c1_primitives_after/suite-avisos-light-960x600.png` | PASS: "Todos" deja de ser bloque verde y queda pill suave. |
| Badges/chips pequenos renderizan pills reales | `qa/_captures_c1_primitives_before/suite-actividades-light-960x600.png` | `qa/_captures_c1_primitives_after/suite-actividades-light-960x600.png` | PASS: tags de categoria y badge "Hecho" dejan de leerse como rectangulos duros. |
| Checkboxes de Rutina no regresan | `qa/_captures_c1_primitives_before/suite-rutina-light-960x600.png` | `qa/_captures_c1_primitives_after/suite-rutina-light-960x600.png` | PASS: checked/unchecked siguen legibles y alineados. |
| Empty state base no regresa | `qa/_captures_c1_primitives_before/suite-timer-empty-light-960x600.png` | `qa/_captures_c1_primitives_after/suite-timer-empty-light-960x600.png` | PASS: primitive estable; composicion de pantalla se difiere a C3. |
| Dark theme mantiene contraste y forma | `qa/_captures_c1_primitives_before/suite-avisos-dark-960x600.png` | `qa/_captures_c1_primitives_after/suite-avisos-dark-960x600.png` | PASS: estado activo visible sin saturacion primaria. |

## Cierre de cluster

- Captura focal before/after: completa para 5 recipes x 2 temas.
- Checklist visual trazado: completo en este archivo.
- P0/P1: no hay P0 en C1; P1 resueltos o diferidos segun tabla del episodio.
- Ruff/tests/probe: solo apoyo tecnico, no criterio unico de cierre.
- ZIP final: no generado.
- Capturas 98: no generadas.

## Handoff

Siguiente cluster en orden: `C2-SUITE-CRITICAL`.

Atencion para C2:

- DBT Biblioteca aun tiene barras de categoria superpuestas a titulos de cards.
- DBT Historial debe eliminarse segun plan.
- Registro TCC, Onboarding y DBT Cierre requieren fixes propios de pantalla.
