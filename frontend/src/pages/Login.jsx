import {
  useEffect,
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

import "./Login.css";


function getHomeForRole(role) {
  return role === "admin"
    ? "/admin/dashboard"
    : "/victim/dashboard";
}


function Icon({
  name,
  size = 20,
}) {
  const props = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": "true",
  };

  if (name === "user") {
    return (
      <svg {...props}>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c.8-4.2 3.5-6.3 8-6.3s7.2 2.1 8 6.3" />
      </svg>
    );
  }

  if (name === "lock") {
    return (
      <svg {...props}>
        <rect x="5" y="10" width="14" height="10" rx="2" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      </svg>
    );
  }

  if (name === "eye") {
    return (
      <svg {...props}>
        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12z" />
        <circle cx="12" cy="12" r="2.5" />
      </svg>
    );
  }

  if (name === "eye-off") {
    return (
      <svg {...props}>
        <path d="m3 3 18 18" />
        <path d="M10.5 10.5A2.2 2.2 0 0 0 13.5 13.5" />
        <path d="M9.8 4.4A11 11 0 0 1 12 4c6.5 0 10 8 10 8a17 17 0 0 1-2.1 3.2" />
        <path d="M6.4 6.5C3.6 8.4 2 12 2 12s3.5 8 10 8a10 10 0 0 0 4.1-.9" />
      </svg>
    );
  }

  if (name === "shield") {
    return (
      <svg {...props}>
        <path d="M12 3 5 6v5c0 4.7 2.7 8 7 10 4.3-2 7-5.3 7-10V6z" />
        <path d="m9 12 2 2 4-4" />
      </svg>
    );
  }

  if (name === "folder") {
    return (
      <svg {...props}>
        <path d="M3 6h7l2 2h9v10H3z" />
      </svg>
    );
  }

  if (name === "clip") {
    return (
      <svg {...props}>
        <path d="m8.5 12.5 6.2-6.2a3 3 0 0 1 4.2 4.2l-8 8a5 5 0 0 1-7.1-7.1l8.2-8.2" />
      </svg>
    );
  }

  if (name === "check") {
    return (
      <svg {...props}>
        <path d="m5 12 4 4L19 6" />
      </svg>
    );
  }

  if (name === "spark") {
    return (
      <svg {...props}>
        <path d="m12 2 1.2 4.2L17 8l-3.8 1.8L12 14l-1.2-4.2L7 8l3.8-1.8z" />
        <path d="m19 15 .6 2 1.8.9-1.8 1-.6 2.1-.6-2.1-1.8-1 1.8-.9z" />
      </svg>
    );
  }

  return (
    <svg {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v8" />
    </svg>
  );
}


function Login() {
  const {
    language,
    setLanguage,
  } = useLanguage();

  const {
    user,
    loading,
    login,
  } = useAuth();

  const navigate =
    useNavigate();

  const location =
    useLocation();

  const isArabic =
    language === "ar";

  const [
    username,
    setUsername,
  ] = useState("");

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    showPassword,
    setShowPassword,
  ] = useState(false);

  const [
    status,
    setStatus,
  ] = useState("idle");

  const [
    error,
    setError,
  ] = useState("");


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
        || !password
        || status === "loading"
      ) {
        return;
      }

      setStatus("loading");
      setError("");

      try {
        const authenticatedUser =
          await login({
            username:
              username.trim(),
            password,
          });

        navigate(
          getHomeForRole(
            authenticatedUser.role
          ),
          {
            replace: true,
          }
        );
      } catch (err) {
        setError(
          err.message
          || (
            isArabic
              ? "تعذر تسجيل الدخول."
              : "Connexion impossible."
          )
        );

        setStatus("error");
        return;
      }

      setStatus("success");
    };


  const copy =
    isArabic
      ? {
          leftBadge:
            "فضاء شخصي آمن",
          leftTitle:
            "لست بحاجة إلى إدارة وضعك الرقمي بمفردك.",
          leftText:
            "تساعدك EMC Helpline على فهم وضعك وحفظ الأدلة واتباع خطة عمل واضحة داخل مساحة شخصية موثقة.",
          journey:
            "مسارك داخل EMC Helpline",
          step1:
            "تقييم الوضع",
          step2:
            "خطة عمل",
          step3:
            "حفظ الأدلة",
          step4:
            "متابعة الملف",
          privacy:
            "المعلومات الخاصة مرتبطة بحسابك فقط.",
          bilingual:
            "واجهة بالفرنسية والعربية",
          welcome:
            "مرحبًا بعودتك",
          intro:
            "سجّل الدخول للوصول إلى مساحتك الشخصية أو الإدارية حسب صلاحيات حسابك.",
          username:
            "اسم المستخدم",
          usernamePlaceholder:
            "أدخل اسم المستخدم",
          password:
            "كلمة المرور",
          forgot:
            "نسيت كلمة المرور؟",
          login:
            "تسجيل الدخول",
          loading:
            "جارٍ تسجيل الدخول...",
          noAccount:
            "ليس لديك حساب؟",
          register:
            "إنشاء حساب",
          secure:
            "اتصال آمن",
          registered:
            "تم إنشاء الحساب بنجاح. يمكنك الآن تسجيل الدخول.",
        }
      : {
          leftBadge:
            "Espace personnel sécurisé",
          leftTitle:
            "Vous n’avez pas à gérer votre situation numérique seul(e).",
          leftText:
            "EMC Helpline vous aide à comprendre votre situation, conserver vos preuves et suivre des démarches claires depuis un espace personnel authentifié.",
          journey:
            "Votre parcours EMC Helpline",
          step1:
            "Évaluer",
          step2:
            "Plan d’action",
          step3:
            "Preuves",
          step4:
            "Suivi",
          privacy:
            "Vos informations privées restent liées à votre compte.",
          bilingual:
            "Interface français + العربية",
          welcome:
            "Bon retour",
          intro:
            "Connectez-vous pour retrouver votre espace victime ou administration selon le rôle de votre compte.",
          username:
            "Nom d’utilisateur",
          usernamePlaceholder:
            "Votre nom d’utilisateur",
          password:
            "Mot de passe",
          forgot:
            "Mot de passe oublié ?",
          login:
            "Se connecter",
          loading:
            "Connexion...",
          noAccount:
            "Vous n’avez pas de compte ?",
          register:
            "Créer un compte",
          secure:
            "Connexion sécurisée",
          registered:
            "Compte créé avec succès. Vous pouvez maintenant vous connecter.",
        };


  return (
    <div
      className="emc-login-page"
      lang={
        isArabic
          ? "ar"
          : "fr"
      }
      dir={
        isArabic
          ? "rtl"
          : "ltr"
      }
    >
      <section className="emc-login-shell">
        {/* ==================================================
            LEFT EXPERIENCE
        ================================================== */}

        <aside className="emc-login-visual">
          <span className="emc-login-orb orb-one" />
          <span className="emc-login-orb orb-two" />
          <span className="emc-login-line line-one" />
          <span className="emc-login-line line-two" />

          <div className="emc-login-brand">
            <span className="emc-login-logo">
              EMC
              <i />
            </span>

            <div>
              <strong>
                EMC Helpline
              </strong>

              <small>
                {copy.leftBadge}
              </small>
            </div>
          </div>

          <div className="emc-login-visual-content">
            <span className="emc-login-kicker">
              <Icon
                name="shield"
                size={18}
              />
              {copy.leftBadge}
            </span>

            <h2>
              {copy.leftTitle}
            </h2>

            <p>
              {copy.leftText}
            </p>

            <div className="emc-login-journey-card">
              <div className="emc-login-journey-head">
                <span>
                  <Icon
                    name="spark"
                    size={17}
                  />
                </span>

                <strong>
                  {copy.journey}
                </strong>
              </div>

              <div className="emc-login-journey">
                <div>
                  <span>
                    <Icon
                      name="shield"
                      size={16}
                    />
                  </span>

                  <small>
                    {copy.step1}
                  </small>
                </div>

                <i />

                <div>
                  <span>
                    <Icon
                      name="check"
                      size={16}
                    />
                  </span>

                  <small>
                    {copy.step2}
                  </small>
                </div>

                <i />

                <div>
                  <span>
                    <Icon
                      name="clip"
                      size={16}
                    />
                  </span>

                  <small>
                    {copy.step3}
                  </small>
                </div>

                <i />

                <div>
                  <span>
                    <Icon
                      name="folder"
                      size={16}
                    />
                  </span>

                  <small>
                    {copy.step4}
                  </small>
                </div>
              </div>
            </div>

            <div className="emc-login-trust-row">
              <span>
                <Icon
                  name="lock"
                  size={16}
                />

                {copy.privacy}
              </span>

              <span>
                <Icon
                  name="shield"
                  size={16}
                />

                {copy.bilingual}
              </span>
            </div>
          </div>

          <div className="emc-login-folder-art">
            <span className="folder-shadow" />
            <span className="folder-back" />

            <span className="folder-main">
              <i />

              <span>
                <Icon
                  name="shield"
                  size={42}
                />
              </span>
            </span>

            <b className="dot-one" />
            <b className="dot-two" />
            <b className="dot-three" />
          </div>
        </aside>


        {/* ==================================================
            RIGHT FORM
        ================================================== */}

        <main className="emc-login-form-side">
          <div className="emc-login-topbar">
            <span className="emc-login-secure-badge">
              <Icon
                name="lock"
                size={15}
              />

              {copy.secure}
            </span>

            <div
              className="emc-login-language"
              dir="ltr"
            >
              <button
                type="button"
                className={
                  language === "fr"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setLanguage("fr")
                }
              >
                FR
              </button>

              <button
                type="button"
                className={
                  language === "ar"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setLanguage("ar")
                }
              >
                العربية
              </button>
            </div>
          </div>

          <div className="emc-login-form-wrap">
            <div className="emc-login-form-brand">
              <span className="emc-login-small-logo">
                EMC
              </span>

              <div>
                <strong>
                  EMC Helpline
                </strong>

                <small>
                  {copy.leftBadge}
                </small>
              </div>
            </div>

            <span className="emc-login-form-kicker">
              {copy.leftBadge}
            </span>

            <h1>
              {copy.welcome}
            </h1>

            <p className="emc-login-intro">
              {copy.intro}
            </p>

            {location.state
              ?.registered && (
              <div className="emc-login-success">
                {copy.registered}
              </div>
            )}

            {error && (
              <div
                className="emc-login-error"
                role="alert"
              >
                {error}
              </div>
            )}

            <form
              className="emc-login-form"
              onSubmit={
                handleSubmit
              }
            >
              <label>
                <span>
                  {copy.username}
                </span>

                <div className="emc-login-input">
                  <Icon
                    name="user"
                    size={19}
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
                    placeholder={
                      copy.usernamePlaceholder
                    }
                    required
                  />
                </div>
              </label>

              <label>
                <span>
                  {copy.password}
                </span>

                <div className="emc-login-input">
                  <Icon
                    name="lock"
                    size={19}
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
                    autoComplete="current-password"
                    required
                  />

                  <button
                    type="button"
                    className="emc-login-eye"
                    aria-label={
                      showPassword
                        ? "Masquer le mot de passe"
                        : "Afficher le mot de passe"
                    }
                    onClick={() =>
                      setShowPassword(
                        (current) =>
                          !current
                      )
                    }
                  >
                    <Icon
                      name={
                        showPassword
                          ? "eye-off"
                          : "eye"
                      }
                      size={18}
                    />
                  </button>
                </div>
              </label>

              <div className="emc-login-forgot">
                <Link to="/forgot-password">
                  {copy.forgot}
                </Link>
              </div>

              <button
                type="submit"
                className="emc-login-submit"
                disabled={
                  status === "loading"
                }
              >
                {status === "loading" && (
                  <span className="emc-login-spinner" />
                )}

                {status === "loading"
                  ? copy.loading
                  : copy.login}
              </button>
            </form>

            <p className="emc-login-register">
              {copy.noAccount}{" "}

              <Link to="/register">
                {copy.register}
              </Link>
            </p>
          </div>
        </main>
      </section>
    </div>
  );
}


export default Login;