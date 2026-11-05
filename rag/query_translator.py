from transformers import (
    MarianMTModel,
    MarianTokenizer,
)

from backend.intent_classifier import predict_intent


MODEL_NAME = "Helsinki-NLP/opus-mt-ar-fr"


print("=" * 70)
print("CHARGEMENT DU MODÈLE DE TRADUCTION AR -> FR")
print("=" * 70)

tokenizer = MarianTokenizer.from_pretrained(
    MODEL_NAME
)

translation_model = MarianMTModel.from_pretrained(
    MODEL_NAME
)

print("Traducteur prêt :", MODEL_NAME)


def translate_arabic_to_french(
    text: str,
) -> str:
    """
    Traduit un texte arabe vers le français.
    """

    if not text or not text.strip():
        raise ValueError(
            "Le texte à traduire est vide."
        )

    inputs = tokenizer(
        [text],
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )

    translated_tokens = (
        translation_model.generate(
            **inputs,
            max_length=512,
            num_beams=4,
        )
    )

    translation = tokenizer.decode(
        translated_tokens[0],
        skip_special_tokens=True,
    )

    translation = translation.strip()

    if not translation:
        raise RuntimeError(
            "La traduction retournée est vide."
        )

    return translation


def test_translation_and_intent(
    arabic_text: str,
) -> None:

    print()
    print("=" * 100)
    print("QUESTION ARABE")
    print("=" * 100)
    print(arabic_text)

    french_text = translate_arabic_to_french(
        arabic_text
    )

    print()
    print("TRADUCTION FRANÇAISE")
    print("-" * 100)
    print(french_text)

    intent_result = predict_intent(
        french_text
    )

    print()
    print("INTENTION CAMEMBERT")
    print("-" * 100)

    print(
        "Intention :",
        intent_result["intent"],
    )

    print(
        "Confiance :",
        intent_result["confidence"],
    )


if __name__ == "__main__":

    test_questions = [
        (
            "تم اختراق حسابي على إنستغرام، "
            "ماذا أفعل؟"
        ),
        (
            "شخص يهدد بنشر صوري الخاصة."
        ),
        (
            "قام شخص بنشر عنواني ورقم هاتفي "
            "دون موافقتي."
        ),
        (
            "كيف يمكنني الاحتفاظ بالأدلة "
            "على التحرش الإلكتروني؟"
        ),
    ]

    for question in test_questions:

        test_translation_and_intent(
            question
        )