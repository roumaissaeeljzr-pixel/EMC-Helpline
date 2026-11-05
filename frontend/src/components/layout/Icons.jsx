const strokeProps = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

export function IconDashboard() {
  return (
    <svg {...strokeProps}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </svg>
  );
}

export function IconChat() {
  return (
    <svg {...strokeProps}>
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
    </svg>
  );
}

export function IconShield() {
  return (
    <svg {...strokeProps}>
      <path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3z" />
    </svg>
  );
}

export function IconCheck() {
  return (
    <svg {...strokeProps}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12.5 2.5 2.5 5-5" />
    </svg>
  );
}

export function IconFolder() {
  return (
    <svg {...strokeProps}>
      <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" />
    </svg>
  );
}

export function IconClip() {
  return (
    <svg {...strokeProps}>
      <path d="M8 8v9a3 3 0 0 0 6 0V6a2 2 0 0 0-4 0v10a1 1 0 0 0 2 0V8" />
    </svg>
  );
}

export function IconBook() {
  return (
    <svg {...strokeProps}>
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15z" />
      <path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20" />
    </svg>
  );
}

export function IconClock() {
  return (
    <svg {...strokeProps}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3.5 2" />
    </svg>
  );
}

export function IconEye() {
  return (
    <svg {...strokeProps}>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

export function IconChart() {
  return (
    <svg {...strokeProps}>
      <path d="M4 20V10M12 20V4M20 20v-7" />
    </svg>
  );
}

export function IconFolders() {
  return (
    <svg {...strokeProps}>
      <path d="M2 8a2 2 0 0 1 2-2h3l2 2h7a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8z" />
    </svg>
  );
}

export function IconAlert() {
  return (
    <svg {...strokeProps}>
      <path d="M12 3 2 20h20L12 3z" />
      <path d="M12 10v4" />
      <path d="M12 17h.01" />
    </svg>
  );
}

export function IconBrain() {
  return (
    <svg {...strokeProps}>
      <path d="M9 4a3 3 0 0 0-3 3v1a3 3 0 0 0-1 5.8V15a3 3 0 0 0 3 3h1M15 4a3 3 0 0 1 3 3v1a3 3 0 0 1 1 5.8V15a3 3 0 0 1-3 3h-1M9 4v15M15 4v15" />
    </svg>
  );
}

export function IconDatabase() {
  return (
    <svg {...strokeProps}>
      <ellipse cx="12" cy="5" rx="8" ry="3" />
      <path d="M4 5v14c0 1.66 3.58 3 8 3s8-1.34 8-3V5" />
      <path d="M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3" />
    </svg>
  );
}

export function IconMenu() {
  return (
    <svg {...strokeProps}>
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}