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


function VerifyResetCode() {
  const {
    language,
  } = useLanguage();

  const navigate =
    useNavigate();

  const isArabic =
    language === "ar";

  const email =
    sessionStorage.getItem(
      "emc_reset_email"
    )
    || "";

  const [code, setCode] =
    useState("");

  const [status, setStatus] =
    useState("idle");

  const [error, setError] =
    useState("");

  const handleCodeChange =
    (event) => {
      const digits =
        event.target.value
          .replace(/\D/g, "")
          .slice(0, 6);

      setCode(digits);
    };

  const handleSubmit =
    async (event) => {
      event.preventDefault();

      if (
        !email
        || code.length !== 6
        || status === "loading"
      ) {
        return;
      }

      setStatus("loading");
      setError("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/auth/verify-reset-code`,
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
                  email,
                  code,
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
                    ? "الرمز غير صالح أو منتهي الصلاحية."
                    : "Le code est invalide ou expiré."
                )
          );
        }

        if (!data?.reset_token) {
          throw new Error(
            isArabic
              ? "تعذر التحقق من الرمز."
              : "Impossible de vérifier le code."
          );
        }

        sessionStorage.setItem(
          "emc_reset_token",
          data.reset_token
        );

        navigate(
          "/reset-password",
          {
            replace: true,
          }
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
      recoveryStep={2}
      eyebrow={
        isArabic
          ? "التحقق من الهوية"
          : "Vérification"
      }
      title={
        isArabic
          ? "أدخل رمز التحقق"
          : "Entrez le code"
      }
      intro={
        isArabic
          ? "أدخل الرمز المكوّن من 6 أرقام الذي أرسلناه إلى بريدك الإلكتروني."
          : "Saisissez le code à 6 chiffres envoyé à votre adresse e-mail."
      }
      leftTitle={
        isArabic
          ? "خطوة واحدة إضافية للتحقق من طلبك."
          : "Une étape supplémentaire pour vérifier votre demande."
      }
      leftText={
        isArabic
          ? "يساعد رمز التحقق على التأكد من أن طلب تغيير كلمة المرور مرتبط بالبريد الإلكتروني الصحيح."
          : "Le code de vérification permet de confirmer que la demande de changement est bien liée à la bonne adresse e-mail."
      }
      footer={
        <p className="emc-auth-footer">
          <Link to="/forgot-password">
            {isArabic
              ? "إرسال رمز جديد"
              : "Renvoyer un nouveau code"}
          </Link>
        </p>
      }
    >
      {!email && (
        <div className="emc-auth-error">
          {isArabic
            ? "يجب أولاً طلب رمز جديد."
            : "Vous devez d'abord demander un nouveau code."}
        </div>
      )}

      {email && (
        <span className="emc-auth-email-pill">
          {email}
        </span>
      )}

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
              ? "رمز التحقق"
              : "Code de vérification"}
          </span>

          <div className="emc-auth-input">
            <ShellIcon
              name="key"
              size={18}
            />

            <input
              className="emc-auth-code-input"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={code}
              onChange={
                handleCodeChange
              }
              maxLength={6}
              placeholder="------"
              autoFocus
              required
              disabled={
                !email
              }
            />
          </div>
        </label>

        <button
          type="submit"
          className="emc-auth-primary"
          disabled={
            !email
            || code.length !== 6
            || status === "loading"
          }
        >
          {status === "loading" && (
            <span className="emc-auth-spinner" />
          )}

          {status === "loading"
            ? (
                isArabic
                  ? "جارٍ التحقق..."
                  : "Vérification..."
              )
            : (
                isArabic
                  ? "تحقق من الرمز"
                  : "Vérifier le code"
              )}
        </button>
      </form>
    </AuthCreativeShell>
  );
}


export default VerifyResetCode;