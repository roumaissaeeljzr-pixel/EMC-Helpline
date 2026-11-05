import { containsArabic } from "../../utils/language.js";
import { useLanguage } from "../../context/LanguageContext.jsx";

function AssessmentForm({
  description,
  onDescriptionChange,
  onSubmit,
  status,
}) {
  const { language, t } = useLanguage();

  const interfaceDir = language === "ar" ? "rtl" : "ltr";
  const isDescriptionArabic = containsArabic(description);
  const isLoading = status === "loading";
  const isSubmitDisabled = !description.trim() || isLoading;

  const handleKeyDown = (event) => {
    // Ctrl/Cmd + Entrée : soumission rapide sans empêcher
    // la saisie multi-lignes normale dans le textarea.
    if (
      event.key === "Enter"
      && (event.ctrlKey || event.metaKey)
    ) {
      event.preventDefault();

      if (!isSubmitDisabled) {
        onSubmit();
      }
    }
  };

  return (
    <div className="assessment-card" dir={interfaceDir}>
      <h2 className="assessment-title">
        {t("assessment.title")}
      </h2>

      <p className="assessment-intro">
        {t("assessment.intro")}
      </p>

      <label
        className="assessment-field-label"
        htmlFor="assessment-description"
      >
        {t("assessment.descriptionLabel")}
      </label>

      <textarea
        id="assessment-description"
        className="assessment-textarea"
        value={description}
        onChange={(event) =>
          onDescriptionChange(event.target.value)
        }
        onKeyDown={handleKeyDown}
        placeholder={t("assessment.placeholder")}
        rows="6"
        dir={isDescriptionArabic ? "rtl" : "ltr"}
        disabled={isLoading}
        aria-busy={isLoading}
      />

      <div className="assessment-actions">
        <button
          type="button"
          className="assessment-button-primary"
          disabled={isSubmitDisabled}
          onClick={onSubmit}
        >
          {isLoading
            ? t("assessment.loading")
            : t("assessment.submit")}
        </button>
      </div>

      {isLoading && (
        <p
          className="assessment-note"
          aria-live="polite"
        >
          {t("assessment.loading")}
        </p>
      )}

      {status === "error" && (
        <p
          className="assessment-error-note"
          role="alert"
        >
          {t("assessment.error")}
        </p>
      )}
    </div>
  );
}

export default AssessmentForm;