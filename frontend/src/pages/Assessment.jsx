import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AssessmentForm from "../components/assessment/AssessmentForm.jsx";
import AssessmentResult from "../components/assessment/AssessmentResult.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";
import "../components/assessment/Assessment.css";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

const ASSESSMENT_API_URL = `${API_BASE_URL}/assessment`;
const CASES_API_URL = `${API_BASE_URL}/cases`;
const ACTION_PLAN_ROUTE = "/victim/action-plan";

function readCookie(name) {
  const prefix = `${name}=`;
  const raw = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(prefix));

  return raw ? decodeURIComponent(raw.slice(prefix.length)) : null;
}

function Assessment() {
  const { language } = useLanguage();
  const navigate = useNavigate();

  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("idle");
  const [result, setResult] = useState(null);
  const [createdCase, setCreatedCase] = useState(null);
  const [ageAtTimeOfFacts, setAgeAtTimeOfFacts] = useState(null);
  const [actionPlanStatus, setActionPlanStatus] = useState("idle");
  const [actionPlanError, setActionPlanError] = useState("");

  const interfaceLanguage = language === "ar" ? "ar" : "fr";
  const interfaceDir = interfaceLanguage === "ar" ? "rtl" : "ltr";

  const getCsrfToken = () => {
    const csrfToken = readCookie("csrf_token");

    if (!csrfToken) {
      throw new Error(
        interfaceLanguage === "ar"
          ? "رمز الحماية غير موجود. يرجى تسجيل الدخول من جديد."
          : "Jeton CSRF introuvable. Veuillez vous reconnecter."
      );
    }

    return csrfToken;
  };

  const createCase = async (cleanDescription) => {
    const response = await fetch(CASES_API_URL, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": getCsrfToken(),
      },
      body: JSON.stringify({ description: cleanDescription }),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      throw new Error(
        typeof data?.detail === "string"
          ? data.detail
          : "Impossible d'enregistrer le dossier."
      );
    }

    return data;
  };

  const handleSubmit = async () => {
    const cleanDescription = description.trim();

    if (!cleanDescription || status === "loading") {
      return;
    }

    setStatus("loading");
    setResult(null);
    setCreatedCase(null);
    setAgeAtTimeOfFacts(null);
    setActionPlanStatus("idle");
    setActionPlanError("");

    try {
      const response = await fetch(ASSESSMENT_API_URL, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: cleanDescription,
          interface_language: interfaceLanguage,
        }),
      });

      if (!response.ok) {
        throw new Error(`Erreur API /assessment (${response.status})`);
      }

      const data = await response.json();
      setResult(data);
      setStatus("success");

      try {
        const caseData = await createCase(cleanDescription);
        setCreatedCase(caseData);
      } catch (caseError) {
        console.error("Erreur lors de l'enregistrement du dossier :", caseError);
        setActionPlanError(
          interfaceLanguage === "ar"
            ? "تم تقييم الحالة، لكن تعذر حفظ الملف."
            : "La situation a été évaluée, mais le dossier n'a pas pu être enregistré."
        );
      }
    } catch (error) {
      console.error("Erreur lors de l'évaluation de la situation :", error);
      setStatus("error");
    }
  };

  const handleAgeAnswer = (ageStatus) => {
    if (ageStatus !== "minor" && ageStatus !== "adult") {
      return;
    }

    setAgeAtTimeOfFacts(ageStatus);
    setActionPlanError("");
  };

  const handleViewActionPlan = async () => {
    if (!result || actionPlanStatus === "loading") {
      return;
    }

    if (
      result.clarification_required &&
      result.clarification_type === "age_at_time_of_facts" &&
      !ageAtTimeOfFacts
    ) {
      return;
    }

    if (!createdCase?.id) {
      setActionPlanStatus("error");
      setActionPlanError(
        interfaceLanguage === "ar"
          ? "تعذر إنشاء خطة العمل لأن الملف لم يُحفظ."
          : "Impossible de créer le plan d'action car le dossier n'a pas été enregistré."
      );
      return;
    }

    setActionPlanStatus("loading");
    setActionPlanError("");

    try {
      const response = await fetch(
        `${CASES_API_URL}/${createdCase.id}/action-plan`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": getCsrfToken(),
          },
          body: JSON.stringify({
            age_at_time_of_facts: ageAtTimeOfFacts,
          }),
        }
      );

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          typeof data?.detail === "string"
            ? data.detail
            : `Erreur API (${response.status})`
        );
      }

      if (!Array.isArray(data?.actions) || data.actions.length === 0) {
        throw new Error("Plan d'action vide.");
      }

      navigate(ACTION_PLAN_ROUTE, {
        state: {
          actionPlan: data,
          caseId: createdCase.id,
        },
      });
    } catch (error) {
      console.error("Erreur lors de la création persistante du plan d'action :", error);
      setActionPlanStatus("error");
      setActionPlanError(
        interfaceLanguage === "ar"
          ? "تعذر إنشاء خطة العمل حاليًا. يرجى المحاولة مرة أخرى."
          : "Impossible de construire le plan d'action pour le moment. Veuillez réessayer."
      );
      return;
    }

    setActionPlanStatus("idle");
  };

  const restart = () => {
    setDescription("");
    setResult(null);
    setCreatedCase(null);
    setAgeAtTimeOfFacts(null);
    setActionPlanStatus("idle");
    setActionPlanError("");
    setStatus("idle");
  };

  return (
    <div
      className="assessment-page"
      lang={interfaceLanguage}
      dir={interfaceDir}
    >
      <div className="assessment-container">
        {status === "success" && result ? (
          <AssessmentResult
            result={result}
            onRestart={restart}
            ageAtTimeOfFacts={ageAtTimeOfFacts}
            onAgeAnswer={handleAgeAnswer}
            onViewActionPlan={handleViewActionPlan}
            actionPlanStatus={actionPlanStatus}
            actionPlanError={actionPlanError}
          />
        ) : (
          <AssessmentForm
            description={description}
            onDescriptionChange={setDescription}
            onSubmit={handleSubmit}
            status={status}
          />
        )}
      </div>
    </div>
  );
}

export default Assessment;