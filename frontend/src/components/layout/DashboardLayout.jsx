import {
  useEffect,
  useState,
} from "react";

import {
  Outlet,
  useLocation,
} from "react-router-dom";

import {
  AnimatePresence,
  motion,
} from "framer-motion";

import Sidebar from "./Sidebar.jsx";
import Header from "./Header.jsx";

import {
  useLanguage,
} from "../../context/LanguageContext.jsx";

import "./layout.css";


const COLLAPSED_KEY =
  "emc_sidebar_collapsed";


function getInitialCollapsedState() {
  try {
    return (
      window.localStorage.getItem(
        COLLAPSED_KEY
      ) === "true"
    );
  } catch {
    return false;
  }
}


function DashboardLayout({
  mode = "victim",
}) {
  const location =
    useLocation();

  const {
    language,
  } = useLanguage();


  const [
    isSidebarOpen,
    setIsSidebarOpen,
  ] = useState(false);


  const [
    isSidebarCollapsed,
    setIsSidebarCollapsed,
  ] = useState(
    getInitialCollapsedState
  );


  useEffect(
    () => {
      setIsSidebarOpen(false);
    },
    [
      location.pathname,
    ]
  );


  useEffect(
    () => {
      try {
        window.localStorage.setItem(
          COLLAPSED_KEY,
          String(
            isSidebarCollapsed
          )
        );
      } catch {
        // Non bloquant.
      }
    },
    [
      isSidebarCollapsed,
    ]
  );


  const closeSidebar = () => {
    setIsSidebarOpen(false);
  };


  const toggleSidebar = () => {
    setIsSidebarOpen(
      (current) => !current
    );
  };


  const toggleCollapsed = () => {
    setIsSidebarCollapsed(
      (current) => !current
    );
  };


  return (
    <div
      className={[
        "dashboard-shell",
        isSidebarCollapsed
          ? "dashboard-shell-collapsed"
          : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <Sidebar
        mode={mode}
        isOpen={isSidebarOpen}
        collapsed={
          isSidebarCollapsed
        }
        onNavigate={
          closeSidebar
        }
        onToggleCollapsed={
          toggleCollapsed
        }
      />


      <AnimatePresence>
        {isSidebarOpen && (
          <motion.button
            type="button"
            className="sidebar-overlay"
            aria-label={
              language === "ar"
                ? "إغلاق القائمة"
                : "Fermer le menu"
            }
            initial={{
              opacity: 0,
            }}
            animate={{
              opacity: 1,
            }}
            exit={{
              opacity: 0,
            }}
            transition={{
              duration: 0.18,
            }}
            onClick={
              closeSidebar
            }
          />
        )}
      </AnimatePresence>


      <div className="dashboard-main">
        <Header
          mode={mode}
          onToggleSidebar={
            toggleSidebar
          }
        />


        <main
          className="dashboard-content"
          dir={
            language === "ar"
              ? "rtl"
              : "ltr"
          }
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}


export default DashboardLayout;