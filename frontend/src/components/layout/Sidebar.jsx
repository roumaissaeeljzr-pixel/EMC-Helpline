import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  NavLink,
  useNavigate,
} from "react-router-dom";

import {
  AnimatePresence,
  motion,
  useReducedMotion,
} from "framer-motion";

import {
  IconDashboard,
  IconChat,
  IconShield,
  IconCheck,
  IconFolder,
  IconClip,
  IconBook,
  IconClock,
  IconEye,
  IconChart,
  IconFolders,
  IconAlert,
  IconDatabase,
} from "./Icons.jsx";

import {
  useLanguage,
} from "../../context/LanguageContext.jsx";

import {
  useAuth,
} from "../../context/AuthContext.jsx";


const victimNavItems = [
  {
    to: "/victim/dashboard",
    labelKey: "dashboard",
    icon: IconDashboard,
    end: true,
  },
  {
    to: "/victim/assistant",
    labelKey: "assistant",
    icon: IconChat,
  },
  {
    to: "/victim/assessment",
    labelKey: "assessment",
    icon: IconShield,
  },
  {
    to: "/victim/action-plan",
    labelKey: "actionPlan",
    icon: IconCheck,
  },
  {
    to: "/victim/case",
    labelKey: "myCase",
    icon: IconFolder,
  },
  {
    to: "/victim/evidence",
    labelKey: "evidence",
    icon: IconClip,
  },
  {
    to: "/victim/resources",
    labelKey: "resources",
    icon: IconBook,
  },
  {
    to: "/victim/history",
    labelKey: "history",
    icon: IconClock,
  },
];


const adminNavItems = [
  {
    to: "/admin/dashboard",
    labelKey: "adminOverview",
    icon: IconEye,
    end: true,
  },
  {
    to: "/admin/statistics",
    labelKey: "adminStatistics",
    icon: IconChart,
  },
  {
    to: "/admin/cases",
    labelKey: "adminCases",
    icon: IconFolders,
  },
  {
    to: "/admin/priority-cases",
    labelKey: "adminPriorityCases",
    icon: IconAlert,
  },
  
  {
    to: "/admin/document-base",
    labelKey: "adminDocumentBase",
    icon: IconDatabase,
  },
];


const COPY = {
  fr: {
    victim:
      "Espace victime",

    admin:
      "Administration",

    personal:
      "Espace personnel sécurisé",

    active:
      "Compte actif",

    profile:
      "Mon profil",

    settings:
      "Paramètres du compte",

    privacy:
      "Confidentialité et sécurité",

    language:
      "Changer la langue",

    logout:
      "Se déconnecter",

    account:
      "Informations du compte",

    secure:
      "Votre session EMC Helpline est authentifiée.",

    settingsText:
      "Gérez votre compte et votre accès sécurisé.",

    usernameLabel:
      "Nom d’utilisateur",

    emailLabel:
      "Adresse e-mail",

    roleLabel:
      "Type de compte",

    victimRole:
      "Victime accompagnée",

    adminRole:
      "Administrateur",

    changePassword:
      "Modifier mon mot de passe",

    securityStatus:
      "Session authentifiée et active",

    collapse:
      "Réduire la navigation",

    expand:
      "Développer la navigation",
  },


  ar: {
    victim:
      "مساحة الضحية",

    admin:
      "الإدارة",

    personal:
      "مساحة شخصية آمنة",

    active:
      "الحساب نشط",

    profile:
      "ملفي الشخصي",

    settings:
      "إعدادات الحساب",

    privacy:
      "الخصوصية والأمان",

    language:
      "تغيير اللغة",

    logout:
      "تسجيل الخروج",

    account:
      "معلومات الحساب",

    secure:
      "جلسة EMC Helpline الخاصة بك موثقة.",

    settingsText:
      "يمكنك إدارة حسابك والوصول الآمن إلى مساحتك.",

    usernameLabel:
      "اسم المستخدم",

    emailLabel:
      "البريد الإلكتروني",

    roleLabel:
      "نوع الحساب",

    victimRole:
      "ضحية تتم مواكبتها",

    adminRole:
      "مسؤول",

    changePassword:
      "تغيير كلمة المرور",

    securityStatus:
      "الجلسة موثقة ونشطة",

    collapse:
      "تصغير القائمة",

    expand:
      "توسيع القائمة",
  },
};


function getDisplayName(user) {
  if (!user) {
    return null;
  }


  const first =
    user.firstName
    || user.first_name
    || "";


  const last =
    user.lastName
    || user.last_name
    || "";


  const composed =
    `${first} ${last}`.trim();


  return (
    composed
    || user.fullName
    || user.full_name
    || user.displayName
    || user.display_name
    || user.name
    || user.username
    || null
  );
}


function getUserPhoto(user) {
  if (!user) {
    return null;
  }


  return (
    user.profilePicture
    || user.profile_picture
    || user.avatar
    || user.avatarUrl
    || user.avatar_url
    || user.photo
    || user.photoUrl
    || user.photo_url
    || user.picture
    || user.image
    || null
  );
}


function getInitials(value) {
  if (!value) {
    return "";
  }


  const parts =
    String(value)
      .trim()
      .split(/\s+/)
      .filter(Boolean);


  if (parts.length === 1) {
    return parts[0]
      .slice(0, 2)
      .toUpperCase();
  }


  return (
    parts[0][0]
    + parts[
      parts.length - 1
    ][0]
  ).toUpperCase();
}


function AccountIcon({
  type,
}) {
  const props = {
    viewBox: "0 0 24 24",
    width: 19,
    height: 19,
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": "true",
  };


  if (type === "user") {
    return (
      <svg {...props}>
        <circle
          cx="12"
          cy="8"
          r="4"
        />
        <path d="M4 21c.8-4.2 3.5-6.3 8-6.3s7.2 2.1 8 6.3" />
      </svg>
    );
  }


  if (type === "settings") {
    return (
      <svg {...props}>
        <circle
          cx="12"
          cy="12"
          r="3"
        />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V21h-4v-.1a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14v-4a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3h4a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9A1.7 1.7 0 0 0 21 10v4a1.7 1.7 0 0 0-1.6 1Z" />
      </svg>
    );
  }


  if (type === "lock") {
    return (
      <svg {...props}>
        <rect
          x="5"
          y="10"
          width="14"
          height="10"
          rx="2"
        />
        <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      </svg>
    );
  }


  if (type === "language") {
    return (
      <svg {...props}>
        <circle
          cx="12"
          cy="12"
          r="9"
        />
        <path d="M3 12h18" />
        <path d="M12 3a15 15 0 0 1 0 18" />
        <path d="M12 3a15 15 0 0 0 0 18" />
      </svg>
    );
  }


  if (type === "logout") {
    return (
      <svg {...props}>
        <path d="M10 17l5-5-5-5" />
        <path d="M15 12H3" />
        <path d="M14 4h5a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-5" />
      </svg>
    );
  }


  return (
    <svg {...props}>
      <path d="m15 18-6-6 6-6" />
    </svg>
  );
}


function Sidebar({
  mode = "victim",
  isOpen,
  collapsed,
  onNavigate,
  onToggleCollapsed,
}) {
  const navigate =
    useNavigate();


  const reducedMotion =
    useReducedMotion();


  const profileRef =
    useRef(null);


  const {
    language,
    setLanguage,
    t,
  } = useLanguage();


  const {
    user,
    loading,
    logout,
  } = useAuth();


  const [
    profileOpen,
    setProfileOpen,
  ] = useState(false);


  const [
    detail,
    setDetail,
  ] = useState(null);


  const isArabic =
    language === "ar";


  const copy =
    COPY[
      isArabic
        ? "ar"
        : "fr"
    ];


  const isAdmin =
    mode === "admin";


  const navItems =
    isAdmin
      ? adminNavItems
      : victimNavItems;


  const displayName =
    getDisplayName(user);


  const profilePhoto =
    getUserPhoto(user);


  const initials =
    getInitials(displayName);


  useEffect(
    () => {
      const handleMouseDown =
        (event) => {
          if (
            profileRef.current
            && !profileRef.current.contains(
              event.target
            )
          ) {
            setProfileOpen(false);
            setDetail(null);
          }
        };


      const handleKeyDown =
        (event) => {
          if (event.key === "Escape") {
            setProfileOpen(false);
            setDetail(null);
          }
        };


      document.addEventListener(
        "mousedown",
        handleMouseDown
      );


      document.addEventListener(
        "keydown",
        handleKeyDown
      );


      return () => {
        document.removeEventListener(
          "mousedown",
          handleMouseDown
        );

        document.removeEventListener(
          "keydown",
          handleKeyDown
        );
      };
    },
    []
  );


  const closeAfterNavigation =
    () => {
      setProfileOpen(false);
      setDetail(null);
      onNavigate?.();
    };


  const handleLogout =
    async () => {
      try {
        await logout();
      } catch (error) {
        console.error(
          "Déconnexion :",
          error
        );
      } finally {
        setProfileOpen(false);
        setDetail(null);

        onNavigate?.();

        navigate(
          "/login",
          {
            replace: true,
          }
        );
      }
    };


  return (
    <motion.aside
      className={[
        "sidebar",
        isOpen
          ? "sidebar-open"
          : "",
        collapsed
          ? "sidebar-collapsed"
          : "",
      ]
        .filter(Boolean)
        .join(" ")}
      initial={false}
      animate={{
        width:
          collapsed
            ? 88
            : 284,
      }}
      transition={
        reducedMotion
          ? {
              duration: 0,
            }
          : {
              duration: 0.24,
              ease: [
                0.22,
                1,
                0.36,
                1,
              ],
            }
      }
    >
      <div className="sidebar-decor sidebar-decor-one" />
      <div className="sidebar-decor sidebar-decor-two" />


      <div className="sidebar-brand">
        <div className="sidebar-logo">
          <span>
            EMC
          </span>

          <i />
        </div>


        <AnimatePresence
          initial={false}
        >
          {!collapsed && (
            <motion.div
              className="sidebar-brand-copy"
              initial={{
                opacity: 0,
                x: -6,
              }}
              animate={{
                opacity: 1,
                x: 0,
              }}
              exit={{
                opacity: 0,
                x: -6,
              }}
            >
              <strong>
                EMC Helpline
              </strong>

              <small>
                {isAdmin
                  ? copy.admin
                  : copy.victim}
              </small>
            </motion.div>
          )}
        </AnimatePresence>
      </div>


      <div
        className="sidebar-profile"
        ref={profileRef}
      >
        {loading ? (
          <div className="sidebar-profile-skeleton">
            <span className="profile-skeleton-avatar" />

            {!collapsed && (
              <div>
                <span className="profile-skeleton-line" />
                <span className="profile-skeleton-line short" />
              </div>
            )}
          </div>
        ) : (
          <button
            type="button"
            className="sidebar-profile-button"
            aria-haspopup="menu"
            aria-expanded={
              profileOpen
            }
            aria-label={
              displayName
              || copy.profile
            }
            title={
              collapsed
                ? (
                    displayName
                    || undefined
                  )
                : undefined
            }
            onClick={() => {
              setProfileOpen(
                (current) =>
                  !current
              );

              setDetail(null);
            }}
          >
            <span className="sidebar-avatar">
              {profilePhoto ? (
                <img
                  src={profilePhoto}
                  alt={
                    displayName
                    || ""
                  }
                />
              ) : (
                <span>
                  {initials || "•"}
                </span>
              )}

              {user?.is_active && (
                <i className="sidebar-avatar-online" />
              )}
            </span>


            {!collapsed && (
              <>
                <span className="sidebar-profile-copy">
                  <strong>
                    {displayName || "—"}
                  </strong>

                  <small>
                    {copy.personal}
                  </small>
                </span>


                <motion.span
                  className="sidebar-profile-chevron"
                  animate={{
                    rotate:
                      profileOpen
                        ? 180
                        : 0,
                  }}
                >
                  ▾
                </motion.span>
              </>
            )}
          </button>
        )}


        <AnimatePresence>
          {profileOpen && !loading && (
            <motion.div
              className={[
                "sidebar-profile-menu",
                collapsed
                  ? "sidebar-profile-menu-collapsed"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
              role="menu"
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
              <div className="sidebar-profile-state">
                <i />

                <span>
                  {copy.active}
                </span>
              </div>


              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  if (!isAdmin) {
                    setProfileOpen(false);
                    setDetail(null);
                    onNavigate?.();

                    navigate(
                      "/victim/profile"
                    );

                    return;
                  }

                  setDetail(
                    detail === "profile"
                      ? null
                      : "profile"
                  );
                }}
              >
                <AccountIcon type="user" />
                <span>
                  {copy.profile}
                </span>
              </button>


              <button
                type="button"
                role="menuitem"
                onClick={() =>
                  setDetail(
                    detail === "settings"
                      ? null
                      : "settings"
                  )
                }
              >
                <AccountIcon type="settings" />
                <span>
                  {copy.settings}
                </span>
              </button>


              <button
                type="button"
                role="menuitem"
                onClick={() =>
                  setDetail(
                    detail === "privacy"
                      ? null
                      : "privacy"
                  )
                }
              >
                <AccountIcon type="lock" />
                <span>
                  {copy.privacy}
                </span>
              </button>


              <button
                type="button"
                role="menuitem"
                onClick={() =>
                  setDetail(
                    detail === "language"
                      ? null
                      : "language"
                  )
                }
              >
                <AccountIcon type="language" />
                <span>
                  {copy.language}
                </span>
              </button>


              <AnimatePresence mode="wait">
                {detail && (
                  <motion.div
                    key={detail}
                    className="sidebar-profile-detail"
                    initial={{
                      opacity: 0,
                      height: 0,
                    }}
                    animate={{
                      opacity: 1,
                      height: "auto",
                    }}
                    exit={{
                      opacity: 0,
                      height: 0,
                    }}
                  >
                    {detail === "profile" && isAdmin && (
                      <>
                        <strong>
                          {copy.account}
                        </strong>

                        <span>
                          {displayName || "—"}
                        </span>

                        {user?.email && (
                          <small>
                            {user.email}
                          </small>
                        )}

                        <em className="sidebar-profile-role">
                          {copy.adminRole}
                        </em>
                      </>
                    )}


                    {detail === "settings" && (
                      <>
                        <strong>
                          {copy.settings}
                        </strong>

                        <small className="sidebar-settings-intro">
                          {copy.settingsText}
                        </small>

                        <div className="sidebar-settings-grid">
                          <div>
                            <span>
                              {copy.usernameLabel}
                            </span>

                            <strong>
                              {user?.username || displayName || "—"}
                            </strong>
                          </div>

                          <div>
                            <span>
                              {copy.emailLabel}
                            </span>

                            <strong>
                              {user?.email || "—"}
                            </strong>
                          </div>

                          <div>
                            <span>
                              {copy.roleLabel}
                            </span>

                            <strong>
                              {isAdmin
                                ? copy.adminRole
                                : copy.victimRole}
                            </strong>
                          </div>
                        </div>

                        <button
                          type="button"
                          className="sidebar-settings-action"
                          onClick={() => {
                            setProfileOpen(false);
                            setDetail(null);
                            onNavigate?.();
                            navigate(
                              "/forgot-password"
                            );
                          }}
                        >
                          <AccountIcon type="lock" />
                          <span>
                            {copy.changePassword}
                          </span>
                        </button>
                      </>
                    )}


                    {detail === "privacy" && (
                      <>
                        <strong>
                          {copy.privacy}
                        </strong>

                        <div className="sidebar-security-state">
                          <i />

                          <span>
                            {copy.securityStatus}
                          </span>
                        </div>

                        <small>
                          {copy.secure}
                        </small>
                      </>
                    )}


                    {detail === "language" && (
                      <div className="sidebar-language-options">
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
                          Français
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
                    )}
                  </motion.div>
                )}
              </AnimatePresence>


              <div className="sidebar-profile-divider" />


              <button
                type="button"
                role="menuitem"
                className="sidebar-profile-logout"
                onClick={
                  handleLogout
                }
              >
                <AccountIcon type="logout" />

                <span>
                  {copy.logout}
                </span>
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>


      <nav
        className="sidebar-nav"
        dir={
          isArabic
            ? "rtl"
            : "ltr"
        }
      >
        {!collapsed && (
          <p className="sidebar-section-label">
            {isAdmin
              ? t(
                  "navigation.sectionAdmin"
                )
              : t(
                  "navigation.sectionVictim"
                )}
          </p>
        )}


        <ul>
          {navItems.map(
            ({
              to,
              labelKey,
              icon: Icon,
              end,
            }) => (
              <motion.li
                key={to}
                whileHover={
                  reducedMotion
                    ? undefined
                    : {
                        x:
                          isArabic
                            ? -2
                            : 2,
                      }
                }
              >
                <NavLink
                  to={to}
                  end={end}
                  onClick={
                    closeAfterNavigation
                  }
                  aria-label={
                    collapsed
                      ? t(
                          `navigation.${labelKey}`
                        )
                      : undefined
                  }
                  title={
                    collapsed
                      ? t(
                          `navigation.${labelKey}`
                        )
                      : undefined
                  }
                  className={({
                    isActive,
                  }) =>
                    [
                      "sidebar-link",
                      isActive
                        ? "sidebar-link-active"
                        : "",
                    ]
                      .filter(Boolean)
                      .join(" ")
                  }
                >
                  <span className="sidebar-link-icon">
                    <Icon />
                  </span>


                  {!collapsed && (
                    <span className="sidebar-link-label">
                      {t(
                        `navigation.${labelKey}`
                      )}
                    </span>
                  )}
                </NavLink>
              </motion.li>
            )
          )}
        </ul>
      </nav>


      <div className="sidebar-footer">
        <button
          type="button"
          className="sidebar-collapse-button"
          aria-label={
            collapsed
              ? copy.expand
              : copy.collapse
          }
          title={
            collapsed
              ? copy.expand
              : copy.collapse
          }
          onClick={
            onToggleCollapsed
          }
        >
          <motion.span
            animate={{
              rotate:
                collapsed
                  ? 180
                  : 0,
            }}
          >
            <AccountIcon type="collapse" />
          </motion.span>


          {!collapsed && (
            <span>
              {copy.collapse}
            </span>
          )}
        </button>


        <button
          type="button"
          className="sidebar-logout-button"
          aria-label={
            copy.logout
          }
          title={
            collapsed
              ? copy.logout
              : undefined
          }
          onClick={
            handleLogout
          }
        >
          <AccountIcon type="logout" />

          {!collapsed && (
            <span>
              {copy.logout}
            </span>
          )}
        </button>
      </div>
    </motion.aside>
  );
}


export default Sidebar;