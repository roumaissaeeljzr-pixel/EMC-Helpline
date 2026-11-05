from pathlib import Path
import re

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)
from arabert.preprocess import ArabertPreprocessor


# ============================================================
# 1. CHEMINS DU PROJET ET DES MODÈLES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CAMEMBERT_MODEL_DIR = (
    BASE_DIR
    / "models"
    / "saved_models"
    / "camembert_final_v6"
)

ARABERT_MODEL_DIR = (
    BASE_DIR
    / "models"
    / "arabert_intent_v1"
)

ARABERT_BASE_MODEL = "aubmindlab/bert-base-arabertv02"

MAX_LENGTH = 96


# ============================================================
# 2. VÉRIFICATION DES DOSSIERS
# ============================================================

if not CAMEMBERT_MODEL_DIR.exists():
    raise FileNotFoundError(
        f"Modèle CamemBERT introuvable : {CAMEMBERT_MODEL_DIR}"
    )

if not ARABERT_MODEL_DIR.exists():
    raise FileNotFoundError(
        f"Modèle AraBERT introuvable : {ARABERT_MODEL_DIR}"
    )


# ============================================================
# 3. DEVICE : GPU OU CPU
# ============================================================

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# 4. CHARGEMENT CAMEMBERT — FRANÇAIS
# ============================================================

print("Chargement du tokenizer CamemBERT...")

camembert_tokenizer = AutoTokenizer.from_pretrained(
    CAMEMBERT_MODEL_DIR
)

print("Chargement du modèle CamemBERT...")

camembert_model = (
    AutoModelForSequenceClassification
    .from_pretrained(CAMEMBERT_MODEL_DIR)
    .to(DEVICE)
)

camembert_model.eval()


# ============================================================
# 5. CHARGEMENT ARABERT — ARABE
# ============================================================

print("Chargement du préprocesseur AraBERT...")

arabert_preprocessor = ArabertPreprocessor(
    model_name=ARABERT_BASE_MODEL,
    apply_farasa_segmentation=False,
)

print("Chargement du tokenizer AraBERT...")

arabert_tokenizer = AutoTokenizer.from_pretrained(
    ARABERT_MODEL_DIR
)

print("Chargement du modèle AraBERT...")

arabert_model = (
    AutoModelForSequenceClassification
    .from_pretrained(ARABERT_MODEL_DIR)
    .to(DEVICE)
)

arabert_model.eval()


# ============================================================
# 6. INFORMATIONS
# ============================================================

print("Classifieur bilingue chargé correctement.")
print("CamemBERT :", CAMEMBERT_MODEL_DIR)
print("AraBERT   :", ARABERT_MODEL_DIR)
print("Device    :", DEVICE)

if torch.cuda.is_available():
    print(
        "GPU :",
        torch.cuda.get_device_name(0)
    )


# ============================================================
# 7. DÉTECTION SIMPLE FR / AR
# ============================================================

ARABIC_CHAR_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]"
)

LATIN_CHAR_RE = re.compile(
    r"[A-Za-zÀ-ÖØ-öø-ÿ]"
)


def detect_message_language(message: str) -> str:
    """
    Détecte la langue principale du message.

    Retour :
        "ar" -> arabe
        "fr" -> français

    La détection tolère les noms latins au milieu d'une phrase arabe
    (WhatsApp, Instagram, Facebook, etc.).
    """

    arabic_count = len(
        ARABIC_CHAR_RE.findall(message)
    )

    latin_count = len(
        LATIN_CHAR_RE.findall(message)
    )

    if arabic_count == 0:
        return "fr"

    if latin_count == 0:
        return "ar"

    total = arabic_count + latin_count
    arabic_ratio = arabic_count / total

    # Une phrase arabe peut contenir un nom de plateforme en caractères latins.
    if arabic_count >= 3 and arabic_ratio >= 0.25:
        return "ar"

    return "fr"


# ============================================================
# 8. UTILITAIRE : NOM DE L'INTENTION
# ============================================================

def _get_intent_label(model, predicted_id: int) -> str:
    """
    Récupère le label de manière robuste selon la forme de id2label.
    """

    id2label = model.config.id2label

    if predicted_id in id2label:
        return id2label[predicted_id]

    string_id = str(predicted_id)

    if string_id in id2label:
        return id2label[string_id]

    raise KeyError(
        f"Label introuvable pour l'id {predicted_id}."
    )


# ============================================================
# 9. PRÉDICTION FRANÇAISE — CAMEMBERT
# ============================================================

def _predict_french(message: str):
    inputs = camembert_tokenizer(
        message,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=MAX_LENGTH,
    )

    inputs = {
        key: value.to(DEVICE)
        for key, value in inputs.items()
    }

    with torch.no_grad():
        outputs = camembert_model(**inputs)

        probabilities = torch.softmax(
            outputs.logits,
            dim=1
        )

    predicted_id = int(
        torch.argmax(
            probabilities,
            dim=1
        ).item()
    )

    confidence = float(
        probabilities[
            0,
            predicted_id
        ].item()
    )

    intent = _get_intent_label(
        camembert_model,
        predicted_id
    )

    return {
        "intent": intent,
        "confidence": confidence,
    }


# ============================================================
# 10. PRÉDICTION ARABE — ARABERT DIRECT
# ============================================================

def _predict_arabic(message: str):
    # Même prétraitement que pendant l'entraînement AraBERT.
    processed_message = (
        arabert_preprocessor
        .preprocess(message)
    )

    inputs = arabert_tokenizer(
        processed_message,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=MAX_LENGTH,
    )

    inputs = {
        key: value.to(DEVICE)
        for key, value in inputs.items()
    }

    with torch.no_grad():
        outputs = arabert_model(**inputs)

        probabilities = torch.softmax(
            outputs.logits,
            dim=1
        )

    predicted_id = int(
        torch.argmax(
            probabilities,
            dim=1
        ).item()
    )

    confidence = float(
        probabilities[
            0,
            predicted_id
        ].item()
    )

    intent = _get_intent_label(
        arabert_model,
        predicted_id
    )

    return {
        "intent": intent,
        "confidence": confidence,
    }


# ============================================================
# 11. FONCTION PUBLIQUE DE PRÉDICTION
# ============================================================

def predict_intent(
    message: str,
    language: str | None = None,
):
    """
    Prédit l'intention d'un message en français ou en arabe.

    Compatibilité :
        predict_intent(message)
    continue de fonctionner comme avant.

    Optionnel :
        predict_intent(message, language="fr")
        predict_intent(message, language="ar")

    Retour :
    {
        "intent": "Piratage de compte",
        "confidence": 0.94
    }
    """

    if not message:
        raise ValueError(
            "Le message ne peut pas être vide."
        )

    message = message.strip()

    if not message:
        raise ValueError(
            "Le message ne peut pas être vide."
        )

    if language is None:
        language = detect_message_language(
            message
        )
    else:
        language = language.strip().lower()

    if language not in {"fr", "ar"}:
        raise ValueError(
            "La langue doit être 'fr' ou 'ar'."
        )

    if language == "ar":
        return _predict_arabic(message)

    return _predict_french(message)