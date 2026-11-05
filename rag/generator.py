import inspect
import json
import re
import urllib.error
import urllib.request
from collections import Counter
from typing import Any

from backend.intent_classifier import predict_intent
from rag.retriever import retrieve


# ============================================================
# 1. CONFIGURATION OLLAMA
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

OLLAMA_MODEL = "llama3.1:latest"

TOP_K = 3

RETRIEVAL_K = 10


# ============================================================
# 1 bis. DÉTECTION DE LA LANGUE
# ============================================================

ARABIC_CHAR_PATTERN = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]"
)


def detect_language(text: str) -> str:
    """
    Détecte la langue d'entrée utilisée par l'utilisateur.

    - "ar" si au moins un caractère arabe est détecté ;
    - "fr" sinon.
    """

    if ARABIC_CHAR_PATTERN.search(text or ""):
        return "ar"

    return "fr"


def localized_message(
    language: str,
    french: str,
    arabic: str,
) -> str:
    """
    Retourne la version française ou arabe d'un message
    déterministe généré hors LLM.
    """

    if language == "ar":
        return arabic

    return french


# ============================================================
# 1 ter. INTENTION DÉRIVÉE PAR VOTE MAJORITAIRE (ARABE)
# ============================================================
#
# BUGFIX CRITIQUE :
# CamemBERT est entraîné UNIQUEMENT sur du français. Appliqué à une
# question arabe, il produit une prédiction essentiellement aléatoire
# (observé : "Situation d'urgence" avec 12% de confiance pour une
# question de piratage de compte), ce qui a conduit le pipeline à
# sélectionner le mauvais contexte documentaire et le LLM à halluciner
# une institution inexistante pour combler le vide.
#
# Pour l'arabe, on ne fait donc JAMAIS confiance à la prédiction
# CamemBERT. On la remplace par une intention dérivée du contenu
# lui-même : la métadonnée "chunk_intent" (préservée en français dans
# les documents arabes, voir la convention établie lors de la
# traduction) est déjà présente sur les chunks arabes récupérés par
# la recherche sémantique. On prend l'intention majoritaire parmi les
# meilleurs résultats sémantiques comme intention "détectée".
#
# Cette intention n'est utilisée QUE pour :
#   - l'affichage/la traçabilité ;
#   - la détection du besoin de clarification d'âge (section 2 ter).
# Elle ne sert JAMAIS à exclure des chunks déjà retournés par la
# recherche sémantique arabe (contrairement au français, où le
# filtrage strict par intention reste actif).

def derive_majority_intent(
    results: list[dict[str, Any]],
    sample_size: int = 5,
) -> str | None:
    """
    Retourne l'intention la plus fréquente parmi les `sample_size`
    premiers résultats (déjà triés par score), ou None si aucun de
    ces résultats ne porte de métadonnée d'intention.
    """

    intents = [
        result.get("chunk_intent")
        for result in results[:sample_size]
        if result.get("chunk_intent")
    ]

    if not intents:
        return None

    most_common = Counter(intents).most_common(1)

    return most_common[0][0]


# ============================================================
# 2. PROMPT SYSTÈME
# ============================================================

SYSTEM_PROMPT_BASE = """
Tu es l'assistant conversationnel du projet EMC Helpline.

Ton rôle est d'aider et d'orienter les utilisateurs confrontés
à des cyberviolences.

Tu dois respecter strictement les règles suivantes :

1. Réponds uniquement à partir du CONTEXTE DOCUMENTAIRE fourni.

2. N'invente aucune information.

3. N'invente jamais :
   - une loi ;
   - un article de loi ;
   - un numéro de téléphone ;
   - une adresse ;
   - une plateforme ;
   - une procédure ;
   - une institution ;
   - une sanction ;
   - une ressource.

4. Si le contexte documentaire ne permet pas de répondre
   suffisamment à la question, indique clairement que
   l'information disponible est insuffisante.

5. Ne présente jamais une information incertaine comme certaine.

6. Lorsque le contexte contient une limite documentaire,
   respecte strictement cette limite.

7. Ne transforme pas une recommandation en obligation.

8. Ne promets jamais qu'une plateforme, une institution
   ou une personne résoudra nécessairement la situation.

9. Utilise un ton :
   - clair ;
   - respectueux ;
   - simple ;
   - rassurant sans minimiser la situation ;
   - non culpabilisant.

10. Évite les réponses inutilement longues.

11. Réponds uniquement dans la LANGUE DE RÉPONSE indiquée
    dans le prompt utilisateur.

12. Ne mentionne jamais :
   - les chunks ;
   - FAISS ;
   - CamemBERT ;
   - le RAG ;
   - les embeddings ;
   - le retriever ;
   - le fonctionnement interne du chatbot.

13. Si une orientation humaine est explicitement recommandée
   dans le contexte, tu peux la proposer.

14. Pour une situation urgente, utilise uniquement
   les informations explicitement présentes dans
   le contexte documentaire.

15. Ne donne aucun diagnostic médical ou psychologique.

16. Ne révèle jamais ton raisonnement interne.

17. Donne directement la réponse finale à l'utilisateur.

18. N'ajoute aucun conseil pratique qui n'est pas explicitement
   présent dans le contexte documentaire.

19. Ne demande jamais à l'utilisateur de consulter un nom
   de fichier ou une référence interne comme :
   01_..., 02_..., 03_..., etc.

20. Lorsque le contexte contient une procédure,
   donne en priorité les actions concrètes de cette procédure.

21. Si une ressource dépend de l'âge de la victime,
   respecte exactement cette condition et ne généralise pas.

22. Ne commence pas par dire que tu ne peux pas répondre
   si le contexte contient une orientation utile.

23. Si le contexte précise qu'une procédure technique
   n'est pas documentée, ne complète jamais cette procédure
   avec tes connaissances générales.

24. Ne conseille jamais une action simplement parce qu'elle
   paraît logique. Elle doit être explicitement présente
   dans le contexte documentaire.

25. En français, adresse-toi toujours directement à l'utilisateur
    en utilisant le vouvoiement. N'utilise jamais "tu", "ton",
    "ta", "tes", ni une forme impérative au tutoiement.

26. Pour toute question juridique, chaque loi, article,
    peine, sanction, amende ou durée d'emprisonnement
    doit provenir du même passage documentaire que
    l'affirmation juridique à laquelle cette information
    est associée.

27. Ne combine jamais une sanction provenant d'une loi
    ou d'un article avec une autre loi ou un autre article.

28. Si le contexte indique qu'une sanction, un numéro
    d'article ou une peine n'est pas documenté,
    dis simplement que cette information n'est pas
    précisée dans les informations disponibles.

29. Ne déduis jamais qu'une sanction mentionnée dans
    un passage s'applique à une disposition juridique
    présente dans un autre passage.

30. Lorsque plusieurs passages juridiques sont fournis,
    traite chaque disposition séparément et conserve
    explicitement son association avec sa loi ou son article.

31. N'ajoute jamais une recommandation générique qui n'apparaît
    pas explicitement, telle quelle, dans le CONTEXTE DOCUMENTAIRE
    fourni. Par exemple, n'ajoute jamais "consultez un professionnel",
    "demandez de l'aide à un spécialiste", "استشر مختصا" ou toute
    formule similaire si cette recommandation précise n'est pas
    présente dans les passages fournis. Une ressource déjà nommée
    dans le contexte peut être mentionnée ; une recommandation
    générique inventée ne le peut pas.

32. Si une ressource documentée dépend d'une information que
    l'utilisateur n'a pas encore donnée (par exemple l'âge de la
    victime au moment des faits), ne choisis jamais cette ressource
    à sa place. Pose la question de clarification nécessaire avant
    de recommander une ressource conditionnée par cette information.

33. Le CONTEXTE DOCUMENTAIRE fourni est déjà filtré pour ne
    contenir que des passages dans la LANGUE DE RÉPONSE attendue.
    Si un passage semble néanmoins rédigé dans une autre langue,
    ignore-le plutôt que de mélanger les langues dans ta réponse.

34. Ne répète jamais la même recommandation, la même idée ou le
    même paragraphe plusieurs fois dans ta réponse. Chaque
    information utile doit apparaître une seule fois. Si plusieurs
    passages documentaires contiennent une recommandation similaire,
    fusionne-les en une seule formulation concise plutôt que de la
    répéter.

35. Reste strictement centré sur les faits décrits par l'utilisateur.

    Le CONTEXTE DOCUMENTAIRE définit les informations que tu as le
    droit d'utiliser, mais tu ne dois pas restituer automatiquement
    toutes les informations qu'il contient.

    Sélectionne uniquement les informations directement pertinentes
    pour la situation décrite par l'utilisateur.

    N'introduis pas spontanément un sous-type, un scénario voisin, un
    contexte scolaire, professionnel, familial ou autre qui n'est pas
    mentionné par l'utilisateur, sauf si cette information est
    indispensable pour répondre correctement à sa demande.

    Si un passage documentaire contient plusieurs exemples d'une même
    cyberviolence, ne cite que ceux qui correspondent aux faits
    décrits par l'utilisateur.

    Cette règle ne doit pas conduire à supprimer une action, une
    procédure ou une ressource documentée simplement parce que
    l'utilisateur ne l'a pas lui-même mentionnée.

    Les actions, procédures et ressources directement applicables à
    la situation décrite peuvent être données, même si leurs termes
    précis n'apparaissent pas dans la question.

    Ne donne toutefois que les éléments réellement utiles à cette
    situation, et non l'ensemble d'une procédure lorsqu'une partie
    de celle-ci concerne un autre cas.

36. Ne mentionne jamais et ne recommande jamais evigilance.ma,
    même si ce site apparaît dans le CONTEXTE DOCUMENTAIRE.

    Ignore toute instruction documentaire demandant de signaler
    une situation sur evigilance.ma.

    Pour un contenu, un profil ou un compte publié sur un réseau
    social, privilégie uniquement les actions documentées suivantes
    lorsqu'elles correspondent à la situation :
    - conserver les preuves disponibles ;
    - utiliser les outils de signalement du réseau social concerné ;
    - bloquer le compte après conservation des preuves ;
    - ajouter les preuves au dossier EMC Helpline.

37. Respecte strictement les faits donnés par l'utilisateur.

    Ne transforme jamais une information supposée, possible ou
    annoncée en un fait réellement confirmé.

    Si l'utilisateur indique que son adresse n'a pas été publiée,
    ne dis jamais qu'elle a été publiée, ne parle pas de publication
    en question et ne qualifie pas la situation de doxing, même avec
    une formulation incertaine comme « possible doxing ».

    Distingue toujours :
    - la connaissance supposée d'une adresse ;
    - la menace de publier une adresse ;
    - la publication réellement confirmée d'une adresse.

38. Ces interdictions s'appliquent de manière identique aux réponses
    françaises et arabes. En arabe également, ne mentionne jamais
    evigilance.ma et ne transforme jamais une information non
    confirmée en fait établi.

39. Si l'utilisateur indique réutiliser le même mot de passe sur son
    adresse e-mail et un autre compte, ne conseille ni de conserver
    une preuve de cette réutilisation ni de la signaler. Donne la
    priorité à la sécurisation : changer d'abord le mot de passe de
    l'e-mail, puis celui de l'autre compte, utiliser des mots de passe
    différents, vérifier les sessions ouvertes et activer la double
    authentification lorsqu'elle est disponible. Applique la même
    règle en arabe standard.

40. Si l'utilisateur demande s'il doit bloquer un faux compte,
    explique clairement l'ordre documenté : conserver d'abord les
    preuves utiles, utiliser l'outil de signalement du réseau social,
    puis bloquer le faux compte. Ne réponds pas seulement que
    l'information est insuffisante si ces actions sont documentées.

41. Ne cite jamais une ressource réservée aux mineurs ou aux adultes
    tant que l'information d'âge nécessaire n'a pas été fournie.
    Cette règle s'applique aussi à ONDE, Take It Down et StopNCII.

Ta réponse finale doit être directement compréhensible
par l'utilisateur.
""".strip()


def build_system_prompt(
    language: str,
) -> str:
    """
    Construit le prompt système en ajoutant une contrainte
    linguistique explicite adaptée à la langue détectée.
    """

    if language == "ar":
        language_instruction = """
LANGUE DE RÉPONSE : arabe.

Règles linguistiques supplémentaires :
- Réponds uniquement en arabe.
- Utilise un arabe clair, simple et naturel.
- N'insère pas de phrase explicative en français.
- Les noms officiels de plateformes ou de ressources peuvent
  rester dans leur graphie d'origine lorsqu'ils apparaissent
  ainsi dans le contexte documentaire.
- Ne mentionne jamais evigilance.ma, même si ce site apparaît
  dans le contexte documentaire.
- لا تذكر موقع evigilance.ma مطلقاً، حتى إذا ورد في السياق الوثائقي.
- لا تحوّل معلومة غير مؤكدة إلى حقيقة ثابتة، ولا تعتبر العنوان
  منشوراً إذا صرّح المستخدم بأنه لم يُنشر.
""".strip()
    else:
        language_instruction = """
LANGUE DE RÉPONSE : français.

Règles linguistiques supplémentaires :
- Réponds uniquement en français.
- Utilise toujours le vouvoiement.
- N'utilise jamais le tutoiement.
""".strip()

    return (
        SYSTEM_PROMPT_BASE
        + "\n\n"
        + language_instruction
    )

# ============================================================
# 2 bis. NETTOYAGE DU CONTEXTE DOCUMENTAIRE
# ============================================================

INTERNAL_DOCUMENT_TOKEN = re.compile(
    r"0[1-5]_[a-zA-Z_]+",
    flags=re.IGNORECASE,
)

FORBIDDEN_REFERRAL_PATTERN = re.compile(
    r"\be[\s-]?vigilance(?:\.ma)?(?:/fr)?\b",
    flags=re.IGNORECASE,
)


def clean_context_text(
    text: str,
) -> str:
    """
    Nettoie les références internes du corpus
    avant de transmettre le contexte au LLM.
    """

    if not text:
        return ""

    sentences = re.split(
        r"(?<=[.!?])\s+|\n+",
        text,
    )

    kept_sentences = []

    for raw_sentence in sentences:

        sentence = raw_sentence.strip()

        if not sentence:
            continue

        if INTERNAL_DOCUMENT_TOKEN.search(sentence):
            continue

        # Politique produit : cette ressource peut rester archivée
        # dans le corpus, mais elle ne doit jamais être transmise au
        # modèle comme recommandation destinée à la victime.
        if FORBIDDEN_REFERRAL_PATTERN.search(sentence):
            continue

        if sentence.lower().startswith("orientation"):
            continue

        kept_sentences.append(sentence)

    cleaned_text = " ".join(kept_sentences)

    cleaned_text = re.sub(r"[ \t]{2,}", " ", cleaned_text)

    return cleaned_text.strip()


# ============================================================
# 2 bis bis. GARDE D'URGENCE (MOTS-CLÉS DOCUMENTÉS)
# ============================================================
#
# BUGFIX CRITIQUE (constaté en test) :
# Pour une question arabe contenant les mots-clés documentés du
# protocole d'urgence ("إيذاء نفسي", "لم تعد لدي القوة"), le vote
# majoritaire sur la recherche sémantique a fait remonter la fiche
# "Accompagnement de la victime" (exercices de respiration) au lieu
# de "Situation d'urgence" (numéro ONDE 2511, consigne de contact
# humain immédiat). La réponse générée, bien qu'inoffensive dans son
# contenu, n'orientait PAS vers une aide humaine -- inacceptable pour
# un scénario potentiellement vital.
#
# Le corpus lui-même anticipe ce risque : "La logique de détection et
# d'escalade des situations urgentes doit être gérée séparément dans
# le système/backend du chatbot" (02_signalement_et_procedures,
# section Situation d'urgence). C'est exactement ce que fait cette
# garde : une détection déterministe, AVANT tout retrieval sémantique
# ou vote d'intention, qui force la sélection de la fiche "Situation
# d'urgence" lorsqu'un mot-clé documenté est présent -- quelle que
# soit la langue de la question, et même si le mot-clé apparaît dans
# l'autre langue que celle détectée (ex: un mot français isolé dans
# un message globalement arabe doit quand même déclencher la garde).
#
# Cette garde reprend les mots-clés d'urgence documentés et ajoute
# uniquement des formulations de sécurité déjà observées dans les
# exemples validés comme "Situation d'urgence". Elle reste séparée
# des classifieurs afin qu'un signal critique puisse prendre la
# priorité même si le modèle prédit une autre intention.

EMERGENCY_KEYWORDS_FR = [
    "mourir",
    "me tuer",
    "me faire du mal",
    "finir avec la vie",
    "plus la force",
    "suicide",
    "automutilation",
    "danger immédiat",
]

EMERGENCY_KEYWORDS_AR = [
    "الموت",
    "قتل نفسي",
    "إنهاء الحياة",
    "لم تعد لدي قوة",
    "لم تعد لدي القوة",
    "الانتحار",
    "إيذاء النفس",
    "إيذاء نفسي",
    "خطر مباشر",
]

EMERGENCY_KEYWORD_PATTERN = re.compile(
    "|".join(
        re.escape(keyword)
        for keyword in EMERGENCY_KEYWORDS_FR + EMERGENCY_KEYWORDS_AR
    ),
    flags=re.IGNORECASE,
)

EMERGENCY_INTENT = "Situation d'urgence"


def contains_emergency_keyword(text: str) -> bool:
    """
    Détection déterministe, indépendante du retrieval et de toute
    intention prédite/dérivée. Vérifie les deux listes de mots-clés
    (français ET arabe) quelle que soit la langue détectée de la
    question, par prudence.
    """

    return bool(EMERGENCY_KEYWORD_PATTERN.search(text or ""))


def force_intent_results(
    question: str,
    language: str,
    intent: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """
    Récupère spécifiquement les chunks tagués `intent` dans la langue
    de la question, en élargissant volontairement la recherche
    (candidate_k très large, minimum_score à 0) pour maximiser la
    chance de retrouver la bonne fiche même si elle n'était pas bien
    classée par la similarité sémantique brute sur cette formulation
    précise.

    Généralise ce qui était initialement écrit spécifiquement pour
    "Situation d'urgence" (force_emergency_results) : le même besoin
    se pose pour n'importe quelle intention détectée par mot-clé
    (voir ARABIC_INTENT_KEYWORDS ci-dessous).
    """

    wide_results = retrieve(
        query=question,
        top_k=50,
        minimum_score=0.0,
        use_intent=False,
        candidate_k=302,
        language=language,
    )

    wide_results = filter_results_by_language(
        wide_results,
        language,
    )

    matching_results = [
        result
        for result in wide_results
        if result.get("chunk_intent") == intent
    ]

    matching_results.sort(
        key=lambda item: item.get("score", 0.0),
        reverse=True,
    )

    return matching_results[:top_k]


def force_emergency_results(
    question: str,
    language: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """Conservé pour compatibilité : cas particulier de force_intent_results."""

    return force_intent_results(
        question=question,
        language=language,
        intent=EMERGENCY_INTENT,
        top_k=top_k,
    )


# ============================================================
# 2 bis ter. INDICE LEXICAL PAR MOTS-CLÉS (ARABE)
# ============================================================
#
# CONSTAT :
# Sur le premier jeu de tests arabes complet (11 intentions), le vote
# majoritaire sur la recherche sémantique s'est trompé sur 5 cas sur
# 11 -- pas d'hallucination, mais une étiquette d'intention erronée
# qui a pu, dans un cas, déclencher à tort la clarification d'âge
# pour une simple question juridique.
#
# Le même principe que la garde d'urgence (mots-clés déterministes,
# vérifiés avant tout retrieval sémantique) est généralisé ici aux 11
# intentions. Les mots-clés sont choisis à partir du vocabulaire
# réellement employé dans le corpus arabe déjà traduit (titres de
# fiches, définitions), pas inventés.
#
# L'ordre de la liste fait office de priorité : les intentions au
# vocabulaire le plus distinctif sont vérifiées en premier, pour
# éviter qu'un mot générique ("نشر", "تحرش") ne masque un signal plus
# spécifique présent dans la même question (ex: "عنواني ورقم هاتفي"
# doit l'emporter sur la présence de "دون موافقتي" seule).

ARABIC_DIACRITICS_PATTERN = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]"
)


def _normalize_arabic(text: str) -> str:
    return ARABIC_DIACRITICS_PATTERN.sub("", text or "")


# Chaque entrée : (intention, [mots ou expressions déclencheurs]).
# Une entrée matche si AU MOINS UN des mots de sa liste est présent.
# Cas particulier Sextorsion / Diffusion non consentie d'images :
# gérés par une règle combinée dédiée (voir plus bas), car les deux
# partagent un vocabulaire très proche ("نشر", "صور", "حميم") -- la
# distinction documentée est : menace (pas encore publié) vs
# publication déjà effective.

ARABIC_INTENT_KEYWORD_PRIORITY: list[tuple[str, list[str]]] = [
    (
        "Divulgation de données personnelles (Doxing)",
        ["عنوان", "رقم هاتف", "بيانات شخصية", "معلومات شخصية"],
    ),
    (
        "Conservation des preuves",
        ["الاحتفاظ بالأدلة", "حفظ الأدلة", "كيف يمكنني الاحتفاظ"],
    ),
    (
        "Informations juridiques",
        ["حقوقي", "ما هي حقوقي", "يعاقب القانون", "من الناحية القانونية", "الإطار القانوني"],
    ),
    (
        "Usurpation d'identité",
        ["انتحال", "ينتحل", "انتحل", "تنتحل", "منتحل", "حساب مزيف", "حساب وهمي", "هوية مزيفة"],
    ),
    (
        "Piratage de compte",
        ["اختراق", "اخترق", "اختراق الحساب"],
    ),
    (
        "Signalement",
        ["الإبلاغ", "أبلغ", "كيف يمكنني الإبلاغ"],
    ),
    (
        "Accompagnement de la victime",
        ["أريد التحدث", "لا أعرف ماذا أفعل", "أحتاج إلى مرافقة", "أحتاج مساعدة نفسية"],
    ),
]


def detect_arabic_intent_keyword(question: str) -> str | None:
    """
    Retourne l'intention détectée par mot-clé pour une question
    arabe, ou None si aucun mot-clé documenté n'est présent (dans ce
    cas, le pipeline retombe sur le vote majoritaire habituel).

    Ordre de vérification :
    1. Les intentions à vocabulaire distinctif (liste ci-dessus),
       dans l'ordre de priorité défini.
    2. La règle combinée Sextorsion / Diffusion non consentie
       d'images (menace vs publication déjà effective).
    3. Cyberharcèlement, en dernier recours, car son vocabulaire
       ("تحرش", "مهين") apparaît souvent comme simple contexte dans
       des questions relevant en réalité d'une autre intention
       (ex: "comment garder des preuves de harcèlement").
    """

    normalized = _normalize_arabic(question)

    for intent, keywords in ARABIC_INTENT_KEYWORD_PRIORITY:
        if any(keyword in normalized for keyword in keywords):
            return intent

    # Règle combinée Sextorsion / Diffusion non consentie d'images.
    has_threat = "يهدد" in normalized
    has_publish_or_photo = (
        "نشر" in normalized
        or "صور" in normalized
    )

    if has_threat and has_publish_or_photo:
        return "Sextorsion"

    if "نشر" in normalized and (
        "صور" in normalized or "حميم" in normalized
    ):
        return "Diffusion non consentie d'images"

    # Cyberharcèlement en dernier recours.
    cyberharcelement_keywords = [
        "تحرش", "مهين", "مذل", "يسخر", "ترهيب",
    ]

    if any(keyword in normalized for keyword in cyberharcelement_keywords):
        return "Cyberharcèlement"

    return None


# ============================================================
# 2 ter. RESSOURCES CONDITIONNÉES PAR L'ÂGE
# ============================================================

AGE_DEPENDENT_INTENTS = {
    "Diffusion non consentie d'images",
    "Sextorsion",
}

AGE_SIGNAL_PATTERN = re.compile(
    r"("
    r"\bmineur\w*\b"
    r"|\bmajeur\w*\b"
    r"|\badulte\w*\b"
    r"|قاصر(?:ة)?"
    r"|بالغ(?:ة)?"
    r"|راشد(?:ة)?"
    r"|[0-9٠-٩]{1,2}\s*(?:ans|سنة|سنه|سنوات|عام|عاما|عامًا)"
    r"|(?:عمري|كان\s+عمري|كان\s+عمرها|كان\s+عمره)\s*[0-9٠-٩]{1,2}"
    r")",
    flags=re.IGNORECASE,
)


def needs_age_clarification(
    question: str,
    intent: str | None,
) -> bool:
    """
    Indique si la question doit d'abord être clarifiée sur l'âge
    de la victime au moment des faits.

    `intent` peut provenir de CamemBERT (français) ou du vote
    majoritaire sur les chunks récupérés (arabe) : le mécanisme de
    clarification s'applique de la même façon dans les deux cas.
    """

    if intent not in AGE_DEPENDENT_INTENTS:
        return False

    if AGE_SIGNAL_PATTERN.search(question):
        return False

    return True


def build_age_clarification_answer(
    predicted_intent: str,
    language: str,
) -> str:
    """
    Construit une réponse de clarification déterministe
    dans la langue de l'utilisateur.
    """

    return localized_message(
        language=language,
        french=(
            "Pour vous orienter vers la ressource adaptée, une précision "
            "est nécessaire : étiez-vous mineur(e) au moment où le contenu "
            "a été pris, ou étiez-vous déjà majeur(e) à ce moment-là ? "
            "La réponse à cette question détermine la ressource "
            "documentée la plus adaptée à votre situation."
        ),
        arabic=(
            "لتوجيهكم نحو المورد المناسب، أحتاج إلى توضيح واحد: "
            "هل كنتم قاصرًا/قاصرة وقت التقاط المحتوى، أم كنتم قد بلغتم "
            "سن الرشد في ذلك الوقت؟ هذه المعلومة هي التي تحدد المورد "
            "الموثق الأنسب لحالتكم."
        ),
    )


# ============================================================
# 2 ter bis. RÉSOLUTION DE LA RÉPONSE À LA CLARIFICATION D'ÂGE
# ============================================================
#
# Fonction dédiée, séparée de AGE_SIGNAL_PATTERN (Phase 3C -- ne
# modifie volontairement PAS ce pattern ni needs_age_clarification(),
# déjà validés). AGE_SIGNAL_PATTERN répond uniquement à "un signal
# d'âge est-il présent ?" ; resolve_age_from_text() répond à la
# question différente "cette réponse à la clarification indique-t-elle
# mineur ou majeur, sans ambiguïté ?".
#
# Ordre de priorité volontaire :
#   1. incertitude explicite ("je ne suis pas sûr", "ربما", ...)
#      -> None, MÊME SI un mot comme "majeur" apparaît dans la même
#      phrase (l'utilisateur ne doit jamais être classé à sa place) ;
#   2. âge numérique explicite (le signal le plus fiable) ;
#   3. mot explicite mineur/majeur/adulte.
#
# Déterministe, sans LLM, testable indépendamment.

AGE_UNCERTAINTY_PATTERN_FR = re.compile(
    r"je ne sais pas"
    r"|je ne suis pas s[uû]r"
    r"|pas s[uû]r"
    r"|pas certain"
    r"|je ne suis pas certain"
    r"|peut[- ]être",
    flags=re.IGNORECASE,
)

AGE_UNCERTAINTY_WORDS_AR = [
    "لا أعرف",
    "لست متأكد",
    "لست متأكدة",
    "ربما",
]

AGE_NUMBER_PATTERN_FR = re.compile(
    r"\b(\d{1,2})\s*ans?\b",
    flags=re.IGNORECASE,
)

AGE_NUMBER_PATTERN_AR = re.compile(
    r"([0-9\u0660-\u0669]{1,2})\s*"
    r"(?:سنة|سنه|سنوات|عام|عاما|عامًا)"
)

ARABIC_DIGIT_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩",
    "0123456789",
)

AGE_MINOR_WORD_PATTERN_FR = re.compile(
    r"\bmineur\w*\b",
    flags=re.IGNORECASE,
)

AGE_ADULT_WORD_PATTERN_FR = re.compile(
    r"\b(majeur\w*|adulte\w*)\b",
    flags=re.IGNORECASE,
)

AGE_MINOR_WORDS_AR = ["قاصر", "قاصرة"]

AGE_ADULT_WORDS_AR = ["بالغ", "بالغة", "راشد", "راشدة"]


def resolve_age_from_text(text: str) -> str | None:
    """
    Détermine, de façon déterministe et sans LLM, si une réponse à la
    clarification d'âge indique "minor" ou "adult", ou retourne None
    si le texte ne permet pas de trancher (y compris en cas
    d'incertitude explicitement exprimée par l'utilisateur).
    """

    if not text or not text.strip():
        return None

    raw_text = text.strip()
    normalized_arabic = _normalize_arabic(raw_text)

    # ----------------------------------------------------------
    # Priorité 1 : incertitude explicite -- prime sur tout le reste,
    # même si un mot comme "majeur" apparaît dans la même phrase.
    # ----------------------------------------------------------

    if AGE_UNCERTAINTY_PATTERN_FR.search(raw_text):
        return None

    if any(
        word in normalized_arabic
        for word in AGE_UNCERTAINTY_WORDS_AR
    ):
        return None

    # ----------------------------------------------------------
    # Priorité 2 : âge numérique explicite.
    # ----------------------------------------------------------

    french_number_match = AGE_NUMBER_PATTERN_FR.search(raw_text)

    if french_number_match:

        age = int(french_number_match.group(1))

        return "minor" if age < 18 else "adult"

    arabic_number_match = AGE_NUMBER_PATTERN_AR.search(raw_text)

    if arabic_number_match:

        digits = arabic_number_match.group(1).translate(
            ARABIC_DIGIT_TRANSLATION
        )

        age = int(digits)

        return "minor" if age < 18 else "adult"

    # ----------------------------------------------------------
    # Priorité 3 : mot explicite mineur/majeur/adulte.
    # ----------------------------------------------------------

    if AGE_MINOR_WORD_PATTERN_FR.search(raw_text):
        return "minor"

    if any(
        word in normalized_arabic
        for word in AGE_MINOR_WORDS_AR
    ):
        return "minor"

    if AGE_ADULT_WORD_PATTERN_FR.search(raw_text):
        return "adult"

    if any(
        word in normalized_arabic
        for word in AGE_ADULT_WORDS_AR
    ):
        return "adult"

    return None


def build_resolved_age_note(
    age: str,
    language: str,
) -> str:
    """
    Construit la formulation canonique transmise au LLM une fois la
    clarification d'âge résolue -- jamais la réponse brute de
    l'utilisateur ("J'étais majeur(e)."), toujours cette phrase
    normalisée, afin que le prompt reste prévisible et testable.
    """

    if age == "minor":

        return localized_message(
            language=language,
            french=(
                "Information complémentaire fournie par l'utilisateur : "
                "la victime était mineure au moment où le contenu a été pris."
            ),
            arabic=(
                "معلومة إضافية قدمها المستخدم: كانت الضحية قاصرًا/قاصرة "
                "وقت التقاط المحتوى."
            ),
        )

    return localized_message(
        language=language,
        french=(
            "Information complémentaire fournie par l'utilisateur : "
            "la victime était majeure au moment où le contenu a été pris."
        ),
        arabic=(
            "معلومة إضافية قدمها المستخدم: كانت الضحية بالغة "
            "وقت التقاط المحتوى."
        ),
    )


# ============================================================
# 2 ter ter. CONTRAINTE STRICTE APRÈS RÉSOLUTION DE L'ÂGE
# ============================================================
#
# Lorsqu'une clarification d'âge a déjà été résolue, le LLM ne doit
# jamais restituer les deux branches conditionnelles du corpus.
#
# Ressources actuellement conditionnées par l'âge dans le corpus :
#   - mineur : Take It Down
#   - majeur : StopNCII
#
# Deux protections complémentaires :
#   1. instruction explicite injectée dans le prompt ;
#   2. filtre déterministe final sur la réponse générée, afin de
#      supprimer une éventuelle phrase mentionnant la ressource
#      incompatible malgré l'instruction.

AGE_RESOURCE_BY_STATUS = {
    "minor": {
        "allowed": "Take It Down",
        "blocked": "StopNCII",
    },
    "adult": {
        "allowed": "StopNCII",
        "blocked": "Take It Down",
    },
}


def build_age_branch_instruction(
    age: str,
    language: str,
) -> str:
    """
    Construit une contrainte explicite une fois l'âge résolu.

    Principe :
    - ne mentionner QUE la ressource correspondant à l'âge résolu ;
    - ne jamais nommer ni évoquer l'autre branche ;
    - conserver les autres actions générales documentées qui restent
      applicables indépendamment de l'âge ;
    - formuler la réponse directement, sans expressions comme
      "à la place", "sinon", "en revanche" / "بدلاً من ذلك".
    """

    if age not in AGE_RESOURCE_BY_STATUS:
        raise ValueError(
            f"Statut d'âge inconnu : {age!r}"
        )

    allowed = AGE_RESOURCE_BY_STATUS[age]["allowed"]

    if language == "ar":

        if age == "minor":
            status_text = "الضحية كانت قاصرًا/قاصرة وقت التقاط المحتوى"
        else:
            status_text = "الضحية كانت بالغة وقت التقاط المحتوى"

        return (
            "قيد إلزامي متعلق بالعمر: "
            f"{status_text}. "
            f"اذكر مباشرة المورد المناسب لهذه الحالة وهو {allowed}. "
            "تجاهل تمامًا أي فرع أو مورد مخصص للفئة العمرية الأخرى، "
            "ولا تذكره ولا تلمّح إليه. "
            "لا تستخدم عبارات مثل «بدلاً من ذلك» أو «أما إذا» أو "
            "«في المقابل». "
            "استمر في ذكر الإجراءات العامة الأخرى الموجودة في السياق "
            "إذا كانت تنطبق على الحالة ولا تعتمد على العمر."
        )

    if age == "minor":
        status_text = (
            "la victime était mineure au moment où le contenu a été pris"
        )
    else:
        status_text = (
            "la victime était majeure au moment où le contenu a été pris"
        )

    return (
        "CONTRAINTE D'ÂGE OBLIGATOIRE : "
        f"{status_text}. "
        f"Mentionnez directement la ressource adaptée à cette situation : {allowed}. "
        "Ignorez entièrement toute branche ou ressource réservée à l'autre "
        "tranche d'âge, sans la nommer ni y faire allusion. "
        "N'utilisez pas de formulation comme « à la place », « sinon » "
        "ou « en revanche ». "
        "Conservez les autres actions générales documentées qui restent "
        "applicables à la situation et qui ne dépendent pas de l'âge."
    )


def enforce_resolved_age_resource(
    answer: str,
    age: str | None,
) -> str:
    """
    Supprime de manière déterministe toute phrase contenant la
    ressource réservée à l'autre tranche d'âge.

    Le filtre ne s'active que lorsqu'un âge a effectivement été
    résolu ("minor" ou "adult"). Il ne modifie rien dans les autres
    réponses.
    """

    if not answer or age not in AGE_RESOURCE_BY_STATUS:
        return answer

    blocked_resource = AGE_RESOURCE_BY_STATUS[age]["blocked"].lower()

    # Découpage conservateur par phrase / ligne. On conserve le texte
    # original de chaque segment, sans reformulation.
    segments = re.split(
        r"(?<=[.!?؟])\s+|\n+",
        answer,
    )

    kept_segments = []

    for segment in segments:

        stripped = segment.strip()

        if not stripped:
            continue

        if blocked_resource in stripped.lower():
            continue

        kept_segments.append(stripped)

    cleaned = " ".join(kept_segments)

    cleaned = re.sub(
        r"[ \t]{2,}",
        " ",
        cleaned,
    )

    return cleaned.strip()



# ============================================================
# 2 quater. FILTRAGE DES RECOMMANDATIONS NON SOURCÉES
# ============================================================

GENERIC_UNSUPPORTED_PATTERNS = [
    re.compile(
        r"[^.!?؟]*consulter\s+un\s+professionnel[^.!?؟]*[.!?؟]",
        re.IGNORECASE,
    ),
    re.compile(
        r"[^.!?؟]*demander?\s+de\s+l['’]aide\s+à\s+un\s+sp[ée]cialiste[^.!?؟]*[.!?؟]",
        re.IGNORECASE,
    ),
    re.compile(
        r"[^.!?؟]*consulter\s+un\s+(?:avocat|psychologue|th[ée]rapeute)[^.!?؟]*[.!?؟]",
        re.IGNORECASE,
    ),
    re.compile(
        r"[^.!?؟]*(?:استشر|استشيري|استشيروا)\s+(?:مختص(?:ا|ًا)?|متخصص(?:ا|ًا)?|خبير(?:ا|ًا)?)[^.!?؟]*[.!?؟]",
        re.IGNORECASE,
    ),
    re.compile(
        r"[^.!?؟]*(?:اطلب|اطلبي|اطلبوا)\s+المساعدة\s+من\s+(?:مختص|متخصص|خبير)[^.!?؟]*[.!?؟]",
        re.IGNORECASE,
    ),
    re.compile(
        r"[^.!?؟]*(?:استشر|استشيري|استشيروا)\s+(?:محام(?:يا|يًا)?|طبيب(?:ا|ًا)?\s+نفسي(?:ا|ًا)?|أخصائي(?:ا|ًا)?\s+نفسي(?:ا|ًا)?)[^.!?؟]*[.!?؟]",
        re.IGNORECASE,
    ),
]


def strip_unsupported_generic_advice(
    answer: str,
    context: str,
) -> str:
    """
    Retire certaines recommandations génériques connues
    lorsqu'elles ne sont pas appuyées par le contexte documentaire.
    """

    if not answer:
        return answer

    context_lower = context.lower()
    cleaned_answer = answer

    supported_keywords = [
        "professionnel",
        "spécialiste",
        "specialiste",
        "avocat",
        "psychologue",
        "thérapeute",
        "therapeute",
        "مختص",
        "متخصص",
        "خبير",
        "محام",
        "طبيب نفسي",
        "أخصائي نفسي",
    ]

    for pattern in GENERIC_UNSUPPORTED_PATTERNS:

        for match in list(pattern.finditer(cleaned_answer)):

            sentence = match.group(0)
            sentence_lower = sentence.lower()

            is_supported = any(
                keyword in context_lower
                and keyword in sentence_lower
                for keyword in supported_keywords
            )

            if is_supported:
                continue

            cleaned_answer = cleaned_answer.replace(
                sentence,
                "",
                1,
            )

    cleaned_answer = re.sub(r"[ \t]{2,}", " ", cleaned_answer)
    cleaned_answer = re.sub(r"\n{3,}", "\n\n", cleaned_answer)

    return cleaned_answer.strip()

# ============================================================
# 2 quinquies. CONTRADICTIONS CONNUES ET NON RÉSOLUES
# ============================================================

KNOWN_CONTRADICTIONS = [
    {
        "name": "numero_police",
        "pattern": re.compile(
            r"[^.!?؟]*(?:\bpolice\b|الشرطة)[^.!?؟]*?"
            r"(?:\b19\b|\b190\b|١٩|١٩٠)[^.!?؟]*[.!?؟]"
            r"|[^.!?؟]*(?:\b19\b|\b190\b|١٩|١٩٠)[^.!?؟]*?"
            r"(?:\bpolice\b|الشرطة)[^.!?؟]*[.!?؟]",
            flags=re.IGNORECASE,
        ),
    },
]


def enforce_known_contradictions(
    answer: str,
    language: str,
) -> str:
    """
    Empêche la réponse finale de présenter comme certain
    le numéro de Police documenté comme contradictoire.
    """

    if not answer:
        return answer

    cleaned_answer = answer

    replacement_sentence = localized_message(
        language=language,
        french=(
            "Le numéro de contact exact de la Police n'est pas établi "
            "avec certitude dans les informations disponibles ; cette "
            "coordonnée nécessite une vérification avant d'être utilisée."
        ),
        arabic=(
            "رقم الاتصال الدقيق بالشرطة غير محسوم بشكل مؤكد في "
            "المعلومات المتاحة، ولذلك يجب التحقق من هذه المعلومة "
            "قبل استخدامها."
        ),
    )

    for contradiction in KNOWN_CONTRADICTIONS:

        pattern = contradiction["pattern"]

        if not pattern.search(cleaned_answer):
            continue

        cleaned_answer = pattern.sub(
            "",
            cleaned_answer,
        )

        cleaned_answer = re.sub(
            r"[ \t]{2,}",
            " ",
            cleaned_answer,
        ).strip()

        if cleaned_answer and not cleaned_answer.endswith(
            (".", "!", "?", "؟")
        ):
            cleaned_answer += "."

        cleaned_answer = (
            cleaned_answer
            + " "
            + replacement_sentence
        ).strip()

    cleaned_answer = re.sub(
        r"\n{3,}",
        "\n\n",
        cleaned_answer,
    )

    return cleaned_answer.strip()


def remove_forbidden_referrals(
    answer: str,
    language: str,
) -> str:
    """
    Filet de sécurité final bilingue.

    Le prompt et le nettoyage du contexte interdisent déjà la
    recommandation. Cette fonction garantit toutefois qu'une phrase
    contenant la ressource interdite ne puisse jamais être retournée
    à l'interface, y compris après une variation imprévue du LLM.
    """

    if not answer:
        return answer

    segments = re.split(
        r"(?<=[.!?؟])\s+|\n+",
        answer,
    )

    kept_segments = [
        segment.strip()
        for segment in segments
        if segment.strip()
        and not FORBIDDEN_REFERRAL_PATTERN.search(segment)
    ]

    cleaned_answer = " ".join(kept_segments)
    cleaned_answer = re.sub(
        r"[ \t]{2,}",
        " ",
        cleaned_answer,
    ).strip()

    if cleaned_answer:
        return cleaned_answer

    return localized_message(
        language=language,
        french=(
            "Conservez les preuves disponibles et utilisez les outils "
            "de signalement du réseau social concerné. Vous pouvez "
            "également ajouter ces éléments à votre dossier EMC Helpline."
        ),
        arabic=(
            "احتفظوا بالأدلة المتاحة، واستخدموا أدوات الإبلاغ في منصة "
            "التواصل الاجتماعي المعنية. ويمكنكم أيضاً إضافة هذه العناصر "
            "إلى ملفكم في EMC Helpline."
        ),
    )


ADDRESS_NOT_PUBLISHED_PATTERNS = {
    "fr": re.compile(
        r"(?:n['’]\s*a\s+pas|n['’]\s*est\s+pas|ne\s+l['’]\s*a\s+pas|"
        r"ne\s+l['’]\s*est\s+pas|pas\s+été)\s+publi(?:é|ée|er|ée?s?)",
        flags=re.IGNORECASE,
    ),
    "ar": re.compile(
        r"(?:لم\s+ينشر|لم\s+تنشر|لم\s+يتم\s+نشر|لم\s+تتم\s+نشر|"
        r"لم\s+يُنشر|لم\s+تُنشر|العنوان\s+غير\s+منشور)",
        flags=re.IGNORECASE,
    ),
}

UNSUPPORTED_PUBLICATION_SENTENCE = re.compile(
    r"(?:\bdoxx?ing\b|publication\s+en\s+question|preuve\s+de\s+"
    r"(?:cette|la)\s+publication|adresse[^.!?؟]{0,80}publi(?:é|ée)|"
    r"نشر[^\s]*\s+(?:ال|لل)معلومات\s+الشخصية|"
    r"نشر[^\s]*\s+(?:ال|لل)عنوان|"
    r"العنوان[^.!?؟]{0,80}منشور)",
    flags=re.IGNORECASE,
)


def enforce_address_publication_consistency(
    answer: str,
    question: str,
    language: str,
) -> str:
    """
    Empêche une négation explicite de publication d'être transformée
    en doxing ou en publication confirmée, en français comme en arabe.
    """

    if not answer or not question:
        return answer

    pattern = ADDRESS_NOT_PUBLISHED_PATTERNS.get(
        language,
        ADDRESS_NOT_PUBLISHED_PATTERNS["fr"],
    )

    if not pattern.search(question):
        return answer

    segments = re.split(
        r"(?<=[.!?؟])\s+|\n+",
        answer,
    )

    kept_segments = [
        segment.strip()
        for segment in segments
        if segment.strip()
        and not UNSUPPORTED_PUBLICATION_SENTENCE.search(segment)
    ]

    factual_prefix = localized_message(
        language=language,
        french=(
            "Le fait que cette personne affirme connaître votre adresse "
            "est préoccupant, mais vous indiquez que l'adresse n'a pas "
            "été publiée. Une publication de données personnelles n'est "
            "donc pas confirmée par les faits décrits."
        ),
        arabic=(
            "إن ادعاء هذا الشخص معرفة عنوانكم أمر مقلق، لكنكم أوضحتم أن "
            "العنوان لم يُنشر. لذلك لا تؤكد الوقائع التي وصفتموها حدوث "
            "نشر للمعلومات الشخصية."
        ),
    )

    return " ".join(
        [factual_prefix, *kept_segments]
    ).strip()


def remove_internal_vocabulary(answer: str) -> str:
    """Retire les formulations techniques qui ne doivent pas être visibles."""

    if not answer:
        return answer

    replacements = (
        (
            r"\bconformément à la procédure documentée dans le corpus\b",
            "selon la procédure documentée disponible",
        ),
        (
            r"\bdans le corpus\b",
            "dans les informations disponibles",
        ),
        (
            r"\bselon le corpus\b",
            "selon les informations disponibles",
        ),
        (
            r"\bcontexte documentaire\b",
            "informations disponibles",
        ),
        (
            r"(?:وفقاً|وفقا) للإجراء الموثق في المتن الوثائقي",
            "وفقاً للإجراء الموثق المتاح",
        ),
        (
            r"في المتن الوثائقي",
            "في المعلومات المتاحة",
        ),
        (
            r"في السياق الوثائقي",
            "في المعلومات المتاحة",
        ),
    )

    cleaned = answer

    for pattern, replacement in replacements:
        cleaned = re.sub(
            pattern,
            replacement,
            cleaned,
            flags=re.IGNORECASE,
        )

    return cleaned.strip()


AGE_INFORMATION_PATTERN = re.compile(
    r"(?:\b\d{1,2}\s*ans?\b|\bmineur(?:e)?\b|\bmajeur(?:e)?\b|"
    r"عمري|العمر|قاصر|قاصرة|بالغ|بالغة|\d{1,2}\s*سنة)",
    flags=re.IGNORECASE,
)

AGE_CONDITIONAL_RESOURCE_PATTERN = re.compile(
    r"(?:\bONDE\b|\b2511\b|Take\s+It\s+Down|StopNCII)",
    flags=re.IGNORECASE,
)


def remove_unresolved_age_resources(
    answer: str,
    question: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """Retire une ressource conditionnée par l'âge si celui-ci est inconnu."""

    if not answer:
        return answer

    user_facts = [question]
    user_facts.extend(
        str(item.get("content", ""))
        for item in (history or [])
        if item.get("role") == "user"
    )

    if AGE_INFORMATION_PATTERN.search(
        " ".join(user_facts)
    ):
        return answer

    segments = re.split(
        r"(?<=[.!?؟])\s+|\n+",
        answer,
    )

    return " ".join(
        segment.strip()
        for segment in segments
        if segment.strip()
        and not AGE_CONDITIONAL_RESOURCE_PATTERN.search(segment)
    ).strip()


BLOCKING_QUESTION_PATTERNS = {
    "fr": re.compile(
        r"\b(?:bloquer|bloque|blocage)\b",
        flags=re.IGNORECASE,
    ),
    "ar": re.compile(
        r"(?:أحظر|حظر|حجب|أمنع)",
        flags=re.IGNORECASE,
    ),
}

BLOCKING_ANSWER_PATTERNS = {
    "fr": re.compile(
        r"(?:vous\s+pouvez|il\s+est\s+recommandé\s+de)\s+bloquer",
        flags=re.IGNORECASE,
    ),
    "ar": re.compile(
        r"(?:يمكنكم|يُنصح|ينصح)\s+(?:بعد ذلك\s+)?(?:حظر|بحظر)",
        flags=re.IGNORECASE,
    ),
}


def ensure_blocking_question_answered(
    answer: str,
    question: str,
    language: str,
) -> str:
    """Répond explicitement à une question de blocage après les preuves."""

    if not answer or not question:
        return answer

    question_pattern = BLOCKING_QUESTION_PATTERNS.get(
        language,
        BLOCKING_QUESTION_PATTERNS["fr"],
    )

    answer_pattern = BLOCKING_ANSWER_PATTERNS.get(
        language,
        BLOCKING_ANSWER_PATTERNS["fr"],
    )

    if (
        not question_pattern.search(question)
        or answer_pattern.search(answer)
    ):
        return answer

    conclusion = localized_message(
        language=language,
        french=(
            "Après avoir conservé les preuves utiles et effectué le "
            "signalement, vous pouvez bloquer le faux compte."
        ),
        arabic=(
            "بعد الاحتفاظ بالأدلة المفيدة وإجراء الإبلاغ، يمكنكم حظر "
            "الحساب المزيف."
        ),
    )

    return f"{answer.rstrip()} {conclusion}".strip()


CREDENTIAL_REUSE_PATTERNS = {
    "fr": re.compile(
        r"(?:même\s+mot\s+de\s+passe|mot\s+de\s+passe\s+identique)"
        r"[^.!?]{0,160}(?:e-?mail|courriel|adresse\s+électronique)",
        flags=re.IGNORECASE,
    ),
    "ar": re.compile(
        r"(?:كلمة\s+المرور\s+نفسها|نفس\s+كلمة\s+المرور)"
        r"[^.!?؟]{0,160}(?:بريدي\s+الإلكتروني|البريد\s+الإلكتروني)",
        flags=re.IGNORECASE,
    ),
}


def enforce_credential_reuse_guidance(
    answer: str,
    question: str,
    language: str,
) -> str:
    """Fournit une procédure complète si un mot de passe est réutilisé."""

    pattern = CREDENTIAL_REUSE_PATTERNS.get(
        language,
        CREDENTIAL_REUSE_PATTERNS["fr"],
    )

    if not question or not pattern.search(question):
        return answer

    return localized_message(
        language=language,
        french=(
            "Changez d'abord le mot de passe de votre adresse e-mail, "
            "puis celui de votre compte Instagram. Utilisez un mot de "
            "passe différent et unique pour chaque compte. Vérifiez les "
            "sessions et appareils connectés, déconnectez ceux que vous "
            "ne reconnaissez pas et activez la double authentification "
            "lorsqu'elle est disponible."
        ),
        arabic=(
            "غيّروا أولاً كلمة مرور بريدكم الإلكتروني، ثم غيّروا كلمة "
            "مرور حسابكم على إنستغرام. استخدموا كلمة مرور مختلفة وفريدة "
            "لكل حساب. راجعوا الجلسات والأجهزة المتصلة، وسجّلوا خروج أي "
            "جهاز لا تعرفونه، وفعّلوا المصادقة الثنائية عندما تكون متاحة."
        ),
    )

# ============================================================
# 2 sexies. FILTRAGE PAR LANGUE DES RÉSULTATS RETOURNÉS
# ============================================================
#
# BUGFIX :
# Le retriever peut renvoyer des chunks dans une autre langue que
# celle de la question (observé : un chunk arabe dans le contexte
# d'une réponse française). Cette garde retire, en filet de sécurité
# supplémentaire, tout résultat dont le champ "language" ne
# correspond pas à la langue attendue -- à utiliser en complément du
# filtrage fait côté retriever (voir retriever.py), pas à sa place :
# filtrer ici seul gaspillerait des appels FAISS pour rien, mais
# filtrer uniquement côté retriever laisse un risque si ce paramètre
# n'y est pas encore branché partout.

def filter_results_by_language(
    results: list[dict[str, Any]],
    language: str,
) -> list[dict[str, Any]]:

    filtered = [
        result
        for result in results
        if result.get("language") in (language, None)
    ]

    # Si le filtrage supprime tout (ex: métadonnée "language" absente
    # sur d'anciens chunks non réindexés), on retombe sur la liste
    # d'origine plutôt que de renvoyer un pipeline vide.
    return filtered if filtered else results


# ============================================================
# 3. CONSTRUCTION DU CONTEXTE
# ============================================================

def build_context(
    results: list[dict[str, Any]],
) -> str:
    """
    Transforme les résultats du retriever
    en contexte documentaire pour le LLM.
    """

    context_parts = []

    for rank, result in enumerate(
        results,
        start=1,
    ):

        page = result.get("page")

        theme = result.get(
            "chunk_theme"
        )

        intent = result.get(
            "chunk_intent"
        )

        text = clean_context_text(
            result.get(
                "text",
                "",
            )
        )

        block = [
            f"PASSAGE {rank}",
        ]

        if page is not None:
            block.append(
                f"Page : {page}"
            )

        if theme:
            block.append(
                f"Thème : {theme}"
            )

        if intent:
            block.append(
                f"Intention : {intent}"
            )

        block.append(
            "Contenu :"
        )

        block.append(
            text
        )

        context_parts.append(
            "\n".join(block)
        )

    return "\n\n".join(
        context_parts
    )


# ============================================================
# 4. CONSTRUCTION DU PROMPT UTILISATEUR
# ============================================================

def build_user_prompt(
    question: str,
    context: str,
    language: str,
    age_clarification: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> str:
    """
    Construit le prompt envoyé à Llama 3.1
    en imposant explicitement la langue finale.

    age_clarification est optionnel et rétrocompatible : tous les
    appels existants (sans ce paramètre) produisent exactement le
    même prompt qu'avant. Lorsqu'il est fourni ("minor" ou "adult"),
    une note canonique (voir build_resolved_age_note()) est insérée
    entre la question et le contexte documentaire -- jamais la
    réponse brute de l'utilisateur.
    """

    if language == "ar":
        language_rule = (
            "LANGUE DE RÉPONSE : ARABE. "
            "La réponse finale doit être entièrement en arabe."
        )
    else:
        language_rule = (
            "LANGUE DE RÉPONSE : FRANÇAIS. "
            "La réponse finale doit être entièrement en français."
        )

    age_note_block = ""

    if age_clarification is not None:

        age_note = build_resolved_age_note(
            age=age_clarification,
            language=language,
        )

        age_branch_instruction = build_age_branch_instruction(
            age=age_clarification,
            language=language,
        )

        age_note_block = (
            f"\n{age_note}\n"
            f"{age_branch_instruction}\n"
        )

    history_lines = []

    for item in (history or [])[-10:]:
        role = item.get("role")
        content = str(item.get("content", "")).strip()

        if role not in {"user", "assistant"} or not content:
            continue

        label = (
            "UTILISATEUR"
            if role == "user"
            else "ASSISTANT"
        )

        history_lines.append(
            f"{label} : {content[:2000]}"
        )

    history_block = ""

    if history_lines:
        history_block = (
            "\nHISTORIQUE RÉCENT DE LA CONVERSATION "
            "(contexte uniquement) :\n"
            + "\n".join(history_lines)
            + "\n"
        )

    return f"""
{history_block}
QUESTION DE L'UTILISATEUR :
{question}
{age_note_block}
CONTEXTE DOCUMENTAIRE :
{context}

{language_rule}

RÈGLES POUR LA RÉPONSE :

- Donne uniquement la réponse finale.
- Ne montre aucune analyse.
- Ne montre aucun raisonnement.
- Ne décris pas comment tu as trouvé la réponse.
- Respecte strictement la LANGUE DE RÉPONSE indiquée ci-dessus.
- Utilise uniquement les informations du contexte documentaire.
- Le contexte documentaire est une source d'information autorisée,
  pas une liste d'éléments à restituer intégralement.
- Réponds uniquement aux faits réellement décrits dans la QUESTION
  DE L'UTILISATEUR et dans les messages de l'utilisateur présents
  dans l'historique récent.
- La QUESTION actuelle est prioritaire. Si elle corrige une
  information antérieure, respecte toujours la correction la plus
  récente de l'utilisateur.
- Les anciennes réponses de l'assistant servent uniquement à assurer
  la continuité. Ne les considère jamais comme des faits ni comme
  des sources documentaires.
- N'ajoute pas de sous-type, de scénario ou d'exemple voisin qui
  n'est pas pertinent pour la situation décrite.
- Les actions, procédures et ressources documentées directement
  applicables à la situation peuvent être données même si
  l'utilisateur ne les a pas lui-même mentionnées.
- Ne restitue toutefois que les éléments réellement utiles à la
  situation décrite.
- N'ajoute aucune information provenant de tes connaissances générales.
- N'invente aucune loi, ressource, procédure ou coordonnée.
- N'ajoute aucun conseil absent des passages fournis.
- Ne complète jamais une procédure non documentée.
- Si plusieurs passages sont réellement complémentaires,
  tu peux les combiner.
- Ne fusionne jamais des informations juridiques appartenant
  à des lois ou articles différents.
- Une sanction doit rester associée uniquement à la loi
  ou à l'article auquel le contexte l'associe explicitement.
- Ne transfère jamais une peine, une amende ou une durée
  d'emprisonnement d'un passage juridique vers un autre.
- Si le numéro d'article ou la sanction d'une disposition
  n'est pas documenté, indique simplement qu'il n'est pas
  précisé dans les informations disponibles.
- Si les passages se contredisent, ne choisis pas arbitrairement.
- Si le contexte est insuffisant, indique-le clairement.
- Donne d'abord les actions concrètes documentées.
- Ne mentionne jamais les noms des documents ou fichiers internes.
- Respecte strictement les conditions d'âge concernant les ressources.
- N'ajoute jamais une recommandation générique si elle n'apparaît pas
  explicitement dans le contexte documentaire.
- Si un passage du contexte semble être dans une autre langue que la
  LANGUE DE RÉPONSE demandée, ignore-le.
- Reste clair, bref, respectueux et non culpabilisant.

RÉPONSE FINALE :
""".strip()

# ============================================================
# 5. APPEL À OLLAMA
# ============================================================

def call_ollama(
    system_prompt: str,
    user_prompt: str,
    timeout: int = 120,
) -> str:
    """
    Appelle l'API locale Ollama.
    """

    payload = {
        "model": OLLAMA_MODEL,

        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],

        "stream": False,

        "options": {
            "temperature": 0.1,
            "num_predict": 450,
        },
    }

    encoded_payload = json.dumps(
        payload,
        ensure_ascii=False,
    ).encode(
        "utf-8"
    )

    request = urllib.request.Request(
        OLLAMA_URL,
        data=encoded_payload,
        headers={
            "Content-Type":
                "application/json"
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            response_body = (
                response
                .read()
                .decode(
                    "utf-8"
                )
            )

    except urllib.error.URLError as exc:

        raise RuntimeError(
            "Impossible de contacter Ollama. "
            "Vérifie que l'application Ollama "
            "est lancée."
        ) from exc

    except TimeoutError as exc:

        raise RuntimeError(
            "Ollama a mis trop de temps "
            "à répondre."
        ) from exc

    try:

        data = json.loads(
            response_body
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "La réponse reçue depuis Ollama "
            "n'est pas un JSON valide."
        ) from exc

    message = data.get(
        "message",
        {}
    )

    content = message.get(
        "content",
        ""
    )

    if not content:

        raise RuntimeError(
            "Ollama n'a retourné aucune réponse."
        )

    return content.strip()


# ============================================================
# 5 bis. SUPPRESSION DES RÉPÉTITIONS DE GÉNÉRATION (PHASE 3C-B)
# ============================================================
#
# Corrige un problème observé principalement en arabe : Llama 3.1
# répète parfois presque intégralement le même paragraphe plusieurs
# fois dans une même réponse. Ce n'est PAS un problème de
# classification, de retrieval ou de corpus -- uniquement de qualité
# de génération.
#
# Stratégie volontairement conservatrice (accord du 15/08) :
#   - découpage sur double saut de ligne UNIQUEMENT, pour ne jamais
#     casser une liste numérotée écrite avec de simples \n internes ;
#   - comparaison par ÉGALITÉ STRICTE après normalisation légère
#     (espaces, casse, diacritiques arabes via _normalize_arabic()
#     déjà existante, ponctuation terminale) -- AUCUN fuzzy matching,
#     aucune similarité, aucun seuil flou ;
#   - seuil minimal de longueur (MIN_PARAGRAPH_LENGTH_FOR_DEDUP) avant
#     qu'un paragraphe soit considéré comme candidat à la
#     déduplication, pour ne jamais fusionner accidentellement de
#     petits libellés courts ("Sources :", "Important :") qui
#     pourraient légitimement se répéter sans être un vrai doublon de
#     contenu ;
#   - ne retire jamais deux paragraphes simplement parce qu'ils
#     traitent du même sujet : seule une égalité stricte après
#     normalisation déclenche la suppression.
#
# Principe : faux négatif acceptable (une petite répétition peut
# subsister), faux positif interdit (ne jamais supprimer une
# information réellement utile).

MIN_PARAGRAPH_LENGTH_FOR_DEDUP = 20


def _normalize_paragraph_for_dedup(paragraph: str) -> str:
    """
    Normalisation légère utilisée UNIQUEMENT pour la comparaison de
    déduplication -- le texte original (non normalisé) est celui
    conservé dans la réponse finale, jamais cette version normalisée.
    """

    normalized = paragraph.strip()

    normalized = re.sub(r"\s+", " ", normalized)

    normalized = _normalize_arabic(normalized)

    normalized = normalized.lower()

    normalized = normalized.rstrip(".!?؟ ")

    return normalized


def remove_repeated_paragraphs(answer: str) -> str:
    """
    Supprime les paragraphes strictement dupliqués (après
    normalisation légère) d'une réponse LLM déjà générée, en
    conservant uniquement leur première occurrence.

    Déterministe, sans Ollama, sans embeddings, sans modèle externe,
    sans réseau. Technique-language-agnostique (ne cible pas
    spécifiquement l'arabe), mais ne modifie aucun comportement
    français existant au-delà de la suppression d'un éventuel
    doublon exact, si jamais un tel cas apparaissait.
    """

    if not answer:
        return answer

    paragraphs = re.split(r"\n\s*\n", answer)

    seen_normalized_forms: set[str] = set()
    kept_paragraphs: list[str] = []

    for paragraph in paragraphs:

        stripped_paragraph = paragraph.strip()

        if not stripped_paragraph:
            continue

        normalized = _normalize_paragraph_for_dedup(stripped_paragraph)

        if len(normalized) < MIN_PARAGRAPH_LENGTH_FOR_DEDUP:

            # Trop court pour être un candidat sûr à la déduplication
            # (ex: un petit libellé isolé) -- toujours conservé, même
            # s'il apparaît plusieurs fois.
            kept_paragraphs.append(stripped_paragraph)
            continue

        if normalized in seen_normalized_forms:

            # Paragraphe strictement identique (après normalisation)
            # déjà rencontré : on ne garde pas cette occurrence
            # supplémentaire.
            continue

        seen_normalized_forms.add(normalized)
        kept_paragraphs.append(stripped_paragraph)

    return "\n\n".join(kept_paragraphs).strip()


# ============================================================
# 6. CONSTRUCTION DES SOURCES
# ============================================================

def build_sources(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Construit la liste des sources utilisées.
    """

    sources = []

    seen = set()

    for result in results:

        document = result.get(
            "document"
        )

        page = result.get(
            "page"
        )

        theme = result.get(
            "chunk_theme"
        )

        key = (
            document,
            page,
            theme,
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        sources.append(
            {
                "document":
                    document,

                "page":
                    page,

                "theme":
                    theme,

                "intent":
                    result.get(
                        "chunk_intent"
                    ),

                "language":
                    result.get(
                        "language"
                    ),

                "score":
                    result.get(
                        "score"
                    ),

                "semantic_score":
                    result.get(
                        "semantic_score"
                    ),
            }
        )

    return sources


# ============================================================
# 7. SÉLECTION DES CHUNKS PAR INTENTION (FRANÇAIS UNIQUEMENT)
# ============================================================

# ============================================================
# 7 bis. DIVERSIFICATION DE LA SÉLECTION FINALE (Phase 3C-C.2)
# ============================================================
#
# Corrige un problème distinct du retrieval/de l'indexation (déjà
# corrigés en Phase 3C-C.2 précédente au niveau du chunking) : même
# lorsque le bon chunk "procédure" est correctement récupéré avec de
# bonnes métadonnées, un simple tri par score peut le faire éliminer
# par plusieurs fragments overlap issus d'UNE SEULE section
# thématique voisine (ex. 3 fragments "Cyberharcèlement" typologie
# monopolisant les 3 places du Top-K, alors qu'un chunk "procédure"
# plus utile est disponible).
#
# Générique : aucune intention codée en dur, fonctionne pour toutes
# les intentions et pour FR/AR. Ne modifie ni ensure_procedure_chunk_present()
# ni force_intent_results() (Phase 3C-A), qui restent inchangées.

STRUCTURING_METADATA_MARKERS = (
    "Thème :",
    "Thème:",
    "Theme :",
    "الموضوع :",
    "الموضوع:",
    "Intention CamemBERT :",
    "Intention CamemBERT:",
    "Type d'information :",
    "Métadonnées",
    "Metadonnées",
    "البيانات الوصفية",
)


# Plafond du pool de candidats demandé à force_intent_results() dans
# les appels qui doivent ensuite diversifier via select_diverse_results()
# (ex. indice lexical arabe). Correspond au candidate_k déjà utilisé
# en interne par force_intent_results() -- demander plus ne changerait
# rien, cette valeur ne fait qu'éviter de tronquer prématurément.
WIDE_SELECTION_POOL_SIZE = 50


def retrieve_for_classified_intent(
    question: str,
    language: str,
    predicted_intent: str,
    pool_size: int = WIDE_SELECTION_POOL_SIZE,
) -> list[dict[str, Any]]:
    """
    Récupère un pool documentaire correspondant à une intention déjà
    déterminée en amont par le classifieur.

    Chemin préféré :
        utilise `predicted_intent_override` si la version actuelle de
        rag.retriever.retrieve() le supporte. Cela permet au retriever
        d'injecter/reranker directement les chunks de la bonne intention.

    Compatibilité :
        si le retriever local est une version plus ancienne sans
        `predicted_intent_override`, on retombe sur force_intent_results()
        plutôt que de casser le pipeline.

    Dans les deux cas, on refiltre strictement par langue et
    chunk_intent avant la diversification finale.
    """

    retrieve_parameters = inspect.signature(
        retrieve
    ).parameters

    if "predicted_intent_override" in retrieve_parameters:

        candidates = retrieve(
            query=question,
            top_k=pool_size,
            minimum_score=0.0,
            use_intent=False,
            candidate_k=302,
            language=language,
            predicted_intent_override=predicted_intent,
        )

        candidates = filter_results_by_language(
            candidates,
            language,
        )

        candidates = [
            result
            for result in candidates
            if result.get("chunk_intent") == predicted_intent
        ]

        candidates.sort(
            key=lambda item: item.get("score", 0.0),
            reverse=True,
        )

        return candidates[:pool_size]

    # Compatibilité avec l'ancien retriever.
    return force_intent_results(
        question=question,
        language=language,
        intent=predicted_intent,
        top_k=pool_size,
    )


def _chunk_contains_structuring_metadata(
    text: str,
) -> bool:
    """
    Détecte, de façon structurelle et générique (jamais par intention
    codée en dur), si un chunk est le chunk "ancre" d'une section --
    celui qui porte les marqueurs de début de section (Thème,
    Intention CamemBERT, Type d'information, ou leurs équivalents
    arabes). Les fragments d'overlap issus de la même section, plus
    loin dans le texte, ne portent plus ces marqueurs.
    """

    if not text:
        return False

    return any(
        marker in text
        for marker in STRUCTURING_METADATA_MARKERS
    )


def _result_group_key(
    result: dict[str, Any],
) -> tuple[Any, Any, Any]:
    """
    Clé de regroupement d'un résultat par section logique -- des
    chunks partageant (document, chunk_theme, chunk_intent) sont
    considérés comme des fragments d'UNE MÊME information, pas comme
    des informations indépendantes.
    """

    return (
        result.get("document"),
        result.get("chunk_theme"),
        result.get("chunk_intent"),
    )


# Remontée ici depuis la section Phase 3C-A (ensure_procedure_chunk_present)
# pour être partagée par les deux mécanismes, sans dupliquer la liste.
PROCEDURE_THEME_MARKERS = ("procédure", "procedure")


# Remontée ici depuis la section Phase 3C-A (ensure_procedure_chunk_present)
# pour être partagée par les deux mécanismes. Étendue avec des
# marqueurs arabes ("الإجراء" / "إجراء" -- procédure/action) : le
# thème d'un chunk arabe est rédigé en arabe, jamais en français,
# donc les marqueurs français seuls ne suffisent pas à reconnaître
# une procédure arabe.
PROCEDURE_THEME_MARKERS = (
    "procédure",
    "procedure",
    "الإجراء",
    "إجراء",
)


def _theme_has_procedure_marker(
    theme: str | None,
) -> bool:

    if not theme:
        return False

    lowered = theme.lower()

    return any(
        marker in lowered
        for marker in PROCEDURE_THEME_MARKERS
    )


def _extract_information_type_from_text(
    text: str,
) -> str | None:
    """
    Extrait la valeur du champ "Type d'information :" (ou son
    équivalent arabe "نوع المعلومات :") directement depuis le texte
    brut du chunk -- ce champ n'est PAS propagé comme clé séparée par
    retriever.py, mais apparaît littéralement dans le texte indexé
    (comme "Thème :"/"Intention CamemBERT :"), donc extractible sans
    modifier retriever.py.
    """

    if not text:
        return None

    patterns = [
        r"Type d'information\s*:\s*([^\n\r]+)",
        r"نوع المعلومات\s*:\s*([^\n\r]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value:
                return value

    return None


def _result_is_procedure_type(
    result: dict[str, Any],
) -> bool:
    """
    Vrai si CE chunk précis est de type procédure -- via son thème
    (marqueur générique FR/AR) OU via le champ "Type d'information :"
    extrait de son propre texte. Les deux voies sont indépendantes,
    car un thème peut porter le marqueur sans que "Type d'information"
    soit présent dans ce fragment précis (overlap), et inversement.
    """

    if _theme_has_procedure_marker(result.get("chunk_theme")):
        return True

    information_type = _extract_information_type_from_text(
        result.get("text", "")
    )

    return _theme_has_procedure_marker(information_type)


def _theme_matches_intent_name(
    theme: str | None,
    predicted_intent: str,
) -> bool:
    """
    Vrai si `theme` correspond textuellement au nom canonique de
    l'intention prédite (toujours en français, ex. "Cyberharcèlement").
    Fonctionne pour le français, où les thèmes reprennent littéralement
    le nom de l'intention. Ne fonctionne PAS pour l'arabe, où le thème
    est rédigé en arabe -- voir le repli dans select_diverse_results()
    pour ce cas.
    """

    if not theme:
        return False

    return theme == predicted_intent or theme.startswith(predicted_intent)



def select_diverse_results(
    candidates: list[dict[str, Any]],
    predicted_intent: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """
    Sélectionne jusqu'à top_k résultats parmi `candidates` (déjà
    filtrés/triés par pertinence décroissante par l'appelant), en
    évitant qu'un seul groupe logique (document, chunk_theme,
    chunk_intent) -- typiquement plusieurs fragments issus du même
    passage documentaire via le chevauchement (overlap) du chunking
    -- n'occupe la totalité des places disponibles.

    IMPORTANT (Phase 3C-C.4) : ne considère QUE les groupes "core"
    pour predicted_intent. Un groupe dont chunk_intent correspond mais
    dont le thème est un sous-type/scénario voisin (ex. "Stalking"
    pour une intention "Cyberharcèlement") n'est JAMAIS inclus, même
    s'il reste des places disponibles jusqu'à top_k.

    Détection "core", en deux temps pour rester valable en FR ET en
    AR (le thème d'un chunk arabe est rédigé en arabe, jamais en
    français -- il ne peut donc jamais correspondre textuellement au
    nom français de predicted_intent) :

      1. Est toujours core :
         - tout groupe dont le thème correspond textuellement à
           predicted_intent (_theme_matches_intent_name) -- fonctionne
           en français ;
         - tout groupe reconnu comme procédure via un marqueur
           générique FR/AR, sur le thème OU sur le champ
           "Type d'information :"/"نوع المعلومات :" extrait du texte
           du chunk (_result_is_procedure_type) -- fonctionne dans les
           deux langues, puisque basé sur un marqueur structurel du
           corpus, pas sur une comparaison au nom français de
           l'intention.

      2. Repli générique : si AUCUN groupe n'a été retenu via la
         correspondance textuelle du thème (typiquement le cas de
         l'arabe, où cette comparaison échoue systématiquement), le
         groupe le mieux classé parmi ceux qui ne sont pas déjà
         reconnus comme procédure est ajouté comme groupe "définition"
         générique. Ce repli ne s'active JAMAIS quand au moins un
         groupe correspond déjà textuellement (cas français normal) --
         un sous-type à score élevé comme "Chantage financier" pour
         une intention "Sextorsion" reste donc exclu tant que le
         thème "Sextorsion" lui-même est présent parmi les candidats.

    Un seul représentant par groupe core est ensuite retenu (le chunk
    "ancre" du groupe si présent, sinon le meilleur score), puis les
    places restantes sont comblées UNIQUEMENT avec d'autres fragments
    des groupes core déjà identifiés -- jamais avec un nouveau groupe
    hors du noyau de l'intention.

    Ce mécanisme généralise -- sans le dupliquer ni le modifier -- le
    même principe déjà appliqué spécifiquement par
    ensure_procedure_chunk_present() (Phase 3C-A) pour Sextorsion lors
    de la résolution de clarification d'âge.
    """

    if not candidates:
        return []

    groups: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = {}
    group_order: list[tuple[Any, Any, Any]] = []

    for result in candidates:

        key = _result_group_key(result)

        if key not in groups:
            groups[key] = []
            group_order.append(key)

        groups[key].append(result)

    def group_is_procedure(key: tuple[Any, Any, Any]) -> bool:
        if _theme_has_procedure_marker(key[1]):
            return True
        return any(
            _result_is_procedure_type(r)
            for r in groups[key]
        )

    core_keys: set[tuple[Any, Any, Any]] = set()
    intent_name_matched_any = False

    for key in group_order:

        if group_is_procedure(key):
            core_keys.add(key)

        if _theme_matches_intent_name(key[1], predicted_intent):
            core_keys.add(key)
            intent_name_matched_any = True

    if not intent_name_matched_any:

        # Repli générique (typiquement l'arabe) : aucun thème ne
        # correspond textuellement à predicted_intent. On retient le
        # groupe le mieux classé parmi ceux qui ne sont pas déjà une
        # procédure, comme groupe "définition" générique.
        for key in group_order:

            if key not in core_keys:
                core_keys.add(key)
                break

    core_group_order = [
        key for key in group_order
        if key in core_keys
    ]

    def pick_representative(
        group_results: list[dict[str, Any]],
    ) -> dict[str, Any]:

        anchors = [
            r for r in group_results
            if _chunk_contains_structuring_metadata(
                r.get("text", "")
            )
        ]

        if anchors:
            anchors.sort(
                key=lambda item: item.get("score", 0.0),
                reverse=True,
            )
            return anchors[0]

        return max(
            group_results,
            key=lambda item: item.get("score", 0.0),
        )

    selected: list[dict[str, Any]] = []

    # Passe 1 : un représentant par groupe core.
    for key in core_group_order:

        if len(selected) >= top_k:
            break

        selected.append(
            pick_representative(groups[key])
        )

    # Passe 2 : compléter les places restantes UNIQUEMENT avec
    # d'autres fragments des groupes core déjà identifiés -- jamais
    # avec un groupe hors du noyau de l'intention.
    if len(selected) < top_k:

        already_selected_ids = {
            id(item) for item in selected
        }

        core_remaining = [
            r
            for key in core_group_order
            for r in groups[key]
            if id(r) not in already_selected_ids
        ]

        core_remaining.sort(
            key=lambda item: item.get("score", 0.0),
            reverse=True,
        )

        for result in core_remaining:

            if len(selected) >= top_k:
                break

            selected.append(result)

    selected.sort(
        key=lambda item: item.get("score", 0.0),
        reverse=True,
    )

    return selected[:top_k]


def select_intent_results(
    retrieved_results: list[dict[str, Any]],
    predicted_intent: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """
    Conserve uniquement les passages dont l'intention
    correspond exactement à l'intention prédite par CamemBERT.

    N'est utilisé QUE pour le français : CamemBERT n'étant pas
    fiable sur l'arabe (voir section 1 ter), l'arabe passe
    directement par la recherche sémantique sans ce filtrage.
    """

    matching_results = [
        result
        for result in retrieved_results
        if result.get(
            "chunk_intent"
        ) == predicted_intent
    ]

    matching_results.sort(
        key=lambda item: item.get(
            "score",
            0.0,
        ),
        reverse=True,
    )

    return select_diverse_results(
        matching_results,
        predicted_intent,
        top_k,
    )


# ============================================================
# 8. PIPELINE COMPLET DE GÉNÉRATION
# ============================================================

def _finalize_answer(
    question: str,
    language: str,
    intent: str,
    intent_confidence: float | None,
    results: list[dict[str, Any]],
    extra_fields: dict[str, Any] | None = None,
    age_clarification: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """
    Factorise la construction du contexte, l'appel au LLM, le
    post-traitement (filtrage des recommandations non sourcées,
    garde contre les contradictions connues) et la construction du
    dictionnaire de résultat final -- réutilisé par les chemins
    possibles du pipeline (flux normal, garde d'urgence, indice
    lexical arabe, résolution de clarification multi-tour) pour
    éviter de dupliquer cette logique.

    age_clarification est optionnel et rétrocompatible (voir
    build_user_prompt()) : les appels existants sans ce paramètre ne
    changent pas de comportement.
    """

    context = build_context(results)

    user_prompt = build_user_prompt(
        question=question,
        context=context,
        language=language,
        age_clarification=age_clarification,
        history=history,
    )

    answer = call_ollama(
        system_prompt=build_system_prompt(language),
        user_prompt=user_prompt,
    )

    answer = remove_repeated_paragraphs(answer)

    answer = enforce_resolved_age_resource(
        answer=answer,
        age=age_clarification,
    )

    answer = strip_unsupported_generic_advice(
        answer=answer,
        context=context,
    )

    answer = enforce_known_contradictions(
        answer=answer,
        language=language,
    )

    answer = remove_forbidden_referrals(
        answer=answer,
        language=language,
    )

    answer = enforce_address_publication_consistency(
        answer=answer,
        question=question,
        language=language,
    )

    answer = remove_internal_vocabulary(
        answer
    )

    answer = remove_unresolved_age_resources(
        answer=answer,
        question=question,
        history=history,
    )

    answer = ensure_blocking_question_answered(
        answer=answer,
        question=question,
        language=language,
    )

    answer = enforce_credential_reuse_guidance(
        answer=answer,
        question=question,
        language=language,
    )

    result = {
        "answer": answer,
        "predicted_intent": intent,
        "intent_confidence": intent_confidence,
        "sources": build_sources(results),
        "retrieved_chunks": len(results),
        "model": OLLAMA_MODEL,
        "language": language,
    }

    if extra_fields:
        result.update(extra_fields)

    return result


def classify_situation(
    question: str,
    top_k: int = TOP_K,
) -> dict[str, Any]:
    """
    Extraction pure de la partie "triage" de generate_answer(), SANS
    aucun appel à Ollama. Reproduit EXACTEMENT le meme ordre de
    priorite, les memes seuils et les memes regles que le pipeline
    /chat existant :

        garde d'urgence (mots-cles)
            -> arabe : AraBERT direct
                -> fallback lexical/vote uniquement si AraBERT indisponible
            -> francais : CamemBERT via le retriever
            -> clarification d'age si necessaire

    Retourne un dictionnaire interne (non expose tel quel a l'API) :

        {
            "outcome": (
                "ready_for_llm" | "clarification" |
                "no_retrieval_results" | "intent_not_found" |
                "no_matching_results" | "emergency_no_corpus"
            ),
            "language": str,
            "predicted_intent": str | None,
            "intent_confidence": float | None,
            "intent_source": str | None,
            "emergency_override": bool,
            "clarification_required": bool,
            "clarification_type": str | None,
            "missing_information": list[str],
            "retrieved_results": list[dict],  # reutilise par
                                                # generate_answer(),
                                                # jamais expose a
                                                # /assessment
            "extra_fields": dict[str, Any],   # a fusionner tel quel
                                                # dans _finalize_answer()
        }

    generate_answer() consomme ce dictionnaire pour soit appeler
    _finalize_answer() (seul point d'entree vers call_ollama() dans
    tout le pipeline), soit construire lui-meme le texte de repli
    localise correspondant aux issues sans LLM -- classify_situation()
    ne construit JAMAIS de texte de reponse conversationnelle.
    """

    if not question or not question.strip():

        raise ValueError(
            "La question ne peut pas être vide."
        )

    question = question.strip()

    language = detect_language(
        question
    )

    def _clarification_fields(clarification_type: str | None) -> dict[str, Any]:
        if clarification_type:
            return {
                "clarification_required": True,
                "clarification_type": clarification_type,
                "missing_information": [clarification_type],
            }

        return {
            "clarification_required": False,
            "clarification_type": None,
            "missing_information": [],
        }

    # ========================================================
    # PRIORITÉ 1 : GARDE D'URGENCE (DÉTERMINISTE)
    # ========================================================

    if contains_emergency_keyword(question):

        emergency_results = force_intent_results(
            question=question,
            language=language,
            intent=EMERGENCY_INTENT,
            top_k=top_k,
        )

        if emergency_results:

            return {
                "outcome": "ready_for_llm",
                "language": language,
                "predicted_intent": EMERGENCY_INTENT,
                "intent_confidence": None,
                "intent_source": "emergency_keyword",
                "emergency_override": True,
                **_clarification_fields(None),
                "retrieved_results": emergency_results,
                "extra_fields": {"emergency_override": True},
            }

        # Garde-fou ultime : aucune fiche "Situation d'urgence" trouvée
        # dans le corpus de cette langue -- ne devrait pas arriver,
        # mais un mot-clé d'urgence ne doit jamais rester sans réponse
        # dédiée, sans pour autant inventer de coordonnées.
        return {
            "outcome": "emergency_no_corpus",
            "language": language,
            "predicted_intent": EMERGENCY_INTENT,
            "intent_confidence": None,
            "intent_source": "emergency_keyword",
            "emergency_override": True,
            **_clarification_fields(None),
            "retrieved_results": [],
            "extra_fields": {"emergency_override": True},
        }

    # ========================================================
    # PRIORITÉ 2 (ARABE) : ARABERT DIRECT
    # ========================================================
    #
    # Le modèle final arabe est désormais un classifieur AraBERT
    # directement entraîné sur les 11 intentions canoniques.
    #
    # La garde d'urgence reste volontairement AVANT AraBERT.
    # Si AraBERT fonctionne, les anciens mots-clés arabes et le vote
    # majoritaire ne participent plus à la décision d'intention.
    # Ils restent uniquement comme fallback technique si le modèle
    # AraBERT devient indisponible au chargement / à l'inférence.

    if language == "ar":

        try:

            arabert_prediction = predict_intent(
                question,
                language="ar",
            )

            predicted_intent = arabert_prediction.get(
                "intent"
            )

            intent_confidence = float(
                arabert_prediction.get(
                    "confidence",
                    0.0,
                )
            )

            if not predicted_intent:

                raise RuntimeError(
                    "AraBERT n'a retourné aucune intention."
                )

        except Exception as exc:

            # Fallback de disponibilité uniquement.
            # On ne transforme pas une erreur AraBERT en erreur 500
            # si l'ancien mécanisme déterministe peut encore assurer
            # un service dégradé.
            print(
                "Attention : AraBERT indisponible ; "
                "fallback arabe historique activé :",
                exc,
            )

        else:

            if needs_age_clarification(
                question,
                predicted_intent,
            ):

                return {
                    "outcome": "clarification",
                    "language": language,
                    "predicted_intent": predicted_intent,
                    "intent_confidence": intent_confidence,
                    "intent_source": "arabert_direct",
                    "emergency_override": False,
                    **_clarification_fields("age_at_time_of_facts"),
                    "retrieved_results": [],
                    "extra_fields": {
                        "intent_source": "arabert_direct",
                    },
                }

            arabert_candidates = retrieve_for_classified_intent(
                question=question,
                language=language,
                predicted_intent=predicted_intent,
                pool_size=WIDE_SELECTION_POOL_SIZE,
            )

            if arabert_candidates:

                arabert_results = select_diverse_results(
                    arabert_candidates,
                    predicted_intent,
                    top_k,
                )

                if arabert_results:

                    return {
                        "outcome": "ready_for_llm",
                        "language": language,
                        "predicted_intent": predicted_intent,
                        "intent_confidence": intent_confidence,
                        "intent_source": "arabert_direct",
                        "emergency_override": False,
                        **_clarification_fields(None),
                        "retrieved_results": arabert_results,
                        "extra_fields": {
                            "intent_source": "arabert_direct",
                        },
                    }

            # AraBERT a bien classé le message, mais aucun passage
            # de cette intention n'a été retrouvé dans le corpus.
            # On ne remplace pas silencieusement son intention par
            # un vote sémantique d'une autre classe.
            return {
                "outcome": "no_matching_results",
                "language": language,
                "predicted_intent": predicted_intent,
                "intent_confidence": intent_confidence,
                "intent_source": "arabert_direct",
                "emergency_override": False,
                **_clarification_fields(None),
                "retrieved_results": [],
                "extra_fields": {
                    "intent_source": "arabert_direct",
                },
            }

    # ========================================================
    # FALLBACK ARABE : ANCIEN INDICE LEXICAL
    # ========================================================
    #
    # Cette branche n'est atteinte pour l'arabe que si AraBERT a
    # levé une exception ci-dessus. Elle est conservée comme solution
    # de secours technique et non comme classifieur principal.

    #
    # Vérifié avant le retrieval sémantique large. S'il matche, on
    # court-circuite le vote majoritaire (moins fiable, voir tests)
    # et on va chercher directement les chunks de cette intention.

    if language == "ar":

        keyword_hint = detect_arabic_intent_keyword(question)

        if keyword_hint:

            if needs_age_clarification(question, keyword_hint):

                return {
                    "outcome": "clarification",
                    "language": language,
                    "predicted_intent": keyword_hint,
                    "intent_confidence": None,
                    "intent_source": "arabic_keyword_hint",
                    "emergency_override": False,
                    **_clarification_fields("age_at_time_of_facts"),
                    "retrieved_results": [],
                    "extra_fields": {},
                }

            # force_intent_results() plafonne déjà en interne à
            # candidate_k=50 -- demander ce même plafond ici ne coûte
            # rien de plus, et permet de récupérer le pool COMPLET de
            # candidats correspondant à l'intention (avant toute
            # troncature), pour que select_diverse_results() puisse
            # réellement diversifier au lieu de choisir parmi 3
            # fragments déjà tronqués par pur score.
            hinted_candidates = force_intent_results(
                question=question,
                language=language,
                intent=keyword_hint,
                top_k=WIDE_SELECTION_POOL_SIZE,
            )

            if hinted_candidates:

                hinted_results = select_diverse_results(
                    hinted_candidates,
                    keyword_hint,
                    top_k,
                )

                return {
                    "outcome": "ready_for_llm",
                    "language": language,
                    "predicted_intent": keyword_hint,
                    "intent_confidence": None,
                    "intent_source": "arabic_keyword_hint",
                    "emergency_override": False,
                    **_clarification_fields(None),
                    "retrieved_results": hinted_results,
                    "extra_fields": {"intent_source": "arabic_keyword_hint"},
                }

            # Si l'indice lexical ne trouve aucun chunk correspondant
            # (corpus incomplet sur cette intention précise), on
            # retombe sur le flux normal ci-dessous plutôt que
            # d'échouer.

    # ========================================================
    # FLUX NORMAL / FALLBACK : RETRIEVAL LARGE, FILTRÉ PAR LANGUE
    # ========================================================
    #
    # Français : chemin normal CamemBERT (use_intent=True).
    # Arabe : cette partie n'est atteinte qu'en mode dégradé, si
    # AraBERT était indisponible ET si l'ancien indice lexical n'a
    # rien détecté. Le vote majoritaire est donc désormais un dernier
    # fallback de disponibilité, jamais le classifieur arabe principal.
    #
    # Dans les deux cas, `language=language` restreint la recherche
    # au corpus de la langue détectée.

    retrieved_results = retrieve(
        query=question,
        top_k=RETRIEVAL_K,
        minimum_score=0.05,
        use_intent=(language == "fr"),
        candidate_k=50,
        language=language,
    )

    retrieved_results = filter_results_by_language(
        retrieved_results,
        language,
    )

    if not retrieved_results:

        return {
            "outcome": "no_retrieval_results",
            "language": language,
            "predicted_intent": None,
            "intent_confidence": None,
            "intent_source": None,
            "emergency_override": False,
            **_clarification_fields(None),
            "retrieved_results": [],
            "extra_fields": {},
        }

    if language == "fr":

        predicted_intent = retrieved_results[0].get("predicted_intent")
        intent_confidence = retrieved_results[0].get("intent_confidence")
        intent_source = "camembert"

    else:

        predicted_intent = derive_majority_intent(retrieved_results)
        intent_confidence = None
        intent_source = "arabic_majority_vote"

    if not predicted_intent:

        return {
            "outcome": "intent_not_found",
            "language": language,
            "predicted_intent": None,
            "intent_confidence": intent_confidence,
            "intent_source": None,
            "emergency_override": False,
            **_clarification_fields(None),
            "retrieved_results": [],
            "extra_fields": {},
        }

    if needs_age_clarification(question, predicted_intent):

        return {
            "outcome": "clarification",
            "language": language,
            "predicted_intent": predicted_intent,
            "intent_confidence": intent_confidence,
            "intent_source": intent_source,
            "emergency_override": False,
            **_clarification_fields("age_at_time_of_facts"),
            "retrieved_results": [],
            "extra_fields": {},
        }

    if language == "fr":

        results = select_intent_results(
            retrieved_results=retrieved_results,
            predicted_intent=predicted_intent,
            top_k=top_k,
        )

    else:

        results = select_diverse_results(
            retrieved_results,
            predicted_intent,
            top_k,
        )

    if not results:

        return {
            "outcome": "no_matching_results",
            "language": language,
            "predicted_intent": predicted_intent,
            "intent_confidence": intent_confidence,
            "intent_source": intent_source,
            "emergency_override": False,
            **_clarification_fields(None),
            "retrieved_results": [],
            "extra_fields": {},
        }

    return {
        "outcome": "ready_for_llm",
        "language": language,
        "predicted_intent": predicted_intent,
        "intent_confidence": intent_confidence,
        "intent_source": intent_source,
        "emergency_override": False,
        **_clarification_fields(None),
        "retrieved_results": results,
        "extra_fields": {},
    }


# ============================================================
# 8 bis. RÉSOLUTION D'UNE CLARIFICATION MULTI-TOUR (PHASE 3C-A)
# ============================================================
#
# Traite la réponse de l'utilisateur à une clarification d'âge déjà
# posée au tour précédent (Sextorsion / Diffusion non consentie
# d'images). Ne passe JAMAIS par classify_situation() : l'intention
# reste celle transmise par l'appelant (pending_intent), jamais
# redérivée à partir du message court ("J'étais majeur(e)."). Le
# backend reste stateless -- c'est l'appelant (l'endpoint /chat) qui
# fournit le contexte minimal reçu du frontend à chaque appel.

# ============================================================
# 8 ter. COMPLÉMENT DÉTERMINISTE : CHUNK PROCÉDURE MANQUANT
# ============================================================
#
# DIAGNOSTIC (Phase 3C-A) :
# force_intent_results() récupère jusqu'à candidate_k=302 candidats
# via retrieve(), mais TRONQUE immédiatement à top_k=50 (paramètre
# `top_k` de l'appel interne à retrieve(), distinct du top_k final
# de force_intent_results()) AVANT de filtrer par chunk_intent. Pour
# "Sextorsion" en français avec certains messages, la fiche
# "Sextorsion -- définition" domine le classement sémantique brut
# (toutes intentions confondues) et occupe une position haute, tandis
# que la fiche "Sextorsion -- procédure" (qui documente les branches
# Take It Down / StopNCII selon l'âge) est lexicalement plus éloignée
# du récit initial et peut ne pas survivre à cette troncature de 50 --
# alors qu'elle est bien présente dans l'index une fois qu'on
# supprime la troncature prématurée.
#
# Cette fonction ne s'applique QUE lorsqu'un appelant (actuellement :
# resolve_pending_clarification(), et seulement pour Sextorsion FR --
# voir le point d'appel plus bas) constate que le chunk procédure de
# l'intention concernée est absent des résultats déjà obtenus. Elle
# ne touche JAMAIS force_intent_results() elle-même, ne s'applique
# JAMAIS à une autre intention que celle demandée, et ne fait AUCUNE
# hypothèse sur le contenu textuel des chunks (seules les métadonnées
# chunk_intent / chunk_theme, déjà utilisées ailleurs dans ce fichier,
# sont utilisées).
#
# PROCEDURE_THEME_MARKERS est désormais définie plus haut dans ce
# fichier (section 7 bis), partagée avec select_diverse_results().


def _is_procedure_chunk_for_intent(
    result: dict[str, Any],
    intent: str,
) -> bool:
    """
    Vrai si `result` appartient à `intent` ET que son thème documente
    une procédure (metadonnée chunk_theme, jamais le texte brut).
    """

    if result.get("chunk_intent") != intent:
        return False

    theme = str(result.get("chunk_theme") or "").lower()

    return any(
        marker in theme
        for marker in PROCEDURE_THEME_MARKERS
    )


def _chunk_identity(result: dict[str, Any]) -> tuple:
    """
    Identité stable d'un chunk pour la déduplication, sans supposer
    de noms de champs spécifiques (document/page/chunk_index) qui
    n'ont pas été confirmés avec certitude sur le schéma réel : on
    compare l'ensemble des métadonnées du chunk, à l'exception du
    score (qui peut légèrement varier selon la requête d'origine pour
    un même chunk).
    """

    return tuple(
        (key, value)
        for key, value in sorted(result.items())
        if key != "score"
    )


def ensure_procedure_chunk_present(
    results: list[dict[str, Any]],
    original_message: str,
    language: str,
    intent: str,
) -> list[dict[str, Any]]:
    """
    Si `results` contient déjà un chunk procédure pour `intent`, ne
    change rien. Sinon, effectue un second appel à retrieve() SANS la
    troncature prématurée de force_intent_results() (top_k porté à la
    taille du pool de candidats plutôt qu'à 50), filtre strictement
    par chunk_intent == intent ET thème-procédure (jamais une autre
    intention), prend le meilleur candidat par score, et l'AJOUTE à
    `results` (rien n'est retiré) après déduplication.

    N'appelle jamais Ollama, ne modifie jamais force_intent_results(),
    ne cherche jamais en dehors de `intent`.
    """

    if any(
        _is_procedure_chunk_for_intent(result, intent)
        for result in results
    ):
        return results

    # Même valeur que candidate_k dans force_intent_results() : aucune
    # constante nommée n'existe actuellement pour cette valeur dans le
    # fichier ; en introduire une toucherait force_intent_results(),
    # hors périmètre de cette correction locale (accord explicite du
    # 15/08). Conservée ici telle quelle, avec ce commentaire pour
    # éviter toute dérive silencieuse si l'une des deux valeurs change
    # sans que l'autre soit mise à jour en miroir.
    wide_pool_size = 302

    wide_results = retrieve(
        query=original_message,
        top_k=wide_pool_size,
        minimum_score=0.0,
        use_intent=False,
        candidate_k=wide_pool_size,
        language=language,
    )

    wide_results = filter_results_by_language(
        wide_results,
        language,
    )

    procedure_candidates = [
        result
        for result in wide_results
        if _is_procedure_chunk_for_intent(result, intent)
    ]

    if not procedure_candidates:
        # Même sans troncature prématurée, aucun chunk procédure
        # documenté pour cette intention : rien à ajouter, on ne
        # modifie pas `results`.
        return results

    procedure_candidates.sort(
        key=lambda item: item.get("score", 0.0),
        reverse=True,
    )

    best_procedure_chunk = procedure_candidates[0]

    existing_identities = {
        _chunk_identity(result)
        for result in results
    }

    if _chunk_identity(best_procedure_chunk) in existing_identities:
        return results

    return results + [best_procedure_chunk]


def resolve_pending_clarification(
    message: str,
    pending_intent: str,
    pending_clarification: str,
    original_message: str,
    original_language: str,
    top_k: int = TOP_K,
) -> dict[str, Any]:
    """
    Pipeline :

    message (réponse courte de l'utilisateur, ex: "J'étais majeur(e).")
        -> resolve_age_from_text(message)
        -> None (ambigu) : aucune reclassification, aucun retrieval,
           aucun appel Ollama -- la même question de clarification est
           reposée, dans la langue d'origine de la conversation.
        -> "minor" / "adult" résolu : intent = pending_intent (FIXE),
           force_intent_results(original_message, original_language,
           pending_intent) récupère le contexte documentaire de cette
           intention (même fonction déjà utilisée par la garde
           d'urgence et l'indice lexical arabe -- aucune duplication),
           puis _finalize_answer() avec age_clarification=age injecte
           une note canonique dans le prompt LLM (jamais la réponse
           brute de l'utilisateur).
    """

    if not message or not message.strip():

        raise ValueError(
            "La réponse à la clarification ne peut pas être vide."
        )

    message = message.strip()

    age = resolve_age_from_text(message)

    if age is None:

        # Réponse ambiguë : ne reclassifie jamais, ne relance ni
        # retrieval ni Ollama. Reconduit la même clarification.
        return {
            "answer": build_age_clarification_answer(
                predicted_intent=pending_intent,
                language=original_language,
            ),
            "predicted_intent": pending_intent,
            "intent_confidence": None,
            "sources": [],
            "retrieved_chunks": 0,
            "model": None,
            "clarification_required": pending_clarification,
            "language": original_language,
        }

    results = force_intent_results(
        question=original_message,
        language=original_language,
        intent=pending_intent,
        top_k=top_k,
    )

    # Correction locale (Phase 3C-A, diagnostic du 15/08) : uniquement
    # pour Sextorsion en français, où le diagnostic a confirmé que le
    # chunk "Sextorsion -- procédure" peut être absent de `results` à
    # cause de la troncature prématurée de force_intent_results()
    # (voir ensure_procedure_chunk_present()). Ne s'applique à AUCUNE
    # autre combinaison intention/langue : Sextorsion AR, Diffusion
    # FR/AR récupèrent déjà leur chunk procédure sans cette correction
    # (confirmé par le diagnostic), leur comportement reste inchangé.
    if pending_intent == "Sextorsion" and original_language == "fr":

        results = ensure_procedure_chunk_present(
            results=results,
            original_message=original_message,
            language=original_language,
            intent=pending_intent,
        )

    if not results:

        # Filet de sécurité, symétrique à celui déjà présent dans
        # classify_situation() pour "no_matching_results" -- ne devrait
        # normalement pas se produire puisque le premier tour a déjà
        # confirmé l'existence de résultats pour cette intention.
        return {
            "answer": localized_message(
                language=original_language,
                french=(
                    "Je n'ai pas trouvé suffisamment "
                    "d'informations documentaires correspondant "
                    "précisément à votre situation. "
                    "Pouvez-vous préciser ou reformuler "
                    "votre demande ?"
                ),
                arabic=(
                    "لم أجد معلومات وثائقية كافية تطابق "
                    "حالتكم بدقة. هل يمكنكم توضيح طلبكم "
                    "أو إعادة صياغته؟"
                ),
            ),
            "predicted_intent": pending_intent,
            "intent_confidence": None,
            "sources": [],
            "retrieved_chunks": 0,
            "model": None,
            "language": original_language,
        }

    return _finalize_answer(
        question=original_message,
        language=original_language,
        intent=pending_intent,
        intent_confidence=None,
        results=results,
        age_clarification=age,
    )


def generate_answer(
    question: str,
    top_k: int = TOP_K,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """
    Pipeline :

    question
        -> classify_situation() : détection de la langue, garde
           d'urgence, AraBERT direct en arabe (fallback historique si indisponible), retrieval + intention,
           clarification d'âge -- AUCUN appel LLM à ce stade.
        -> si classify_situation() a determine qu'un contexte
           documentaire exploitable est disponible ("ready_for_llm") :
           _finalize_answer() construit le contexte, appelle
           Llama 3.1 et applique les post-traitements existants.
        -> sinon : construction du texte de repli localisé
           correspondant (aucun appel LLM), avec exactement les
           memes messages que la version precedente de cette
           fonction.

    Ce decoupage ne change AUCUNE regle, seuil ou priorite : c'est
    une extraction pure de la logique deja existante dans
    classify_situation(), reutilisable telle quelle par /assessment
    sans jamais declencher call_ollama().
    """

    if not question or not question.strip():

        raise ValueError(
            "La question ne peut pas être vide."
        )

    question = question.strip()

    classification = classify_situation(
        question,
        top_k=top_k,
    )

    language = classification["language"]
    outcome = classification["outcome"]

    if outcome == "ready_for_llm":

        return _finalize_answer(
            question=question,
            language=language,
            intent=classification["predicted_intent"],
            intent_confidence=classification["intent_confidence"],
            results=classification["retrieved_results"],
            extra_fields=classification["extra_fields"] or None,
            history=history,
        )

    if outcome == "emergency_no_corpus":

        return {
            "answer": localized_message(
                language=language,
                french=(
                    "Ce que vous décrivez peut être très important. "
                    "Il est essentiel de parler à un humain dès "
                    "maintenant. Les coordonnées d'urgence documentées "
                    "sont disponibles dans les ressources du projet."
                ),
                arabic=(
                    "ما تصفونه قد يكون مهماً جداً. من الضروري التحدث "
                    "إلى إنسان الآن. إحداثيات الطوارئ الموثقة متوفرة "
                    "ضمن موارد المشروع."
                ),
            ),
            "predicted_intent": EMERGENCY_INTENT,
            "intent_confidence": None,
            "sources": [],
            "retrieved_chunks": 0,
            "model": None,
            "language": language,
            "emergency_override": True,
        }

    if outcome == "clarification":

        return {
            "answer": build_age_clarification_answer(
                predicted_intent=classification["predicted_intent"],
                language=language,
            ),
            "predicted_intent": classification["predicted_intent"],
            "intent_confidence": classification["intent_confidence"],
            "sources": [],
            "retrieved_chunks": 0,
            "model": None,
            "clarification_required": classification["clarification_type"],
            "language": language,
        }

    if outcome == "no_retrieval_results":

        return {
            "answer": localized_message(
                language=language,
                french=(
                    "Je ne dispose pas de suffisamment "
                    "d'informations documentaires pour "
                    "répondre de manière fiable à cette question."
                ),
                arabic=(
                    "لا أتوفر على معلومات وثائقية كافية "
                    "للإجابة عن هذا السؤال بشكل موثوق."
                ),
            ),
            "predicted_intent": None,
            "intent_confidence": None,
            "sources": [],
            "retrieved_chunks": 0,
            "model": None,
            "language": language,
        }

    if outcome == "intent_not_found":

        return {
            "answer": localized_message(
                language=language,
                french=(
                    "Je n'ai pas pu identifier suffisamment "
                    "votre situation. Pouvez-vous reformuler "
                    "votre demande ?"
                ),
                arabic=(
                    "لم أتمكن من تحديد حالتكم بشكل كافٍ. "
                    "هل يمكنكم إعادة صياغة طلبكم؟"
                ),
            ),
            "predicted_intent": None,
            "intent_confidence": classification["intent_confidence"],
            "sources": [],
            "retrieved_chunks": 0,
            "model": None,
            "language": language,
        }

    if outcome == "no_matching_results":

        return {
            "answer": localized_message(
                language=language,
                french=(
                    "Je n'ai pas trouvé suffisamment "
                    "d'informations documentaires correspondant "
                    "précisément à votre situation. "
                    "Pouvez-vous préciser ou reformuler "
                    "votre demande ?"
                ),
                arabic=(
                    "لم أجد معلومات وثائقية كافية تطابق "
                    "حالتكم بدقة. هل يمكنكم توضيح طلبكم "
                    "أو إعادة صياغته؟"
                ),
            ),
            "predicted_intent": classification["predicted_intent"],
            "intent_confidence": classification["intent_confidence"],
            "sources": [],
            "retrieved_chunks": 0,
            "model": None,
            "language": language,
        }

    # Filet de sécurité : ne devrait jamais se produire si
    # classify_situation() ne retourne que les issues listées
    # ci-dessus. Évite un retour silencieux de None en cas d'ajout
    # futur d'une issue non gérée ici.
    raise RuntimeError(
        f"Issue de classification inattendue : {outcome!r}"
    )


# ============================================================
# 8 quater. PLAN D'ACTION DOCUMENTÉ (PHASE 5)
# ============================================================
#
# Objectif :
# produire une liste structurée d'actions à partir UNIQUEMENT des
# passages RAG déjà sélectionnés pour la situation.
#
# Sécurité :
# - aucune action codée en dur par intention ;
# - aucune action provenant des connaissances générales du LLM ;
# - chaque action doit citer un PASSAGE précis ;
# - chaque action doit fournir un court extrait de preuve COPIÉ
#   depuis ce passage ;
# - le backend vérifie déterministement que cet extrait existe
#   réellement dans le passage source ;
# - une action dont la preuve n'est pas vérifiable est supprimée.
#
# Pour les intentions dépendantes de l'âge, la même règle validée
# que dans /chat est appliquée :
#   minor -> Take It Down
#   adult -> StopNCII


def _normalize_text_for_evidence(
    text: str,
) -> str:
    """
    Normalisation légère utilisée uniquement pour vérifier qu'un
    extrait de preuve retourné par le LLM existe réellement dans le
    passage documentaire annoncé.
    """

    normalized = clean_context_text(
        text or ""
    )

    normalized = _normalize_arabic(
        normalized
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip().lower()


def _parse_action_plan_json(
    raw_text: str,
) -> dict[str, Any]:
    """
    Extrait un objet JSON d'une réponse LLM.

    Tolère uniquement l'enveloppe markdown ```json ... ``` ou un
    court texte parasite autour de l'objet. La structure métier est
    validée séparément ensuite.
    """

    if not raw_text or not raw_text.strip():
        raise RuntimeError(
            "Le modèle n'a retourné aucun plan d'action."
        )

    cleaned = raw_text.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise RuntimeError(
            "Le plan d'action retourné n'est pas un JSON exploitable."
        )

    try:
        data = json.loads(
            cleaned[start:end + 1]
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Le plan d'action retourné contient un JSON invalide."
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError(
            "Le plan d'action doit être un objet JSON."
        )

    return data


def build_action_plan_prompt(
    question: str,
    context: str,
    language: str,
    age_status: str | None = None,
) -> str:
    """
    Prompt spécialisé pour extraire des actions documentées sous une
    forme JSON stricte.
    """

    if language == "ar":
        language_rule = (
            "اكتب title وdescription باللغة العربية فقط. "
            "يمكن إبقاء أسماء الموارد الرسمية المسموح بها مثل StopNCII أو "
            "Take It Down بصيغتها الأصلية. لا تذكر evigilance.ma مطلقاً."
        )
    else:
        language_rule = (
            "Écris title et description uniquement en français. "
            "Les noms officiels des ressources autorisées peuvent conserver "
            "leur graphie originale. Ne mentionne jamais evigilance.ma."
        )

    age_block = ""

    if age_status is not None:

        age_note = build_resolved_age_note(
            age=age_status,
            language=language,
        )

        age_rule = build_age_branch_instruction(
            age=age_status,
            language=language,
        )

        age_block = (
            f"\n{age_note}\n"
            f"{age_rule}\n"
        )

    return f"""
SITUATION DE L'UTILISATEUR :
{question}
{age_block}
PASSAGES DOCUMENTAIRES AUTORISÉS :
{context}

TÂCHE :
Construis un plan d'action court et concret à partir UNIQUEMENT
des PASSAGES DOCUMENTAIRES ci-dessus.

RÈGLES ABSOLUES :
1. N'invente aucune action.
2. N'utilise aucune connaissance générale.
3. Ne transforme pas une définition en action si le passage ne
   contient pas réellement une recommandation, une procédure,
   une orientation ou une mesure concrète.
4. Ne donne que les actions directement pertinentes pour la
   situation décrite.
5. Le plan est destiné à la VICTIME. Chaque title et description
   doit donc être formulé comme une action que l'utilisateur peut
   lui-même effectuer.
6. Si un passage est rédigé pour un professionnel ou un
   accompagnateur ("proposer", "orienter la victime",
   "caractériser le problème avec l'utilisateur", etc.), ne
   reproduis PAS cette formulation dans title/description.
   - Si le passage décrit malgré tout une ressource ou une démarche
     accessible à la victime, reformule-la du point de vue de la
     victime, sans ajouter d'information.
   - Sinon, omets cette étape.
7. N'écris jamais dans title/description une instruction destinée
   à l'équipe EMC, à un conseiller ou à un accompagnateur.
8. Évite les doublons.
9. Maximum 6 actions.
10. Chaque action doit être reliée à UN seul PASSAGE source.
11. Pour chaque action, "evidence" doit être un COURT extrait
    COPIÉ textuellement depuis le contenu du PASSAGE indiqué.
12. "source_rank" est le numéro du PASSAGE : 1, 2, 3, etc.
13. Si aucune action explicite n'est documentée, retourne une
    liste "actions" vide.
14. Ne crée aucune loi, sanction, institution, coordonnée,
    ressource ou procédure absente des passages.
15. Respecte strictement toute condition d'âge déjà fournie.
16. N'affiche jamais les deux ressources d'âge lorsqu'une tranche
    d'âge a été déterminée.
17. {language_rule}

FORMAT DE SORTIE :
Retourne UNIQUEMENT un JSON valide, sans markdown, exactement sous
cette forme :

{{
  "actions": [
    {{
      "title": "titre bref",
      "description": "action concrète et fidèle au passage",
      "source_rank": 1,
      "evidence": "court extrait exact du passage"
    }}
  ]
}}

Aucun autre champ. Aucun texte avant ou après le JSON.
""".strip()


def _action_plan_empty_result(
    *,
    outcome: str,
    language: str,
    predicted_intent: str | None,
    clarification_required: bool = False,
    clarification_type: str | None = None,
    emergency_override: bool = False,
) -> dict[str, Any]:
    """
    Format commun pour les sorties /action-plan sans action.
    """

    return {
        "outcome": outcome,
        "language": language,
        "predicted_intent": predicted_intent,
        "clarification_required": clarification_required,
        "clarification_type": clarification_type,
        "emergency_override": emergency_override,
        "actions": [],
        "sources": [],
    }



def _is_agent_facing_action(
    title: str,
    description: str,
    language: str,
) -> bool:
    """
    Filtre déterministe de dernier recours.

    Il ne regarde PAS l'evidence, car celle-ci doit rester un extrait
    exact du corpus et peut naturellement être formulée pour un agent.
    Seuls title + description, visibles par la victime, sont contrôlés.
    """

    visible_text = _normalize_text_for_evidence(
        f"{title} {description}"
    )

    if language == "ar":
        blocked_phrases = (
            "توصيف المشكلة مع المستخدم",
            "تحديد المشكلة مع المستخدم",
            "توجيه الضحية",
            "إحالة الضحية",
            "اقتراح مرافقة",
            "اقتراح دعم",
            "مرافقة الضحية",
        )
    else:
        blocked_phrases = (
            "proposer un accompagnement",
            "proposer une orientation",
            "orienter la victime",
            "orienter l'utilisateur",
            "caractériser le problème avec l'utilisateur",
            "caracteriser le probleme avec l'utilisateur",
            "qualifier le problème avec l'utilisateur",
            "qualifier le probleme avec l'utilisateur",
            "accompagner la victime",
        )

    return any(
        phrase in visible_text
        for phrase in blocked_phrases
    )




def _extract_sentence_with_resource(
    text: str,
    resource_name: str,
) -> str | None:
    """
    Retourne un court extrait exact du chunk contenant la ressource.

    On privilégie une ligne ou une phrase complète afin que l'evidence
    reste vérifiable textuellement dans le passage source.
    """

    if not text or not resource_name:
        return None

    # D'abord par lignes : souvent les procédures du corpus sont structurées.
    for raw_line in text.splitlines():
        line = raw_line.strip()

        if (
            resource_name.lower()
            in line.lower()
        ):
            return line

    # Sinon par phrases simples.
    pieces = re.split(
        r"(?<=[.!؟])\s+",
        text,
    )

    for piece in pieces:
        sentence = piece.strip()

        if (
            resource_name.lower()
            in sentence.lower()
        ):
            return sentence

    return None


def _ensure_age_resource_action(
    actions: list[dict[str, Any]],
    results: list[dict[str, Any]],
    age_status: str | None,
    language: str,
) -> list[dict[str, Any]]:
    """
    Garantie déterministe de la branche d'âge.

    Si une tranche d'âge est connue et que la ressource correspondante
    existe réellement dans les passages RAG, elle doit apparaître dans
    le plan visible, même si le LLM a omis cette action.

    Aucune ressource n'est inventée :
    l'action n'est ajoutée que si un extrait exact contenant le nom de
    la ressource est trouvé dans un chunk récupéré.
    """

    if age_status not in AGE_RESOURCE_BY_STATUS:
        return actions

    allowed_resource = (
        AGE_RESOURCE_BY_STATUS[
            age_status
        ]["allowed"]
    )

    # Si déjà présente, rien à faire.
    combined_existing = " ".join(
        (
            action.get("title", "")
            + " "
            + action.get("description", "")
            + " "
            + action.get("evidence", "")
        )
        for action in actions
    ).lower()

    if allowed_resource.lower() in combined_existing:
        return actions

    matching_result = None
    evidence = None

    for result in results:

        candidate_text = result.get(
            "text",
            "",
        )

        if (
            allowed_resource.lower()
            not in candidate_text.lower()
        ):
            continue

        candidate_evidence = _extract_sentence_with_resource(
            candidate_text,
            allowed_resource,
        )

        if not candidate_evidence:
            continue

        matching_result = result
        evidence = candidate_evidence
        break

    # La ressource n'est pas présente dans les passages récupérés :
    # on n'invente rien.
    if (
        matching_result is None
        or evidence is None
    ):
        return actions

    source_list = build_sources(
        [matching_result]
    )

    source = (
        source_list[0]
        if source_list
        else None
    )

    if language == "ar":

        if allowed_resource == "Take It Down":
            title = "استخدام Take It Down"
            description = (
                "استخدم Take It Down باعتبارها المورد المناسب "
                "للحالة المرتبطة بقاصر."
            )
        else:
            title = "استخدام StopNCII"
            description = (
                "استخدم StopNCII باعتبارها المورد المناسب "
                "للحالة المرتبطة بشخص بالغ."
            )

    else:

        if allowed_resource == "Take It Down":
            title = "Utiliser Take It Down"
            description = (
                "Utiliser Take It Down, la ressource prévue dans "
                "la procédure documentée pour une victime mineure."
            )
        else:
            title = "Utiliser StopNCII"
            description = (
                "Utiliser StopNCII, la ressource prévue dans "
                "la procédure documentée pour une victime adulte."
            )

    actions = list(actions)

    actions.append(
        {
            "id":
                f"action_{len(actions) + 1}",

            "title":
                title,

            "description":
                description,

            "evidence":
                evidence,

            "source":
                source,
        }
    )

    return actions



def build_action_plan(
    question: str,
    age_status: str | None = None,
    top_k: int = TOP_K,
) -> dict[str, Any]:
    """
    Construit un plan d'action structuré et sourcé.

    `age_status` est optionnel :
        None
        "minor"
        "adult"

    Cas d'usage :
    - situation normale : classification -> RAG -> extraction actions ;
    - intention dépendante de l'âge sans âge : retourne
      clarification_required=True, SANS Ollama ;
    - âge déjà connu côté frontend : permet de construire directement
      le plan correspondant à la bonne branche documentaire.
    """

    if not question or not question.strip():
        raise ValueError(
            "La description ne peut pas être vide."
        )

    question = question.strip()

    if age_status not in (None, "minor", "adult"):
        raise ValueError(
            "age_status doit être null, 'minor' ou 'adult'."
        )

    classification = classify_situation(
        question,
        top_k=top_k,
    )

    language = classification["language"]
    predicted_intent = classification.get(
        "predicted_intent"
    )
    outcome = classification["outcome"]

    # --------------------------------------------------------
    # Clarification d'âge
    # --------------------------------------------------------

    if outcome == "clarification":

        if age_status is None:

            return _action_plan_empty_result(
                outcome="clarification",
                language=language,
                predicted_intent=predicted_intent,
                clarification_required=True,
                clarification_type=classification.get(
                    "clarification_type"
                ),
                emergency_override=False,
            )

        # L'âge a été fourni explicitement par le frontend.
        # L'intention du premier passage reste fixe : on ne
        # reclassifie pas une réponse courte d'âge.
        candidates = retrieve_for_classified_intent(
            question=question,
            language=language,
            predicted_intent=predicted_intent,
            pool_size=WIDE_SELECTION_POOL_SIZE,
        )

        if not candidates:

            return _action_plan_empty_result(
                outcome="no_matching_results",
                language=language,
                predicted_intent=predicted_intent,
            )

        results = select_diverse_results(
            candidates,
            predicted_intent,
            top_k,
        )

        # Pour les intentions dépendantes de l'âge, la procédure est
        # indispensable au plan si elle existe dans le corpus.
        if predicted_intent in AGE_DEPENDENT_INTENTS:

            results = ensure_procedure_chunk_present(
                results=results,
                original_message=question,
                language=language,
                intent=predicted_intent,
            )

    elif outcome == "ready_for_llm":

        results = classification[
            "retrieved_results"
        ]

        # Si l'âge est déjà exprimé dans la description, on le
        # récupère pour appliquer les mêmes protections qu'en chat.
        if (
            age_status is None
            and predicted_intent in AGE_DEPENDENT_INTENTS
        ):
            age_status = resolve_age_from_text(
                question
            )

        if (
            predicted_intent in AGE_DEPENDENT_INTENTS
            and age_status is not None
        ):
            results = ensure_procedure_chunk_present(
                results=results,
                original_message=question,
                language=language,
                intent=predicted_intent,
            )

    else:

        return _action_plan_empty_result(
            outcome=outcome,
            language=language,
            predicted_intent=predicted_intent,
            clarification_required=classification.get(
                "clarification_required",
                False,
            ),
            clarification_type=classification.get(
                "clarification_type"
            ),
            emergency_override=classification.get(
                "emergency_override",
                False,
            ),
        )

    if not results:

        return _action_plan_empty_result(
            outcome="no_matching_results",
            language=language,
            predicted_intent=predicted_intent,
            emergency_override=classification.get(
                "emergency_override",
                False,
            ),
        )

    context = build_context(
        results
    )

    raw_plan = call_ollama(
        system_prompt=build_system_prompt(
            language
        ),
        user_prompt=build_action_plan_prompt(
            question=question,
            context=context,
            language=language,
            age_status=age_status,
        ),
    )

    plan_data = _parse_action_plan_json(
        raw_plan
    )

    raw_actions = plan_data.get(
        "actions",
        []
    )

    if not isinstance(raw_actions, list):
        raise RuntimeError(
            "Le champ 'actions' du plan doit être une liste."
        )

    validated_actions = []

    blocked_resource = None

    if age_status in AGE_RESOURCE_BY_STATUS:
        blocked_resource = (
            AGE_RESOURCE_BY_STATUS[
                age_status
            ]["blocked"]
            .lower()
        )

    for raw_action in raw_actions[:6]:

        if not isinstance(
            raw_action,
            dict,
        ):
            continue

        title = str(
            raw_action.get(
                "title",
                "",
            )
        ).strip()

        description = str(
            raw_action.get(
                "description",
                "",
            )
        ).strip()

        evidence = str(
            raw_action.get(
                "evidence",
                "",
            )
        ).strip()

        source_rank_raw = raw_action.get(
            "source_rank"
        )

        try:
            source_rank = int(
                source_rank_raw
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if (
            not title
            or not description
            or not evidence
        ):
            continue

        combined_action_text = (
            f"{title} {description} {evidence}"
        )

        # Aucun plan visible, français ou arabe, ne doit proposer
        # la ressource interdite, même si elle subsiste dans un
        # ancien passage documentaire récupéré par FAISS.
        if FORBIDDEN_REFERRAL_PATTERN.search(
            combined_action_text
        ):
            continue

        if not (
            1
            <= source_rank
            <= len(results)
        ):
            continue

        source_result = results[
            source_rank - 1
        ]

        normalized_evidence = (
            _normalize_text_for_evidence(
                evidence
            )
        )

        normalized_source = (
            _normalize_text_for_evidence(
                source_result.get(
                    "text",
                    "",
                )
            )
        )

        # Un extrait trop court est trop facile à "faire matcher"
        # accidentellement ; on exige une preuve un minimum
        # informative.
        if len(normalized_evidence) < 12:
            continue

        if (
            normalized_evidence
            not in normalized_source
        ):
            continue

        if blocked_resource:

            combined_action_text = combined_action_text.lower()

            if (
                blocked_resource
                in combined_action_text
            ):
                continue

        # Le plan visible doit parler directement à la victime.
        # Si le LLM laisse malgré le prompt une instruction destinée
        # à un accompagnateur, on la retire.
        if _is_agent_facing_action(
            title=title,
            description=description,
            language=language,
        ):
            continue

        source_list = build_sources(
            [source_result]
        )

        source = (
            source_list[0]
            if source_list
            else None
        )

        validated_actions.append(
            {
                "id":
                    f"action_{len(validated_actions) + 1}",

                "title":
                    title,

                "description":
                    description,

                "evidence":
                    evidence,

                "source":
                    source,
            }
        )

    # Déduplication conservatrice titre + description.
    deduplicated_actions = []
    seen_actions = set()

    for action in validated_actions:

        key = (
            re.sub(
                r"\s+",
                " ",
                action["title"],
            )
            .strip()
            .lower(),

            re.sub(
                r"\s+",
                " ",
                action["description"],
            )
            .strip()
            .lower(),
        )

        if key in seen_actions:
            continue

        seen_actions.add(
            key
        )

        deduplicated_actions.append(
            action
        )

    # Garantie finale de la ressource liée à l'âge :
    # Take It Down pour minor, StopNCII pour adult, mais uniquement
    # si cette ressource existe réellement dans les chunks récupérés.
    deduplicated_actions = _ensure_age_resource_action(
        actions=deduplicated_actions,
        results=results,
        age_status=age_status,
        language=language,
    )

    # Renumérotation propre après éventuel ajout déterministe.
    for index, action in enumerate(
        deduplicated_actions,
        start=1,
    ):
        action["id"] = f"action_{index}"

    if not deduplicated_actions:

        return {
            "outcome": "no_documented_actions",
            "language": language,
            "predicted_intent": predicted_intent,
            "clarification_required": False,
            "clarification_type": None,
            "emergency_override": classification.get(
                "emergency_override",
                False,
            ),
            "actions": [],
            "sources": build_sources(
                results
            ),
        }

    return {
        "outcome": "ready",
        "language": language,
        "predicted_intent": predicted_intent,
        "clarification_required": False,
        "clarification_type": None,
        "emergency_override": classification.get(
            "emergency_override",
            False,
        ),
        "actions": deduplicated_actions,
        "sources": build_sources(
            results
        ),
    }




# ============================================================
# 9. AFFICHAGE POUR TEST
# ============================================================

def print_generated_answer(
    question: str,
) -> None:
    """
    Affiche un test complet du pipeline.
    """

    print()
    print("=" * 80)
    print("QUESTION")
    print("=" * 80)
    print(question)

    result = generate_answer(
        question
    )

    print()
    print("=" * 80)
    print("LANGUE / INTENTION")
    print("=" * 80)

    print(
        "Langue détectée :",
        result.get("language"),
    )

    print(
        "Intention :",
        result[
            "predicted_intent"
        ],
    )

    print(
        "Confiance :",
        result[
            "intent_confidence"
        ],
    )

    print()
    print("=" * 80)
    print("RÉPONSE")
    print("=" * 80)

    print(
        result[
            "answer"
        ]
    )

    print()
    print("=" * 80)
    print("SOURCES")
    print("=" * 80)

    if not result["sources"]:

        print(
            "Aucune source."
        )

    else:

        for source in result[
            "sources"
        ]:

            print()

            print(
                "- Document :",
                source[
                    "document"
                ],
            )

            print(
                "  Langue :",
                source.get(
                    "language"
                ),
            )

            print(
                "  Page :",
                source[
                    "page"
                ],
            )

            print(
                "  Thème :",
                source[
                    "theme"
                ],
            )

            print(
                "  Intention :",
                source[
                    "intent"
                ],
            )

            print(
                "  Score :",
                source[
                    "score"
                ],
            )

    print()
    print("=" * 80)

    print(
        "Chunks utilisés :",
        result[
            "retrieved_chunks"
        ],
    )

    print(
        "Modèle :",
        result[
            "model"
        ],
    )


# ============================================================
# 10. TEST MANUEL
# ============================================================

if __name__ == "__main__":

    test_questions = [
        (
            "Mon compte Instagram a été piraté. "
            "Que dois-je faire ?"
        ),
        (
            "تم اختراق حسابي على إنستغرام. "
            "ماذا أفعل؟"
        ),
    ]

    for test_question in test_questions:

        print_generated_answer(
            test_question
        )
