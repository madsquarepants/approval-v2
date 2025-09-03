import { useEffect, useState } from "react";
import { api } from "../lib/api";
import SubscriptionList from "../components/SubscriptionList";
import UpcomingBanner from "../components/UpcomingBanner";

export default function Dashboard() {
  const [subs, setSubs] = useState<any[]>([]);
  const [upcoming, setUpcoming] = useState<any[]>([]);
  const [token, setToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadAll = async (t:string) => {
    const [s, u] = await Promise.all([
      api("/subscriptions", {}, t),
      api("/subscriptions/upcoming?days=7", {}, t),
    ]);
    setSubs(s); setUpcoming(u);
  };

  useEffect(() => {
    const t = localStorage.getItem("token");
    setToken(t);
    if (!t) { setError("No token. Please sign in."); return; }
    loadAll(t).catch(e => setError(e.message));
  }, []);

  return (
    <main style={{ maxWidth: 900, margin: "48px auto", fontFamily: "system-ui" }}>
      <h1>My Subscriptions</h1>
      <p><a href="/activity">View Activity</a></p>
      {error && <p style={{ color:"crimson" }}>{error}</p>}
      {token && <UpcomingBanner items={upcoming} token={token} onUpdate={(next)=>setSubs(next)} />}
      <SubscriptionList subs={subs} token={token!} onUpdate={(next)=>setSubs(next)} />
    </main>
  );
}
