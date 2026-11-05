import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext.jsx";
import "./ActionPlan.css";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

const LATEST_ACTION_PLAN_API_URL =
  `${API_BASE_URL}/action-plans/latest`;

const SELECTED_CASE_STORAGE_KEY =
  "emc_selected_case_id";

const ARABIC_INTENT_LABELS = {
  "Cyberharcèlement": "التحرش الإلكتروني",
  "Sextorsion": "الابتزاز الجنسي",
  "Piratage de compte": "اختراق الحساب",
  "Divulgation de données personnelles (Doxing)":
    "الكشف عن البيانات الشخصية",
  "Conservation des preuves": "الاحتفاظ بالأدلة",
  "Informations juridiques": "معلومات قانونية",
  "Usurpation d'identité": "انتحال الهوية",
  "Diffusion non consentie d'images": "نشر الصور دون موافقة",
  "Signalement": "الإبلاغ",
  "Situation d'urgence": "حالة طارئة",
  "Accompagnement de la victime": "مرافقة الضحية",
};

function readCookie(name) {
  const prefix = `${name}=`;
  const raw = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(prefix));

  return raw ? decodeURIComponent(raw.slice(prefix.length)) : null;
}

function ActionPlan() {
  const { language, t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const locationCaseId =
    location.state?.caseId
    || null;

  const storedCaseId =
    window.localStorage.getItem(
      SELECTED_CASE_STORAGE_KEY
    );

  const selectedCaseId =
    locationCaseId
    || storedCaseId
    || null;

  const interfaceLanguage = language === "ar" ? "ar" : "fr";
  const interfaceDir = interfaceLanguage === "ar" ? "rtl" : "ltr";

  const [actionPlan, setActionPlan] = useState(
    location.state?.actionPlan ?? null
  );

  const [loadStatus, setLoadStatus] = useState(
    location.state?.actionPlan ? "success" : "loading"
  );

  const [loadError, setLoadError] = useState("");
  const [updatingItems, setUpdatingItems] = useState({});

  useEffect(() => {
    if (!locationCaseId) {
      return;
    }

    window.localStorage.setItem(
      SELECTED_CASE_STORAGE_KEY,
      locationCaseId
    );
  }, [locationCaseId]);

  useEffect(() => {
    if (location.state?.actionPlan) {
      return;
    }

    let cancelled = false;

    const loadPlan = async () => {
      setLoadStatus("loading");
      setLoadError("");

      try {
        const endpoint =
          selectedCaseId
            ? `${API_BASE_URL}/cases/${selectedCaseId}/action-plan`
            : LATEST_ACTION_PLAN_API_URL;

        const response = await fetch(endpoint, {
          method: "GET",
          credentials: "include",
          headers: { Accept: "application/json" },
        });

        if (response.status === 404) {
          if (!cancelled) {
            setActionPlan(null);
            setLoadStatus("empty");
          }
          return;
        }

        const data = await response.json().catch(() => null);

        if (!response.ok) {
          throw new Error(
            typeof data?.detail === "string"
              ? data.detail
              : "Impossible de charger le plan d'action."
          );
        }

        if (!cancelled) {
          setActionPlan(data);
          setLoadStatus("success");
        }
      } catch (error) {
        console.error("Erreur lors du chargement du plan d'action :", error);

        if (!cancelled) {
          setLoadError(error.message);
          setLoadStatus("error");
        }
      }
    };

    loadPlan();

    return () => {
      cancelled = true;
    };
  }, [
    location.state,
    selectedCaseId,
  ]);

  const actions = Array.isArray(actionPlan?.actions)
    ? actionPlan.actions
    : [];

  const completedCount = useMemo(
    () => actions.filter((action) => Boolean(action.completed)).length,
    [actions]
  );

  const planLanguage = actionPlan?.language === "ar" ? "ar" : "fr";
  const planDir = planLanguage === "ar" ? "rtl" : "ltr";

  const displayedIntent = actionPlan?.detected_intent
    ? interfaceLanguage === "ar"
      ? ARABIC_INTENT_LABELS[actionPlan.detected_intent] ||
        actionPlan.detected_intent
      : actionPlan.detected_intent
    : "";

  const toggleAction = async (action) => {
    if (!action?.id || updatingItems[action.id]) {
      return;
    }

    const csrfToken = readCookie("csrf_token");

    if (!csrfToken) {
      setLoadError(
        interfaceLanguage === "ar"
          ? "انتهت الجلسة. يرجى تسجيل الدخول من جديد."
          : "Session expirée. Veuillez vous reconnecter."
      );
      return;
    }

    const nextCompleted = !Boolean(action.completed);

    setActionPlan((current) => ({
      ...current,
      actions: current.actions.map((item) =>
        item.id === action.id
          ? { ...item, completed: nextCompleted }
          : item
      ),
    }));

    setUpdatingItems((current) => ({
      ...current,
      [action.id]: true,
    }));

    try {
      const response = await fetch(
        `${API_BASE_URL}/action-items/${action.id}`,
        {
          method: "PATCH",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken,
          },
          body: JSON.stringify({ completed: nextCompleted }),
        }
      );

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          typeof data?.detail === "string"
            ? data.detail
            : "Impossible d'enregistrer la progression."
        );
      }

      setActionPlan((current) => ({
        ...current,
        actions: current.actions.map((item) =>
          item.id === action.id ? data : item
        ),
      }));

      setLoadError("");
    } catch (error) {
      console.error("Erreur lors de la mise à jour d'une action :", error);

      setActionPlan((current) => ({
        ...current,
        actions: current.actions.map((item) =>
          item.id === action.id
            ? { ...item, completed: !nextCompleted }
            : item
        ),
      }));

      setLoadError(error.message);
    } finally {
      setUpdatingItems((current) => ({
        ...current,
        [action.id]: false,
      }));
    }
  };

  const goToAssessment = () => {
    navigate("/victim/assessment");
  };

  if (loadStatus === "loading") {
    return (
      <div className="action-plan-page" lang={interfaceLanguage} dir={interfaceDir}>
        <div className="action-plan-container">
          <section className="action-plan-card">
            <h2 className="action-plan-title">{t("pages.actionPlan.title")}</h2>
            <div className="action-plan-empty">
              <p>
                {interfaceLanguage === "ar"
                  ? "جارٍ تحميل خطة العمل..."
                  : "Chargement du plan d'action..."}
              </p>
            </div>
          </section>
        </div>
      </div>
    );
  }

  if (!actionPlan || loadStatus === "empty" || loadStatus === "error") {
    return (
      <div className="action-plan-page" lang={interfaceLanguage} dir={interfaceDir}>
        <div className="action-plan-container">
          <section className="action-plan-card">
            <h2 className="action-plan-title">{t("pages.actionPlan.title")}</h2>

            {loadError && (
              <div role="alert" style={{ marginBottom: 14, color: "#8d3030" }}>
                {loadError}
              </div>
            )}

            <div className="action-plan-empty">
              <h3>
                {interfaceLanguage === "ar"
                  ? selectedCaseId
                    ? "لا توجد خطة عمل لهذا الملف"
                    : "لا توجد خطة عمل نشطة"
                  : selectedCaseId
                    ? "Aucun plan d'action pour ce dossier"
                    : "Aucun plan d'action actif"}
              </h3>

              <p>
                {interfaceLanguage === "ar"
                  ? selectedCaseId
                    ? "الملف المحدد لا يحتوي بعد على خطة عمل."
                    : "ابدأ أولًا بتقييم وضعيتك لإنشاء خطة عمل موثقة."
                  : selectedCaseId
                    ? "Le dossier sélectionné ne possède pas encore de plan d'action."
                    : "Commencez par évaluer votre situation pour construire un plan d'action documenté."}
              </p>

              <button
                type="button"
                className="action-plan-primary-button"
                onClick={goToAssessment}
              >
                {interfaceLanguage === "ar"
                  ? "تقييم وضعيتي"
                  : "Évaluer ma situation"}
              </button>
            </div>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="action-plan-page" lang={interfaceLanguage} dir={interfaceDir}>
      <div className="action-plan-container">
        <section className="action-plan-card">
          <header className="action-plan-header">
            <div>
              <h2 className="action-plan-title">{t("pages.actionPlan.title")}</h2>
              <p className="action-plan-intro">
                {t("pages.actionPlan.description")}
              </p>
            </div>

            <div className="action-plan-progress">
              <strong>{completedCount}/{actions.length}</strong>
              <span>
                {interfaceLanguage === "ar" ? "مكتمل" : "terminée(s)"}
              </span>
            </div>
          </header>

          {loadError && (
            <div
              role="alert"
              style={{
                marginBottom: 14,
                padding: "10px 12px",
                border: "1px solid #efc9c9",
                borderRadius: 10,
                background: "#fff7f7",
                color: "#8d3030",
                fontSize: 13,
              }}
            >
              {loadError}
            </div>
          )}

          {displayedIntent && (
            <div className="action-plan-intent">
              <span>
                {interfaceLanguage === "ar"
                  ? "الوضعية المكتشفة"
                  : "Situation détectée"}
              </span>
              <strong>{displayedIntent}</strong>
            </div>
          )}

          <div className="action-plan-list" dir={planDir}>
            {actions.map((action, index) => {
              const isCompleted = Boolean(action.completed);
              const isUpdating = Boolean(updatingItems[action.id]);

              return (
                <article
                  key={action.id}
                  className={
                    isCompleted
                      ? "action-plan-item action-plan-item-completed"
                      : "action-plan-item"
                  }
                >
                  <label className="action-plan-item-main">
                    <input
                      type="checkbox"
                      checked={isCompleted}
                      disabled={isUpdating}
                      onChange={() => toggleAction(action)}
                    />

                    <div>
                      <div className="action-plan-item-heading">
                        <span className="action-plan-step">{index + 1}</span>
                        <h3>{action.title}</h3>
                      </div>
                      <p>{action.description}</p>
                    </div>
                  </label>

                  <span className="action-plan-status">
                    {isUpdating
                      ? planLanguage === "ar"
                        ? "جارٍ الحفظ..."
                        : "Enregistrement..."
                      : isCompleted
                        ? planLanguage === "ar"
                          ? "مكتمل"
                          : "Terminé"
                        : planLanguage === "ar"
                          ? "للقيام به"
                          : "À faire"}
                  </span>
                </article>
              );
            })}
          </div>

          <p className="action-plan-note">
            {interfaceLanguage === "ar"
              ? "يتم حفظ تقدمك تلقائيًا في حسابك."
              : "Votre progression est enregistrée automatiquement dans votre compte."}
          </p>
        </section>
      </div>
    </div>
  );
}

export default ActionPlan;