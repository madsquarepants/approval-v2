// app/pages/dashboard.tsx
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

// ----- types -----
type Subscription = {
  id: number;
  merchant: string;
  plan?: string | null;
  price_cents?: number | null;
  amount_cents?: number | null;
  price?: number | string | null;
  amount?: number | string | null;
  interval?: string | null;      // "monthly", "yearly", etc.
  status?: string;               // legacy
  cancel_status?: string | null; // new: 'active' | 'in_progress' | 'canceled' | 'failed' | 'attention_needed'
  next_renewal_at?: string | null;
};

// ----- helpers -----
const toCents = (v: any): number | null => {
  if (v == null) return null;
  if (typeof v === "number") return v >= 1000 ? Math.round(v) : Math.round(v * 100);
  if (typeof v === "string") {
    const n = parseFloat(v.replace(/[^0-9.]/g, ""));
    return Number.isNaN(n) ? null : Math.round(n * 100);
  }
  return null;
};

const amountCents = (s: any): number | null =>
  toCents(s.price_cents) ??
  toCents(s.amount_cents) ??
  toCents(s.price) ??
  toCents(s.amount) ??
  toCents(s.plan_amount) ??
  null;

const prettyInterval = (x: any): string => {
  const v = (x || "").toString().toLowerCase();
  if (!v) return "";
  if (["mo", "mon", "month", "monthly"].includes(v)) return "month";
  if (["yr", "year", "yearly", "annual", "annually"].includes(v)) return "year";
  if (v.startsWith("week")) return "week";
  if (v.startsWith("day")) return "day";
  return v;
};

const fmtMoney = (cents?: number | null) =>
  typeof cents === "number" ? `$${(cents / 100).toFixed(2)}` : "";

// ----- page -----
export default function Dashboard() {
  const [token, setToken] = useState<string>("");
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string>("");

  // Load token + subscriptions
  useEffect(() => {
    const t = localStorage.getItem("token") || "";
    if (!t) { window.location.href = "/"; return; }
    setToken(t);
    loadSubs(t);
  }, []);

  async function loadSubs(t = token) {
    setLoading(true);
    setError("");
    try {
      const list = await api("/subscriptions", {}, t);
      setSubs(Array.isArray(list) ? list : []);
    } catch (e: any) {
      setError(e?.message || "Failed to load subscriptions.");
    } finally {
      setLoading(false);
    }
  }

  async function rescan() {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      await api("/subscriptions/scan_real", { method: "POST" }, token);
      await loadSubs();
    } catch (e: any) {
      setError(e?.message || "Rescan failed.");
      setLoading(false);
    }
  }

  async function decide(id: number, decision: "approve" | "deny") {
    if (!token) return;
    setBusyId(id);
    setError("");
    try {
      await api("/approvals", {
        method: "POST",
        body: JSON.stringify({ subscription_id: id, decision }),
      }, token);
      await loadSubs();
    } catch (e: any) {
      setError(e?.message || "Action failed.");
    } finally {
      setBusyId(null);
    }
  }

  async function startCancel(id: number) {
    if (!token) return;
    setBusyId(id);
    setError("");
    try {
      await api("/cancellations/start", {
        method: "POST",
        body: JSON.stringify({ subscription_id: id }),
      }, token);
      await loadSubs();
    } catch (e: any) {
      setError(e?.message || "Cancellation failed.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <main style={{ maxWidth: 900, margin: "48px auto", fontFamily: "system-ui" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <h1 style={{ fontSize: 42, lineHeight: 1.1, margin: 0 }}>My Subscriptions</h1>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Link href="/connect"><button type="button">Connect bank</button></Link>
          <button type="button" onClick={rescan} disabled={loading}>
            {loading ? "Scanning…" : "Rescan"}
          </button>
          <Link href="/activity"><button type="button">View Activity</button></Link>
        </div>
      </header>

      {/* build marker */}
      <div style={{ color: "#64748b", fontSize: 12, marginTop: 6 }}>build: dashboard-clean-v4</div>

      {error && <p style={{ color: "crimson", marginTop: 12 }}>{error}</p>}

      {loading && subs.length === 0 ? (
        <p style={{ marginTop: 16 }}>Loading…</p>
      ) : subs.length === 0 ? (
        <p style={{ marginTop: 24 }}>
          No subscriptions found yet.{" "}
          <Link href="/connect">Connect bank</Link> to get started.
        </p>
      ) : (
        <section style={{ display: "grid", gap: 16, marginTop: 24 }}>
          {subs.map((s) => {
            const cents = amountCents(s);
            const intv = prettyInterval(s.interval);
            const cStatus = (s as any).cancel_status || s.status || "active";
            return (
              <article key={s.id} style={{ border: "1px solid #e5e7eb", borderRadius: 12, padding: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "baseline" }}>
                  <div style={{ fontSize: 20, fontWeight: 600 }}>
                    {s.merchant}{s.plan ? ` — ${s.plan}` : ""}{" "}
                    {cents != null ? `${fmtMoney(cents)}${intv ? `/${intv}` : ""}` : ""}
                  </div>
                  <div style={{ color: "#475569" }}>
                    Status: <b>{cStatus}</b>
                    {s.next_renewal_at && (
                      <span> — next {new Date(s.next_renewal_at).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>

                <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
                  <button
                    type="button"
                    onClick={() => decide(s.id, "approve")}
                    disabled={busyId === s.id}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => decide(s.id, "deny")}
                    disabled={busyId === s.id}
                  >
                    Deny
                  </button>
                  <button
                    type="button"
                    onClick={() => startCancel(s.id)}
                    disabled={busyId === s.id || cStatus === "in_progress" || cStatus === "canceled"}
                  >
                    Start Cancellation
                  </button>
                </div>
              </article>
            );
          })}
        </section>
      )}
    </main>
  );
}
