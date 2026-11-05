import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  motion,
  useReducedMotion,
} from "framer-motion";

import {
  useAuth,
} from "../../context/AuthContext.jsx";

import {
  useLanguage,
} from "../../context/LanguageContext.jsx";

import {
  DashboardIcon,
  GuidedFolderIllustration,
  ProgressCircle,
} from "../../components/dashboard/DashboardComponents.jsx";

import "../Dashboard.css";
import "./Overview.css";


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


const COPY = {
  fr: {
    kicker:
      "Administration EMC Helpline",

    welcome:
      "Bienvenue dans votre espace administration",

    intro:
      "Retrouvez ici une vue claire de l’activité de la plateforme, des dossiers en cours et des éléments qui nécessitent votre attention.",

    victims:
      "Victimes inscrites",

    activeVictims:
      "comptes actifs",

    activeCases:
      "Dossiers actifs",

    totalCases:
      "dossiers au total",

    priorityCases:
      "Cas prioritaires",

    urgentActive:
      "urgences actives",

    publishedResources:
      "Ressources publiées",

    drafts:
      "brouillons",

    priorityHeader:
      "À traiter en priorité",

    noPriorityTitle:
      "Aucun cas urgent actif",

    noPriorityText:
      "Aucune situation marquée comme urgente ne nécessite actuellement une intervention administrative.",

    priorityTitle:
      "cas nécessitent votre attention",

    priorityText:
      "Consultez les situations urgentes encore actives et priorisez leur suivi.",

    viewPriority:
      "Voir les cas prioritaires",

    platform:
      "Vue d’ensemble de la plateforme",

    platformText:
      "Les indicateurs ci-dessous sont calculés à partir des données réellement enregistrées.",

    activity:
      "Activité des 7 derniers jours",

    activityText:
      "Nouveaux dossiers créés chaque jour.",

    actionProgress:
      "Progression des actions",

    actionsCompleted:
      "actions terminées",

    evidence:
      "Preuves enregistrées",

    plans:
      "Plans d’action générés",

    languages:
      "Langues des dossiers",

    french:
      "Français",

    arabic:
      "Arabe",

    situations:
      "Situations les plus détectées",

    situationsText:
      "Répartition des principales intentions enregistrées dans les dossiers.",

    noSituations:
      "Aucune situation détectée pour le moment.",

    recent:
      "Activité récente",

    recentText:
      "Dernières actions enregistrées dans la plateforme.",

    noActivity:
      "Aucune activité récente.",

    quick:
      "Accès rapides",

    statistics:
      "Statistiques",

    statisticsText:
      "Consultez les indicateurs détaillés de la plateforme.",

    cases:
      "Dossiers",

    casesText:
      "Consultez et gérez les dossiers enregistrés.",

    priority:
      "Cas prioritaires",

    priorityQuickText:
      "Accédez rapidement aux situations urgentes.",

    documents:
      "Base documentaire",

    documentsText:
      "Gérez les ressources publiées et les brouillons.",

    today:
      "Aujourd’hui",

    newToday:
      "nouveau(x) dossier(s)",

    loading:
      "Chargement de la vue générale...",

    error:
      "Certaines informations n’ont pas pu être chargées.",

    retry:
      "Réessayer",

    open:
      "Ouvrir",

    eventLabels: {
      case_created:
        "Dossier créé",

      assessment_completed:
        "Évaluation terminée",

      action_plan_generated:
        "Plan d’action généré",

      action_completed:
        "Action terminée",

      action_reopened:
        "Action rouverte",

      evidence_added:
        "Preuve ajoutée",

      evidence_deleted:
        "Preuve supprimée",

      case_status_changed:
        "Statut du dossier modifié",
    },
  },


  ar: {
    kicker:
      "إدارة EMC Helpline",

    welcome:
      "مرحبًا بك في فضاء الإدارة",

    intro:
      "تجد هنا نظرة واضحة على نشاط المنصة والملفات الحالية والعناصر التي تحتاج إلى انتباه فريق الإدارة.",

    victims:
      "الضحايا المسجلون",

    activeVictims:
      "حسابات نشطة",

    activeCases:
      "الملفات النشطة",

    totalCases:
      "ملفات في المجموع",

    priorityCases:
      "الحالات ذات الأولوية",

    urgentActive:
      "حالات طارئة نشطة",

    publishedResources:
      "الموارد المنشورة",

    drafts:
      "مسودات",

    priorityHeader:
      "الأولوية الحالية",

    noPriorityTitle:
      "لا توجد حالة طارئة نشطة",

    noPriorityText:
      "لا توجد حاليًا حالة مصنفة كطارئة تحتاج إلى تدخل إداري.",

    priorityTitle:
      "حالات تحتاج إلى انتباهك",

    priorityText:
      "راجع الحالات الطارئة النشطة وحدد أولويات المتابعة.",

    viewPriority:
      "عرض الحالات ذات الأولوية",

    platform:
      "نظرة عامة على المنصة",

    platformText:
      "المؤشرات التالية محسوبة انطلاقًا من البيانات المسجلة فعليًا.",

    activity:
      "نشاط آخر 7 أيام",

    activityText:
      "عدد الملفات الجديدة المنشأة يوميًا.",

    actionProgress:
      "تقدم الإجراءات",

    actionsCompleted:
      "إجراءات منجزة",

    evidence:
      "الأدلة المسجلة",

    plans:
      "خطط العمل المنشأة",

    languages:
      "لغات الملفات",

    french:
      "الفرنسية",

    arabic:
      "العربية",

    situations:
      "أكثر الحالات اكتشافًا",

    situationsText:
      "توزيع أهم أنواع الحالات المسجلة في الملفات.",

    noSituations:
      "لا توجد حالات مكتشفة حاليًا.",

    recent:
      "النشاط الأخير",

    recentText:
      "آخر العمليات المسجلة في المنصة.",

    noActivity:
      "لا يوجد نشاط حديث.",

    quick:
      "الوصول السريع",

    statistics:
      "الإحصائيات",

    statisticsText:
      "اطلع على مؤشرات المنصة بالتفصيل.",

    cases:
      "الملفات",

    casesText:
      "اطلع على الملفات المسجلة وقم بإدارتها.",

    priority:
      "الحالات ذات الأولوية",

    priorityQuickText:
      "الوصول السريع إلى الحالات الطارئة.",

    documents:
      "القاعدة الوثائقية",

    documentsText:
      "أدر الموارد المنشورة والمسودات.",

    today:
      "اليوم",

    newToday:
      "ملفات جديدة",

    loading:
      "جارٍ تحميل النظرة العامة...",

    error:
      "تعذر تحميل بعض المعلومات.",

    retry:
      "إعادة المحاولة",

    open:
      "فتح",

    eventLabels: {
      case_created:
        "تم إنشاء ملف",

      assessment_completed:
        "تم إنهاء التقييم",

      action_plan_generated:
        "تم إنشاء خطة العمل",

      action_completed:
        "تم إنهاء إجراء",

      action_reopened:
        "تمت إعادة فتح إجراء",

      evidence_added:
        "تمت إضافة دليل",

      evidence_deleted:
        "تم حذف دليل",

      case_status_changed:
        "تم تعديل حالة الملف",
    },
  },
};


function getDisplayName(user) {
  if (!user) {
    return "";
  }

  const first =
    user.firstName
    || user.first_name
    || "";

  const last =
    user.lastName
    || user.last_name
    || "";

  return (
    `${first} ${last}`.trim()
    || user.fullName
    || user.full_name
    || user.name
    || user.displayName
    || user.display_name
    || user.username
    || ""
  );
}


function formatDate(
  value,
  language,
) {
  if (!value) {
    return "—";
  }

  try {
    return new Intl.DateTimeFormat(
      language === "ar"
        ? "ar-MA"
        : "fr-FR",
      {
        day:
          "numeric",

        month:
          "short",

        hour:
          "2-digit",

        minute:
          "2-digit",
      }
    ).format(
      new Date(value)
    );
  } catch {
    return value;
  }
}


function SummaryCard({
  icon,
  tone,
  label,
  value,
  detail,
  reducedMotion,
}) {
  return (
    <motion.article
      className={`admin-guided-summary-card tone-${tone}`}
      initial={
        reducedMotion
          ? false
          : {
              opacity: 0,
              y: 10,
            }
      }
      animate={{
        opacity: 1,
        y: 0,
      }}
      whileHover={
        reducedMotion
          ? undefined
          : {
              y: -3,
            }
      }
    >
      <span className="admin-guided-summary-icon">
        <DashboardIcon
          name={icon}
          size={25}
        />
      </span>

      <div>
        <small>
          {label}
        </small>

        <strong>
          {value}
        </strong>

        <p>
          {detail}
        </p>
      </div>
    </motion.article>
  );
}


function QuickAdminCard({
  icon,
  tone,
  title,
  description,
  onClick,
  reducedMotion,
}) {
  return (
    <motion.button
      type="button"
      className={`admin-guided-quick-card tone-${tone}`}
      onClick={onClick}
      whileHover={
        reducedMotion
          ? undefined
          : {
              y: -4,
            }
      }
      whileTap={
        reducedMotion
          ? undefined
          : {
              scale:
                0.985,
            }
      }
    >
      <span className="admin-guided-quick-icon">
        <DashboardIcon
          name={icon}
          size={22}
        />
      </span>

      <strong>
        {title}
      </strong>

      <p>
        {description}
      </p>

      <span className="admin-guided-quick-arrow">
        <DashboardIcon
          name="arrow"
          size={18}
        />
      </span>
    </motion.button>
  );
}


function Overview() {
  const navigate =
    useNavigate();

  const reducedMotion =
    useReducedMotion();

  const {
    user,
  } = useAuth();

  const {
    language,
  } = useLanguage();

  const isArabic =
    language === "ar";

  const labels =
    COPY[
      isArabic
        ? "ar"
        : "fr"
    ];

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");

  const [
    data,
    setData,
  ] = useState(null);


  const displayName =
    getDisplayName(user);

  const firstName =
    displayName
      .split(/\s+/)
      .filter(Boolean)[0]
    || "";


  const loadOverview =
    useCallback(
      async () => {
        setLoading(true);
        setError("");

        try {
          const response =
            await fetch(
              `${API_BASE_URL}/admin/overview`,
              {
                credentials:
                  "include",

                headers: {
                  Accept:
                    "application/json",
                },
              }
            );

          const payload =
            await response
              .json()
              .catch(
                () => null
              );

          if (!response.ok) {
            throw new Error(
              typeof payload?.detail
                === "string"
                ? payload.detail
                : labels.error
            );
          }

          setData(
            payload
          );
        } catch (loadError) {
          console.error(
            "Admin Overview :",
            loadError
          );

          setData(null);

          setError(
            loadError.message
            || labels.error
          );
        } finally {
          setLoading(false);
        }
      },
      [
        labels.error,
      ]
    );


  useEffect(
    () => {
      loadOverview();
    },
    [
      loadOverview,
    ]
  );


  const summary =
    data?.summary
    || {};


  const maxDaily =
    useMemo(
      () =>
        Math.max(
          1,
          ...(
            data?.cases_last_7_days
            || []
          ).map(
            (item) =>
              Number(
                item.count
                || 0
              )
          )
        ),
      [
        data,
      ]
    );


  const intentTotal =
    useMemo(
      () =>
        (
          data?.by_intent
          || []
        ).reduce(
          (
            total,
            item
          ) =>
            total
            + Number(
                item.count
                || 0
              ),
          0
        ),
      [
        data,
      ]
    );


  const languageTotal =
    useMemo(
      () =>
        (
          data?.by_language
          || []
        ).reduce(
          (
            total,
            item
          ) =>
            total
            + Number(
                item.count
                || 0
              ),
          0
        ),
      [
        data,
      ]
    );


  if (loading) {
    return (
      <div className="guided-dashboard admin-guided-dashboard">
        <section className="admin-guided-loading">
          <span className="admin-guided-spinner" />

          <h2>
            {labels.loading}
          </h2>
        </section>
      </div>
    );
  }


  if (error) {
    return (
      <div className="guided-dashboard admin-guided-dashboard">
        <section className="guided-no-case admin-guided-error">
          <span>
            <DashboardIcon
              name="alert"
              size={38}
            />
          </span>

          <h1>
            {labels.error}
          </h1>

          <p>
            {error}
          </p>

          <button
            type="button"
            onClick={
              loadOverview
            }
          >
            {labels.retry}
          </button>
        </section>
      </div>
    );
  }


  const priorityCount =
    Number(
      summary.priority_cases
      || 0
    );


  return (
    <motion.div
      key={language}
      className="guided-dashboard admin-guided-dashboard"
      dir={
        isArabic
          ? "rtl"
          : "ltr"
      }
      initial={
        reducedMotion
          ? false
          : {
              opacity: 0,
            }
      }
      animate={{
        opacity: 1,
      }}
      transition={{
        duration: 0.25,
      }}
    >
      {/* =================================================
          WELCOME — SAME STRUCTURE AS VICTIM DASHBOARD
      ================================================= */}

      <motion.section
        className="guided-welcome"
        initial={
          reducedMotion
            ? false
            : {
                opacity: 0,
                y: 12,
              }
        }
        animate={{
          opacity: 1,
          y: 0,
        }}
      >
        <div className="guided-welcome-copy">
          <span className="guided-welcome-kicker">
            {labels.kicker}
          </span>

          <h1>
            {labels.welcome}

            {firstName
              ? `, ${firstName}`
              : ""}

            !
          </h1>

          <p>
            {labels.intro}
          </p>
        </div>

        <GuidedFolderIllustration />
      </motion.section>


      {/* =================================================
          4 MAIN INDICATORS
      ================================================= */}

      <section className="admin-guided-summary-grid">
        <SummaryCard
          icon="shield"
          tone="purple"
          label={
            labels.victims
          }
          value={
            summary.victims
            || 0
          }
          detail={
            `${summary.active_victims || 0} ${labels.activeVictims}`
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="folder"
          tone="blue"
          label={
            labels.activeCases
          }
          value={
            summary.active_cases
            || 0
          }
          detail={
            `${summary.total_cases || 0} ${labels.totalCases}`
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="alert"
          tone="coral"
          label={
            labels.priorityCases
          }
          value={
            priorityCount
          }
          detail={
            labels.urgentActive
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="spark"
          tone="orange"
          label={
            labels.publishedResources
          }
          value={
            summary.published_resources
            || 0
          }
          detail={
            `${summary.draft_resources || 0} ${labels.drafts}`
          }
          reducedMotion={
            reducedMotion
          }
        />
      </section>


      {/* =================================================
          PRIORITY — SAME VISUAL LANGUAGE AS NEXT ACTION
      ================================================= */}

      <motion.section
        className={
          priorityCount > 0
            ? "guided-next-action admin-guided-priority"
            : "guided-next-action admin-guided-priority is-complete"
        }
        initial={
          reducedMotion
            ? false
            : {
                opacity: 0,
                y: 12,
              }
        }
        animate={{
          opacity: 1,
          y: 0,
        }}
      >
        <div className="guided-next-header">
          <strong>
            {labels.priorityHeader}
          </strong>
        </div>

        <div className="guided-next-body">
          <span className="guided-next-icon">
            <DashboardIcon
              name={
                priorityCount > 0
                  ? "alert"
                  : "check"
              }
              size={25}
            />
          </span>

          <div className="guided-next-copy">
            <h2>
              {priorityCount > 0
                ? `${priorityCount} ${labels.priorityTitle}`
                : labels.noPriorityTitle}
            </h2>

            <p>
              {priorityCount > 0
                ? labels.priorityText
                : labels.noPriorityText}
            </p>
          </div>

          <div className="guided-next-meta">
            <div>
              <small>
                {labels.today}
              </small>

              <strong>
                {summary.new_cases_today
                  || 0}{" "}
                {labels.newToday}
              </strong>
            </div>
          </div>

          <button
            type="button"
            className="guided-next-button"
            onClick={() =>
              navigate(
                "/admin/priority-cases"
              )
            }
          >
            {labels.viewPriority}

            <DashboardIcon
              name="arrow"
              size={18}
            />
          </button>
        </div>
      </motion.section>


      {/* =================================================
          PLATFORM OVERVIEW
      ================================================= */}

      <section className="guided-section admin-guided-platform-section">
        <div className="admin-guided-section-heading">
          <div>
            <h2>
              {labels.platform}
            </h2>

            <p>
              {labels.platformText}
            </p>
          </div>
        </div>

        <div className="admin-guided-platform-grid">
          <article className="admin-guided-chart-card">
            <header>
              <span className="admin-guided-panel-icon tone-purple">
                <DashboardIcon
                  name="clock"
                  size={22}
                />
              </span>

              <div>
                <h3>
                  {labels.activity}
                </h3>

                <p>
                  {labels.activityText}
                </p>
              </div>
            </header>

            <div className="admin-guided-week-chart">
              {(
                data?.cases_last_7_days
                || []
              ).map(
                (item) => {
                  const height =
                    Math.max(
                      8,
                      (
                        Number(
                          item.count
                          || 0
                        )
                        / maxDaily
                      )
                      * 100
                    );

                  return (
                    <div
                      className="admin-guided-week-column"
                      key={
                        item.date
                      }
                    >
                      <strong>
                        {item.count}
                      </strong>

                      <div>
                        <motion.span
                          initial={
                            reducedMotion
                              ? false
                              : {
                                  height: 0,
                                }
                          }
                          animate={{
                            height:
                              `${height}%`,
                          }}
                          transition={{
                            duration:
                              0.45,
                          }}
                        />
                      </div>

                      <small>
                        {new Intl.DateTimeFormat(
                          isArabic
                            ? "ar-MA"
                            : "fr-FR",
                          {
                            weekday:
                              "short",
                          }
                        ).format(
                          new Date(
                            `${item.date}T12:00:00`
                          )
                        )}
                      </small>
                    </div>
                  );
                }
              )}
            </div>
          </article>


          <article className="admin-guided-progress-panel">
            <div>
              <span className="admin-guided-panel-icon tone-green">
                <DashboardIcon
                  name="check"
                  size={22}
                />
              </span>

              <div>
                <h3>
                  {labels.actionProgress}
                </h3>

                <p>
                  {summary.completed_action_items
                    || 0}
                  /
                  {summary.total_action_items
                    || 0}{" "}
                  {labels.actionsCompleted}
                </p>
              </div>
            </div>

            <ProgressCircle
              value={
                Number(
                  summary.action_completion_rate
                  || 0
                )
              }
            />

            <div className="admin-guided-mini-stats">
              <div>
                <span>
                  <DashboardIcon
                    name="clip"
                    size={19}
                  />
                </span>

                <div>
                  <small>
                    {labels.evidence}
                  </small>

                  <strong>
                    {summary.total_evidence
                      || 0}
                  </strong>
                </div>
              </div>

              <div>
                <span>
                  <DashboardIcon
                    name="folder"
                    size={19}
                  />
                </span>

                <div>
                  <small>
                    {labels.plans}
                  </small>

                  <strong>
                    {summary.total_action_plans
                      || 0}
                  </strong>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>


      {/* =================================================
          SITUATIONS + LANGUAGES
      ================================================= */}

      <div className="admin-guided-two-column">
        <section className="guided-section admin-guided-intents">
          <div className="admin-guided-section-heading">
            <div>
              <h2>
                {labels.situations}
              </h2>

              <p>
                {labels.situationsText}
              </p>
            </div>
          </div>

          {(
            data?.by_intent
            || []
          ).length > 0 ? (
            <div className="admin-guided-intent-list">
              {data.by_intent.map(
                (
                  item,
                  index
                ) => {
                  const percentage =
                    intentTotal > 0
                      ? Math.round(
                          (
                            Number(
                              item.count
                              || 0
                            )
                            / intentTotal
                          )
                          * 100
                        )
                      : 0;

                  return (
                    <div
                      className="admin-guided-intent-item"
                      key={
                        item.label
                      }
                    >
                      <div>
                        <strong>
                          {item.label}
                        </strong>

                        <span>
                          {item.count}
                        </span>
                      </div>

                      <div className="admin-guided-intent-track">
                        <motion.span
                          className={
                            `tone-${index % 4}`
                          }
                          initial={
                            reducedMotion
                              ? false
                              : {
                                  width: 0,
                                }
                          }
                          animate={{
                            width:
                              `${percentage}%`,
                          }}
                        />
                      </div>

                      <small>
                        {percentage}%
                      </small>
                    </div>
                  );
                }
              )}
            </div>
          ) : (
            <div className="admin-guided-empty">
              {labels.noSituations}
            </div>
          )}
        </section>


        <section className="guided-section admin-guided-language-section">
          <div className="admin-guided-section-heading">
            <div>
              <h2>
                {labels.languages}
              </h2>

              <p>
                FR / AR
              </p>
            </div>
          </div>

          <div className="admin-guided-language-grid">
            {(
              data?.by_language
              || []
            ).map(
              (item) => {
                const percentage =
                  languageTotal > 0
                    ? Math.round(
                        (
                          Number(
                            item.count
                            || 0
                          )
                          / languageTotal
                        )
                        * 100
                      )
                    : 0;

                const name =
                  item.label === "ar"
                    ? labels.arabic
                    : item.label === "fr"
                      ? labels.french
                      : item.label;

                return (
                  <article
                    key={
                      item.label
                    }
                  >
                    <span>
                      {item.label
                        .toUpperCase()}
                    </span>

                    <strong>
                      {percentage}%
                    </strong>

                    <p>
                      {name}
                    </p>
                  </article>
                );
              }
            )}
          </div>
        </section>
      </div>


      {/* =================================================
          RECENT ACTIVITY
      ================================================= */}

      <section className="guided-section admin-guided-recent-section">
        <div className="admin-guided-section-heading">
          <div>
            <h2>
              {labels.recent}
            </h2>

            <p>
              {labels.recentText}
            </p>
          </div>
        </div>

        {(
          data?.recent_activity
          || []
        ).length > 0 ? (
          <div className="admin-guided-recent-list">
            {data.recent_activity.map(
              (
                item,
                index
              ) => (
                <article
                  className="admin-guided-recent-item"
                  key={
                    `${item.created_at}-${index}`
                  }
                >
                  <span className="admin-guided-recent-marker">
                    <DashboardIcon
                      name={
                        item.event_type
                          .includes(
                            "evidence"
                          )
                          ? "clip"
                          : item.event_type
                              .includes(
                                "action"
                              )
                            ? "check"
                            : "folder"
                      }
                      size={20}
                    />
                  </span>

                  <div>
                    <strong>
                      {labels.eventLabels[
                        item.event_type
                      ]
                      || item.event_type}
                    </strong>

                    <p>
                      {item.detected_intent
                        || "—"}
                    </p>
                  </div>

                  <time>
                    {formatDate(
                      item.created_at,
                      language
                    )}
                  </time>
                </article>
              )
            )}
          </div>
        ) : (
          <div className="admin-guided-empty">
            {labels.noActivity}
          </div>
        )}
      </section>


      {/* =================================================
          QUICK ACCESS
      ================================================= */}

      <section className="guided-section admin-guided-quick-section">
        <h2>
          {labels.quick}
        </h2>

        <div className="admin-guided-quick-grid">
          <QuickAdminCard
            icon="spark"
            tone="purple"
            title={
              labels.statistics
            }
            description={
              labels.statisticsText
            }
            onClick={() =>
              navigate(
                "/admin/statistics"
              )
            }
            reducedMotion={
              reducedMotion
            }
          />

          <QuickAdminCard
            icon="folder"
            tone="blue"
            title={
              labels.cases
            }
            description={
              labels.casesText
            }
            onClick={() =>
              navigate(
                "/admin/cases"
              )
            }
            reducedMotion={
              reducedMotion
            }
          />

          <QuickAdminCard
            icon="alert"
            tone="orange"
            title={
              labels.priority
            }
            description={
              labels.priorityQuickText
            }
            onClick={() =>
              navigate(
                "/admin/priority-cases"
              )
            }
            reducedMotion={
              reducedMotion
            }
          />

          <QuickAdminCard
            icon="clip"
            tone="purple"
            title={
              labels.documents
            }
            description={
              labels.documentsText
            }
            onClick={() =>
              navigate(
                "/admin/document-base"
              )
            }
            reducedMotion={
              reducedMotion
            }
          />
        </div>
      </section>
    </motion.div>
  );
}


export default Overview;