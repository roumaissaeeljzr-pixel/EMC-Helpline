import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


# ============================================================
# 1. CHEMINS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DOCUMENTS_DIR = BASE_DIR / "documents"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"

FR_DOCUMENTS_DIR = DOCUMENTS_DIR / "fr"
AR_DOCUMENTS_DIR = DOCUMENTS_DIR / "ar"

VECTOR_STORE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

SUPPORTED_LANGUAGES = (
    "fr",
    "ar",
)


# ============================================================
# 2. CONFIGURATION DES DOCUMENTS
# ============================================================

DOCUMENT_DEFAULT_INTENTS = {
    "03_cadre_juridique_maroc_final.pdf":
        "Informations juridiques",

    "03_cadre_juridique_maroc_final.txt":
        "Informations juridiques",

    "05_accompagnement_et_conversation.pdf":
        "Accompagnement de la victime",

    "05_accompagnement_et_conversation.txt":
        "Accompagnement de la victime",
}


DOCUMENT_TYPES = {
    "01_cyberviolences_et_typologies.pdf":
        "Définition",

    "01_cyberviolences_et_typologies.txt":
        "Définition",

    "02_signalement_et_procedures.pdf":
        "Procédure",

    "02_signalement_et_procedures.txt":
        "Procédure",

    "03_cadre_juridique_maroc_final.pdf":
        "Informations juridiques",

    "03_cadre_juridique_maroc_final.txt":
        "Informations juridiques",

    "04_ressources_et_orientation_final.pdf":
        "Ressource / orientation",

    "04_ressources_et_orientation_final.txt":
        "Ressource / orientation",

    "05_accompagnement_et_conversation.pdf":
        "Accompagnement conversationnel",

    "05_accompagnement_et_conversation.txt":
        "Accompagnement conversationnel",
}


# ============================================================
# 3. NOM CANONIQUE DU DOCUMENT
# ============================================================

def canonical_document_name(
    path: Path,
) -> str:
    """
    Transforme par exemple :

    01_cyberviolences_et_typologies_ar.txt
        ->
    01_cyberviolences_et_typologies.txt

    Cela permet d'utiliser les mêmes configurations
    pour le français et l'arabe.
    """

    stem = path.stem

    if stem.endswith("_ar"):
        stem = stem[:-3]

    return (
        stem
        + path.suffix.lower()
    )


def canonical_pdf_name(
    path: Path,
) -> str:
    """
    Produit le nom logique du document,
    indépendamment du format source.

    Exemple :
    01_cyberviolences_et_typologies_ar.txt
        ->
    01_cyberviolences_et_typologies.pdf
    """

    stem = path.stem

    if stem.endswith("_ar"):
        stem = stem[:-3]

    return stem + ".pdf"


# ============================================================
# 4. DÉCOUVERTE DES DOCUMENTS
# ============================================================

def resolve_source_files() -> dict[str, list[Path]]:
    """
    Français :
        privilégie les PDF.

    Arabe :
        privilégie les TXT lorsqu'ils existent,
        car leur extraction est beaucoup plus fiable
        pour le texte RTL.

        Le PDF est utilisé uniquement lorsqu'aucun TXT
        correspondant n'existe.
    """

    result: dict[str, list[Path]] = {
        "fr": [],
        "ar": [],
    }

    # ========================================================
    # FRANÇAIS
    # ========================================================

    if FR_DOCUMENTS_DIR.is_dir():

        result["fr"] = sorted(
            FR_DOCUMENTS_DIR.glob("*.pdf")
        )

    else:

        # Compatibilité ancienne structure
        result["fr"] = sorted(
            DOCUMENTS_DIR.glob("*.pdf")
        )

    # ========================================================
    # ARABE
    # ========================================================

    if not AR_DOCUMENTS_DIR.is_dir():
        return result

    txt_files = sorted(
        AR_DOCUMENTS_DIR.glob("*.txt")
    )

    pdf_files = sorted(
        AR_DOCUMENTS_DIR.glob("*.pdf")
    )

    # On mémorise les documents déjà couverts par TXT.
    txt_stems = {
        path.stem.removesuffix("_ar")
        for path in txt_files
    }

    result["ar"].extend(
        txt_files
    )

    # Ajoute un PDF seulement si aucun TXT
    # du même document n'existe.
    for pdf_path in pdf_files:

        base_stem = (
            pdf_path.stem
            .removesuffix("_ar")
        )

        if base_stem not in txt_stems:

            result["ar"].append(
                pdf_path
            )

    result["ar"] = sorted(
        result["ar"]
    )

    return result


# ============================================================
# 5. MODÈLE D'EMBEDDING
# ============================================================

EMBEDDING_MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

print("=" * 70)
print("CHARGEMENT DU MODÈLE D'EMBEDDING")
print("=" * 70)

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)

print(
    "Modèle :",
    EMBEDDING_MODEL_NAME,
)


# ============================================================
# 6. NETTOYAGE GÉNÉRAL
# ============================================================

def clean_text(
    text: str,
) -> str:

    if not text:
        return ""

    text = text.replace(
        "\x00",
        " ",
    )

    text = unicodedata.normalize(
        "NFC",
        text,
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# ============================================================
# 7. NETTOYAGE ARABE
# ============================================================

ARABIC_DIACRITICS_PATTERN = re.compile(
    r"[\u0610-\u061A"
    r"\u064B-\u065F"
    r"\u0670"
    r"\u06D6-\u06DC"
    r"\u06DF-\u06E8"
    r"\u06EA-\u06ED]"
)


def clean_arabic_text(
    text: str,
) -> str:

    if not text:
        return ""

    text = unicodedata.normalize(
        "NFC",
        text,
    )

    text = ARABIC_DIACRITICS_PATTERN.sub(
        "",
        text,
    )

    return clean_text(
        text
    )


# ============================================================
# 8. EXTRACTION PDF
# ============================================================

def extract_pdf_pages(
    path: Path,
    language: str,
) -> list[dict[str, Any]]:

    reader = PdfReader(
        str(path)
    )

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):

        text = (
            page.extract_text()
            or ""
        )

        if language == "ar":

            text = clean_arabic_text(
                text
            )

        else:

            text = clean_text(
                text
            )

        if not text:
            continue

        pages.append(
            {
                "page": page_number,
                "text": text,
                "language": language,
            }
        )

    return pages


# ============================================================
# 9. EXTRACTION TXT
# ============================================================

def extract_txt_pages(
    path: Path,
    language: str,
) -> list[dict[str, Any]]:
    """
    Un TXT est traité comme une source structurée unique.

    page=1 est conservé pour rester compatible
    avec le reste du pipeline.
    """

    text = path.read_text(
        encoding="utf-8"
    )

    if language == "ar":

        text = clean_arabic_text(
            text
        )

    else:

        text = clean_text(
            text
        )

    if not text:
        return []

    return [
        {
            "page": 1,
            "text": text,
            "language": language,
        }
    ]


# ============================================================
# 10. EXTRACTION D'UNE SOURCE
# ============================================================

def extract_source(
    path: Path,
    language: str,
) -> list[dict[str, Any]]:

    suffix = (
        path.suffix.lower()
    )

    if suffix == ".pdf":

        return extract_pdf_pages(
            path,
            language,
        )

    if suffix == ".txt":

        return extract_txt_pages(
            path,
            language,
        )

    raise ValueError(
        f"Format non supporté : {path}"
    )


# ============================================================
# 11. EXTRACTION DU THÈME
# ============================================================

def extract_theme(
    text: str,
) -> str | None:
    """
    Reconnaît :

    Français :
        Thème : Piratage de compte

    Arabe :
        الموضوع : اختراق الحساب
    """

    patterns = [
        r"Th[eè]me\s*:\s*([^\n\r]+)",
        r"الموضوع\s*:\s*([^\n\r]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:

            value = (
                match
                .group(1)
                .strip()
            )

            if value:
                return value

    return None


# ============================================================
# 12. EXTRACTION DE L'INTENTION
# ============================================================

def extract_intent(
    text: str,
) -> str | None:
    """
    Les valeurs des intentions restent volontairement
    en français dans les deux corpus.
    """

    patterns = [
        (
            r"Intention\s+CamemBERT\s*:\s*"
            r"([^\n\r]+)"
        ),
        (
            r"Intention\s+CamemBERT\s+"
            r"associ[eé]e\s*:\s*"
            r"([^\n\r]+)"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:

            intent = (
                match
                .group(1)
                .strip()
            )

            if intent:
                return intent

    return None


# ============================================================
# 13. MÉTADONNÉES : FR + AR
# ============================================================

def is_metadata_label(
    line: str,
) -> bool:

    value = line.strip().lower()

    return value in {
        "métadonnées",
        "metadonnées",
        "metadata",
        "البيانات الوصفية",
    }


def is_theme_line(
    line: str,
) -> bool:

    line = line.strip()

    patterns = [
        r"^Th[eè]me\s*:\s*\S+",
        r"^الموضوع\s*:\s*\S+",
    ]

    return any(
        re.match(
            pattern,
            line,
            flags=re.IGNORECASE,
        )
        is not None
        for pattern in patterns
    )


# ============================================================
# 14. DÉTECTION TITRES NUMÉROTÉS
# ============================================================

def is_section_title(
    line: str,
) -> bool:

    line = line.strip()

    # 1. titre
    # 10. titre
    #
    # \s+ (et non \s*) exige au moins un espace après le point, pour
    # ne pas matcher des tokens comme "2511.ma" (faux positif
    # identifié dans 04_ressources_et_orientation_final).
    if re.match(
        r"^\d+\.\s+\S+",
        line,
    ):
        return True

    return False


# ============================================================
# 14 bis. DÉTECTION : LE DOCUMENT UTILISE-T-IL LA CONVENTION
# "titre / Métadonnées / Thème" ?
# ============================================================
#
# Détection ADAPTATIVE, sans aucun nom de document ni intention codés
# en dur : on observe uniquement si CE document utilise, au moins une
# fois, le bloc structuré (titre suivi de Métadonnées puis Thème).
#
#   - Si oui (document "structuré", ex. 02_signalement_et_procedures) :
#     une ligne numérotée qui n'est PAS suivie de ce bloc n'est plus
#     traitée comme un nouveau titre de section -- elle reste à
#     l'intérieur de la section en cours (très probablement une étape
#     interne d'une procédure, comme "1. Qualifier la situation...").
#
#   - Si non (document "non structuré", ex. 03_cadre_juridique_maroc_final,
#     05_accompagnement_et_conversation, dont les titres numérotés ne
#     sont JAMAIS suivis d'un bloc Métadonnées/Thème) : le comportement
#     d'origine est intégralement conservé -- toute ligne numérotée
#     continue d'être traitée comme un nouveau titre, car c'est la
#     seule façon dont ces documents délimitent leurs sections.
#
# Utilise exactement le même fenêtrage ligne par ligne, page par page,
# que build_document_sections() (jamais de lookahead au-delà d'une
# page), pour rester rigoureusement cohérent avec la détection réelle.

def document_has_structured_sections(
    pages: list[dict[str, Any]],
) -> bool:

    for page_data in pages:

        lines = [
            line.strip()
            for line in (
                page_data["text"]
                .splitlines()
            )
            if line.strip()
            and line.strip() != "---"
        ]

        for i, line in enumerate(lines):

            if (
                i + 2
                < len(lines)
                and is_metadata_label(
                    lines[i + 1]
                )
                and is_theme_line(
                    lines[i + 2]
                )
            ):

                return True

    return False


# ============================================================
# 15. CHUNKING
# ============================================================

BREAK_MARKERS = (
    "\n\n",
    ". ",
    "? ",
    "! ",
    "؟ ",
    "؛ ",
    "۔",
    "\n",
)


def chunk_text(
    text: str,
    chunk_size: int = 850,
    overlap: int = 120,
) -> list[str]:

    text = text.strip()

    if not text:
        return []

    if len(text) <= chunk_size:
        return [
            text
        ]

    chunks = []

    start = 0

    while start < len(text):

        end = min(
            start + chunk_size,
            len(text),
        )

        chunk = text[
            start:end
        ]

        if end < len(text):

            break_positions = [
                chunk.rfind(marker)
                for marker in BREAK_MARKERS
            ]

            best_break = max(
                break_positions
            )

            if (
                best_break
                > chunk_size * 0.55
            ):

                chunk = chunk[
                    :best_break + 1
                ]

        chunk = chunk.strip()

        if chunk:

            chunks.append(
                chunk
            )

        consumed = len(
            chunk
        )

        if consumed <= 0:
            break

        next_start = (
            start
            + consumed
            - overlap
        )

        if next_start <= start:

            next_start = (
                start
                + consumed
            )

        start = next_start

    return chunks


# ============================================================
# 16. RECONSTRUCTION DES SECTIONS
# ============================================================

def build_document_sections(
    pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    # Calculé UNE SEULE FOIS pour tout le document (pas par page, pas
    # par ligne) : détermine si ce document utilise la convention
    # structurée quelque part. Aucun nom de fichier ni intention codés
    # en dur -- uniquement basé sur la structure réelle observée.
    document_is_structured = document_has_structured_sections(
        pages
    )

    sections = []

    current_lines: list[str] = []

    current_page: int | None = None

    current_language: str | None = None

    def save_current_section() -> None:

        nonlocal current_lines
        nonlocal current_page
        nonlocal current_language

        text = "\n".join(
            current_lines
        ).strip()

        if text:

            sections.append(
                {
                    "page":
                        current_page or 1,

                    "language":
                        current_language,

                    "text":
                        text,
                }
            )

        current_lines = []
        current_page = None
        current_language = None

    # ========================================================
    # PAGES
    # ========================================================

    for page_data in pages:

        page_number = int(
            page_data["page"]
        )

        page_language = str(
            page_data["language"]
        )

        lines = [
            line.strip()
            for line in (
                page_data["text"]
                .splitlines()
            )
            if line.strip()
            and line.strip() != "---"
        ]

        i = 0

        while i < len(lines):

            line = lines[i]

            # =================================================
            # CAS STRUCTURÉ :
            #
            # titre
            # Métadonnées / البيانات الوصفية
            # Thème / الموضوع
            # =================================================

            if (
                i + 2
                < len(lines)
                and is_metadata_label(
                    lines[i + 1]
                )
                and is_theme_line(
                    lines[i + 2]
                )
            ):

                if current_lines:
                    save_current_section()

                current_page = (
                    page_number
                )

                current_language = (
                    page_language
                )

                current_lines = [
                    line,
                    lines[i + 1],
                    lines[i + 2],
                ]

                i += 3
                continue

            # =================================================
            # THÈME DIRECT
            # =================================================

            if is_theme_line(
                line
            ):

                if current_lines:
                    save_current_section()

                current_page = (
                    page_number
                )

                current_language = (
                    page_language
                )

                current_lines = [
                    line
                ]

                i += 1
                continue

            # =================================================
            # TITRE NUMÉROTÉ
            #
            # Désormais actif UNIQUEMENT si le document n'utilise
            # jamais la convention structurée ailleurs. Dans un
            # document structuré, une ligne numérotée sans le bloc
            # Métadonnées/Thème qui suit tombe dans la branche
            # TEXTE NORMAL ci-dessous -- elle reste à l'intérieur de
            # la section en cours, au lieu d'en démarrer une nouvelle.
            # =================================================

            if (
                is_section_title(
                    line
                )
                and not document_is_structured
            ):

                if current_lines:
                    save_current_section()

                current_page = (
                    page_number
                )

                current_language = (
                    page_language
                )

                current_lines = [
                    line
                ]

                i += 1
                continue

            # =================================================
            # TEXTE NORMAL
            # =================================================

            if current_page is None:

                current_page = (
                    page_number
                )

            if current_language is None:

                current_language = (
                    page_language
                )

            current_lines.append(
                line
            )

            i += 1

    if current_lines:

        save_current_section()

    return sections


# ============================================================
# 17. CRÉATION DES CHUNKS D'UNE SOURCE
# ============================================================

def create_document_chunks(
    source_path: Path,
    language: str,
) -> list[dict[str, Any]]:

    pages = extract_source(
        source_path,
        language,
    )

    sections = build_document_sections(
        pages
    )

    logical_document_name = (
        canonical_pdf_name(
            source_path
        )
    )

    config_name = (
        canonical_document_name(
            source_path
        )
    )

    # Si source TXT -> utilise clé TXT si elle existe,
    # sinon clé PDF canonique.
    default_intent = (
        DOCUMENT_DEFAULT_INTENTS.get(
            config_name
        )
        or DOCUMENT_DEFAULT_INTENTS.get(
            logical_document_name
        )
    )

    document_type = (
        DOCUMENT_TYPES.get(
            config_name
        )
        or DOCUMENT_TYPES.get(
            logical_document_name
        )
        or "Document"
    )

    document_chunks = []

    global_chunk_index = 0

    for section in sections:

        section_text = (
            section["text"]
        )

        section_language = (
            section.get(
                "language"
            )
            or language
        )

        theme = extract_theme(
            section_text
        )

        intent = extract_intent(
            section_text
        )

        if not intent:
            intent = (
                default_intent
            )

        section_chunks = chunk_text(
            section_text
        )

        for chunk in section_chunks:

            meaningful_text = re.sub(
                r"\s+",
                " ",
                chunk,
            ).strip()

            if len(
                meaningful_text
            ) < 40:

                continue

            global_chunk_index += 1

            document_chunks.append(
                {
                    "id": None,

                    "document":
                        logical_document_name,

                    "source_file":
                        source_path.name,

                    "source_format":
                        source_path.suffix.lower(),

                    "language":
                        section_language,

                    "page":
                        section["page"],

                    "chunk_index":
                        global_chunk_index,

                    "theme":
                        theme,

                    "intent":
                        intent,

                    "document_type":
                        document_type,

                    "text":
                        chunk,
                }
            )

    return document_chunks


# ============================================================
# 18. CHARGEMENT DES DOCUMENTS
# ============================================================

files_by_language = (
    resolve_source_files()
)

total_source_files = sum(
    len(files)
    for files in (
        files_by_language.values()
    )
)

if total_source_files == 0:

    raise FileNotFoundError(
        "Aucun document trouvé.\n"
        f"Français attendu dans : {FR_DOCUMENTS_DIR}\n"
        f"Arabe attendu dans : {AR_DOCUMENTS_DIR}"
    )


print()
print("=" * 70)
print("DOCUMENTS TROUVÉS")
print("=" * 70)

for language in SUPPORTED_LANGUAGES:

    files = files_by_language.get(
        language,
        [],
    )

    print(
        f"[{language}] "
        f"{len(files)} document(s)"
    )

    for path in files:

        print(
            "   -",
            path.name,
            f"({path.suffix.lower()})",
        )


# ============================================================
# 19. TOUS LES CHUNKS
# ============================================================

all_chunks: list[dict[str, Any]] = []

for language in SUPPORTED_LANGUAGES:

    for source_path in (
        files_by_language.get(
            language,
            [],
        )
    ):

        document_chunks = (
            create_document_chunks(
                source_path,
                language,
            )
        )

        for chunk in document_chunks:

            chunk["id"] = len(
                all_chunks
            )

            all_chunks.append(
                chunk
            )


if not all_chunks:

    raise RuntimeError(
        "Aucun chunk n'a été créé."
    )


# ============================================================
# 20. STATISTIQUES
# ============================================================

print()
print("=" * 70)
print("CHUNKS")
print("=" * 70)

print(
    "Nombre total :",
    len(all_chunks),
)

for language in SUPPORTED_LANGUAGES:

    count = sum(
        1
        for item in all_chunks
        if item.get(
            "language"
        ) == language
    )

    print(
        f"  [{language}] :",
        count,
    )


chunks_with_theme = sum(
    1
    for item in all_chunks
    if item.get("theme")
)

chunks_with_intent = sum(
    1
    for item in all_chunks
    if item.get("intent")
)

print(
    "Chunks avec thème :",
    chunks_with_theme,
)

print(
    "Chunks avec intention :",
    chunks_with_intent,
)


# ============================================================
# 21. CONTRÔLE SPÉCIFIQUE ARABE
# ============================================================

arabic_chunks = [
    item
    for item in all_chunks
    if item.get(
        "language"
    ) == "ar"
]

arabic_with_theme = sum(
    1
    for item in arabic_chunks
    if item.get(
        "theme"
    )
)

arabic_with_intent = sum(
    1
    for item in arabic_chunks
    if item.get(
        "intent"
    )
)

print()
print(
    "Chunks AR avec thème :",
    f"{arabic_with_theme}/"
    f"{len(arabic_chunks)}",
)

print(
    "Chunks AR avec intention :",
    f"{arabic_with_intent}/"
    f"{len(arabic_chunks)}",
)


# ============================================================
# 22. TEXTE POUR EMBEDDING
# ============================================================

def build_embedding_text(
    item: dict[str, Any],
) -> str:

    parts = []

    theme = item.get(
        "theme"
    )

    intent = item.get(
        "intent"
    )

    language = item.get(
        "language"
    )

    # Pour l'arabe, le thème est déjà en arabe.
    # L'intention reste en français comme signal technique.
    if theme:

        if language == "ar":

            parts.append(
                "الموضوع : "
                + str(theme)
            )

        else:

            parts.append(
                "Thème : "
                + str(theme)
            )

    if intent:

        parts.append(
            "Intention : "
            + str(intent)
        )

    parts.append(
        str(
            item["text"]
        )
    )

    return "\n".join(
        parts
    )


texts = [
    build_embedding_text(
        item
    )
    for item in all_chunks
]


# ============================================================
# 23. EMBEDDINGS
# ============================================================

print()
print("=" * 70)
print("CRÉATION DES EMBEDDINGS")
print("=" * 70)

embeddings = (
    embedding_model.encode_document(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
)

embeddings = np.asarray(
    embeddings,
    dtype="float32",
)


print(
    "Shape embeddings :",
    embeddings.shape,
)


# ============================================================
# 24. INDEX FAISS
# ============================================================

dimension = int(
    embeddings.shape[1]
)

index = faiss.IndexFlatIP(
    dimension
)

index.add(
    embeddings
)


print()
print("=" * 70)
print("INDEX FAISS")
print("=" * 70)

print(
    "Dimension :",
    dimension,
)

print(
    "Vecteurs indexés :",
    index.ntotal,
)


# ============================================================
# 25. SAUVEGARDE
# ============================================================

INDEX_FILE = (
    VECTOR_STORE_DIR
    / "emc_faiss.index"
)

CHUNKS_FILE = (
    VECTOR_STORE_DIR
    / "chunks.json"
)

CONFIG_FILE = (
    VECTOR_STORE_DIR
    / "rag_config.json"
)


faiss.write_index(
    index,
    str(INDEX_FILE),
)


with CHUNKS_FILE.open(
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        all_chunks,
        file,
        ensure_ascii=False,
        indent=2,
    )


languages_present = sorted(
    {
        str(
            item["language"]
        )
        for item in all_chunks
        if item.get(
            "language"
        )
    }
)


chunks_per_language = {
    language: sum(
        1
        for item in all_chunks
        if item.get(
            "language"
        ) == language
    )
    for language
    in languages_present
}


config = {
    "embedding_model":
        EMBEDDING_MODEL_NAME,

    "number_of_source_files":
        total_source_files,

    "number_of_chunks":
        len(all_chunks),

    "embedding_dimension":
        dimension,

    "chunk_size":
        850,

    "chunk_overlap":
        120,

    "languages_indexed":
        languages_present,

    "chunks_per_language":
        chunks_per_language,

    "arabic_source_preference":
        "txt",

    "metadata_version":
        4,
}


with CONFIG_FILE.open(
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        config,
        file,
        ensure_ascii=False,
        indent=2,
    )


# ============================================================
# 26. FIN
# ============================================================

print()
print("=" * 70)
print(
    "RAG INDEX V4 BILINGUE "
    "CRÉÉ AVEC SUCCÈS"
)
print("=" * 70)

print(
    "Index :",
    INDEX_FILE,
)

print(
    "Chunks :",
    CHUNKS_FILE,
)

print(
    "Config :",
    CONFIG_FILE,
)

print(
    "Langues :",
    languages_present,
)

print(
    "Chunks par langue :",
    chunks_per_language,
)