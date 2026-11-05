import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

CHUNKS_FILE = (
    BASE_DIR
    / "rag"
    / "vector_store"
    / "chunks.json"
)


with CHUNKS_FILE.open(
    "r",
    encoding="utf-8",
) as file:
    chunks = json.load(file)


targets = [
    "Conservation des preuves",
    "Piratage de compte",
    "Stalking",
    "Sextorsion",
    "Doxing",
    "Divulgation de données personnelles",
]


for target in targets:

    print()
    print("=" * 100)
    print("TARGET :", target)
    print("=" * 100)

    found = False

    for chunk in chunks:

        theme = chunk.get("theme")
        intent = chunk.get("intent")
        text = chunk.get("text", "")

        theme_normalized = (
            theme.lower()
            if theme
            else ""
        )

        intent_normalized = (
            intent.lower()
            if intent
            else ""
        )

        text_normalized = (
            text.lower()
            if text
            else ""
        )

        target_normalized = target.lower()

        if (
            target_normalized
            in theme_normalized
            or target_normalized
            in intent_normalized
            or target_normalized
            in text_normalized
        ):

            found = True

            print()
            print("-" * 100)

            print(
                "ID       :",
                chunk.get("id"),
            )

            print(
                "Document :",
                chunk.get("document"),
            )

            print(
                "Page     :",
                chunk.get("page"),
            )

            print(
                "Chunk    :",
                chunk.get("chunk_index"),
            )

            print(
                "Thème    :",
                theme,
            )

            print(
                "Intent   :",
                intent,
            )

            print()
            print(text)

    if not found:
        print(
            "\nAucun chunk trouvé pour :",
            target,
        )