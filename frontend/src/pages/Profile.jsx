import {
  useEffect,
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
  DashboardIcon,
} from "../components/dashboard/DashboardComponents.jsx";

import "./Dashboard.css";
import "./Profile.css";


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


const COPY = {
  fr: {
    kicker:
      "Espace personnel sécurisé",

    title:
      "Informations personnelles",

    intro:
      "Renseignez votre identité une seule fois. Elle permettra à l’équipe EMC d’identifier correctement la personne associée à vos dossiers.",

    requiredTitle:
      "Complétez votre profil pour continuer",

    requiredIntro:
      "Ces informations obligatoires doivent être renseignées avant d’accéder aux autres fonctionnalités de votre espace victime.",

    identityCard:
      "Identité de la victime",

    identityCardText:
      "Ces informations restent liées à votre compte et ne sont pas ressaisies à chaque dossier.",

    emcId:
      "Identifiant EMC",

    status:
      "État de l’identité",

    complete:
      "Identité renseignée",

    incomplete:
      "À compléter",

    account:
      "Compte",

    active:
      "Actif",

    firstName:
      "Prénom",

    lastName:
      "Nom",

    birthDate:
      "Date de naissance",

    cin:
      "CIN",

    phone:
      "Téléphone",

    username:
      "Nom d’utilisateur",

    email:
      "E-mail",

    save:
      "Enregistrer mes informations",

    saving:
      "Enregistrement...",

    saved:
      "Vos informations ont été enregistrées.",

    error:
      "Impossible d’enregistrer vos informations.",

    loading:
      "Chargement de votre profil...",

    retry:
      "Réessayer",

    privacyTitle:
      "Protection de votre identité",

    privacyText:
      "Votre CIN est chiffrée avant son stockage. Elle n’est jamais ajoutée aux logs ni exposée dans les listes publiques de dossiers.",

    clarification:
      "Le statut « Identité renseignée » signifie que les champs sont complétés. Il ne constitue pas une vérification officielle de la CIN.",

    cinPlaceholder:
      "Ex. AB123456",

    phonePlaceholder:
      "Ex. 0612345678",

    required:
      "Tous les champs avec * sont obligatoires.",

    allFieldsRequired:
      "Veuillez remplir tous les champs obligatoires avant d’enregistrer.",
  },

  ar: {
    kicker:
      "مساحة شخصية آمنة",

    title:
      "المعلومات الشخصية",

    intro:
      "أدخل بيانات هويتك مرة واحدة فقط. ستساعد هذه المعلومات فريق EMC على تحديد الشخص المرتبط بالملفات بشكل صحيح.",

    requiredTitle:
      "أكمل ملفك الشخصي للمتابعة",

    requiredIntro:
      "يجب إدخال هذه المعلومات الإلزامية قبل الوصول إلى باقي وظائف مساحة الضحية.",

    identityCard:
      "هوية الضحية",

    identityCardText:
      "ترتبط هذه المعلومات بحسابك ولا تحتاج إلى إدخالها من جديد عند إنشاء كل ملف.",

    emcId:
      "معرف EMC",

    status:
      "حالة الهوية",

    complete:
      "الهوية مكتملة",

    incomplete:
      "تحتاج إلى الاستكمال",

    account:
      "الحساب",

    active:
      "نشط",

    firstName:
      "الاسم الشخصي",

    lastName:
      "الاسم العائلي",

    birthDate:
      "تاريخ الميلاد",

    cin:
      "رقم البطاقة الوطنية",

    phone:
      "الهاتف",

    username:
      "اسم المستخدم",

    email:
      "البريد الإلكتروني",

    save:
      "حفظ معلوماتي",

    saving:
      "جارٍ الحفظ...",

    saved:
      "تم حفظ معلوماتك.",

    error:
      "تعذر حفظ معلوماتك.",

    loading:
      "جارٍ تحميل الملف الشخصي...",

    retry:
      "إعادة المحاولة",

    privacyTitle:
      "حماية هويتك",

    privacyText:
      "يتم تشفير رقم البطاقة الوطنية قبل تخزينه، ولا تتم إضافته إلى السجلات أو عرضه في القوائم العامة للملفات.",

    clarification:
      "حالة «الهوية مكتملة» تعني أن الحقول تم ملؤها، ولا تعني التحقق الرسمي من البطاقة الوطنية.",

    cinPlaceholder:
      "مثال AB123456",

    phonePlaceholder:
      "مثال 0612345678",

    required:
      "جميع الحقول التي تحمل * إلزامية.",

    allFieldsRequired:
      "يرجى ملء جميع الحقول الإلزامية قبل الحفظ.",
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


function Profile() {
  const navigate =
    useNavigate();

  const {
    language,
  } = useLanguage();

  const {
    refreshVictimProfile,
  } = useAuth();

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
    profile,
    setProfile,
  ] = useState(null);

  const [
    form,
    setForm,
  ] = useState({
    first_name: "",
    last_name: "",
    date_of_birth: "",
    phone: "",
    cin: "",
  });

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    status,
    setStatus,
  ] = useState("idle");

  const [
    message,
    setMessage,
  ] = useState("");


  const loadProfile =
    async () => {
      setLoading(true);
      setMessage("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/profile/me`,
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
              : labels.error
          );
        }

        setProfile(
          data
        );

        setForm({
          first_name:
            data.first_name
            || "",

          last_name:
            data.last_name
            || "",

          date_of_birth:
            data.date_of_birth
            || "",

          phone:
            data.phone
            || "",

          cin:
            data.cin
            || "",
        });
      } catch (error) {
        setMessage(
          error.message
          || labels.error
        );
      } finally {
        setLoading(false);
      }
    };


  useEffect(
    () => {
      loadProfile();
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );


  const updateField =
    (
      field,
      value
    ) => {
      setForm(
        (current) => ({
          ...current,
          [field]:
            value,
        })
      );

      if (
        status !== "idle"
      ) {
        setStatus(
          "idle"
        );

        setMessage("");
      }
    };


  const isFormComplete =
    Boolean(
      form.first_name.trim()
      && form.last_name.trim()
      && form.date_of_birth
      && form.phone.trim()
      && form.cin.trim()
    );


  const handleSubmit =
    async (
      event
    ) => {
      event.preventDefault();

      if (
        status
        === "saving"
      ) {
        return;
      }

      if (!isFormComplete) {
        setStatus(
          "error"
        );

        setMessage(
          labels.allFieldsRequired
        );

        return;
      }

      const csrfToken =
        readCookie(
          "csrf_token"
        );

      if (!csrfToken) {
        setStatus(
          "error"
        );

        setMessage(
          labels.error
        );

        return;
      }

      setStatus(
        "saving"
      );

      setMessage("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/profile/me`,
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
                  first_name:
                    form.first_name.trim()
                    || null,

                  last_name:
                    form.last_name.trim()
                    || null,

                  date_of_birth:
                    form.date_of_birth
                    || null,

                  phone:
                    form.phone.trim()
                    || null,

                  cin:
                    form.cin.trim()
                    || null,
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
          let detail =
            data?.detail;

          if (
            Array.isArray(
              detail
            )
          ) {
            detail =
              detail
                .map(
                  (item) =>
                    item?.msg
                )
                .filter(
                  Boolean
                )
                .join(" ");
          }

          throw new Error(
            typeof detail
              === "string"
              ? detail
              : labels.error
          );
        }

        const wasIncomplete =
          !profile?.identity_complete;

        setProfile(
          data
        );

        setForm({
          first_name:
            data.first_name
            || "",

          last_name:
            data.last_name
            || "",

          date_of_birth:
            data.date_of_birth
            || "",

          phone:
            data.phone
            || "",

          cin:
            data.cin
            || "",
        });

        setStatus(
          "success"
        );

        setMessage(
          labels.saved
        );

        await refreshVictimProfile();

        if (
          wasIncomplete
          && data.identity_complete
        ) {
          navigate(
            "/victim/dashboard",
            {
              replace: true,
            }
          );
        }
      } catch (error) {
        setStatus(
          "error"
        );

        setMessage(
          error.message
          || labels.error
        );
      }
    };


  if (loading) {
    return (
      <div className="guided-dashboard victim-profile-page">
        <section className="victim-profile-loading">
          <span className="victim-profile-spinner" />

          <h2>
            {labels.loading}
          </h2>
        </section>
      </div>
    );
  }


  return (
    <motion.div
      key={language}
      className="guided-dashboard victim-profile-page"
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
      {profile && !profile.identity_complete && (
        <section className="victim-profile-required-banner">
          <strong>
            {labels.requiredTitle}
          </strong>

          <p>
            {labels.requiredIntro}
          </p>
        </section>
      )}

      <section className="victim-profile-heading">
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


      {profile && (
        <section className="victim-profile-summary-grid">
          <article className="victim-profile-summary tone-purple">
            <span>
              <DashboardIcon
                name="shield"
                size={24}
              />
            </span>

            <div>
              <small>
                {labels.emcId}
              </small>

              <strong>
                {profile.emc_id}
              </strong>
            </div>
          </article>


          <article
            className={
              `victim-profile-summary ${
                profile.identity_complete
                  ? "tone-green"
                  : "tone-orange"
              }`
            }
          >
            <span>
              <DashboardIcon
                name={
                  profile.identity_complete
                    ? "check"
                    : "alert"
                }
                size={24}
              />
            </span>

            <div>
              <small>
                {labels.status}
              </small>

              <strong>
                {profile.identity_complete
                  ? labels.complete
                  : labels.incomplete}
              </strong>
            </div>
          </article>


          <article className="victim-profile-summary tone-blue">
            <span>
              <DashboardIcon
                name="folder"
                size={24}
              />
            </span>

            <div>
              <small>
                {labels.account}
              </small>

              <strong>
                {labels.active}
              </strong>
            </div>
          </article>
        </section>
      )}


      <div className="victim-profile-grid">
        <section className="guided-section victim-profile-form-card">
          <div className="victim-profile-section-heading">
            <div>
              <h2>
                {labels.identityCard}
              </h2>

              <p>
                {labels.identityCardText}
              </p>
            </div>
          </div>


          <form
            onSubmit={
              handleSubmit
            }
            className="victim-profile-form"
          >
            <div className="victim-profile-fields">
              <label>
                <span>
                  {labels.firstName} *
                </span>

                <input
                  type="text"
                  value={
                    form.first_name
                  }
                  onChange={
                    (event) =>
                      updateField(
                        "first_name",
                        event.target.value
                      )
                  }
                  autoComplete="given-name"
                  required
                />
              </label>


              <label>
                <span>
                  {labels.lastName} *
                </span>

                <input
                  type="text"
                  value={
                    form.last_name
                  }
                  onChange={
                    (event) =>
                      updateField(
                        "last_name",
                        event.target.value
                      )
                  }
                  autoComplete="family-name"
                  required
                />
              </label>


              <label>
                <span>
                  {labels.birthDate} *
                </span>

                <input
                  type="date"
                  value={
                    form.date_of_birth
                  }
                  onChange={
                    (event) =>
                      updateField(
                        "date_of_birth",
                        event.target.value
                      )
                  }
                  autoComplete="bday"
                  required
                />
              </label>


              <label>
                <span>
                  {labels.phone} *
                </span>

                <input
                  type="tel"
                  value={
                    form.phone
                  }
                  onChange={
                    (event) =>
                      updateField(
                        "phone",
                        event.target.value
                      )
                  }
                  placeholder={
                    labels.phonePlaceholder
                  }
                  autoComplete="tel"
                  dir="ltr"
                  required
                />
              </label>


              <label className="victim-profile-field-wide">
                <span>
                  {labels.cin} *
                </span>

                <input
                  type="text"
                  value={
                    form.cin
                  }
                  onChange={
                    (event) =>
                      updateField(
                        "cin",
                        event.target.value
                      )
                  }
                  placeholder={
                    labels.cinPlaceholder
                  }
                  autoComplete="off"
                  dir="ltr"
                  required
                />
              </label>


              <label>
                <span>
                  {labels.username}
                </span>

                <input
                  type="text"
                  value={
                    profile?.username
                    || ""
                  }
                  readOnly
                  disabled
                />
              </label>


              <label>
                <span>
                  {labels.email}
                </span>

                <input
                  type="email"
                  value={
                    profile?.email
                    || ""
                  }
                  readOnly
                  disabled
                />
              </label>
            </div>


            <p className="victim-profile-required">
              {labels.required}
            </p>


            {message && (
              <div
                className={
                  `victim-profile-message ${
                    status === "success"
                      ? "success"
                      : "error"
                  }`
                }
              >
                {message}
              </div>
            )}


            <div className="victim-profile-actions">
              <button
                type="submit"
                disabled={
                  status === "saving"
                  || !isFormComplete
                }
              >
                {status === "saving"
                  ? labels.saving
                  : labels.save}
              </button>
            </div>
          </form>
        </section>


        <aside className="victim-profile-side">
          <section className="victim-profile-security-card">
            <span>
              <DashboardIcon
                name="lock"
                size={24}
              />
            </span>

            <div>
              <h2>
                {labels.privacyTitle}
              </h2>

              <p>
                {labels.privacyText}
              </p>
            </div>
          </section>


          <section className="victim-profile-info-card">
            <DashboardIcon
              name="shield"
              size={21}
            />

            <p>
              {labels.clarification}
            </p>
          </section>
        </aside>
      </div>
    </motion.div>
  );
}


export default Profile;
