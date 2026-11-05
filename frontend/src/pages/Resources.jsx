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
  AnimatePresence,
  motion,
  useReducedMotion,
} from "framer-motion";

import {
  useLanguage,
} from "../context/LanguageContext.jsx";

import "./Resources.css";


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


/* =========================================================
   INTENT -> CATEGORIES RECOMMANDÉES
========================================================= */

const INTENT_CATEGORY_MAP = {
  "Cyberharcèlement": [
    "harassment",
    "evidence",
    "report",
  ],

  "Sextorsion": [
    "images",
    "evidence",
    "report",
  ],

  "Piratage de compte": [
    "account",
    "evidence",
  ],

  "Divulgation de données personnelles (Doxing)": [
    "privacy",
    "evidence",
    "report",
  ],

  "Conservation des preuves": [
    "evidence",
  ],

  "Informations juridiques": [
    "legal",
  ],

  "Usurpation d'identité": [
    "identity",
    "evidence",
    "report",
  ],

  "Diffusion non consentie d'images": [
    "images",
    "evidence",
    "report",
  ],

  "Signalement": [
    "report",
    "evidence",
  ],

  "Situation d'urgence": [
    "emergency",
  ],

  "Accompagnement de la victime": [
    "support",
  ],
};


/* =========================================================
   ICONS
========================================================= */

function ResourceIcon({
  name,
  size = 22,
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


  if (name === "shield") {
    return (
      <svg {...props}>
        <path d="M12 3 5 6v5c0 4.7 2.7 8 7 10 4.3-2 7-5.3 7-10V6z" />
        <path d="m9 12 2 2 4-4" />
      </svg>
    );
  }


  if (name === "account") {
    return (
      <svg {...props}>
        <circle
          cx="12"
          cy="8"
          r="4"
        />

        <path d="M5 20c.8-4 3.2-6 7-6s6.2 2 7 6" />
        <path d="M18 5l2-2" />
        <path d="M19 8h3" />
      </svg>
    );
  }


  if (name === "clip") {
    return (
      <svg {...props}>
        <path d="m8.5 12.5 6.2-6.2a3 3 0 0 1 4.2 4.2l-8 8a5 5 0 0 1-7.1-7.1l8.2-8.2" />
      </svg>
    );
  }


  if (name === "privacy") {
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


  if (name === "identity") {
    return (
      <svg {...props}>
        <rect
          x="3"
          y="5"
          width="18"
          height="14"
          rx="2"
        />

        <circle
          cx="9"
          cy="11"
          r="2"
        />

        <path d="M6 16c.5-2 1.5-3 3-3s2.5 1 3 3" />
        <path d="M14 10h4" />
        <path d="M14 14h4" />
      </svg>
    );
  }


  if (name === "image") {
    return (
      <svg {...props}>
        <rect
          x="3"
          y="4"
          width="18"
          height="16"
          rx="2"
        />

        <circle
          cx="9"
          cy="9"
          r="2"
        />

        <path d="m4 17 5-5 4 4 2-2 5 5" />
      </svg>
    );
  }


  if (name === "chat") {
    return (
      <svg {...props}>
        <path d="M4 5h16v11H8l-4 3z" />
        <path d="M8 9h8" />
        <path d="M8 12h5" />
      </svg>
    );
  }


  if (name === "law") {
    return (
      <svg {...props}>
        <path d="M12 3v18" />
        <path d="M6 6h12" />
        <path d="m6 6-3 6h6z" />
        <path d="m18 6-3 6h6z" />
        <path d="M7 21h10" />
      </svg>
    );
  }


  if (name === "alert") {
    return (
      <svg {...props}>
        <path d="M12 3 3 20h18z" />
        <path d="M12 9v4" />
        <path d="M12 17h.01" />
      </svg>
    );
  }


  if (name === "report") {
    return (
      <svg {...props}>
        <path d="M5 21V4" />
        <path d="M5 5h11l-1 5 1 5H5" />
      </svg>
    );
  }


  if (name === "book") {
    return (
      <svg {...props}>
        <path d="M4 5a3 3 0 0 1 3-2h5v17H7a3 3 0 0 0-3 2z" />
        <path d="M20 5a3 3 0 0 0-3-2h-5v17h5a3 3 0 0 1 3 2z" />
      </svg>
    );
  }


  if (name === "spark") {
    return (
      <svg {...props}>
        <path d="m12 2 1.2 4.2L17 8l-3.8 1.8L12 14l-1.2-4.2L7 8l3.8-1.8z" />
        <path d="m19 15 .6 2 1.8.9-1.8 1-.6 2.1-.6-2.1-1.8-1 1.8-.9z" />
      </svg>
    );
  }


  if (name === "arrow") {
    return (
      <svg {...props}>
        <path d="M5 12h14" />
        <path d="m14 7 5 5-5 5" />
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
        <path d="M6.2 8a7 7 0 0 1 11.7-2L20 8" />
        <path d="M17.8 16a7 7 0 0 1-11.7 2L4 16" />
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

      <path d="M12 8v5" />
      <path d="M12 17h.01" />
    </svg>
  );
}


/* =========================================================
   TEXTES
========================================================= */

const COPY = {
  fr: {
    eyebrow:
      "Centre de ressources EMC",

    title:
      "Ressources",

    subtitle:
      "Retrouvez des informations pratiques pour mieux comprendre votre situation, protéger vos données et poursuivre vos démarches.",

    search:
      "Rechercher une ressource...",

    all:
      "Toutes",

    recommended:
      "Recommandées pour votre situation",

    allResources:
      "Toutes les ressources",

    resource:
      "Ressource EMC",

    consult:
      "Consulter",

    close:
      "Fermer",

    useful:
      "À retenir",

    assistantBlock:
      "Besoin d’une orientation personnalisée ?",

    assistantText:
      "L’assistant IA peut vous orienter à partir des informations disponibles dans EMC Helpline.",

    assistant:
      "Parler à l’assistant IA",

    assessment:
      "Évaluer ma situation",

    noResult:
      "Aucune ressource ne correspond à votre recherche.",

    noResources:
      "Aucune ressource n’est disponible pour le moment.",

    noResourcesText:
      "Les ressources publiées par l’équipe EMC apparaîtront ici automatiquement.",

    clear:
      "Effacer la recherche",

    currentSituation:
      "Selon votre dossier actif",

    loading:
      "Chargement des ressources...",

    error:
      "Impossible de charger les ressources.",

    retry:
      "Réessayer",

    categories: {
      account:
        "Piratage de compte",

      evidence:
        "Conservation des preuves",

      harassment:
        "Cyberharcèlement",

      privacy:
        "Données personnelles",

      identity:
        "Usurpation d’identité",

      images:
        "Images non consenties",

      legal:
        "Informations juridiques",

      report:
        "Signalement",

      emergency:
        "Situation d’urgence",

      support:
        "Accompagnement",
    },
  },


  ar: {
    eyebrow:
      "مركز موارد EMC",

    title:
      "الموارد",

    subtitle:
      "اطّلع على معلومات عملية تساعدك على فهم وضعك وحماية بياناتك ومواصلة إجراءاتك.",

    search:
      "البحث عن مورد...",

    all:
      "الكل",

    recommended:
      "موارد مقترحة لحالتك",

    allResources:
      "جميع الموارد",

    resource:
      "مورد EMC",

    consult:
      "عرض",

    close:
      "إغلاق",

    useful:
      "ما يجب تذكره",

    assistantBlock:
      "هل تحتاج إلى توجيه مخصص؟",

    assistantText:
      "يمكن للمساعد الذكي توجيهك اعتمادًا على المعلومات المتاحة داخل EMC Helpline.",

    assistant:
      "التحدث مع المساعد الذكي",

    assessment:
      "تقييم وضعي",

    noResult:
      "لا يوجد مورد مطابق لبحثك.",

    noResources:
      "لا توجد موارد متاحة حاليًا.",

    noResourcesText:
      "ستظهر هنا تلقائيًا الموارد التي تنشرها إدارة EMC.",

    clear:
      "مسح البحث",

    currentSituation:
      "حسب ملفك النشط",

    loading:
      "جار تحميل الموارد...",

    error:
      "تعذر تحميل الموارد.",

    retry:
      "إعادة المحاولة",

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
        "الصور المنشورة دون موافقة",

      legal:
        "المعلومات القانونية",

      report:
        "التبليغ",

      emergency:
        "حالة طارئة",

      support:
        "المرافقة",
    },
  },
};


/* =========================================================
   FALLBACK ICONS / COLORS
========================================================= */

const CATEGORY_ICON = {
  account:
    "account",

  evidence:
    "clip",

  harassment:
    "chat",

  privacy:
    "privacy",

  identity:
    "identity",

  images:
    "image",

  legal:
    "law",

  report:
    "report",

  emergency:
    "alert",

  support:
    "shield",
};


const CATEGORY_TONE = {
  account:
    "purple",

  evidence:
    "blue",

  harassment:
    "pink",

  privacy:
    "green",

  identity:
    "purple",

  images:
    "orange",

  legal:
    "blue",

  report:
    "orange",

  emergency:
    "coral",

  support:
    "green",
};


/* =========================================================
   CARD
========================================================= */

function ResourceCard({
  resource,
  language,
  labels,
  recommended = false,
  index = 0,
  onOpen,
}) {
  const reducedMotion =
    useReducedMotion();


  const isArabic =
    language === "ar";


  const title =
    isArabic
      ? resource.title_ar
      : resource.title_fr;


  const description =
    isArabic
      ? resource.description_ar
      : resource.description_fr;


  const icon =
    resource.icon
    || CATEGORY_ICON[
      resource.category
    ]
    || "book";


  const tone =
    resource.tone
    || CATEGORY_TONE[
      resource.category
    ]
    || "purple";


  return (
    <motion.article
      className={[
        "resource-card",
        `resource-tone-${tone}`,
        recommended
          ? "resource-card-recommended"
          : "",
      ]
        .filter(Boolean)
        .join(" ")}
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
        delay:
          Math.min(
            index * 0.05,
            0.3
          ),
      }}
      whileHover={
        reducedMotion
          ? undefined
          : {
              y: -4,
            }
      }
    >
      <div className="resource-card-top">
        <span className="resource-card-icon">
          <ResourceIcon
            name={icon}
            size={24}
          />
        </span>


        {recommended && (
          <span className="resource-recommended-badge">
            <ResourceIcon
              name="spark"
              size={14}
            />

            {labels.currentSituation}
          </span>
        )}
      </div>


      <span className="resource-category-label">
        {
          labels.categories[
            resource.category
          ]
          || resource.category
        }
      </span>


      <h3>
        {title}
      </h3>


      <p>
        {description}
      </p>


      <button
        type="button"
        className="resource-consult-button"
        onClick={() =>
          onOpen(resource)
        }
      >
        {labels.consult}

        <ResourceIcon
          name="arrow"
          size={17}
        />
      </button>
    </motion.article>
  );
}


/* =========================================================
   CTA ASSISTANT
========================================================= */

function AssistantCallToAction({
  labels,
  navigate,
  reducedMotion,
}) {
  return (
    <motion.section
      className="resources-assistant-card"
      initial={
        reducedMotion
          ? false
          : {
              opacity: 0,
              y: 10,
            }
      }
      whileInView={{
        opacity: 1,
        y: 0,
      }}
      viewport={{
        once: true,
      }}
    >
      <div className="resources-assistant-icon">
        <ResourceIcon
          name="spark"
          size={28}
        />
      </div>


      <div className="resources-assistant-copy">
        <h2>
          {labels.assistantBlock}
        </h2>


        <p>
          {labels.assistantText}
        </p>
      </div>


      <div className="resources-assistant-actions">
        <button
          type="button"
          className="resources-primary-button"
          onClick={() =>
            navigate(
              "/victim/assistant"
            )
          }
        >
          <ResourceIcon
            name="chat"
            size={18}
          />

          {labels.assistant}
        </button>


        <button
          type="button"
          className="resources-secondary-button"
          onClick={() =>
            navigate(
              "/victim/assessment"
            )
          }
        >
          <ResourceIcon
            name="shield"
            size={18}
          />

          {labels.assessment}
        </button>
      </div>
    </motion.section>
  );
}


/* =========================================================
   MAIN
========================================================= */

function Resources() {
  const navigate =
    useNavigate();


  const reducedMotion =
    useReducedMotion();


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
    resources,
    setResources,
  ] = useState([]);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  const [
    search,
    setSearch,
  ] = useState("");


  const [
    category,
    setCategory,
  ] = useState("all");


  const [
    activeIntent,
    setActiveIntent,
  ] = useState(null);


  const [
    selectedResource,
    setSelectedResource,
  ] = useState(null);


  /* ======================================================
     LOAD RESOURCES + ACTIVE CASE
  ====================================================== */

  const loadData =
    useCallback(
      async () => {
        setLoading(true);
        setError("");


        try {
          const [
            resourcesResult,
            casesResult,
          ] =
            await Promise.allSettled([
              fetch(
                `${API_BASE_URL}/resources`,
                {
                  credentials:
                    "include",

                  headers: {
                    Accept:
                      "application/json",
                  },
                }
              ),

              fetch(
                `${API_BASE_URL}/cases`,
                {
                  credentials:
                    "include",

                  headers: {
                    Accept:
                      "application/json",
                  },
                }
              ),
            ]);


          if (
            resourcesResult.status
            !== "fulfilled"
          ) {
            throw new Error(
              labels.error
            );
          }


          const resourcesResponse =
            resourcesResult.value;


          const resourcesData =
            await resourcesResponse
              .json()
              .catch(
                () => null
              );


          if (
            !resourcesResponse.ok
          ) {
            throw new Error(
              typeof resourcesData
                ?.detail
                === "string"
                ? resourcesData.detail
                : labels.error
            );
          }


          setResources(
            Array.isArray(
              resourcesData
            )
              ? resourcesData
              : []
          );


          if (
            casesResult.status
            === "fulfilled"
            && casesResult.value.ok
          ) {
            const casesData =
              await casesResult
                .value
                .json()
                .catch(
                  () => []
                );


            if (
              Array.isArray(
                casesData
              )
              && casesData.length
            ) {
              const activeCase =
                casesData.find(
                  (item) =>
                    item.status
                    === "active"
                )
                || casesData[0];


              setActiveIntent(
                activeCase
                  ?.detected_intent
                || null
              );
            } else {
              setActiveIntent(
                null
              );
            }
          } else {
            setActiveIntent(
              null
            );
          }
        } catch (
          loadError
        ) {
          console.error(
            "Erreur Resources :",
            loadError
          );


          setResources([]);


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
      loadData();
    },
    [
      loadData,
    ]
  );


  /* ======================================================
     CATEGORIES DISPONIBLES
  ====================================================== */

  const availableCategories =
    useMemo(
      () => {
        const found =
          new Set();


        resources.forEach(
          (resource) => {
            if (
              resource.category
            ) {
              found.add(
                resource.category
              );
            }
          }
        );


        return [
          "all",
          ...Array.from(found),
        ];
      },
      [
        resources,
      ]
    );


  useEffect(
    () => {
      if (
        category !== "all"
        && !availableCategories
          .includes(category)
      ) {
        setCategory("all");
      }
    },
    [
      availableCategories,
      category,
    ]
  );


  /* ======================================================
     RECOMMANDATIONS
  ====================================================== */

  const recommendedResources =
    useMemo(
      () => {
        if (
          !resources.length
        ) {
          return [];
        }


        const recommendedCategories =
          INTENT_CATEGORY_MAP[
            activeIntent
          ]
          || [];


        if (
          !recommendedCategories
            .length
        ) {
          return resources.slice(
            0,
            3
          );
        }


        const matches =
          resources.filter(
            (resource) =>
              recommendedCategories
                .includes(
                  resource.category
                )
          );


        if (
          matches.length
        ) {
          return matches.slice(
            0,
            3
          );
        }


        return resources.slice(
          0,
          3
        );
      },
      [
        resources,
        activeIntent,
      ]
    );


  /* ======================================================
     FILTER
  ====================================================== */

  const filteredResources =
    useMemo(
      () => {
        const normalizedSearch =
          search
            .trim()
            .toLocaleLowerCase(
              isArabic
                ? "ar"
                : "fr"
            );


        return resources.filter(
          (resource) => {
            const title =
              isArabic
                ? resource.title_ar
                : resource.title_fr;


            const description =
              isArabic
                ? resource.description_ar
                : resource.description_fr;


            const categoryLabel =
              labels.categories[
                resource.category
              ]
              || resource.category
              || "";


            const categoryMatches =
              category === "all"
              || resource.category
                === category;


            if (
              !categoryMatches
            ) {
              return false;
            }


            if (
              !normalizedSearch
            ) {
              return true;
            }


            const searchable =
              [
                title,
                description,
                categoryLabel,
              ]
                .filter(Boolean)
                .join(" ")
                .toLocaleLowerCase(
                  isArabic
                    ? "ar"
                    : "fr"
                );


            return searchable.includes(
              normalizedSearch
            );
          }
        );
      },
      [
        resources,
        search,
        category,
        isArabic,
        labels.categories,
      ]
    );


  /* ======================================================
     SELECTED RESOURCE
  ====================================================== */

  const selectedTitle =
    selectedResource
      ? (
          isArabic
            ? selectedResource.title_ar
            : selectedResource.title_fr
        )
      : "";


  const selectedDescription =
    selectedResource
      ? (
          isArabic
            ? selectedResource.description_ar
            : selectedResource.description_fr
        )
      : "";


  const selectedContent =
    selectedResource
      ? (
          isArabic
            ? selectedResource.content_ar
            : selectedResource.content_fr
        )
      : "";


  const selectedPoints =
    selectedResource
      ? (
          isArabic
            ? selectedResource.points_ar
            : selectedResource.points_fr
        )
      : [];


  const selectedTone =
    selectedResource
      ? (
          selectedResource.tone
          || CATEGORY_TONE[
            selectedResource.category
          ]
          || "purple"
        )
      : "purple";


  const selectedIcon =
    selectedResource
      ? (
          selectedResource.icon
          || CATEGORY_ICON[
            selectedResource.category
          ]
          || "book"
        )
      : "book";


  /* ======================================================
     MODAL SCROLL / ESCAPE
  ====================================================== */

  useEffect(
    () => {
      if (
        !selectedResource
      ) {
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
            event.key
            === "Escape"
          ) {
            setSelectedResource(
              null
            );
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
      selectedResource,
    ]
  );


  /* ======================================================
     LOADING
  ====================================================== */

  if (loading) {
    return (
      <div
        className="resources-page"
        dir={
          isArabic
            ? "rtl"
            : "ltr"
        }
      >
        <section className="resources-loading-state">
          <span className="resources-loading-spinner" />

          <h3>
            {labels.loading}
          </h3>
        </section>
      </div>
    );
  }


  return (
    <motion.div
      className="resources-page"
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
          ERROR
      ================================================= */}

      {error ? (
        <section className="resources-empty resources-error-state">
          <span>
            <ResourceIcon
              name="alert"
              size={30}
            />
          </span>


          <h3>
            {error}
          </h3>


          <button
            type="button"
            onClick={
              loadData
            }
          >
            {labels.retry}
          </button>
        </section>
      ) : (
        <>
          {/* =================================================
              HERO
          ================================================= */}

          <section className="resources-hero">
            <div className="resources-hero-copy">
              <span className="resources-eyebrow">
                <ResourceIcon
                  name="book"
                  size={17}
                />

                {labels.eyebrow}
              </span>


              <h1>
                {labels.title}
              </h1>


              <p>
                {labels.subtitle}
              </p>
            </div>


            <div className="resources-hero-visual">
              <div className="resources-book-stack">
                <span className="book-back" />
                <span className="book-middle" />

                <span className="book-front">
                  <ResourceIcon
                    name="shield"
                    size={36}
                  />
                </span>
              </div>


              <span className="resource-orbit resource-orbit-one" />
              <span className="resource-orbit resource-orbit-two" />

              <span className="resource-dot resource-dot-one" />
              <span className="resource-dot resource-dot-two" />
              <span className="resource-dot resource-dot-three" />
            </div>
          </section>


          {/* =================================================
              EMPTY
          ================================================= */}

          {resources.length === 0 ? (
            <>
              <section className="resources-section">
                <div className="resources-empty">
                  <span>
                    <ResourceIcon
                      name="book"
                      size={31}
                    />
                  </span>


                  <h3>
                    {labels.noResources}
                  </h3>


                  <p className="resources-empty-description">
                    {labels.noResourcesText}
                  </p>


                  <button
                    type="button"
                    onClick={
                      loadData
                    }
                  >
                    {labels.retry}
                  </button>
                </div>
              </section>


              <AssistantCallToAction
                labels={labels}
                navigate={navigate}
                reducedMotion={
                  reducedMotion
                }
              />
            </>
          ) : (
            <>
              {/* =================================================
                  SEARCH
              ================================================= */}

              <section className="resources-search-section">
                <div className="resources-search">
                  <ResourceIcon
                    name="search"
                    size={21}
                  />


                  <input
                    type="search"
                    value={search}
                    placeholder={
                      labels.search
                    }
                    aria-label={
                      labels.search
                    }
                    onChange={
                      (event) =>
                        setSearch(
                          event.target.value
                        )
                    }
                  />


                  {search && (
                    <button
                      type="button"
                      aria-label={
                        labels.clear
                      }
                      onClick={() =>
                        setSearch("")
                      }
                    >
                      <ResourceIcon
                        name="close"
                        size={17}
                      />
                    </button>
                  )}
                </div>


                <div className="resources-filters">
                  {availableCategories.map(
                    (item) => (
                      <button
                        type="button"
                        key={item}
                        className={
                          category === item
                            ? "resource-filter active"
                            : "resource-filter"
                        }
                        onClick={() =>
                          setCategory(
                            item
                          )
                        }
                      >
                        {item === "all"
                          ? labels.all
                          : (
                              labels.categories[
                                item
                              ]
                              || item
                            )}
                      </button>
                    )
                  )}
                </div>
              </section>


              {/* =================================================
                  RECOMMENDED
              ================================================= */}

              {category === "all"
                && !search
                && recommendedResources.length > 0
                && (
                  <section className="resources-section">
                    <div className="resources-section-heading">
                      <div>
                        <span className="resources-section-icon purple">
                          <ResourceIcon
                            name="spark"
                            size={18}
                          />
                        </span>


                        <div>
                          <h2>
                            {labels.recommended}
                          </h2>


                          {activeIntent && (
                            <p>
                              {labels.currentSituation}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>


                    <div className="resources-grid resources-grid-featured">
                      {recommendedResources.map(
                        (
                          resource,
                          index
                        ) => (
                          <ResourceCard
                            key={
                              resource.id
                            }
                            resource={
                              resource
                            }
                            language={
                              language
                            }
                            labels={
                              labels
                            }
                            recommended
                            index={
                              index
                            }
                            onOpen={
                              setSelectedResource
                            }
                          />
                        )
                      )}
                    </div>
                  </section>
                )}


              {/* =================================================
                  ALL RESOURCES
              ================================================= */}

              <section className="resources-section">
                <div className="resources-section-heading">
                  <div>
                    <span className="resources-section-icon blue">
                      <ResourceIcon
                        name="book"
                        size={18}
                      />
                    </span>


                    <h2>
                      {labels.allResources}
                    </h2>
                  </div>


                  <span className="resources-count">
                    {filteredResources.length}
                  </span>
                </div>


                {filteredResources.length > 0 ? (
                  <div className="resources-grid">
                    {filteredResources.map(
                      (
                        resource,
                        index
                      ) => (
                        <ResourceCard
                          key={
                            resource.id
                          }
                          resource={
                            resource
                          }
                          language={
                            language
                          }
                          labels={
                            labels
                          }
                          index={
                            index
                          }
                          onOpen={
                            setSelectedResource
                          }
                        />
                      )
                    )}
                  </div>
                ) : (
                  <div className="resources-empty">
                    <span>
                      <ResourceIcon
                        name="search"
                        size={30}
                      />
                    </span>


                    <h3>
                      {labels.noResult}
                    </h3>


                    <button
                      type="button"
                      onClick={() => {
                        setSearch("");
                        setCategory(
                          "all"
                        );
                      }}
                    >
                      {labels.clear}
                    </button>
                  </div>
                )}
              </section>


              <AssistantCallToAction
                labels={labels}
                navigate={navigate}
                reducedMotion={
                  reducedMotion
                }
              />
            </>
          )}
        </>
      )}


      {/* =================================================
          MODAL CENTRÉE
      ================================================= */}

      <AnimatePresence>
        {selectedResource && (
          <motion.div
            className="resource-modal-layer"
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
              className="resource-modal-backdrop"
              aria-label={
                labels.close
              }
              onClick={() =>
                setSelectedResource(
                  null
                )
              }
            />


            <motion.section
              className="resource-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="resource-modal-title"
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
              <button
                type="button"
                className="resource-modal-close"
                aria-label={
                  labels.close
                }
                onClick={() =>
                  setSelectedResource(
                    null
                  )
                }
              >
                <ResourceIcon
                  name="close"
                  size={19}
                />
              </button>


              <span
                className={
                  `resource-modal-icon resource-tone-${selectedTone}`
                }
              >
                <ResourceIcon
                  name={
                    selectedIcon
                  }
                  size={28}
                />
              </span>


              <span className="resource-modal-category">
                {
                  labels.categories[
                    selectedResource.category
                  ]
                  || selectedResource.category
                }
              </span>


              <h2 id="resource-modal-title">
                {selectedTitle}
              </h2>


              <p className="resource-modal-description">
                {selectedDescription}
              </p>


              {selectedContent && (
                <div className="resource-modal-content">
                  {selectedContent}
                </div>
              )}


              {Array.isArray(
                selectedPoints
              )
                && selectedPoints.length > 0
                && (
                  <div className="resource-modal-points">
                    <h3>
                      {labels.useful}
                    </h3>


                    <ul>
                      {selectedPoints.map(
                        (
                          point,
                          index
                        ) => (
                          <li
                            key={
                              `${selectedResource.id}-${index}`
                            }
                          >
                            <span>
                              ✓
                            </span>


                            <p>
                              {point}
                            </p>
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}


              <div className="resource-modal-footer">
                <span>
                  <ResourceIcon
                    name="book"
                    size={16}
                  />

                  {labels.resource}
                </span>


                <button
                  type="button"
                  onClick={() =>
                    setSelectedResource(
                      null
                    )
                  }
                >
                  {labels.close}
                </button>
              </div>
            </motion.section>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}


export default Resources;