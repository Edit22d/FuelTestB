/* ─── Themes ─────────────────────────────────────────────────────────────── */
export const T = {
  dark: {
    sb: "#0d0f14", sbBdr: "rgba(255,255,255,.06)", sbTxt: "#7e8fa3",
    sbTxtHov: "#c0cad8", sbTxtAct: "#fbbf24", sbHov: "rgba(255,255,255,.045)",
    sbAct: "rgba(251,191,36,.09)", sbBar: "#f59e0b", secLbl: "#3a4358",
    divider: "rgba(255,255,255,.05)",
    hdrBg: "rgba(13,15,20,.94)", hdrBdr: "rgba(255,255,255,.06)",
    bg: "#0b0c12", card: "#13151d", cardBdr: "rgba(255,255,255,.07)",
    txt: "#eef0f6", txtSec: "#4d5a6e", txtMut: "#252c3a",
    amber: "#f59e0b", amberS: "rgba(245,158,11,.13)",
    teal: "#14b8a6",  tealS: "rgba(20,184,166,.13)",
    red: "#f43f5e",   redS: "rgba(244,63,94,.13)",
    green: "#10b981", greenS: "rgba(16,185,129,.13)",
    blue: "#3b82f6",  blueS: "rgba(59,130,246,.13)",
    purple: "#8b5cf6",
    input: "rgba(255,255,255,.05)",
    userBg: "rgba(255,255,255,.04)", userBdr: "rgba(255,255,255,.08)",
    themeBtn: "rgba(255,255,255,.04)",
    notifBdr: "#0b0c12",
  },
  light: {
    sb: "#16192a", sbBdr: "rgba(255,255,255,.07)", sbTxt: "#7a8799",
    sbTxtHov: "#b0bacb", sbTxtAct: "#fbbf24", sbHov: "rgba(255,255,255,.05)",
    sbAct: "rgba(251,191,36,.1)", sbBar: "#f59e0b", secLbl: "#384056",
    divider: "rgba(255,255,255,.06)",
    hdrBg: "rgba(246,245,240,.94)", hdrBdr: "rgba(0,0,0,.08)",
    bg: "#f0efe9", card: "#ffffff", cardBdr: "rgba(0,0,0,.07)",
    txt: "#1a1f2e", txtSec: "#6a7588", txtMut: "#c0c8d4",
    amber: "#d97706", amberS: "rgba(217,119,6,.1)",
    teal: "#0d9488",  tealS: "rgba(13,148,136,.1)",
    red: "#e11d48",   redS: "rgba(225,29,72,.1)",
    green: "#059669", greenS: "rgba(5,150,105,.1)",
    blue: "#2563eb",  blueS: "rgba(37,99,235,.1)",
    purple: "#7c3aed",
    input: "rgba(0,0,0,.05)",
    userBg: "rgba(255,255,255,.06)", userBdr: "rgba(255,255,255,.1)",
    themeBtn: "rgba(255,255,255,.05)",
    notifBdr: "#f0efe9",
  }
};

export const toggleTheme = (current) => current === "dark" ? "light" : "dark";
export const toggleExpanded = (expanded, id) => ({ ...expanded, [id]: !expanded[id] });