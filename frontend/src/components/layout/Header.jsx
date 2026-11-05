import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  useLocation,
} from "react-router-dom";

import {
  AnimatePresence,
  motion,
} from "framer-motion";

import {
  useLanguage,
} from "../../context/LanguageContext.jsx";


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


const COPY = {
  fr: {
    victim:
      "Espace victime",

    admin:
      "Administration",

    available:
      "Service disponible",

    unavailable:
      "Service indisponible",

    notifications:
      "Notifications",

    empty:
      "Aucune nouvelle notification.",

    menu:
      "Ouvrir la navigation",

    pages: {
      "/victim/dashboard":
        "Tableau de bord",

      "/victim/assistant":
        "Assistant IA",

      "/victim/assessment":
        "Évaluer ma situation",

      "/victim/action-plan":
        "Plan d’action",

      "/victim/case":
        "Mon dossier",

      "/victim/evidence":
        "Mes preuves",

      "/victim/resources":
        "Ressources",

      "/victim/history":
        "Historique",

      "/admin/dashboard":
        "Vue générale",

      "/admin/statistics":
        "Statistiques",

      "/admin/cases":
        "Dossiers",

      "/admin/priority-cases":
        "Cas prioritaires",

      "/admin/ai-performance":
        "Performance IA",

      "/admin/document-base":
        "Base documentaire",
    },
  },


  ar: {
    victim:
      "مساحة الضحية",

    admin:
      "الإدارة",

    available:
      "الخدمة متاحة",

    unavailable:
      "الخدمة غير متاحة",

    notifications:
      "الإشعارات",

    empty:
      "لا توجد إشعارات جديدة.",

    menu:
      "فتح القائمة",

    pages: {
      "/victim/dashboard":
        "لوحة التحكم",

      "/victim/assistant":
        "المساعد الذكي",

      "/victim/assessment":
        "تقييم وضعي",

      "/victim/action-plan":
        "خطة العمل",

      "/victim/case":
        "ملفي",

      "/victim/evidence":
        "أدلتي",

      "/victim/resources":
        "الموارد",

      "/victim/history":
        "السجل",

      "/admin/dashboard":
        "نظرة عامة",

      "/admin/statistics":
        "الإحصائيات",

      "/admin/cases":
        "الملفات",

      "/admin/priority-cases":
        "الحالات ذات الأولوية",

      "/admin/ai-performance":
        "أداء الذكاء الاصطناعي",

      "/admin/document-base":
        "قاعدة الوثائق",
    },
  },
};


function HeaderIcon({
  name,
}) {
  const props = {
    width: 20,
    height: 20,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": "true",
  };


  if (name === "bell") {
    return (
      <svg {...props}>
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
        <path d="M10 21h4" />
      </svg>
    );
  }


  return (
    <svg {...props}>
      <path d="M4 7h16" />
      <path d="M4 12h16" />
      <path d="M4 17h16" />
    </svg>
  );
}


function Header({
  mode = "victim",
  onToggleSidebar,
}) {
  const location =
    useLocation();


  const notificationRef =
    useRef(null);


  const {
    language,
    setLanguage,
  } = useLanguage();


  const [
    serviceAvailable,
    setServiceAvailable,
  ] = useState(null);


  const [
    notificationsOpen,
    setNotificationsOpen,
  ] = useState(false);


  const isArabic =
    language === "ar";


  const copy =
    COPY[
      isArabic
        ? "ar"
        : "fr"
    ];


  const pageTitle =
    copy.pages[
      location.pathname
    ]
    || "EMC Helpline";


  /* ======================================================
     SERVICE STATUS
  ====================================================== */

  useEffect(
    () => {
      let active = true;


      const checkHealth =
        async () => {
          try {
            const response =
              await fetch(
                `${API_BASE_URL}/health`
              );


            if (active) {
              setServiceAvailable(
                response.ok
              );
            }
          } catch {
            if (active) {
              setServiceAvailable(
                false
              );
            }
          }
        };


      checkHealth();


      const timer =
        window.setInterval(
          checkHealth,
          20000
        );


      return () => {
        active = false;

        window.clearInterval(
          timer
        );
      };
    },
    []
  );


  /* ======================================================
     CLOSE NOTIFICATIONS OUTSIDE
  ====================================================== */

  useEffect(
    () => {
      const handler =
        (event) => {
          if (
            notificationRef.current
            && !notificationRef.current
              .contains(event.target)
          ) {
            setNotificationsOpen(false);
          }
        };


      document.addEventListener(
        "mousedown",
        handler
      );


      return () => {
        document.removeEventListener(
          "mousedown",
          handler
        );
      };
    },
    []
  );


  useEffect(
    () => {
      setNotificationsOpen(false);
    },
    [
      location.pathname,
    ]
  );


  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          type="button"
          className="sidebar-toggle"
          aria-label={
            copy.menu
          }
          onClick={
            onToggleSidebar
          }
        >
          <HeaderIcon
            name="menu"
          />
        </button>


        <div
          className="topbar-title"
          dir={
            isArabic
              ? "rtl"
              : "ltr"
          }
        >
          <span>
            {mode === "admin"
              ? copy.admin
              : copy.victim}
          </span>

          <h1>
            {pageTitle}
          </h1>
        </div>
      </div>


      <div className="topbar-right">
        {/* LANGUE */}

        <div
          className="language-switch"
          dir="ltr"
        >
          <button
            type="button"
            className={
              language === "fr"
                ? "language-option language-option-active"
                : "language-option"
            }
            aria-pressed={
              language === "fr"
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
                ? "language-option language-option-active"
                : "language-option"
            }
            aria-pressed={
              language === "ar"
            }
            onClick={() =>
              setLanguage("ar")
            }
          >
            العربية
          </button>
        </div>


        {/* SERVICE */}

        <div className="status">
          <span
            className={[
              "status-dot",
              serviceAvailable
                ? "status-dot-online"
                : "status-dot-down",
            ]
              .filter(Boolean)
              .join(" ")}
          />

          <span className="status-text">
            {serviceAvailable
              ? copy.available
              : copy.unavailable}
          </span>
        </div>


        {/* NOTIFICATIONS */}

        <div
          ref={notificationRef}
          className="notification-wrapper"
        >
          <button
            type="button"
            className="header-icon-button"
            aria-label={
              copy.notifications
            }
            aria-expanded={
              notificationsOpen
            }
            onClick={() =>
              setNotificationsOpen(
                (current) =>
                  !current
              )
            }
          >
            <HeaderIcon
              name="bell"
            />
          </button>


          <AnimatePresence>
            {notificationsOpen && (
              <motion.div
                className="notification-popover"
                dir={
                  isArabic
                    ? "rtl"
                    : "ltr"
                }
                initial={{
                  opacity: 0,
                  y: -6,
                  scale: 0.98,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                  scale: 1,
                }}
                exit={{
                  opacity: 0,
                  y: -6,
                  scale: 0.98,
                }}
                transition={{
                  duration: 0.16,
                }}
              >
                <strong>
                  {copy.notifications}
                </strong>

                <p>
                  {copy.empty}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}


export default Header;