import { api } from "../lib/api";
import { useState } from "react";

export default function SubscriptionList({ subs, token, onUpdate }: { subs:any[]; token:string; onUpdate:(s:any[])=>void }) {
  const [busy, setBusy] = useState<number | null>(null);

  const refresh = async () => {
    const next = await api("/subscriptions", {}, token);
    onUpdate(next);
    return next;
  };

  const decide = async (id:number, decision:"approve"|"deny") => {
    setBusy(id);
    await api(`/approvals/${id}`, { method:"POST", body: JSON.stringify({ decision }) }, token);
    await refresh();
    setBusy(null);
  };

  const cancel = async (id:number) => {
    setBusy(id);
    await api(`/cancellations/${id}`, { method:"POST" }, token); // schedules background completion
    // poll a few times for status change to "canceled"
    for (let i = 0; i < 6; i++) {
      await new Promise(r => setTimeout(r, 1200));
      const next = await refresh();
      const cur = next.find((s:any) => s.id === id);
      if (cur && (cur.status === "canceled" || cur.status === "paused")) break;
    }
    setBusy(null);
  };

  const disabled = (s:any) => busy === s.id;

  return (
    <div>
      {subs.length === 0 && <p>No subscriptions found yet.</p>}
      {subs.map(s => (
        <div key={s.id} style={{ border:"1px solid #eee", padding:12, marginBottom:12, borderRadius:8, opacity: disabled(s) ? 0.6 : 1 }}>
          <b>{s.merchant}</b> — {s.plan || "Plan"} — ${s.amount}/{s.interval}
          <div style={{ marginTop:8 }}>
            <button onClick={()=>decide(s.id, "approve")} disabled={disabled(s)} style={{ marginRight:8 }}>Approve</button>
            <button onClick={()=>decide(s.id, "deny")} disabled={disabled(s)} style={{ marginRight:8 }}>Deny</button>
            <button onClick={()=>cancel(s.id)} disabled={disabled(s)}>Start Cancellation</button>
          </div>
          <div style={{ marginTop:6, fontSize:12, color:"#666" }}>
            Status: {s.status}{disabled(s) ? " • working..." : ""}
          </div>
        </div>
      ))}
    </div>
  );
}
