import {
  useLanguage,
} from "../../context/LanguageContext.jsx";


function ShellIcon({
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

  if (name === "lock") {
    return (
      <svg {...props}>
        <rect x="5" y="10" width="14" height="10" rx="2" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      </svg>
    );
  }

  if (name === "mail") {
    return (
      <svg {...props}>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m4 7 8 6 8-6" />
      </svg>
    );
  }

  if (name === "key") {
    return (
      <svg {...props}>
        <circle cx="8" cy="15" r="4" />
        <path d="m11 12 8-8" />
        <path d="m16 7 2 2" />
        <path d="m14 9 2 2" />
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

  if (name === "user") {
    return (
      <svg {...props}>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c.8-4.2 3.5-6.3 8-6.3s7.2 2.1 8 6.3" />
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
      </svg>
    );
  }

  return (
    <svg {...props}>
      <circle cx="12" cy="12" r="9" />
    </svg>
  );
}


function AuthCreativeShell({
  eyebrow,
  title,
  intro,
  leftTitle,
  leftText,
  children,
  footer,
  recoveryStep = 0,
}) {
  const {
    language,
    setLanguage,
  } = useLanguage();

  const isArabic =
    language === "ar";

  const copy =
    isArabic
      ? {
          secure: "اتصال آمن",
          private: "مساحة شخصية محمية",
          bilingual: "فرنسية + العربية",
          support: "مرافقة خطوة بخطوة",
          journey: "مسار EMC Helpline",
          evaluate: "تقييم",
          plan: "خطة",
          evidence: "أدلة",
          follow: "متابعة",
          recover: "استعادة الحساب بأمان",
          email: "البريد",
          code: "الرمز",
          password: "كلمة المرور",
        }
      : {
          secure: "Connexion sécurisée",
          private: "Espace personnel protégé",
          bilingual: "Français + العربية",
          support: "Accompagnement pas à pas",
          journey: "Parcours EMC Helpline",
          evaluate: "Évaluer",
          plan: "Plan",
          evidence: "Preuves",
          follow: "Suivi",
          recover: "Récupération sécurisée",
          email: "E-mail",
          code: "Code",
          password: "Mot de passe",
        };

  const recoveryLabels = [
    copy.email,
    copy.code,
    copy.password,
  ];

  return (
    <div
      className="emc-auth-page"
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
      <section className="emc-auth-shell">
        <aside className="emc-auth-visual">
          <span className="emc-auth-orb orb-a" />
          <span className="emc-auth-orb orb-b" />
          <span className="emc-auth-line line-a" />
          <span className="emc-auth-line line-b" />

          <div className="emc-auth-brand">
            <span className="emc-auth-logo">
              EMC
              <i />
            </span>

            <div>
              <strong>
                EMC Helpline
              </strong>

              <small>
                {copy.private}
              </small>
            </div>
          </div>

          <div className="emc-auth-left-copy">
            <span className="emc-auth-left-badge">
              <ShellIcon
                name="shield"
                size={17}
              />

              {recoveryStep
                ? copy.recover
                : copy.private}
            </span>

            <h2>
              {leftTitle}
            </h2>

            <p>
              {leftText}
            </p>

            {recoveryStep ? (
              <div className="emc-auth-recovery-card">
                <div className="emc-auth-recovery-head">
                  <span>
                    <ShellIcon
                      name="key"
                      size={17}
                    />
                  </span>

                  <strong>
                    {copy.recover}
                  </strong>
                </div>

                <div className="emc-auth-recovery-steps">
                  {recoveryLabels.map(
                    (
                      label,
                      index
                    ) => {
                      const number =
                        index + 1;

                      const state =
                        number < recoveryStep
                          ? "done"
                          : number === recoveryStep
                            ? "current"
                            : "next";

                      return (
                        <div
                          className={`emc-auth-recovery-step ${state}`}
                          key={label}
                        >
                          <span>
                            {number < recoveryStep
                              ? (
                                  <ShellIcon
                                    name="check"
                                    size={14}
                                  />
                                )
                              : number}
                          </span>

                          <small>
                            {label}
                          </small>
                        </div>
                      );
                    }
                  )}
                </div>
              </div>
            ) : (
              <div className="emc-auth-journey-card">
                <div className="emc-auth-journey-title">
                  <ShellIcon
                    name="spark"
                    size={16}
                  />
                  {copy.journey}
                </div>

                <div className="emc-auth-journey">
                  <div>
                    <span>
                      <ShellIcon
                        name="shield"
                        size={15}
                      />
                    </span>
                    <small>
                      {copy.evaluate}
                    </small>
                  </div>

                  <i />

                  <div>
                    <span>
                      <ShellIcon
                        name="check"
                        size={15}
                      />
                    </span>
                    <small>
                      {copy.plan}
                    </small>
                  </div>

                  <i />

                  <div>
                    <span>
                      <ShellIcon
                        name="mail"
                        size={15}
                      />
                    </span>
                    <small>
                      {copy.evidence}
                    </small>
                  </div>

                  <i />

                  <div>
                    <span>
                      <ShellIcon
                        name="user"
                        size={15}
                      />
                    </span>
                    <small>
                      {copy.follow}
                    </small>
                  </div>
                </div>
              </div>
            )}

            <div className="emc-auth-trust-row">
              <span>
                <ShellIcon
                  name="lock"
                  size={15}
                />
                {copy.private}
              </span>

              <span>
                <ShellIcon
                  name="shield"
                  size={15}
                />
                {copy.bilingual}
              </span>

              <span>
                <ShellIcon
                  name="check"
                  size={15}
                />
                {copy.support}
              </span>
            </div>
          </div>

          <div className="emc-auth-folder-art">
            <span className="folder-back" />

            <span className="folder-front">
              <i />

              <span>
                <ShellIcon
                  name={
                    recoveryStep
                      ? "key"
                      : "shield"
                  }
                  size={42}
                />
              </span>
            </span>

            <b className="dot-a" />
            <b className="dot-b" />
            <b className="dot-c" />
          </div>
        </aside>

        <main className="emc-auth-form-side">
          <div className="emc-auth-topbar">
            <span className="emc-auth-secure">
              <ShellIcon
                name="lock"
                size={14}
              />
              {copy.secure}
            </span>

            <div
              className="emc-auth-language"
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

          <div className="emc-auth-form-wrap">
            <div className="emc-auth-mobile-brand">
              <span>
                EMC
              </span>

              <strong>
                EMC Helpline
              </strong>
            </div>

            {eyebrow && (
              <span className="emc-auth-eyebrow">
                {eyebrow}
              </span>
            )}

            <h1>
              {title}
            </h1>

            {intro && (
              <p className="emc-auth-intro">
                {intro}
              </p>
            )}

            {children}

            {footer}
          </div>
        </main>
      </section>
    </div>
  );
}


export {
  ShellIcon,
};

export default AuthCreativeShell;