import { useLanguage } from "../../context/LanguageContext.jsx";

const ARABIC_INTENT_LABELS = {
  "Cyberharcèlement": "التحرش الإلكتروني",
  "Sextorsion": "الابتزاز الجنسي",
  "Piratage de compte": "اختراق الحساب",
  "Divulgation de données personnelles (Doxing)":
    "الكشف عن البيانات الشخصية",
  "Conservation des preuves": "الاحتفاظ بالأدلة",
  "Informations juridiques": "معلومات قانونية",
  "Usurpation d'identité": "انتحال الهوية",
  "Diffusion non consentie d'images":
    "نشر الصور دون موافقة",
  "Signalement": "الإبلاغ",
  "Situation d'urgence": "حالة طارئة",
  "Accompagnement de la victime": "مرافقة الضحية",
};

function getDisplayedIntent(
  canonicalIntent,
  interfaceLanguage,
) {
  if (!canonicalIntent) {
    return "";
  }

  if (interfaceLanguage === "ar") {
    return (
      ARABIC_INTENT_LABELS[canonicalIntent]
      || canonicalIntent
    );
  }

  return canonicalIntent;
}

function AssessmentResult({
  result,
  onRestart,
  ageAtTimeOfFacts,
  onAgeAnswer,
  onViewActionPlan,
  actionPlanStatus = "idle",
  actionPlanError = "",
}) {
  const { language, t } = useLanguage();

  const interfaceLanguage =
    language === "ar" ? "ar" : "fr";

  const interfaceDir =
    interfaceLanguage === "ar" ? "rtl" : "ltr";

  const {
    detected_text_language: detectedLanguage,
    detected_intent: detectedIntent,
    clarification_required: clarificationRequired,
    clarification_type: clarificationType,
    emergency_override: emergencyOverride,
  } = result;

  const displayedIntent = getDisplayedIntent(
    detectedIntent,
    interfaceLanguage,
  );

  const languageName =
    detectedLanguage === "ar"
      ? t("assessment.result.languageNameAr")
      : t("assessment.result.languageNameFr");

  const isAgeClarification =
    clarificationRequired
    && clarificationType
      === "age_at_time_of_facts";

  const ageClarificationResolved =
    isAgeClarification
    && Boolean(ageAtTimeOfFacts);

  const effectiveClarificationRequired =
    clarificationRequired
    && !ageClarificationResolved;

  const isActionPlanLoading =
    actionPlanStatus === "loading";

  const canViewActionPlan =
    Boolean(detectedIntent)
    && !effectiveClarificationRequired
    && !emergencyOverride
    && typeof onViewActionPlan === "function";

  const actionPlanLabel =
    interfaceLanguage === "ar"
      ? "عرض خطة العمل"
      : "Voir mon plan d'action";

  const actionPlanLoadingLabel =
    interfaceLanguage === "ar"
      ? "جارٍ إنشاء خطة العمل..."
      : "Création du plan...";

  const minorLabel =
    interfaceLanguage === "ar"
      ? "كنت قاصرًا/قاصرة"
      : "J'étais mineur(e)";

  const adultLabel =
    interfaceLanguage === "ar"
      ? "كنت بالغًا/بالغة"
      : "J'étais majeur(e)";

  const ageConfirmedLabel =
    interfaceLanguage === "ar"
      ? (
          ageAtTimeOfFacts === "minor"
            ? "تم تحديد الحالة: قاصر وقت الوقائع."
            : "تم تحديد الحالة: بالغ وقت الوقائع."
        )
      : (
          ageAtTimeOfFacts === "minor"
            ? "Âge renseigné : mineur(e) au moment des faits."
            : "Âge renseigné : majeur(e) au moment des faits."
        );

  return (
    <div
      className="assessment-card"
      dir={interfaceDir}
    >
      <h2 className="assessment-title">
        {t("assessment.result.title")}
      </h2>

      {emergencyOverride && (
        <div
          className="assessment-emergency-note"
          role="alert"
        >
          <strong>
            {t("assessment.emergency.title")}
          </strong>

          <p>
            {t("assessment.emergency.message")}
          </p>
        </div>
      )}

      {detectedIntent && (
        <div className="assessment-summary-block">
          <span className="assessment-field-label">
            {t(
              "assessment.result.situationDetected"
            )}
          </span>

          <p
            className="assessment-summary-description"
            dir={interfaceDir}
          >
            {displayedIntent}
          </p>
        </div>
      )}

      {detectedLanguage && (
        <p className="assessment-note">
          {t(
            "assessment.result.languageDetected",
            { language: languageName },
          )}
        </p>
      )}

      {isAgeClarification && !ageAtTimeOfFacts && (
        <div className="assessment-clarification-note">
          <strong>
            {t("assessment.clarification.title")}
          </strong>

          <p>
            {t(
              "assessment.clarification.ageQuestion"
            )}
          </p>

          <div className="assessment-choice-group">
            <button
              type="button"
              className="assessment-choice"
              onClick={() => onAgeAnswer?.("minor")}
            >
              {minorLabel}
            </button>

            <button
              type="button"
              className="assessment-choice"
              onClick={() => onAgeAnswer?.("adult")}
            >
              {adultLabel}
            </button>
          </div>
        </div>
      )}

      {isAgeClarification && ageAtTimeOfFacts && (
        <div className="assessment-clarification-note">
          <strong>
            {t("assessment.clarification.title")}
          </strong>

          <p>{ageConfirmedLabel}</p>

          <div className="assessment-choice-group">
            <button
              type="button"
              className={
                ageAtTimeOfFacts === "minor"
                  ? (
                      "assessment-choice "
                      + "assessment-choice-selected"
                    )
                  : "assessment-choice"
              }
              onClick={() => onAgeAnswer?.("minor")}
            >
              {minorLabel}
            </button>

            <button
              type="button"
              className={
                ageAtTimeOfFacts === "adult"
                  ? (
                      "assessment-choice "
                      + "assessment-choice-selected"
                    )
                  : "assessment-choice"
              }
              onClick={() => onAgeAnswer?.("adult")}
            >
              {adultLabel}
            </button>
          </div>
        </div>
      )}

      {clarificationRequired
        && !isAgeClarification && (
          <div className="assessment-clarification-note">
            <strong>
              {t("assessment.clarification.title")}
            </strong>

            <p>
              {t(
                "assessment.clarification.generic"
              )}
            </p>
          </div>
        )}

      {actionPlanError && (
        <p
          className="assessment-error-note"
          role="alert"
        >
          {actionPlanError}
        </p>
      )}

      <div
        className={
          canViewActionPlan
            ? (
                "assessment-actions "
                + "assessment-actions-split"
              )
            : "assessment-actions"
        }
      >
        <button
          type="button"
          className="assessment-button-secondary"
          onClick={onRestart}
          disabled={isActionPlanLoading}
        >
          {t(
            "assessment.result.newEvaluation"
          )}
        </button>

        {canViewActionPlan && (
          <button
            type="button"
            className="assessment-button-primary"
            onClick={onViewActionPlan}
            disabled={isActionPlanLoading}
            aria-busy={isActionPlanLoading}
          >
            {isActionPlanLoading
              ? actionPlanLoadingLabel
              : actionPlanLabel}
          </button>
        )}
      </div>
    </div>
  );
}

export default AssessmentResult;