/* ─── Nav Config ─────────────────────────────────────────────────────────── */
export const NAV = [
  {
    s: "OVERVIEW",
    items: [
      { id: "dashboard", label: "Dashboard", icon: "LayoutDashboard" },
    ],
  },
  {
    s: "OPERATIONS",
    items: [
      { id: "stations",   label: "Stations",    icon: "MapPin",         count: 12 },
      { id: "fuel-types", label: "Fuel Types",  icon: "Droplets" },
      { id: "orders",     label: "Orders",      icon: "ShoppingCart",   count: 5, cc: "#f59e0b" },
      { id: "payments",   label: "Payments",    icon: "CreditCard" },
    ],
  },
  {
    s: "MANAGEMENT",
    items: [
      {
        id: "users", label: "Staff & Users", icon: "Users",
        sub: [
          { id: "activity-logs", label: "Activity Logs", icon: "Activity" },
        ],
      },
      { id: "notifications", label: "Notifications", icon: "Bell", count: 3, cc: "#f43f5e" },
    ],
  },
  {
    s: "SYSTEM",
    items: [
      {
        id: "settings", label: "Settings", icon: "Settings",
        sub: [
          { id: "appearance", label: "Appearance",  icon: "Sun" },
          { id: "general",    label: "General",     icon: "Gauge" },
        ],
      },
    ],
  },
  {
    s: "ACCOUNT",
    items: [
      { id: "profile",       label: "Profile",          icon: "User" },
      { id: "security",      label: "Security",         icon: "Shield" },
      { id: "acct-settings", label: "Account Settings", icon: "UserCog" },
    ],
  },
];

export const ROLE_COLORS = {
  "super_admin": { bg: "rgba(245,158,11,.15)", txt: "#f59e0b" },
  "sub_admin":   { bg: "rgba(59,130,246,.15)", txt: "#60a5fa" },
  "staff":       { bg: "rgba(16,185,129,.15)", txt: "#34d399" },
  "user":        { bg: "rgba(139,92,246,.15)", txt: "#a78bfa" },
};