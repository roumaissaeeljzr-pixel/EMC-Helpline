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

import "./DocumentBase.css";


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


/* =========================================================
   COOKIE / CSRF
========================================================= */

function readCookie(name) {
  const prefix = `${name}=`;

  const raw = document.cookie
    .split("; ")
    .find(
      (entry) =>
        entry.startsWith(prefix)
    );

  return raw
    ? decodeURIComponent(
        raw.slice(prefix.length)
      )
    : null;
}


function getCsrfToken() {
  const token =
    readCookie("csrf_token");

  if (!token) {
    throw new Error(
      "Jeton CSRF introuvable. Veuillez vous reconnecter."
    );
  }

  return token;
}


/* =========================================================
   ICONS
========================================================= */

function AdminResourceIcon({
  name,
  size = 20,
}) {
  const props = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": "true",
  };


  if (name === "plus") {
    return (
      <svg {...props}>
        <path d="M12 5v14" />
        <path d="M5 12h14" />
      </svg>
    );
  }


  if (name === "search") {
    return (
      <svg {...props}>
        <circle
          cx="11"
          cy="11"
          r="7"
        />

        <path d="m20 20-4-4" />
      </svg>
    );
  }


  if (name === "edit") {
    return (
      <svg {...props}>
        <path d="M12 20h9" />
        <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4z" />
      </svg>
    );
  }


  if (name === "trash") {
    return (
      <svg {...props}>
        <path d="M3 6h18" />
        <path d="M8 6V4h8v2" />
        <path d="M19 6l-1 14H6L5 6" />
        <path d="M10 11v5" />
        <path d="M14 11v5" />
      </svg>
    );
  }


  if (name === "eye") {
    return (
      <svg {...props}>
        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12z" />

        <circle
          cx="12"
          cy="12"
          r="2.5"
        />
      </svg>
    );
  }


  if (name === "eye-off") {
    return (
      <svg {...props}>
        <path d="m3 3 18 18" />
        <path d="M10.6 10.6A2 2 0 0 0 13.4 13.4" />
        <path d="M9.9 4.2A11 11 0 0 1 12 4c6.5 0 10 8 10 8a17 17 0 0 1-2 3.1" />
        <path d="M6.6 6.6C3.7 8.5 2 12 2 12s3.5 8 10 8a10 10 0 0 0 4.1-.9" />
      </svg>
    );
  }


  if (name === "database") {
    return (
      <svg {...props}>
        <ellipse
          cx="12"
          cy="5"
          rx="8"
          ry="3"
        />

        <path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
        <path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
      </svg>
    );
  }


  if (name === "close") {
    return (
      <svg {...props}>
        <path d="M6 6l12 12" />
        <path d="M18 6 6 18" />
      </svg>
    );
  }


  if (name === "refresh") {
    return (
      <svg {...props}>
        <path d="M20 7v5h-5" />
        <path d="M4 17v-5h5" />
        <path d="M6.1 8a7 7 0 0 1 11.8-2L20 8" />
        <path d="M17.9 16a7 7 0 0 1-11.8 2L4 16" />
      </svg>
    );
  }


  if (name === "check") {
    return (
      <svg {...props}>
        <path d="m5 12 4 4L19 6" />
      </svg>
    );
  }


  if (name === "warning") {
    return (
      <svg {...props}>
        <path d="M12 3 3 20h18z" />
        <path d="M12 9v4" />
        <path d="M12 17h.01" />
      </svg>
    );
  }


  return (
    <svg {...props}>
      <circle
        cx="12"
        cy="12"
        r="9"
      />

      <path d="M12 8v8" />
      <path d="M8 12h8" />
    </svg>
  );
}


/* =========================================================
   CATEGORIES
========================================================= */

const CATEGORY_CONFIG = {
  account: {
    icon: "account",
    tone: "purple",
  },

  evidence: {
    icon: "clip",
    tone: "blue",
  },

  harassment: {
    icon: "chat",
    tone: "pink",
  },

  privacy: {
    icon: "privacy",
    tone: "green",
  },

  identity: {
    icon: "identity",
    tone: "purple",
  },

  images: {
    icon: "image",
    tone: "orange",
  },

  legal: {
    icon: "law",
    tone: "blue",
  },

  report: {
    icon: "report",
    tone: "orange",
  },

  emergency: {
    icon: "alert",
    tone: "coral",
  },

  support: {
    icon: "shield",
    tone: "green",
  },
};


/* =========================================================
   COPY
========================================================= */

const COPY = {
  fr: {
    eyebrow:
      "Administration des contenus",

    title:
      "Base documentaire",

    subtitle:
      "Ajoutez, modifiez et publiez les ressources proposées aux victimes dans leur espace EMC Helpline.",

    add:
      "Ajouter une ressource",

    total:
      "Total",

    published:
      "Publiées",

    drafts:
      "Brouillons",

    searchPlaceholder:
      "Rechercher une ressource...",

    all:
      "Toutes",

    publishedFilter:
      "Publiées",

    draftsFilter:
      "Brouillons",

    empty:
      "Aucune ressource ne correspond aux critères sélectionnés.",

    loading:
      "Chargement des ressources...",

    retry:
      "Réessayer",

    edit:
      "Modifier",

    publish:
      "Publier",

    unpublish:
      "Dépublier",

    delete:
      "Supprimer",

    created:
      "Créée",

    updated:
      "Modifiée",

    order:
      "Ordre",

    french:
      "Français",

    arabic:
      "العربية",

    newResource:
      "Nouvelle ressource",

    editResource:
      "Modifier la ressource",

    formSubtitle:
      "Les champs français et arabes seront affichés dans l’espace victime selon la langue choisie.",

    category:
      "Catégorie",

    titleFr:
      "Titre français",

    titleAr:
      "Titre arabe",

    descriptionFr:
      "Description courte en français",

    descriptionAr:
      "Description courte en arabe",

    contentFr:
      "Contenu détaillé en français",

    contentAr:
      "Contenu détaillé en arabe",

    pointsFr:
      "Points / conseils en français",

    pointsAr:
      "Points / conseils en arabe",

    pointsHint:
      "Un point par ligne.",

    status:
      "Statut",

    draft:
      "Brouillon",

    publishedStatus:
      "Publiée",

    displayOrder:
      "Ordre d’affichage",

    appearance:
      "Présentation",

    icon:
      "Icône",

    tone:
      "Couleur",

    cancel:
      "Annuler",

    save:
      "Enregistrer",

    create:
      "Créer la ressource",

    saving:
      "Enregistrement...",

    confirmDelete:
      "Supprimer cette ressource ?",

    deleteText:
      "Cette action supprimera définitivement la ressource de PostgreSQL. Elle ne sera plus visible dans l’espace victime.",

    keep:
      "Conserver",

    deleting:
      "Suppression...",

    successCreated:
      "La ressource a été créée.",

    successUpdated:
      "La ressource a été mise à jour.",

    successPublished:
      "La ressource est maintenant publiée.",

    successUnpublished:
      "La ressource est maintenant en brouillon.",

    successDeleted:
      "La ressource a été supprimée.",

    categories: {
      account:
        "Piratage de compte",

      evidence:
        "Conservation des preuves",

      harassment:
        "Cyberharcèlement",

      privacy:
        "Données personnelles / Doxing",

      identity:
        "Usurpation d’identité",

      images:
        "Diffusion d’images",

      legal:
        "Informations juridiques",

      report:
        "Signalement",

      emergency:
        "Situation d’urgence",

      support:
        "Accompagnement",
    },

    tones: {
      purple:
        "Violet",

      blue:
        "Bleu",

      green:
        "Vert",

      pink:
        "Rose",

      orange:
        "Orange",

      coral:
        "Corail",
    },
  },


  ar: {
    eyebrow:
      "إدارة المحتوى",

    title:
      "قاعدة الموارد",

    subtitle:
      "أضف الموارد وعدّلها وانشرها لتظهر للضحايا داخل مساحة EMC Helpline.",

    add:
      "إضافة مورد",

    total:
      "المجموع",

    published:
      "منشورة",

    drafts:
      "مسودات",

    searchPlaceholder:
      "البحث عن مورد...",

    all:
      "الكل",

    publishedFilter:
      "المنشورة",

    draftsFilter:
      "المسودات",

    empty:
      "لا توجد موارد مطابقة للمعايير المحددة.",

    loading:
      "جار تحميل الموارد...",

    retry:
      "إعادة المحاولة",

    edit:
      "تعديل",

    publish:
      "نشر",

    unpublish:
      "إلغاء النشر",

    delete:
      "حذف",

    created:
      "أُنشئت",

    updated:
      "عُدلت",

    order:
      "الترتيب",

    french:
      "Français",

    arabic:
      "العربية",

    newResource:
      "مورد جديد",

    editResource:
      "تعديل المورد",

    formSubtitle:
      "سيظهر المحتوى باللغة الفرنسية أو العربية حسب اللغة المختارة في مساحة الضحية.",

    category:
      "الفئة",

    titleFr:
      "العنوان بالفرنسية",

    titleAr:
      "العنوان بالعربية",

    descriptionFr:
      "الوصف المختصر بالفرنسية",

    descriptionAr:
      "الوصف المختصر بالعربية",

    contentFr:
      "المحتوى المفصل بالفرنسية",

    contentAr:
      "المحتوى المفصل بالعربية",

    pointsFr:
      "النقاط والإرشادات بالفرنسية",

    pointsAr:
      "النقاط والإرشادات بالعربية",

    pointsHint:
      "ضع كل نقطة في سطر مستقل.",

    status:
      "الحالة",

    draft:
      "مسودة",

    publishedStatus:
      "منشورة",

    displayOrder:
      "ترتيب العرض",

    appearance:
      "المظهر",

    icon:
      "الأيقونة",

    tone:
      "اللون",

    cancel:
      "إلغاء",

    save:
      "حفظ",

    create:
      "إنشاء المورد",

    saving:
      "جار الحفظ...",

    confirmDelete:
      "هل تريد حذف هذا المورد؟",

    deleteText:
      "سيتم حذف المورد نهائيًا من قاعدة البيانات ولن يظهر بعد ذلك في مساحة الضحية.",

    keep:
      "الاحتفاظ به",

    deleting:
      "جار الحذف...",

    successCreated:
      "تم إنشاء المورد.",

    successUpdated:
      "تم تحديث المورد.",

    successPublished:
      "تم نشر المورد.",

    successUnpublished:
      "تم تحويل المورد إلى مسودة.",

    successDeleted:
      "تم حذف المورد.",

    categories: {
      account:
        "اختراق الحساب",

      evidence:
        "الاحتفاظ بالأدلة",

      harassment:
        "التحرش الإلكتروني",

      privacy:
        "البيانات الشخصية",

      identity:
        "انتحال الهوية",

      images:
        "نشر الصور دون موافقة",

      legal:
        "المعلومات القانونية",

      report:
        "التبليغ",

      emergency:
        "حالة طارئة",

      support:
        "المرافقة",
    },

    tones: {
      purple:
        "بنفسجي",

      blue:
        "أزرق",

      green:
        "أخضر",

      pink:
        "وردي",

      orange:
        "برتقالي",

      coral:
        "مرجاني",
    },
  },
};


/* =========================================================
   EMPTY FORM
========================================================= */

const EMPTY_FORM = {
  category:
    "account",

  title_fr:
    "",

  title_ar:
    "",

  description_fr:
    "",

  description_ar:
    "",

  content_fr:
    "",

  content_ar:
    "",

  points_fr:
    "",

  points_ar:
    "",

  icon:
    "account",

  tone:
    "purple",

  status:
    "draft",

  display_order:
    0,
};


/* =========================================================
   HELPERS
========================================================= */

function pointsToText(points) {
  return Array.isArray(points)
    ? points.join("\n")
    : "";
}


function textToPoints(value) {
  return value
    .split("\n")
    .map(
      (item) =>
        item.trim()
    )
    .filter(Boolean);
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
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    ).format(
      new Date(value)
    );
  } catch {
    return value;
  }
}


/* =========================================================
   RESOURCE FORM MODAL
========================================================= */

function ResourceFormModal({
  open,
  resource,
  language,
  copy,
  saving,
  onClose,
  onSave,
}) {
  const reducedMotion =
    useReducedMotion();


  const [
    form,
    setForm,
  ] = useState(
    EMPTY_FORM
  );


  const [
    localError,
    setLocalError,
  ] = useState("");


  useEffect(
    () => {
      if (!open) {
        return;
      }

      setLocalError("");


      if (resource) {
        setForm({
          category:
            resource.category
            || "account",

          title_fr:
            resource.title_fr
            || "",

          title_ar:
            resource.title_ar
            || "",

          description_fr:
            resource.description_fr
            || "",

          description_ar:
            resource.description_ar
            || "",

          content_fr:
            resource.content_fr
            || "",

          content_ar:
            resource.content_ar
            || "",

          points_fr:
            pointsToText(
              resource.points_fr
            ),

          points_ar:
            pointsToText(
              resource.points_ar
            ),

          icon:
            resource.icon
            || CATEGORY_CONFIG[
              resource.category
            ]?.icon
            || "account",

          tone:
            resource.tone
            || CATEGORY_CONFIG[
              resource.category
            ]?.tone
            || "purple",

          status:
            resource.status
            || "draft",

          display_order:
            Number(
              resource.display_order
            )
            || 0,
        });
      } else {
        setForm({
          ...EMPTY_FORM,
        });
      }
    },
    [
      open,
      resource,
    ]
  );


  useEffect(
    () => {
      if (!open) {
        return undefined;
      }


      const previous =
        document.body.style
          .overflow;


      document.body.style
        .overflow = "hidden";


      const handleEscape =
        (event) => {
          if (
            event.key === "Escape"
            && !saving
          ) {
            onClose();
          }
        };


      document.addEventListener(
        "keydown",
        handleEscape
      );


      return () => {
        document.body.style
          .overflow = previous;


        document.removeEventListener(
          "keydown",
          handleEscape
        );
      };
    },
    [
      open,
      saving,
      onClose,
    ]
  );


  const setField =
    (
      field,
      value
    ) => {
      setForm(
        (current) => ({
          ...current,
          [field]: value,
        })
      );
    };


  const handleCategory =
    (value) => {
      const config =
        CATEGORY_CONFIG[value];


      setForm(
        (current) => ({
          ...current,

          category:
            value,

          icon:
            config?.icon
            || current.icon,

          tone:
            config?.tone
            || current.tone,
        })
      );
    };


  const handleSubmit =
    async (event) => {
      event.preventDefault();

      setLocalError("");


      const required = [
        form.title_fr,
        form.title_ar,
        form.description_fr,
        form.description_ar,
      ];


      if (
        required.some(
          (value) =>
            !value.trim()
        )
      ) {
        setLocalError(
          language === "ar"
            ? "يرجى ملء العنوان والوصف بالفرنسية والعربية."
            : "Veuillez renseigner les titres et descriptions en français et en arabe."
        );

        return;
      }


      try {
        await onSave({
          category:
            form.category,

          title_fr:
            form.title_fr.trim(),

          title_ar:
            form.title_ar.trim(),

          description_fr:
            form.description_fr.trim(),

          description_ar:
            form.description_ar.trim(),

          content_fr:
            form.content_fr.trim()
            || null,

          content_ar:
            form.content_ar.trim()
            || null,

          points_fr:
            textToPoints(
              form.points_fr
            ),

          points_ar:
            textToPoints(
              form.points_ar
            ),

          icon:
            form.icon.trim()
            || null,

          tone:
            form.tone
            || null,

          status:
            form.status,

          display_order:
            Math.max(
              0,
              Number(
                form.display_order
              )
              || 0
            ),
        });
      } catch (submitError) {
        setLocalError(
          submitError.message
        );
      }
    };


  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="document-modal-layer"
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          exit={{
            opacity: 0,
          }}
          transition={{
            duration: 0.16,
          }}
        >
          <button
            type="button"
            className="document-modal-backdrop"
            aria-label={
              copy.cancel
            }
            onClick={
              saving
                ? undefined
                : onClose
            }
          />


          <motion.section
            className="document-resource-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-modal-title"
            dir={
              language === "ar"
                ? "rtl"
                : "ltr"
            }
            initial={
              reducedMotion
                ? false
                : {
                    opacity: 0,
                    scale: 0.96,
                    y: 18,
                  }
            }
            animate={{
              opacity: 1,
              scale: 1,
              y: 0,
            }}
            exit={{
              opacity: 0,
              scale: 0.96,
              y: 12,
            }}
            transition={{
              duration: 0.2,
              ease: "easeOut",
            }}
          >
            <header className="document-modal-header">
              <div>
                <span>
                  {resource
                    ? copy.editResource
                    : copy.newResource}
                </span>


                <h2 id="document-modal-title">
                  {resource
                    ? copy.editResource
                    : copy.newResource}
                </h2>


                <p>
                  {copy.formSubtitle}
                </p>
              </div>


              <button
                type="button"
                className="document-modal-close"
                onClick={
                  onClose
                }
                disabled={
                  saving
                }
                aria-label={
                  copy.cancel
                }
              >
                <AdminResourceIcon
                  name="close"
                />
              </button>
            </header>


            <form
              className="document-resource-form"
              onSubmit={
                handleSubmit
              }
            >
              {localError && (
                <div className="document-form-error">
                  <AdminResourceIcon
                    name="warning"
                    size={18}
                  />

                  <span>
                    {localError}
                  </span>
                </div>
              )}


              {/* GENERAL */}

              <div className="document-form-grid">
                <label className="document-form-field">
                  <span>
                    {copy.category}
                  </span>


                  <select
                    value={
                      form.category
                    }
                    onChange={
                      (event) =>
                        handleCategory(
                          event.target.value
                        )
                    }
                  >
                    {Object.keys(
                      CATEGORY_CONFIG
                    ).map(
                      (item) => (
                        <option
                          key={item}
                          value={item}
                        >
                          {
                            copy.categories[
                              item
                            ]
                          }
                        </option>
                      )
                    )}
                  </select>
                </label>


                <label className="document-form-field">
                  <span>
                    {copy.status}
                  </span>


                  <select
                    value={
                      form.status
                    }
                    onChange={
                      (event) =>
                        setField(
                          "status",
                          event.target.value
                        )
                    }
                  >
                    <option value="draft">
                      {copy.draft}
                    </option>

                    <option value="published">
                      {copy.publishedStatus}
                    </option>
                  </select>
                </label>


                <label className="document-form-field">
                  <span>
                    {copy.displayOrder}
                  </span>


                  <input
                    type="number"
                    min="0"
                    max="100000"
                    value={
                      form.display_order
                    }
                    onChange={
                      (event) =>
                        setField(
                          "display_order",
                          event.target.value
                        )
                    }
                  />
                </label>


                <label className="document-form-field">
                  <span>
                    {copy.tone}
                  </span>


                  <select
                    value={
                      form.tone
                    }
                    onChange={
                      (event) =>
                        setField(
                          "tone",
                          event.target.value
                        )
                    }
                  >
                    {Object.keys(
                      copy.tones
                    ).map(
                      (tone) => (
                        <option
                          key={tone}
                          value={tone}
                        >
                          {
                            copy.tones[
                              tone
                            ]
                          }
                        </option>
                      )
                    )}
                  </select>
                </label>
              </div>


              {/* FR */}

              <div className="document-form-language-block">
                <div className="document-language-title">
                  <span>
                    FR
                  </span>

                  <strong>
                    {copy.french}
                  </strong>
                </div>


                <label className="document-form-field">
                  <span>
                    {copy.titleFr}
                  </span>


                  <input
                    type="text"
                    maxLength={255}
                    value={
                      form.title_fr
                    }
                    onChange={
                      (event) =>
                        setField(
                          "title_fr",
                          event.target.value
                        )
                    }
                  />
                </label>


                <label className="document-form-field">
                  <span>
                    {copy.descriptionFr}
                  </span>


                  <textarea
                    rows={3}
                    value={
                      form.description_fr
                    }
                    onChange={
                      (event) =>
                        setField(
                          "description_fr",
                          event.target.value
                        )
                    }
                  />
                </label>


                <label className="document-form-field">
                  <span>
                    {copy.contentFr}
                  </span>


                  <textarea
                    rows={5}
                    value={
                      form.content_fr
                    }
                    onChange={
                      (event) =>
                        setField(
                          "content_fr",
                          event.target.value
                        )
                    }
                  />
                </label>


                <label className="document-form-field">
                  <span>
                    {copy.pointsFr}
                  </span>


                  <textarea
                    rows={5}
                    value={
                      form.points_fr
                    }
                    placeholder={
                      copy.pointsHint
                    }
                    onChange={
                      (event) =>
                        setField(
                          "points_fr",
                          event.target.value
                        )
                    }
                  />


                  <small>
                    {copy.pointsHint}
                  </small>
                </label>
              </div>


              {/* AR */}

              <div
                className="document-form-language-block document-form-arabic"
                dir="rtl"
              >
                <div className="document-language-title">
                  <span>
                    AR
                  </span>

                  <strong>
                    {copy.arabic}
                  </strong>
                </div>


                <label className="document-form-field">
                  <span>
                    {copy.titleAr}
                  </span>


                  <input
                    type="text"
                    maxLength={255}
                    value={
                      form.title_ar
                    }
                    onChange={
                      (event) =>
                        setField(
                          "title_ar",
                          event.target.value
                        )
                    }
                  />
                </label>


                <label className="document-form-field">
                  <span>
                    {copy.descriptionAr}
                  </span>


                  <textarea
                    rows={3}
                    value={
                      form.description_ar
                    }
                    onChange={
                      (event) =>
                        setField(
                          "description_ar",
                          event.target.value
                        )
                    }
                  />
                </label>


                <label className="document-form-field">
                  <span>
                    {copy.contentAr}
                  </span>


                  <textarea
                    rows={5}
                    value={
                      form.content_ar
                    }
                    onChange={
                      (event) =>
                        setField(
                          "content_ar",
                          event.target.value
                        )
                    }
                  />
                </label>


                <label className="document-form-field">
                  <span>
                    {copy.pointsAr}
                  </span>


                  <textarea
                    rows={5}
                    value={
                      form.points_ar
                    }
                    placeholder={
                      copy.pointsHint
                    }
                    onChange={
                      (event) =>
                        setField(
                          "points_ar",
                          event.target.value
                        )
                    }
                  />


                  <small>
                    {copy.pointsHint}
                  </small>
                </label>
              </div>


              {/* APPEARANCE */}

              <div className="document-form-appearance">
                <strong>
                  {copy.appearance}
                </strong>


                <div className="document-form-grid">
                  <label className="document-form-field">
                    <span>
                      {copy.icon}
                    </span>


                    <input
                      type="text"
                      maxLength={50}
                      value={
                        form.icon
                      }
                      onChange={
                        (event) =>
                          setField(
                            "icon",
                            event.target.value
                          )
                      }
                    />
                  </label>


                  <div className="document-tone-preview">
                    <span
                      className={
                        `document-tone-dot tone-${form.tone}`
                      }
                    />


                    <div>
                      <small>
                        {copy.tone}
                      </small>

                      <strong>
                        {
                          copy.tones[
                            form.tone
                          ]
                        }
                      </strong>
                    </div>
                  </div>
                </div>
              </div>


              {/* FOOTER */}

              <footer className="document-form-footer">
                <button
                  type="button"
                  className="document-secondary-button"
                  onClick={
                    onClose
                  }
                  disabled={
                    saving
                  }
                >
                  {copy.cancel}
                </button>


                <button
                  type="submit"
                  className="document-primary-button"
                  disabled={
                    saving
                  }
                >
                  {saving
                    ? copy.saving
                    : resource
                      ? copy.save
                      : copy.create}
                </button>
              </footer>
            </form>
          </motion.section>
        </motion.div>
      )}
    </AnimatePresence>
  );
}


/* =========================================================
   DELETE MODAL
========================================================= */

function DeleteModal({
  resource,
  language,
  copy,
  deleting,
  onClose,
  onConfirm,
}) {
  const reducedMotion =
    useReducedMotion();


  return (
    <AnimatePresence>
      {resource && (
        <motion.div
          className="document-modal-layer document-delete-layer"
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          exit={{
            opacity: 0,
          }}
        >
          <button
            type="button"
            className="document-modal-backdrop"
            aria-label={
              copy.cancel
            }
            onClick={
              deleting
                ? undefined
                : onClose
            }
          />


          <motion.section
            className="document-delete-modal"
            role="alertdialog"
            aria-modal="true"
            dir={
              language === "ar"
                ? "rtl"
                : "ltr"
            }
            initial={
              reducedMotion
                ? false
                : {
                    opacity: 0,
                    scale: 0.96,
                    y: 14,
                  }
            }
            animate={{
              opacity: 1,
              scale: 1,
              y: 0,
            }}
            exit={{
              opacity: 0,
              scale: 0.96,
              y: 10,
            }}
            transition={{
              duration: 0.18,
            }}
          >
            <span className="document-delete-icon">
              <AdminResourceIcon
                name="trash"
                size={27}
              />
            </span>


            <h2>
              {copy.confirmDelete}
            </h2>


            <strong>
              {language === "ar"
                ? resource.title_ar
                : resource.title_fr}
            </strong>


            <p>
              {copy.deleteText}
            </p>


            <div className="document-delete-actions">
              <button
                type="button"
                className="document-secondary-button"
                onClick={
                  onClose
                }
                disabled={
                  deleting
                }
              >
                {copy.keep}
              </button>


              <button
                type="button"
                className="document-danger-button"
                onClick={
                  onConfirm
                }
                disabled={
                  deleting
                }
              >
                {deleting
                  ? copy.deleting
                  : copy.delete}
              </button>
            </div>
          </motion.section>
        </motion.div>
      )}
    </AnimatePresence>
  );
}


/* =========================================================
   MAIN
========================================================= */

function DocumentBase() {
  const {
    language,
  } = useLanguage();


  const reducedMotion =
    useReducedMotion();


  const isArabic =
    language === "ar";


  const copy =
    COPY[
      isArabic
        ? "ar"
        : "fr"
    ];


  const [
    resources,
    setResources,
  ] = useState([]);


  const [
    loadStatus,
    setLoadStatus,
  ] = useState("loading");


  const [
    error,
    setError,
  ] = useState("");


  const [
    message,
    setMessage,
  ] = useState("");


  const [
    search,
    setSearch,
  ] = useState("");


  const [
    statusFilter,
    setStatusFilter,
  ] = useState("all");


  const [
    formOpen,
    setFormOpen,
  ] = useState(false);


  const [
    editingResource,
    setEditingResource,
  ] = useState(null);


  const [
    saving,
    setSaving,
  ] = useState(false);


  const [
    deletingResource,
    setDeletingResource,
  ] = useState(null);


  const [
    deleting,
    setDeleting,
  ] = useState(false);


  const [
    busyIds,
    setBusyIds,
  ] = useState({});


  /* ======================================================
     LOAD
  ====================================================== */

  const loadResources =
    useCallback(
      async () => {
        setLoadStatus("loading");
        setError("");


        try {
          const response =
            await fetch(
              `${API_BASE_URL}/admin/resources`,
              {
                credentials:
                  "include",

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
                : `Erreur API (${response.status})`
            );
          }


          setResources(
            Array.isArray(data)
              ? data
              : []
          );


          setLoadStatus(
            "success"
          );
        } catch (loadError) {
          console.error(
            "Erreur ressources admin :",
            loadError
          );


          setError(
            loadError.message
          );


          setLoadStatus(
            "error"
          );
        }
      },
      []
    );


  useEffect(
    () => {
      loadResources();
    },
    [
      loadResources,
    ]
  );


  /* ======================================================
     STATS
  ====================================================== */

  const stats =
    useMemo(
      () => {
        const published =
          resources.filter(
            (item) =>
              item.status
              === "published"
          ).length;


        const drafts =
          resources.filter(
            (item) =>
              item.status
              === "draft"
          ).length;


        return {
          total:
            resources.length,

          published,

          drafts,
        };
      },
      [
        resources,
      ]
    );


  /* ======================================================
     FILTER
  ====================================================== */

  const filteredResources =
    useMemo(
      () => {
        const normalized =
          search
            .trim()
            .toLowerCase();


        return resources.filter(
          (resource) => {
            const statusMatches =
              statusFilter
                === "all"
              || resource.status
                === statusFilter;


            if (!statusMatches) {
              return false;
            }


            if (!normalized) {
              return true;
            }


            const searchable = [
              resource.title_fr,
              resource.title_ar,
              resource.description_fr,
              resource.description_ar,
              resource.category,
            ]
              .filter(Boolean)
              .join(" ")
              .toLowerCase();


            return searchable.includes(
              normalized
            );
          }
        );
      },
      [
        resources,
        search,
        statusFilter,
      ]
    );


  /* ======================================================
     OPEN FORM
  ====================================================== */

  const handleNew =
    () => {
      setEditingResource(
        null
      );

      setFormOpen(
        true
      );
    };


  const handleEdit =
    (resource) => {
      setEditingResource(
        resource
      );

      setFormOpen(
        true
      );
    };


  const closeForm =
    () => {
      if (saving) {
        return;
      }


      setFormOpen(false);
      setEditingResource(null);
    };


  /* ======================================================
     CREATE / UPDATE
  ====================================================== */

  const handleSave =
    async (payload) => {
      setSaving(true);
      setError("");
      setMessage("");


      try {
        const csrfToken =
          getCsrfToken();


        const isEdit =
          Boolean(
            editingResource?.id
          );


        const url =
          isEdit
            ? `${API_BASE_URL}/admin/resources/${editingResource.id}`
            : `${API_BASE_URL}/admin/resources`;


        const response =
          await fetch(
            url,
            {
              method:
                isEdit
                  ? "PATCH"
                  : "POST",

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
                JSON.stringify(
                  payload
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
            typeof data?.detail
              === "string"
              ? data.detail
              : `Erreur API (${response.status})`
          );
        }


        if (isEdit) {
          setResources(
            (current) =>
              current.map(
                (item) =>
                  item.id
                    === data.id
                    ? data
                    : item
              )
          );


          setMessage(
            copy.successUpdated
          );
        } else {
          setResources(
            (current) => [
              data,
              ...current,
            ]
          );


          setMessage(
            copy.successCreated
          );
        }


        setFormOpen(false);
        setEditingResource(null);
      } finally {
        setSaving(false);
      }
    };


  /* ======================================================
     PUBLISH / UNPUBLISH
  ====================================================== */

  const handleToggleStatus =
    async (resource) => {
      if (
        busyIds[
          resource.id
        ]
      ) {
        return;
      }


      setBusyIds(
        (current) => ({
          ...current,

          [resource.id]:
            true,
        })
      );


      setError("");
      setMessage("");


      try {
        const nextStatus =
          resource.status
            === "published"
            ? "draft"
            : "published";


        const response =
          await fetch(
            `${API_BASE_URL}/admin/resources/${resource.id}`,
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
                  getCsrfToken(),
              },

              body:
                JSON.stringify({
                  status:
                    nextStatus,
                }),
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
              : `Erreur API (${response.status})`
          );
        }


        setResources(
          (current) =>
            current.map(
              (item) =>
                item.id
                  === data.id
                  ? data
                  : item
            )
        );


        setMessage(
          nextStatus
            === "published"
            ? copy.successPublished
            : copy.successUnpublished
        );
      } catch (statusError) {
        console.error(
          "Erreur changement statut :",
          statusError
        );


        setError(
          statusError.message
        );
      } finally {
        setBusyIds(
          (current) => ({
            ...current,

            [resource.id]:
              false,
          })
        );
      }
    };


  /* ======================================================
     DELETE
  ====================================================== */

  const handleDelete =
    async () => {
      if (
        !deletingResource?.id
      ) {
        return;
      }


      setDeleting(true);
      setError("");
      setMessage("");


      try {
        const response =
          await fetch(
            `${API_BASE_URL}/admin/resources/${deletingResource.id}`,
            {
              method:
                "DELETE",

              credentials:
                "include",

              headers: {
                "X-CSRF-Token":
                  getCsrfToken(),
              },
            }
          );


        if (
          response.status
          !== 204
        ) {
          const data =
            await response
              .json()
              .catch(
                () => null
              );


          throw new Error(
            typeof data?.detail
              === "string"
              ? data.detail
              : `Erreur API (${response.status})`
          );
        }


        setResources(
          (current) =>
            current.filter(
              (item) =>
                item.id
                !== deletingResource.id
            )
        );


        setDeletingResource(
          null
        );


        setMessage(
          copy.successDeleted
        );
      } catch (deleteError) {
        console.error(
          "Erreur suppression ressource :",
          deleteError
        );


        setError(
          deleteError.message
        );
      } finally {
        setDeleting(false);
      }
    };


  return (
    <motion.div
      className="document-base-page"
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
      {/* HERO */}

      <section className="document-admin-hero">
        <div>
          <span className="document-admin-eyebrow">
            <AdminResourceIcon
              name="database"
              size={18}
            />

            {copy.eyebrow}
          </span>


          <h1>
            {copy.title}
          </h1>


          <p>
            {copy.subtitle}
          </p>
        </div>


        <button
          type="button"
          className="document-add-button"
          onClick={
            handleNew
          }
        >
          <AdminResourceIcon
            name="plus"
            size={19}
          />

          {copy.add}
        </button>
      </section>


      {/* STATS */}

      <section className="document-stats-grid">
        <article>
          <span className="document-stat-icon total">
            <AdminResourceIcon
              name="database"
            />
          </span>


          <div>
            <small>
              {copy.total}
            </small>

            <strong>
              {stats.total}
            </strong>
          </div>
        </article>


        <article>
          <span className="document-stat-icon published">
            <AdminResourceIcon
              name="eye"
            />
          </span>


          <div>
            <small>
              {copy.published}
            </small>

            <strong>
              {stats.published}
            </strong>
          </div>
        </article>


        <article>
          <span className="document-stat-icon draft">
            <AdminResourceIcon
              name="eye-off"
            />
          </span>


          <div>
            <small>
              {copy.drafts}
            </small>

            <strong>
              {stats.drafts}
            </strong>
          </div>
        </article>
      </section>


      {/* SUCCESS */}

      <AnimatePresence>
        {message && (
          <motion.div
            className="document-message success"
            initial={{
              opacity: 0,
              y: -6,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            exit={{
              opacity: 0,
            }}
          >
            <AdminResourceIcon
              name="check"
              size={18}
            />


            <span>
              {message}
            </span>


            <button
              type="button"
              onClick={() =>
                setMessage("")
              }
              aria-label="Fermer"
            >
              ×
            </button>
          </motion.div>
        )}
      </AnimatePresence>


      {/* ERROR */}

      {error && (
        <div className="document-message error">
          <AdminResourceIcon
            name="warning"
            size={18}
          />


          <span>
            {error}
          </span>


          <button
            type="button"
            onClick={() =>
              setError("")
            }
            aria-label="Fermer"
          >
            ×
          </button>
        </div>
      )}


      {/* TOOLBAR */}

      <section className="document-toolbar">
        <div className="document-search">
          <AdminResourceIcon
            name="search"
            size={19}
          />


          <input
            type="search"
            value={
              search
            }
            placeholder={
              copy.searchPlaceholder
            }
            onChange={
              (event) =>
                setSearch(
                  event.target.value
                )
            }
          />
        </div>


        <div className="document-filter-tabs">
          <button
            type="button"
            className={
              statusFilter
                === "all"
                ? "active"
                : ""
            }
            onClick={() =>
              setStatusFilter(
                "all"
              )
            }
          >
            {copy.all}

            <span>
              {stats.total}
            </span>
          </button>


          <button
            type="button"
            className={
              statusFilter
                === "published"
                ? "active"
                : ""
            }
            onClick={() =>
              setStatusFilter(
                "published"
              )
            }
          >
            {copy.publishedFilter}

            <span>
              {stats.published}
            </span>
          </button>


          <button
            type="button"
            className={
              statusFilter
                === "draft"
                ? "active"
                : ""
            }
            onClick={() =>
              setStatusFilter(
                "draft"
              )
            }
          >
            {copy.draftsFilter}

            <span>
              {stats.drafts}
            </span>
          </button>
        </div>


        <button
          type="button"
          className="document-refresh-button"
          onClick={
            loadResources
          }
          aria-label={
            copy.retry
          }
        >
          <AdminResourceIcon
            name="refresh"
            size={19}
          />
        </button>
      </section>


      {/* LIST */}

      {loadStatus
        === "loading"
        ? (
          <section className="document-loading">
            <span />

            <p>
              {copy.loading}
            </p>
          </section>
        )
        : loadStatus
            === "error"
          ? (
            <section className="document-empty-state">
              <span>
                <AdminResourceIcon
                  name="warning"
                  size={30}
                />
              </span>


              <p>
                {error}
              </p>


              <button
                type="button"
                onClick={
                  loadResources
                }
              >
                {copy.retry}
              </button>
            </section>
          )
          : filteredResources.length
              === 0
            ? (
              <section className="document-empty-state">
                <span>
                  <AdminResourceIcon
                    name="database"
                    size={31}
                  />
                </span>


                <p>
                  {copy.empty}
                </p>
              </section>
            )
            : (
              <section className="document-resource-list">
                {filteredResources.map(
                  (
                    resource,
                    index
                  ) => {
                    const title =
                      isArabic
                        ? resource.title_ar
                        : resource.title_fr;


                    const description =
                      isArabic
                        ? resource.description_ar
                        : resource.description_fr;


                    return (
                      <motion.article
                        key={
                          resource.id
                        }
                        className="document-resource-card"
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
                            Math.min(
                              index
                              * 0.035,
                              0.25
                            ),
                        }}
                      >
                        <div className="document-resource-main">
                          <span
                            className={
                              `document-resource-symbol tone-${resource.tone || "purple"}`
                            }
                          >
                            <AdminResourceIcon
                              name="database"
                              size={23}
                            />
                          </span>


                          <div className="document-resource-copy">
                            <div className="document-resource-title-line">
                              <h2>
                                {title}
                              </h2>


                              <span
                                className={
                                  resource.status
                                    === "published"
                                    ? "document-status published"
                                    : "document-status draft"
                                }
                              >
                                <i />

                                {resource.status
                                  === "published"
                                  ? copy.publishedStatus
                                  : copy.draft}
                              </span>
                            </div>


                            <div className="document-resource-meta">
                              <span>
                                {
                                  copy.categories[
                                    resource.category
                                  ]
                                  || resource.category
                                }
                              </span>


                              <span>
                                FR + العربية
                              </span>


                              <span>
                                {copy.order}
                                {" "}
                                {resource.display_order}
                              </span>
                            </div>


                            <p>
                              {description}
                            </p>


                            <small className="document-resource-date">
                              {copy.updated}
                              {" : "}
                              {formatDate(
                                resource.updated_at,
                                language
                              )}
                            </small>
                          </div>
                        </div>


                        <div className="document-resource-actions">
                          <button
                            type="button"
                            className="document-card-action edit"
                            onClick={() =>
                              handleEdit(
                                resource
                              )
                            }
                          >
                            <AdminResourceIcon
                              name="edit"
                              size={17}
                            />

                            {copy.edit}
                          </button>


                          <button
                            type="button"
                            className={
                              resource.status
                                === "published"
                                ? "document-card-action unpublish"
                                : "document-card-action publish"
                            }
                            disabled={
                              Boolean(
                                busyIds[
                                  resource.id
                                ]
                              )
                            }
                            onClick={() =>
                              handleToggleStatus(
                                resource
                              )
                            }
                          >
                            <AdminResourceIcon
                              name={
                                resource.status
                                  === "published"
                                  ? "eye-off"
                                  : "eye"
                              }
                              size={17}
                            />


                            {resource.status
                              === "published"
                              ? copy.unpublish
                              : copy.publish}
                          </button>


                          <button
                            type="button"
                            className="document-card-action delete"
                            onClick={() =>
                              setDeletingResource(
                                resource
                              )
                            }
                          >
                            <AdminResourceIcon
                              name="trash"
                              size={17}
                            />

                            {copy.delete}
                          </button>
                        </div>
                      </motion.article>
                    );
                  }
                )}
              </section>
            )}


      <ResourceFormModal
        open={
          formOpen
        }
        resource={
          editingResource
        }
        language={
          language
        }
        copy={
          copy
        }
        saving={
          saving
        }
        onClose={
          closeForm
        }
        onSave={
          handleSave
        }
      />


      <DeleteModal
        resource={
          deletingResource
        }
        language={
          language
        }
        copy={
          copy
        }
        deleting={
          deleting
        }
        onClose={() =>
          !deleting
          && setDeletingResource(
            null
          )
        }
        onConfirm={
          handleDelete
        }
      />
    </motion.div>
  );
}


export default DocumentBase;