import { useEffect, useMemo, useRef, useState } from "react";
import "../components/chat/Chat.css";
import { containsArabic } from "../utils/language.js";
import { useLanguage } from "../context/LanguageContext.jsx";
import { useAuth } from "../context/AuthContext.jsx";

const API_URL = "http://127.0.0.1:8000/chat";
const CHAT_SESSION_PREFIX = "emc-helpline:victim-chat:";

const createWelcomeMessage = () => ({
  id: "welcome",
  role: "assistant",
  isWelcome: true,
});

const readChatSession = (storageKey) => {
  if (!storageKey) {
    return {
      messages: [createWelcomeMessage()],
      pendingContext: null,
    };
  }

  try {
    const storedValue = sessionStorage.getItem(storageKey);

    if (!storedValue) {
      return {
        messages: [createWelcomeMessage()],
        pendingContext: null,
      };
    }

    const parsedValue = JSON.parse(storedValue);
    const storedMessages = Array.isArray(parsedValue?.messages)
      ? parsedValue.messages
      : [];

    return {
      messages: storedMessages.length > 0
        ? storedMessages
        : [createWelcomeMessage()],
      pendingContext: parsedValue?.pendingContext || null,
    };
  } catch (error) {
    console.error("Impossible de restaurer la conversation :", error);

    return {
      messages: [createWelcomeMessage()],
      pendingContext: null,
    };
  }
};

function Assistant() {
  const { language, t } = useLanguage();
  const { user } = useAuth();

  const chatStorageKey = useMemo(() => {
    const userIdentifier =
      user?.id || user?.username || user?.email;

    return userIdentifier
      ? `${CHAT_SESSION_PREFIX}${userIdentifier}`
      : null;
  }, [user?.id, user?.username, user?.email]);

  const interfaceLanguage =
    language === "ar" ? "ar" : "fr";

  const interfaceDir =
    interfaceLanguage === "ar" ? "rtl" : "ltr";

  // Le message d'accueil n'est pas figé en texte : il est marqué
  // isWelcome et son texte est résolu à l'affichage via t(), afin
  // de suivre la langue de l'interface sans jamais réinitialiser
  // la conversation déjà en cours.
  const [messages, setMessages] = useState([
    createWelcomeMessage(),
  ]);

  // Mémoire minimale de clarification multi-tour.
  // Elle reste uniquement en mémoire React et correspond exactement
  // au ChatContext attendu par POST /chat côté FastAPI.
  const [pendingContext, setPendingContext] = useState(null);
  const [sessionRestored, setSessionRestored] = useState(false);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    const storedSession = readChatSession(chatStorageKey);

    setMessages(storedSession.messages);
    setPendingContext(storedSession.pendingContext);
    setSessionRestored(Boolean(chatStorageKey));
  }, [chatStorageKey]);

  useEffect(() => {
    if (!chatStorageKey || !sessionRestored) {
      return;
    }

    try {
      sessionStorage.setItem(
        chatStorageKey,
        JSON.stringify({ messages, pendingContext })
      );
    } catch (error) {
      console.error("Impossible de mémoriser la conversation :", error);
    }
  }, [chatStorageKey, messages, pendingContext, sessionRestored]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const sendMessage = async () => {
    const cleanMessage = input.trim();

    if (!cleanMessage || loading) {
      return;
    }

    const userLanguage =
      containsArabic(cleanMessage) ? "ar" : "fr";

    const userMessage = {
      id: Date.now(),
      role: "user",
      text: cleanMessage,
      language: userLanguage,
    };

    setMessages((previousMessages) => [
      ...previousMessages,
      userMessage,
    ]);

    // On capture le contexte exactement au moment de l'envoi.
    // Cela évite qu'une mise à jour React ultérieure ne change
    // le contexte associé à cette requête en cours.
    const requestContext = pendingContext
      ? { ...pendingContext }
      : null;

    const wasPending = requestContext !== null;

    // Les dix derniers messages visibles sont renvoyés avec chaque
    // requête afin d'assurer la continuité sans stocker de données
    // de conversation supplémentaires côté serveur.
    const requestHistory = messages
      .filter(
        (message) =>
          !message.isWelcome
          && !message.error
          && (message.role === "user"
            || message.role === "assistant")
          && typeof message.text === "string"
          && message.text.trim()
      )
      .slice(-10)
      .map((message) => ({
        role: message.role,
        content: message.text.trim().slice(0, 2000),
      }));

    setInput("");
    setLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: cleanMessage,
          debug: false,
          context: requestContext,
          history: requestHistory,
        }),
      });

      if (!response.ok) {
        throw new Error(
          `Erreur API /chat (${response.status})`
        );
      }

      const data = await response.json();

      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: data.answer,
        language: data.language || userLanguage,
      };

      setMessages((previousMessages) => [
        ...previousMessages,
        assistantMessage,
      ]);

      // Si le backend demande encore une clarification, on conserve
      // toujours le message ORIGINAL et sa langue.
      //
      // Exemple :
      // 1) "Une personne menace de publier mes photos..."
      // 2) backend -> demande de l'âge
      // 3) "Je ne sais pas"
      // 4) backend -> repose la clarification
      //
      // L'étape 3 ne doit jamais remplacer original_message.
      if (data.clarification_required) {
        setPendingContext({
          pending_intent: data.predicted_intent,
          pending_clarification:
            data.clarification_required,
          original_message: wasPending
            ? requestContext.original_message
            : cleanMessage,
          original_language: wasPending
            ? requestContext.original_language
            : data.language || userLanguage,
        });
      } else {
        setPendingContext(null);
      }
    } catch (error) {
      console.error(
        "Erreur lors de l'envoi du message :",
        error
      );

      const errorMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: t("assistant.error"),
        language: interfaceLanguage,
        error: true,
      };

      setMessages((previousMessages) => [
        ...previousMessages,
        errorMessage,
      ]);

      // IMPORTANT :
      // on ne supprime pas pendingContext en cas d'erreur réseau/API.
      // L'utilisateur peut ainsi réessayer sans perdre la
      // clarification en cours.
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (
      event.key === "Enter"
      && !event.shiftKey
    ) {
      event.preventDefault();
      sendMessage();
    }
  };

  const inputDir = input.trim()
    ? containsArabic(input)
      ? "rtl"
      : "ltr"
    : interfaceDir;

  return (
    <div
      className="chat-page"
      lang={interfaceLanguage}
      dir={interfaceDir}
    >
      <div className="chat-container">
        <div className="chat-header">
          <div className="assistant-avatar">
            EMC
          </div>

          <div>
            <h2>{t("assistant.title")}</h2>
            <p>Français · العربية</p>
          </div>
        </div>

        <div
          className="messages"
          aria-live="polite"
        >
          {messages.map((message) => {
            const text = message.isWelcome
              ? t("assistant.welcome")
              : message.text;

            const isArabic = message.isWelcome
              ? interfaceLanguage === "ar"
              : (
                  message.language === "ar"
                  || containsArabic(
                    message.text || ""
                  )
                );

            return (
              <div
                key={message.id}
                className={`message-row ${
                  message.role === "user"
                    ? "user-row"
                    : "assistant-row"
                }`}
              >
                <div
                  className={`message ${
                    message.role === "user"
                      ? "user-message"
                      : "assistant-message"
                  } ${
                    message.error
                      ? "error-message"
                      : ""
                  }`}
                  lang={isArabic ? "ar" : "fr"}
                  dir={isArabic ? "rtl" : "ltr"}
                >
                  {text}
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="message-row assistant-row">
              <div
                className="message assistant-message loading-message"
                lang={interfaceLanguage}
                dir={interfaceDir}
              >
                {t("assistant.loading")}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <textarea
            value={input}
            onChange={(event) =>
              setInput(event.target.value)
            }
            onKeyDown={handleKeyDown}
            placeholder={t(
              "assistant.placeholder"
            )}
            rows="1"
            lang={interfaceLanguage}
            dir={inputDir}
            disabled={loading}
          />

          <button
            type="button"
            onClick={sendMessage}
            disabled={!input.trim() || loading}
          >
            {loading
              ? "..."
              : t("assistant.send")}
          </button>
        </div>

        <p
          className="disclaimer"
          lang={interfaceLanguage}
          dir={interfaceDir}
        >
          {t("assistant.disclaimer")}
        </p>
      </div>
    </div>
  );
}

export default Assistant;
