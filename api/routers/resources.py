"""
api/routers/resources.py

Gestion des ressources documentaires EMC Helpline.

Côté victime :
    GET /resources
    GET /resources/{resource_id}

Côté administration :
    GET    /admin/resources
    POST   /admin/resources
    PATCH  /admin/resources/{resource_id}
    DELETE /admin/resources/{resource_id}

Sécurité :
- authentification obligatoire ;
- une victime voit uniquement les ressources publiées ;
- les brouillons restent invisibles côté victime ;
- ajout / modification / suppression réservés à l'admin ;
- CSRF obligatoire sur POST / PATCH / DELETE ;
- created_by provient exclusivement de l'admin authentifié ;
- aucune modification du pipeline RAG / LLM / FAISS.
"""

import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

from sqlalchemy import (
    select,
)

from sqlalchemy.orm import (
    Session,
)


from api.deps import (
    require_role,
    verify_csrf,
)

from db.database import (
    get_db,
)

from db.models import (
    Resource,
    User,
    UserRole,
)

from db.resource_schemas import (
    AdminResourcePublic,
    ResourceCreate,
    ResourcePublic,
    ResourceUpdate,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    tags=[
        "resources",
    ]
)


# ============================================================
# HELPERS
# ============================================================

def _get_resource_or_404(
    resource_id: uuid.UUID,
    db: Session,
) -> Resource:
    """
    Recherche une ressource indépendamment de son statut.

    À utiliser uniquement dans les routes administrateur.
    """

    resource = db.get(
        Resource,
        resource_id,
    )

    if resource is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Ressource introuvable."
            ),
        )

    return resource


# ============================================================
# VICTIME
# GET /resources
# ============================================================

@router.get(
    "/resources",
    response_model=list[
        ResourcePublic
    ],
)
def list_published_resources(
    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),
    db: Session = Depends(
        get_db
    ),
) -> list[Resource]:
    """
    Liste les ressources publiées.

    Les ressources draft ne sont jamais retournées.
    """

    del current_user

    stmt = (
        select(Resource)
        .where(
            Resource.status
            == "published"
        )
        .order_by(
            Resource.display_order.asc(),
            Resource.created_at.desc(),
        )
    )

    return list(
        db.scalars(
            stmt
        ).all()
    )


# ============================================================
# VICTIME
# GET /resources/{resource_id}
# ============================================================

@router.get(
    "/resources/{resource_id}",
    response_model=ResourcePublic,
)
def get_published_resource(
    resource_id: uuid.UUID,
    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),
    db: Session = Depends(
        get_db
    ),
) -> Resource:
    """
    Retourne une ressource uniquement si elle est publiée.

    Une ressource draft renvoie volontairement 404 côté victime
    afin de ne pas révéler son existence.
    """

    del current_user

    stmt = (
        select(Resource)
        .where(
            Resource.id
            == resource_id,
            Resource.status
            == "published",
        )
    )

    resource = db.scalar(
        stmt
    )

    if resource is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Ressource introuvable."
            ),
        )

    return resource


# ============================================================
# ADMIN
# GET /admin/resources
# ============================================================

@router.get(
    "/admin/resources",
    response_model=list[
        AdminResourcePublic
    ],
)
def list_admin_resources(
    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),
    db: Session = Depends(
        get_db
    ),
) -> list[Resource]:
    """
    Liste toutes les ressources pour l'administration.

    Inclut :
    - published
    - draft
    """

    del current_user

    stmt = (
        select(Resource)
        .order_by(
            Resource.display_order.asc(),
            Resource.created_at.desc(),
        )
    )

    return list(
        db.scalars(
            stmt
        ).all()
    )


# ============================================================
# ADMIN
# POST /admin/resources
# ============================================================

@router.post(
    "/admin/resources",
    response_model=(
        AdminResourcePublic
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
def create_resource(
    payload: ResourceCreate,

    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),

    _: None = Depends(
        verify_csrf
    ),

    db: Session = Depends(
        get_db
    ),
) -> Resource:
    """
    Crée une nouvelle ressource.

    created_by est toujours dérivé du compte admin connecté.
    Le client ne peut jamais choisir cet identifiant.
    """

    resource = Resource(
        category=payload.category,

        title_fr=payload.title_fr,
        title_ar=payload.title_ar,

        description_fr=(
            payload.description_fr
        ),

        description_ar=(
            payload.description_ar
        ),

        content_fr=payload.content_fr,
        content_ar=payload.content_ar,

        points_fr=payload.points_fr,
        points_ar=payload.points_ar,

        icon=payload.icon,
        tone=payload.tone,

        status=payload.status,

        display_order=(
            payload.display_order
        ),

        created_by=(
            current_user.id
        ),
    )

    db.add(
        resource
    )

    db.commit()

    db.refresh(
        resource
    )

    return resource


# ============================================================
# ADMIN
# PATCH /admin/resources/{resource_id}
# ============================================================

@router.patch(
    "/admin/resources/{resource_id}",
    response_model=(
        AdminResourcePublic
    ),
)
def update_resource(
    resource_id: uuid.UUID,

    payload: ResourceUpdate,

    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),

    _: None = Depends(
        verify_csrf
    ),

    db: Session = Depends(
        get_db
    ),
) -> Resource:
    """
    Modifie partiellement une ressource existante.

    created_by et id ne sont jamais modifiables via cette route.
    """

    del current_user

    resource = (
        _get_resource_or_404(
            resource_id,
            db,
        )
    )

    changes = (
        payload.model_dump(
            exclude_unset=True
        )
    )

    for (
        field_name,
        value,
    ) in changes.items():
        setattr(
            resource,
            field_name,
            value,
        )

    db.commit()

    db.refresh(
        resource
    )

    return resource


# ============================================================
# ADMIN
# DELETE /admin/resources/{resource_id}
# ============================================================

@router.delete(
    "/admin/resources/{resource_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
def delete_resource(
    resource_id: uuid.UUID,

    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),

    _: None = Depends(
        verify_csrf
    ),

    db: Session = Depends(
        get_db
    ),
) -> Response:
    """
    Supprime définitivement une ressource.

    La suppression est réservée à un administrateur authentifié.
    """

    del current_user

    resource = (
        _get_resource_or_404(
            resource_id,
            db,
        )
    )

    db.delete(
        resource
    )

    db.commit()

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )