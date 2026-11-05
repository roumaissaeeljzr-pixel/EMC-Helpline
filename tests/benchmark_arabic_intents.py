# -*- coding: utf-8 -*-
"""
tests/benchmark_arabic_intents.py

Benchmark INDÉPENDANT de la classification arabe actuelle. Charge
tests/data/arabic_intent_benchmark.json (110 exemples, 11 intentions
x 10, figé -- voir generate_arabic_benchmark.py pour sa construction)
et exécute CHAQUE exemple à travers le pipeline de classification
RÉEL actuellement en production, sans le reproduire ni le modifier :

    from rag.generator import classify_situation

classify_situation() ne fait AUCUN appel à Ollama (voir sa docstring
et le refactoring de la Phase 3B) -- ce benchmark fonctionne donc
qu'Ollama soit lancé ou non.

Ce script est un CONSOMMATEUR en lecture seule du pipeline existant.
Il ne modifie :
    - ni rag/generator.py
    - ni rag/retriever.py
    - ni rag/build_index.py
    - ni le routeur arabe (detect_arabic_intent_keyword, etc.)
    - ni CamemBERT / backend/intent_classifier.py
    - ni le corpus / vector_store/

Lancement (depuis 06_Development, venv activé) :

    python tests/benchmark_arabic_intents.py

Résultats :
    - Affichage console (métriques globales, par intention, matrice
      de confusion, détail des erreurs)
    - tests/results/arabic_benchmark_results.json (créé/écrasé)
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Permet l'exécution directe (python tests/benchmark_arabic_intents.py)
# depuis 06_Development sans installation du package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.generator import classify_situation  # noqa: E402


DATASET_PATH = Path(__file__).resolve().parent / "data" / "arabic_intent_benchmark.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_PATH = RESULTS_DIR / "arabic_benchmark_results.json"

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
            "Lancez d'abord generate_arabic_benchmark.py."
        )

    with DATASET_PATH.open(encoding="utf-8") as f:
        dataset = json.load(f)

    if len(dataset) != 110:
        print(
            f"AVERTISSEMENT : {len(dataset)} exemples chargés (110 attendus).",
            file=sys.stderr,
        )

    return dataset


def run_benchmark(dataset: list[dict]) -> list[dict]:

    results = []

    for example in dataset:

        text = example["text"]
        expected_intent = example["expected_intent"]

        classification = classify_situation(text)

        predicted_intent = classification.get("predicted_intent")

        result_entry = {
            "id": example["id"],
            "text": text,
            "difficulty": example.get("difficulty"),
            "expected_intent": expected_intent,
            "predicted_intent": predicted_intent,
            "correct": predicted_intent == expected_intent,
            "intent_source": classification.get("intent_source"),
            "language": classification.get("language"),
            "confidence": classification.get("intent_confidence"),
            "outcome": classification.get("outcome"),
            "emergency_override": classification.get("emergency_override"),
        }

        results.append(result_entry)

    return results


# ============================================================
# MÉTRIQUES
# ============================================================

def compute_metrics(results: list[dict]) -> dict:
    """
    Calcule accuracy globale, precision/recall/F1 macro, et le détail
    par intention. Utilise sklearn.metrics si disponible (déjà
    présent dans l'environnement), sinon un calcul manuel équivalent
    -- aucune nouvelle dépendance n'est ajoutée dans les deux cas.
    """

    y_true = [r["expected_intent"] for r in results]
    y_pred = [r["predicted_intent"] for r in results]

    # `predicted_intent` peut être None (aucune intention détectée
    # par le pipeline). sklearn.metrics n'est pas garanti de bien
    # gérer une valeur None mélangée à des labels `str` -- on
    # substitue donc un sentinelle "(aucune)" UNIQUEMENT pour ce
    # calcul sklearn, jamais dans `results` ni dans l'export JSON, ni
    # dans le calcul manuel de repli (qui gère déjà None nativement
    # via une simple comparaison `==`), où predicted_intent reste
    # None tel quel.
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
    print("BENCHMARK ARABE -- 11 INTENTIONS SUPPORTÉES")
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
            print(f"    (hors périmètre) : {dict(other_predictions)}")

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
            print("Texte :")
            print(r["text"])
            print()
            print("Attendu :")
            print(r["expected_intent"])
            print()
            print("Prédit :")
            print(r["predicted_intent"])
            print()
            print("Source de l'intention :")
            print(r["intent_source"])

    print()
    print("=" * 78)


def export_results(results: list[dict]) -> None:

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    export_data = [
        {
            "id": r["id"],
            "text": r["text"],
            "expected_intent": r["expected_intent"],
            "predicted_intent": r["predicted_intent"],
            "correct": r["correct"],
            "intent_source": r["intent_source"],
        }
        for r in results
    ]

    with RESULTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"Résultats exportés vers : {RESULTS_PATH}")


def main() -> None:

    dataset = load_dataset()
    results = run_benchmark(dataset)
    metrics = compute_metrics(results)

    print_report(results, metrics)
    export_results(results)


if __name__ == "__main__":
    main()