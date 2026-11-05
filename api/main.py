"""
api/main.py

API FastAPI exposant le pipeline RAG bilingue (français/arabe)
d'EMC Helpline, déjà validé (rag/generator.py -> generate_answer()).

Cette API conserve une couche HTTP mince : elle délègue la logique
métier à rag.generator et met en forme les réponses en JSON. Le pipeline
IA (CamemBERT, FAISS, Llama 3.1) n'est ni modifié ni dupliqué ici.

Lancement (depuis 06_Development, venv activé) :

    uvicorn api.main:app --reload

Documentation interactive une fois lancé :

    http://127.0.0.1:8000/docs
"""

from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from auth.config import FRONTEND_ORIGIN
from api.routers import profile as profile_router
from api.routers import (
    auth as auth_router,
    cases as cases_router,
    action_plans as action_plans_router,
    evidence,
    history as history_router,
)
from api.routers import resources as resources_router



from api.routers import (
    admin_cases
    as admin_cases_router,
)

from api.routers import (
    admin_overview
    as admin_overview_router,
)

from api.routers import (
    admin_statistics
    as admin_statistics_router,
)
from rag.generator import (
    build_action_plan,
    classify_situation,
    generate_answer,
    resolve_pending_clarification,
)


# ============================================================
# 1. APPLICATION FASTAPI
# ============================================================

app = FastAPI(
    title="EMC Helpline API",
    description=(
        "API du chatbot EMC Helpline (assistance et orientation des "
        "victimes de cyberviolences). Expose le pipeline RAG bilingue "
        "(français / arabe) déjà validé."
    ),
    version="0.2.0",
)


# ============================================================
# 2. CORS
# ============================================================
#
# Ouvert à toutes les origines pour l'instant (développement local,
# tests via /docs). À restreindre à l'origine exacte du frontend
# React lorsqu'il existera (ex: ["http://localhost:5173"]).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "X-CSRF-Token",
    ],
)


# ============================================================
# 2 bis. ROUTER AUTH
# ============================================================

app.include_router(
    auth_router.router
)

app.include_router(
    cases_router.router
)

app.include_router(
    action_plans_router.router
)

app.include_router(
    evidence.router
)

app.include_router(
    history_router.router
)
app.include_router(
    resources_router.router
)
app.include_router(
    admin_overview_router.router
)
app.include_router(
    admin_statistics_router.router
)
app.include_router(
    admin_cases_router.router
)
app.include_router(
    profile_router.router
)

# ============================================================
# 3. SCHÉMAS PYDANTIC
# ============================================================

class ChatContext(BaseModel):
    """
    Contexte minimal de clarification multi-tour (Phase 3C-A).

    Envoyé par le frontend UNIQUEMENT lorsqu'une clarification d'âge
    est en attente (pendingContext côté React). Le backend reste
    stateless : aucune conversation n'est stockée côté FastAPI, ce
    contexte est intégralement fourni à chaque appel par l'appelant.

    Volontairement strict (Literal) pour cette version MVP : ne
    couvre que les deux intentions actuellement dépendantes de l'âge
    et le seul type de clarification existant. Pas de validation
    supplémentaire par nouvelle classification de original_message --
    cela ajouterait du retrieval inutile pour ce qui reste une simple
    vérification de forme.
    """

    pending_intent: Literal[
        "Sextorsion",
        "Diffusion non consentie d'images",
    ]

    pending_clarification: Literal["age_at_time_of_facts"]

    original_message: str = Field(..., min_length=1)

    original_language: Literal["fr", "ar"]

    @field_validator("original_message")
    @classmethod
    def original_message_must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("original_message ne peut pas être vide.")

        return value.strip()


class ChatHistoryMessage(BaseModel):
    """Message récent envoyé uniquement pour assurer la continuité."""

    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Le contenu historique ne peut pas être vide.")

        return value.strip()


class ChatRequest(BaseModel):
    """Requête envoyée par l'utilisateur (ou par Swagger /docs)."""

    message: str = Field(
        ...,
        min_length=1,
        description="Message de l'utilisateur, en français ou en arabe.",
        examples=["Mon compte Instagram a été piraté. Que dois-je faire ?"],
    )

    debug: bool = Field(
        default=False,
        description=(
            "Si True, la réponse inclut les sources documentaires et "
            "des informations techniques internes (mode développement)."
        ),
    )

    context: ChatContext | None = Field(
        default=None,
        description=(
            "Contexte optionnel de clarification multi-tour en attente "
            "(Phase 3C-A). Absent ou null pour une requête normale -- "
            "entièrement rétrocompatible avec les clients existants."
        ),
    )

    history: list[ChatHistoryMessage] = Field(
        default_factory=list,
        max_length=10,
        description=(
            "Dix derniers messages visibles de la conversation. "
            "Le serveur ne les conserve pas entre les requêtes."
        ),
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        """
        Rejette une question vide ou ne contenant que des espaces.
        Pydantic vérifie déjà min_length=1 sur la chaîne brute, mais
        cela n'empêche pas une chaîne composée uniquement d'espaces
        (" ") de passer -- on le vérifie donc explicitement ici.
        """

        if not value or not value.strip():
            raise ValueError("Le message ne peut pas être vide.")

        return value.strip()


class ChatResponse(BaseModel):
    """Réponse renvoyée à l'utilisateur."""

    answer: str
    language: str | None = None
    predicted_intent: str | None = None
    clarification_required: str | None = None

    # Présents uniquement si `debug=True` dans la requête. Volontairement
    # typés en `list[dict]` / `dict` plutôt qu'en modèles Pydantic stricts,
    # pour ne pas avoir à resynchroniser ce fichier si la forme exacte des
    # sources retournées par generate_answer() évolue légèrement plus tard.
    sources: list[dict[str, Any]] | None = None
    debug_info: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    status: str


class AssessmentRequest(BaseModel):
    """
    Requête envoyée par la page Assessment.jsx (Phase 3B).

    interface_language reflète uniquement la langue globale choisie
    par l'utilisateur dans l'interface (FR / العربية) : elle ne sert
    à AUCUN moment à classifier la description. La classification
    utilise toujours detect_language(description), exactement comme
    /chat -- interface_language est conservé pour un usage futur
    (ex: formuler des messages dans la bonne langue) mais n'influence
    pas classify_situation().
    """

    description: str = Field(
        ...,
        min_length=1,
        description="Description libre de la situation, en français ou en arabe.",
        examples=["Mon compte Instagram a été piraté. Que dois-je faire ?"],
    )

    interface_language: Literal["fr", "ar"] | None = Field(
        default=None,
        description=(
            "Langue globale de l'interface (FR/AR), à titre informatif "
            "uniquement. N'affecte pas la classification de la description."
        ),
    )

    platform: str | None = None
    threat_present: bool | None = None
    content_already_shared: bool | None = None
    intimate_content: bool | None = None
    personal_data_exposed: bool | None = None
    account_compromised: bool | None = None

    @field_validator("description")
    @classmethod
    def description_must_not_be_blank(cls, value: str) -> str:
        """
        Même garde-fou que ChatRequest.message : Pydantic vérifie déjà
        min_length=1 sur la chaîne brute, mais cela n'empêche pas une
        chaîne composée uniquement d'espaces (" ") de passer.
        """

        if not value or not value.strip():
            raise ValueError("La description ne peut pas être vide.")

        return value.strip()


class AssessmentResponse(BaseModel):
    """
    Réponse structurée de /assessment. Ne contient JAMAIS de texte
    conversationnel généré par un LLM -- uniquement le résultat de
    classify_situation(), qui n'appelle jamais Ollama.

    Les champs structurés du formulaire (threat_present, platform,
    etc.) ne sont volontairement PAS encore utilisés pour détecter des
    contradictions dans cette première version : cette fonctionnalité
    est prévue pour une sous-phase ultérieure, après validation d'une
    table de correspondance intention -> champs attendus.
    """

    detected_text_language: str
    detected_intent: str | None
    clarification_required: bool
    clarification_type: str | None = None
    missing_information: list[str] = Field(default_factory=list)
    emergency_override: bool



class ActionPlanRequest(BaseModel):
    """
    Demande de construction d'un plan d'action à partir d'une
    description libre.

    age_at_time_of_facts est optionnel et ne doit être envoyé que
    lorsqu'une clarification d'âge a déjà été résolue côté interface.
    """

    description: str = Field(
        ...,
        min_length=1,
        description=(
            "Description de la situation à partir de laquelle "
            "construire le plan d'action."
        ),
    )

    interface_language: Literal[
        "fr",
        "ar",
    ] | None = None

    age_at_time_of_facts: Literal[
        "minor",
        "adult",
    ] | None = None

    @field_validator("description")
    @classmethod
    def action_plan_description_must_not_be_blank(
        cls,
        value: str,
    ) -> str:

        if not value or not value.strip():
            raise ValueError(
                "La description ne peut pas être vide."
            )

        return value.strip()


class ActionPlanSource(BaseModel):
    document: str | None = None
    page: int | None = None
    theme: str | None = None
    intent: str | None = None
    language: str | None = None
    score: float | None = None
    semantic_score: float | None = None


class ActionPlanItem(BaseModel):
    id: str
    title: str
    description: str
    evidence: str
    source: ActionPlanSource | None = None


class ActionPlanResponse(BaseModel):
    outcome: str
    language: str
    detected_intent: str | None = None
    clarification_required: bool
    clarification_type: str | None = None
    emergency_override: bool
    actions: list[ActionPlanItem] = Field(
        default_factory=list
    )
    sources: list[ActionPlanSource] = Field(
        default_factory=list
    )




# ============================================================
# 4. ENDPOINT /health
# ============================================================

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Vérifie simplement que l'API répond."""

    return HealthResponse(status="ok")


# ============================================================
# 5. ENDPOINT /chat
# ============================================================

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Reçoit un message utilisateur (français ou arabe) et retourne la
    réponse générée par le pipeline RAG existant.

    Deux chemins possibles :
    - request.context est None (cas normal, y compris tous les
      clients existants) : generate_answer(request.message), inchangé
      depuis la Phase 3B -- passe par classify_situation().
    - request.context est fourni (Phase 3C-A, réponse à une
      clarification d'âge en attente) : resolve_pending_clarification(),
      qui ne passe JAMAIS par classify_situation() -- l'intention
      reste celle transmise dans le contexte, jamais redérivée à
      partir du message court.
    """

    try:

        if request.context is not None:

            result = resolve_pending_clarification(
                message=request.message,
                pending_intent=request.context.pending_intent,
                pending_clarification=request.context.pending_clarification,
                original_message=request.context.original_message,
                original_language=request.context.original_language,
            )

        else:

            result = generate_answer(
                request.message,
                history=[
                    item.model_dump()
                    for item in request.history
                ],
            )

    except ValueError as exc:
        # generate_answer() / resolve_pending_clarification() lèvent
        # ValueError pour un message vide ; normalement déjà
        # intercepté par le validator Pydantic ci-dessus, mais on le
        # gère aussi ici par sécurité.
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        # Erreurs venant de call_ollama() : Ollama non lancé, timeout,
        # réponse invalide, etc. Peut survenir sur les deux chemins
        # dès que force_intent_results() trouve des résultats et que
        # _finalize_answer() est appelée.
        raise HTTPException(
            status_code=503,
            detail=(
                "Le service de génération de réponse est momentanément "
                "indisponible. Vérifiez qu'Ollama est bien lancé."
            ),
        ) from exc

    except Exception as exc:
        # Filet de sécurité générique : ne jamais laisser fuiter une
        # trace interne à l'utilisateur final.
        raise HTTPException(
            status_code=500,
            detail="Une erreur interne est survenue lors du traitement de votre demande.",
        ) from exc

    response = ChatResponse(
        answer=result.get("answer", ""),
        language=result.get("language"),
        predicted_intent=result.get("predicted_intent"),
        clarification_required=result.get("clarification_required"),
    )

    if request.debug:

        response.sources = result.get("sources", [])

        response.debug_info = {
            "intent_confidence": result.get("intent_confidence"),
            "retrieved_chunks": result.get("retrieved_chunks"),
            "model": result.get("model"),
            "emergency_override": result.get("emergency_override", False),
            "intent_source": result.get("intent_source"),
        }

    return response


# ============================================================
# 6. ENDPOINT /assessment
# ============================================================

@app.post("/assessment", response_model=AssessmentResponse)
def assessment(request: AssessmentRequest) -> AssessmentResponse:
    """
    Reçoit la description libre saisie dans la page "Évaluer ma
    situation" et retourne un résultat de triage structuré, SANS
    jamais appeler Ollama.

    N'effectue aucune logique métier ici : classify_situation() gère
    déjà la détection de langue, la garde d'urgence, le routeur par
    mots-clés arabe, le retrieval + classification (CamemBERT ou vote
    majoritaire) et la clarification d'âge -- exactement la même
    logique que /chat, jusqu'au point où /chat appellerait Llama.
    classify_situation() s'arrête avant cet appel.

    Les réponses structurées du formulaire (threat_present, platform,
    etc.) ne sont pas encore exploitées : cette version se limite à
    la classification de la description libre.
    """

    try:
        classification = classify_situation(request.description)

    except ValueError as exc:
        # classify_situation() lève ValueError pour une description
        # vide ; normalement déjà intercepté par le validator Pydantic
        # ci-dessus, mais on le gère aussi ici par sécurité.
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Filet de sécurité générique : ne jamais laisser fuiter une
        # trace interne à l'utilisateur final. Notez qu'aucune erreur
        # liée à Ollama (RuntimeError de call_ollama()) ne peut
        # survenir ici : classify_situation() n'appelle jamais
        # call_ollama().
        raise HTTPException(
            status_code=500,
            detail="Une erreur interne est survenue lors du traitement de votre demande.",
        ) from exc

    return AssessmentResponse(
        detected_text_language=classification["language"],
        detected_intent=classification["predicted_intent"],
        clarification_required=classification["clarification_required"],
        clarification_type=classification["clarification_type"],
        missing_information=classification["missing_information"],
        emergency_override=classification["emergency_override"],
    )


# ============================================================
# 7. ENDPOINT /action-plan
# ============================================================

@app.post(
    "/action-plan",
    response_model=ActionPlanResponse,
)
def action_plan(
    request: ActionPlanRequest,
) -> ActionPlanResponse:
    """
    Construit un plan d'action structuré à partir du pipeline RAG.

    FastAPI ne définit aucune action métier ici :
    build_action_plan() effectue la classification, sélectionne les
    passages documentaires et ne conserve que les actions dont la
    preuve textuelle a été vérifiée dans le passage source.

    L'endpoint reste stateless.
    """

    try:

        result = build_action_plan(
            question=request.description,
            age_status=request.age_at_time_of_facts,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=503,
            detail=(
                "Le service de construction du plan d'action "
                "est momentanément indisponible. "
                "Vérifiez qu'Ollama est bien lancé."
            ),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Une erreur interne est survenue lors de la "
                "construction du plan d'action."
            ),
        ) from exc

    return ActionPlanResponse(
        outcome=result["outcome"],
        language=result["language"],
        detected_intent=result.get(
            "predicted_intent"
        ),
        clarification_required=result.get(
            "clarification_required",
            False,
        ),
        clarification_type=result.get(
            "clarification_type"
        ),
        emergency_override=result.get(
            "emergency_override",
            False,
        ),
        actions=result.get(
            "actions",
            [],
        ),
        sources=result.get(
            "sources",
            [],
        ),
    )
