import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useLanguage,
} from "../context/LanguageContext.jsx";

import "./History.css";


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


const ARABIC_INTENT_LABELS = {

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


const LABELS = {

  fr: {

    title:
      "Historique",

    subtitle:
      "Retrouvez les principales actions effectuées dans vos dossiers.",

    allCases:
      "Tous les dossiers",

    selectCase:
      "Afficher le dossier",

    loading:
      "Chargement de l'historique...",

    loadingCases:
      "Chargement des dossiers...",

    emptyTitle:
      "Aucun événement",

    emptyText:
      "Aucune activité n'a encore été enregistrée pour ce dossier.",

    error:
      "Impossible de charger l'historique.",

    retry:
      "Réessayer",

    events:
      "événement(s)",

    caseLabel:
      "Dossier",

    unknownCase:
      "Dossier",

    statusActive:
      "Actif",

    statusClosed:
      "Fermé",

    types: {
      screenshot:
        "Capture d'écran",

      file:
        "Fichier",

      link:
        "Lien",

      note:
        "Note",
    },

    eventTitles: {

      case_created:
        "Dossier créé",

      action_plan_generated:
        "Plan d'action généré",

      action_completed:
        "Action terminée",

      action_reopened:
        "Action rouverte",

      evidence_added:
        "Preuve ajoutée",

      evidence_deleted:
        "Preuve supprimée",

      case_viewed_by_admin:
        "Votre dossier a été consulté par l’équipe EMC",

      case_exported:
        "Votre dossier a été exporté par l’équipe EMC",

      case_status_changed:
        "Statut du dossier mis à jour",

      case_workflow_status_changed:
        "Prise en charge du dossier mise à jour",

      case_deletion_requested:
        "Demande de suppression envoyée",

      case_deletion_rejected:
        "Demande de suppression refusée",
    },

    workflowStatuses: {
      new:
        "Nouveau",

      in_progress:
        "En cours de traitement",

      waiting_information:
        "En attente d’informations",

      resolved:
        "Résolu",

      closed:
        "Clôturé",
    },

    adminViewedDescription:
      "L’équipe EMC a ouvert votre dossier afin d’en assurer le suivi.",

    adminExportedDescription:
      "Une copie PDF sécurisée de votre dossier a été générée par l’équipe EMC.",

    statusChangedDescription:
      "Le statut administratif de votre dossier a été modifié par l’équipe EMC.",

    workflowChangedPrefix:
      "Votre dossier est maintenant",

    deletionRequestedDescription:
      "Votre demande de suppression a été transmise à l’équipe EMC.",

    deletionRejectedDescription:
      "L’équipe EMC a refusé la demande de suppression de ce dossier.",

    actionsCount:
      "actions proposées",

    noDetails:
      "Activité enregistrée.",
  },


  ar: {

    title:
      "السجل",

    subtitle:
      "راجع أهم الأنشطة التي تم تنفيذها داخل ملفاتك.",

    allCases:
      "جميع الملفات",

    selectCase:
      "عرض الملف",

    loading:
      "جارٍ تحميل السجل...",

    loadingCases:
      "جارٍ تحميل الملفات...",

    emptyTitle:
      "لا توجد أحداث",

    emptyText:
      "لم يتم تسجيل أي نشاط لهذا الملف بعد.",

    error:
      "تعذر تحميل السجل.",

    retry:
      "إعادة المحاولة",

    events:
      "حدث",

    caseLabel:
      "الملف",

    unknownCase:
      "ملف",

    statusActive:
      "نشط",

    statusClosed:
      "مغلق",

    types: {
      screenshot:
        "لقطة شاشة",

      file:
        "ملف",

      link:
        "رابط",

      note:
        "ملاحظة",
    },

    eventTitles: {

      case_created:
        "تم إنشاء الملف",

      action_plan_generated:
        "تم إنشاء خطة العمل",

      action_completed:
        "تم إكمال الإجراء",

      action_reopened:
        "تمت إعادة فتح الإجراء",

      evidence_added:
        "تمت إضافة دليل",

      evidence_deleted:
        "تم حذف دليل",

      case_viewed_by_admin:
        "تمت معاينة ملفك من طرف فريق EMC",

      case_exported:
        "تم تصدير ملفك من طرف فريق EMC",

      case_status_changed:
        "تم تحديث حالة الملف",

      case_workflow_status_changed:
        "تم تحديث مرحلة معالجة الملف",

      case_deletion_requested:
        "تم إرسال طلب حذف الملف",

      case_deletion_rejected:
        "تم رفض طلب حذف الملف",
    },

    workflowStatuses: {
      new:
        "جديد",

      in_progress:
        "قيد المعالجة",

      waiting_information:
        "في انتظار معلومات",

      resolved:
        "تمت المعالجة",

      closed:
        "مغلق",
    },

    adminViewedDescription:
      "قام فريق EMC بفتح ملفك من أجل متابعته ومعالجته.",

    adminExportedDescription:
      "تم إنشاء نسخة PDF آمنة من ملفك من طرف فريق EMC.",

    statusChangedDescription:
      "قام فريق EMC بتعديل الحالة الإدارية لملفك.",

    workflowChangedPrefix:
      "أصبحت مرحلة معالجة ملفك الآن",

    deletionRequestedDescription:
      "تم إرسال طلب حذف ملفك إلى فريق EMC.",

    deletionRejectedDescription:
      "رفض فريق EMC طلب حذف هذا الملف.",

    actionsCount:
      "إجراءات مقترحة",

    noDetails:
      "تم تسجيل النشاط.",
  },
};


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
        dateStyle: "medium",
        timeStyle: "short",
      }

    ).format(
      new Date(value)
    );

  } catch {

    return value;
  }
}


function displayIntent(
  intent,
  language,
) {

  if (!intent) {
    return "";
  }


  if (
    language === "ar"
  ) {

    return (
      ARABIC_INTENT_LABELS[
        intent
      ]
      || intent
    );
  }


  return intent;
}


function getEventIcon(
  eventType,
) {

  switch (eventType) {

    case "case_created":
      return "📁";

    case "action_plan_generated":
      return "📋";

    case "action_completed":
      return "✓";

    case "action_reopened":
      return "↺";

    case "evidence_added":
      return "＋";

    case "evidence_deleted":
      return "−";

    case "case_viewed_by_admin":
      return "◉";

    case "case_exported":
      return "⇩";

    case "case_status_changed":
      return "↻";

    case "case_workflow_status_changed":
      return "◆";

    case "case_deletion_requested":
      return "⌫";

    case "case_deletion_rejected":
      return "×";

    default:
      return "•";
  }
}


function getEventDescription(
  event,
  language,
  labels,
) {

  const data =
    event.event_data
    || {};


  switch (
    event.event_type
  ) {

    case "case_created": {

      const intent =
        displayIntent(
          data.detected_intent,
          language,
        );


      const statusLabel =
        data.status === "closed"
          ? labels.statusClosed
          : labels.statusActive;


      if (intent) {

        return (
          `${intent} · ${statusLabel}`
        );
      }


      return statusLabel;
    }


    case "action_plan_generated": {

      const parts = [];


      if (
        Number.isFinite(
          data.actions_count
        )
      ) {

        parts.push(
          `${data.actions_count} ${labels.actionsCount}`
        );
      }


      const intent =
        displayIntent(
          data.detected_intent,
          language,
        );


      if (intent) {

        parts.push(
          intent
        );
      }


      return (
        parts.join(" · ")
        || labels.noDetails
      );
    }


    case "action_completed":

    case "action_reopened":

      return (
        data.title
        || labels.noDetails
      );


    case "evidence_added":

    case "evidence_deleted": {

      const parts = [];


      if (data.title) {

        parts.push(
          data.title
        );
      }


      if (
        data.evidence_type
        && labels.types[
          data.evidence_type
        ]
      ) {

        parts.push(
          labels.types[
            data.evidence_type
          ]
        );
      }


      return (
        parts.join(" · ")
        || labels.noDetails
      );
    }


    case "case_viewed_by_admin":

      return (
        labels.adminViewedDescription
      );


    case "case_exported":

      return (
        labels.adminExportedDescription
      );


    case "case_status_changed":

      return (
        labels.statusChangedDescription
      );


    case "case_workflow_status_changed": {

      const workflowStatus =
        labels.workflowStatuses[
          data.new_workflow_status
        ]
        || data.new_workflow_status
        || "";

      if (!workflowStatus) {
        return labels.noDetails;
      }

      return (
        `${labels.workflowChangedPrefix} : ${workflowStatus}.`
      );
    }


    case "case_deletion_requested":

      return (
        labels.deletionRequestedDescription
      );


    case "case_deletion_rejected":

      return (
        labels.deletionRejectedDescription
      );


    default:

      return labels.noDetails;
  }
}


function History() {

  const {
    language,
  } = useLanguage();


  const interfaceLanguage =
    language === "ar"
      ? "ar"
      : "fr";


  const interfaceDir =
    interfaceLanguage === "ar"
      ? "rtl"
      : "ltr";


  const labels =
    LABELS[
      interfaceLanguage
    ];


  const [
    cases,
    setCases,
  ] = useState([]);


  const [
    selectedCaseId,
    setSelectedCaseId,
  ] = useState("all");


  const [
    events,
    setEvents,
  ] = useState([]);


  const [
    casesLoading,
    setCasesLoading,
  ] = useState(true);


  const [
    historyLoading,
    setHistoryLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  const caseById =
    useMemo(
      () => {

        const map =
          new Map();


        for (
          const item
          of cases
        ) {

          map.set(
            item.id,
            item,
          );
        }


        return map;
      },
      [cases]
    );


  const loadCases =
    async () => {

      setCasesLoading(
        true
      );


      try {

        const response =
          await fetch(

            `${API_BASE_URL}/cases`,

            {
              method: "GET",
              credentials:
                "include",
            }
          );


        if (!response.ok) {

          throw new Error(
            `GET /cases (${response.status})`
          );
        }


        const data =
          await response.json();


        setCases(
          Array.isArray(data)
            ? data
            : []
        );


      } catch (err) {

        console.error(
          err
        );


        setError(
          labels.error
        );


      } finally {

        setCasesLoading(
          false
        );
      }
    };


  const loadHistory =
    async () => {

      setHistoryLoading(
        true
      );

      setError("");


      try {

        const url =

          selectedCaseId
          === "all"

            ? (
                `${API_BASE_URL}/history`
              )

            : (
                `${API_BASE_URL}/history`
                + `?case_id=${encodeURIComponent(
                  selectedCaseId
                )}`
              );


        const response =
          await fetch(

            url,

            {
              method: "GET",
              credentials:
                "include",
            }
          );


        const data =
          await response
            .json()
            .catch(
              () => null
            );


        if (!response.ok) {

          const detail =

            typeof data?.detail
            === "string"

              ? data.detail

              : labels.error;


          throw new Error(
            detail
          );
        }


        setEvents(
          Array.isArray(data)
            ? data
            : []
        );


      } catch (err) {

        console.error(
          err
        );


        setEvents([]);


        setError(
          err.message
          || labels.error
        );


      } finally {

        setHistoryLoading(
          false
        );
      }
    };


  useEffect(
    () => {

      loadCases();

    },
    []
  );


  useEffect(
    () => {

      loadHistory();

    },
    [
      selectedCaseId,
      interfaceLanguage,
    ]
  );


  const eventCount =
    events.length;


  return (

    <div
      className="history-page"
      lang={
        interfaceLanguage
      }
      dir={
        interfaceDir
      }
    >

      <div
        className="history-container"
      >

        {/* ================================================
            HEADER
        ================================================= */}

        <header
          className="history-header"
        >

          <div>

            <h1
              className="history-title"
            >
              {labels.title}
            </h1>


            <p
              className="history-subtitle"
            >
              {labels.subtitle}
            </p>

          </div>


          <div
            className="history-counter"
          >

            <strong>
              {eventCount}
            </strong>

            <span>
              {labels.events}
            </span>

          </div>

        </header>


        {/* ================================================
            FILTER
        ================================================= */}

        <section
          className="history-filter-card"
        >

          <label
            htmlFor="history-case-select"
          >

            {labels.selectCase}

          </label>


          <select

            id="history-case-select"

            value={
              selectedCaseId
            }

            disabled={
              casesLoading
            }

            onChange={
              (
                event
              ) => {

                setSelectedCaseId(
                  event.target.value
                );
              }
            }

          >

            <option
              value="all"
            >

              {labels.allCases}

            </option>


            {cases.map(
              (
                item
              ) => {

                const intent =
                  displayIntent(
                    item.detected_intent,
                    interfaceLanguage,
                  );


                return (

                  <option
                    key={
                      item.id
                    }
                    value={
                      item.id
                    }
                  >

                    {
                      intent
                      || labels.unknownCase
                    }

                    {" · "}

                    {
                      formatDate(
                        item.created_at,
                        interfaceLanguage,
                      )
                    }

                  </option>
                );
              }
            )}

          </select>


          {casesLoading && (

            <span
              className="history-filter-loading"
            >
              {labels.loadingCases}
            </span>

          )}

        </section>


        {/* ================================================
            ERROR
        ================================================= */}

        {error && (

          <section
            className="history-error"
            role="alert"
          >

            <span>
              {error}
            </span>


            <button
              type="button"
              onClick={
                loadHistory
              }
            >
              {labels.retry}
            </button>

          </section>

        )}


        {/* ================================================
            LOADING
        ================================================= */}

        {historyLoading && (

          <section
            className="history-state-card"
          >

            <div
              className="history-spinner"
              aria-hidden="true"
            />


            <p>
              {labels.loading}
            </p>

          </section>

        )}


        {/* ================================================
            EMPTY
        ================================================= */}

        {
          !historyLoading
          && !error
          && events.length === 0
          && (

            <section
              className="history-state-card"
            >

              <div
                className="history-empty-icon"
              >
                ◷
              </div>


              <h2>
                {labels.emptyTitle}
              </h2>


              <p>
                {labels.emptyText}
              </p>

            </section>

          )
        }


        {/* ================================================
            TIMELINE
        ================================================= */}

        {
          !historyLoading
          && events.length > 0
          && (

            <section
              className="history-timeline"
            >

              {events.map(
                (
                  event
                ) => {

                  const caseItem =
                    caseById.get(
                      event.case_id
                    );


                  const caseIntent =
                    caseItem
                      ? displayIntent(
                          caseItem
                            .detected_intent,
                          interfaceLanguage,
                        )
                      : "";


                  const title =

                    labels
                      .eventTitles[
                        event.event_type
                      ]

                    || event.event_type;


                  const description =
                    getEventDescription(
                      event,
                      interfaceLanguage,
                      labels,
                    );


                  return (

                    <article
                      className="history-event"
                      key={
                        event.id
                      }
                    >

                      <div
                        className={
                          "history-event-marker "
                          + `history-event-marker-${event.event_type}`
                        }
                        aria-hidden="true"
                      >

                        {
                          getEventIcon(
                            event.event_type
                          )
                        }

                      </div>


                      <div
                        className="history-event-card"
                      >

                        <div
                          className="history-event-top"
                        >

                          <div>

                            <h2>
                              {title}
                            </h2>


                            <time
                              dateTime={
                                event.created_at
                              }
                            >

                              {
                                formatDate(
                                  event.created_at,
                                  interfaceLanguage,
                                )
                              }

                            </time>

                          </div>


                          {
                            selectedCaseId
                            === "all"
                            && caseIntent
                            && (

                              <span
                                className="history-case-badge"
                              >

                                {caseIntent}

                              </span>

                            )
                          }

                        </div>


                        <p
                          className="history-event-description"
                        >
                          {description}
                        </p>

                      </div>

                    </article>
                  );
                }
              )}

            </section>
          )
        }

      </div>

    </div>
  );
}


export default History;