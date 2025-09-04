// app/pages/index.tsx
import { useState } from "react";
import { api } from "../lib/api";

export default function Home() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [out, setOut] = useState<string>("");

  const log = (v: any) => setOut(typeof v === "string" ? v : JSON.stringify(v, null, 2));

  async function doAuth(mode: "signup" | "login") {
    try {
      const data = await api(`/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (data?.access_token) {
        localStorage.setItem("token", data.access_token);
        window.location.href = "/dashboard"; // simple, reliable redirect
      } else {
        log(data);
      }
    } catch (e: any) {
      log(`${mode.toUpperCase()} ERROR: ${e?.message || e}`);
    }
  }

  return (
    <main style={{ maxWidth: 520, margin: "48px auto", fontFamily: "system-ui" }}>
      <h1>Approval — Sign In</h1>
      <div style={{ display: "grid", gap: 8 }}>
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com"
               style={{ padding: 8, border: "1px solid #ddd", borderRadius: 8 }} />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
               placeholder="••••••••" style={{ padding: 8, border: "1px solid #ddd", borderRadius: 8 }} />
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button type="button" onClick={() => doAuth("signup")}>Sign Up</button>
          <button type="button" onClick={() => doAuth("login")}>Log In</button>
        </div>
      </div>
      {out && (
        <pre style={{ marginTop: 16, background: "#f8fafc", padding: 12, borderRadius: 8, whiteSpace: "pre-wrap" }}>
          {out}
        </pre>
      )}
    </main>
  );
}
