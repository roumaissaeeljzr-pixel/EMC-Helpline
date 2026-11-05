import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";


const AuthContext =
  createContext(null);


const API_BASE_URL =
  import.meta.env.VITE_API_URL
  || "http://localhost:8000";


const CHAT_SESSION_PREFIX =
  "emc-helpline:victim-chat:";


function clearVictimChatSession() {
  for (
    let index = sessionStorage.length - 1;
    index >= 0;
    index -= 1
  ) {
    const key =
      sessionStorage.key(index);

    if (
      key?.startsWith(
        CHAT_SESSION_PREFIX
      )
    ) {
      sessionStorage.removeItem(key);
    }
  }
}


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


export function AuthProvider({
  children,
}) {
  const [
    user,
    setUser,
  ] = useState(null);

  const [
    victimProfile,
    setVictimProfile,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    profileLoading,
    setProfileLoading,
  ] = useState(false);


  // ==========================================================
  // PROFIL VICTIME
  // ==========================================================

  const fetchVictimProfile =
    async (currentUser) => {

      if (
        !currentUser
        || currentUser.role
        !== "victim"
      ) {
        setVictimProfile(null);

        return null;
      }

      setProfileLoading(true);

      try {
        const response = await fetch(
          `${API_BASE_URL}/profile/me`,
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
          setVictimProfile(null);

          return null;
        }

        const data =
          await response.json();

        setVictimProfile(data);

        return data;
      } catch (error) {
        console.error(
          "Erreur lors du chargement "
          + "du profil victime :",
          error
        );

        setVictimProfile(null);

        return null;
      } finally {
        setProfileLoading(false);
      }
    };


  // ==========================================================
  // ACTUALISER LA SESSION
  // ==========================================================

  const refreshSession =
    async () => {

      try {
        const response = await fetch(
          `${API_BASE_URL}/auth/me`,
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
          setUser(null);
          setVictimProfile(null);

          return null;
        }

        const data =
          await response.json();

        setUser(data);

        await fetchVictimProfile(
          data
        );

        return data;
      } catch (error) {
        console.error(
          "Erreur lors de la vérification "
          + "de la session :",
          error
        );

        setUser(null);
        setVictimProfile(null);

        return null;
      }
    };


  const refreshVictimProfile =
    async () => {

      return fetchVictimProfile(
        user
      );
    };


  // ==========================================================
  // INITIALISATION
  // ==========================================================

  useEffect(() => {
    let cancelled = false;

    const initialize =
      async () => {

        try {
          const response = await fetch(
            `${API_BASE_URL}/auth/me`,
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

          if (cancelled) {
            return;
          }

          if (!response.ok) {
            setUser(null);
            setVictimProfile(null);

            return;
          }

          const data =
            await response.json();

          if (cancelled) {
            return;
          }

          setUser(data);

          if (
            data.role === "victim"
          ) {
            setProfileLoading(true);

            try {
              const profileResponse =
                await fetch(
                  `${API_BASE_URL}/profile/me`,
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

              if (cancelled) {
                return;
              }

              if (
                profileResponse.ok
              ) {
                const profileData =
                  await profileResponse
                    .json();

                if (!cancelled) {
                  setVictimProfile(
                    profileData
                  );
                }
              } else {
                setVictimProfile(
                  null
                );
              }
            } catch (
              profileError
            ) {
              if (!cancelled) {
                console.error(
                  "Erreur lors du "
                  + "chargement initial "
                  + "du profil victime :",
                  profileError
                );

                setVictimProfile(
                  null
                );
              }
            } finally {
              if (!cancelled) {
                setProfileLoading(
                  false
                );
              }
            }
          } else {
            setVictimProfile(null);
          }
        } catch (error) {
          if (!cancelled) {
            console.error(
              "Erreur lors de "
              + "l'initialisation de "
              + "l'authentification :",
              error
            );

            setUser(null);
            setVictimProfile(null);
          }
        } finally {
          if (!cancelled) {
            setLoading(false);
          }
        }
      };

    initialize();

    return () => {
      cancelled = true;
    };
  }, []);


  // ==========================================================
  // INSCRIPTION
  // ==========================================================

  const register = async ({
    username,
    email,
    password,
    language = "fr",
  }) => {

    const response = await fetch(
      `${API_BASE_URL}/auth/register`,
      {
        method: "POST",

        credentials:
          "include",

        headers: {
          "Content-Type":
            "application/json",

          Accept:
            "application/json",
        },

        body: JSON.stringify({
          username,
          email,
          password,
          language,
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
      const message =
        data?.detail
        || "Impossible de créer le compte.";

      throw new Error(
        typeof message
        === "string"
          ? message
          : "Impossible de créer le compte."
      );
    }

    return data;
  };


  // ==========================================================
  // VÉRIFIER L'ADRESSE E-MAIL
  // ==========================================================

  const verifyEmail = async ({
    email,
    code,
  }) => {

    const response = await fetch(
      `${API_BASE_URL}/auth/verify-email`,
      {
        method: "POST",

        credentials:
          "include",

        headers: {
          "Content-Type":
            "application/json",

          Accept:
            "application/json",
        },

        body: JSON.stringify({
          email,
          code,
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
      const message =
        data?.detail
        || "Le code est invalide ou expiré.";

      throw new Error(
        typeof message
        === "string"
          ? message
          : "Le code est invalide ou expiré."
      );
    }

    return data;
  };


  // ==========================================================
  // RENVOYER LE CODE
  // ==========================================================

  const resendVerificationCode =
    async ({
      email,
      language = "fr",
    }) => {

      const response = await fetch(
        `${API_BASE_URL}/auth/resend-verification-code`,
        {
          method: "POST",

          credentials:
            "include",

          headers: {
            "Content-Type":
              "application/json",

            Accept:
              "application/json",
          },

          body: JSON.stringify({
            email,
            language,
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
        const message =
          data?.detail
          || "Impossible de renvoyer le code.";

        throw new Error(
          typeof message
          === "string"
            ? message
            : "Impossible de renvoyer le code."
        );
      }

      return data;
    };


  // ==========================================================
  // CONNEXION
  // ==========================================================

  const login = async ({
    username,
    password,
  }) => {

    const response = await fetch(
      `${API_BASE_URL}/auth/login`,
      {
        method: "POST",

        credentials:
          "include",

        headers: {
          "Content-Type":
            "application/json",

          Accept:
            "application/json",
        },

        body: JSON.stringify({
          username,
          password,
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
      const message =
        data?.detail
        || "Connexion impossible.";

      throw new Error(
        typeof message
        === "string"
          ? message
          : "Connexion impossible."
      );
    }

    setUser(data);

    await fetchVictimProfile(
      data
    );

    return data;
  };


  // ==========================================================
  // DÉCONNEXION
  // ==========================================================

  const logout = async () => {
    const csrfToken =
      readCookie(
        "csrf_token"
      );

    if (!csrfToken) {
      clearVictimChatSession();
      setUser(null);
      setVictimProfile(null);

      throw new Error(
        "Jeton CSRF introuvable. "
        + "Veuillez vous reconnecter."
      );
    }

    const response = await fetch(
      `${API_BASE_URL}/auth/logout`,
      {
        method: "POST",

        credentials:
          "include",

        headers: {
          "X-CSRF-Token":
            csrfToken,
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
        || "Déconnexion impossible."
      );
    }

    clearVictimChatSession();
    setUser(null);
    setVictimProfile(null);
  };


  // ==========================================================
  // ÉTAT DU PROFIL
  // ==========================================================

  const identityComplete =
    user?.role === "victim"
      ? Boolean(
          victimProfile
            ?.identity_complete
        )
      : true;


  // ==========================================================
  // VALEURS EXPOSÉES
  // ==========================================================

  const value = useMemo(
    () => ({
      user,
      loading,
      profileLoading,
      victimProfile,
      identityComplete,

      register,
      verifyEmail,
      resendVerificationCode,

      login,
      logout,

      refreshSession,
      refreshVictimProfile,

      isAuthenticated:
        Boolean(user),

      isVictim:
        user?.role === "victim",

      isAdmin:
        user?.role === "admin",
    }),
    [
      user,
      loading,
      profileLoading,
      victimProfile,
      identityComplete,
    ]
  );


  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}


export function useAuth() {
  const context =
    useContext(
      AuthContext
    );

  if (!context) {
    throw new Error(
      "useAuth doit être utilisé "
      + "à l'intérieur de AuthProvider."
    );
  }

  return context;
}


export default AuthContext;
