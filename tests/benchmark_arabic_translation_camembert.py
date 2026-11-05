# -*- coding: utf-8 -*-
"""
tests/benchmark_arabic_translation_camembert.py

Benchmark B -- EXPÉRIMENTAL / COMPARATIF UNIQUEMENT.

Teste le pipeline alternatif :

    texte arabe (dataset figé)
        -> translate_arabic_to_french()   (rag/query_translator.py, réel)
        -> predict_intent()               (backend/intent_classifier.py, réel)
        -> intention canonique

sur EXACTEMENT le même jeu de 110 exemples figé que le benchmark A
(tests/data/arabic_intent_benchmark.json), pour comparaison équitable.

Ce benchmark N'UTILISE PAS et n'appelle JAMAIS :
    - classify_situation()
    - detect_arabic_intent_keyword() / arabic_keyword_hint
    - derive_majority_intent() / arabic_majority_vote
    - retrieve() / le RAG
    - Ollama / generate_answer() / /chat

Il réutilise strictement les DEUX fonctions réelles déjà existantes
dans le projet, sans les dupliquer ni les modifier :

    from rag.query_translator import translate_arabic_to_french
    from backend.intent_classifier import predict_intent

Ces deux modules chargent leurs modèles (MarianMT AR->FR et
CamemBERT) UNE SEULE FOIS au niveau module, au moment de l'import --
confirmé par lecture du code source réel avant d'écrire ce script.

Ce script est AUTONOME (ne importe aucune fonction depuis
tests/benchmark_arabic_intents.py, sur demande explicite) : la
logique de métriques est dupliquée ici, volontairement, pour garder
les deux benchmarks indépendants l'un de l'autre.

NE MODIFIE AUCUN FICHIER EXISTANT :
    - rag/query_translator.py
    - backend/intent_classifier.py
    - rag/generator.py
    - rag/retriever.py
    - tests/benchmark_arabic_intents.py
    - tests/data/arabic_intent_benchmark.json (dataset figé, lu seulement)

Lancement (depuis 06_Development, venv activé) :

    python tests/benchmark_arabic_translation_camembert.py

Le chargement des deux modèles (traduction + CamemBERT) au démarrage
peut prendre du temps -- c'est normal et attendu, une seule fois.
"""

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ces deux imports déclenchent le chargement des modèles réels
# (traducteur MarianMT + CamemBERT), une seule fois, au niveau
# module de rag/query_translator.py et backend/intent_classifier.py
# -- confirmé par lecture du code source, non supposé.
from backend.intent_classifier import predict_intent  # noqa: E402
from rag.query_translator import translate_arabic_to_french  # noqa: E402


DATASET_PATH = Path(__file__).resolve().parent / "data" / "arabic_intent_benchmark.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_PATH = RESULTS_DIR / "arabic_translation_camembert_results.json"

SUPPORTED_INTENTS = [
    "Cyberharcèlement",
    "Sextorsion",
    "Piratage de compte",
    "Divulgation de données personnelles (Doxing)",
    "Conservation des preuves",
    "Informations juridiques",
    "Usurpation d'identité",
    "Diffusion non consentie d'images",
    "Signalement",
    "Situation d'urgence",
    "Accompagnement de la victime",
]


def load_dataset() -> list[dict]:

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset introuvable : {DATASET_PATH}. "
            "Le benchmark A doit avoir été créé au préalable "
            "(tests/data/arabic_intent_benchmark.json)."
        )

    with DATASET_PATH.open(encoding="utf-8") as f:
        dataset = json.load(f)

    if len(dataset) != 110:
        print(
            f"AVERTISSEMENT : {len(dataset)} exemples chargés (110 attendus). "
            "Le dataset figé aurait-il été modifié ?",
            file=sys.stderr,
        )

    return dataset


# ============================================================
# PIPELINE B : traduction -> CamemBERT, avec gestion d'erreurs
# stricte (aucun exemple ne doit jamais interrompre le benchmark)
# ============================================================

def classify_via_translation(arabic_text: str) -> dict:
    """
    Exécute EXACTEMENT le pipeline B pour un texte arabe :
    translate_arabic_to_french() puis predict_intent(), sans aucun
    recours au routeur arabe existant, au RAG, ni à Ollama.

    Ne lève jamais d'exception : toute erreur (traduction ou
    classification) est capturée et retournée dans le champ "error".
    """

    translated_text = None
    predicted_intent = None
    confidence = None
    error = None

    try:
        translated_text = translate_arabic_to_french(arabic_text)

    except Exception as exc:
        error = f"translation_error: {exc}"

    if error is None:

        try:
            intent_result = predict_intent(translated_text)
            predicted_intent = intent_result["intent"]
            confidence = intent_result["confidence"]

        except Exception as exc:
            error = f"camembert_error: {exc}"

    return {
        "translated_text": translated_text,
        "predicted_intent": predicted_intent,
        "confidence": confidence,
        "error": error,
    }


def run_benchmark(dataset: list[dict]) -> list[dict]:

    results = []
    total = len(dataset)

    for index, example in enumerate(dataset, start=1):

        arabic_text = example["text"]
        expected_intent = example["expected_intent"]

        pipeline_output = classify_via_translation(arabic_text)

        predicted_intent = pipeline_output["predicted_intent"]

        result_entry = {
            "id": example["id"],
            "arabic_text": arabic_text,
            "translated_text": pipeline_output["translated_text"],
            "expected_intent": expected_intent,
            "predicted_intent": predicted_intent,
            "correct": predicted_intent == expected_intent,
            "confidence": pipeline_output["confidence"],
            "error": pipeline_output["error"],
            "difficulty": example.get("difficulty"),
        }

        results.append(result_entry)

        if index % 10 == 0 or index == total:
            print(f"  ... {index}/{total} exemples traités", file=sys.stderr)

    return results


# ============================================================
# MÉTRIQUES (dupliquées volontairement, script autonome --
# ne dépend pas de tests/benchmark_arabic_intents.py)
# ============================================================

def compute_metrics(results: list[dict]) -> dict:

    y_true = [r["expected_intent"] for r in results]
    y_pred = [r["predicted_intent"] for r in results]

    # Sentinelle "(aucune)" UNIQUEMENT pour le calcul sklearn --
    # jamais dans `results` ni dans l'export JSON, où
    # predicted_intent reste None tel quel.
    y_pred_for_metrics = [
        value if value is not None else "(aucune)"
        for value in y_pred
    ]

    try:
        from sklearn.metrics import precision_recall_fscore_support

        labels = SUPPORTED_INTENTS

        precision, recall, f1, support = precision_recall_fscore_support(
            y_true,
            y_pred_for_metrics,
            labels=labels,
            average=None,
            zero_division=0,
        )

        macro_precision = sum(precision) / len(precision)
        macro_recall = sum(recall) / len(recall)
        macro_f1 = sum(f1) / len(f1)

        per_intent = {
            label: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i, label in enumerate(labels)
        }

        used_sklearn = True

    except ImportError:

        per_intent = {}

        for label in SUPPORTED_INTENTS:

            tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
            fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
            fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
            support = sum(1 for t in y_true if t == label)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )

            per_intent[label] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": support,
            }

        macro_precision = sum(v["precision"] for v in per_intent.values()) / len(per_intent)
        macro_recall = sum(v["recall"] for v in per_intent.values()) / len(per_intent)
        macro_f1 = sum(v["f1"] for v in per_intent.values()) / len(per_intent)

        used_sklearn = False

    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    accuracy = correct / total if total else 0.0

    return {
        "total": total,
        "correct": correct,
        "errors": total - correct,
        "accuracy": accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "per_intent": per_intent,
        "used_sklearn": used_sklearn,
    }


def build_confusion_matrix(results: list[dict]) -> dict[str, Counter]:

    matrix: dict[str, Counter] = {intent: Counter() for intent in SUPPORTED_INTENTS}

    for r in results:

        expected = r["expected_intent"]
        predicted = r["predicted_intent"] or "(aucune)"

        if expected in matrix:
            matrix[expected][predicted] += 1

    return matrix


# ============================================================
# AFFICHAGE
# ============================================================

def print_report(results: list[dict], metrics: dict) -> None:

    print("=" * 78)
    print("BENCHMARK B -- AR -> TRADUCTION FR -> CAMEMBERT")
    print("=" * 78)
    print()
    print(f"Nombre total : {metrics['total']}")
    print(f"Corrects     : {metrics['correct']}")
    print(f"Erreurs      : {metrics['errors']}")
    print(f"Accuracy     : {metrics['accuracy'] * 100:.2f} %")
    print()
    print(f"Macro Precision : {metrics['macro_precision'] * 100:.2f} %")
    print(f"Macro Recall    : {metrics['macro_recall'] * 100:.2f} %")
    print(f"Macro F1        : {metrics['macro_f1'] * 100:.2f} %")
    print(f"(calculé via {'sklearn.metrics' if metrics['used_sklearn'] else 'implémentation manuelle -- sklearn indisponible'})")
    print()

    pipeline_failures = [r for r in results if r["error"]]
    if pipeline_failures:
        print(f"Échecs de pipeline (traduction ou CamemBERT) : {len(pipeline_failures)}/{metrics['total']}")
        print()

    print("-" * 78)
    print("PERFORMANCE PAR INTENTION")
    print("-" * 78)

    per_intent_correct = defaultdict(int)
    per_intent_total = defaultdict(int)

    for r in results:
        per_intent_total[r["expected_intent"]] += 1
        if r["correct"]:
            per_intent_correct[r["expected_intent"]] += 1

    for intent in SUPPORTED_INTENTS:
        correct = per_intent_correct[intent]
        total = per_intent_total[intent]
        p = metrics["per_intent"][intent]["precision"]
        r_ = metrics["per_intent"][intent]["recall"]
        f1 = metrics["per_intent"][intent]["f1"]
        print(
            f"  {intent:<50} {correct}/{total}   "
            f"P={p*100:5.1f}%  R={r_*100:5.1f}%  F1={f1*100:5.1f}%"
        )
    print()

    print("-" * 78)
    print("MATRICE DE CONFUSION (lignes = attendu, colonnes = prédit)")
    print("-" * 78)

    matrix = build_confusion_matrix(results)

    short_labels = {intent: intent[:18] for intent in SUPPORTED_INTENTS}

    header = " " * 22 + " ".join(f"{short_labels[i]:<20}" for i in SUPPORTED_INTENTS)
    print(header)

    for expected in SUPPORTED_INTENTS:
        row_counts = matrix[expected]
        row = f"  {expected[:20]:<20}"
        for predicted in SUPPORTED_INTENTS:
            count = row_counts.get(predicted, 0)
            row += f"{count:<21}"
        print(row)

        other_predictions = {
            k: v for k, v in row_counts.items() if k not in SUPPORTED_INTENTS
        }
        if other_predictions:
            print(f"    (hors périmètre / aucune / échec) : {dict(other_predictions)}")

    print()

    print("-" * 78)
    print("DÉTAIL DES ERREURS")
    print("-" * 78)

    errors = [r for r in results if not r["correct"]]

    if not errors:
        print("  Aucune erreur.")
    else:
        for r in errors:
            print()
            print("[ERREUR]")
            print()
            print("Texte arabe :")
            print(r["arabic_text"])
            print()
            print("Traduction française :")
            print(r["translated_text"] if r["translated_text"] else "(échec de traduction)")
            print()
            print("Attendu :")
            print(r["expected_intent"])
            print()
            print("Prédit :")
            print(r["predicted_intent"])
            print()
            print("Confiance :")
            print(r["confidence"])
            if r["error"]:
                print()
                print("Erreur technique :")
                print(r["error"])

    print()
    print("=" * 78)


def export_results(results: list[dict]) -> None:

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    export_data = [
        {
            "id": r["id"],
            "arabic_text": r["arabic_text"],
            "translated_text": r["translated_text"],
            "expected_intent": r["expected_intent"],
            "predicted_intent": r["predicted_intent"],
            "correct": r["correct"],
            "confidence": r["confidence"],
            "error": r["error"],
        }
        for r in results
    ]

    with RESULTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"Résultats exportés vers : {RESULTS_PATH}")


def main() -> None:

    dataset = load_dataset()

    print(f"Dataset chargé : {len(dataset)} exemples.")
    print("Exécution du pipeline B (traduction AR->FR + CamemBERT) sur chaque exemple...")
    print("(les modèles ont déjà été chargés une seule fois à l'import de ce script)")
    print()

    start = time.time()
    results = run_benchmark(dataset)
    elapsed = time.time() - start

    print(f"\nTerminé en {elapsed:.1f} secondes ({elapsed / len(dataset):.2f} s/exemple en moyenne).\n")

    metrics = compute_metrics(results)

    print_report(results, metrics)
    export_results(results)


if __name__ == "__main__":
    main()