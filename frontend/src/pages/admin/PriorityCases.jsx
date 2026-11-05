import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AnimatePresence,
  motion,
  useReducedMotion,
} from "framer-motion";

import {
  useNavigate,
} from "react-router-dom";

import {
  useLanguage,
} from "../../context/LanguageContext.jsx";

import {
  DashboardIcon,
} from "../../components/dashboard/DashboardComponents.jsx";

import "../Dashboard.css";
import "./PriorityCases.css";


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


const REFRESH_INTERVAL_MS =
  60000;


const COPY = {
  fr: {
    kicker:
      "Surveillance prioritaire",

    title:
      "Cas prioritaires",

    intro:
      "Cette vue regroupe uniquement les dossiers actifs signalés comme urgents. Aucun score de priorité artificiel n’est ajouté : la priorité repose sur le signalement d’urgence enregistré dans le dossier.",

    urgentCases:
      "Urgences actives",

    withEvidence:
      "Avec preuves",

    withoutPlan:
      "Sans plan d’action",

    oldest:
      "Plus ancien",

    days:
      "jour(s)",

    live:
      "Surveillance active",

    autoRefresh:
      "Actualisation automatique toutes les 60 secondes",

    refresh:
      "Actualiser",

    lastRefresh:
      "Dernière actualisation",

    prioritySection:
      "À traiter en priorité",

    priorityText:
      "Consultez les dossiers urgents encore actifs et ouvrez leur détail pour vérifier la situation, les preuves et l’avancement du plan d’action.",

    case:
      "Dossier",

    victim:
      "Victime",

    fullName:
      "Nom complet",

    emcId:
      "ID EMC",

    username:
      "Nom d’utilisateur",

    phone:
      "Téléphone",

    cin:
      "CIN",

    email:
      "E-mail",

    birthDate:
      "Date de naissance",

    identity:
      "Identité",

    identityComplete:
      "Identité renseignée",

    identityIncomplete:
      "Identité incomplète",

    situation:
      "Situation détectée",

    evidence:
      "Preuves",

    progress:
      "Plan d’action",

    created:
      "Créé le",

    updated:
      "Mis à jour",

    view:
      "Consulter",

    noPlan:
      "Aucun plan",

    noCasesTitle:
      "Aucun cas prioritaire actif",

    noCasesText:
      "Aucun dossier actif n’est actuellement marqué comme urgent. Cette page se mettra à jour automatiquement lorsqu’une nouvelle urgence sera enregistrée.",

    allCases:
      "Voir tous les dossiers",

    loading:
      "Chargement des cas prioritaires...",

    error:
      "Impossible de charger les cas prioritaires.",

    retry:
      "Réessayer",

    detailTitle:
      "Détail du cas prioritaire",

    emergency:
      "Urgence active",

    description:
      "Situation déclarée",

    language:
      "Langue",

    status:
      "Statut",

    active:
      "Actif",

    actionProgress:
      "Progression du plan",

    completedActions:
      "actions terminées",

    close:
      "Fermer",

    openCases:
      "Ouvrir la gestion des dossiers",

    unknown:
      "Non renseigné",
  },

  ar: {
    kicker:
      "المراقبة ذات الأولوية",

    title:
      "الحالات ذات الأولوية",

    intro:
      "تعرض هذه الصفحة فقط الملفات النشطة المصنفة كحالات طارئة. لا يتم إنشاء أي درجة أولوية اصطناعية، بل تعتمد الأولوية على إشارة الطوارئ المسجلة داخل الملف.",

    urgentCases:
      "الطوارئ النشطة",

    withEvidence:
      "مع أدلة",

    withoutPlan:
      "دون خطة عمل",

    oldest:
      "الأقدم",

    days:
      "يوم",

    live:
      "مراقبة نشطة",

    autoRefresh:
      "تحديث تلقائي كل 60 ثانية",

    refresh:
      "تحديث",

    lastRefresh:
      "آخر تحديث",

    prioritySection:
      "للمعالجة بالأولوية",

    priorityText:
      "راجع الملفات الطارئة النشطة وافتح تفاصيلها للتحقق من الحالة والأدلة وتقدم خطة العمل.",

    case:
      "الملف",

    victim:
      "الضحية",

    fullName:
      "الاسم الكامل",

    emcId:
      "معرف EMC",

    username:
      "اسم المستخدم",

    phone:
      "الهاتف",

    cin:
      "رقم البطاقة الوطنية",

    email:
      "البريد الإلكتروني",

    birthDate:
      "تاريخ الميلاد",

    identity:
      "الهوية",

    identityComplete:
      "الهوية مكتملة",

    identityIncomplete:
      "الهوية غير مكتملة",

    situation:
      "الحالة المكتشفة",

    evidence:
      "الأدلة",

    progress:
      "خطة العمل",

    created:
      "تاريخ الإنشاء",

    updated:
      "آخر تحديث",

    view:
      "عرض",

    noPlan:
      "لا توجد خطة",

    noCasesTitle:
      "لا توجد حالة ذات أولوية نشطة",

    noCasesText:
      "لا يوجد حاليًا ملف نشط مصنف كحالة طارئة. سيتم تحديث هذه الصفحة تلقائيًا عند تسجيل حالة طارئة جديدة.",

    allCases:
      "عرض كل الملفات",

    loading:
      "جارٍ تحميل الحالات ذات الأولوية...",

    error:
      "تعذر تحميل الحالات ذات الأولوية.",

    retry:
      "إعادة المحاولة",

    detailTitle:
      "تفاصيل الحالة ذات الأولوية",

    emergency:
      "حالة طارئة نشطة",

    description:
      "الحالة المصرح بها",

    language:
      "اللغة",

    status:
      "الحالة",

    active:
      "نشط",

    actionProgress:
      "تقدم الخطة",

    completedActions:
      "إجراءات منجزة",

    close:
      "إغلاق",

    openCases:
      "فتح إدارة الملفات",

    unknown:
      "غير محدد",
  },
};


const ARABIC_INTENTS = {
  "Cyberharcèlement":
    "التحرش الإلكتروني",

  "Sextorsion":
    "الابتزاز الجنسي",

  "Piratage de compte":
    "اختراق الحساب",

  "Divulgation de données personnelles (Doxing)":
    "الكشف عن البيانات الشخصية",

  "Conservation des preuves":
    "الاحتفاظ بالأدلة",

  "Informations juridiques":
    "معلومات قانونية",

  "Usurpation d'identité":
    "انتحال الهوية",

  "Diffusion non consentie d'images":
    "نشر الصور دون موافقة",

  "Signalement":
    "الإبلاغ",

  "Situation d'urgence":
    "حالة طارئة",

  "Accompagnement de la victime":
    "مرافقة الضحية",
};


function displayIntent(
  value,
  language,
) {
  if (!value) {
    return "—";
  }

  if (
    language === "ar"
  ) {
    return (
      ARABIC_INTENTS[
        value
      ]
      || value
    );
  }

  return value;
}


function shortId(
  value,
) {
  if (!value) {
    return "—";
  }

  return value
    .split("-")[0]
    .toUpperCase();
}


function formatDate(
  value,
  language,
  withTime = false,
) {
  if (!value) {
    return "—";
  }

  const options = {
    day:
      "2-digit",

    month:
      "short",

    year:
      "numeric",
  };

  if (withTime) {
    options.hour =
      "2-digit";

    options.minute =
      "2-digit";
  }

  return new Intl.DateTimeFormat(
    language === "ar"
      ? "ar-MA"
      : "fr-FR",
    options
  ).format(
    new Date(value)
  );
}


function formatBirthDate(
  value,
  language,
) {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat(
    language === "ar"
      ? "ar-MA"
      : "fr-FR",
    {
      day:
        "2-digit",

      month:
        "2-digit",

      year:
        "numeric",
    }
  ).format(
    new Date(value)
  );
}


function getAgeInDays(
  value,
) {
  if (!value) {
    return 0;
  }

  const created =
    new Date(value);

  const now =
    new Date();

  const difference =
    now.getTime()
    - created.getTime();

  return Math.max(
    0,
    Math.floor(
      difference
      / (
        1000
        * 60
        * 60
        * 24
      )
    )
  );
}


function SummaryCard({
  icon,
  tone,
  label,
  value,
  reducedMotion,
}) {
  return (
    <motion.article
      className={`priority-summary-card tone-${tone}`}
      initial={
        reducedMotion
          ? false
          : {
              opacity: 0,
              y: 8,
            }
      }
      animate={{
        opacity: 1,
        y: 0,
      }}
    >
      <span>
        <DashboardIcon
          name={icon}
          size={24}
        />
      </span>

      <div>
        <small>
          {label}
        </small>

        <strong>
          {value}
        </strong>
      </div>
    </motion.article>
  );
}


function PriorityCases() {
  const navigate =
    useNavigate();

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

  const [
    lastRefresh,
    setLastRefresh,
  ] = useState(null);

  const [
    selectedCase,
    setSelectedCase,
  ] = useState(null);

  const [
    detailLoading,
    setDetailLoading,
  ] = useState(false);

  const [
    detailError,
    setDetailError,
  ] = useState("");


  const loadPriorityCases =
    useCallback(
      async (
        silent = false
      ) => {
        if (!silent) {
          setLoading(true);
        }

        setError("");

        try {
          const response =
            await fetch(
              `${API_BASE_URL}/admin/cases?status=active&emergency=true`,
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
          setLastRefresh(
            new Date()
          );
        } catch (
          loadError
        ) {
          console.error(
            "Priority cases:",
            loadError
          );

          setError(
            loadError.message
            || labels.error
          );
        } finally {
          if (!silent) {
            setLoading(false);
          }
        }
      },
      [
        labels.error,
      ]
    );


  useEffect(
    () => {
      loadPriorityCases();

      const interval =
        window.setInterval(
          () => {
            loadPriorityCases(
              true
            );
          },
          REFRESH_INTERVAL_MS
        );

      return () =>
        window.clearInterval(
          interval
        );
    },
    [
      loadPriorityCases,
    ]
  );


  const items =
    data?.items
    || [];


  const withEvidence =
    useMemo(
      () =>
        items.filter(
          (item) =>
            Number(
              item.evidence_count
              || 0
            ) > 0
        ).length,
      [
        items,
      ]
    );


  const withoutPlan =
    useMemo(
      () =>
        items.filter(
          (item) =>
            !item.has_action_plan
        ).length,
      [
        items,
      ]
    );


  const oldestDays =
    useMemo(
      () => {
        if (
          items.length === 0
        ) {
          return 0;
        }

        return Math.max(
          ...items.map(
            (item) =>
              getAgeInDays(
                item.created_at
              )
          )
        );
      },
      [
        items,
      ]
    );


  const openCase =
    async (
      caseId
    ) => {
      setDetailLoading(true);
      setDetailError("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/admin/cases/${caseId}`,
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

        setSelectedCase(
          payload
        );
      } catch (
        loadDetailError
      ) {
        setDetailError(
          loadDetailError.message
          || labels.error
        );
      } finally {
        setDetailLoading(false);
      }
    };


  const closeDetail =
    () => {
      setSelectedCase(null);
      setDetailError("");
    };


  if (
    loading
    && !data
  ) {
    return (
      <div className="guided-dashboard priority-cases-page">
        <section className="priority-loading">
          <span className="priority-spinner" />

          <h2>
            {labels.loading}
          </h2>
        </section>
      </div>
    );
  }


  if (
    error
    && !data
  ) {
    return (
      <div className="guided-dashboard priority-cases-page">
        <section className="guided-no-case priority-error">
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
            onClick={() =>
              loadPriorityCases()
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
      key={language}
      className="guided-dashboard priority-cases-page"
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

      <section className="priority-heading">
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

        <div className="priority-live-card">
          <span className="priority-live-dot" />

          <div>
            <strong>
              {labels.live}
            </strong>

            <small>
              {labels.autoRefresh}
            </small>
          </div>

          <button
            type="button"
            onClick={() =>
              loadPriorityCases(
                true
              )
            }
          >
            {labels.refresh}
          </button>
        </div>
      </section>


      {/* =================================================
          SUMMARY
      ================================================= */}

      <section className="priority-summary-grid">
        <SummaryCard
          icon="alert"
          tone="coral"
          label={
            labels.urgentCases
          }
          value={
            items.length
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="clip"
          tone="purple"
          label={
            labels.withEvidence
          }
          value={
            withEvidence
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="folder"
          tone="blue"
          label={
            labels.withoutPlan
          }
          value={
            withoutPlan
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="clock"
          tone="orange"
          label={
            labels.oldest
          }
          value={
            items.length > 0
              ? `${oldestDays} ${labels.days}`
              : "—"
          }
          reducedMotion={
            reducedMotion
          }
        />
      </section>


      {/* =================================================
          PRIORITY AREA
      ================================================= */}

      <section className="guided-section priority-main-section">
        <div className="priority-section-heading">
          <div>
            <h2>
              {labels.prioritySection}
            </h2>

            <p>
              {labels.priorityText}
            </p>
          </div>

          <div className="priority-refresh-meta">
            {lastRefresh && (
              <>
                <small>
                  {labels.lastRefresh}
                </small>

                <strong>
                  {formatDate(
                    lastRefresh,
                    language,
                    true
                  )}
                </strong>
              </>
            )}
          </div>
        </div>


        {items.length === 0 ? (
          <div className="priority-empty">
            <span>
              <DashboardIcon
                name="shield"
                size={42}
              />
            </span>

            <h3>
              {labels.noCasesTitle}
            </h3>

            <p>
              {labels.noCasesText}
            </p>

            <button
              type="button"
              onClick={() =>
                navigate(
                  "/admin/cases"
                )
              }
            >
              {labels.allCases}

              <DashboardIcon
                name="arrow"
                size={17}
              />
            </button>
          </div>
        ) : (
          <div className="priority-list">
            {items.map(
              (item) => (
                <motion.article
                  className="priority-case-card"
                  key={
                    item.id
                  }
                  initial={
                    reducedMotion
                      ? false
                      : {
                          opacity: 0,
                          y: 8,
                        }
                  }
                  animate={{
                    opacity: 1,
                    y: 0,
                  }}
                >
                  <div className="priority-case-alert">
                    <DashboardIcon
                      name="alert"
                      size={22}
                    />

                    <strong>
                      {labels.emergency}
                    </strong>
                  </div>

                  <div className="priority-case-main">
                    <div className="priority-case-reference">
                      <span>
                        <DashboardIcon
                          name="folder"
                          size={18}
                        />
                      </span>

                      <div>
                        <small>
                          {labels.case}
                        </small>

                        <strong>
                          #{shortId(
                            item.id
                          )}
                        </strong>
                      </div>
                    </div>

                    <div className="priority-case-info">
                      <div>
                        <small>
                          {labels.victim}
                        </small>

                        <strong>
                          {item.victim_full_name
                            || item.victim_username
                            || labels.unknown}
                        </strong>

                        <span
                          style={{
                            display: "grid",
                            gap: 2,
                            marginTop: 4,
                            fontSize: 12,
                            opacity: 0.72,
                          }}
                        >
                          <span>
                            {labels.emcId}
                            {" : "}
                            {item.victim_emc_id
                              || "—"}
                          </span>

                          {item.victim_phone && (
                            <span dir="ltr">
                              {item.victim_phone}
                            </span>
                          )}

                          {item.victim_cin_masked && (
                            <span dir="ltr">
                              {labels.cin}
                              {" : "}
                              {item.victim_cin_masked}
                            </span>
                          )}
                        </span>
                      </div>

                      <div>
                        <small>
                          {labels.situation}
                        </small>

                        <strong>
                          {displayIntent(
                            item.detected_intent,
                            language
                          )}
                        </strong>
                      </div>
                    </div>

                    <div className="priority-case-stats">
                      <div>
                        <small>
                          {labels.evidence}
                        </small>

                        <strong>
                          {item.evidence_count}
                        </strong>
                      </div>

                      <div>
                        <small>
                          {labels.progress}
                        </small>

                        <strong>
                          {item.has_action_plan
                            ? `${item.completed_actions}/${item.total_actions}`
                            : labels.noPlan}
                        </strong>
                      </div>

                      <div>
                        <small>
                          {labels.created}
                        </small>

                        <strong>
                          {formatDate(
                            item.created_at,
                            language
                          )}
                        </strong>
                      </div>
                    </div>

                    {item.has_action_plan && (
                      <div className="priority-case-progress">
                        <div>
                          <span
                            style={{
                              width:
                                `${item.action_progress}%`,
                            }}
                          />
                        </div>

                        <small>
                          {Math.round(
                            item.action_progress
                          )}%
                        </small>
                      </div>
                    )}
                  </div>

                  <button
                    type="button"
                    className="priority-case-open"
                    onClick={() =>
                      openCase(
                        item.id
                      )
                    }
                  >
                    {labels.view}

                    <DashboardIcon
                      name="arrow"
                      size={17}
                    />
                  </button>
                </motion.article>
              )
            )}
          </div>
        )}
      </section>


      {/* =================================================
          DETAIL MODAL
      ================================================= */}

      <AnimatePresence>
        {(
          selectedCase
          || detailLoading
        ) && (
          <>
            <motion.button
              type="button"
              className="priority-modal-backdrop"
              aria-label={
                labels.close
              }
              initial={{
                opacity: 0,
              }}
              animate={{
                opacity: 1,
              }}
              exit={{
                opacity: 0,
              }}
              onClick={
                closeDetail
              }
            />

            <motion.aside
              className="priority-modal"
              initial={
                reducedMotion
                  ? false
                  : {
                      opacity: 0,
                      x:
                        isArabic
                          ? -28
                          : 28,
                    }
              }
              animate={{
                opacity: 1,
                x: 0,
              }}
              exit={{
                opacity: 0,
                x:
                  isArabic
                    ? -28
                    : 28,
              }}
            >
              {detailLoading
                && !selectedCase ? (
                <div className="priority-modal-loading">
                  <span className="priority-spinner" />

                  <p>
                    {labels.loading}
                  </p>
                </div>
              ) : selectedCase ? (
                <>
                  <header className="priority-modal-header">
                    <div>
                      <span className="guided-welcome-kicker">
                        {labels.detailTitle}
                      </span>

                      <h2>
                        #{shortId(
                          selectedCase.id
                        )}
                      </h2>
                    </div>

                    <button
                      type="button"
                      onClick={
                        closeDetail
                      }
                    >
                      ×
                    </button>
                  </header>

                  <div className="priority-modal-body">
                    <div className="priority-modal-emergency">
                      <DashboardIcon
                        name="alert"
                        size={20}
                      />

                      <strong>
                        {labels.emergency}
                      </strong>
                    </div>

                    <div className="priority-modal-grid">
                      <div>
                        <small>
                          {labels.victim}
                        </small>

                        <strong>
                          {selectedCase.victim_full_name
                            || selectedCase.victim_username
                            || labels.unknown}
                        </strong>
                      </div>

                      <div>
                        <small>
                          {labels.situation}
                        </small>

                        <strong>
                          {displayIntent(
                            selectedCase.detected_intent,
                            language
                          )}
                        </strong>
                      </div>

                      <div>
                        <small>
                          {labels.language}
                        </small>

                        <strong>
                          {selectedCase.language
                            ? selectedCase.language.toUpperCase()
                            : labels.unknown}
                        </strong>
                      </div>

                      <div>
                        <small>
                          {labels.status}
                        </small>

                        <strong>
                          {labels.active}
                        </strong>
                      </div>
                    </div>

                    <section className="priority-modal-section">
                      <h3>
                        {labels.identity}
                      </h3>

                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns:
                            "repeat(2, minmax(0, 1fr))",
                          gap: 10,
                          marginTop: 10,
                        }}
                      >
                        {[
                          [
                            labels.fullName,
                            selectedCase.victim_full_name
                              || labels.unknown,
                          ],
                          [
                            labels.emcId,
                            selectedCase.victim_emc_id
                              || "—",
                          ],
                          [
                            labels.username,
                            selectedCase.victim_username
                              || "—",
                          ],
                          [
                            labels.phone,
                            selectedCase.victim_phone
                              || "—",
                          ],
                          [
                            labels.cin,
                            selectedCase.victim_cin
                              || selectedCase.victim_cin_masked
                              || "—",
                          ],
                          [
                            labels.email,
                            selectedCase.victim_email
                              || "—",
                          ],
                          [
                            labels.birthDate,
                            formatBirthDate(
                              selectedCase.victim_date_of_birth,
                              language
                            ),
                          ],
                          [
                            labels.identity,
                            selectedCase.victim_identity_complete
                              ? labels.identityComplete
                              : labels.identityIncomplete,
                          ],
                        ].map(
                          ([label, value]) => (
                            <div
                              key={label}
                              style={{
                                padding: "11px 12px",
                                border:
                                  "1px solid rgba(112,72,184,0.12)",
                                borderRadius: 12,
                                background:
                                  "rgba(112,72,184,0.035)",
                              }}
                            >
                              <small
                                style={{
                                  display: "block",
                                  opacity: 0.66,
                                  marginBottom: 4,
                                }}
                              >
                                {label}
                              </small>

                              <strong
                                style={{
                                  display: "block",
                                  overflowWrap: "anywhere",
                                }}
                              >
                                {value}
                              </strong>
                            </div>
                          )
                        )}
                      </div>
                    </section>

                    <section className="priority-modal-section">
                      <h3>
                        {labels.description}
                      </h3>

                      <p>
                        {selectedCase.description}
                      </p>
                    </section>

                    <section className="priority-modal-metrics">
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
                            {selectedCase.evidence_count}
                          </strong>
                        </div>
                      </div>

                      <div>
                        <span>
                          <DashboardIcon
                            name="check"
                            size={19}
                          />
                        </span>

                        <div>
                          <small>
                            {labels.actionProgress}
                          </small>

                          <strong>
                            {selectedCase.has_action_plan
                              ? `${selectedCase.completed_actions}/${selectedCase.total_actions} ${labels.completedActions}`
                              : labels.noPlan}
                          </strong>
                        </div>
                      </div>
                    </section>

                    <button
                      type="button"
                      className="priority-open-cases-button"
                      onClick={() =>
                        navigate(
                          "/admin/cases"
                        )
                      }
                    >
                      {labels.openCases}

                      <DashboardIcon
                        name="arrow"
                        size={17}
                      />
                    </button>

                    {detailError && (
                      <div className="priority-detail-error">
                        {detailError}
                      </div>
                    )}
                  </div>
                </>
              ) : null}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  );
}


export default PriorityCases;