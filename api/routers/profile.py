"""
api/routers/profile.py

Profil personnel d'une victime authentifiée.

GET   /profile/me
PATCH /profile/me

Le endpoint PATCH est protégé par CSRF.
La CIN est chiffrée avant stockage.
"""

from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from api.deps import (
    require_role,
    verify_csrf,
)

from auth.pii_crypto import (
    decrypt_sensitive,
    encrypt_sensitive,
)

from db.database import get_db

from db.models import (
    User,
    UserRole,
)

from db.victim_profile_model import (
    VictimProfile,
)

from db.victim_profile_schemas import (
    VictimProfilePublic,
    VictimProfileUpdate,
)


router = APIRouter(
    prefix="/profile",
    tags=["victim-profile"],
)


def build_emc_id(
    user_id,
) -> str:
    # Identifiant d'affichage.
    # Le UUID complet reste la vraie clé unique en base.
    compact = str(
        user_id
    ).replace(
        "-",
        ""
    ).upper()

    return (
        f"V-{compact[:12]}"
    )


def mask_cin(
    cin: str | None,
) -> str | None:
    if not cin:
        return None

    if len(cin) <= 4:
        return "•" * len(
            cin
        )

    prefix_length = min(
        2,
        max(
            1,
            len(cin) - 4,
        ),
    )

    return (
        cin[:prefix_length]
        + "•" * max(
            2,
            len(cin)
            - prefix_length
            - 2,
        )
        + cin[-2:]
    )


def is_identity_complete(
    profile: VictimProfile | None,
) -> bool:
    if profile is None:
        return False

    return all(
        [
            profile.first_name,
            profile.last_name,
            profile.date_of_birth,
            profile.phone,
            profile.cin_encrypted,
        ]
    )


def serialize_profile(
    *,
    user: User,
    profile: VictimProfile | None,
) -> VictimProfilePublic:
    cin = (
        decrypt_sensitive(
            profile.cin_encrypted
        )
        if (
            profile
            and profile.cin_encrypted
        )
        else None
    )

    first_name = (
        profile.first_name
        if profile
        else None
    )

    last_name = (
        profile.last_name
        if profile
        else None
    )

    full_name = (
        " ".join(
            part
            for part in [
                first_name,
                last_name,
            ]
            if part
        )
        or None
    )

    return VictimProfilePublic(
        user_id=user.id,
        emc_id=build_emc_id(
            user.id
        ),
        username=user.username,
        email=user.email,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        date_of_birth=(
            profile.date_of_birth
            if profile
            else None
        ),
        phone=(
            profile.phone
            if profile
            else None
        ),
        cin=cin,
        cin_masked=mask_cin(
            cin
        ),
        identity_complete=(
            is_identity_complete(
                profile
            )
        ),
        identity_completed_at=(
            profile.identity_completed_at
            if profile
            else None
        ),
        created_at=(
            profile.created_at
            if profile
            else None
        ),
        updated_at=(
            profile.updated_at
            if profile
            else None
        ),
    )


@router.get(
    "/me",
    response_model=VictimProfilePublic,
)
def get_my_profile(
    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),
    db: Session = Depends(
        get_db
    ),
) -> VictimProfilePublic:

    profile = db.get(
        VictimProfile,
        current_user.id,
    )

    return serialize_profile(
        user=current_user,
        profile=profile,
    )


@router.patch(
    "/me",
    response_model=VictimProfilePublic,
)
def update_my_profile(
    payload: VictimProfileUpdate,
    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),
    _: None = Depends(
        verify_csrf
    ),
    db: Session = Depends(
        get_db
    ),
) -> VictimProfilePublic:

    profile = db.get(
        VictimProfile,
        current_user.id,
    )

    if profile is None:
        profile = VictimProfile(
            user_id=current_user.id
        )

        db.add(
            profile
        )

    fields = (
        payload.model_fields_set
    )

    if "first_name" in fields:
        profile.first_name = (
            payload.first_name
        )

    if "last_name" in fields:
        profile.last_name = (
            payload.last_name
        )

    if "date_of_birth" in fields:
        profile.date_of_birth = (
            payload.date_of_birth
        )

    if "phone" in fields:
        profile.phone = (
            payload.phone
        )

    if "cin" in fields:
        if payload.cin:
            profile.cin_encrypted = (
                encrypt_sensitive(
                    payload.cin
                )
            )

            profile.cin_last4 = (
                payload.cin[-4:]
            )
        else:
            profile.cin_encrypted = None
            profile.cin_last4 = None

    if is_identity_complete(
        profile
    ):
        if (
            profile.identity_completed_at
            is None
        ):
            profile.identity_completed_at = (
                datetime.now(
                    timezone.utc
                )
            )
    else:
        profile.identity_completed_at = (
            None
        )

    db.commit()

    db.refresh(
        profile
    )

    return serialize_profile(
        user=current_user,
        profile=profile,
    )
