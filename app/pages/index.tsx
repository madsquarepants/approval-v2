import { useState } from "react";
import { api } from "../lib/api";

export default function Home() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [out, setOut] = useState<string>("");

  const log = (v: any) => setOut(typeof v === "string" ? v : JSON.stringify(v, null, 2));

  const signup = async () => {
    try {
      const data = await api("/auth/signup", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      log(data);
    } catch (e: any) {
      log(`SIGNUP ERROR: ${e?.message || e}`);
    }
  };

  const login = async () => {
    try {
      const data = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      log(data);
      if (data?.access_token) localStorage.setItem("token", data.access_token);
    } catch (e: any) {
      log(`LOGIN ERROR: ${e?.message || e}`);
    }
  };

  return (
    <main style={{ maxWidth: 520, margin: "48px auto", fontFamily: "system-ui" }}>
      <h1>Approval — Sign In</h1>
      <div style={{ display: "grid", gap: 8 }}>
        <label>Email</label>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          style={{ padding: 8, border: "1px solid #ddd", borderRadius: 8 }}
        />
        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          style={{ padding: 8, border: "1px solid #ddd", borderRadius: 8 }}
        />
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button type="button" onClick={signup}>Sign Up</button>
          <button type="button" onClick={login}>Log In</button>
        </div>
      </div>

      <pre style={{ marginTop: 16, background: "#f8fafc", padding: 12, borderRadius: 8, whiteSpace: "pre-wrap" }}>
        {out || "Results will appear here…"}
      </pre>
    </main>
  );
}
