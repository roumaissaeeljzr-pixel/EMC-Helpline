import { useEffect, useMemo, useState } from "react";
import { useLanguage } from "../context/LanguageContext.jsx";
import "./CaseFile.css";
import "./CaseFileDeletion.css";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

const SELECTED_CASE_STORAGE_KEY =
  "emc_selected_case_id";

function readCookie(name) {
  const prefix = `${name}=`;

  const raw = document.cookie
    .split("; ")
    .find((entry) =>
      entry.startsWith(prefix)
    );

  return raw
    ? decodeURIComponent(
        raw.slice(prefix.length)
      )
    : null;
}


function formatDate(value, language) {
  if (!value) {
    return "—";
  }

  try {
    return new Intl.DateTimeFormat(
      language === "ar" ? "ar-MA" : "fr-FR",
      {
        dateStyle: "medium",
        timeStyle: "short",
      }
    ).format(new Date(value));
  } catch {
    return value;
  }
}

function CaseFile() {
  const { language } = useLanguage();
  const isArabic = language === "ar";

  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState(
    () =>
      window.localStorage.getItem(
        SELECTED_CASE_STORAGE_KEY
      )
      || null
  );

  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");

  const [
    deletionStatus,
    setDeletionStatus,
  ] = useState(null);

  const [
    deletionLoading,
    setDeletionLoading,
  ] = useState(false);

  const [
    deletionSubmitting,
    setDeletionSubmitting,
  ] = useState(false);

  const [
    deletionMessage,
    setDeletionMessage,
  ] = useState("");

  const [
    deletionMessageType,
    setDeletionMessageType,
  ] = useState("");

  const copy = useMemo(
    () =>
      isArabic
        ? {
            title: "ملفي",
            subtitle:
              "اعرض الملفات المرتبطة بحسابك فقط. لا يمكن لمستخدم آخر الوصول إليها.",
            loading: "جارٍ تحميل الملف...",
            emptyTitle: "لا يوجد ملف بعد",
            emptyText:
              "لم يتم تسجيل أي ملف لهذا الحساب حتى الآن.",
            retry: "إعادة المحاولة",
            detectedIntent: "نوع الحالة",
            status: "الحالة",
            language: "اللغة",
            emergency: "حالة استعجالية",
            description: "وصف الحالة",
            createdAt: "تاريخ الإنشاء",
            updatedAt: "آخر تحديث",
            yes: "نعم",
            no: "لا",
            active: "نشط",
            closed: "مغلق",
            french: "الفرنسية",
            arabic: "العربية",
            dossierList: "ملفاتي",
            details: "تفاصيل الملف",

            managementTitle:
              "إدارة الملف",

            managementText:
              "يمكنك إدارة حذف هذا الملف حسب حالة متابعته من طرف فريق EMC.",

            deleteNow:
              "حذف الملف نهائيًا",

            requestDeletion:
              "طلب حذف الملف",

            deletionPending:
              "طلب الحذف قيد المعالجة",

            deleteImmediateInfo:
              "لم تتم معاينة هذا الملف بعد من طرف فريق EMC، لذلك يمكن حذفه نهائيًا.",

            requestRequiredInfo:
              "تمت معاينة هذا الملف من طرف فريق EMC. حفاظًا على التتبع، سيتم إرسال طلب حذف إلى الفريق بدل الحذف المباشر.",

            pendingInfo:
              "لقد تم إرسال طلب حذف هذا الملف بالفعل إلى فريق EMC وهو في انتظار المعالجة.",

            confirmDelete1:
              "هل تريد فعلًا حذف هذا الملف نهائيًا؟ سيتم حذف الملف وخطة العمل والأدلة المرتبطة به.",

            confirmDelete2:
              "تأكيد نهائي: هذا الإجراء لا يمكن التراجع عنه. هل تريد المتابعة؟",

            confirmRequest:
              "هل تريد إرسال طلب حذف هذا الملف إلى فريق EMC؟",

            deletedSuccess:
              "تم حذف الملف نهائيًا.",

            requestSuccess:
              "تم إرسال طلب الحذف إلى فريق EMC.",

            deletionError:
              "تعذر تنفيذ عملية الحذف.",

            sessionExpired:
              "انتهت الجلسة. يرجى تسجيل الدخول من جديد.",

            deletionLoading:
              "جارٍ التحقق من إمكانية الحذف...",

            deleting:
              "جارٍ التنفيذ...",

            error:
              "تعذر تحميل الملفات. تأكد من أن الخادم يعمل وأنك متصل بالحساب.",
          }
        : {
            title: "Mon dossier",
            subtitle:
              "Consultez uniquement les dossiers rattachés à votre compte.",
            loading: "Chargement du dossier...",
            emptyTitle: "Aucun dossier pour le moment",
            emptyText:
              "Aucun dossier n'a encore été enregistré pour ce compte.",
            retry: "Réessayer",
            detectedIntent: "Type d'incident",
            status: "Statut",
            language: "Langue",
            emergency: "Situation d'urgence",
            description: "Description",
            createdAt: "Créé le",
            updatedAt: "Dernière mise à jour",
            yes: "Oui",
            no: "Non",
            active: "Actif",
            closed: "Clôturé",
            french: "Français",
            arabic: "Arabe",
            dossierList: "Mes dossiers",
            details: "Détails du dossier",

            managementTitle:
              "Gestion du dossier",

            managementText:
              "Gérez la suppression de ce dossier selon son état de prise en charge par l’équipe EMC.",

            deleteNow:
              "Supprimer définitivement",

            requestDeletion:
              "Demander la suppression",

            deletionPending:
              "Demande de suppression en attente",

            deleteImmediateInfo:
              "Ce dossier n’a pas encore été consulté par l’équipe EMC. Il peut donc être supprimé définitivement.",

            requestRequiredInfo:
              "Ce dossier a déjà été consulté par l’équipe EMC. Pour préserver la traçabilité, une demande de suppression sera transmise à l’équipe au lieu d’un effacement immédiat.",

            pendingInfo:
              "Une demande de suppression a déjà été transmise à l’équipe EMC et attend son traitement.",

            confirmDelete1:
              "Voulez-vous vraiment supprimer définitivement ce dossier ? Le dossier, son plan d’action et ses preuves associées seront supprimés.",

            confirmDelete2:
              "Confirmation finale : cette action est irréversible. Voulez-vous continuer ?",

            confirmRequest:
              "Voulez-vous transmettre une demande de suppression de ce dossier à l’équipe EMC ?",

            deletedSuccess:
              "Le dossier a été supprimé définitivement.",

            requestSuccess:
              "La demande de suppression a été transmise à l’équipe EMC.",

            deletionError:
              "Impossible d’effectuer l’opération de suppression.",

            sessionExpired:
              "Votre session a expiré. Veuillez vous reconnecter.",

            deletionLoading:
              "Vérification de la suppression...",

            deleting:
              "Traitement en cours...",

            error:
              "Impossible de charger vos dossiers. Vérifiez que le backend fonctionne et que vous êtes connecté.",
          },
    [isArabic]
  );

  const loadCases = async () => {
    setStatus("loading");
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/cases`, {
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);

        throw new Error(
          typeof data?.detail === "string"
            ? data.detail
            : copy.error
        );
      }

      const data = await response.json();

      setCases(Array.isArray(data) ? data : []);

      setSelectedCaseId((current) => {
        const safeData =
          Array.isArray(data)
            ? data
            : [];

        const storedCaseId =
          window.localStorage.getItem(
            SELECTED_CASE_STORAGE_KEY
          );

        const preferredId =
          current
          || storedCaseId;

        if (
          preferredId
          && safeData.some(
            (item) =>
              item.id
              === preferredId
          )
        ) {
          window.localStorage.setItem(
            SELECTED_CASE_STORAGE_KEY,
            preferredId
          );

          return preferredId;
        }

        const activeCase =
          safeData.find(
            (item) =>
              item.status
              === "active"
          );

        const nextId =
          activeCase?.id
          || safeData[0]?.id
          || null;

        if (nextId) {
          window.localStorage.setItem(
            SELECTED_CASE_STORAGE_KEY,
            nextId
          );
        } else {
          window.localStorage.removeItem(
            SELECTED_CASE_STORAGE_KEY
          );
        }

        return nextId;
      });

      setStatus("success");
    } catch (err) {
      setCases([]);
      setSelectedCaseId(null);
      setError(err.message || copy.error);
      setStatus("error");
    }
  };

  useEffect(() => {
    loadCases();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  useEffect(() => {
    if (!selectedCaseId) {
      setDeletionStatus(null);
      setDeletionMessage("");
      return;
    }

    let cancelled = false;

    const loadDeletionStatus =
      async () => {
        setDeletionLoading(true);
        setDeletionMessage("");

        try {
          const response =
            await fetch(
              `${API_BASE_URL}/cases/${selectedCaseId}/deletion-status`,
              {
                method: "GET",
                credentials: "include",
                headers: {
                  Accept:
                    "application/json",
                },
              }
            );

          const data =
            await response
              .json()
              .catch(
                () => null
              );

          if (!response.ok) {
            throw new Error(
              typeof data?.detail
                === "string"
                ? data.detail
                : copy.deletionError
            );
          }

          if (!cancelled) {
            setDeletionStatus(data);
          }
        } catch (err) {
          if (!cancelled) {
            setDeletionStatus(null);
            setDeletionMessageType(
              "error"
            );
            setDeletionMessage(
              err.message
              || copy.deletionError
            );
          }
        } finally {
          if (!cancelled) {
            setDeletionLoading(false);
          }
        }
      };

    loadDeletionStatus();

    return () => {
      cancelled = true;
    };
  }, [
    selectedCaseId,
    copy.deletionError,
  ]);


  const selectedCase =
    cases.find((item) => item.id === selectedCaseId) ||
    cases[0] ||
    null;

  const selectCase = (
    caseId
  ) => {
    setSelectedCaseId(
      caseId
    );

    window.localStorage.setItem(
      SELECTED_CASE_STORAGE_KEY,
      caseId
    );

    setDeletionMessage("");
    setDeletionMessageType("");
  };


  const handleDeletion =
    async () => {
      if (
        !selectedCase
        || !deletionStatus
        || deletionSubmitting
      ) {
        return;
      }

      if (
        deletionStatus.mode
        === "request_pending"
      ) {
        return;
      }

      if (
        deletionStatus.mode
        === "delete_immediately"
      ) {
        const firstConfirmation =
          window.confirm(
            copy.confirmDelete1
          );

        if (!firstConfirmation) {
          return;
        }

        const finalConfirmation =
          window.confirm(
            copy.confirmDelete2
          );

        if (!finalConfirmation) {
          return;
        }
      } else {
        const confirmed =
          window.confirm(
            copy.confirmRequest
          );

        if (!confirmed) {
          return;
        }
      }

      const csrfToken =
        readCookie(
          "csrf_token"
        );

      if (!csrfToken) {
        setDeletionMessageType(
          "error"
        );
        setDeletionMessage(
          copy.sessionExpired
        );
        return;
      }

      setDeletionSubmitting(true);
      setDeletionMessage("");
      setDeletionMessageType("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/cases/${selectedCase.id}/deletion`,
            {
              method: "POST",
              credentials: "include",
              headers: {
                Accept:
                  "application/json",
                "X-CSRF-Token":
                  csrfToken,
              },
            }
          );

        const data =
          await response
            .json()
            .catch(
              () => null
            );

        if (!response.ok) {
          throw new Error(
            typeof data?.detail
              === "string"
              ? data.detail
              : copy.deletionError
          );
        }

        if (
          data?.outcome
          === "deleted"
        ) {
          const remainingCases =
            cases.filter(
              (item) =>
                item.id
                !== selectedCase.id
            );

          setCases(
            remainingCases
          );

          const nextCase =
            remainingCases.find(
              (item) =>
                item.status
                === "active"
            )
            || remainingCases[0]
            || null;

          if (nextCase) {
            setSelectedCaseId(
              nextCase.id
            );

            window.localStorage.setItem(
              SELECTED_CASE_STORAGE_KEY,
              nextCase.id
            );
          } else {
            setSelectedCaseId(
              null
            );

            window.localStorage.removeItem(
              SELECTED_CASE_STORAGE_KEY
            );
          }

          setDeletionStatus(null);
          setDeletionMessageType(
            "success"
          );
          setDeletionMessage(
            data.message
            || copy.deletedSuccess
          );

          return;
        }

        setDeletionStatus(
          (current) => ({
            ...(current || {}),
            case_id:
              selectedCase.id,
            viewed_by_admin:
              true,
            deletion_requested:
              true,
            mode:
              "request_pending",
          })
        );

        setDeletionMessageType(
          "success"
        );

        setDeletionMessage(
          data?.message
          || copy.requestSuccess
        );
      } catch (err) {
        setDeletionMessageType(
          "error"
        );

        setDeletionMessage(
          err.message
          || copy.deletionError
        );
      } finally {
        setDeletionSubmitting(
          false
        );
      }
    };


  const translateStatus = (value) => {
    if (value === "active") {
      return copy.active;
    }

    if (value === "closed") {
      return copy.closed;
    }

    return value || "—";
  };

  const translateLanguage = (value) => {
    if (value === "fr") {
      return copy.french;
    }

    if (value === "ar") {
      return copy.arabic;
    }

    return value || "—";
  };

  if (status === "loading") {
    return (
      <section
        className="case-page"
        dir={isArabic ? "rtl" : "ltr"}
      >
        <div className="case-page-heading">
          <div>
            <h1>{copy.title}</h1>
            <p>{copy.subtitle}</p>
          </div>
        </div>

        <div className="case-state-card">
          <div className="case-loader" aria-hidden="true" />
          <p>{copy.loading}</p>
        </div>
      </section>
    );
  }

  if (status === "error") {
    return (
      <section
        className="case-page"
        dir={isArabic ? "rtl" : "ltr"}
      >
        <div className="case-page-heading">
          <div>
            <h1>{copy.title}</h1>
            <p>{copy.subtitle}</p>
          </div>
        </div>

        <div className="case-state-card case-state-error">
          <strong>{copy.error}</strong>
          <p>{error}</p>

          <button
            type="button"
            className="case-primary-button"
            onClick={loadCases}
          >
            {copy.retry}
          </button>
        </div>
      </section>
    );
  }

  if (cases.length === 0) {
    return (
      <section
        className="case-page"
        dir={isArabic ? "rtl" : "ltr"}
      >
        <div className="case-page-heading">
          <div>
            <h1>{copy.title}</h1>
            <p>{copy.subtitle}</p>
          </div>
        </div>

        <div className="case-state-card">
          <div className="case-empty-icon" aria-hidden="true">
            ◻
          </div>
          <h2>{copy.emptyTitle}</h2>
          <p>{copy.emptyText}</p>
        </div>
      </section>
    );
  }

  return (
    <section
      className="case-page"
      dir={isArabic ? "rtl" : "ltr"}
    >
      <div className="case-page-heading">
        <div>
          <h1>{copy.title}</h1>
          <p>{copy.subtitle}</p>
        </div>

        <div className="case-count-badge">
          {cases.length}
        </div>
      </div>

      <div
        className={`case-layout ${
          cases.length === 1 ? "case-layout-single" : ""
        }`}
      >
        {cases.length > 1 && (
          <aside className="case-list-card">
            <h2>{copy.dossierList}</h2>

            <div className="case-list">
              {cases.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() =>
                    selectCase(
                      item.id
                    )
                  }
                  className={`case-list-item ${
                    item.id === selectedCase?.id
                      ? "case-list-item-active"
                      : ""
                  }`}
                >
                  <span className="case-list-item-title">
                    {item.detected_intent || "—"}
                  </span>

                  <span className="case-list-item-meta">
                    {translateStatus(item.status)}
                    {" · "}
                    {formatDate(item.created_at, language)}
                  </span>
                </button>
              ))}
            </div>
          </aside>
        )}

        {selectedCase && (
          <article className="case-detail-card">
            <div className="case-detail-header">
              <div>
                <span className="case-detail-eyebrow">
                  {copy.details}
                </span>
                <h2>
                  {selectedCase.detected_intent || "—"}
                </h2>
              </div>

              <span
                className={`case-status-badge ${
                  selectedCase.status === "closed"
                    ? "case-status-closed"
                    : "case-status-active"
                }`}
              >
                {translateStatus(selectedCase.status)}
              </span>
            </div>

            <div className="case-summary-grid">
              <div className="case-summary-item">
                <span>{copy.detectedIntent}</span>
                <strong>
                  {selectedCase.detected_intent || "—"}
                </strong>
              </div>

              <div className="case-summary-item">
                <span>{copy.language}</span>
                <strong>
                  {translateLanguage(selectedCase.language)}
                </strong>
              </div>

              <div className="case-summary-item">
                <span>{copy.emergency}</span>
                <strong>
                  {selectedCase.emergency ? copy.yes : copy.no}
                </strong>
              </div>
            </div>

            <div className="case-description-block">
              <span>{copy.description}</span>
              <p>{selectedCase.description}</p>
            </div>

            <div className="case-dates">
              <div>
                <span>{copy.createdAt}</span>
                <strong>
                  {formatDate(
                    selectedCase.created_at,
                    language
                  )}
                </strong>
              </div>

              <div>
                <span>{copy.updatedAt}</span>
                <strong>
                  {formatDate(
                    selectedCase.updated_at,
                    language
                  )}
                </strong>
              </div>
            </div>


            <section className="case-deletion-zone">
              <div className="case-deletion-copy">
                <span className="case-deletion-icon">
                  !
                </span>

                <div>
                  <h3>
                    {copy.managementTitle}
                  </h3>

                  <p>
                    {deletionLoading
                      ? copy.deletionLoading
                      : deletionStatus?.mode
                          === "delete_immediately"
                        ? copy.deleteImmediateInfo
                        : deletionStatus?.mode
                            === "request_required"
                          ? copy.requestRequiredInfo
                          : deletionStatus?.mode
                              === "request_pending"
                            ? copy.pendingInfo
                            : copy.managementText}
                  </p>
                </div>
              </div>

              <button
                type="button"
                className={
                  deletionStatus?.mode
                    === "request_pending"
                    ? "case-deletion-button is-pending"
                    : deletionStatus?.mode
                        === "request_required"
                      ? "case-deletion-button is-request"
                      : "case-deletion-button is-danger"
                }
                disabled={
                  deletionLoading
                  || deletionSubmitting
                  || !deletionStatus
                  || deletionStatus?.mode
                    === "request_pending"
                }
                onClick={
                  handleDeletion
                }
              >
                {deletionSubmitting
                  ? copy.deleting
                  : deletionStatus?.mode
                      === "request_pending"
                    ? copy.deletionPending
                    : deletionStatus?.mode
                        === "request_required"
                      ? copy.requestDeletion
                      : copy.deleteNow}
              </button>

              {deletionMessage && (
                <div
                  className={
                    `case-deletion-message ${
                      deletionMessageType
                      === "success"
                        ? "success"
                        : "error"
                    }`
                  }
                  role={
                    deletionMessageType
                    === "error"
                      ? "alert"
                      : undefined
                  }
                >
                  {deletionMessage}
                </div>
              )}
            </section>
          </article>
        )}
      </div>
    </section>
  );
}

export default CaseFile;