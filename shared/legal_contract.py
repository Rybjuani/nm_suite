"""legal_contract.py — Contrato legal único y fuente de verdad para el consentimiento."""

import hashlib

from shared.version import NM_VERSION

SUITE_VERSION = NM_VERSION
DISCLAIMER_VERSION = "legal-2026-05-16"
PRIVACY_VERSION = "privacy-2026-05-16"

CONSENT_SCOPE = (
    "db_local,sync_autorizado,revision_profesional,visualizacion_neuromood_hub,"
    "ia_asistida_profesional,constancia_legal_remota"
)

LEGAL_DISCLAIMER_TEXT = """NeuroMood Suite es una herramienta digital complementaria de bienestar, registro emocional, organización de hábitos y apoyo personal. Su finalidad es facilitar el registro de estados de ánimo, rutinas, pensamientos, actividades, recordatorios y ejercicios de autorregulación.

NeuroMood Suite no realiza diagnósticos médicos, psicológicos ni psiquiátricos; no indica tratamientos; no reemplaza la evaluación, seguimiento, criterio ni intervención de profesionales de la salud habilitados; y no debe utilizarse como único medio para tomar decisiones sobre la salud física o mental.

NeuroMood Suite puede utilizarse como apoyo complementario dentro de un proceso acompañado por profesionales habilitados. El seguimiento, interpretación clínica, evaluación de riesgo, indicación terapéutica, derivación o toma de decisiones corresponden exclusivamente al profesional tratante.

Los contenidos, registros, gráficos, sugerencias, recordatorios o actividades incluidos en NeuroMood Suite tienen carácter orientativo, educativo y de apoyo complementario. Su interpretación y uso quedan bajo responsabilidad del paciente y, cuando corresponda, del profesional tratante.

NeuroMood Suite no es un servicio de emergencias. En caso de crisis emocional intensa, riesgo de autolesión, ideación suicida, emergencia médica, empeoramiento significativo del estado de salud o cualquier situación de peligro, el paciente debe comunicarse inmediatamente con un servicio de emergencias, guardia médica, línea local de asistencia, familiar responsable o profesional de confianza.

NeuroMood Suite puede tratar datos personales y datos sensibles vinculados al bienestar emocional, hábitos, registros de ánimo, pensamientos, actividades, recordatorios y uso de módulos. El paciente acepta que NeuroMood Suite pueda almacenar estos datos localmente y sincronizarlos, cuando corresponda, para el funcionamiento de NeuroMood Suite, continuidad de uso, visualización de evolución y, si existe vinculación profesional, revisión desde NeuroMood Hub por parte del profesional o equipo autorizado.

Cuando exista vinculación con un profesional, los registros sincronizados podrán ser utilizados en NeuroMood Hub para organizar información, preparar preguntas, generar borradores o sintetizar contexto mediante funciones asistidas por inteligencia artificial. La IA no realiza diagnósticos, evaluaciones clínicas, detección de riesgo, indicaciones terapéuticas, prescripciones, decisiones clínicas ni seguimiento autónomo del paciente. Todo contenido generado por IA debe ser revisado, validado y corregido por el profesional antes de utilizarse.

El paciente acepta que NeuroMood Suite registre una constancia técnica de esta aceptación, localmente y en un registro remoto seguro, incluyendo fecha, cuenta asociada, versión de NeuroMood Suite, versión del Instalador Suite, versión del aviso legal, versión de privacidad y hash del texto aceptado. Esta constancia podrá ser consultada por el profesional o equipo autorizado desde NeuroMood Hub únicamente para verificar el estado del consentimiento.

Estos datos se utilizarán exclusivamente para el funcionamiento de NeuroMood Suite, la continuidad de uso, la sincronización autorizada, la visualización profesional cuando corresponda, la constancia legal de consentimiento y el acompañamiento complementario dentro del entorno correspondiente. Su tratamiento deberá realizarse conforme a la política de privacidad aplicable, con medidas razonables de seguridad, confidencialidad y control de acceso.

La autenticación puede requerir email y contraseña mediante el sistema de cuenta de NeuroMood Suite. La contraseña no debe guardarse localmente en texto plano. El paciente se compromete a no compartir su cuenta, contraseña ni equipo con terceros no autorizados.

Al continuar, el paciente declara haber leído, comprendido y aceptado este aviso legal, el consentimiento de uso, el tratamiento de datos personales y sensibles, la sincronización autorizada cuando corresponda, la visualización profesional desde NeuroMood Hub y la generación de una constancia auditable de consentimiento."""


def legal_hash(text: str) -> str:
    """Calcula hash SHA256 del texto."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


DISCLAIMER_TEXT_HASH = legal_hash(LEGAL_DISCLAIMER_TEXT)
PRIVACY_TEXT_HASH = legal_hash(f"{PRIVACY_VERSION}|{CONSENT_SCOPE}|{DISCLAIMER_TEXT_HASH}")
