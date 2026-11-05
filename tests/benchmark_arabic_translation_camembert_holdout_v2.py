# -*- coding: utf-8 -*-
"""
tests/benchmark_arabic_translation_camembert_holdout_v2.py

Benchmark B sur le HOLDOUT AR-2 (55 exemples, jamais vus par le
système auparavant) -- EXPÉRIMENTAL / COMPARATIF UNIQUEMENT.

Teste EXACTEMENT le même pipeline que le benchmark B historique
(tests/benchmark_arabic_translation_camembert.py, 110 exemples), mais
sur tests/data/arabic_intent_holdout_v2.json (55 exemples, figé),
avec en plus une répartition des performances par niveau de
difficulté (direct / indirect / contextual / paraphrase / difficult).

    texte arabe (holdout AR-2, 55 exemples)
        -> translate_arabic_to_french()   (rag/query_translator.py, réel)
        -> predict_intent()               (backend/intent_classifier.py, réel)
        -> intention canonique

Ce benchmark N'UTILISE PAS et n'appelle JAMAIS :
    - classify_situation()
    - detect_arabic_intent_keyword() / arabic_keyword_hint
    - derive_majority_intent() / arabic_majority_vote
    - retrieve() / le RAG
    - Ollama / generate_answer() / /chat

NE MODIFIE AUCUN FICHIER EXISTANT :
    - rag/query_translator.py
    - backend/intent_classifier.py
    - rag/generator.py
    - rag/retriever.py
    - tests/benchmark_arabic_translation_camembert.py (benchmark historique, intact)
    - tests/data/arabic_intent_holdout_v2.json (lu seulement, jamais modifié)
    - tests/data/arabic_intent_benchmark.json (jamais touché)

Export séparé, n'écrase JAMAIS les résultats existants :
    tests/results/arabic_translation_camembert_holdout_v2_results.json

Lancement (depuis 06_Development, venv activé) :

    $env:PYTHONIOENCODING="utf-8"
    python tests/benchmark_arabic_translation_camembert_holdout_v2.py
"""

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Chargement des modèles réels (traducteur MarianMT + CamemBERT),
# une seule fois, au niveau module -- comportement déjà confirmé par
# lecture du code source lors de la création du benchmark B historique.
from backend.intent_classifier import predict_intent  # noqa: E402
from rag.query_translator import translate_arabic_to_french  # noqa: E402


DATASET_PATH = Path(__file__).resolve().parent / "data" / "arabic_intent_holdout_v2.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_PATH = RESULTS_DIR / "arabic_translation_camembert_holdout_v2_results.json"

EXPECTED_EXAMPLE_COUNT = 55

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

DIFFICULTY_LEVELS = ["direct", "indirect", "contextual", "paraphrase", "difficult"]


def load_dataset() -> list[dict]:

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset holdout introuvable : {DATASET_PATH}. "
            "Le fichier tests/data/arabic_intent_holdout_v2.json "
            "doit déjà exister et être figé."
        )

    with DATASET_PATH.open(encoding="utf-8") as f:
        dataset = json.load(f)

    if len(dataset) != EXPECTED_EXAMPLE_COUNT:
        print(
            f"AVERTISSEMENT : {len(dataset)} exemples chargés "
            f"({EXPECTED_EXAMPLE_COUNT} attendus). "
            "Le holdout AR-2 aurait-il été modifié ?",
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
            "difficulty": example.get("difficulty"),
            "error": pipeline_output["error"],
        }

        results.append(result_entry)

        print(f"  ... {index}/{total} exemples traités", file=sys.stderr)

    return results


# ============================================================
# MÉTRIQUES (dupliquées volontairement, script autonome --
# ne dépend pas des autres scripts de benchmark)
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


def compute_difficulty_breakdown(results: list[dict]) -> dict:

    breakdown = {}

    for level in DIFFICULTY_LEVELS:

        subset = [r for r in results if r.get("difficulty") == level]
        total = len(subset)
        correct = sum(1 for r in subset if r["correct"])

        breakdown[level] = {
            "correct": correct,
            "total": total,
            "accuracy": (correct / total) if total else 0.0,
        }

    return breakdown


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

def print_report(results: list[dict], metrics: dict, elapsed: float) -> None:

    print("=" * 78)
    print("BENCHMARK B -- HOLDOUT AR-2 (55 exemples) -- AR -> TRADUCTION FR -> CAMEMBERT")
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
    print(f"Temps total d'exécution : {elapsed:.1f} s ({elapsed / metrics['total']:.2f} s/exemple en moyenne)")
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
    print("PERFORMANCE PAR DIFFICULTÉ")
    print("-" * 78)

    difficulty_breakdown = compute_difficulty_breakdown(results)

    for level in DIFFICULTY_LEVELS:
        stats = difficulty_breakdown[level]
        print(
            f"  {level:<15} {stats['correct']}/{stats['total']}   "
            f"accuracy={stats['accuracy']*100:5.1f}%"
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
            print("ID :")
            print(r["id"])
            print()
            print("Difficulté :")
            print(r["difficulty"])
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
            "difficulty": r["difficulty"],
            "error": r["error"],
        }
        for r in results
    ]

    with RESULTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"Résultats exportés vers : {RESULTS_PATH}")


def main() -> None:

    dataset = load_dataset()

    print(f"Dataset holdout AR-2 chargé : {len(dataset)} exemples.")
    print("Exécution du pipeline B (traduction AR->FR + CamemBERT) sur chaque exemple...")
    print("(les modèles ont déjà été chargés une seule fois à l'import de ce script)")
    print()

    start = time.time()
    results = run_benchmark(dataset)
    elapsed = time.time() - start

    print()

    metrics = compute_metrics(results)

    print_report(results, metrics, elapsed)
    export_results(results)


if __name__ == "__main__":
    main()