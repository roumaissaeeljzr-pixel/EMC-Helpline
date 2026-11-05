import {
  useEffect,
  useId,
  useState,
} from "react";

import {
  AnimatePresence,
  motion,
  useReducedMotion,
} from "framer-motion";


export function DashboardIcon({
  name,
  size = 22,
}) {
  const props = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": "true",
  };


  const icons = {
    shield: (
      <>
        <path d="M12 3 5 6v5c0 4.7 2.7 8 7 10 4.3-2 7-5.3 7-10V6z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),

    folder: (
      <>
        <path d="M3 7h6l2 2h10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <path d="M3 9h18" />
      </>
    ),

    clip: (
      <path d="m8.5 12.5 6.2-6.2a3 3 0 0 1 4.2 4.2l-8 8a5 5 0 0 1-7.1-7.1l8.2-8.2" />
    ),

    check: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="m8 12 2.5 2.5L16 9" />
      </>
    ),

    chat: (
      <>
        <path d="M4 5h16v11H8l-4 3z" />
        <path d="M8 9h8" />
        <path d="M8 12h5" />
      </>
    ),

    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),

    arrow: (
      <>
        <path d="M5 12h14" />
        <path d="m14 7 5 5-5 5" />
      </>
    ),

    lock: (
      <>
        <rect
          x="5"
          y="10"
          width="14"
          height="10"
          rx="2"
        />
        <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      </>
    ),

    spark: (
      <>
        <path d="m12 2 1.2 4.2L17 8l-3.8 1.8L12 14l-1.2-4.2L7 8l3.8-1.8z" />
        <path d="m19 15 .6 2 1.8.9-1.8 1-.6 2.1-.6-2.1-1.8-1 1.8-.9z" />
      </>
    ),
  };


  return (
    <svg {...props}>
      {icons[name] || icons.shield}
    </svg>
  );
}


/* ==========================================================
   ANIMATED NUMBER
   ========================================================== */

export function AnimatedProgressNumber({
  value,
}) {
  const reducedMotion =
    useReducedMotion();


  const [
    visibleValue,
    setVisibleValue,
  ] = useState(
    reducedMotion
      ? value
      : 0
  );


  useEffect(
    () => {
      if (reducedMotion) {
        setVisibleValue(value);
        return;
      }


      let frame;

      const start =
        performance.now();

      const duration = 750;


      const animate =
        (time) => {
          const ratio =
            Math.min(
              1,
              (
                time - start
              )
              / duration
            );


          const eased =
            1
            - Math.pow(
                1 - ratio,
                3
              );


          setVisibleValue(
            Math.round(
              value * eased
            )
          );


          if (ratio < 1) {
            frame =
              requestAnimationFrame(
                animate
              );
          }
        };


      frame =
        requestAnimationFrame(
          animate
        );


      return () => {
        cancelAnimationFrame(
          frame
        );
      };
    },
    [
      value,
      reducedMotion,
    ]
  );


  return (
    <>
      {visibleValue}%
    </>
  );
}


/* ==========================================================
   FOLDER + SHIELD ILLUSTRATION
   ========================================================== */

export function GuidedFolderIllustration() {
  const reducedMotion =
    useReducedMotion();


  return (
    <motion.div
      className="guided-folder-illustration"
      initial={
        reducedMotion
          ? false
          : {
              opacity: 0,
              y: 10,
              scale: 0.97,
            }
      }
      animate={{
        opacity: 1,
        y: 0,
        scale: 1,
      }}
      transition={{
        duration: 0.55,
      }}
      aria-hidden="true"
    >
      <span className="guided-orb orb-a" />
      <span className="guided-orb orb-b" />
      <span className="guided-orb orb-c" />
      <span className="guided-spark spark-a" />
      <span className="guided-spark spark-b" />


      <svg
        viewBox="0 0 380 280"
        className="guided-folder-svg"
      >
        <defs>
          <linearGradient
            id="folderMain"
            x1="0"
            y1="0"
            x2="1"
            y2="1"
          >
            <stop
              offset="0%"
              stopColor="#8d63dc"
            />

            <stop
              offset="100%"
              stopColor="#5632ad"
            />
          </linearGradient>


          <linearGradient
            id="folderInner"
            x1="0"
            y1="0"
            x2="1"
            y2="1"
          >
            <stop
              offset="0%"
              stopColor="#ff9a54"
            />

            <stop
              offset="100%"
              stopColor="#ed567e"
            />
          </linearGradient>


          <filter
            id="folderShadow"
            x="-30%"
            y="-30%"
            width="160%"
            height="160%"
          >
            <feDropShadow
              dx="0"
              dy="15"
              stdDeviation="14"
              floodColor="#5c3a8e"
              floodOpacity=".18"
            />
          </filter>
        </defs>


        <circle
          cx="205"
          cy="137"
          r="112"
          fill="#f2ecfb"
        />


        <circle
          cx="92"
          cy="72"
          r="9"
          fill="#f6a33f"
          opacity=".6"
        />


        <circle
          cx="310"
          cy="71"
          r="7"
          fill="#7451c9"
          opacity=".6"
        />


        <circle
          cx="327"
          cy="200"
          r="10"
          fill="#ec6492"
          opacity=".25"
        />


        <path
          d="M112 93h72l20 20h86c10 0 18 8 18 18v78c0 10-8 18-18 18H112c-10 0-18-8-18-18v-98c0-10 8-18 18-18Z"
          fill="url(#folderMain)"
          filter="url(#folderShadow)"
        />


        <path
          d="M114 126h178v82H114Z"
          rx="12"
          fill="#7150c2"
        />


        <path
          d="M138 105h62l14 15h-76Z"
          fill="#a98ae8"
        />


        <rect
          x="141"
          y="138"
          width="117"
          height="55"
          rx="10"
          fill="url(#folderInner)"
          opacity=".95"
        />


        <path
          d="M202 139 166 154v29c0 28 15 49 36 60 22-11 37-32 37-60v-29Z"
          fill="#fff"
          stroke="#f4e9fb"
          strokeWidth="3"
        />


        <path
          d="M202 151 177 161v21c0 19 10 34 25 42 15-8 25-23 25-42v-21Z"
          fill="#6c45bc"
        />


        <path
          d="m190 183 9 9 17-20"
          fill="none"
          stroke="#ffffff"
          strokeWidth="5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />


        <path
          d="M74 164c-18 11-29 28-30 49"
          fill="none"
          stroke="#e0d2f5"
          strokeWidth="4"
          strokeLinecap="round"
        />


        <path
          d="M323 132c15 8 26 21 31 37"
          fill="none"
          stroke="#f2c8dd"
          strokeWidth="4"
          strokeLinecap="round"
        />
      </svg>
    </motion.div>
  );
}


/* ==========================================================
   PROGRESS CIRCLE
   ========================================================== */

export function ProgressCircle({
  value,
  label,
  sublabel,
}) {
  const reducedMotion =
    useReducedMotion();


  const gradientId =
    useId()
      .replace(/:/g, "");


  const radius = 52;

  const circumference =
    2 * Math.PI * radius;


  const offset =
    circumference
    - (
      value / 100
    )
    * circumference;


  return (
    <div className="guided-progress-circle">
      <svg
        viewBox="0 0 130 130"
        aria-hidden="true"
      >
        <defs>
          <linearGradient
            id={gradientId}
            x1="0"
            y1="0"
            x2="1"
            y2="1"
          >
            <stop
              offset="0%"
              stopColor="#7650c5"
            />

            <stop
              offset="48%"
              stopColor="#e0539a"
            />

            <stop
              offset="100%"
              stopColor="#f3a13c"
            />
          </linearGradient>
        </defs>


        <circle
          cx="65"
          cy="65"
          r={radius}
          className="guided-progress-track"
        />


        <motion.circle
          cx="65"
          cy="65"
          r={radius}
          className="guided-progress-value"
          stroke={`url(#${gradientId})`}
          strokeDasharray={
            circumference
          }
          initial={{
            strokeDashoffset:
              circumference,
          }}
          animate={{
            strokeDashoffset:
              offset,
          }}
          transition={{
            duration:
              reducedMotion
                ? 0
                : 0.9,
            ease: "easeOut",
          }}
        />
      </svg>


      <div className="guided-progress-content">
        <strong>
          <AnimatedProgressNumber
            value={value}
          />
        </strong>

        {label && (
          <span>
            {label}
          </span>
        )}

        {sublabel && (
          <small>
            {sublabel}
          </small>
        )}
      </div>
    </div>
  );
}


/* ==========================================================
   JOURNEY
   ========================================================== */

export function JourneyTimeline({
  steps,
  title,
}) {
  const reducedMotion =
    useReducedMotion();


  const currentIndex =
    Math.max(
      0,
      steps.findIndex(
        (step) =>
          step.status === "current"
      )
    );


  const finishedIndexes =
    steps
      .map(
        (step, index) =>
          step.status === "completed"
            ? index
            : -1
      )
      .filter(
        (index) =>
          index >= 0
      );


  const highestIndex =
    Math.max(
      currentIndex,
      ...finishedIndexes,
      0
    );


  const width =
    steps.length > 1
      ? (
          highestIndex
          / (
            steps.length - 1
          )
        )
        * 100
      : 0;


  return (
    <motion.section
      className="guided-journey-card"
      initial={
        reducedMotion
          ? false
          : {
              opacity: 0,
              y: 12,
            }
      }
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        delay: 0.12,
      }}
    >
      <h2>
        {title}
      </h2>


      <div className="guided-journey">
        <div className="guided-journey-line">
          <motion.span
            initial={{
              width: 0,
            }}
            animate={{
              width:
                `${width}%`,
            }}
            transition={{
              duration:
                reducedMotion
                  ? 0
                  : 0.7,
            }}
          />
        </div>


        {steps.map(
          (
            step,
            index
          ) => (
            <div
              className={
                `guided-journey-step is-${step.status}`
              }
              key={step.key}
            >
              <motion.span
                className="guided-journey-node"
                initial={
                  reducedMotion
                    ? false
                    : {
                        scale: 0.85,
                        opacity: 0,
                      }
                }
                animate={{
                  scale: 1,
                  opacity: 1,
                }}
                transition={{
                  delay:
                    index * 0.07,
                }}
              >
                {step.status
                  === "completed"
                  ? "✓"
                  : index + 1}
              </motion.span>

              <strong>
                {step.label}
              </strong>
            </div>
          )
        )}
      </div>
    </motion.section>
  );
}


/* ==========================================================
   QUICK ACTION
   ========================================================== */

export function QuickActionCard({
  icon,
  tone,
  title,
  description,
  onClick,
  index = 0,
}) {
  const reducedMotion =
    useReducedMotion();


  return (
    <motion.button
      type="button"
      className={
        `guided-quick-card guided-quick-${tone}`
      }
      onClick={onClick}
      initial={
        reducedMotion
          ? false
          : {
              opacity: 0,
              y: 10,
            }
      }
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        delay:
          index * 0.05,
      }}
      whileHover={
        reducedMotion
          ? undefined
          : {
              y: -3,
            }
      }
      whileTap={
        reducedMotion
          ? undefined
          : {
              scale: 0.99,
            }
      }
    >
      <span className="guided-quick-icon">
        <DashboardIcon
          name={icon}
          size={22}
        />
      </span>


      <strong>
        {title}
      </strong>


      <p>
        {description}
      </p>


      <span className="guided-quick-arrow">
        <DashboardIcon
          name="arrow"
          size={18}
        />
      </span>
    </motion.button>
  );
}


/* ==========================================================
   ACTIVITY
   ========================================================== */

export function ActivityTimeline({
  events,
  getTitle,
  getDescription,
  formatDate,
  emptyLabel,
}) {
  return (
    <div className="guided-activity-list">
      {events.length === 0 ? (
        <div className="guided-activity-empty">
          <DashboardIcon
            name="clock"
            size={27}
          />

          <span>
            {emptyLabel}
          </span>
        </div>
      ) : (
        events.map(
          (
            event,
            index
          ) => (
            <article
              className="guided-activity-item"
              key={
                event.id
                || `${event.event_type}-${index}`
              }
            >
              <span
                className={
                  `guided-activity-icon event-${event.event_type}`
                }
              >
                {event.event_type
                  === "action_completed"
                  ? "✓"
                  : event.event_type
                    === "action_plan_generated"
                    ? "◇"
                    : "•"}
              </span>


              <div>
                <strong>
                  {getTitle(event)}
                </strong>

                <p>
                  {getDescription(event)}
                </p>
              </div>


              <time>
                {formatDate(
                  event.created_at
                )}
              </time>
            </article>
          )
        )
      )}
    </div>
  );
}


/* ==========================================================
   DASHBOARD SKELETON
   ========================================================== */

export function DashboardSkeleton() {
  return (
    <div
      className="guided-dashboard guided-dashboard-loading"
      aria-busy="true"
    >
      <div className="guided-skeleton hero-skeleton" />

      <div className="guided-overview-skeleton">
        <div className="guided-skeleton" />
        <div className="guided-skeleton" />
      </div>

      <div className="guided-skeleton action-skeleton" />

      <div className="guided-skeleton journey-skeleton" />
    </div>
  );
}


/* ==========================================================
   ASSISTANT PREVIEW
   ========================================================== */

export function AssistantPreview({
  open,
  language,
  onClose,
  onOpenAssistant,
}) {
  const copy =
    language === "ar"
      ? {
          title:
            "المساعد الذكي",

          description:
            "يمكن للمساعد مساعدتك على فهم الخطوات المقترحة والوصول إلى المعلومات المناسبة لحالتك.",

          open:
            "فتح المساعد",

          close:
            "إغلاق",
        }
      : {
          title:
            "Assistant IA",

          description:
            "L’assistant peut vous aider à comprendre les étapes proposées et retrouver les informations adaptées à votre situation.",

          open:
            "Ouvrir l’assistant",

          close:
            "Fermer",
        };


  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.button
            type="button"
            className="guided-assistant-backdrop"
            aria-label={
              copy.close
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
            onClick={onClose}
          />


          <motion.aside
            className="guided-assistant-preview"
            dir={
              language === "ar"
                ? "rtl"
                : "ltr"
            }
            initial={{
              opacity: 0,
              x:
                language === "ar"
                  ? -30
                  : 30,
            }}
            animate={{
              opacity: 1,
              x: 0,
            }}
            exit={{
              opacity: 0,
              x:
                language === "ar"
                  ? -30
                  : 30,
            }}
            transition={{
              duration: 0.22,
            }}
          >
            <button
              type="button"
              className="guided-assistant-close"
              aria-label={
                copy.close
              }
              onClick={onClose}
            >
              ×
            </button>


            <span className="guided-assistant-logo">
              <DashboardIcon
                name="spark"
                size={28}
              />
            </span>


            <h2>
              {copy.title}
            </h2>

            <p>
              {copy.description}
            </p>


            <button
              type="button"
              className="guided-assistant-open"
              onClick={
                onOpenAssistant
              }
            >
              {copy.open}

              <DashboardIcon
                name="arrow"
                size={17}
              />
            </button>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}