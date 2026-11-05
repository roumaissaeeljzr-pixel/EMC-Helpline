import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  motion,
  useReducedMotion,
} from "framer-motion";

import {
  useLanguage,
} from "../../context/LanguageContext.jsx";

import {
  DashboardIcon,
  ProgressCircle,
} from "../../components/dashboard/DashboardComponents.jsx";

import "../Dashboard.css";
import "./Statistics.css";


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


const PERIODS = [
  7,
  30,
  90,
];


const COPY = {
  fr: {
    kicker:
      "Analyse de la plateforme",

    title:
      "Statistiques",

    intro:
      "Analysez les dossiers, les situations détectées, les langues utilisées et la progression des actions à partir des données réellement enregistrées.",

    period:
      "Période",

    days:
      "jours",

    cases:
      "Dossiers",

    periodCases:
      "sur la période",

    victims:
      "Victimes inscrites",

    evidence:
      "Preuves enregistrées",

    emergency:
      "Cas d’urgence",

    activeEmergency:
      "urgences actives",

    noEmergency:
      "Aucune urgence active",

    evolution:
      "Évolution des dossiers",

    evolutionText:
      "Nombre de nouveaux dossiers créés au cours de la période sélectionnée.",

    vsPrevious:
      "par rapport à la période précédente",

    intentions:
      "Répartition par situation",

    intentionsText:
      "Principales intentions détectées dans les dossiers.",

    languages:
      "Répartition par langue",

    french:
      "Français",

    arabic:
      "Arabe",

    status:
      "État des dossiers",

    active:
      "Actifs",

    closed:
      "Clôturés",

    evidenceTypes:
      "Types de preuves",

    screenshot:
      "Captures d’écran",

    file:
      "Fichiers",

    link:
      "Liens",

    note:
      "Notes",

    actionProgress:
      "Progression des actions",

    completed:
      "actions terminées",

    plans:
      "Plans d’action",

    noData:
      "Aucune donnée disponible pour le moment.",

    loading:
      "Chargement des statistiques...",

    error:
      "Impossible de charger les statistiques.",

    retry:
      "Réessayer",

    increase:
      "Hausse",

    decrease:
      "Baisse",

    stable:
      "Stable",

    newActivity:
      "Nouvelle activité",
  },

  ar: {
    kicker:
      "تحليل المنصة",

    title:
      "الإحصائيات",

    intro:
      "حلّل الملفات والحالات المكتشفة واللغات المستخدمة وتقدم الإجراءات انطلاقًا من البيانات المسجلة فعليًا.",

    period:
      "الفترة",

    days:
      "أيام",

    cases:
      "الملفات",

    periodCases:
      "خلال الفترة",

    victims:
      "الضحايا المسجلون",

    evidence:
      "الأدلة المسجلة",

    emergency:
      "الحالات الطارئة",

    activeEmergency:
      "حالات طارئة نشطة",

    noEmergency:
      "لا توجد حالة طارئة نشطة",

    evolution:
      "تطور الملفات",

    evolutionText:
      "عدد الملفات الجديدة التي تم إنشاؤها خلال الفترة المحددة.",

    vsPrevious:
      "مقارنة بالفترة السابقة",

    intentions:
      "التوزيع حسب الحالة",

    intentionsText:
      "أهم أنواع الحالات المكتشفة داخل الملفات.",

    languages:
      "التوزيع حسب اللغة",

    french:
      "الفرنسية",

    arabic:
      "العربية",

    status:
      "حالة الملفات",

    active:
      "نشطة",

    closed:
      "مغلقة",

    evidenceTypes:
      "أنواع الأدلة",

    screenshot:
      "لقطات الشاشة",

    file:
      "ملفات",

    link:
      "روابط",

    note:
      "ملاحظات",

    actionProgress:
      "تقدم الإجراءات",

    completed:
      "إجراءات منجزة",

    plans:
      "خطط العمل",

    noData:
      "لا توجد بيانات متاحة حاليًا.",

    loading:
      "جارٍ تحميل الإحصائيات...",

    error:
      "تعذر تحميل الإحصائيات.",

    retry:
      "إعادة المحاولة",

    increase:
      "ارتفاع",

    decrease:
      "انخفاض",

    stable:
      "مستقر",

    newActivity:
      "نشاط جديد",
  },
};


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
      className={`statistics-summary-card tone-${tone}`}
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
      <span>
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


function Statistics() {
  const {
    language,
  } = useLanguage();

  const reducedMotion =
    useReducedMotion();

  const isArabic =
    language === "ar";

  const labels =
    COPY[
      isArabic
        ? "ar"
        : "fr"
    ];

  const [
    period,
    setPeriod,
  ] = useState(30);

  const [
    data,
    setData,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");


  const loadStatistics =
    useCallback(
      async () => {
        setLoading(true);
        setError("");

        try {
          const response =
            await fetch(
              `${API_BASE_URL}/admin/statistics?days=${period}`,
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

          setData(payload);
        } catch (loadError) {
          console.error(
            "Admin Statistics:",
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
        period,
      ]
    );


  useEffect(
    () => {
      loadStatistics();
    },
    [
      loadStatistics,
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
            data?.daily_cases
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


  const visibleDaily =
    useMemo(
      () => {
        const points =
          data?.daily_cases
          || [];

        if (points.length <= 14) {
          return points;
        }

        const step =
          Math.ceil(
            points.length / 14
          );

        return points.filter(
          (
            _,
            index
          ) =>
            index % step === 0
            || index === points.length - 1
        );
      },
      [
        data,
      ]
    );


  const hasComparablePreviousPeriod =
    Number(
      summary.previous_period_cases
      || 0
    ) > 0;

  const hasNewActivityWithoutBaseline =
    !hasComparablePreviousPeriod
    && Number(
      summary.period_cases
      || 0
    ) > 0;

  const change =
    summary.period_change_percent == null
      ? 0
      : Number(
          summary.period_change_percent
          || 0
        );

  const changeLabel =
    hasNewActivityWithoutBaseline
      ? labels.newActivity
      : change > 0
        ? labels.increase
        : change < 0
          ? labels.decrease
          : labels.stable;


  if (loading) {
    return (
      <div className="guided-dashboard admin-statistics-page">
        <section className="statistics-loading">
          <span className="statistics-spinner" />

          <h2>
            {labels.loading}
          </h2>
        </section>
      </div>
    );
  }


  if (error) {
    return (
      <div className="guided-dashboard admin-statistics-page">
        <section className="guided-no-case statistics-error">
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
              loadStatistics
            }
          >
            {labels.retry}
          </button>
        </section>
      </div>
    );
  }


  return (
    <motion.div
      key={
        `${language}-${period}`
      }
      className="guided-dashboard admin-statistics-page"
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
    >
      {/* =================================================
          HEADER
      ================================================= */}

      <section className="statistics-heading">
        <div>
          <span className="guided-welcome-kicker">
            {labels.kicker}
          </span>

          <h1>
            {labels.title}
          </h1>

          <p>
            {labels.intro}
          </p>
        </div>

        <div className="statistics-period">
          <small>
            {labels.period}
          </small>

          <div>
            {PERIODS.map(
              (days) => (
                <button
                  type="button"
                  key={days}
                  className={
                    period === days
                      ? "active"
                      : ""
                  }
                  onClick={() =>
                    setPeriod(days)
                  }
                >
                  {days}{" "}
                  {labels.days}
                </button>
              )
            )}
          </div>
        </div>
      </section>


      {/* =================================================
          SUMMARY
      ================================================= */}

      <section className="statistics-summary-grid">
        <SummaryCard
          icon="folder"
          tone="purple"
          label={
            labels.cases
          }
          value={
            summary.total_cases
            || 0
          }
          detail={
            `${summary.period_cases || 0} ${labels.periodCases}`
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="shield"
          tone="blue"
          label={
            labels.victims
          }
          value={
            summary.total_victims
            || 0
          }
          detail={
            `${summary.active_victims || 0} ${labels.active}`
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="clip"
          tone="green"
          label={
            labels.evidence
          }
          value={
            summary.total_evidence
            || 0
          }
          detail={
            `${summary.total_action_plans || 0} ${labels.plans}`
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="alert"
          tone="orange"
          label={
            labels.emergency
          }
          value={
            summary.active_emergency_cases
            || 0
          }
          detail={
            Number(
              summary.active_emergency_cases
              || 0
            ) > 0
              ? `${summary.active_emergency_cases || 0} ${labels.activeEmergency}`
              : labels.noEmergency
          }
          reducedMotion={
            reducedMotion
          }
        />
      </section>


      {/* =================================================
          EVOLUTION
      ================================================= */}

      <section className="guided-section statistics-evolution-section">
        <div className="statistics-section-heading">
          <div>
            <h2>
              {labels.evolution}
            </h2>

            <p>
              {labels.evolutionText}
            </p>
          </div>

          <div
            className={
              `statistics-change ${
                hasNewActivityWithoutBaseline
                  ? "stable"
                  : change > 0
                    ? "up"
                    : change < 0
                      ? "down"
                      : "stable"
              }`
            }
          >
            <strong>
              {hasNewActivityWithoutBaseline
                ? changeLabel
                : `${change > 0 ? "+" : ""}${change}%`}
            </strong>

            <small>
              {hasNewActivityWithoutBaseline
                ? labels.vsPrevious
                : `${changeLabel} — ${labels.vsPrevious}`}
            </small>
          </div>
        </div>

        <div className="statistics-bar-chart">
          {visibleDaily.map(
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
                  className="statistics-bar-column"
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
                          0.4,
                      }}
                    />
                  </div>

                  <small>
                    {new Intl.DateTimeFormat(
                      isArabic
                        ? "ar-MA"
                        : "fr-FR",
                      {
                        day:
                          "2-digit",

                        month:
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
      </section>


      {/* =================================================
          INTENTS + PROGRESS
      ================================================= */}

      <div className="statistics-two-column">
        <section className="guided-section">
          <div className="statistics-section-heading">
            <div>
              <h2>
                {labels.intentions}
              </h2>

              <p>
                {labels.intentionsText}
              </p>
            </div>
          </div>

          {(
            data?.by_intent
            || []
          ).length > 0 ? (
            <div className="statistics-intent-list">
              {data.by_intent.map(
                (
                  item,
                  index
                ) => (
                  <div
                    className="statistics-intent-item"
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

                    <div className="statistics-intent-track">
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
                            `${item.percentage}%`,
                        }}
                      />
                    </div>

                    <small>
                      {item.percentage}%
                    </small>
                  </div>
                )
              )}
            </div>
          ) : (
            <div className="statistics-empty">
              {labels.noData}
            </div>
          )}
        </section>


        <section className="guided-section statistics-progress-section">
          <div className="statistics-section-heading">
            <div>
              <h2>
                {labels.actionProgress}
              </h2>

              <p>
                {summary.completed_action_items
                  || 0}
                /
                {summary.total_action_items
                  || 0}{" "}
                {labels.completed}
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

          <div className="statistics-progress-meta">
            <span>
              <DashboardIcon
                name="folder"
                size={20}
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
        </section>
      </div>


      {/* =================================================
          LANGUAGE + STATUS + EVIDENCE
      ================================================= */}

      <div className="statistics-three-column">
        <section className="guided-section statistics-small-panel">
          <h2>
            {labels.languages}
          </h2>

          <div className="statistics-language-grid">
            {(
              data?.by_language
              || []
            ).map(
              (item) => (
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
                    {item.percentage}%
                  </strong>

                  <p>
                    {item.label === "fr"
                      ? labels.french
                      : item.label === "ar"
                        ? labels.arabic
                        : item.label}
                  </p>
                </article>
              )
            )}
          </div>
        </section>


        <section className="guided-section statistics-small-panel">
          <h2>
            {labels.status}
          </h2>

          <div className="statistics-status-list">
            {(
              data?.by_status
              || []
            ).map(
              (item) => (
                <div
                  key={
                    item.label
                  }
                >
                  <span
                    className={
                      item.label === "active"
                        ? "active"
                        : "closed"
                    }
                  />

                  <strong>
                    {item.label === "active"
                      ? labels.active
                      : item.label === "closed"
                        ? labels.closed
                        : item.label}
                  </strong>

                  <em>
                    {item.count}
                  </em>

                  <small>
                    {item.percentage}%
                  </small>
                </div>
              )
            )}
          </div>
        </section>


        <section className="guided-section statistics-small-panel">
          <h2>
            {labels.evidenceTypes}
          </h2>

          <div className="statistics-evidence-list">
            {(
              data?.by_evidence_type
              || []
            ).map(
              (item) => {
                const translated =
                  {
                    screenshot:
                      labels.screenshot,

                    file:
                      labels.file,

                    link:
                      labels.link,

                    note:
                      labels.note,
                  }[
                    item.label
                  ]
                  || item.label;

                return (
                  <div
                    key={
                      item.label
                    }
                  >
                    <span>
                      <DashboardIcon
                        name="clip"
                        size={18}
                      />
                    </span>

                    <strong>
                      {translated}
                    </strong>

                    <em>
                      {item.count}
                    </em>

                    <small>
                      {item.percentage}%
                    </small>
                  </div>
                );
              }
            )}
          </div>
        </section>
      </div>
    </motion.div>
  );
}


export default Statistics;