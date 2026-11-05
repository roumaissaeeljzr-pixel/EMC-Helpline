import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../context/AuthContext.jsx";

import {
  useLanguage,
} from "../context/LanguageContext.jsx";

import AuthCreativeShell, {
  ShellIcon,
} from "../components/auth/AuthCreativeShell.jsx";

import "./AuthCreative.css";


const CODE_LENGTH = 6;

const RESEND_SECONDS = 60;


function VerifyEmail() {
  const {
    language,
  } = useLanguage();

  const {
    verifyEmail,
    resendVerificationCode,
  } = useAuth();

  const location =
    useLocation();

  const navigate =
    useNavigate();

  const isArabic =
    language === "ar";

  const registrationEmail =
    location.state?.email || "";

  const cameFromRegistration =
    Boolean(
      location.state?.registration
    );

  const [
    email,
    setEmail,
  ] = useState(
    registrationEmail
  );

  const [
    code,
    setCode,
  ] = useState(
    Array(CODE_LENGTH).fill("")
  );

  const [
    status,
    setStatus,
  ] = useState("idle");

  const [
    error,
    setError,
  ] = useState("");

  const [
    message,
    setMessage,
  ] = useState(
    cameFromRegistration
      ? (
          isArabic
            ? (
                "أرسلنا رمزًا مكونًا "
                + "من 6 أرقام إلى بريدك الإلكتروني."
              )
            : (
                "Un code à 6 chiffres "
                + "a été envoyé à votre adresse e-mail."
              )
        )
      : ""
  );

  const [
    resendRemaining,
    setResendRemaining,
  ] = useState(
    cameFromRegistration
      ? RESEND_SECONDS
      : 0
  );

  const inputRefs =
    useRef([]);


  // ==========================================================
  // COMPTE À REBOURS
  // ==========================================================

  useEffect(() => {
    if (
      resendRemaining <= 0
    ) {
      return undefined;
    }

    const timer =
      window.setInterval(
        () => {
          setResendRemaining(
            (current) =>
              Math.max(
                0,
                current - 1
              )
          );
        },
        1000
      );

    return () => {
      window.clearInterval(
        timer
      );
    };
  }, [
    resendRemaining,
  ]);


  // ==========================================================
  // MODIFICATION D'UNE CASE
  // ==========================================================

  const handleCodeChange = (
    index,
    value,
  ) => {
    const digit =
      value.replace(
        /\D/g,
        ""
      )
      .slice(-1);

    const nextCode = [
      ...code,
    ];

    nextCode[index] =
      digit;

    setCode(
      nextCode
    );

    setError("");

    if (
      digit
      && index < CODE_LENGTH - 1
    ) {
      inputRefs.current[
        index + 1
      ]?.focus();
    }
  };


  // ==========================================================
  // TOUCHE RETOUR
  // ==========================================================

  const handleCodeKeyDown = (
    index,
    event,
  ) => {
    if (
      event.key === "Backspace"
      && !code[index]
      && index > 0
    ) {
      inputRefs.current[
        index - 1
      ]?.focus();
    }

    if (
      event.key === "ArrowLeft"
      && index > 0
    ) {
      inputRefs.current[
        index - 1
      ]?.focus();
    }

    if (
      event.key === "ArrowRight"
      && index < CODE_LENGTH - 1
    ) {
      inputRefs.current[
        index + 1
      ]?.focus();
    }
  };


  // ==========================================================
  // COLLER LE CODE COMPLET
  // ==========================================================

  const handlePaste = (
    event,
  ) => {
    event.preventDefault();

    const pastedCode =
      event.clipboardData
        .getData("text")
        .replace(/\D/g, "")
        .slice(
          0,
          CODE_LENGTH
        );

    if (!pastedCode) {
      return;
    }

    const nextCode =
      Array(CODE_LENGTH)
        .fill("");

    pastedCode
      .split("")
      .forEach(
        (digit, index) => {
          nextCode[index] =
            digit;
        }
      );

    setCode(
      nextCode
    );

    const focusIndex =
      Math.min(
        pastedCode.length,
        CODE_LENGTH
      ) - 1;

    inputRefs.current[
      focusIndex
    ]?.focus();
  };


  // ==========================================================
  // VÉRIFICATION
  // ==========================================================

  const handleSubmit =
    async (event) => {
      event.preventDefault();

      const cleanEmail =
        email
          .trim()
          .toLowerCase();

      const completeCode =
        code.join("");

      if (!cleanEmail) {
        setError(
          isArabic
            ? "أدخل بريدك الإلكتروني."
            : "Saisissez votre adresse e-mail."
        );

        return;
      }

      if (
        completeCode.length
        !== CODE_LENGTH
      ) {
        setError(
          isArabic
            ? "أدخل الرمز المكون من 6 أرقام."
            : "Saisissez le code complet à 6 chiffres."
        );

        return;
      }

      if (
        status === "loading"
      ) {
        return;
      }

      setStatus(
        "loading"
      );

      setError("");
      setMessage("");

      try {
        await verifyEmail({
          email:
            cleanEmail,

          code:
            completeCode,
        });

        setStatus(
          "success"
        );

        setMessage(
          isArabic
            ? (
                "تم تأكيد بريدك الإلكتروني بنجاح."
              )
            : (
                "Votre adresse e-mail "
                + "a été vérifiée avec succès."
              )
        );

        window.setTimeout(
          () => {
            navigate(
              "/login",
              {
                replace: true,

                state: {
                  emailVerified:
                    true,
                },
              }
            );
          },
          1200
        );
      } catch (err) {
        setStatus(
          "error"
        );

        setError(
          err.message
          || (
            isArabic
              ? "الرمز غير صحيح أو منتهي الصلاحية."
              : "Le code est invalide ou expiré."
          )
        );
      }
    };


  // ==========================================================
  // RENVOYER LE CODE
  // ==========================================================

  const handleResend =
    async () => {

      const cleanEmail =
        email
          .trim()
          .toLowerCase();

      if (!cleanEmail) {
        setError(
          isArabic
            ? "أدخل بريدك الإلكتروني أولاً."
            : "Saisissez d’abord votre adresse e-mail."
        );

        return;
      }

      if (
        resendRemaining > 0
        || status === "resending"
      ) {
        return;
      }

      setStatus(
        "resending"
      );

      setError("");
      setMessage("");

      try {
        await resendVerificationCode({
          email:
            cleanEmail,

          language,
        });

        setCode(
          Array(
            CODE_LENGTH
          ).fill("")
        );

        setResendRemaining(
          RESEND_SECONDS
        );

        setStatus(
          "idle"
        );

        setMessage(
          isArabic
            ? (
                "إذا كان الحساب موجودًا "
                + "وغير مؤكد، فقد تم إرسال رمز جديد."
              )
            : (
                "Si le compte existe et n’est "
                + "pas encore vérifié, "
                + "un nouveau code a été envoyé."
              )
        );

        window.setTimeout(
          () => {
            inputRefs.current[
              0
            ]?.focus();
          },
          0
        );
      } catch (err) {
        setStatus(
          "error"
        );

        setError(
          err.message
          || (
            isArabic
              ? "تعذر إعادة إرسال الرمز."
              : "Impossible de renvoyer le code."
          )
        );
      }
    };


  return (
    <AuthCreativeShell
      eyebrow={
        isArabic
          ? "تأكيد البريد الإلكتروني"
          : "Vérification de sécurité"
      }

      title={
        isArabic
          ? "تحقق من بريدك الإلكتروني"
          : "Vérifiez votre e-mail"
      }

      intro={
        isArabic
          ? (
              "أدخل الرمز المكون من ستة أرقام "
              + "الذي أرسلناه إلى بريدك الإلكتروني."
            )
          : (
              "Saisissez le code à six chiffres "
              + "envoyé à votre adresse e-mail."
            )
      }

      leftTitle={
        isArabic
          ? (
              "خطوة أخيرة لحماية "
              + "مساحتك الشخصية."
            )
          : (
              "Une dernière étape pour "
              + "protéger votre espace."
            )
      }

      leftText={
        isArabic
          ? (
              "يؤكد هذا الرمز أن عنوان البريد "
              + "الإلكتروني يخصك قبل السماح "
              + "بالوصول إلى حسابك."
            )
          : (
              "Ce code confirme que l’adresse "
              + "e-mail vous appartient avant "
              + "d’autoriser l’accès au compte."
            )
      }

      footer={
        <p
          className=
            "emc-auth-footer"
        >
          {isArabic
            ? "العودة إلى"
            : "Retour à la"}{" "}

          <Link to="/login">
            {isArabic
              ? "صفحة تسجيل الدخول"
              : "connexion"}
          </Link>
        </p>
      }
    >
      {error && (
        <div
          className=
            "emc-auth-error"

          role="alert"
        >
          {error}
        </div>
      )}

      {message && (
        <div
          className={
            status === "success"
              ? "emc-auth-success"
              : "emc-auth-information"
          }

          role="status"
        >
          {message}
        </div>
      )}

      <form
        className=
          "emc-auth-form"

        onSubmit={
          handleSubmit
        }
      >
        <label
          className=
            "emc-auth-field"
        >
          <span>
            {isArabic
              ? "البريد الإلكتروني"
              : "Adresse e-mail"}
          </span>

          <div
            className=
              "emc-auth-input"
          >
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

              placeholder={
                isArabic
                  ? "name@example.com"
                  : "nom@exemple.com"
              }

              required
            />
          </div>
        </label>

        <fieldset
          className=
            "emc-code-fieldset"
        >
          <legend>
            {isArabic
              ? "رمز التحقق"
              : "Code de vérification"}
          </legend>

          <div
            className=
              "emc-code-inputs"

            dir="ltr"

            onPaste={
              handlePaste
            }
          >
            {code.map(
              (
                digit,
                index
              ) => (
                <input
                  key={index}

                  ref={
                    (element) => {
                      inputRefs.current[
                        index
                      ] = element;
                    }
                  }

                  className=
                    "emc-code-input"

                  type="text"

                  inputMode=
                    "numeric"

                  pattern="[0-9]*"

                  maxLength={1}

                  value={
                    digit
                  }

                  aria-label={
                    isArabic
                      ? (
                          `الرقم ${index + 1}`
                        )
                      : (
                          `Chiffre ${index + 1}`
                        )
                  }

                  onChange={
                    (event) =>
                      handleCodeChange(
                        index,
                        event.target.value
                      )
                  }

                  onKeyDown={
                    (event) =>
                      handleCodeKeyDown(
                        index,
                        event
                      )
                  }

                  autoFocus={
                    index === 0
                  }
                />
              )
            )}
          </div>
        </fieldset>

        <button
          type="submit"

          className=
            "emc-auth-primary"

          disabled={
            status === "loading"
            || status === "success"
          }
        >
          {status === "loading" && (
            <span
              className=
                "emc-auth-spinner"
            />
          )}

          {status === "loading"
            ? (
                isArabic
                  ? "جارٍ التحقق..."
                  : "Vérification..."
              )
            : (
                isArabic
                  ? "تأكيد بريدي الإلكتروني"
                  : "Confirmer mon e-mail"
              )}
        </button>

        <div
          className=
            "emc-verification-resend"
        >
          <span>
            {isArabic
              ? "لم تستلم الرمز؟"
              : "Vous n’avez pas reçu le code ?"}
          </span>

          <button
            type="button"

            className=
              "emc-auth-text-button"

            onClick={
              handleResend
            }

            disabled={
              resendRemaining > 0
              || status === "resending"
            }
          >
            {status === "resending"
              ? (
                  isArabic
                    ? "جارٍ الإرسال..."
                    : "Envoi..."
                )
              : (
                  resendRemaining > 0
                    ? (
                        isArabic
                          ? (
                              `إعادة الإرسال خلال ${resendRemaining} ثانية`
                            )
                          : (
                              `Renvoyer dans ${resendRemaining} s`
                            )
                      )
                    : (
                        isArabic
                          ? "إعادة إرسال الرمز"
                          : "Renvoyer le code"
                      )
                )}
          </button>
        </div>

        <div
          className=
            "emc-auth-note"
        >
          {isArabic
            ? (
                "الرمز صالح لمدة 10 دقائق "
                + "ويمكن استخدامه مرة واحدة فقط."
              )
            : (
                "Le code est valable pendant "
                + "10 minutes et ne peut être "
                + "utilisé qu’une seule fois."
              )}
        </div>
      </form>
    </AuthCreativeShell>
  );
}


export default VerifyEmail;