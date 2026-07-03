# Diff Confinement Report

Verdict: PASS
Base: `HEAD^`
Touched files: 4
Prohibited files: 0
Hunks outside block: 0

## Files
- PERMITTED: `VISUAL_REPAIR_HANDOFF.md`
  - ok: `@@ -100,0 +101,16 @@ checklist from this promotion.`
- PERMITTED: `app/modules/dbt_qt.py`
  - ok: `@@ -94,4 +94,5 @@ _DBT_FAMILY_COLOR_KEYS = {`
  - ok: `@@ -468 +469 @@ class _SkillCard(NMCard):`
  - ok: `@@ -478,2 +479,2 @@ class _SkillCard(NMCard):`
  - ok: `@@ -486 +487 @@ class _SkillCard(NMCard):`
  - ok: `@@ -499 +500 @@ class _SkillCard(NMCard):`
  - ok: `@@ -501 +502 @@ class _SkillCard(NMCard):`
  - ok: `@@ -505 +506 @@ class _SkillCard(NMCard):`
  - ok: `@@ -507 +508,2 @@ class _SkillCard(NMCard):`
  - ok: `@@ -511 +513 @@ class _SkillCard(NMCard):`
  - ok: `@@ -521,2 +523,2 @@ class _SkillCard(NMCard):`
  - ok: `@@ -527 +529 @@ class _SkillCard(NMCard):`
  - ok: `@@ -560 +562 @@ class _SkillCard(NMCard):`
  - ok: `@@ -890,3 +892,3 @@ class _PracticeModalScrim(QWidget):`
  - ok: `@@ -1254,0 +1257 @@ class ModuloDBT(NMModule):`
  - ok: `@@ -1261,3 +1264,3 @@ class ModuloDBT(NMModule):`
  - ok: `@@ -1265 +1268 @@ class ModuloDBT(NMModule):`
  - ok: `@@ -1290 +1293 @@ class ModuloDBT(NMModule):`
- PERMITTED: `tests/test_component_visual_contract.py`
  - ok: `@@ -813,0 +814 @@ def test_dbt_cards_match_mockup_family_bar_contract(qtbot) -> None:`
  - ok: `@@ -847 +848,2 @@ def test_dbt_cards_match_mockup_family_bar_contract(qtbot) -> None:`
  - ok: `@@ -849,8 +851,10 @@ def test_dbt_cards_match_mockup_family_bar_contract(qtbot) -> None:`
- PERMITTED: `tests/test_dbt_visual_contract.py`
  - ok: `@@ -71,0 +72,4 @@ def test_dbt_library_has_16_formal_practices(qtbot, monkeypatch) -> None:`
  - ok: `@@ -211,2 +215,5 @@ def test_dbt_skill_card_title_uses_serif_font(qtbot, monkeypatch) -> None:`
