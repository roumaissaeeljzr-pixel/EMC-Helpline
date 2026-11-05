"""
diagnose_section_title_corpus.py

Script de DIAGNOSTIC UNIQUEMENT -- analyse TOUTES les lignes du
corpus (FR + AR, tous documents) correspondant à
is_section_title() (^\\d+\\.\\s*\\S+), et classe chacune en :

    A. vrai titre de section (suivi du bloc structuré
       Métadonnées / Thème / Intention CamemBERT, exactement le
       même test que celui déjà utilisé par build_document_sections()
       dans build_index.py -- "CAS STRUCTURÉ")
    B. candidat sans ce bloc structuré (probable étape numérotée
       interne à une procédure, à confirmer visuellement via le
       contexte affiché)

IMPORTANT SUR LA SÉCURITÉ DE CE SCRIPT :
Il NE FAIT PAS `import rag.build_index`, car ce module exécute du
code au chargement (chargement du modèle d'embedding, et
potentiellement la construction/écriture de l'index plus loin dans
le fichier). Pour rester strictement en LECTURE SEULE, ce script
DUPLIQUE fidèlement -- copié tel quel depuis le build_index.py fourni
le 15/08 -- uniquement les fonctions pures nécessaires (aucune
écriture de fichier, aucun appel FAISS, aucun modèle d'embedding
chargé) :

    canonical_document_name, canonical_pdf_name, resolve_source_files
    clean_text, clean_arabic_text
    extract_pdf_pages, extract_txt_pages, extract_source
    extract_theme, extract_intent
    is_metadata_label, is_theme_line, is_section_title

Ce script n'écrit AUCUN fichier de sortie autre que ce que tu
rediriges toi-même (> diagnostic.txt). Il ne touche ni chunks.json,
ni emc_faiss.index, ni le corpus, ni build_index.py, ni retriever.py,
ni generator.py.

Lancement (depuis 06_Development, venv activé, donc avec pypdf déjà
installé) :

    python diagnose_section_title_corpus.py > diagnostic_section_title.txt
"""

import re
import unicodedata
from pathlib import Path
from typing import Any

from pypdf import PdfReader


# ============================================================
# DUPLICATION FIDÈLE DES FONCTIONS PURES DE build_index.py
# (copiées telles quelles, aucune modification de logique)
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "documents"
FR_DOCUMENTS_DIR = DOCUMENTS_DIR / "fr"
AR_DOCUMENTS_DIR = DOCUMENTS_DIR / "ar"


def canonical_document_name(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_ar"):
        stem = stem[:-3]
    return stem + path.suffix.lower()


def canonical_pdf_name(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_ar"):
        stem = stem[:-3]
    return stem + ".pdf"


def resolve_source_files() -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = {"fr": [], "ar": []}

    if FR_DOCUMENTS_DIR.is_dir():
        result["fr"] = sorted(FR_DOCUMENTS_DIR.glob("*.pdf"))
    else:
        result["fr"] = sorted(DOCUMENTS_DIR.glob("*.pdf"))

    if not AR_DOCUMENTS_DIR.is_dir():
        return result

    txt_files = sorted(AR_DOCUMENTS_DIR.glob("*.txt"))
    pdf_files = sorted(AR_DOCUMENTS_DIR.glob("*.pdf"))

    txt_stems = {path.stem.removesuffix("_ar") for path in txt_files}

    result["ar"].extend(txt_files)

    for pdf_path in pdf_files:
        base_stem = pdf_path.stem.removesuffix("_ar")
        if base_stem not in txt_stems:
            result["ar"].append(pdf_path)

    result["ar"] = sorted(result["ar"])

    return result


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


def is_metadata_label(line: str) -> bool:
    value = line.strip().lower()
    return value in {
        "métadonnées",
        "metadonnées",
        "metadata",
        "البيانات الوصفية",
    }


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


def is_section_title(line: str) -> bool:
    line = line.strip()
    if re.match(r"^\d+\.\s*\S+", line):
        return True
    return False


# ============================================================
# DIAGNOSTIC : PARCOURS DE TOUT LE CORPUS
# ============================================================

def main() -> None:

    files_by_language = resolve_source_files()

    total_matches = 0
    true_titles_with_block = []      # Catégorie A confirmée
    candidates_without_block = []    # Catégorie B à confirmer visuellement

    for language, paths in files_by_language.items():

        for path in paths:

            document_name = canonical_pdf_name(path)

            pages = extract_source(path, language)

            for page_data in pages:

                page_number = page_data["page"]

                lines = [
                    line.strip()
                    for line in page_data["text"].splitlines()
                    if line.strip() and line.strip() != "---"
                ]

                for i, line in enumerate(lines):

                    if not is_section_title(line):
                        continue

                    total_matches += 1

                    has_structured_block = (
                        i + 2 < len(lines)
                        and is_metadata_label(lines[i + 1])
                        and is_theme_line(lines[i + 2])
                    )

                    context_before = lines[i - 1] if i - 1 >= 0 else None
                    context_after = lines[i + 1 : i + 4]

                    entry = {
                        "document": document_name,
                        "source_file": path.name,
                        "language": language,
                        "page": page_number,
                        "line": line,
                        "context_before": context_before,
                        "context_after": context_after,
                    }

                    if has_structured_block:
                        true_titles_with_block.append(entry)
                    else:
                        candidates_without_block.append(entry)

    # ============================================================
    # RÉSUMÉ FACTUEL
    # ============================================================

    print("=" * 78)
    print("RÉSUMÉ FACTUEL")
    print("=" * 78)
    print(f"Nombre total de lignes matchant ^\\d+\\.\\s*\\S+           : {total_matches}")
    print(f"  -> avec bloc structuré Métadonnées/Thème/Intention   : {len(true_titles_with_block)}  (catégorie A -- vrais titres confirmés)")
    print(f"  -> SANS ce bloc structuré                             : {len(candidates_without_block)}  (catégorie B candidate -- à confirmer visuellement ci-dessous)")
    print()

    # Répartition par document / langue
    from collections import Counter

    print("Répartition catégorie A (vrais titres) par document/langue :")
    counter_a = Counter((e["document"], e["language"]) for e in true_titles_with_block)
    for (doc, lang), count in sorted(counter_a.items()):
        print(f"  {doc} [{lang}] : {count}")
    print()

    print("Répartition catégorie B (candidats sans bloc) par document/langue :")
    counter_b = Counter((e["document"], e["language"]) for e in candidates_without_block)
    for (doc, lang), count in sorted(counter_b.items()):
        print(f"  {doc} [{lang}] : {count}")
    print()

    # ============================================================
    # EXEMPLES -- CATÉGORIE A (vrais titres confirmés)
    # ============================================================

    print("=" * 78)
    print(f"EXEMPLES -- CATÉGORIE A (vrais titres, {len(true_titles_with_block)} au total, jusqu'à 15 affichés)")
    print("=" * 78)
    for entry in true_titles_with_block[:15]:
        print(f"[{entry['document']} / {entry['language']} / page {entry['page']}]")
        print(f"  ligne              : {entry['line']!r}")
        print(f"  contexte suivant   : {entry['context_after']}")
        print()

    # ============================================================
    # EXEMPLES -- CATÉGORIE B (candidats sans bloc, à confirmer)
    # ============================================================

    print("=" * 78)
    print(f"EXEMPLES -- CATÉGORIE B (SANS bloc structuré, {len(candidates_without_block)} au total, TOUS affichés pour inspection manuelle)")
    print("=" * 78)
    for entry in candidates_without_block:
        print(f"[{entry['document']} / {entry['language']} / page {entry['page']}]")
        print(f"  contexte précédent : {entry['context_before']!r}")
        print(f"  ligne              : {entry['line']!r}")
        print(f"  contexte suivant   : {entry['context_after']}")
        print()

    print("=" * 78)
    print("FIN DU DIAGNOSTIC -- copier/coller la sortie complète pour analyse.")
    print("=" * 78)
    print()
    print("NOTE DE LECTURE : la catégorie B n'est PAS automatiquement égale à")
    print("'étape numérotée interne'. Chaque entrée doit être confirmée")
    print("visuellement : un vrai titre de section rédigé sans bloc de")
    print("métadonnées structuré (variante non standard) tomberait aussi ici,")
    print("et ne devrait alors pas être traité comme une étape interne.")


if __name__ == "__main__":
    main()