"""
test_section_segmentation.py

TEST LOCAL DE SEGMENTATION -- lecture seule, aucune écriture, aucun
chargement de modèle d'embedding, aucun appel FAISS.

Vérifie le comportement de la correction proposée pour
is_section_title() / build_document_sections() / la nouvelle
document_has_structured_sections(), sur les 4 scénarios demandés,
directement sur les documents réels du corpus (lus, jamais modifiés).

Ce script duplique fidèlement les fonctions pures nécessaires
(copiées depuis la version CORRIGÉE de build_index.py) plutôt que de
faire `import rag.build_index`, qui exécuterait tout le pipeline
d'indexation (chargement du modèle d'embedding, et l'écriture de
chunks.json / emc_faiss.index plus loin dans ce fichier) comme effet
de bord du simple import.

Lancement (depuis 06_Development, venv activé) :

    python test_section_segmentation.py
"""

import re
import unicodedata
from pathlib import Path
from typing import Any

from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "documents"
FR_DOCUMENTS_DIR = DOCUMENTS_DIR / "fr"
AR_DOCUMENTS_DIR = DOCUMENTS_DIR / "ar"


# ============================================================
# FONCTIONS DUPLIQUÉES (version CORRIGÉE)
# ============================================================

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\x00", " ")
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


ARABIC_DIACRITICS_PATTERN = re.compile(
    r"[\u0610-\u061A"
    r"\u064B-\u065F"
    r"\u0670"
    r"\u06D6-\u06DC"
    r"\u06DF-\u06E8"
    r"\u06EA-\u06ED]"
)


def clean_arabic_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = ARABIC_DIACRITICS_PATTERN.sub("", text)
    return clean_text(text)


def extract_pdf_pages(path: Path, language: str) -> list[dict[str, Any]]:
    reader = PdfReader(str(path))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = clean_arabic_text(text) if language == "ar" else clean_text(text)
        if not text:
            continue
        pages.append({"page": page_number, "text": text, "language": language})
    return pages


def extract_txt_pages(path: Path, language: str) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    text = clean_arabic_text(text) if language == "ar" else clean_text(text)
    if not text:
        return []
    return [{"page": 1, "text": text, "language": language}]


def extract_source(path: Path, language: str) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_pages(path, language)
    if suffix == ".txt":
        return extract_txt_pages(path, language)
    raise ValueError(f"Format non supporté : {path}")


def is_metadata_label(line: str) -> bool:
    value = line.strip().lower()
    return value in {
        "métadonnées",
        "metadonnées",
        "metadata",
        "البيانات الوصفية",
    }


def extract_theme(text: str) -> str | None:
    patterns = [
        r"Th[eè]me\s*:\s*([^\n\r]+)",
        r"الموضوع\s*:\s*([^\n\r]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None


def extract_intent(text: str) -> str | None:
    patterns = [
        r"Intention\s+CamemBERT\s*:\s*([^\n\r]+)",
        r"Intention\s+CamemBERT\s+associ[eé]e\s*:\s*([^\n\r]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            intent = match.group(1).strip()
            if intent:
                return intent
    return None


def is_theme_line(line: str) -> bool:
    line = line.strip()
    patterns = [
        r"^Th[eè]me\s*:\s*\S+",
        r"^الموضوع\s*:\s*\S+",
    ]
    return any(
        re.match(pattern, line, flags=re.IGNORECASE) is not None
        for pattern in patterns
    )


# --- VERSION CORRIGÉE ---

def is_section_title(line: str) -> bool:
    line = line.strip()
    if re.match(r"^\d+\.\s+\S+", line):  # \s+ au lieu de \s*
        return True
    return False


def document_has_structured_sections(pages: list[dict[str, Any]]) -> bool:
    for page_data in pages:
        lines = [
            line.strip()
            for line in page_data["text"].splitlines()
            if line.strip() and line.strip() != "---"
        ]
        for i, line in enumerate(lines):
            if (
                i + 2 < len(lines)
                and is_metadata_label(lines[i + 1])
                and is_theme_line(lines[i + 2])
            ):
                return True
    return False


def build_document_sections(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:

    document_is_structured = document_has_structured_sections(pages)

    sections = []
    current_lines: list[str] = []
    current_page: int | None = None
    current_language: str | None = None

    def save_current_section() -> None:
        nonlocal current_lines, current_page, current_language
        text = "\n".join(current_lines).strip()
        if text:
            sections.append(
                {"page": current_page or 1, "language": current_language, "text": text}
            )
        current_lines = []
        current_page = None
        current_language = None

    for page_data in pages:

        page_number = int(page_data["page"])
        page_language = str(page_data["language"])

        lines = [
            line.strip()
            for line in page_data["text"].splitlines()
            if line.strip() and line.strip() != "---"
        ]

        i = 0
        while i < len(lines):

            line = lines[i]

            # CAS STRUCTURÉ
            if (
                i + 2 < len(lines)
                and is_metadata_label(lines[i + 1])
                and is_theme_line(lines[i + 2])
            ):
                if current_lines:
                    save_current_section()
                current_page = page_number
                current_language = page_language
                current_lines = [line, lines[i + 1], lines[i + 2]]
                i += 3
                continue

            # THÈME DIRECT
            if is_theme_line(line):
                if current_lines:
                    save_current_section()
                current_page = page_number
                current_language = page_language
                current_lines = [line]
                i += 1
                continue

            # TITRE NUMÉROTÉ -- conditionné (CORRECTION)
            if is_section_title(line) and not document_is_structured:
                if current_lines:
                    save_current_section()
                current_page = page_number
                current_language = page_language
                current_lines = [line]
                i += 1
                continue

            # TEXTE NORMAL
            if current_page is None:
                current_page = page_number
            if current_language is None:
                current_language = page_language
            current_lines.append(line)
            i += 1

    if current_lines:
        save_current_section()

    return sections


# ============================================================
# RÉSOLUTION DES FICHIERS SOURCES CIBLÉS
# ============================================================

def find_document(name_fragment: str, language: str) -> Path | None:
    directory = FR_DOCUMENTS_DIR if language == "fr" else AR_DOCUMENTS_DIR
    if not directory.is_dir():
        return None
    for path in sorted(directory.glob("*")):
        if name_fragment in path.name and path.suffix.lower() in (".pdf", ".txt"):
            return path
    return None


def marker_status(sections: list[dict[str, Any]], marker: str) -> str:
    """
    Retourne :
      "NOUVELLE_SECTION" si `marker` démarre une section (sections[i]["text"].startswith(marker))
      "MEME_SECTION"     si `marker` apparaît à l'intérieur d'une section sans la démarrer
      "INTROUVABLE"      si `marker` n'apparaît dans aucune section
    """
    for section in sections:
        text = section["text"]
        if text.startswith(marker):
            return "NOUVELLE_SECTION"
    for section in sections:
        text = section["text"]
        if marker in text:
            return "MEME_SECTION (contenu à l'intérieur d'une section existante)"
    return "INTROUVABLE"


def find_all_sections_by_intent(
    sections: list[dict[str, Any]],
    target_intent: str,
) -> list[tuple[int, dict[str, Any], str | None]]:
    """
    Localise TOUTES les sections dont l'intention CALCULÉE
    (extract_intent) correspond à target_intent -- sans filtrer sur
    le thème, car celui-ci peut être rédigé en arabe (donc ne jamais
    contenir le mot français "procédure").

    Retourne une liste de (index, section, theme_calculé) -- s'il y a
    plusieurs correspondances, l'appelant doit désambiguïser à partir
    de données réelles du corpus, jamais en devinant une traduction.
    """
    matches = []
    for index, section in enumerate(sections):
        intent = extract_intent(section["text"])
        if intent == target_intent:
            theme = extract_theme(section["text"])
            matches.append((index, section, theme))
    return matches


def dump_all_sections(sections: list[dict[str, Any]]) -> None:
    print("  --- Dump complet de toutes les sections produites ---")
    for index, section in enumerate(sections):
        intent = extract_intent(section["text"])
        theme = extract_theme(section["text"])
        preview = section["text"][:120].replace("\n", " \\n ")
        print(f"  [{index}] intent={intent!r} theme={theme!r}")
        print(f"        texte (120 premiers caractères) : {preview!r}")
    print()


def run_test_ar_procedure(
    label: str,
    document_fragment: str,
    step_markers: list[str],
) -> bool:
    """
    Test A-AR : localise les sections d'intention "Cyberharcèlement"
    et "Sextorsion" par leur métadonnée CALCULÉE uniquement (jamais
    par un thème/titre arabe deviné -- le thème peut être rédigé en
    arabe). Si l'intention correspond à plusieurs sections, la
    désambiguïsation utilise exclusivement des données réelles déjà
    fournies (ici : les deux étapes arabes réelles de la procédure
    Cyberharcèlement) -- jamais une traduction inventée.

    En cas d'échec de quelque nature que ce soit, affiche
    automatiquement le dump complet de toutes les sections produites
    (index / intent / theme / 120 premiers caractères), pour permettre
    l'analyse sans nouvel aller-retour.
    """
    print("=" * 78)
    print(label)
    print("=" * 78)

    path = find_document(document_fragment, "ar")
    if path is None:
        print(f"  DOCUMENT INTROUVABLE pour le fragment {document_fragment!r} en ar")
        print()
        return False

    print(f"  Fichier : {path.name}")

    pages = extract_source(path, "ar")
    sections = build_document_sections(pages)

    print(f"  Nombre de sections produites : {len(sections)}")
    print()

    all_pass = True
    cyber_index: int | None = None
    cyber_section: dict[str, Any] | None = None

    # ============================================================
    # Localisation de la section Cyberharcèlement
    # ============================================================

    cyber_matches = find_all_sections_by_intent(sections, "Cyberharcèlement")

    if not cyber_matches:
        print("  [FAIL] Aucune section avec intent='Cyberharcèlement'")
        all_pass = False

    elif len(cyber_matches) == 1:
        cyber_index, cyber_section, cyber_theme = cyber_matches[0]
        print(f"  [OK  ] Section 'Cyberharcèlement' localisée sans ambiguïté (index {cyber_index}, theme={cyber_theme!r})")
        print(f"         début du texte : {cyber_section['text'][:80]!r}")

    else:
        print(f"  {len(cyber_matches)} sections trouvées avec intent='Cyberharcèlement' -- désambiguïsation nécessaire :")
        for idx, sec, theme in cyber_matches:
            preview = sec["text"][:120].replace("\n", " \\n ")
            print(f"    [{idx}] theme={theme!r}")
            print(f"          texte (120 premiers caractères) : {preview!r}")

        # Désambiguïsation via les étapes réelles déjà fournies (pas
        # une traduction devinée) : la bonne section est celle qui
        # contient les DEUX étapes arabes réelles de la procédure.
        candidates_with_steps = [
            (idx, sec, theme)
            for idx, sec, theme in cyber_matches
            if all(marker in sec["text"] for marker in step_markers)
        ]

        if len(candidates_with_steps) == 1:
            cyber_index, cyber_section, cyber_theme = candidates_with_steps[0]
            print(f"  [OK  ] Désambiguïsée via les étapes réelles fournies -> index {cyber_index}")
        else:
            print(f"  [FAIL] Désambiguïsation impossible ({len(candidates_with_steps)} candidat(s) contenant les deux étapes)")
            all_pass = False

    print()

    # ============================================================
    # Vérification des étapes internes
    # ============================================================

    if cyber_section is not None:
        for marker in step_markers:
            is_inside = marker in cyber_section["text"]
            starts_own_section = any(s["text"].startswith(marker) for s in sections)
            ok = is_inside and not starts_own_section
            symbol = "OK  " if ok else "FAIL"
            if not ok:
                all_pass = False
            status = (
                "PAS nouvelle section (à l'intérieur de la section Cyberharcèlement)"
                if ok else
                ("nouvelle section propre (INCORRECT)" if starts_own_section else "INTROUVABLE dans la section Cyberharcèlement")
            )
            print(f"  [{symbol}] {marker!r:65} -> {status}")
        print()

    # ============================================================
    # Localisation de la section Sextorsion (distincte)
    # ============================================================

    sextorsion_matches = find_all_sections_by_intent(sections, "Sextorsion")

    if not sextorsion_matches:
        print("  [FAIL] Aucune section avec intent='Sextorsion'")
        all_pass = False

    elif len(sextorsion_matches) == 1:
        sextorsion_index, sextorsion_section, sextorsion_theme = sextorsion_matches[0]
        is_distinct = cyber_index is None or sextorsion_index != cyber_index
        symbol = "OK  " if is_distinct else "FAIL"
        if not is_distinct:
            all_pass = False
        print(f"  [{symbol}] Section 'Sextorsion' localisée sans ambiguïté (index {sextorsion_index}, theme={sextorsion_theme!r}), "
              f"{'distincte de Cyberharcèlement -> nouvelle section confirmée' if is_distinct else 'PROBLÈME : identique à Cyberharcèlement'}")
        print(f"         début du texte : {sextorsion_section['text'][:80]!r}")

    else:
        print(f"  {len(sextorsion_matches)} sections trouvées avec intent='Sextorsion' -- désambiguïsation nécessaire :")
        for idx, sec, theme in sextorsion_matches:
            preview = sec["text"][:120].replace("\n", " \\n ")
            print(f"    [{idx}] theme={theme!r}")
            print(f"          texte (120 premiers caractères) : {preview!r}")

        distinct_candidates = [
            (idx, sec, theme) for idx, sec, theme in sextorsion_matches
            if cyber_index is None or idx != cyber_index
        ]

        if len(distinct_candidates) == 1:
            idx, sec, theme = distinct_candidates[0]
            print(f"  [OK  ] Une seule section 'Sextorsion' distincte de Cyberharcèlement -> index {idx}")
        else:
            print(f"  [FAIL] Désambiguïsation impossible pour Sextorsion sans donnée supplémentaire "
                  f"({len(distinct_candidates)} candidat(s) distincts) -- aucune traduction devinée, "
                  f"merci de fournir un extrait réel de cette section pour trancher")
            all_pass = False

    print()

    if not all_pass:
        print("  Échec détecté -- dump complet pour analyse :")
        dump_all_sections(sections)

    return all_pass


def run_test(label: str, document_fragment: str, language: str, cases: list[tuple[str, str]]) -> bool:

    print("=" * 78)
    print(label)
    print("=" * 78)

    path = find_document(document_fragment, language)
    if path is None:
        print(f"  DOCUMENT INTROUVABLE pour le fragment {document_fragment!r} en {language}")
        print()
        return False

    print(f"  Fichier : {path.name}")

    pages = extract_source(path, language)
    sections = build_document_sections(pages)

    print(f"  Nombre de sections produites : {len(sections)}")
    print()

    all_pass = True
    for marker, expected in cases:
        status = marker_status(sections, marker)
        is_new_section = status == "NOUVELLE_SECTION"
        actual = "nouvelle section" if is_new_section else (
            "PAS nouvelle section" if "MEME_SECTION" in status else "INTROUVABLE"
        )
        ok = (actual == expected) or (expected == "PAS nouvelle section" and "MEME_SECTION" in status)
        symbol = "OK  " if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  [{symbol}] {marker!r:55} -> {actual}  (attendu: {expected})")

    print()
    return all_pass


def main() -> None:

    fr_results = []
    ar_results = []

    # ============================================================
    # FR
    # ============================================================

    fr_results.append(run_test(
        "A. 02_signalement_et_procedures FR",
        "02_signalement_et_procedures",
        "fr",
        [
            ("6. Cyberharcèlement — procédure", "nouvelle section"),
            ("1. Qualifier la situation", "PAS nouvelle section"),
            ("2. Protéger les comptes", "PAS nouvelle section"),
            ("7. Sextorsion — procédure", "nouvelle section"),
        ],
    ))

    fr_results.append(run_test(
        "B. 03_cadre_juridique_maroc_final",
        "03_cadre_juridique_maroc_final",
        "fr",
        [
            ("1. Objet du document", "nouvelle section"),
            ("3. Cyberharcèlement", "nouvelle section"),
        ],
    ))

    fr_results.append(run_test(
        "C. 05_accompagnement_et_conversation",
        "05_accompagnement_et_conversation",
        "fr",
        [
            ("1. Objectif", "nouvelle section"),
            ("7. Situation d'urgence", "nouvelle section"),
        ],
    ))

    fr_results.append(run_test(
        "D. 04_ressources_et_orientation_final",
        "04_ressources_et_orientation_final",
        "fr",
        [
            ("2511.ma", "PAS nouvelle section"),
        ],
    ))

    # ============================================================
    # AR
    # ============================================================

    ar_results.append(run_test_ar_procedure(
        "A-AR. 02_signalement_et_procedures AR "
        "(localisation par intent calculé uniquement, thème arabe non filtré)",
        "02_signalement_et_procedures",
        step_markers=[
            "1. توصيف الوضعية : نوع المحتوى، المنصة المعنية، تكرار الوقائع.",
            "2. حماية الحسابات المعنية (الإعدادات الخاصة، إدارة جهات الاتصال).",
        ],
    ))

    ar_results.append(run_test(
        "B-AR. 03_cadre_juridique_maroc_final AR",
        "03_cadre_juridique_maroc_final",
        "ar",
        [
            ("1. غرض الوثيقة", "nouvelle section"),
            ("3. التحرش الإلكتروني — الإطار القانوني في المغرب", "nouvelle section"),
        ],
    ))

    ar_results.append(run_test(
        "C-AR. 05_accompagnement_et_conversation AR",
        "05_accompagnement_et_conversation",
        "ar",
        [
            ("1. هدف المرافقة", "nouvelle section"),
            ("7. حالة الطوارئ", "nouvelle section"),
        ],
    ))

    # ============================================================
    # RÉSUMÉ FINAL
    # ============================================================

    print("=" * 78)
    print("RÉSUMÉ FINAL")
    print("=" * 78)

    if all(fr_results):
        print("FR : tous les scénarios passent")
    else:
        print("FR : AU MOINS UN SCÉNARIO A ÉCHOUÉ")

    if all(ar_results):
        print("AR : tous les scénarios passent")
    else:
        print("AR : AU MOINS UN SCÉNARIO A ÉCHOUÉ")

    print("=" * 78)

    if all(fr_results) and all(ar_results):
        print("TOUS LES SCÉNARIOS FR + AR PASSENT")
    else:
        print("AU MOINS UN SCÉNARIO A ÉCHOUÉ -- voir le détail ci-dessus. "
              "Ne pas modifier build_index.py ni réindexer avant d'avoir "
              "analysé la cause du/des échec(s).")
    print("=" * 78)


if __name__ == "__main__":
    main()