import {
  useState,
} from "react";

import {
  Link,
  useNavigate,
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


function ForgotPassword() {
  const {
    language,
  } = useLanguage();

  const navigate =
    useNavigate();

  const isArabic =
    language === "ar";

  const [email, setEmail] =
    useState("");

  const [status, setStatus] =
    useState("idle");

  const [error, setError] =
    useState("");

  const handleSubmit =
    async (event) => {
      event.preventDefault();

      const cleanEmail =
        email.trim();

      if (
        !cleanEmail
        || status === "loading"
      ) {
        return;
      }

      setStatus("loading");
      setError("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/auth/forgot-password`,
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
                  email:
                    cleanEmail,
                  language:
                    isArabic
                      ? "ar"
                      : "fr",
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
                    ? "تعذر إرسال الرمز."
                    : "Impossible d'envoyer le code."
                )
          );
        }

        sessionStorage.setItem(
          "emc_reset_email",
          cleanEmail
        );

        navigate(
          "/verify-reset-code"
        );
      } catch (err) {
        setError(
          err.message
        );

        setStatus("error");
        return;
      }

      setStatus("success");
    };

  return (
    <AuthCreativeShell
      recoveryStep={1}
      eyebrow={
        isArabic
          ? "استعادة الوصول"
          : "Récupération du compte"
      }
      title={
        isArabic
          ? "نسيت كلمة المرور؟"
          : "Mot de passe oublié ?"
      }
      intro={
        isArabic
          ? "أدخل بريدك الإلكتروني. ستتلقى رمز تحقق مكوّنًا من 6 أرقام."
          : "Saisissez votre adresse e-mail. Vous recevrez un code de vérification à 6 chiffres."
      }
      leftTitle={
        isArabic
          ? "استعد الوصول إلى حسابك بطريقة بسيطة وآمنة."
          : "Récupérez l’accès à votre compte simplement et en toute sécurité."
      }
      leftText={
        isArabic
          ? "تمر العملية بثلاث مراحل: البريد الإلكتروني، التحقق من الرمز، ثم اختيار كلمة مرور جديدة."
          : "La récupération suit trois étapes : e-mail, vérification du code, puis création d’un nouveau mot de passe."
      }
      footer={
        <p className="emc-auth-footer">
          <Link to="/login">
            {isArabic
              ? "العودة إلى تسجيل الدخول"
              : "Retour à la connexion"}
          </Link>
        </p>
      }
    >
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
              ? "البريد الإلكتروني"
              : "Adresse e-mail"}
          </span>

          <div className="emc-auth-input">
            <ShellIcon
              name="mail"
              size={18}
            />

            <input
              type="email"
              value={
                email
              }
              onChange={
                (event) =>
                  setEmail(
                    event.target.value
                  )
              }
              autoComplete="email"
              required
            />
          </div>
        </label>

        <button
          type="submit"
          className="emc-auth-primary"
          disabled={
            status === "loading"
          }
        >
          {status === "loading" && (
            <span className="emc-auth-spinner" />
          )}

          {status === "loading"
            ? (
                isArabic
                  ? "جارٍ الإرسال..."
                  : "Envoi..."
              )
            : (
                isArabic
                  ? "إرسال الرمز"
                  : "Envoyer le code"
              )}
        </button>

        <div className="emc-auth-note">
          {isArabic
            ? "يُستخدم رمز التحقق فقط لإتمام طلب إعادة تعيين كلمة المرور."
            : "Le code de vérification sert uniquement à finaliser votre demande de réinitialisation."}
        </div>
      </form>
    </AuthCreativeShell>
  );
}


export default ForgotPassword;