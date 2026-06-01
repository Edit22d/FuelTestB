import { useState } from "react";
import {
  LayoutDashboard, MapPin, Droplets, ShoppingCart, CreditCard,
  Users, Bell, Settings, User, Shield, ChevronDown, Sun, Moon,
  Activity, LogOut, Gauge, UserCog, ChevronRight, Search,
  TrendingUp, Zap, Menu, X, BarChart3, Package, AlertCircle
} from "lucide-react";
import { T, toggleTheme, toggleExpanded } from "./theme.js";
import { NAV, ROLE_COLORS } from "./config.js";

// ICON_MAP for string-based icon lookup (since CDN imports don't support named imports directly)
const ICON_MAP = {
  LayoutDashboard, MapPin, Droplets, ShoppingCart, CreditCard,
  Users, Bell, Settings, User, Shield, ChevronDown, Sun, Moon,
  Activity, LogOut, Gauge, UserCog, ChevronRight, Search,
  TrendingUp, Zap, Menu, X, BarChart3, Package, AlertCircle
};

/* ─── NavItem ─────────────────────────────────────────────────────────────── */
function NavItem({ item, theme, active, setActive, expanded, toggleExp, col }) {
  const [hov, setHov] = useState(false);
  const isAct = active === item.id || item.sub?.some(c => c.id === active);
  const isExp = expanded[item.id];
  const hasSub = item.sub?.length > 0;
  const C = T[theme];
  const Icon = ICON_MAP[item.icon];

  return (
    <div>
      <div
        className="nav-item"
        onMouseEnter={() => setHov(true)}
        onMouseLeave={() => setHov(false)}
        onClick={() => { setActive(item.id); if (hasSub) toggleExp(item.id); }}
        title={col ? item.label : ""}
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          gap: 9,
          padding: col ? "10px 0" : "8.5px 13px",
          margin: col ? "1px 10px" : "1px 8px",
          borderRadius: 8,
          justifyContent: col ? "center" : "flex-start",
          background: isAct ? C.sbAct : hov ? C.sbHov : "transparent",
          color: isAct ? C.sbTxtAct : hov ? C.sbTxtHov : C.sbTxt,
        }}
      >
        {isAct && !col && (
          <div style={{
            position: "absolute", left: -8, top: "22%", height: "56%",
            width: 3, background: C.sbBar, borderRadius: "0 3px 3px 0",
          }} />
        )}

        {Icon && <Icon size={15} strokeWidth={isAct ? 2.5 : 1.9} style={{ flexShrink: 0 }} />}

        {!col && (
          <>
            <span style={{
              flex: 1, fontSize: 13, fontWeight: isAct ? 600 : 400,
              fontFamily: "'DM Sans', sans-serif", letterSpacing: ".01em",
            }}>
              {item.label}
            </span>

            {item.count !== undefined && (
              <span className="badge" style={{
                fontSize: 10, fontWeight: 700, padding: "2px 7px",
                borderRadius: 10,
                background: item.cc ? `${item.cc}22` : "rgba(255,255,255,.07)",
                color: item.cc || C.sbTxt,
                letterSpacing: ".02em",
                fontFamily: "'DM Mono', monospace",
                animation: item.cc === "#f43f5e" ? "pulse-dot 2.2s ease infinite" : undefined,
              }}>
                {item.count}
              </span>
            )}

            {hasSub && (
              <ChevronDown
                size={12}
                className="chevron-rot"
                style={{
                  transform: isExp ? "rotate(0deg)" : "rotate(-90deg)",
                  opacity: 0.55,
                }}
              />
            )}
          </>
        )}

        {col && item.count !== undefined && (
          <div style={{
            position: "absolute", top: 3, right: 3,
            width: 7, height: 7, borderRadius: "50%",
            background: item.cc || C.sbTxt,
            animation: item.cc === "#f43f5e" ? "pulse-dot 2.2s ease infinite" : undefined,
          }} />
        )}
      </div>

      {hasSub && isExp && !col && (
        <div className="sub-list">
          {item.sub.map(ch => {
            const chAct = active === ch.id;
            const SubIcon = ICON_MAP[ch.icon];
            return (
              <div
                key={ch.id}
                className="nav-item"
                onClick={() => setActive(ch.id)}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "7px 13px 7px 38px",
                  margin: "1px 8px", borderRadius: 7, cursor: "pointer",
                  color: chAct ? C.sbTxtAct : C.sbTxt,
                  background: chAct ? C.sbAct : "transparent",
                  fontSize: 12.5, fontWeight: chAct ? 600 : 400,
                  fontFamily: "'DM Sans', sans-serif",
                }}
              >
                <div style={{
                  width: 5, height: 5, borderRadius: "50%", flexShrink: 0,
                  background: chAct ? C.sbBar : C.sbTxt,
                  opacity: chAct ? 1 : 0.45,
                }} />
                {ch.label}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── Fake Mini Bar Chart ─────────────────────────────────────────────────── */
function MiniBarChart({ theme }) {
  const C = T[theme];
  const bars = [62,78,55,88,70,82,58,94,72,86,65,90,76,84,68];
  const colors = [C.amber, C.teal, C.blue];
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 5, height: 100 }}>
      {bars.map((h, i) => (
        <div key={i} style={{
          flex: 1, height: `${h}%`, borderRadius: "3px 3px 0 0",
          background: colors[i % 3], opacity: 0.55 + (i % 3) * 0.1,
        }} />
      ))}
    </div>
  );
}

/* ─── Main Component ─────────────────────────────────────────────────────── */
export default function FuelConnect() {
  const [theme, setTheme] = useState("dark");
  const [col, setCol] = useState(false);
  const [active, setActive] = useState("dashboard");
  const [expanded, setExpanded] = useState({ users: true });

  const C = T[theme];
  const isDark = theme === "dark";

  const handleToggleTheme = () => setTheme(toggleTheme);
  const handleToggleExp = (id) => setExpanded(prev => toggleExpanded(prev, id));

  const activeLabel = (() => {
    for (const sec of NAV) {
      for (const item of sec.items) {
        if (item.id === active) return item.label;
        const ch = item.sub?.find(c => c.id === active);
        if (ch) return ch.label;
      }
    }
    return "Dashboard";
  })();

  const STATS = [
    { lbl: "Total Stations",  val: "12",       sub: "+2 this month",        icon: "MapPin",        color: C.amber, soft: C.amberS },
    { lbl: "Active Orders",   val: "47",        sub: "↑12 since yesterday",  icon: "ShoppingCart",  color: C.teal,  soft: C.tealS  },
    { lbl: "Revenue (MTD)",   val: "UGX 2.4M",  sub: "+8.2% vs last month",  icon: "TrendingUp",    color: C.green, soft: C.greenS },
    { lbl: "Pending Alerts",  val: "3",         sub: "2 critical",           icon: "AlertCircle",   color: C.red,   soft: C.redS   },
  ];

  const role = "super_admin"; // TODO: Replace with Django user role from context
  const rc = ROLE_COLORS[role];

  return (
    <div style={{ display: "flex", height: "100vh", background: C.bg, fontFamily: "'DM Sans', sans-serif", overflow: "hidden" }}>

      {/* ══ SIDEBAR ══════════════════════════════════════════════════════════ */}
      <aside
        className="sidebar-transition"
        style={{
          width: col ? 68 : 258, minWidth: col ? 68 : 258,
          background: C.sb,
          borderRight: `1px solid ${C.sbBdr}`,
          display: "flex", flexDirection: "column",
          overflow: "hidden", position: "relative", zIndex: 20,
        }}
      >
        {/* Brand */}
        <div style={{
          padding: "17px 15px", minHeight: 62,
          borderBottom: `1px solid ${C.sbBdr}`,
          display: "flex", alignItems: "center", gap: 11,
        }}>
          <div
            className="logo-icon"
            style={{
              width: 36, height: 36, borderRadius: 9,
              background: "linear-gradient(135deg,#f59e0b,#d97706)",
              display: "flex", alignItems: "center", justifyContent: "center",
              flexShrink: 0, cursor: "pointer",
            }}
          >
            <Zap size={17} color="#0d0f14" strokeWidth={2.8} />
          </div>

          {!col && (
            <div style={{ overflow: "hidden" }}>
              <div style={{
                fontFamily: "'Barlow Condensed', sans-serif",
                fontSize: 20, fontWeight: 800, letterSpacing: ".05em",
                color: "#eef0f6", lineHeight: 1, whiteSpace: "nowrap",
              }}>
                FUEL<span style={{ color: "#f59e0b" }}>CONNECT</span>
              </div>
              <div style={{
                fontFamily: "'DM Mono', monospace",
                fontSize: 9, color: C.secLbl,
                letterSpacing: ".16em", textTransform: "uppercase", marginTop: 3,
              }}>
                Management Portal
              </div>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, overflowY: "auto", overflowX: "hidden", padding: "5px 0 10px" }}>
          {NAV.map((sec, si) => (
            <div key={sec.s} style={{ marginBottom: 2 }}>
              {!col ? (
                <div style={{
                  padding: "13px 20px 4px",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: 9.5, fontWeight: 500, color: C.secLbl,
                  letterSpacing: ".15em", textTransform: "uppercase",
                }}>
                  {sec.s}
                </div>
              ) : si > 0 && (
                <div style={{ height: 1, margin: "7px 12px", background: C.divider }} />
              )}

              {sec.items.map(item => (
                <NavItem
                  key={item.id} item={item} theme={theme}
                  active={active} setActive={setActive}
                  expanded={expanded} toggleExp={handleToggleExp} col={col}
                />
              ))}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div style={{
          borderTop: `1px solid ${C.sbBdr}`,
          padding: col ? "10px 8px 12px" : "10px 9px 12px",
        }}>
          <button
            onClick={handleToggleTheme}
            style={{
              width: "100%",
              padding: col ? "8px 0" : "7px 10px",
              marginBottom: 9,
              background: C.themeBtn,
              border: `1px solid ${C.sbBdr}`,
              borderRadius: 8, cursor: "pointer",
              display: "flex", alignItems: "center",
              justifyContent: col ? "center" : "flex-start",
              gap: 9, color: C.sbTxt,
              fontFamily: "'DM Sans', sans-serif",
            }}
          >
            {isDark ? <Sun size={14} strokeWidth={2} /> : <Moon size={14} strokeWidth={2} />}
            {!col && (
              <span style={{ fontSize: 12, fontWeight: 500 }}>
                {isDark ? "Switch to Light" : "Switch to Dark"}
              </span>
            )}
          </button>

          <div style={{
            padding: col ? "8px 0" : "9px 10px",
            background: C.userBg,
            border: `1px solid ${C.userBdr}`,
            borderRadius: 10,
            display: "flex", alignItems: "center",
            gap: 10,
            justifyContent: col ? "center" : "flex-start",
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: "50%",
              background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 11.5, fontWeight: 700, color: "#fff",
              flexShrink: 0, letterSpacing: ".04em",
            }}>
              {{ user_initials|default:"JD" }}
            </div>

            {!col && (
              <>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: 12.5, fontWeight: 600, color: "#c8d4e4",
                    whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                  }}>
                    {{ user_name|default:"John Doe" }}
                  </div>
                  <span style={{
                    display: "inline-block", marginTop: 2,
                    fontSize: 8.5, fontWeight: 700, letterSpacing: ".1em",
                    padding: "2px 6px", borderRadius: 4,
                    background: rc.bg, color: rc.txt,
                    textTransform: "uppercase",
                    fontFamily: "'DM Mono', monospace",
                  }}>
                    {{ user_role|default:"super_admin" }}
                  </span>
                </div>
                <LogOut size={13} color={C.sbTxt} style={{ cursor: "pointer", flexShrink: 0, opacity: .65 }} />
              </>
            )}
          </div>
        </div>

        <button
          className="collapse-btn"
          onClick={() => setCol(c => !c)}
          style={{
            position: "absolute", top: 66, right: -11,
            width: 22, height: 22, borderRadius: "50%",
            background: C.sb,
            border: `1px solid ${C.sbBdr}`,
            cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: C.sbTxt, zIndex: 30,
            boxShadow: "0 2px 10px rgba(0,0,0,.35)",
          }}
        >
          <ChevronRight
            size={11}
            className="chevron-rot"
            style={{ transform: col ? "rotate(0deg)" : "rotate(180deg)" }}
          />
        </button>
      </aside>

      {/* ══ RIGHT COLUMN ═════════════════════════════════════════════════════ */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
        <header style={{
          height: 56, flexShrink: 0, zIndex: 10,
          background: C.hdrBg,
          borderBottom: `1px solid ${C.hdrBdr}`,
          backdropFilter: "blur(16px)",
          display: "flex", alignItems: "center",
          padding: "0 22px", gap: 14,
        }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{
              fontFamily: "'Barlow Condensed', sans-serif",
              fontSize: 19, fontWeight: 700, letterSpacing: ".04em",
              color: C.txt, lineHeight: 1.1,
            }}>
              {activeLabel}
            </div>
            <div style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 9.5, color: C.txtSec,
              letterSpacing: ".07em", marginTop: 1,
            }}>
              FUELCONNECT / {activeLabel.toUpperCase()}
            </div>
          </div>

          <div style={{
            display: "flex", alignItems: "center", gap: 8,
            background: C.input,
            border: `1px solid ${C.cardBdr}`,
            borderRadius: 8, padding: "7px 13px",
            width: 210, cursor: "text",
          }}>
            <Search size={13} color={C.txtSec} />
            <span style={{ fontSize: 12.5, color: C.txtSec, fontFamily: "'DM Sans', sans-serif" }}>
              Search anything…
            </span>
          </div>

          <div style={{ position: "relative", cursor: "pointer" }}>
            <div style={{
              width: 34, height: 34,
              background: C.input, border: `1px solid ${C.cardBdr}`,
              borderRadius: 8,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Bell size={15} color={C.txtSec} />
            </div>
            <div className="badge" style={{
              position: "absolute", top: -3, right: -3,
              width: 16, height: 16, borderRadius: "50%",
              background: C.red,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 9, fontWeight: 800, color: "#fff",
              border: `2px solid ${C.notifBdr}`,
            }}>
              3
            </div>
          </div>

          <div style={{
            width: 34, height: 34, borderRadius: "50%",
            background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 12, fontWeight: 700, color: "#fff", cursor: "pointer",
            border: `2px solid ${isDark ? "rgba(255,255,255,.1)" : "rgba(0,0,0,.08)"}`,
          }}>
            {{ user_initials|default:"JD" }}
          </div>
        </header>

        <main
          className={isDark ? "" : "sc"}
          style={{ flex: 1, overflow: "auto", padding: 22, background: C.bg }}
        >
          {/* Stat cards */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(4,1fr)",
            gap: 13, marginBottom: 18,
          }}>
            {STATS.map(s => {
              const StatIcon = ICON_MAP[s.icon];
              return (
                <div
                  key={s.lbl}
                  className="stat-card"
                  style={{
                    background: C.card,
                    border: `1px solid ${C.cardBdr}`,
                    borderRadius: 12, padding: "18px 19px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 13 }}>
                    <div style={{
                      fontSize: 11, fontWeight: 500, color: C.txtSec,
                      letterSpacing: ".03em", fontFamily: "'DM Sans', sans-serif",
                    }}>
                      {s.lbl}
                    </div>
                    <div style={{
                      width: 32, height: 32, borderRadius: 8,
                      background: s.soft,
                      display: "flex", alignItems: "center", justifyContent: "center",
                    }}>
                      {StatIcon && <StatIcon size={15} color={s.color} />}
                    </div>
                  </div>
                  <div style={{
                    fontFamily: "'Barlow Condensed', sans-serif",
                    fontSize: 28, fontWeight: 700,
                    color: C.txt, lineHeight: 1, letterSpacing: ".02em",
                  }}>
                    {s.val}
                  </div>
                  <div style={{ fontSize: 11, color: C.txtSec, marginTop: 6 }}>{s.sub}</div>
                </div>
              );
            })}
          </div>

          {/* Middle row: chart + orders */}
          <div style={{ display: "grid", gridTemplateColumns: "1.75fr 1fr", gap: 13, marginBottom: 13 }}>
            <div style={{
              background: C.card, border: `1px solid ${C.cardBdr}`,
              borderRadius: 12, padding: "19px 21px",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                <div>
                  <div style={{
                    fontFamily: "'Barlow Condensed', sans-serif",
                    fontSize: 14, fontWeight: 700, letterSpacing: ".06em",
                    color: C.txt,
                  }}>
                    REVENUE OVERVIEW
                  </div>
                  <div style={{ fontSize: 11, color: C.txtSec, marginTop: 2 }}>
                    Last 30 days · by fuel type
                  </div>
                </div>
                <div style={{
                  fontSize: 9.5, padding: "4px 10px", borderRadius: 6,
                  background: C.amberS, color: C.amber,
                  fontWeight: 700, letterSpacing: ".08em",
                  fontFamily: "'DM Mono', monospace",
                }}>
                  LIVE
                </div>
              </div>
              <MiniBarChart theme={theme} />
              <div style={{ display: "flex", gap: 16, marginTop: 12 }}>
                {[["Petrol", C.amber], ["Diesel", C.teal], ["Kerosene", C.blue]].map(([l, c]) => (
                  <div key={l} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                    <div style={{ width: 8, height: 8, borderRadius: 2, background: c, opacity: .75 }} />
                    <span style={{ fontSize: 11, color: C.txtSec }}>{l}</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{
              background: C.card, border: `1px solid ${C.cardBdr}`,
              borderRadius: 12, padding: "19px 20px",
              display: "flex", flexDirection: "column",
            }}>
              <div style={{
                fontFamily: "'Barlow Condensed', sans-serif",
                fontSize: 14, fontWeight: 700, letterSpacing: ".06em",
                color: C.txt, marginBottom: 3,
              }}>
                RECENT ORDERS
              </div>
              <div style={{ fontSize: 11, color: C.txtSec, marginBottom: 14 }}>Latest transactions</div>
              <div style={{ flex: 1 }}>
                {[
                  { id: "FC-1042", fuel: "Petrol 95",   amt: "UGX 84K",  status: "completed" },
                  { id: "FC-1041", fuel: "Diesel",       amt: "UGX 120K", status: "processing" },
                  { id: "FC-1040", fuel: "Petrol 95",   amt: "UGX 36K",  status: "completed" },
                  { id: "FC-1039", fuel: "Kerosene",    amt: "UGX 28K",  status: "completed" },
                ].map((o, i, arr) => (
                  <div key={o.id} style={{
                    display: "flex", alignItems: "center", gap: 10,
                    padding: "9px 0",
                    borderBottom: i < arr.length - 1 ? `1px solid ${C.cardBdr}` : "none",
                  }}>
                    <div style={{
                      width: 6, height: 6, borderRadius: "50%", flexShrink: 0,
                      background: o.status === "completed" ? C.green : C.amber,
                    }} />
                    <div style={{ flex: 1 }}>
                      <div style={{
                        fontSize: 12, fontWeight: 600, color: C.txt,
                        fontFamily: "'DM Mono', monospace",
                      }}>
                        {o.id}
                      </div>
                      <div style={{ fontSize: 10.5, color: C.txtSec }}>{o.fuel}</div>
                    </div>
                    <div style={{
                      fontSize: 12, fontWeight: 700,
                      color: o.status === "completed" ? C.green : C.amber,
                    }}>
                      {o.amt}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom row: 3 panels */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 13 }}>
            {[
              {
                hdr: "TOP STATIONS",
                rows: [
                  ["Kampala Central", "UGX 840K"],
                  ["Ntinda Branch",   "UGX 620K"],
                  ["Entebbe Rd",      "UGX 510K"],
                ],
                colored: false,
              },
              {
                hdr: "FUEL PRICE INDEX",
                rows: [
                  ["Petrol 95",  "UGX 4,850/L"],
                  ["Diesel",    "UGX 4,600/L"],
                  ["Kerosene",  "UGX 3,200/L"],
                ],
                colored: false,
              },
              {
                hdr: "QUICK ACTIONS",
                rows: [
                  ["＋ Add New Station", null],
                  ["＋ Create Order",   null],
                  ["⚙ Manage Staff",   null],
                ],
                colored: true,
              },
            ].map(panel => (
              <div key={panel.hdr} style={{
                background: C.card, border: `1px solid ${C.cardBdr}`,
                borderRadius: 12, padding: "17px 19px",
              }}>
                <div style={{
                  fontFamily: "'DM Mono', monospace",
                  fontSize: 9.5, fontWeight: 600, color: C.txtSec,
                  letterSpacing: ".13em", marginBottom: 13,
                }}>
                  {panel.hdr}
                </div>
                {panel.rows.map(([a, b], i) => (
                  <div key={i} style={{
                    display: "flex", alignItems: "center", gap: 8,
                    padding: "8px 0",
                    borderBottom: i < panel.rows.length - 1 ? `1px solid ${C.cardBdr}` : "none",
                    cursor: panel.colored ? "pointer" : "default",
                  }}>
                    <div style={{
                      width: 4, height: 4, borderRadius: "50%",
                      background: C.amber, flexShrink: 0,
                    }} />
                    <span style={{
                      flex: 1, fontSize: 12, color: panel.colored ? C.amber : C.txt,
                      fontFamily: "'DM Sans', sans-serif", fontWeight: panel.colored ? 500 : 400,
                    }}>
                      {a}
                    </span>
                    {b && (
                      <span style={{
                        fontSize: 11.5, fontWeight: 600, color: C.txtSec,
                        fontFamily: "'DM Mono', monospace",
                      }}>
                        {b}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>

          {/* Role badge legend */}
          <div style={{
            marginTop: 18,
            background: C.card,
            border: `1px solid ${C.cardBdr}`,
            borderRadius: 12, padding: "14px 19px",
            display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap",
          }}>
            <span style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 9.5, fontWeight: 600, color: C.txtSec,
              letterSpacing: ".13em", marginRight: 4,
            }}>
              RBAC ROLES
            </span>
            {[
              ["SUPER ADMIN", "rgba(245,158,11,.15)", "#f59e0b"],
              ["SUB ADMIN",   "rgba(59,130,246,.15)", "#60a5fa"],
              ["STAFF",       "rgba(16,185,129,.15)", "#34d399"],
              ["USER",        "rgba(139,92,246,.15)", "#a78bfa"],
            ].map(([lbl, bg, clr]) => (
              <span key={lbl} style={{
                fontSize: 9, fontWeight: 700, letterSpacing: ".1em",
                padding: "3px 8px", borderRadius: 5,
                background: bg, color: clr,
                fontFamily: "'DM Mono', monospace",
              }}>
                {lbl}
              </span>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}