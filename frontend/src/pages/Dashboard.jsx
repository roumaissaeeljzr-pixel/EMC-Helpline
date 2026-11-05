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
  useLanguage,
} from "../context/LanguageContext.jsx";

import {
  useAuth,
} from "../context/AuthContext.jsx";

import {
  ActivityTimeline,
  AssistantPreview,
  DashboardIcon,
  DashboardSkeleton,
  GuidedFolderIllustration,
  ProgressCircle,
  QuickActionCard,
} from "../components/dashboard/DashboardComponents.jsx";

import "./Dashboard.css";
import "./DashboardCaseSelector.css";


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


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


const COPY = {
  fr: {
    welcome:
      "Bienvenue dans votre espace",

    intro:
      "Nous vous guidons pas à pas pour vous protéger et poursuivre vos démarches en confiance.",

    activeCase:
      "Dossier actif",

    trackedCase:
      "Dossier suivi",

    chooseCase:
      "Choisissez le dossier dont vous souhaitez consulter la progression.",

    opened:
      "Ouvert le",

    inProgress:
      "En cours",

    workflowNew:
      "Nouveau",

    workflowInProgress:
      "En cours de traitement",

    workflowWaiting:
      "En attente d’informations",

    workflowResolved:
      "Résolu",

    workflowClosed:
      "Clôturé",

    workflowUpdated:
      "Prise en charge du dossier mise à jour",

    workflowNow:
      "Votre dossier est maintenant",

    adminViewed:
      "Votre dossier a été consulté par l’équipe EMC",

    adminViewedText:
      "L’équipe EMC a ouvert votre dossier afin d’en assurer le suivi.",

    caseExported:
      "Votre dossier a été exporté par l’équipe EMC",

    caseExportedText:
      "Une copie sécurisée de votre dossier a été générée par l’équipe EMC.",

    caseStatusChanged:
      "Statut du dossier mis à jour",

    caseStatusChangedText:
      "Le statut administratif de votre dossier a été modifié par l’équipe EMC.",

    deletionRequested:
      "Demande de suppression envoyée",

    deletionRequestedText:
      "Votre demande de suppression a été transmise à l’équipe EMC.",

    deletionRejected:
      "Demande de suppression refusée",

    deletionRejectedText:
      "L’équipe EMC a refusé la demande de suppression de ce dossier.",

    progression:
      "Progression",

    step:
      "Étape",

    of:
      "sur",

    nextAction:
      "Votre prochaine action",

    priority:
      "Priorité",

    recommended:
      "Recommandée",

    high:
      "Élevée",

    estimated:
      "Temps estimé",

    ownPace:
      "À votre rythme",

    start:
      "Continuer cette action",

    generatePlan:
      "Générer mon plan d’action",

    viewPlan:
      "Voir mon plan d’action",

    noAction:
      "Toutes les actions proposées sont terminées.",

    noPlan:
      "Votre plan d’action n’a pas encore été généré.",

    needEvidence:
      "Ajoutez une preuve à votre dossier.",

    needEvidenceText:
      "Conservez au moins une capture, un fichier, un lien ou une note utile avant de poursuivre.",

    addEvidenceNow:
      "Ajouter une preuve",

    planNeedsReview:
      "Votre plan d’action est créé.",

    planNeedsReviewText:
      "Consultez votre plan pour vérifier les actions proposées.",

    journeyComplete:
      "Votre parcours principal est terminé.",

    journeyCompleteText:
      "La situation a été évaluée, le dossier est créé, le plan est généré, une preuve est conservée et toutes les actions du plan sont terminées.",

    status:
      "Statut",

    completed:
      "Terminé",

    followUp:
      "Suivi",

    upToDate:
      "À jour",

    journey:
      "Parcours guidé",

    situation:
      "Situation évaluée",

    dossier:
      "Dossier créé",

    plan:
      "Plan d’action généré",

    evidence:
      "Preuves ajoutées",

    actionsDone:
      "Actions du plan terminées",

    quick:
      "Accès rapides",

    assistant:
      "Parler à l’assistant IA",

    assistantDescription:
      "Posez vos questions et obtenez une orientation adaptée.",

    assess:
      "Évaluer une situation",

    assessDescription:
      "Décrivez une nouvelle situation pour obtenir une analyse.",

    planQuick:
      "Consulter mon plan d’action",

    planQuickDescription:
      "Suivez les actions proposées et leur progression.",

    caseQuick:
      "Consulter mon dossier",

    caseQuickDescription:
      "Retrouvez la situation enregistrée et les informations du dossier.",

    addEvidence:
      "Ajouter une preuve",

    evidenceDescription:
      "Conservez capture, fichier, lien ou note.",

    resources:
      "Consulter les ressources",

    resourcesDescription:
      "Accédez aux ressources publiées par l’équipe EMC.",

    history:
      "Consulter l’historique",

    historyDescription:
      "Retrouvez les étapes et actions déjà enregistrées.",

    recent:
      "Activité récente",

    viewHistory:
      "Voir tout l’historique",

    emptyActivity:
      "Aucune activité récente.",

    secure:
      "Votre espace est sécurisé",

    secureText:
      "L’accès à vos dossiers et à vos preuves nécessite votre session authentifiée EMC Helpline.",

    noCase:
      "Aucun dossier actif",

    noCaseText:
      "Commencez par évaluer votre situation afin de créer votre premier dossier.",

    evaluate:
      "Évaluer ma situation",

    error:
      "Certaines informations n’ont pas pu être chargées.",

    retry:
      "Réessayer",

    eventLabels: {
      case_created:
        "Situation évaluée",

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

      case_workflow_status_changed:
        "Prise en charge du dossier mise à jour",

      case_status_changed:
        "Statut du dossier mis à jour",

      case_viewed_by_admin:
        "Votre dossier a été consulté par l’équipe EMC",

      case_exported:
        "Votre dossier a été exporté par l’équipe EMC",

      case_deletion_requested:
        "Demande de suppression envoyée",

      case_deletion_rejected:
        "Demande de suppression refusée",
    },
  },


  ar: {
    welcome:
      "مرحبًا بك في مساحتك",

    intro:
      "نرافقك خطوة بخطوة لحمايتك ومواصلة إجراءاتك بثقة.",

    activeCase:
      "الملف النشط",

    trackedCase:
      "الملف المتابع",

    chooseCase:
      "اختر الملف الذي تريد عرض تقدمه.",

    opened:
      "تم فتحه في",

    inProgress:
      "قيد المتابعة",

    workflowNew:
      "جديد",

    workflowInProgress:
      "قيد المعالجة",

    workflowWaiting:
      "في انتظار معلومات",

    workflowResolved:
      "تمت المعالجة",

    workflowClosed:
      "مغلق",

    workflowUpdated:
      "تم تحديث مرحلة معالجة الملف",

    workflowNow:
      "أصبحت مرحلة معالجة ملفك الآن",

    adminViewed:
      "تمت معاينة ملفك من طرف فريق EMC",

    adminViewedText:
      "فتح فريق EMC ملفك من أجل متابعة حالتك.",

    caseExported:
      "تم تصدير ملفك من طرف فريق EMC",

    caseExportedText:
      "أنشأ فريق EMC نسخة آمنة من ملفك.",

    caseStatusChanged:
      "تم تحديث حالة الملف",

    caseStatusChangedText:
      "قام فريق EMC بتعديل الحالة الإدارية لملفك.",

    deletionRequested:
      "تم إرسال طلب حذف الملف",

    deletionRequestedText:
      "تم إرسال طلب حذف ملفك إلى فريق EMC.",

    deletionRejected:
      "تم رفض طلب حذف الملف",

    deletionRejectedText:
      "رفض فريق EMC طلب حذف هذا الملف.",

    progression:
      "التقدم",

    step:
      "المرحلة",

    of:
      "من",

    nextAction:
      "إجراؤك التالي",

    priority:
      "الأولوية",

    recommended:
      "موصى بها",

    high:
      "مرتفعة",

    estimated:
      "الوقت التقديري",

    ownPace:
      "حسب وتيرتك",

    start:
      "متابعة هذا الإجراء",

    generatePlan:
      "إنشاء خطة العمل",

    viewPlan:
      "عرض خطة العمل",

    noAction:
      "تم إنجاز جميع الإجراءات المقترحة.",

    noPlan:
      "لم يتم إنشاء خطة العمل بعد.",

    needEvidence:
      "أضف دليلاً إلى ملفك.",

    needEvidenceText:
      "احتفظ بلقطة شاشة أو ملف أو رابط أو ملاحظة مفيدة واحدة على الأقل قبل المتابعة.",

    addEvidenceNow:
      "إضافة دليل",

    planNeedsReview:
      "تم إنشاء خطة العمل.",

    planNeedsReviewText:
      "راجع خطتك للتحقق من الإجراءات المقترحة.",

    journeyComplete:
      "اكتمل مسارك الرئيسي.",

    journeyCompleteText:
      "تم تقييم الحالة وإنشاء الملف وخطة العمل وحفظ دليل واحد على الأقل وإنجاز جميع إجراءات الخطة.",

    status:
      "الحالة",

    completed:
      "مكتمل",

    followUp:
      "المتابعة",

    upToDate:
      "محدّثة",

    journey:
      "المسار الموجّه",

    situation:
      "تم تقييم الحالة",

    dossier:
      "تم إنشاء الملف",

    plan:
      "تم إنشاء خطة العمل",

    evidence:
      "تمت إضافة الأدلة",

    actionsDone:
      "تم إنجاز إجراءات الخطة",

    quick:
      "الوصول السريع",

    assistant:
      "التحدث مع المساعد الذكي",

    assistantDescription:
      "اطرح أسئلتك واحصل على توجيه مناسب.",

    assess:
      "تقييم حالة",

    assessDescription:
      "صف حالة جديدة للحصول على تحليل.",

    planQuick:
      "عرض خطة العمل",

    planQuickDescription:
      "تابع الإجراءات المقترحة ونسبة تقدمها.",

    caseQuick:
      "عرض ملفي",

    caseQuickDescription:
      "راجع الحالة المسجلة ومعلومات الملف.",

    addEvidence:
      "إضافة دليل",

    evidenceDescription:
      "احتفظ بلقطة أو ملف أو رابط أو ملاحظة.",

    resources:
      "عرض الموارد",

    resourcesDescription:
      "اطّلع على الموارد التي ينشرها فريق EMC.",

    history:
      "عرض السجل",

    historyDescription:
      "راجع الخطوات والإجراءات المسجلة.",

    recent:
      "النشاط الأخير",

    viewHistory:
      "عرض السجل الكامل",

    emptyActivity:
      "لا يوجد نشاط حديث.",

    secure:
      "مساحتك آمنة",

    secureText:
      "يتطلب الوصول إلى ملفاتك وأدلتك جلسة EMC Helpline موثقة.",

    noCase:
      "لا يوجد ملف نشط",

    noCaseText:
      "ابدأ بتقييم وضعك لإنشاء ملفك الأول.",

    evaluate:
      "تقييم وضعي",

    error:
      "تعذر تحميل بعض المعلومات.",

    retry:
      "إعادة المحاولة",

    eventLabels: {
      case_created:
        "تم تقييم الحالة",

      action_plan_generated:
        "تم إنشاء خطة العمل",

      action_completed:
        "تم إكمال إجراء",

      action_reopened:
        "تمت إعادة فتح إجراء",

      evidence_added:
        "تمت إضافة دليل",

      evidence_deleted:
        "تم حذف دليل",

      case_workflow_status_changed:
        "تم تحديث مرحلة معالجة الملف",

      case_status_changed:
        "تم تحديث حالة الملف",

      case_viewed_by_admin:
        "تمت معاينة ملفك من طرف فريق EMC",

      case_exported:
        "تم تصدير ملفك من طرف فريق EMC",

      case_deletion_requested:
        "تم إرسال طلب حذف الملف",

      case_deletion_rejected:
        "تم رفض طلب حذف الملف",
    },
  },
};


/* ==========================================================
   USER DISPLAY
========================================================= */

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


/* ==========================================================
   INTENT
========================================================= */

function displayIntent(
  intent,
  language,
) {
  if (!intent) {
    return "—";
  }


  return language === "ar"
    ? (
        ARABIC_INTENTS[intent]
        || intent
      )
    : intent;
}


function displayWorkflowStatus(
  value,
  labels,
) {
  switch (value) {
    case "in_progress":
      return labels.workflowInProgress;

    case "waiting_information":
      return labels.workflowWaiting;

    case "resolved":
      return labels.workflowResolved;

    case "closed":
      return labels.workflowClosed;

    case "new":
    default:
      return labels.workflowNew;
  }
}


/* ==========================================================
   DATE
========================================================= */

function formatDate(
  value,
  language,
  withTime = false,
) {
  if (!value) {
    return "—";
  }


  try {
    return new Intl.DateTimeFormat(
      language === "ar"
        ? "ar-MA"
        : "fr-FR",
      withTime
        ? {
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
          }
        : {
            day: "numeric",
            month: "long",
            year: "numeric",
          }
    ).format(
      new Date(value)
    );
  } catch {
    return value;
  }
}


/* ==========================================================
   CASE REFERENCE
========================================================= */

function formatCaseReference(
  value,
) {
  if (!value) {
    return "—";
  }

  return (
    "#"
    + String(value)
      .replace(/-/g, "")
      .slice(0, 8)
      .toUpperCase()
  );
}


/* ==========================================================
   DASHBOARD
========================================================= */

function Dashboard() {
  const navigate =
    useNavigate();


  const reducedMotion =
    useReducedMotion();


  const {
    language,
  } = useLanguage();


  const {
    user,
  } = useAuth();


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
    partialError,
    setPartialError,
  ] = useState(false);


  const [
    availableCases,
    setAvailableCases,
  ] = useState([]);


  const [
    selectedCaseId,
    setSelectedCaseId,
  ] = useState(
    () =>
      window.localStorage.getItem(
        "emc_selected_case_id"
      )
      || ""
  );


  const [
    activeCase,
    setActiveCase,
  ] = useState(null);


  const [
    actionPlan,
    setActionPlan,
  ] = useState(null);


  const [
    evidences,
    setEvidences,
  ] = useState([]);


  const [
    history,
    setHistory,
  ] = useState([]);


  const [
    assistantOpen,
    setAssistantOpen,
  ] = useState(false);


  const displayName =
    getDisplayName(user);


  const firstName =
    displayName
      .split(/\s+/)
      .filter(Boolean)[0]
    || "";


  /* ======================================================
     LOAD DASHBOARD DATA
  ====================================================== */

  const loadDashboard =
    useCallback(
      async () => {
        setLoading(true);
        setPartialError(false);


        try {
          const casesResponse =
            await fetch(
              `${API_BASE_URL}/cases`,
              {
                credentials:
                  "include",
              }
            );


          if (!casesResponse.ok) {
            throw new Error(
              `GET /cases ${casesResponse.status}`
            );
          }


          const casesData =
            await casesResponse.json();


          const cases =
            Array.isArray(casesData)
              ? casesData
              : [];


          if (!cases.length) {
            setAvailableCases([]);
            setSelectedCaseId("");
            setActiveCase(null);
            setActionPlan(null);
            setEvidences([]);
            setHistory([]);

            window.localStorage.removeItem(
              "emc_selected_case_id"
            );

            return;
          }


          const activeCases =
            cases.filter(
              (item) =>
                item.status === "active"
            );


          const selectableCases =
            activeCases.length > 0
              ? activeCases
              : cases;


          setAvailableCases(
            selectableCases
          );


          const selectedCase =
            selectableCases.find(
              (item) =>
                item.id === selectedCaseId
            )
            || selectableCases[0];


          if (
            selectedCase.id
            !== selectedCaseId
          ) {
            setSelectedCaseId(
              selectedCase.id
            );

            window.localStorage.setItem(
              "emc_selected_case_id",
              selectedCase.id
            );
          }


          setActiveCase(
            selectedCase
          );


          const results =
            await Promise.allSettled([
              fetch(
                `${API_BASE_URL}/cases/${selectedCase.id}/action-plan`,
                {
                  credentials:
                    "include",
                }
              ),

              fetch(
                `${API_BASE_URL}/cases/${selectedCase.id}/evidence`,
                {
                  credentials:
                    "include",
                }
              ),

              fetch(
                `${API_BASE_URL}/history?case_id=${encodeURIComponent(
                  selectedCase.id
                )}`,
                {
                  credentials:
                    "include",
                }
              ),
            ]);


          /* ACTION PLAN */

          const planResult =
            results[0];


          if (
            planResult.status
              === "fulfilled"
            && planResult.value.ok
          ) {
            setActionPlan(
              await planResult
                .value
                .json()
            );
          } else {
            setActionPlan(null);


            if (
              !(
                planResult.status
                  === "fulfilled"
                && planResult.value.status
                  === 404
              )
            ) {
              setPartialError(true);
            }
          }


          /* EVIDENCE */

          const evidenceResult =
            results[1];


          if (
            evidenceResult.status
              === "fulfilled"
            && evidenceResult.value.ok
          ) {
            const data =
              await evidenceResult
                .value
                .json();


            setEvidences(
              Array.isArray(data)
                ? data
                : []
            );
          } else {
            setEvidences([]);
            setPartialError(true);
          }


          /* HISTORY */

          const historyResult =
            results[2];


          if (
            historyResult.status
              === "fulfilled"
            && historyResult.value.ok
          ) {
            const data =
              await historyResult
                .value
                .json();


            setHistory(
              Array.isArray(data)
                ? data
                : []
            );
          } else {
            setHistory([]);
            setPartialError(true);
          }
        } catch (error) {
          console.error(
            "Dashboard :",
            error
          );


          setPartialError(true);

          setActiveCase(null);
          setActionPlan(null);
          setEvidences([]);
          setHistory([]);
        } finally {
          setLoading(false);
        }
      },
      [
        selectedCaseId,
      ]
    );


  useEffect(
    () => {
      loadDashboard();
    },
    [
      loadDashboard,
    ]
  );


  const handleCaseChange =
    (event) => {
      const nextCaseId =
        event.target.value;

      setSelectedCaseId(
        nextCaseId
      );

      window.localStorage.setItem(
        "emc_selected_case_id",
        nextCaseId
      );
    };


  /* ======================================================
     ACTION PLAN
  ====================================================== */

  const actions =
    useMemo(
      () => {
        const source =
          Array.isArray(
            actionPlan?.actions
          )
            ? actionPlan.actions
            : Array.isArray(
                actionPlan?.items
              )
              ? actionPlan.items
              : [];


        return [
          ...source,
        ].sort(
          (
            first,
            second
          ) =>
            (
              Number(
                first.position
              )
              || 0
            )
            -
            (
              Number(
                second.position
              )
              || 0
            )
        );
      },
      [
        actionPlan,
      ]
    );


  const completedActions =
    actions.filter(
      (item) =>
        Boolean(
          item.completed
        )
    );


  const nextAction =
    actions.find(
      (item) =>
        !item.completed
    )
    || null;


  /* ======================================================
     JOURNEY / GLOBAL PROGRESS
  ====================================================== */

  const journeyFlags =
    useMemo(
      () => [
        Boolean(activeCase),

        Boolean(activeCase),

        Boolean(actionPlan),

        evidences.length > 0,

        Boolean(actionPlan)
        && actions.length > 0
        && completedActions.length
          === actions.length,
      ],
      [
        activeCase,
        actionPlan,
        evidences.length,
        actions.length,
        completedActions.length,
      ]
    );


  const journeyLabels =
    useMemo(
      () => [
        labels.situation,
        labels.dossier,
        labels.plan,
        labels.evidence,
        labels.actionsDone,
      ],
      [
        labels,
      ]
    );


  const firstIncompleteJourneyIndex =
    journeyFlags.findIndex(
      (value) =>
        !value
    );


  const journeySteps =
    useMemo(
      () =>
        journeyLabels.map(
          (
            label,
            index
          ) => ({
            key:
              `journey-${index}`,

            label,

            status:
              journeyFlags[index]
                ? "completed"
                : index
                    === firstIncompleteJourneyIndex
                  ? "current"
                  : "upcoming",
          })
        ),
      [
        journeyFlags,
        journeyLabels,
        firstIncompleteJourneyIndex,
      ]
    );


  const completedJourneySteps =
    journeyFlags.filter(
      Boolean
    ).length;


  const journeyProgress =
    Math.round(
      (
        completedJourneySteps
        / journeyFlags.length
      )
      * 100
    );


  const currentJourneyStep =
    firstIncompleteJourneyIndex
      === -1
      ? journeyFlags.length
      : firstIncompleteJourneyIndex + 1;


  const journeyComplete =
    completedJourneySteps
      === journeyFlags.length;


  /* ======================================================
     NEXT RECOMMENDED STEP
  ====================================================== */

  const dashboardNext =
    useMemo(
      () => {
        if (!actionPlan) {
          return {
            title:
              labels.noPlan,

            description:
              "",

            button:
              labels.generatePlan,

            route:
              "/victim/action-plan",

            icon:
              "check",

            completed:
              false,
          };
        }


        if (
          evidences.length === 0
        ) {
          return {
            title:
              labels.needEvidence,

            description:
              labels.needEvidenceText,

            button:
              labels.addEvidenceNow,

            route:
              "/victim/evidence",

            icon:
              "clip",

            completed:
              false,
          };
        }


        if (
          actions.length === 0
        ) {
          return {
            title:
              labels.planNeedsReview,

            description:
              labels.planNeedsReviewText,

            button:
              labels.viewPlan,

            route:
              "/victim/action-plan",

            icon:
              "check",

            completed:
              false,
          };
        }


        if (nextAction) {
          return {
            title:
              nextAction.title,

            description:
              nextAction.description
              || "",

            button:
              labels.start,

            route:
              "/victim/action-plan",

            icon:
              "check",

            completed:
              false,

            estimatedMinutes:
              nextAction.estimated_minutes
              || null,
          };
        }


        return {
          title:
            labels.journeyComplete,

          description:
            labels.journeyCompleteText,

          button:
            labels.viewHistory,

          route:
            "/victim/history",

          icon:
            "check",

          completed:
            true,
        };
      },
      [
        actionPlan,
        actions.length,
        evidences.length,
        nextAction,
        labels,
      ]
    );


  /* ======================================================
     HISTORY
  ====================================================== */

  const recentEvents =
    history.slice(
      0,
      3
    );


  const currentWorkflowStatus =
    useMemo(
      () => {
        if (
          activeCase?.workflow_status
        ) {
          return (
            activeCase.workflow_status
          );
        }

        const latestWorkflowEvent =
          history.find(
            (event) =>
              event.event_type
              === "case_workflow_status_changed"
          );

        const historyStatus =
          latestWorkflowEvent
            ?.event_data
            ?.new_workflow_status;

        if (historyStatus) {
          return historyStatus;
        }

        return (
          activeCase?.status
          === "closed"
            ? "closed"
            : "new"
        );
      },
      [
        activeCase,
        history,
      ]
    );


  const getEventTitle =
    (event) =>
      labels.eventLabels[
        event.event_type
      ]
      || event.event_type;


  const getEventDescription =
    (event) => {
      const data =
        event.event_data
        || {};


      if (
        event.event_type
        === "case_created"
      ) {
        return displayIntent(
          data.detected_intent,
          language
        );
      }


      if (
        event.event_type
        === "action_plan_generated"
      ) {
        return typeof data.actions_count
          === "number"
          ? (
              isArabic
                ? `${data.actions_count} إجراءات مقترحة`
                : `${data.actions_count} actions proposées`
            )
          : "";
      }


      if (
        event.event_type
        === "case_workflow_status_changed"
      ) {
        const statusLabel =
          displayWorkflowStatus(
            data.new_workflow_status,
            labels
          );

        return (
          `${labels.workflowNow} : ${statusLabel}.`
        );
      }


      if (
        event.event_type
        === "case_status_changed"
      ) {
        return (
          labels.caseStatusChangedText
        );
      }


      if (
        event.event_type
        === "case_viewed_by_admin"
      ) {
        return (
          labels.adminViewedText
        );
      }


      if (
        event.event_type
        === "case_exported"
      ) {
        return (
          labels.caseExportedText
        );
      }


      if (
        event.event_type
        === "case_deletion_requested"
      ) {
        return (
          labels.deletionRequestedText
        );
      }


      if (
        event.event_type
        === "case_deletion_rejected"
      ) {
        return (
          labels.deletionRejectedText
        );
      }


      return (
        data.title
        || ""
      );
    };


  /* ======================================================
     LOADING
  ====================================================== */

  if (loading) {
    return (
      <DashboardSkeleton />
    );
  }


  return (
    <motion.div
      key={language}
      className="guided-dashboard"
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
          ERROR
      ================================================= */}

      {partialError && (
        <div className="guided-error">
          <span>
            {labels.error}
          </span>

          <button
            type="button"
            onClick={
              loadDashboard
            }
          >
            {labels.retry}
          </button>
        </div>
      )}


      {/* =================================================
          NO CASE
      ================================================= */}

      {!activeCase ? (
        <section className="guided-no-case">
          <span>
            <DashboardIcon
              name="shield"
              size={38}
            />
          </span>


          <h1>
            {labels.noCase}
          </h1>


          <p>
            {labels.noCaseText}
          </p>


          <button
            type="button"
            onClick={() =>
              navigate(
                "/victim/assessment"
              )
            }
          >
            {labels.evaluate}
          </button>
        </section>
      ) : (
        <>
          {/* =================================================
              HERO
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
                EMC Helpline
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
              CASE SELECTOR
          ================================================= */}

          {availableCases.length > 1 && (
            <section className="guided-case-switcher">
              <div className="guided-case-switcher-copy">
                <span>
                  <DashboardIcon
                    name="folder"
                    size={21}
                  />
                </span>

                <div>
                  <strong>
                    {labels.trackedCase}
                  </strong>

                  <small>
                    {labels.chooseCase}
                  </small>
                </div>
              </div>


              <div className="guided-case-switcher-control">
                <select
                  value={activeCase?.id || ""}
                  onChange={handleCaseChange}
                  aria-label={labels.trackedCase}
                >
                  {availableCases.map(
                    (item) => (
                      <option
                        key={item.id}
                        value={item.id}
                      >
                        {displayIntent(
                          item.detected_intent,
                          language
                        )}
                        {" — "}
                        {formatCaseReference(
                          item.id
                        )}
                      </option>
                    )
                  )}
                </select>
              </div>
            </section>
          )}


          {/* =================================================
              CASE + PROGRESS
          ================================================= */}

          <div className="guided-overview-grid">
            <motion.button
              type="button"
              className="guided-overview-card guided-case-card"
              onClick={() =>
                navigate(
                  "/victim/case"
                )
              }
              whileHover={
                reducedMotion
                  ? undefined
                  : {
                      y: -3,
                    }
              }
            >
              <span className="guided-overview-icon folder">
                <DashboardIcon
                  name="folder"
                  size={25}
                />
              </span>


              <div>
                <small>
                  {labels.activeCase}
                </small>


                <strong>
                  {displayIntent(
                    activeCase
                      .detected_intent,
                    language
                  )}
                </strong>


                <p>
                  {labels.opened}
                  {" "}
                  {formatDate(
                    activeCase.created_at,
                    language
                  )}
                </p>


                <em>
                  {displayWorkflowStatus(
                    currentWorkflowStatus,
                    labels
                  )}
                </em>
              </div>


              <span className="guided-overview-arrow">
                <DashboardIcon
                  name="arrow"
                  size={18}
                />
              </span>
            </motion.button>


            <motion.button
              type="button"
              className="guided-overview-card guided-progress-card"
              onClick={() =>
                navigate(
                  "/victim/action-plan"
                )
              }
              whileHover={
                reducedMotion
                  ? undefined
                  : {
                      y: -3,
                    }
              }
            >
              <div>
                <small>
                  {labels.progression}
                </small>


                <strong>
                  {labels.step}
                  {" "}
                  {currentJourneyStep}
                  {" "}
                  {labels.of}
                  {" "}
                  5
                </strong>
              </div>


              <ProgressCircle
                value={
                  journeyProgress
                }
              />
            </motion.button>
          </div>


          {/* =================================================
              NEXT ACTION
          ================================================= */}

          <motion.section
            className={
              journeyComplete
                ? "guided-next-action is-complete"
                : "guided-next-action"
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
            transition={{
              delay: 0.07,
            }}
          >
            <div className="guided-next-header">
              <strong>
                {labels.nextAction}
              </strong>
            </div>


            <div className="guided-next-body">
              <span className="guided-next-icon">
                <DashboardIcon
                  name={
                    dashboardNext.icon
                  }
                  size={25}
                />
              </span>


              <div className="guided-next-copy">
                <h2>
                  {
                    dashboardNext.title
                  }
                </h2>


                {dashboardNext.description
                  && (
                    <p>
                      {
                        dashboardNext
                          .description
                      }
                    </p>
                  )}
              </div>


              <div className="guided-next-meta">
                <div>
                  <small>
                    {dashboardNext.completed
                      ? labels.status
                      : labels.priority}
                  </small>

                  <strong
                    className={
                      !dashboardNext.completed
                      && activeCase.emergency
                        ? "urgent"
                        : ""
                    }
                  >
                    {dashboardNext.completed
                      ? labels.completed
                      : activeCase.emergency
                        ? labels.high
                        : labels.recommended}
                  </strong>
                </div>


                <div>
                  <small>
                    {dashboardNext.completed
                      ? labels.followUp
                      : labels.estimated}
                  </small>

                  <strong>
                    {dashboardNext.completed
                      ? labels.upToDate
                      : dashboardNext
                          .estimatedMinutes
                        ? `${dashboardNext.estimatedMinutes} min`
                        : labels.ownPace}
                  </strong>
                </div>
              </div>


              <button
                type="button"
                className="guided-next-button"
                onClick={() =>
                  navigate(
                    dashboardNext.route
                  )
                }
              >
                {
                  dashboardNext.button
                }

                <DashboardIcon
                  name="arrow"
                  size={18}
                />
              </button>
            </div>
          </motion.section>


          {/* =================================================
              JOURNEY
          ================================================= */}

          <motion.section
            className="guided-journey-card"
            initial={
              reducedMotion
                ? false
                : {
                    opacity: 0,
                    y: 14,
                  }
            }
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              delay: 0.18,
            }}
          >
            <h2>
              {labels.journey}
            </h2>


            <div
              className="guided-journey"
              style={{
                "--journey-progress":
                  `${journeyProgress}%`,
              }}
            >
              <div className="guided-journey-line">
                <motion.span
                  initial={{
                    width: "0%",
                  }}
                  animate={{
                    width:
                      `${journeyProgress}%`,
                  }}
                  transition={{
                    duration:
                      reducedMotion
                        ? 0
                        : 0.8,
                  }}
                />
              </div>


              {journeySteps.map(
                (
                  step,
                  index
                ) => (
                  <motion.div
                    key={
                      step.key
                    }
                    className={
                      `guided-journey-step is-${step.status}`
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
                    transition={{
                      delay:
                        0.08
                        * index,
                    }}
                  >
                    <span className="guided-journey-node">
                      {step.status
                        === "completed"
                        ? "✓"
                        : index + 1}
                    </span>


                    <strong>
                      {step.label}
                    </strong>
                  </motion.div>
                )
              )}
            </div>
          </motion.section>


          {/* =================================================
              QUICK ACCESS
          ================================================= */}

          <section className="guided-section">
            <h2>
              {labels.quick}
            </h2>


            <div className="guided-quick-grid">
              <QuickActionCard
                index={0}
                icon="chat"
                tone="purple"
                title={
                  labels.assistant
                }
                description={
                  labels.assistantDescription
                }
                onClick={() =>
                  setAssistantOpen(
                    true
                  )
                }
              />


              <QuickActionCard
                index={1}
                icon="shield"
                tone="green"
                title={
                  labels.assess
                }
                description={
                  labels.assessDescription
                }
                onClick={() =>
                  navigate(
                    "/victim/assessment"
                  )
                }
              />


              <QuickActionCard
                index={2}
                icon="check"
                tone="orange"
                title={
                  labels.planQuick
                }
                description={
                  labels.planQuickDescription
                }
                onClick={() =>
                  navigate(
                    "/victim/action-plan"
                  )
                }
              />


              <QuickActionCard
                index={3}
                icon="folder"
                tone="purple"
                title={
                  labels.caseQuick
                }
                description={
                  labels.caseQuickDescription
                }
                onClick={() =>
                  navigate(
                    "/victim/case"
                  )
                }
              />


              <QuickActionCard
                index={4}
                icon="clip"
                tone="blue"
                title={
                  labels.addEvidence
                }
                description={
                  labels.evidenceDescription
                }
                onClick={() =>
                  navigate(
                    "/victim/evidence"
                  )
                }
              />


              <QuickActionCard
                index={5}
                icon="spark"
                tone="green"
                title={
                  labels.resources
                }
                description={
                  labels.resourcesDescription
                }
                onClick={() =>
                  navigate(
                    "/victim/resources"
                  )
                }
              />


              <QuickActionCard
                index={6}
                icon="clock"
                tone="orange"
                title={
                  labels.history
                }
                description={
                  labels.historyDescription
                }
                onClick={() =>
                  navigate(
                    "/victim/history"
                  )
                }
              />
            </div>
          </section>


          {/* =================================================
              BOTTOM
          ================================================= */}

          <div className="guided-bottom-grid">
            <section className="guided-activity-card">
              <header>
                <h2>
                  {labels.recent}
                </h2>


                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      "/victim/history"
                    )
                  }
                >
                  {labels.viewHistory}
                </button>
              </header>


              <ActivityTimeline
                events={
                  recentEvents
                }
                getTitle={
                  getEventTitle
                }
                getDescription={
                  getEventDescription
                }
                formatDate={
                  (value) =>
                    formatDate(
                      value,
                      language,
                      true
                    )
                }
                emptyLabel={
                  labels.emptyActivity
                }
              />
            </section>


            {/* SECURITY */}

            <motion.section
              className="guided-security-card"
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
              <span className="security-halo" />


              <span className="security-lock">
                <DashboardIcon
                  name="lock"
                  size={28}
                />
              </span>


              <h2>
                {labels.secure}
              </h2>


              <p>
                {labels.secureText}
              </p>


              <span className="security-dot security-dot-one" />
              <span className="security-dot security-dot-two" />
            </motion.section>
          </div>
        </>
      )}


      {/* =================================================
          ASSISTANT PREVIEW
      ================================================= */}

      <AssistantPreview
        open={
          assistantOpen
        }
        language={
          language
        }
        onClose={() =>
          setAssistantOpen(
            false
          )
        }
        onOpenAssistant={() => {
          setAssistantOpen(false);

          navigate(
            "/victim/assistant"
          );
        }}
      />
    </motion.div>
  );
}


export default Dashboard;