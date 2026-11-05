import { createContext, useContext, useEffect, useState } from "react";
import { translations } from "../i18n/translations.js";

const STORAGE_KEY = "emc_language";
const DEFAULT_LANGUAGE = "fr";
const SUPPORTED_LANGUAGES = ["fr", "ar"];

const LanguageContext = createContext(null);

function getInitialLanguage() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);

    if (SUPPORTED_LANGUAGES.includes(stored)) {
      return stored;
    }
  } catch (error) {
    // localStorage indisponible (mode privé, etc.) : on retombe sur le défaut
  }

  return DEFAULT_LANGUAGE;
}

function resolvePath(path, language) {
  return path
    .split(".")
    .reduce(
      (value, key) => (value && value[key] !== undefined ? value[key] : undefined),
      translations[language]
    );
}

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(getInitialLanguage);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, language);
    } catch (error) {
      // pas de persistance possible, l'interface continue de fonctionner
    }

    document.documentElement.lang = language;
    document.documentElement.dir = language === "ar" ? "rtl" : "ltr";
  }, [language]);

  const t = (key, params) => {
    const template = resolvePath(key, language);

    if (template === undefined) {
      return key;
    }

    if (!params) {
      return template;
    }

    return Object.keys(params).reduce(
      (result, paramKey) =>
        result.replace(new RegExp(`{${paramKey}}`, "g"), params[paramKey]),
      template
    );
  };

  const value = { language, setLanguage, t };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);

  if (!context) {
    throw new Error("useLanguage doit être utilisé à l'intérieur de LanguageProvider");
  }

  return context;
}