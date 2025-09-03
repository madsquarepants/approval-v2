import { api } from "../lib/api";
import { useMemo } from "react";

export default function UpcomingBanner({
  items, token, onUpdate
}: { items:any[]; token:string; onUpdate:(s:any[])=>void }) {

  const formatDue = (iso?: string) => {
    if (!iso) return "soon";
    const d = new Date(iso);
    const days = Math.ceil((d.getTime() - Date.now()) / 86400000);
    if (days <= 0) return "today";
    if (days === 1) return "in 1 day";
    return `in ${days} days`;
  };

  const take = useMemo(() => items.slice(0, 5), [items]);

  const decide = async (id:number, decision:"approve"|"deny") => {
    await api(`/approvals/${id}`, { method:"POST", body: JSON.stringify({ decision }) }, token);
    const next = await api("/subscriptions", {}, token);
    onUpdate(next);
  };

  if (!items || items.length === 0) return null;

  return (
    <div style={{
      border: "1px solid #dbeafe",
      background: "#eff6ff",
      padding: 12,
      borderRadius: 8,
      marginBottom: 16
    }}>
      <b>{items.length} upcoming renewal{items.length>1?"s":""} in the next 7 days</b>
      <ul style={{ listStyle: "none", padding: 0, margin: "8px 0 0" }}>
        {take.map(s => (
          <li key={s.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 0" }}>
            <span style={{ minWidth: 160 }}>{s.merchant}</span>
            <span style={{ color: "#2563eb" }}>${s.amount}/{s.interval}</span>
            <span style={{ color: "#555" }}>• due {formatDue(s.next_renewal_at)}</span>
            <span style={{ marginLeft: "auto" }}>
              <button onClick={()=>decide(s.id,"approve")} style={{ marginRight: 8 }}>Approve</button>
              <button onClick={()=>decide(s.id,"deny")}>Deny</button>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

