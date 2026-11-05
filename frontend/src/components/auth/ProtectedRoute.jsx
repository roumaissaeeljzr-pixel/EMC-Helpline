import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import {
  useAuth,
} from "../../context/AuthContext.jsx";


function getRoleHome(role) {
  return role === "admin"
    ? "/admin/dashboard"
    : "/victim/dashboard";
}


function ProtectedRoute({
  allowedRoles = [],
}) {
  const location = useLocation();

  const {
    user,
    loading,
    profileLoading,
    identityComplete,
  } = useAuth();


  if (loading || profileLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          fontFamily: "inherit",
        }}
      >
        Chargement...
      </div>
    );
  }


  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }


  if (
    allowedRoles.length > 0
    && !allowedRoles.includes(user.role)
  ) {
    return (
      <Navigate
        to={getRoleHome(user.role)}
        replace
      />
    );
  }


  const isVictim =
    user.role === "victim";

  const isProfileRoute =
    location.pathname === "/victim/profile";


  if (
    isVictim
    && !identityComplete
    && !isProfileRoute
  ) {
    return (
      <Navigate
        to="/victim/profile"
        replace
        state={{
          requiredProfile: true,
          from: location.pathname,
        }}
      />
    );
  }


  return <Outlet />;
}


export default ProtectedRoute;
