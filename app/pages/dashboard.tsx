import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

type Subscription = {
  id: number;
  merchant: string;
  plan?: string | null;
  price_cents?: number | null;
  interval?: string | null;
  status: string;
  next_renewal_at?: string | null;
};

export default function Dashboard() {
  const [token, setToken] = useState<string>("");
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const t = localStorage.getItem("token") || "";
    if (!t) { window.location.href = "/"; return; }
    setToken(t);
    loadSubs(t);
  }, []);

  async function loadSubs(t: string) {
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
    try {
      await api("/subscriptions/scan_real", { method: "POST" }, token);
      await loadSubs(token);
    } catch (e: any) {
      setError(e?.message || "Rescan failed.");
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 760, margin: "48px auto", fontFamily: "system-ui" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <h1 style={{ fontSize: 48, lineHeight: 1.1, margin: 0 }}>My Subscriptions</h1>
        <div style={{ display: "flex", gap: 8 }}>
          {/* ALWAYS visible CTA */}
          <Link href="/connect"><button type="button">Connect bank</button></Link>
          <button type="button" onClick={rescan} disabled={loading}>
            {loading ? "Scanning…" : "Rescan"}
          </button>
          <Link href="/activity"><button type="button">View Activity</button></Link>
        </div>
      </header>

      {/* build marker so you know this file is live */}
      <div style={{ color: "#64748b", fontSize: 12, marginTop: 6 }}>build: connect-cta-1</div>

      {error && <p style={{ color: "crimson", marginTop: 12 }}>{error}</p>}

      {loading && subs.length === 0 ? (
        <p style={{ marginTop: 16 }}>Loading…</p>
      ) : subs.length === 0 ? (
        <p style={{ marginTop: 24 }}>
          No subscriptions found yet. <Link href="/connect">Connect bank</Link> to get started.
        </p>
      ) : (
        <section style={{ display: "grid", gap: 16, marginTop: 24 }}>
          {subs.map((s) => (
            <article key={s.id} style={{ border: "1px solid #eee", borderRadius: 12, padding: 16 }}>
              <div style={{ fontSize: 20, fontWeight: 600 }}>
                {s.merchant}{s.plan ? ` — ${s.plan}` : ""}{" "}
                {typeof s.price_cents === "number" ? `— $${(s.price_cents/100).toFixed(2)}` : ""}
                {s.interval ? `/${s.interval.replace("ly", "")}` : ""}
              </div>
              <div style={{ marginTop: 8, color: "#475569" }}>
                Status: <b>{s.status}</b>
                {s.next_renewal_at && <> — next renewal {new Date(s.next_renewal_at).toLocaleDateString()}</>}
              </div>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
