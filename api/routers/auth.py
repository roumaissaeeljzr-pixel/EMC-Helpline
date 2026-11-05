"""
api/routers/auth.py

Authentification EMC Helpline.

Endpoints :

POST /auth/register
POST /auth/resend-verification-code
POST /auth/verify-email

POST /auth/login
POST /auth/logout
GET  /auth/me

POST /auth/forgot-password
POST /auth/verify-reset-code
POST /auth/reset-password
"""

import logging
import uuid

from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

from sqlalchemy import (
    func,
)

from sqlalchemy.orm import (
    Session,
)

from api.deps import (
    get_current_user,
    verify_csrf,
)

from auth.config import (
    ACCESS_TOKEN_COOKIE_NAME,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    CSRF_COOKIE_NAME,
    EMAIL_VERIFICATION_EXPIRE_MINUTES,
    PASSWORD_RESET_EXPIRE_MINUTES,
)

from auth.email_service import (
    send_email_verification_code,
    send_password_reset_code_email,
)

from auth.email_verification import (
    email_verification_code_matches,
    generate_email_verification_code,
    hash_email_verification_code,
)

from auth.password_reset import (
    create_verified_reset_token,
    decode_verified_reset_token,
    generate_reset_code,
    hash_reset_code,
    password_hash_fingerprint,
    reset_code_matches,
)

from auth.password_reset_schemas import (
    AuthMessage,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyResetCodeRequest,
    VerifyResetCodeResponse,
)

from auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)

from db.database import (
    get_db,
)

from db.models import (
    EmailVerificationCode,
    PasswordResetCode,
    User,
    UserRole,
)

from db.schemas import (
    ResendVerificationCodeRequest,
    UserLogin,
    UserPublic,
    UserRegister,
    VerifyEmailRequest,
)


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# ============================================================
# CONSTANTES
# ============================================================

GENERIC_VERIFICATION_MESSAGE = (
    "Si un compte non vérifié correspondant existe, "
    "un code de vérification a été envoyé."
)

INVALID_VERIFICATION_CODE_MESSAGE = (
    "Le code est invalide ou expiré."
)

EMAIL_VERIFICATION_MAX_ATTEMPTS = 5

EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS = 60


GENERIC_FORGOT_MESSAGE = (
    "Si un compte correspondant existe, "
    "un code de vérification a été envoyé."
)

INVALID_RESET_CODE_MESSAGE = (
    "Le code est invalide ou expiré."
)

INVALID_RESET_MESSAGE = (
    "La demande de réinitialisation "
    "est invalide ou expirée."
)

RESET_MAX_ATTEMPTS = 5

RESET_RESEND_COOLDOWN_SECONDS = 60


# ============================================================
# COOKIES
# ============================================================

def _set_auth_cookies(
    response: Response,
    token: str,
    csrf_value: str,
) -> None:

    max_age = (
        ACCESS_TOKEN_EXPIRE_MINUTES
        * 60
    )

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=max_age,
        path="/",
    )

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_value,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=max_age,
        path="/",
    )


# ============================================================
# INSCRIPTION
# ============================================================

@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserRegister,
    db: Session = Depends(
        get_db
    ),
) -> User:

    existing = (
        db.query(User)
        .filter(
            (
                func.lower(
                    User.username
                )
                ==
                payload.username.lower()
            )
            |
            (
                func.lower(
                    User.email
                )
                ==
                payload.email.lower()
            )
        )
        .first()
    )

    if existing is not None:

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Ce nom d'utilisateur "
                "ou cet email est déjà utilisé."
            ),
        )

    user = User(
        username=payload.username,

        email=(
            payload.email.lower()
        ),

        password_hash=(
            hash_password(
                payload.password
            )
        ),

        role=UserRole.victim,

        email_verified=False,
    )

    db.add(user)

    # Génère l'identifiant UUID sans encore
    # terminer la transaction.
    db.flush()

    now = datetime.now(
        timezone.utc
    )

    code = (
        generate_email_verification_code()
    )

    verification_request = (
        EmailVerificationCode(
            user_id=user.id,

            code_hash=(
                hash_email_verification_code(
                    user_id=str(
                        user.id
                    ),
                    code=code,
                )
            ),

            attempts=0,

            expires_at=(
                now
                + timedelta(
                    minutes=(
                        EMAIL_VERIFICATION_EXPIRE_MINUTES
                    )
                )
            ),
        )
    )

    db.add(
        verification_request
    )

    db.commit()

    db.refresh(user)

    try:

        send_email_verification_code(
            to_email=user.email,
            code=code,
            language=payload.language,
        )

    except Exception:

        # Le compte reste enregistré.
        # L'utilisateur pourra redemander
        # le code après correction du SMTP.
        logger.exception(
            "Échec de l'envoi du code "
            "de vérification d'e-mail."
        )

    return user


# ============================================================
# RENVOYER LE CODE DE VÉRIFICATION
# ============================================================

@router.post(
    "/resend-verification-code",
    response_model=AuthMessage,
)
def resend_verification_code(
    payload: ResendVerificationCodeRequest,

    db: Session = Depends(
        get_db
    ),
) -> AuthMessage:

    user = (
        db.query(User)
        .filter(
            func.lower(
                User.email
            )
            ==
            payload.email.lower()
        )
        .first()
    )

    # Réponse générique afin de ne pas révéler
    # si une adresse existe dans PostgreSQL.
    if (
        user is None
        or not user.is_active
        or user.email_verified
    ):

        return AuthMessage(
            message=(
                GENERIC_VERIFICATION_MESSAGE
            )
        )

    now = datetime.now(
        timezone.utc
    )

    latest_request = (
        db.query(
            EmailVerificationCode
        )
        .filter(
            EmailVerificationCode.user_id
            == user.id
        )
        .order_by(
            EmailVerificationCode
            .created_at
            .desc()
        )
        .first()
    )

    # Empêcher les renvois répétés
    # pendant 60 secondes.
    if (
        latest_request is not None
        and latest_request.created_at
        is not None
        and latest_request.created_at
        >
        now
        - timedelta(
            seconds=(
                EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS
            )
        )
    ):

        return AuthMessage(
            message=(
                GENERIC_VERIFICATION_MESSAGE
            )
        )

    # Invalider tous les anciens codes actifs.
    (
        db.query(
            EmailVerificationCode
        )
        .filter(
            EmailVerificationCode.user_id
            == user.id,

            EmailVerificationCode.used_at
            .is_(None),
        )
        .update(
            {
                EmailVerificationCode.used_at:
                    now
            },
            synchronize_session=False,
        )
    )

    code = (
        generate_email_verification_code()
    )

    verification_request = (
        EmailVerificationCode(
            user_id=user.id,

            code_hash=(
                hash_email_verification_code(
                    user_id=str(
                        user.id
                    ),
                    code=code,
                )
            ),

            attempts=0,

            expires_at=(
                now
                + timedelta(
                    minutes=(
                        EMAIL_VERIFICATION_EXPIRE_MINUTES
                    )
                )
            ),
        )
    )

    db.add(
        verification_request
    )

    db.commit()

    try:

        send_email_verification_code(
            to_email=user.email,
            code=code,
            language=payload.language,
        )

    except Exception:

        logger.exception(
            "Échec du renvoi du code "
            "de vérification d'e-mail."
        )

    return AuthMessage(
        message=(
            GENERIC_VERIFICATION_MESSAGE
        )
    )


# ============================================================
# VÉRIFIER LE CODE DE L'ADRESSE E-MAIL
# ============================================================

@router.post(
    "/verify-email",
    response_model=AuthMessage,
)
def verify_email(
    payload: VerifyEmailRequest,

    db: Session = Depends(
        get_db
    ),
) -> AuthMessage:

    user = (
        db.query(User)
        .filter(
            func.lower(
                User.email
            )
            ==
            payload.email.lower()
        )
        .first()
    )

    if (
        user is None
        or not user.is_active
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                INVALID_VERIFICATION_CODE_MESSAGE
            ),
        )

    if user.email_verified:

        return AuthMessage(
            message=(
                "L'adresse e-mail "
                "est déjà vérifiée."
            )
        )

    verification_request = (
        db.query(
            EmailVerificationCode
        )
        .filter(
            EmailVerificationCode.user_id
            == user.id,

            EmailVerificationCode.used_at
            .is_(None),
        )
        .order_by(
            EmailVerificationCode
            .created_at
            .desc()
        )
        .first()
    )

    now = datetime.now(
        timezone.utc
    )

    if (
        verification_request is None
        or verification_request.expires_at
        <= now
        or verification_request.attempts
        >= EMAIL_VERIFICATION_MAX_ATTEMPTS
    ):

        if (
            verification_request
            is not None
            and verification_request.used_at
            is None
        ):

            verification_request.used_at = (
                now
            )

            db.commit()

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                INVALID_VERIFICATION_CODE_MESSAGE
            ),
        )

    code_is_valid = (
        email_verification_code_matches(
            user_id=str(
                user.id
            ),
            code=payload.code,
            expected_hash=(
                verification_request.code_hash
            ),
        )
    )

    if not code_is_valid:

        verification_request.attempts += 1

        if (
            verification_request.attempts
            >= EMAIL_VERIFICATION_MAX_ATTEMPTS
        ):

            verification_request.used_at = (
                now
            )

        db.commit()

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                INVALID_VERIFICATION_CODE_MESSAGE
            ),
        )

    verification_request.used_at = (
        now
    )

    user.email_verified = True

    user.email_verified_at = (
        now
    )

    db.commit()

    return AuthMessage(
        message=(
            "Adresse e-mail vérifiée "
            "avec succès."
        )
    )


# ============================================================
# CONNEXION
# ============================================================

@router.post(
    "/login",
    response_model=UserPublic,
)
def login(
    payload: UserLogin,
    response: Response,

    db: Session = Depends(
        get_db
    ),
) -> User:

    user = (
        db.query(User)
        .filter(
            func.lower(
                User.username
            )
            ==
            payload.username.lower()
        )
        .first()
    )

    if (
        user is None
        or not verify_password(
            payload.password,
            user.password_hash,
        )
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Nom d'utilisateur ou "
                "mot de passe incorrect."
            ),
        )

    if not user.is_active:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Ce compte est désactivé."
            ),
        )

    if not user.email_verified:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Adresse e-mail non vérifiée. "
                "Demandez un nouveau code "
                "de vérification."
            ),
        )

    token, csrf_value = (
        create_access_token(
            user_id=str(
                user.id
            ),
            role=user.role.value,
        )
    )

    _set_auth_cookies(
        response,
        token,
        csrf_value,
    )

    return user


# ============================================================
# DÉCONNEXION
# ============================================================

@router.post(
    "/logout",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
def logout(
    response: Response,

    current_user: User = Depends(
        get_current_user
    ),

    _csrf_checked: None = Depends(
        verify_csrf
    ),
) -> None:

    response.delete_cookie(
        ACCESS_TOKEN_COOKIE_NAME,
        path="/",
    )

    response.delete_cookie(
        CSRF_COOKIE_NAME,
        path="/",
    )


# ============================================================
# UTILISATEUR CONNECTÉ
# ============================================================

@router.get(
    "/me",
    response_model=UserPublic,
)
def me(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:

    return current_user


# ============================================================
# MOT DE PASSE OUBLIÉ
# ============================================================

@router.post(
    "/forgot-password",
    response_model=AuthMessage,
)
def forgot_password(
    payload: ForgotPasswordRequest,

    db: Session = Depends(
        get_db
    ),
) -> AuthMessage:

    user = (
        db.query(User)
        .filter(
            func.lower(
                User.email
            )
            ==
            payload.email.lower()
        )
        .first()
    )

    # Ne jamais révéler si une adresse
    # existe dans la base.
    if (
        user is None
        or not user.is_active
    ):

        return AuthMessage(
            message=(
                GENERIC_FORGOT_MESSAGE
            )
        )

    now = datetime.now(
        timezone.utc
    )

    latest_request = (
        db.query(
            PasswordResetCode
        )
        .filter(
            PasswordResetCode.user_id
            == user.id
        )
        .order_by(
            PasswordResetCode
            .created_at
            .desc()
        )
        .first()
    )

    if (
        latest_request is not None
        and latest_request.created_at
        is not None
        and latest_request.created_at
        >
        now
        - timedelta(
            seconds=(
                RESET_RESEND_COOLDOWN_SECONDS
            )
        )
    ):

        return AuthMessage(
            message=(
                GENERIC_FORGOT_MESSAGE
            )
        )

    # Invalider les anciens codes.
    (
        db.query(
            PasswordResetCode
        )
        .filter(
            PasswordResetCode.user_id
            == user.id,

            PasswordResetCode.used_at
            .is_(None),
        )
        .update(
            {
                PasswordResetCode.used_at:
                    now
            },
            synchronize_session=False,
        )
    )

    code = (
        generate_reset_code()
    )

    reset_request = (
        PasswordResetCode(
            user_id=user.id,

            code_hash=(
                hash_reset_code(
                    user_id=str(
                        user.id
                    ),
                    code=code,
                )
            ),

            attempts=0,

            expires_at=(
                now
                + timedelta(
                    minutes=(
                        PASSWORD_RESET_EXPIRE_MINUTES
                    )
                )
            ),
        )
    )

    db.add(
        reset_request
    )

    db.commit()

    try:

        send_password_reset_code_email(
            to_email=user.email,
            code=code,
            language=payload.language,
        )

    except Exception:

        logger.exception(
            "Échec de l'envoi du code "
            "de réinitialisation."
        )

    return AuthMessage(
        message=(
            GENERIC_FORGOT_MESSAGE
        )
    )


# ============================================================
# VÉRIFIER LE CODE DE RÉINITIALISATION
# ============================================================

@router.post(
    "/verify-reset-code",
    response_model=(
        VerifyResetCodeResponse
    ),
)
def verify_reset_code(
    payload: VerifyResetCodeRequest,

    db: Session = Depends(
        get_db
    ),
) -> VerifyResetCodeResponse:

    user = (
        db.query(User)
        .filter(
            func.lower(
                User.email
            )
            ==
            payload.email.lower()
        )
        .first()
    )

    if (
        user is None
        or not user.is_active
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                INVALID_RESET_CODE_MESSAGE
            ),
        )

    reset_request = (
        db.query(
            PasswordResetCode
        )
        .filter(
            PasswordResetCode.user_id
            == user.id,

            PasswordResetCode.used_at
            .is_(None),
        )
        .order_by(
            PasswordResetCode
            .created_at
            .desc()
        )
        .first()
    )

    now = datetime.now(
        timezone.utc
    )

    if (
        reset_request is None
        or reset_request.expires_at
        <= now
        or reset_request.attempts
        >= RESET_MAX_ATTEMPTS
    ):

        if (
            reset_request is not None
            and reset_request.used_at
            is None
        ):

            reset_request.used_at = (
                now
            )

            db.commit()

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                INVALID_RESET_CODE_MESSAGE
            ),
        )

    code_is_valid = (
        reset_code_matches(
            user_id=str(
                user.id
            ),
            code=payload.code,
            expected_hash=(
                reset_request.code_hash
            ),
        )
    )

    if not code_is_valid:

        reset_request.attempts += 1

        if (
            reset_request.attempts
            >= RESET_MAX_ATTEMPTS
        ):

            reset_request.used_at = (
                now
            )

        db.commit()

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                INVALID_RESET_CODE_MESSAGE
            ),
        )

    reset_request.used_at = (
        now
    )

    db.commit()

    reset_token = (
        create_verified_reset_token(
            user_id=str(
                user.id
            ),
            password_hash=(
                user.password_hash
            ),
        )
    )

    return VerifyResetCodeResponse(
        reset_token=reset_token
    )


# ============================================================
# RÉINITIALISER LE MOT DE PASSE
# ============================================================

@router.post(
    "/reset-password",
    response_model=AuthMessage,
)
def reset_password(
    payload: ResetPasswordRequest,
    response: Response,

    db: Session = Depends(
        get_db
    ),
) -> AuthMessage:

    try:

        token_payload = (
            decode_verified_reset_token(
                payload.reset_token
            )
        )

        user_id_raw = (
            token_payload.get(
                "sub"
            )
        )

        if not user_id_raw:
            raise jwt.InvalidTokenError()

        user_id = uuid.UUID(
            user_id_raw
        )

    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                INVALID_RESET_MESSAGE
            ),
        )

    user = db.get(
        User,
        user_id,
    )

    if (
        user is None
        or not user.is_active
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                INVALID_RESET_MESSAGE
            ),
        )

    expected_fingerprint = (
        password_hash_fingerprint(
            user.password_hash
        )
    )

    if (
        token_payload.get(
            "pwd"
        )
        != expected_fingerprint
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                INVALID_RESET_MESSAGE
            ),
        )

    if verify_password(
        payload.new_password,
        user.password_hash,
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Le nouveau mot de passe "
                "doit être différent "
                "de l'ancien."
            ),
        )

    user.password_hash = (
        hash_password(
            payload.new_password
        )
    )

    db.commit()

    # Fermer une éventuelle session
    # présente dans le navigateur.
    response.delete_cookie(
        ACCESS_TOKEN_COOKIE_NAME,
        path="/",
    )

    response.delete_cookie(
        CSRF_COOKIE_NAME,
        path="/",
    )

    return AuthMessage(
        message=(
            "Mot de passe réinitialisé "
            "avec succès."
        )
    )