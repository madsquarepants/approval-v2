import { useEffect, useState } from "react";
import { api } from "../lib/api";

export default function Activity() {
  const [items, setItems] = useState<any[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("token");
    if (!t) { setErr("Please sign in first."); return; }
    api("/events/", {}, t).then(setItems).catch(e => setErr(e.message));
  }, []);

  return (
    <main style={{ maxWidth: 720, margin: "48px auto", fontFamily: "system-ui" }}>
      <h1>Activity</h1>
      {err && <p style={{color:"crimson"}}>{err}</p>}
      <ul style={{ listStyle: "none", padding: 0 }}>
        {items.map((it) => (
          <li key={it.id} style={{ padding: "10px 12px", borderBottom: "1px solid #eee" }}>
            <div style={{ fontWeight: 600 }}>{it.message}</div>
            <div style={{ fontSize: 12, color: "#666" }}>{new Date(it.created_at).toLocaleString()} • {it.type}</div>
          </li>
        ))}
        {items.length === 0 && !err && <p>No activity yet.</p>}
      </ul>
    </main>
  );
}
