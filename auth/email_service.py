"""
auth/email_service.py

Envoi des codes de vérification EMC Helpline :

- vérification de l'adresse e-mail ;
- réinitialisation du mot de passe.
"""

import logging
import smtplib

from email.message import (
    EmailMessage,
)

from auth.config import (
    EMAIL_VERIFICATION_EXPIRE_MINUTES,
    IS_PRODUCTION,
    PASSWORD_RESET_EXPIRE_MINUTES,
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_USE_TLS,
)


logger = logging.getLogger(
    __name__
)


# ============================================================
# CONNEXION ET ENVOI SMTP
# ============================================================

def _send_message(
    message: EmailMessage,
) -> None:
    """
    Ouvre la connexion SMTP et envoie
    le message préparé.
    """

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
        timeout=15,
    ) as server:

        if SMTP_USE_TLS:
            server.starttls()

        if (
            SMTP_USERNAME
            and SMTP_PASSWORD
        ):
            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD,
            )

        server.send_message(
            message
        )


# ============================================================
# VÉRIFICATION DE L'ADRESSE E-MAIL
# ============================================================

def send_email_verification_code(
    *,
    to_email: str,
    code: str,
    language: str = "fr",
) -> None:
    """
    Envoie le code OTP permettant
    de confirmer une nouvelle inscription.
    """

    # ========================================================
    # DÉVELOPPEMENT SANS SMTP
    # ========================================================

    if (
        not SMTP_HOST
        or not SMTP_FROM_EMAIL
    ):

        if IS_PRODUCTION:
            raise RuntimeError(
                "Le service SMTP "
                "n'est pas configuré."
            )

        print()
        print(
            "[DEV][EMC HELPLINE]"
        )

        print(
            "Code de vérification "
            f"pour {to_email}: {code}"
        )

        print()

        return

    # ========================================================
    # CRÉATION DU MESSAGE
    # ========================================================

    message = EmailMessage()

    message["From"] = (
        SMTP_FROM_EMAIL
    )

    message["To"] = (
        to_email
    )

    # ========================================================
    # VERSION ARABE
    # ========================================================

    if language == "ar":

        message["Subject"] = (
            "EMC Helpline - "
            "تأكيد البريد الإلكتروني"
        )

        message.set_content(
            f"""
EMC Helpline

رمز تأكيد بريدك الإلكتروني هو:

        {code}

هذا الرمز صالح لمدة
{EMAIL_VERIFICATION_EXPIRE_MINUTES} دقائق.

لا تشارك هذا الرمز مع أي شخص.

إذا لم تقم بإنشاء هذا الحساب،
فتجاهل هذه الرسالة.

EMC Helpline
"""
        )

    # ========================================================
    # VERSION FRANÇAISE
    # ========================================================

    else:

        message["Subject"] = (
            "EMC Helpline - "
            "Confirmez votre adresse e-mail"
        )

        message.set_content(
            f"""
EMC Helpline

Votre code de vérification est :

        {code}

Ce code est valable pendant
{EMAIL_VERIFICATION_EXPIRE_MINUTES} minutes.

Ne communiquez ce code à personne.

Si vous n'avez pas créé ce compte,
ignorez simplement ce message.

EMC Helpline
"""
        )

    # ========================================================
    # ENVOI
    # ========================================================

    _send_message(
        message
    )

    logger.info(
        "Code de vérification "
        "de l'adresse e-mail envoyé."
    )


# ============================================================
# RÉINITIALISATION DU MOT DE PASSE
# ============================================================

def send_password_reset_code_email(
    *,
    to_email: str,
    code: str,
    language: str = "fr",
) -> None:
    """
    Envoie le code OTP permettant
    de réinitialiser le mot de passe.
    """

    # ========================================================
    # DÉVELOPPEMENT SANS SMTP
    # ========================================================

    if (
        not SMTP_HOST
        or not SMTP_FROM_EMAIL
    ):

        if IS_PRODUCTION:
            raise RuntimeError(
                "Le service SMTP "
                "n'est pas configuré."
            )

        print()
        print(
            "[DEV][EMC HELPLINE]"
        )

        print(
            "Code de réinitialisation "
            f"pour {to_email}: {code}"
        )

        print()

        return

    # ========================================================
    # CRÉATION DU MESSAGE
    # ========================================================

    message = EmailMessage()

    message["From"] = (
        SMTP_FROM_EMAIL
    )

    message["To"] = (
        to_email
    )

    # ========================================================
    # VERSION ARABE
    # ========================================================

    if language == "ar":

        message["Subject"] = (
            "EMC Helpline - رمز التحقق"
        )

        message.set_content(
            f"""
EMC Helpline

لقد طلبت إعادة تعيين كلمة المرور الخاصة بك.

رمز التحقق الخاص بك هو:

        {code}

هذا الرمز صالح لمدة
{PASSWORD_RESET_EXPIRE_MINUTES} دقيقة.

يمكن استخدام الرمز مرة واحدة فقط.

إذا لم تكن أنت من طلب إعادة تعيين كلمة المرور،
فتجاهل هذه الرسالة.

EMC Helpline
"""
        )

    # ========================================================
    # VERSION FRANÇAISE
    # ========================================================

    else:

        message["Subject"] = (
            "EMC Helpline - "
            "Code de vérification"
        )

        message.set_content(
            f"""
EMC Helpline

Vous avez demandé la réinitialisation
de votre mot de passe.

Votre code de vérification est :

        {code}

Ce code est valable pendant
{PASSWORD_RESET_EXPIRE_MINUTES} minutes.

Le code ne peut être utilisé
qu'une seule fois.

Si vous n'êtes pas à l'origine
de cette demande,
ignorez simplement cet e-mail.

EMC Helpline
"""
        )

    # ========================================================
    # ENVOI
    # ========================================================

    _send_message(
        message
    )

    logger.info(
        "Code de réinitialisation "
        "envoyé par e-mail."
    )