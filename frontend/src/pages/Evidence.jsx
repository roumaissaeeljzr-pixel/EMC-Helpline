import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useLanguage,
} from "../context/LanguageContext.jsx";

import "./Evidence.css";


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


const SELECTED_CASE_STORAGE_KEY =
  "emc_selected_case_id";


function getCsrfToken() {

  const cookie = document.cookie
    .split("; ")
    .find(
      (row) =>
        row.startsWith(
          "csrf_token="
        )
    );

  if (!cookie) {
    return "";
  }

  return decodeURIComponent(
    cookie.split("=")[1]
  );
}


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


function Evidence() {

  const {
    language,
  } = useLanguage();


  const isArabic =
    language === "ar";


  const t = useMemo(
    () => {

      if (isArabic) {

        return {
          title: "أدلتي",
          subtitle:
            "احتفظ بالأدلة المرتبطة بحالتك في مكان آمن.",

          dossier:
            "الملف",

          noCase:
            "لا يوجد لديك أي ملف حتى الآن. قم أولاً بتقييم حالتك لإنشاء ملف.",

          chooseCase:
            "اختر ملفًا",

          evidenceCount:
            "الأدلة المحفوظة",

          addEvidence:
            "إضافة دليل",

          screenshot:
            "لقطة شاشة",

          file:
            "ملف",

          link:
            "رابط",

          note:
            "ملاحظة",

          titleLabel:
            "عنوان الدليل",

          titlePlaceholder:
            "مثال: لقطة شاشة للمحادثة",

          urlLabel:
            "الرابط",

          urlPlaceholder:
            "https://...",

          noteLabel:
            "الملاحظة",

          notePlaceholder:
            "اكتب المعلومات التي تريد الاحتفاظ بها...",

          fileLabel:
            "اختر ملفًا",

          selectedFile:
            "الملف المختار",

          add:
            "إضافة",

          adding:
            "جارٍ الإضافة...",

          cancel:
            "إلغاء",

          empty:
            "لا توجد أدلة محفوظة لهذا الملف.",

          download:
            "تنزيل",

          open:
            "فتح",

          delete:
            "حذف",

          deleting:
            "جارٍ الحذف...",

          confirmDelete:
            "هل تريد حذف هذا الدليل نهائيًا؟",

          loadError:
            "تعذر تحميل الأدلة.",

          createError:
            "تعذر إضافة الدليل.",

          deleteError:
            "تعذر حذف الدليل.",

          downloadError:
            "تعذر تنزيل الملف.",

          success:
            "تمت إضافة الدليل بنجاح.",

          typeScreenshot:
            "لقطة شاشة",

          typeFile:
            "ملف",

          typeLink:
            "رابط",

          typeNote:
            "ملاحظة",

          size:
            "الحجم",

          created:
            "أضيف في",

          loading:
            "جارٍ التحميل...",

          csrfError:
            "انتهت الجلسة أو رمز الحماية غير متوفر. أعد تسجيل الدخول.",

          noFile:
            "اختر ملفًا أولاً.",

          required:
            "يرجى ملء الحقول المطلوبة.",
        };
      }


      return {
        title: "Mes preuves",

        subtitle:
          "Conservez en sécurité les éléments utiles liés à votre situation.",

        dossier:
          "Dossier",

        noCase:
          "Vous n'avez encore aucun dossier. Effectuez d'abord une évaluation de votre situation pour créer un dossier.",

        chooseCase:
          "Choisir un dossier",

        evidenceCount:
          "preuves enregistrées",

        addEvidence:
          "Ajouter une preuve",

        screenshot:
          "Capture d'écran",

        file:
          "Fichier",

        link:
          "Lien",

        note:
          "Note",

        titleLabel:
          "Titre de la preuve",

        titlePlaceholder:
          "Ex. Capture de la conversation",

        urlLabel:
          "Lien",

        urlPlaceholder:
          "https://...",

        noteLabel:
          "Note",

        notePlaceholder:
          "Écrivez les informations que vous souhaitez conserver...",

        fileLabel:
          "Choisir un fichier",

        selectedFile:
          "Fichier sélectionné",

        add:
          "Ajouter",

        adding:
          "Ajout en cours...",

        cancel:
          "Annuler",

        empty:
          "Aucune preuve enregistrée pour ce dossier.",

        download:
          "Télécharger",

        open:
          "Ouvrir",

        delete:
          "Supprimer",

        deleting:
          "Suppression...",

        confirmDelete:
          "Voulez-vous supprimer définitivement cette preuve ?",

        loadError:
          "Impossible de charger les preuves.",

        createError:
          "Impossible d'ajouter la preuve.",

        deleteError:
          "Impossible de supprimer la preuve.",

        downloadError:
          "Impossible de télécharger le fichier.",

        success:
          "Preuve ajoutée avec succès.",

        typeScreenshot:
          "Capture d'écran",

        typeFile:
          "Fichier",

        typeLink:
          "Lien",

        typeNote:
          "Note",

        size:
          "Taille",

        created:
          "Ajoutée le",

        loading:
          "Chargement...",

        csrfError:
          "Votre session a expiré ou le jeton de sécurité est indisponible. Reconnectez-vous.",

        noFile:
          "Choisissez d'abord un fichier.",

        required:
          "Veuillez remplir les champs obligatoires.",
      };

    },
    [
      isArabic,
    ]
  );


  const [
    cases,
    setCases,
  ] = useState([]);


  const [
    selectedCaseId,
    setSelectedCaseId,
  ] = useState(
    () =>
      window.localStorage.getItem(
        SELECTED_CASE_STORAGE_KEY
      )
      || ""
  );


  const [
    evidences,
    setEvidences,
  ] = useState([]);


  const [
    loadingCases,
    setLoadingCases,
  ] = useState(true);


  const [
    loadingEvidence,
    setLoadingEvidence,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");


  const [
    successMessage,
    setSuccessMessage,
  ] = useState("");


  const [
    activeForm,
    setActiveForm,
  ] = useState(null);


  const [
    title,
    setTitle,
  ] = useState("");


  const [
    note,
    setNote,
  ] = useState("");


  const [
    url,
    setUrl,
  ] = useState("");


  const [
    selectedFile,
    setSelectedFile,
  ] = useState(null);


  const [
    submitting,
    setSubmitting,
  ] = useState(false);


  const [
    deletingId,
    setDeletingId,
  ] = useState(null);


  // ============================================================
  // LOAD CASES
  // ============================================================

  useEffect(
    () => {

      const loadCases =
        async () => {

          setLoadingCases(true);
          setError("");

          try {

            const response =
              await fetch(
                `${API_BASE_URL}/cases`,
                {
                  method: "GET",
                  credentials:
                    "include",

                  headers: {
                    Accept:
                      "application/json",
                  },
                }
              );


            if (!response.ok) {

              throw new Error(
                t.loadError
              );
            }


            const data =
              await response.json();


            const safeCases =
              Array.isArray(data)
                ? data
                : [];


            const activeCases =
              safeCases.filter(
                (item) =>
                  item.status
                  === "active"
              );


            const selectableCases =
              activeCases.length > 0
                ? activeCases
                : safeCases;


            setCases(
              selectableCases
            );


            if (
              selectableCases.length > 0
            ) {

              const storedCaseId =
                window.localStorage.getItem(
                  SELECTED_CASE_STORAGE_KEY
                );


              const selectedCase =
                selectableCases.find(
                  (item) =>
                    item.id
                    === storedCaseId
                )
                || selectableCases[0];


              setSelectedCaseId(
                selectedCase.id
              );


              window.localStorage.setItem(
                SELECTED_CASE_STORAGE_KEY,
                selectedCase.id
              );

            } else {

              setSelectedCaseId(
                ""
              );


              window.localStorage.removeItem(
                SELECTED_CASE_STORAGE_KEY
              );
            }


          } catch (err) {

            setError(
              err.message
            );

          } finally {

            setLoadingCases(
              false
            );
          }
        };


      loadCases();

    },
    [
      t.loadError,
    ]
  );


  // ============================================================
  // LOAD EVIDENCE
  // ============================================================

  useEffect(
    () => {

      if (!selectedCaseId) {

        setEvidences([]);

        return;
      }


      const loadEvidence =
        async () => {

          setLoadingEvidence(
            true
          );

          setError("");


          try {

            const response =
              await fetch(
                `${API_BASE_URL}/cases/${selectedCaseId}/evidence`,
                {
                  method:
                    "GET",

                  credentials:
                    "include",

                  headers: {
                    Accept:
                      "application/json",
                  },
                }
              );


            if (!response.ok) {

              throw new Error(
                t.loadError
              );
            }


            const data =
              await response.json();


            setEvidences(
              Array.isArray(data)
                ? data
                : []
            );


          } catch (err) {

            setError(
              err.message
            );

          } finally {

            setLoadingEvidence(
              false
            );
          }
        };


      loadEvidence();

    },
    [
      selectedCaseId,
      t.loadError,
    ]
  );


  // ============================================================
  // HELPERS
  // ============================================================

  const selectedCase =
    cases.find(
      (item) =>
        item.id
        === selectedCaseId
    );


  const resetForm = () => {

    setTitle("");
    setNote("");
    setUrl("");
    setSelectedFile(null);
    setActiveForm(null);
  };


  const refreshEvidence =
    async () => {

      if (!selectedCaseId) {
        return;
      }


      const response =
        await fetch(
          `${API_BASE_URL}/cases/${selectedCaseId}/evidence`,
          {
            credentials:
              "include",

            headers: {
              Accept:
                "application/json",
            },
          }
        );


      if (response.ok) {

        const data =
          await response.json();

        setEvidences(
          Array.isArray(data)
            ? data
            : []
        );
      }
    };


  // ============================================================
  // CREATE NOTE
  // ============================================================

  const createNote =
    async () => {

      if (
        !title.trim()
        || !note.trim()
      ) {

        setError(
          t.required
        );

        return;
      }


      const csrf =
        getCsrfToken();


      if (!csrf) {

        setError(
          t.csrfError
        );

        return;
      }


      setSubmitting(true);
      setError("");
      setSuccessMessage("");


      try {

        const response =
          await fetch(
            `${API_BASE_URL}/cases/${selectedCaseId}/evidence/note`,
            {
              method:
                "POST",

              credentials:
                "include",

              headers: {
                "Content-Type":
                  "application/json",

                Accept:
                  "application/json",

                "X-CSRF-Token":
                  csrf,
              },

              body:
                JSON.stringify(
                  {
                    title:
                      title.trim(),

                    note:
                      note.trim(),
                  }
                ),
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
            data?.detail
            || t.createError
          );
        }


        await refreshEvidence();

        resetForm();

        setSuccessMessage(
          t.success
        );


      } catch (err) {

        setError(
          err.message
        );

      } finally {

        setSubmitting(
          false
        );
      }
    };


  // ============================================================
  // CREATE LINK
  // ============================================================

  const createLink =
    async () => {

      if (
        !title.trim()
        || !url.trim()
      ) {

        setError(
          t.required
        );

        return;
      }


      const csrf =
        getCsrfToken();


      if (!csrf) {

        setError(
          t.csrfError
        );

        return;
      }


      setSubmitting(true);
      setError("");
      setSuccessMessage("");


      try {

        const response =
          await fetch(
            `${API_BASE_URL}/cases/${selectedCaseId}/evidence/link`,
            {
              method:
                "POST",

              credentials:
                "include",

              headers: {
                "Content-Type":
                  "application/json",

                Accept:
                  "application/json",

                "X-CSRF-Token":
                  csrf,
              },

              body:
                JSON.stringify(
                  {
                    title:
                      title.trim(),

                    url:
                      url.trim(),
                  }
                ),
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
            data?.detail
            || t.createError
          );
        }


        await refreshEvidence();

        resetForm();

        setSuccessMessage(
          t.success
        );


      } catch (err) {

        setError(
          err.message
        );

      } finally {

        setSubmitting(
          false
        );
      }
    };


  // ============================================================
  // CREATE FILE / SCREENSHOT
  // ============================================================

  const createFile =
    async (
      evidenceType
    ) => {

      if (
        !title.trim()
      ) {

        setError(
          t.required
        );

        return;
      }


      if (!selectedFile) {

        setError(
          t.noFile
        );

        return;
      }


      const csrf =
        getCsrfToken();


      if (!csrf) {

        setError(
          t.csrfError
        );

        return;
      }


      const formData =
        new FormData();


      formData.append(
        "title",
        title.trim()
      );


      formData.append(
        "evidence_type",
        evidenceType
      );


      formData.append(
        "file",
        selectedFile
      );


      setSubmitting(true);
      setError("");
      setSuccessMessage("");


      try {

        const response =
          await fetch(
            `${API_BASE_URL}/cases/${selectedCaseId}/evidence/file`,
            {
              method:
                "POST",

              credentials:
                "include",

              headers: {
                "X-CSRF-Token":
                  csrf,
              },

              body:
                formData,
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
            data?.detail
            || t.createError
          );
        }


        await refreshEvidence();

        resetForm();

        setSuccessMessage(
          t.success
        );


      } catch (err) {

        setError(
          err.message
        );

      } finally {

        setSubmitting(
          false
        );
      }
    };


  // ============================================================
  // DELETE
  // ============================================================

  const deleteEvidence =
    async (
      evidenceId
    ) => {

      const confirmed =
        window.confirm(
          t.confirmDelete
        );


      if (!confirmed) {
        return;
      }


      const csrf =
        getCsrfToken();


      if (!csrf) {

        setError(
          t.csrfError
        );

        return;
      }


      setDeletingId(
        evidenceId
      );

      setError("");
      setSuccessMessage("");


      try {

        const response =
          await fetch(
            `${API_BASE_URL}/evidence/${evidenceId}`,
            {
              method:
                "DELETE",

              credentials:
                "include",

              headers: {
                "X-CSRF-Token":
                  csrf,
              },
            }
          );


        if (!response.ok) {

          const data =
            await response
              .json()
              .catch(
                () => null
              );


          throw new Error(
            data?.detail
            || t.deleteError
          );
        }


        setEvidences(
          (current) =>
            current.filter(
              (item) =>
                item.id
                !== evidenceId
            )
        );


      } catch (err) {

        setError(
          err.message
        );

      } finally {

        setDeletingId(
          null
        );
      }
    };


  // ============================================================
  // DOWNLOAD
  // ============================================================

  const downloadEvidence =
    async (
      evidence
    ) => {

      setError("");


      try {

        const response =
          await fetch(
            `${API_BASE_URL}/evidence/${evidence.id}/download`,
            {
              method:
                "GET",

              credentials:
                "include",
            }
          );


        if (!response.ok) {

          const data =
            await response
              .json()
              .catch(
                () => null
              );


          throw new Error(
            data?.detail
            || t.downloadError
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
          evidence.original_filename
          || "preuve";


        document.body.appendChild(
          anchor
        );


        anchor.click();


        anchor.remove();


        URL.revokeObjectURL(
          objectUrl
        );


      } catch (err) {

        setError(
          err.message
        );
      }
    };


  // ============================================================
  // FORMAT
  // ============================================================

  const getTypeLabel =
    (type) => {

      switch (type) {

        case "screenshot":
          return t.typeScreenshot;

        case "file":
          return t.typeFile;

        case "link":
          return t.typeLink;

        case "note":
          return t.typeNote;

        default:
          return type;
      }
    };


  const getTypeIcon =
    (type) => {

      switch (type) {

        case "screenshot":
          return "▣";

        case "file":
          return "↥";

        case "link":
          return "↗";

        case "note":
          return "≡";

        default:
          return "•";
      }
    };


  const formatBytes =
    (bytes) => {

      if (
        bytes === null
        || bytes === undefined
      ) {
        return "";
      }


      if (
        bytes < 1024
      ) {

        return `${bytes} B`;
      }


      if (
        bytes
        < 1024 * 1024
      ) {

        return (
          `${(
            bytes / 1024
          ).toFixed(1)} KB`
        );
      }


      return (
        `${(
          bytes
          / 1024
          / 1024
        ).toFixed(1)} MB`
      );
    };


  const formatDate =
    (value) => {

      if (!value) {
        return "";
      }


      return new Intl.DateTimeFormat(
        isArabic
          ? "ar-MA"
          : "fr-FR",
        {
          dateStyle:
            "medium",

          timeStyle:
            "short",
        }
      ).format(
        new Date(value)
      );
    };


  // ============================================================
  // RENDER
  // ============================================================

  return (

    <div
      className="evidence-page"
      dir={
        isArabic
          ? "rtl"
          : "ltr"
      }
    >

      <div
        className="evidence-header"
      >

        <div>

          <h1>
            {t.title}
          </h1>

          <p>
            {t.subtitle}
          </p>

        </div>

      </div>


      {error && (

        <div
          className=
            "evidence-message evidence-message-error"
        >
          {error}
        </div>

      )}


      {successMessage && (

        <div
          className=
            "evidence-message evidence-message-success"
        >
          {successMessage}
        </div>

      )}


      {loadingCases
        ? (

            <div
              className="evidence-empty"
            >
              {t.loading}
            </div>

          )

        : cases.length === 0
          ? (

              <div
                className="evidence-empty"
              >
                {t.noCase}
              </div>

            )

          : (

              <>

                <section
                  className="evidence-case-card"
                >

                  <label
                    htmlFor=
                      "evidence-case-select"
                  >
                    {t.dossier}
                  </label>


                  <select
                    id=
                      "evidence-case-select"

                    value={
                      selectedCaseId
                    }

                    onChange={
                      (event) => {

                        const nextCaseId =
                          event.target.value;


                        setSelectedCaseId(
                          nextCaseId
                        );


                        window.localStorage.setItem(
                          SELECTED_CASE_STORAGE_KEY,
                          nextCaseId
                        );


                        resetForm();

                        setError("");

                        setSuccessMessage("");
                      }
                    }
                  >

                    {cases.map(
                      (item) => (

                        <option
                          key={
                            item.id
                          }

                          value={
                            item.id
                          }
                        >

                          {item.detected_intent
                            || t.chooseCase}
                          {" — "}
                          {formatCaseReference(
                            item.id
                          )}

                        </option>

                      )
                    )}

                  </select>


                  {selectedCase && (

                    <div
                      className=
                        "evidence-case-summary"
                    >

                      <span
                        className=
                          "evidence-status"
                      >
                        {selectedCase.status}
                      </span>

                      <p>
                        {
                          selectedCase.description
                        }
                      </p>

                    </div>

                  )}

                </section>


                <section
                  className=
                    "evidence-add-section"
                >

                  <div
                    className=
                      "evidence-section-heading"
                  >

                    <div>

                      <h2>
                        {t.addEvidence}
                      </h2>

                    </div>

                  </div>


                  <div
                    className=
                      "evidence-type-grid"
                  >

                    <button
                      type="button"

                      className={
                        activeForm
                        === "screenshot"
                          ? "evidence-type-card active"
                          : "evidence-type-card"
                      }

                      onClick={() => {

                        resetForm();

                        setActiveForm(
                          "screenshot"
                        );

                        setError("");
                      }}
                    >

                      <span
                        className=
                          "evidence-type-icon"
                      >
                        ▣
                      </span>

                      <strong>
                        {t.screenshot}
                      </strong>

                    </button>


                    <button
                      type="button"

                      className={
                        activeForm
                        === "file"
                          ? "evidence-type-card active"
                          : "evidence-type-card"
                      }

                      onClick={() => {

                        resetForm();

                        setActiveForm(
                          "file"
                        );

                        setError("");
                      }}
                    >

                      <span
                        className=
                          "evidence-type-icon"
                      >
                        ↥
                      </span>

                      <strong>
                        {t.file}
                      </strong>

                    </button>


                    <button
                      type="button"

                      className={
                        activeForm
                        === "link"
                          ? "evidence-type-card active"
                          : "evidence-type-card"
                      }

                      onClick={() => {

                        resetForm();

                        setActiveForm(
                          "link"
                        );

                        setError("");
                      }}
                    >

                      <span
                        className=
                          "evidence-type-icon"
                      >
                        ↗
                      </span>

                      <strong>
                        {t.link}
                      </strong>

                    </button>


                    <button
                      type="button"

                      className={
                        activeForm
                        === "note"
                          ? "evidence-type-card active"
                          : "evidence-type-card"
                      }

                      onClick={() => {

                        resetForm();

                        setActiveForm(
                          "note"
                        );

                        setError("");
                      }}
                    >

                      <span
                        className=
                          "evidence-type-icon"
                      >
                        ≡
                      </span>

                      <strong>
                        {t.note}
                      </strong>

                    </button>

                  </div>


                  {activeForm && (

                    <div
                      className=
                        "evidence-form-card"
                    >

                      <label>

                        <span>
                          {t.titleLabel}
                        </span>

                        <input
                          type="text"

                          value={
                            title
                          }

                          onChange={
                            (event) =>
                              setTitle(
                                event.target.value
                              )
                          }

                          placeholder={
                            t.titlePlaceholder
                          }

                          maxLength={255}
                        />

                      </label>


                      {activeForm
                        === "note"
                        && (

                          <label>

                            <span>
                              {t.noteLabel}
                            </span>

                            <textarea
                              value={
                                note
                              }

                              onChange={
                                (event) =>
                                  setNote(
                                    event.target.value
                                  )
                              }

                              placeholder={
                                t.notePlaceholder
                              }

                              rows={5}
                            />

                          </label>

                        )}


                      {activeForm
                        === "link"
                        && (

                          <label>

                            <span>
                              {t.urlLabel}
                            </span>

                            <input
                              type="url"

                              value={
                                url
                              }

                              onChange={
                                (event) =>
                                  setUrl(
                                    event.target.value
                                  )
                              }

                              placeholder={
                                t.urlPlaceholder
                              }
                            />

                          </label>

                        )}


                      {(
                        activeForm
                        === "file"
                        ||
                        activeForm
                        === "screenshot"
                      )
                        && (

                          <label>

                            <span>
                              {t.fileLabel}
                            </span>

                            <input
                              type="file"

                              accept={
                                activeForm
                                === "screenshot"
                                  ? "image/png,image/jpeg,image/webp,image/gif,image/heic,image/heif"
                                  : undefined
                              }

                              onChange={
                                (event) =>
                                  setSelectedFile(
                                    event.target
                                      .files?.[0]
                                    || null
                                  )
                              }
                            />


                            {selectedFile && (

                              <small>
                                {t.selectedFile}
                                {" : "}
                                {
                                  selectedFile.name
                                }
                              </small>

                            )}

                          </label>

                        )}


                      <div
                        className=
                          "evidence-form-actions"
                      >

                        <button
                          type="button"

                          className=
                            "evidence-secondary-button"

                          onClick={
                            resetForm
                          }

                          disabled={
                            submitting
                          }
                        >
                          {t.cancel}
                        </button>


                        <button
                          type="button"

                          className=
                            "evidence-primary-button"

                          disabled={
                            submitting
                          }

                          onClick={() => {

                            if (
                              activeForm
                              === "note"
                            ) {

                              createNote();

                            } else if (
                              activeForm
                              === "link"
                            ) {

                              createLink();

                            } else {

                              createFile(
                                activeForm
                              );
                            }
                          }}
                        >

                          {submitting
                            ? t.adding
                            : t.add
                          }

                        </button>

                      </div>

                    </div>

                  )}

                </section>


                <section
                  className=
                    "evidence-list-section"
                >

                  <div
                    className=
                      "evidence-section-heading"
                  >

                    <div>

                      <h2>
                        {t.evidenceCount}
                      </h2>

                      <span
                        className=
                          "evidence-count"
                      >
                        {evidences.length}
                      </span>

                    </div>

                  </div>


                  {loadingEvidence
                    ? (

                        <div
                          className=
                            "evidence-empty"
                        >
                          {t.loading}
                        </div>

                      )

                    : evidences.length
                      === 0
                      ? (

                          <div
                            className=
                              "evidence-empty"
                          >
                            {t.empty}
                          </div>

                        )

                      : (

                          <div
                            className=
                              "evidence-list"
                          >

                            {evidences.map(
                              (
                                evidence
                              ) => (

                                <article
                                  key={
                                    evidence.id
                                  }

                                  className=
                                    "evidence-item"
                                >

                                  <div
                                    className=
                                      "evidence-item-icon"
                                  >
                                    {
                                      getTypeIcon(
                                        evidence.type
                                      )
                                    }
                                  </div>


                                  <div
                                    className=
                                      "evidence-item-content"
                                  >

                                    <div
                                      className=
                                        "evidence-item-top"
                                    >

                                      <div>

                                        <span
                                          className=
                                            "evidence-badge"
                                        >
                                          {
                                            getTypeLabel(
                                              evidence.type
                                            )
                                          }
                                        </span>

                                        <h3>
                                          {
                                            evidence.title
                                          }
                                        </h3>

                                      </div>


                                      <button
                                        type="button"

                                        className=
                                          "evidence-delete-button"

                                        disabled={
                                          deletingId
                                          === evidence.id
                                        }

                                        onClick={() =>
                                          deleteEvidence(
                                            evidence.id
                                          )
                                        }
                                      >

                                        {deletingId
                                        === evidence.id
                                          ? t.deleting
                                          : t.delete
                                        }

                                      </button>

                                    </div>


                                    {evidence.type
                                      === "note"
                                      && (

                                        <p
                                          className=
                                            "evidence-note"
                                        >
                                          {
                                            evidence.note
                                          }
                                        </p>

                                      )}


                                    {evidence.type
                                      === "link"
                                      && (

                                        <p
                                          className=
                                            "evidence-link-text"
                                        >
                                          {
                                            evidence.url
                                          }
                                        </p>

                                      )}


                                    {(
                                      evidence.type
                                      === "file"
                                      ||
                                      evidence.type
                                      === "screenshot"
                                    )
                                      && (

                                        <div
                                          className=
                                            "evidence-file-info"
                                        >

                                          <span>
                                            {
                                              evidence.original_filename
                                            }
                                          </span>

                                          {evidence.file_size
                                          !== null
                                          && (

                                            <span>
                                              {t.size}
                                              {" : "}
                                              {
                                                formatBytes(
                                                  evidence.file_size
                                                )
                                              }
                                            </span>

                                          )}

                                        </div>

                                      )}


                                    <div
                                      className=
                                        "evidence-item-footer"
                                    >

                                      <span>

                                        {t.created}
                                        {" "}
                                        {
                                          formatDate(
                                            evidence.created_at
                                          )
                                        }

                                      </span>


                                      <div
                                        className=
                                          "evidence-item-actions"
                                      >

                                        {evidence.type
                                          === "link"
                                          && (

                                            <button
                                              type="button"

                                              className=
                                                "evidence-action-button"

                                              onClick={() =>
                                                window.open(
                                                  evidence.url,
                                                  "_blank",
                                                  "noopener,noreferrer"
                                                )
                                              }
                                            >
                                              {t.open}
                                            </button>

                                          )}


                                        {(
                                          evidence.type
                                          === "file"
                                          ||
                                          evidence.type
                                          === "screenshot"
                                        )
                                          && (

                                            <button
                                              type="button"

                                              className=
                                                "evidence-action-button"

                                              onClick={() =>
                                                downloadEvidence(
                                                  evidence
                                                )
                                              }
                                            >
                                              {t.download}
                                            </button>

                                          )}

                                      </div>

                                    </div>

                                  </div>

                                </article>

                              )
                            )}

                          </div>

                        )
                  }

                </section>

              </>

            )
      }

    </div>
  );
}


export default Evidence;