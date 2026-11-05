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
  useLanguage,
} from "../../context/LanguageContext.jsx";

import {
  DashboardIcon,
} from "../../components/dashboard/DashboardComponents.jsx";

import "../Dashboard.css";
import "./Cases.css";


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
    kicker:
      "Gestion administrative",

    title:
      "Dossiers",

    intro:
      "Consultez et gérez les dossiers enregistrés tout en limitant l’accès aux informations nécessaires au suivi administratif.",

    total:
      "Tous les dossiers",

    active:
      "Actifs",

    closed:
      "Clôturés",

    priority:
      "Prioritaires",

    results:
      "dossier(s) affiché(s)",

    search:
      "Rechercher par victime ou situation",

    allStatuses:
      "Tous les statuts",

    activeStatus:
      "Actif",

    closedStatus:
      "Clôturé",

    allLanguages:
      "Toutes les langues",

    french:
      "Français",

    arabic:
      "Arabe",

    allPriorities:
      "Toutes les priorités",

    priorityOnly:
      "Urgences uniquement",

    normalOnly:
      "Non urgents",

    allIntents:
      "Toutes les situations",

    reset:
      "Réinitialiser",

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

    language:
      "Langue",

    progress:
      "Progression",

    evidence:
      "Preuves",

    status:
      "Statut",

    updated:
      "Mis à jour",

    actions:
      "Actions",

    view:
      "Consulter",

    noPlan:
      "Aucun plan",

    urgent:
      "Urgent",

    noCases:
      "Aucun dossier ne correspond aux filtres sélectionnés.",

    loading:
      "Chargement des dossiers...",

    error:
      "Impossible de charger les dossiers.",

    retry:
      "Réessayer",

    detailTitle:
      "Détail du dossier",

    close:
      "Fermer",

    reference:
      "Référence",

    created:
      "Créé le",

    lastUpdate:
      "Dernière mise à jour",

    description:
      "Situation déclarée",

    evidenceSection:
      "Preuves du dossier",

    evidenceSectionText:
      "Consultez les éléments conservés par la victime uniquement lorsqu’ils sont nécessaires au suivi.",

    evidencePlural:
      "preuves",

    evidenceSingular:
      "preuve",

    evidenceView:
      "Consulter",

    evidenceClose:
      "Masquer",

    evidenceOpenLink:
      "Ouvrir le lien",

    evidenceOpenFile:
      "Ouvrir le fichier",

    evidenceLoading:
      "Chargement de la preuve...",

    evidenceError:
      "Impossible de consulter cette preuve.",

    noEvidence:
      "Aucune preuve enregistrée dans ce dossier.",

    evidenceTypes: {
      screenshot:
        "Capture d’écran",

      file:
        "Fichier",

      link:
        "Lien",

      note:
        "Note",
    },

    fileName:
      "Fichier",

    fileSize:
      "Taille",

    addedOn:
      "Ajoutée le",

    privacyTitle:
      "Accès administratif limité",

    privacyText:
      "Les informations d’identité complètes ne sont affichées qu’après ouverture explicite du dossier. Les métadonnées des preuves sont visibles ici, tandis que leur contenu nécessite une action explicite de consultation. Le chemin de stockage des fichiers n’est jamais exposé.",

    actionPlan:
      "Plan d’action",

    completedActions:
      "actions terminées",

    exportTitle:
      "Dossier complet",

    exportText:
      "Générez un seul PDF contenant la situation, le plan d’action et toutes les preuves directement dans le rapport : captures d’écran, notes, liens cliquables et documents justificatifs.",

    exportButton:
      "Télécharger le PDF complet",

    exporting:
      "Génération du PDF...",

    exportSuccess:
      "Le téléchargement du PDF complet a démarré.",

    exportError:
      "Impossible de générer le PDF complet.",

    integrity:
      "Intégrité SHA-256",

    deletionRequest:
      "Demande de suppression",

    deletionPending:
      "Suppression demandée",

    deletionText:
      "La victime demande la suppression de ce dossier. Vous pouvez accepter la suppression définitive ou refuser la demande.",

    approveDeletion:
      "Accepter la suppression",

    rejectDeletion:
      "Refuser",

    deletionProcessing:
      "Traitement...",

    deletionApproved:
      "Le dossier a été supprimé définitivement.",

    deletionRejected:
      "La demande de suppression a été refusée.",

    confirmApproveDeletion:
      "Confirmer la suppression définitive de ce dossier et de ses données associées ?",

    confirmRejectDeletion:
      "Confirmer le refus de la demande de suppression ?",

    deletionDecisionError:
      "Impossible de traiter la demande de suppression.",

    changeStatus:
      "Prise en charge du dossier",

    workflowHelp:
      "Indiquez l’étape actuelle du suivi par l’équipe EMC.",

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

    saveWorkflow:
      "Mettre à jour",

    saving:
      "Enregistrement...",

    saved:
      "Étape de prise en charge mise à jour.",

    updateError:
      "Impossible de modifier l’étape de prise en charge.",

    unknown:
      "Non renseigné",
  },


  ar: {
    kicker:
      "الإدارة",

    title:
      "الملفات",

    intro:
      "اطلع على الملفات المسجلة وقم بإدارتها مع حصر الوصول في المعلومات الضرورية للمتابعة الإدارية.",

    total:
      "جميع الملفات",

    active:
      "نشطة",

    closed:
      "مغلقة",

    priority:
      "ذات أولوية",

    results:
      "ملفات معروضة",

    search:
      "البحث حسب اسم الضحية أو نوع الحالة",

    allStatuses:
      "كل الحالات",

    activeStatus:
      "نشط",

    closedStatus:
      "مغلق",

    allLanguages:
      "كل اللغات",

    french:
      "الفرنسية",

    arabic:
      "العربية",

    allPriorities:
      "كل الأولويات",

    priorityOnly:
      "الطوارئ فقط",

    normalOnly:
      "غير طارئة",

    allIntents:
      "كل أنواع الحالات",

    reset:
      "إعادة الضبط",

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

    language:
      "اللغة",

    progress:
      "التقدم",

    evidence:
      "الأدلة",

    status:
      "الحالة",

    updated:
      "آخر تحديث",

    actions:
      "إجراءات",

    view:
      "عرض",

    noPlan:
      "لا توجد خطة",

    urgent:
      "طارئ",

    noCases:
      "لا يوجد ملف يطابق عوامل التصفية المحددة.",

    loading:
      "جارٍ تحميل الملفات...",

    error:
      "تعذر تحميل الملفات.",

    retry:
      "إعادة المحاولة",

    detailTitle:
      "تفاصيل الملف",

    close:
      "إغلاق",

    reference:
      "المرجع",

    created:
      "تاريخ الإنشاء",

    lastUpdate:
      "آخر تحديث",

    description:
      "الحالة المصرح بها",

    evidenceSection:
      "أدلة الملف",

    evidenceSectionText:
      "اطلع على العناصر التي احتفظت بها الضحية فقط عندما تكون ضرورية للمتابعة.",

    evidencePlural:
      "أدلة",

    evidenceSingular:
      "دليل",

    evidenceView:
      "عرض",

    evidenceClose:
      "إخفاء",

    evidenceOpenLink:
      "فتح الرابط",

    evidenceOpenFile:
      "فتح الملف",

    evidenceLoading:
      "جارٍ تحميل الدليل...",

    evidenceError:
      "تعذر عرض هذا الدليل.",

    noEvidence:
      "لا يوجد دليل مسجل في هذا الملف.",

    evidenceTypes: {
      screenshot:
        "لقطة شاشة",

      file:
        "ملف",

      link:
        "رابط",

      note:
        "ملاحظة",
    },

    fileName:
      "الملف",

    fileSize:
      "الحجم",

    addedOn:
      "أضيف في",

    privacyTitle:
      "وصول إداري محدود",

    privacyText:
      "لا تظهر معلومات الهوية الكاملة إلا بعد فتح الملف صراحة. تظهر بيانات الأدلة الوصفية هنا، بينما يتطلب عرض محتواها إجراءً صريحًا. لا يتم عرض مسار تخزين الملفات.",

    actionPlan:
      "خطة العمل",

    completedActions:
      "إجراءات منجزة",

    exportTitle:
      "الملف الكامل",

    exportText:
      "أنشئ ملف PDF واحدًا يحتوي على الحالة وخطة العمل وجميع الأدلة مباشرة داخل التقرير، بما في ذلك لقطات الشاشة والملاحظات والروابط القابلة للنقر والمستندات الداعمة.",

    exportButton:
      "تحميل PDF الكامل",

    exporting:
      "جارٍ إنشاء PDF...",

    exportSuccess:
      "بدأ تحميل ملف PDF الكامل.",

    exportError:
      "تعذر إنشاء ملف PDF الكامل.",

    integrity:
      "سلامة SHA-256",

    deletionRequest:
      "طلب حذف الملف",

    deletionPending:
      "طلب حذف",

    deletionText:
      "طلبت الضحية حذف هذا الملف. يمكنك قبول الحذف النهائي أو رفض الطلب.",

    approveDeletion:
      "قبول الحذف",

    rejectDeletion:
      "رفض الطلب",

    deletionProcessing:
      "جارٍ المعالجة...",

    deletionApproved:
      "تم حذف الملف نهائيًا.",

    deletionRejected:
      "تم رفض طلب الحذف.",

    confirmApproveDeletion:
      "هل تؤكد الحذف النهائي لهذا الملف والبيانات المرتبطة به؟",

    confirmRejectDeletion:
      "هل تؤكد رفض طلب الحذف؟",

    deletionDecisionError:
      "تعذر معالجة طلب الحذف.",

    changeStatus:
      "مرحلة معالجة الملف",

    workflowHelp:
      "حدد المرحلة الحالية لمتابعة الملف من طرف فريق EMC.",

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

    saveWorkflow:
      "تحديث المرحلة",

    saving:
      "جارٍ الحفظ...",

    saved:
      "تم تحديث مرحلة معالجة الملف.",

    updateError:
      "تعذر تعديل مرحلة معالجة الملف.",

    unknown:
      "غير محدد",
  },
};


function readCookie(
  name,
) {
  const prefix =
    `${name}=`;

  const raw =
    document.cookie
      .split("; ")
      .find(
        (entry) =>
          entry.startsWith(
            prefix
          )
      );

  return raw
    ? decodeURIComponent(
        raw.slice(
          prefix.length
        )
      )
    : null;
}


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


function workflowLabel(
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


function formatDate(
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
        "short",

      year:
        "numeric",
    }
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


function formatFileSize(
  value,
) {
  const bytes =
    Number(value);

  if (
    !Number.isFinite(
      bytes
    )
    || bytes <= 0
  ) {
    return "—";
  }

  if (bytes < 1024) {
    return `${bytes} o`;
  }

  if (
    bytes
    < 1024 * 1024
  ) {
    return `${(
      bytes / 1024
    ).toFixed(1)} Ko`;
  }

  return `${(
    bytes
    / (
      1024
      * 1024
    )
  ).toFixed(1)} Mo`;
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
      className={`admin-cases-summary-card tone-${tone}`}
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


function Cases() {
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
    query,
    setQuery,
  ] = useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] = useState("");

  const [
    languageFilter,
    setLanguageFilter,
  ] = useState("");

  const [
    priorityFilter,
    setPriorityFilter,
  ] = useState("");

  const [
    intentFilter,
    setIntentFilter,
  ] = useState("");

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
    selectedCase,
    setSelectedCase,
  ] = useState(null);

  const [
    detailLoading,
    setDetailLoading,
  ] = useState(false);

  const [
    updateStatus,
    setUpdateStatus,
  ] = useState("idle");

  const [
    workflowDraft,
    setWorkflowDraft,
  ] = useState("new");

  const [
    detailMessage,
    setDetailMessage,
  ] = useState("");

  const [
    selectedEvidence,
    setSelectedEvidence,
  ] = useState(null);

  const [
    evidenceLoading,
    setEvidenceLoading,
  ] = useState(null);

  const [
    evidenceError,
    setEvidenceError,
  ] = useState("");

  const [
    exportStatus,
    setExportStatus,
  ] = useState("idle");

  const [
    exportMessage,
    setExportMessage,
  ] = useState("");

  const [
    deletionDecisionStatus,
    setDeletionDecisionStatus,
  ] = useState("idle");


  const params =
    useMemo(
      () => {
        const search =
          new URLSearchParams();

        const cleanQuery =
          query.trim();

        if (cleanQuery) {
          search.set(
            "q",
            cleanQuery
          );
        }

        if (statusFilter) {
          search.set(
            "status",
            statusFilter
          );
        }

        if (languageFilter) {
          search.set(
            "language",
            languageFilter
          );
        }

        if (priorityFilter) {
          search.set(
            "emergency",
            priorityFilter
          );
        }

        if (intentFilter) {
          search.set(
            "intent",
            intentFilter
          );
        }

        const value =
          search.toString();

        return value
          ? `?${value}`
          : "";
      },
      [
        query,
        statusFilter,
        languageFilter,
        priorityFilter,
        intentFilter,
      ]
    );


  const loadCases =
    useCallback(
      async () => {
        setLoading(true);
        setError("");

        try {
          const response =
            await fetch(
              `${API_BASE_URL}/admin/cases${params}`,
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
        } catch (
          loadError
        ) {
          console.error(
            "Admin cases:",
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
        params,
      ]
    );


  useEffect(
    () => {
      const timer =
        window.setTimeout(
          () => {
            loadCases();
          },
          query
            ? 250
            : 0
        );

      return () =>
        window.clearTimeout(
          timer
        );
    },
    [
      loadCases,
      query,
    ]
  );


  const openCase =
    async (
      caseId
    ) => {
      setDetailLoading(true);
      setDetailMessage("");
      setSelectedEvidence(null);
      setEvidenceError("");
      setExportStatus("idle");
      setExportMessage("");
      setDeletionDecisionStatus("idle");

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

        setWorkflowDraft(
          payload?.workflow_status
          || (
            payload?.status
            === "closed"
              ? "closed"
              : "new"
          )
        );

        setUpdateStatus(
          "idle"
        );
      } catch (
        detailError
      ) {
        setDetailMessage(
          detailError.message
          || labels.error
        );
      } finally {
        setDetailLoading(false);
      }
    };


  const downloadCompleteCase =
    async () => {
      if (
        !selectedCase
        || exportStatus
          === "loading"
      ) {
        return;
      }

      const csrfToken =
        readCookie(
          "csrf_token"
        );

      if (!csrfToken) {
        setExportStatus(
          "error"
        );

        setExportMessage(
          labels.exportError
        );

        return;
      }

      setExportStatus(
        "loading"
      );

      setExportMessage("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/admin/cases/${selectedCase.id}/export`,
            {
              method:
                "POST",

              credentials:
                "include",

              headers: {
                Accept:
                  "application/pdf",

                "X-CSRF-Token":
                  csrfToken,
              },
            }
          );

        if (!response.ok) {
          const payload =
            await response
              .json()
              .catch(
                () => null
              );

          throw new Error(
            typeof payload?.detail
              === "string"
              ? payload.detail
              : labels.exportError
          );
        }

        const blob =
          await response.blob();

        const objectUrl =
          URL.createObjectURL(
            blob
          );

        const anchor =
          document.createElement(
            "a"
          );

        anchor.href =
          objectUrl;

        anchor.download =
          `Dossier_EMC_${shortId(
            selectedCase.id
          )}.pdf`;

        document.body.appendChild(
          anchor
        );

        anchor.click();

        anchor.remove();

        window.setTimeout(
          () => {
            URL.revokeObjectURL(
              objectUrl
            );
          },
          60000
        );

        setExportStatus(
          "success"
        );

        setExportMessage(
          labels.exportSuccess
        );
      } catch (
        exportError
      ) {
        setExportStatus(
          "error"
        );

        setExportMessage(
          exportError.message
          || labels.exportError
        );
      }
    };


  const consultEvidence =
    async (
      evidence
    ) => {
      if (
        !selectedCase
        || evidenceLoading
      ) {
        return;
      }

      if (
        selectedEvidence?.id
        === evidence.id
      ) {
        setSelectedEvidence(
          null
        );
        setEvidenceError("");
        return;
      }

      setEvidenceLoading(
        evidence.id
      );
      setEvidenceError("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/admin/cases/${selectedCase.id}/evidence/${evidence.id}`,
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
              : labels.evidenceError
          );
        }

        if (
          payload.type === "file"
          || payload.type
            === "screenshot"
        ) {
          const fileResponse =
            await fetch(
              `${API_BASE_URL}/admin/cases/${selectedCase.id}/evidence/${payload.id}/download`,
              {
                credentials:
                  "include",
              }
            );

          if (!fileResponse.ok) {
            const errorPayload =
              await fileResponse
                .json()
                .catch(
                  () => null
                );

            throw new Error(
              typeof errorPayload?.detail
                === "string"
                ? errorPayload.detail
                : labels.evidenceError
            );
          }

          const blob =
            await fileResponse.blob();

          const objectUrl =
            URL.createObjectURL(
              blob
            );

          window.open(
            objectUrl,
            "_blank",
            "noopener,noreferrer"
          );

          window.setTimeout(
            () => {
              URL.revokeObjectURL(
                objectUrl
              );
            },
            60000
          );

          return;
        }

        setSelectedEvidence(
          payload
        );
      } catch (
        loadEvidenceError
      ) {
        setEvidenceError(
          loadEvidenceError.message
          || labels.evidenceError
        );
      } finally {
        setEvidenceLoading(
          null
        );
      }
    };


  const decideDeletionRequest =
    async (
      decision
    ) => {
      if (
        !selectedCase
        || !selectedCase.deletion_requested
        || deletionDecisionStatus
          === "saving"
      ) {
        return;
      }

      const confirmed =
        window.confirm(
          decision === "approve"
            ? labels.confirmApproveDeletion
            : labels.confirmRejectDeletion
        );

      if (!confirmed) {
        return;
      }

      const csrfToken =
        readCookie(
          "csrf_token"
        );

      if (!csrfToken) {
        setDetailMessage(
          labels.deletionDecisionError
        );
        setDeletionDecisionStatus(
          "error"
        );
        return;
      }

      setDeletionDecisionStatus(
        "saving"
      );
      setDetailMessage("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/admin/cases/${selectedCase.id}/deletion-request`,
            {
              method:
                "PATCH",

              credentials:
                "include",

              headers: {
                "Content-Type":
                  "application/json",

                Accept:
                  "application/json",

                "X-CSRF-Token":
                  csrfToken,
              },

              body:
                JSON.stringify({
                  decision,
                }),
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
              : labels.deletionDecisionError
          );
        }

        if (
          payload?.outcome
          === "deleted"
        ) {
          setDeletionDecisionStatus(
            "success"
          );

          setDetailMessage(
            payload.message
            || labels.deletionApproved
          );

          await loadCases();

          window.setTimeout(
            () => {
              closeModal();
            },
            700
          );

          return;
        }

        setSelectedCase(
          (current) => (
            current
              ? {
                  ...current,
                  deletion_requested:
                    false,
                  deletion_request_status:
                    "rejected",
                }
              : current
          )
        );

        setDeletionDecisionStatus(
          "success"
        );

        setDetailMessage(
          payload?.message
          || labels.deletionRejected
        );

        await loadCases();

      } catch (
        deletionError
      ) {
        setDeletionDecisionStatus(
          "error"
        );

        setDetailMessage(
          deletionError.message
          || labels.deletionDecisionError
        );
      }
    };


  const closeModal =
    () => {
      if (
        updateStatus
        === "saving"
      ) {
        return;
      }

      setSelectedCase(null);
      setSelectedEvidence(null);
      setEvidenceError("");
      setEvidenceLoading(null);
      setExportStatus("idle");
      setExportMessage("");
      setDeletionDecisionStatus("idle");
      setDetailMessage("");
      setUpdateStatus(
        "idle"
      );

      setWorkflowDraft(
        "new"
      );
    };


  const changeWorkflowStatus =
    async () => {
      if (
        !selectedCase
        || updateStatus
          === "saving"
      ) {
        return;
      }

      const currentWorkflow =
        selectedCase.workflow_status
        || (
          selectedCase.status
          === "closed"
            ? "closed"
            : "new"
        );

      if (
        workflowDraft
        === currentWorkflow
      ) {
        return;
      }

      const csrfToken =
        readCookie(
          "csrf_token"
        );

      if (!csrfToken) {
        setDetailMessage(
          labels.updateError
        );

        setUpdateStatus(
          "error"
        );

        return;
      }

      setUpdateStatus(
        "saving"
      );

      setDetailMessage("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/admin/cases/${selectedCase.id}/workflow-status`,
            {
              method:
                "PATCH",

              credentials:
                "include",

              headers: {
                "Content-Type":
                  "application/json",

                Accept:
                  "application/json",

                "X-CSRF-Token":
                  csrfToken,
              },

              body:
                JSON.stringify({
                  workflow_status:
                    workflowDraft,
                }),
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
              : labels.updateError
          );
        }

        setSelectedCase(
          payload
        );

        setWorkflowDraft(
          payload?.workflow_status
          || workflowDraft
        );

        setUpdateStatus(
          "success"
        );

        setDetailMessage(
          labels.saved
        );

        await loadCases();

      } catch (
        statusError
      ) {
        setUpdateStatus(
          "error"
        );

        setDetailMessage(
          statusError.message
          || labels.updateError
        );
      }
    };


  const resetFilters =
    () => {
      setQuery("");
      setStatusFilter("");
      setLanguageFilter("");
      setPriorityFilter("");
      setIntentFilter("");
    };


  if (
    loading
    && !data
  ) {
    return (
      <div className="guided-dashboard admin-cases-page">
        <section className="admin-cases-loading">
          <span className="admin-cases-spinner" />

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
      <div className="guided-dashboard admin-cases-page">
        <section className="guided-no-case admin-cases-error">
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
              loadCases
            }
          >
            {labels.retry}
          </button>
        </section>
      </div>
    );
  }


  const summary =
    data?.summary
    || {};


  const items =
    data?.items
    || [];


  return (
    <motion.div
      key={language}
      className="guided-dashboard admin-cases-page"
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

      <section className="admin-cases-heading">
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
      </section>


      {/* =================================================
          SUMMARY
      ================================================= */}

      <section className="admin-cases-summary-grid">
        <SummaryCard
          icon="folder"
          tone="purple"
          label={
            labels.total
          }
          value={
            summary.total_cases
            || 0
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="check"
          tone="green"
          label={
            labels.active
          }
          value={
            summary.active_cases
            || 0
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="lock"
          tone="blue"
          label={
            labels.closed
          }
          value={
            summary.closed_cases
            || 0
          }
          reducedMotion={
            reducedMotion
          }
        />

        <SummaryCard
          icon="alert"
          tone="orange"
          label={
            labels.priority
          }
          value={
            summary.priority_cases
            || 0
          }
          reducedMotion={
            reducedMotion
          }
        />
      </section>


      {/* =================================================
          FILTERS
      ================================================= */}

      <section className="guided-section admin-cases-filter-card">
        <div className="admin-cases-filter-top">
          <div className="admin-cases-search">
            <DashboardIcon
              name="folder"
              size={19}
            />

            <input
              type="search"
              value={
                query
              }
              onChange={
                (event) =>
                  setQuery(
                    event.target.value
                  )
              }
              placeholder={
                labels.search
              }
            />
          </div>

          <div className="admin-cases-results">
            <strong>
              {data?.filtered_count
                ?? items.length}
            </strong>

            <span>
              {labels.results}
            </span>
          </div>
        </div>

        <div className="admin-cases-filters">
          <select
            value={
              statusFilter
            }
            onChange={
              (event) =>
                setStatusFilter(
                  event.target.value
                )
            }
          >
            <option value="">
              {labels.allStatuses}
            </option>

            <option value="active">
              {labels.activeStatus}
            </option>

            <option value="closed">
              {labels.closedStatus}
            </option>
          </select>

          <select
            value={
              languageFilter
            }
            onChange={
              (event) =>
                setLanguageFilter(
                  event.target.value
                )
            }
          >
            <option value="">
              {labels.allLanguages}
            </option>

            <option value="fr">
              {labels.french}
            </option>

            <option value="ar">
              {labels.arabic}
            </option>
          </select>

          <select
            value={
              priorityFilter
            }
            onChange={
              (event) =>
                setPriorityFilter(
                  event.target.value
                )
            }
          >
            <option value="">
              {labels.allPriorities}
            </option>

            <option value="true">
              {labels.priorityOnly}
            </option>

            <option value="false">
              {labels.normalOnly}
            </option>
          </select>

          <select
            value={
              intentFilter
            }
            onChange={
              (event) =>
                setIntentFilter(
                  event.target.value
                )
            }
          >
            <option value="">
              {labels.allIntents}
            </option>

            {(
              data?.intents
              || []
            ).map(
              (intent) => (
                <option
                  value={
                    intent
                  }
                  key={
                    intent
                  }
                >
                  {displayIntent(
                    intent,
                    language
                  )}
                </option>
              )
            )}
          </select>

          <button
            type="button"
            className="admin-cases-reset"
            onClick={
              resetFilters
            }
          >
            {labels.reset}
          </button>
        </div>
      </section>


      {/* =================================================
          TABLE / LIST
      ================================================= */}

      <section className="guided-section admin-cases-list-section">
        {loading && (
          <div className="admin-cases-soft-loading">
            {labels.loading}
          </div>
        )}

        {items.length === 0 ? (
          <div className="admin-cases-empty">
            <span>
              <DashboardIcon
                name="folder"
                size={34}
              />
            </span>

            <p>
              {labels.noCases}
            </p>
          </div>
        ) : (
          <div className="admin-cases-table-wrap">
            <table className="admin-cases-table">
              <thead>
                <tr>
                  <th>
                    {labels.case}
                  </th>

                  <th>
                    {labels.victim}
                  </th>

                  <th>
                    {labels.situation}
                  </th>

                  <th>
                    {labels.language}
                  </th>

                  <th>
                    {labels.progress}
                  </th>

                  <th>
                    {labels.evidence}
                  </th>

                  <th>
                    {labels.status}
                  </th>

                  <th>
                    {labels.updated}
                  </th>

                  <th>
                    {labels.actions}
                  </th>
                </tr>
              </thead>

              <tbody>
                {items.map(
                  (item) => (
                    <tr
                      key={
                        item.id
                      }
                      className={
                        item.emergency
                          ? "is-emergency"
                          : ""
                      }
                    >
                      <td>
                        <div className="admin-case-reference">
                          <span>
                            <DashboardIcon
                              name={
                                item.emergency
                                  ? "alert"
                                  : "folder"
                              }
                              size={18}
                            />
                          </span>

                          <div>
                            <strong>
                              #{shortId(
                                item.id
                              )}
                            </strong>

                            {item.emergency && (
                              <em>
                                {labels.urgent}
                              </em>
                            )}

                            {item.deletion_requested && (
                              <em
                                style={{
                                  marginTop: 4,
                                  display: "inline-flex",
                                  width: "fit-content",
                                  padding: "3px 7px",
                                  borderRadius: 999,
                                  background: "#fff0f2",
                                  color: "#b13c52",
                                  fontStyle: "normal",
                                  fontWeight: 800,
                                  fontSize: 11,
                                }}
                              >
                                {labels.deletionPending}
                              </em>
                            )}
                          </div>
                        </div>
                      </td>

                      <td>
                        <div
                          style={{
                            display: "grid",
                            gap: 4,
                            minWidth: 190,
                          }}
                        >
                          <strong className="admin-case-username">
                            {item.victim_full_name
                              || item.victim_username
                              || labels.unknown}
                          </strong>

                          <small
                            style={{
                              opacity: 0.72,
                            }}
                          >
                            {labels.emcId}
                            {" : "}
                            {item.victim_emc_id
                              || "—"}
                          </small>

                          {item.victim_phone && (
                            <small
                              style={{
                                opacity: 0.72,
                              }}
                              dir="ltr"
                            >
                              {item.victim_phone}
                            </small>
                          )}

                          {item.victim_cin_masked && (
                            <small
                              style={{
                                opacity: 0.72,
                              }}
                              dir="ltr"
                            >
                              {labels.cin}
                              {" : "}
                              {item.victim_cin_masked}
                            </small>
                          )}

                          <small
                            style={{
                              fontWeight: 700,
                              opacity: 0.78,
                            }}
                          >
                            {item.victim_identity_complete
                              ? labels.identityComplete
                              : labels.identityIncomplete}
                          </small>
                        </div>
                      </td>

                      <td>
                        <span className="admin-case-intent">
                          {displayIntent(
                            item.detected_intent,
                            language
                          )}
                        </span>
                      </td>

                      <td>
                        <span className="admin-case-language">
                          {item.language
                            ? item.language.toUpperCase()
                            : "—"}
                        </span>
                      </td>

                      <td>
                        {item.has_action_plan ? (
                          <div className="admin-case-progress">
                            <div>
                              <span
                                style={{
                                  width:
                                    `${item.action_progress}%`,
                                }}
                              />
                            </div>

                            <small>
                              {item.completed_actions}
                              /
                              {item.total_actions}
                              {" "}
                              ({Math.round(
                                item.action_progress
                              )}%)
                            </small>
                          </div>
                        ) : (
                          <span className="admin-case-muted">
                            {labels.noPlan}
                          </span>
                        )}
                      </td>

                      <td>
                        <span className="admin-case-count">
                          <DashboardIcon
                            name="clip"
                            size={16}
                          />

                          {item.evidence_count}
                        </span>
                      </td>

                      <td>
                        <span
                          className={
                            `admin-case-status ${item.status}`
                          }
                        >
                          {workflowLabel(
                            item.workflow_status
                            || (
                              item.status
                              === "closed"
                                ? "closed"
                                : "new"
                            ),
                            labels
                          )}
                        </span>
                      </td>

                      <td>
                        <time>
                          {formatDate(
                            item.updated_at,
                            language
                          )}
                        </time>
                      </td>

                      <td>
                        <button
                          type="button"
                          className="admin-case-view-button"
                          onClick={() =>
                            openCase(
                              item.id
                            )
                          }
                        >
                          {labels.view}

                          <DashboardIcon
                            name="arrow"
                            size={16}
                          />
                        </button>
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
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
              className="admin-case-modal-backdrop"
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
                closeModal
              }
            />

            <motion.aside
              className="admin-case-modal"
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
                <div className="admin-case-modal-loading">
                  <span className="admin-cases-spinner" />

                  <p>
                    {labels.loading}
                  </p>
                </div>
              ) : selectedCase ? (
                <>
                  <header className="admin-case-modal-header">
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
                        closeModal
                      }
                      aria-label={
                        labels.close
                      }
                    >
                      ×
                    </button>
                  </header>

                  <div className="admin-case-modal-body">
                    <div className="admin-case-detail-summary">
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
                          {workflowLabel(
                            selectedCase.workflow_status
                            || (
                              selectedCase.status
                              === "closed"
                                ? "closed"
                                : "new"
                            ),
                            labels
                          )}
                        </strong>
                      </div>
                    </div>

                    {selectedCase.emergency && (
                      <div className="admin-case-emergency-note">
                        <DashboardIcon
                          name="alert"
                          size={20}
                        />

                        <strong>
                          {labels.urgent}
                        </strong>
                      </div>
                    )}

                    <section className="admin-case-detail-section">
                      <h3>
                        {labels.identity}
                      </h3>

                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns:
                            "repeat(2, minmax(0, 1fr))",
                          gap: 12,
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
                                padding: "12px 14px",
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

                    <section className="admin-case-export-card">
                      <span className="admin-case-export-icon">
                        <DashboardIcon
                          name="folder"
                          size={24}
                        />
                      </span>

                      <div className="admin-case-export-copy">
                        <div>
                          <h3>
                            {labels.exportTitle}
                          </h3>

                          <span className="admin-case-integrity-badge">
                            {labels.integrity}
                          </span>
                        </div>

                        <p>
                          {labels.exportText}
                        </p>
                      </div>

                      <button
                        type="button"
                        className="admin-case-export-button"
                        disabled={
                          exportStatus
                          === "loading"
                        }
                        onClick={
                          downloadCompleteCase
                        }
                      >
                        {exportStatus === "loading"
                          ? labels.exporting
                          : labels.exportButton}
                      </button>

                      {exportMessage && (
                        <div
                          className={
                            `admin-case-export-message ${
                              exportStatus === "success"
                                ? "success"
                                : "error"
                            }`
                          }
                        >
                          {exportMessage}
                        </div>
                      )}
                    </section>

                    <section className="admin-case-detail-section">
                      <h3>
                        {labels.description}
                      </h3>

                      <p className="admin-case-description">
                        {selectedCase.description}
                      </p>
                    </section>

                    <section className="admin-case-detail-grid">
                      <div>
                        <span>
                          <DashboardIcon
                            name="clock"
                            size={18}
                          />
                        </span>

                        <div>
                          <small>
                            {labels.created}
                          </small>

                          <strong>
                            {formatDate(
                              selectedCase.created_at,
                              language
                            )}
                          </strong>
                        </div>
                      </div>

                      <div>
                        <span>
                          <DashboardIcon
                            name="clock"
                            size={18}
                          />
                        </span>

                        <div>
                          <small>
                            {labels.lastUpdate}
                          </small>

                          <strong>
                            {formatDate(
                              selectedCase.updated_at,
                              language
                            )}
                          </strong>
                        </div>
                      </div>

                      <div>
                        <span>
                          <DashboardIcon
                            name="clip"
                            size={18}
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
                            size={18}
                          />
                        </span>

                        <div>
                          <small>
                            {labels.actionPlan}
                          </small>

                          <strong>
                            {selectedCase.has_action_plan
                              ? `${selectedCase.completed_actions}/${selectedCase.total_actions} ${labels.completedActions}`
                              : labels.noPlan}
                          </strong>
                        </div>
                      </div>
                    </section>

                    <section className="admin-case-evidence-section">
                      <div className="admin-case-evidence-heading">
                        <div>
                          <h3>
                            {labels.evidenceSection}
                          </h3>

                          <p>
                            {labels.evidenceSectionText}
                          </p>
                        </div>

                        <span>
                          {selectedCase.evidence_count}{" "}
                          {selectedCase.evidence_count === 1
                            ? labels.evidenceSingular
                            : labels.evidencePlural}
                        </span>
                      </div>

                      {(
                        selectedCase.evidences
                        || []
                      ).length === 0 ? (
                        <div className="admin-case-evidence-empty">
                          <DashboardIcon
                            name="clip"
                            size={26}
                          />

                          <p>
                            {labels.noEvidence}
                          </p>
                        </div>
                      ) : (
                        <div className="admin-case-evidence-list">
                          {selectedCase.evidences.map(
                            (evidence) => {
                              const isSelected =
                                selectedEvidence?.id
                                === evidence.id;

                              const isLoadingEvidence =
                                evidenceLoading
                                === evidence.id;

                              return (
                                <article
                                  className={
                                    `admin-case-evidence-item ${
                                      isSelected
                                        ? "is-selected"
                                        : ""
                                    }`
                                  }
                                  key={
                                    evidence.id
                                  }
                                >
                                  <div className="admin-case-evidence-item-main">
                                    <span className="admin-case-evidence-icon">
                                      <DashboardIcon
                                        name="clip"
                                        size={19}
                                      />
                                    </span>

                                    <div className="admin-case-evidence-copy">
                                      <div className="admin-case-evidence-title-row">
                                        <strong>
                                          {evidence.title}
                                        </strong>

                                        <span>
                                          {labels.evidenceTypes[
                                            evidence.type
                                          ]
                                          || evidence.type}
                                        </span>
                                      </div>

                                      <div className="admin-case-evidence-meta">
                                        <small>
                                          {labels.addedOn}{" "}
                                          {formatDate(
                                            evidence.created_at,
                                            language
                                          )}
                                        </small>

                                        {evidence.original_filename && (
                                          <small dir="ltr">
                                            {evidence.original_filename}
                                          </small>
                                        )}

                                        {evidence.file_size && (
                                          <small>
                                            {formatFileSize(
                                              evidence.file_size
                                            )}
                                          </small>
                                        )}
                                      </div>
                                    </div>

                                    <button
                                      type="button"
                                      className="admin-case-evidence-view"
                                      disabled={
                                        isLoadingEvidence
                                      }
                                      onClick={() =>
                                        consultEvidence(
                                          evidence
                                        )
                                      }
                                    >
                                      {isLoadingEvidence
                                        ? labels.evidenceLoading
                                        : isSelected
                                          ? labels.evidenceClose
                                          : labels.evidenceView}
                                    </button>
                                  </div>

                                  <AnimatePresence>
                                    {isSelected
                                      && selectedEvidence && (
                                      <motion.div
                                        className="admin-case-evidence-detail"
                                        initial={
                                          reducedMotion
                                            ? false
                                            : {
                                                opacity: 0,
                                                height: 0,
                                              }
                                        }
                                        animate={{
                                          opacity: 1,
                                          height: "auto",
                                        }}
                                        exit={{
                                          opacity: 0,
                                          height: 0,
                                        }}
                                      >
                                        {selectedEvidence.type === "note" && (
                                          <p className="admin-case-evidence-note-text">
                                            {selectedEvidence.note
                                              || "—"}
                                          </p>
                                        )}

                                        {selectedEvidence.type === "link" && (
                                          <div className="admin-case-evidence-link">
                                            <code dir="ltr">
                                              {selectedEvidence.url
                                                || "—"}
                                            </code>

                                            {selectedEvidence.url && (
                                              <a
                                                href={
                                                  selectedEvidence.url
                                                }
                                                target="_blank"
                                                rel="noopener noreferrer"
                                              >
                                                {labels.evidenceOpenLink}
                                              </a>
                                            )}
                                          </div>
                                        )}
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                                </article>
                              );
                            }
                          )}
                        </div>
                      )}

                      {evidenceError && (
                        <div className="admin-case-evidence-error">
                          {evidenceError}
                        </div>
                      )}
                    </section>

                    {selectedCase.deletion_requested && (
                      <section
                        style={{
                          marginTop: 18,
                          padding: 16,
                          border:
                            "1px solid rgba(185,62,83,0.22)",
                          borderRadius: 14,
                          background:
                            "linear-gradient(135deg, #fff7f8, #fcf8ff)",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            gap: 12,
                            alignItems: "flex-start",
                          }}
                        >
                          <span
                            style={{
                              width: 36,
                              height: 36,
                              display: "inline-flex",
                              alignItems: "center",
                              justifyContent: "center",
                              borderRadius: 11,
                              background:
                                "rgba(185,62,83,0.10)",
                              color: "#b13c52",
                              fontWeight: 900,
                              flex: "0 0 auto",
                            }}
                          >
                            !
                          </span>

                          <div>
                            <h3
                              style={{
                                margin: 0,
                              }}
                            >
                              {labels.deletionRequest}
                            </h3>

                            <p
                              style={{
                                margin:
                                  "6px 0 0",
                                lineHeight: 1.55,
                              }}
                            >
                              {labels.deletionText}
                            </p>
                          </div>
                        </div>

                        <div
                          style={{
                            display: "flex",
                            gap: 10,
                            flexWrap: "wrap",
                            marginTop: 14,
                          }}
                        >
                          <button
                            type="button"
                            disabled={
                              deletionDecisionStatus
                              === "saving"
                            }
                            onClick={() =>
                              decideDeletionRequest(
                                "approve"
                              )
                            }
                            style={{
                              border: 0,
                              borderRadius: 11,
                              padding:
                                "10px 14px",
                              background:
                                "#b93e53",
                              color: "#fff",
                              fontWeight: 800,
                              cursor:
                                deletionDecisionStatus
                                === "saving"
                                  ? "not-allowed"
                                  : "pointer",
                            }}
                          >
                            {deletionDecisionStatus
                              === "saving"
                              ? labels.deletionProcessing
                              : labels.approveDeletion}
                          </button>

                          <button
                            type="button"
                            disabled={
                              deletionDecisionStatus
                              === "saving"
                            }
                            onClick={() =>
                              decideDeletionRequest(
                                "reject"
                              )
                            }
                            style={{
                              border:
                                "1px solid rgba(112,72,184,0.25)",
                              borderRadius: 11,
                              padding:
                                "10px 14px",
                              background:
                                "#fff",
                              color:
                                "#7048b8",
                              fontWeight: 800,
                              cursor:
                                deletionDecisionStatus
                                === "saving"
                                  ? "not-allowed"
                                  : "pointer",
                            }}
                          >
                            {labels.rejectDeletion}
                          </button>
                        </div>
                      </section>
                    )}

                    <section className="admin-case-privacy-note">
                      <span>
                        <DashboardIcon
                          name="lock"
                          size={20}
                        />
                      </span>

                      <div>
                        <strong>
                          {labels.privacyTitle}
                        </strong>

                        <p>
                          {labels.privacyText}
                        </p>
                      </div>
                    </section>

                    <section
                      className="admin-case-status-action"
                      style={{
                        alignItems:
                          "flex-end",
                        gap: 16,
                        flexWrap:
                          "wrap",
                      }}
                    >
                      <div
                        style={{
                          flex:
                            "1 1 280px",
                        }}
                      >
                        <h3>
                          {labels.changeStatus}
                        </h3>

                        <p>
                          {labels.workflowHelp}
                        </p>

                        <select
                          value={
                            workflowDraft
                          }
                          disabled={
                            updateStatus
                            === "saving"
                          }
                          onChange={
                            (event) => {
                              setWorkflowDraft(
                                event.target.value
                              );

                              setUpdateStatus(
                                "idle"
                              );

                              setDetailMessage(
                                ""
                              );
                            }
                          }
                          style={{
                            width:
                              "100%",
                            minHeight:
                              44,
                            marginTop:
                              10,
                            padding:
                              "0 12px",
                            border:
                              "1px solid #ded7eb",
                            borderRadius:
                              11,
                            background:
                              "#ffffff",
                            color:
                              "#34284b",
                            font:
                              "inherit",
                            fontWeight:
                              700,
                          }}
                        >
                          <option value="new">
                            {labels.workflowNew}
                          </option>

                          <option value="in_progress">
                            {labels.workflowInProgress}
                          </option>

                          <option value="waiting_information">
                            {labels.workflowWaiting}
                          </option>

                          <option value="resolved">
                            {labels.workflowResolved}
                          </option>

                          <option value="closed">
                            {labels.workflowClosed}
                          </option>
                        </select>
                      </div>

                      <button
                        type="button"
                        className={
                          workflowDraft
                          === "closed"
                            ? "close-case"
                            : "reopen-case"
                        }
                        disabled={
                          updateStatus
                          === "saving"
                          || workflowDraft
                          === (
                            selectedCase.workflow_status
                            || (
                              selectedCase.status
                              === "closed"
                                ? "closed"
                                : "new"
                            )
                          )
                        }
                        onClick={
                          changeWorkflowStatus
                        }
                      >
                        {updateStatus
                          === "saving"
                          ? labels.saving
                          : labels.saveWorkflow}
                      </button>
                    </section>

                    {detailMessage && (
                      <div
                        className={
                          `admin-case-detail-message ${
                            updateStatus === "success"
                              ? "success"
                              : "error"
                          }`
                        }
                      >
                        {detailMessage}
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


export default Cases;