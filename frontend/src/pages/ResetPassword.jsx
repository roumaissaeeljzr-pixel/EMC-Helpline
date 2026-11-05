import {
  useMemo,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  useLanguage,
} from "../context/LanguageContext.jsx";

import AuthCreativeShell, {
  ShellIcon,
} from "../components/auth/AuthCreativeShell.jsx";

import "./AuthCreative.css";


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


function passwordStrength(
  password,
) {
  if (!password) {
    return 0;
  }

  let score = 0;

  if (password.length >= 8) {
    score += 1;
  }

  if (
    /[A-ZÀ-Ý]/.test(password)
    && /[a-zà-ÿ]/.test(password)
  ) {
    score += 1;
  }

  if (/\d/.test(password)) {
    score += 1;
  }

  if (/[^A-Za-zÀ-ÿ0-9]/.test(password)) {
    score += 1;
  }

  return score;
}


function ResetPassword() {
  const {
    language,
  } = useLanguage();

  const isArabic =
    language === "ar";

  const resetToken =
    sessionStorage.getItem(
      "emc_reset_token"
    )
    || "";

  const [
    newPassword,
    setNewPassword,
  ] = useState("");

  const [
    passwordConfirm,
    setPasswordConfirm,
  ] = useState("");

  const [
    showPassword,
    setShowPassword,
  ] = useState(false);

  const [status, setStatus] =
    useState("idle");

  const [error, setError] =
    useState("");

  const missingToken =
    !resetToken;

  const strength =
    useMemo(
      () =>
        passwordStrength(
          newPassword
        ),
      [
        newPassword,
      ]
    );

  const handleSubmit =
    async (event) => {
      event.preventDefault();

      if (
        missingToken
        || status === "loading"
      ) {
        return;
      }

      if (
        newPassword
        !== passwordConfirm
      ) {
        setError(
          isArabic
            ? "كلمتا المرور غير متطابقتين."
            : "Les mots de passe ne correspondent pas."
        );

        return;
      }

      setStatus("loading");
      setError("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/auth/reset-password`,
            {
              method: "POST",
              headers: {
                "Content-Type":
                  "application/json",
                Accept:
                  "application/json",
              },
              body:
                JSON.stringify({
                  reset_token:
                    resetToken,
                  new_password:
                    newPassword,
                }),
            }
          );

        const data =
          await response
            .json()
            .catch(
              () => null
            );

        if (!response.ok) {
          throw new Error(
            typeof data?.detail
              === "string"
              ? data.detail
              : (
                  isArabic
                    ? "تعذر تغيير كلمة المرور."
                    : "Impossible de réinitialiser le mot de passe."
                )
          );
        }

        sessionStorage.removeItem(
          "emc_reset_token"
        );

        sessionStorage.removeItem(
          "emc_reset_email"
        );

        setStatus("success");
      } catch (err) {
        setError(
          err.message
        );

        setStatus("error");
      }
    };

  return (
    <AuthCreativeShell
      recoveryStep={3}
      eyebrow={
        isArabic
          ? "تأمين الحساب"
          : "Sécurisation du compte"
      }
      title={
        isArabic
          ? "كلمة مرور جديدة"
          : "Nouveau mot de passe"
      }
      intro={
        isArabic
          ? "اختر كلمة مرور جديدة لا تقل عن 8 أحرف."
          : "Choisissez un nouveau mot de passe d'au moins 8 caractères."
      }
      leftTitle={
        isArabic
          ? "أنهِ عملية الاستعادة بكلمة مرور جديدة."
          : "Finalisez la récupération avec un nouveau mot de passe."
      }
      leftText={
        isArabic
          ? "بعد حفظ كلمة المرور الجديدة، يمكنك العودة مباشرة إلى صفحة تسجيل الدخول."
          : "Une fois le nouveau mot de passe enregistré, vous pourrez retourner directement à la page de connexion."
      }
      footer={
        <p className="emc-auth-footer">
          <Link
            to={
              missingToken
                ? "/forgot-password"
                : "/login"
            }
          >
            {missingToken
              ? (
                  isArabic
                    ? "طلب رمز جديد"
                    : "Demander un nouveau code"
                )
              : (
                  isArabic
                    ? "تسجيل الدخول"
                    : "Se connecter"
                )}
          </Link>
        </p>
      }
    >
      {missingToken && (
        <div className="emc-auth-error">
          {isArabic
            ? "يجب أولاً التحقق من الرمز الذي تلقيته عبر البريد الإلكتروني."
            : "Vous devez d'abord vérifier le code reçu par e-mail."}
        </div>
      )}

      {status === "success" ? (
        <div className="emc-auth-success">
          {isArabic
            ? "تم تغيير كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول."
            : "Votre mot de passe a été modifié avec succès. Vous pouvez maintenant vous connecter."}
        </div>
      ) : (
        <>
          {error && (
            <div
              className="emc-auth-error"
              role="alert"
            >
              {error}
            </div>
          )}

          <form
            className="emc-auth-form"
            onSubmit={
              handleSubmit
            }
          >
            <label className="emc-auth-field">
              <span>
                {isArabic
                  ? "كلمة المرور الجديدة"
                  : "Nouveau mot de passe"}
              </span>

              <div className="emc-auth-input">
                <ShellIcon
                  name="lock"
                  size={18}
                />

                <input
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  value={
                    newPassword
                  }
                  onChange={
                    (event) =>
                      setNewPassword(
                        event.target.value
                      )
                  }
                  minLength={8}
                  maxLength={128}
                  autoComplete="new-password"
                  required
                  disabled={
                    missingToken
                  }
                />

                <button
                  type="button"
                  className="emc-auth-eye"
                  onClick={() =>
                    setShowPassword(
                      (current) =>
                        !current
                    )
                  }
                >
                  {showPassword
                    ? "◉"
                    : "○"}
                </button>
              </div>

              <div
                className={
                  `emc-auth-strength level-${strength}`
                }
              >
                <div className="emc-auth-strength-bars">
                  <span />
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </label>

            <label className="emc-auth-field">
              <span>
                {isArabic
                  ? "تأكيد كلمة المرور"
                  : "Confirmer le mot de passe"}
              </span>

              <div className="emc-auth-input">
                <ShellIcon
                  name="check"
                  size={18}
                />

                <input
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  value={
                    passwordConfirm
                  }
                  onChange={
                    (event) =>
                      setPasswordConfirm(
                        event.target.value
                      )
                  }
                  minLength={8}
                  maxLength={128}
                  autoComplete="new-password"
                  required
                  disabled={
                    missingToken
                  }
                />
              </div>
            </label>

            <button
              type="submit"
              className="emc-auth-primary"
              disabled={
                missingToken
                || status === "loading"
              }
            >
              {status === "loading" && (
                <span className="emc-auth-spinner" />
              )}

              {status === "loading"
                ? (
                    isArabic
                      ? "جارٍ الحفظ..."
                      : "Enregistrement..."
                  )
                : (
                    isArabic
                      ? "تغيير كلمة المرور"
                      : "Changer le mot de passe"
                  )}
            </button>
          </form>
        </>
      )}
    </AuthCreativeShell>
  );
}


export default ResetPassword;