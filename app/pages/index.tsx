import { useState } from "react";
import { api } from "../lib/api";

export default function Home() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string>("");

  async function doAuth(mode: "signup" | "login") {
    setErr("");
    try {
      const data = await api(`/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (data?.access_token) {
        localStorage.setItem("token", data.access_token);
        window.location.href = "/dashboard"; // redirect
      } else {
        setErr("Unexpected response. Try Log In.");
      }
    } catch (e: any) {
      setErr(e?.message || "Auth failed");
    }
  }

  return (
    <main style={{ maxWidth: 520, margin: "48px auto", fontFamily: "system-ui" }}>
      <h1>Approval — Sign In</h1>
      <div style={{ display: "grid", gap: 8 }}>
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)}
               placeholder="you@example.com"
               style={{ padding: 8, border: "1px solid #ddd", borderRadius: 8 }} />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
               placeholder="••••••••"
               style={{ padding: 8, border: "1px solid #ddd", borderRadius: 8 }} />
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button type="button" onClick={() => doAuth("signup")}>Sign Up</button>
          <button type="button" onClick={() => doAuth("login")}>Log In</button>
        </div>
        {err && <p style={{ color:"crimson", marginTop: 8 }}>{err}</p>}
      </div>
    </main>
  );
}
