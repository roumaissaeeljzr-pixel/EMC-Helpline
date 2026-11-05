import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";


import Dashboard
  from "./pages/Dashboard.jsx";

import Assistant
  from "./pages/Assistant.jsx";

import Assessment
  from "./pages/Assessment.jsx";

import ActionPlan
  from "./pages/ActionPlan.jsx";

import CaseFile
  from "./pages/CaseFile.jsx";

import Evidence
  from "./pages/Evidence.jsx";

import Resources
  from "./pages/Resources.jsx";

import History
  from "./pages/History.jsx";

import Profile
  from "./pages/Profile.jsx";


import AdminOverview
  from "./pages/admin/Overview.jsx";

import AdminStatistics
  from "./pages/admin/Statistics.jsx";

import AdminCases
  from "./pages/admin/Cases.jsx";

import AdminPriorityCases
  from "./pages/admin/PriorityCases.jsx";



import AdminDocumentBase
  from "./pages/admin/DocumentBase.jsx";


import Login
  from "./pages/Login.jsx";

import Register
  from "./pages/Register.jsx";

import VerifyEmail
  from "./pages/VerifyEmail.jsx";

import ForgotPassword
  from "./pages/ForgotPassword.jsx";

import VerifyResetCode
  from "./pages/VerifyResetCode.jsx";

import ResetPassword
  from "./pages/ResetPassword.jsx";


import VictimLayout
  from "./components/layout/VictimLayout.jsx";

import AdminLayout
  from "./components/layout/AdminLayout.jsx";


import ProtectedRoute
  from "./components/auth/ProtectedRoute.jsx";


import {
  AuthProvider,
  useAuth,
} from "./context/AuthContext.jsx";


function RoleHome() {
  const {
    user,
    loading,
  } = useAuth();


  if (loading) {
    return null;
  }


  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }


  return (
    <Navigate
      to={
        user.role === "admin"
          ? "/admin/dashboard"
          : "/victim/dashboard"
      }
      replace
    />
  );
}


function AppRoutes() {
  return (
    <Routes>

      {/* ================================================= */}
      {/* PUBLIC */}
      {/* ================================================= */}

      <Route
        path="/"
        element={
          <RoleHome />
        }
      />


      <Route
        path="/login"
        element={
          <Login />
        }
      />


      <Route
        path="/register"
        element={
          <Register />
        }
      />


      <Route
        path="/verify-email"
        element={
          <VerifyEmail />
        }
      />


      <Route
        path="/forgot-password"
        element={
          <ForgotPassword />
        }
      />


      <Route
        path="/verify-reset-code"
        element={
          <VerifyResetCode />
        }
      />


      <Route
        path="/reset-password"
        element={
          <ResetPassword />
        }
      />


      {/* ================================================= */}
      {/* VICTIME */}
      {/* ================================================= */}

      <Route
        element={
          <ProtectedRoute
            allowedRoles={[
              "victim",
            ]}
          />
        }
      >

        <Route
          element={
            <VictimLayout />
          }
        >

          <Route
            path="/victim/dashboard"
            element={
              <Dashboard />
            }
          />


          <Route
            path="/victim/assistant"
            element={
              <Assistant />
            }
          />


          <Route
            path="/victim/assessment"
            element={
              <Assessment />
            }
          />


          <Route
            path="/victim/action-plan"
            element={
              <ActionPlan />
            }
          />


          <Route
            path="/victim/case"
            element={
              <CaseFile />
            }
          />


          <Route
            path="/victim/evidence"
            element={
              <Evidence />
            }
          />


          <Route
            path="/victim/resources"
            element={
              <Resources />
            }
          />


          <Route
            path="/victim/history"
            element={
              <History />
            }
          />


          <Route
            path="/victim/profile"
            element={
              <Profile />
            }
          />

        </Route>

      </Route>


      {/* ================================================= */}
      {/* ADMINISTRATEUR */}
      {/* ================================================= */}

      <Route
        element={
          <ProtectedRoute
            allowedRoles={[
              "admin",
            ]}
          />
        }
      >

        <Route
          element={
            <AdminLayout />
          }
        >

          <Route
            path="/admin/dashboard"
            element={
              <AdminOverview />
            }
          />


          <Route
            path="/admin/statistics"
            element={
              <AdminStatistics />
            }
          />


          <Route
            path="/admin/cases"
            element={
              <AdminCases />
            }
          />


          <Route
            path="/admin/priority-cases"
            element={
              <AdminPriorityCases />
            }
          />


          


          <Route
            path="/admin/document-base"
            element={
              <AdminDocumentBase />
            }
          />

        </Route>

      </Route>


      {/* ================================================= */}
      {/* ROUTE INCONNUE */}
      {/* ================================================= */}

      <Route
        path="*"
        element={
          <RoleHome />
        }
      />

    </Routes>
  );
}


function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}


export default App;
