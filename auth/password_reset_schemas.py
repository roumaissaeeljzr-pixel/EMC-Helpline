"""
auth/password_reset_schemas.py

Schémas Pydantic pour la récupération
du mot de passe par code à 6 chiffres.
"""

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


# ============================================================
# FORGOT PASSWORD
# ============================================================

class ForgotPasswordRequest(
    BaseModel
):

    model_config = ConfigDict(
        extra="forbid"
    )

    email: EmailStr

    language: Literal[
        "fr",
        "ar",
    ] = "fr"


# ============================================================
# VERIFY CODE
# ============================================================

class VerifyResetCodeRequest(
    BaseModel
):

    model_config = ConfigDict(
        extra="forbid"
    )

    email: EmailStr

    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
    )

    @field_validator(
        "code"
    )
    @classmethod
    def validate_code(
        cls,
        value: str,
    ) -> str:

        clean_code = (
            value.strip()
        )

        if (
            len(clean_code) != 6
            or not clean_code.isdigit()
        ):
            raise ValueError(
                "Le code doit contenir "
                "exactement 6 chiffres."
            )

        return clean_code


class VerifyResetCodeResponse(
    BaseModel
):

    reset_token: str


# ============================================================
# RESET PASSWORD
# ============================================================

class ResetPasswordRequest(
    BaseModel
):

    model_config = ConfigDict(
        extra="forbid"
    )

    reset_token: str = Field(
        ...,
        min_length=20,
    )

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


# ============================================================
# MESSAGE
# ============================================================

class AuthMessage(
    BaseModel
):

    message: str