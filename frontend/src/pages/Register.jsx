import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Link,
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


function getHomeForRole(role) {
  return role === "admin"
    ? "/admin/dashboard"
    : "/victim/dashboard";
}


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


function Register() {
  const {
    language,
  } = useLanguage();

  const {
    user,
    loading,
    register,
  } = useAuth();

  const navigate =
    useNavigate();

  const isArabic =
    language === "ar";

  const [username, setUsername] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

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

  const strength =
    useMemo(
      () =>
        passwordStrength(
          password
        ),
      [
        password,
      ]
    );

  useEffect(() => {
    if (!loading && user) {
      navigate(
        getHomeForRole(
          user.role
        ),
        {
          replace: true,
        }
      );
    }
  }, [
    loading,
    user,
    navigate,
  ]);

  const handleSubmit =
    async (event) => {
      event.preventDefault();

      if (
        !username.trim()
        || !email.trim()
        || !password
        || status === "loading"
      ) {
        return;
      }

      if (
        password
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
        await register({
          username:
            username.trim(),

          email:
            email
              .trim()
              .toLowerCase(),

          password,

          language,
        });

        navigate(
          "/verify-email",
          {
            replace: true,

            state: {
              email:
                email
                  .trim()
                  .toLowerCase(),

              registration:
                true,
            },
          }
        );
      } catch (err) {
        setError(
          err.message
          || (
            isArabic
              ? "تعذر إنشاء الحساب."
              : "Impossible de créer le compte."
          )
        );

        setStatus("error");
        return;
      }

      setStatus("success");
    };

  return (
    <AuthCreativeShell
      eyebrow={
        isArabic
          ? "إنشاء مساحة شخصية"
          : "Création de l’espace victime"
      }
      title={
        isArabic
          ? "إنشاء حساب"
          : "Créer votre compte"
      }
      intro={
        isArabic
          ? "أنشئ حسابًا للوصول إلى التقييم وخطة العمل والأدلة والموارد داخل مساحة آمنة."
          : "Créez un compte pour accéder à l’évaluation, au plan d’action, aux preuves et aux ressources dans un espace sécurisé."
      }
      leftTitle={
        isArabic
          ? "ابدأ مساحتك الشخصية الآمنة في دقائق."
          : "Commencez votre espace personnel sécurisé en quelques minutes."
      }
      leftText={
        isArabic
          ? "بعد إنشاء الحساب، يمكنك تقييم وضعك والحصول على خطة عمل وحفظ الأدلة ومتابعة ملفك."
          : "Après votre inscription, vous pourrez évaluer votre situation, obtenir un plan d’action, conserver vos preuves et suivre votre dossier."
      }
      footer={
        <p className="emc-auth-footer">
          {isArabic
            ? "لديك حساب بالفعل؟"
            : "Vous avez déjà un compte ?"}{" "}

          <Link to="/login">
            {isArabic
              ? "تسجيل الدخول"
              : "Se connecter"}
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
              ? "اسم المستخدم"
              : "Nom d'utilisateur"}
          </span>

          <div className="emc-auth-input">
            <ShellIcon
              name="user"
              size={18}
            />

            <input
              type="text"
              value={
                username
              }
              onChange={
                (event) =>
                  setUsername(
                    event.target.value
                  )
              }
              autoComplete="username"
              required
            />
          </div>
        </label>

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

        <label className="emc-auth-field">
          <span>
            {isArabic
              ? "كلمة المرور"
              : "Mot de passe"}
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
                password
              }
              onChange={
                (event) =>
                  setPassword(
                    event.target.value
                  )
              }
              minLength={8}
              maxLength={128}
              autoComplete="new-password"
              required
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
                ? "جارٍ إنشاء الحساب..."
                : "Création..."
            )
            : (
              isArabic
                ? "إنشاء الحساب"
                : "Créer mon compte"
            )}
        </button>

        <div className="emc-auth-note">
          {isArabic
            ? "التسجيل العمومي ينشئ حساب ضحية فقط."
            : "L’inscription publique crée uniquement un compte victime."}
        </div>
      </form>
    </AuthCreativeShell>
  );
}


export default Register;