import { useEffect, useState } from "react";
import Router from "next/router";
import { api } from "../lib/api";
import { usePlaidLink } from "react-plaid-link";

export default function Home() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [openWhenReady, setOpenWhenReady] = useState(false);

  const { open, ready } = usePlaidLink({
    token: linkToken || "",
    onSuccess: async (public_token) => {
      // 1) exchange token, 2) (still) fake scan, 3) dashboard
      await api("/plaid/exchange", { method: "POST", body: JSON.stringify({ public_token }) }, token!);
      await api("/subscriptions/scan_real", { method: "POST" }, token!);
      Router.push("/dashboard");
    },
    onExit: () => setMsg("Plaid closed."),
  });

  useEffect(() => {
    if (openWhenReady && ready) open();
  }, [openWhenReady, ready, open]);

  const startAuth = async (mode: "signup" | "login") => {
    setMsg(null);
    const data = await api(`/auth/${mode}`, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    const t = data.access_token as string;
    localStorage.setItem("token", t);
    setToken(t);
  };

  const connectBank = async () => {
    if (!token) { setMsg("Please sign up or log in first."); return; }
    const res = await api("/plaid/link_token", { method: "POST" }, token);
    setLinkToken(res.link_token);
    setOpenWhenReady(true); // auto-opens Link once SDK is ready
  };

  return (
    <main style={{ maxWidth: 480, margin: "72px auto", fontFamily: "system-ui" }}>
      <h1>Approval v2 — Onboarding</h1>
      <p>1) Sign up or log in → 2) Connect bank via Plaid → 3) We’ll scan and show your subs.</p>

      <label>Email</label>
      <input value={email} onChange={e=>setEmail(e.target.value)} style={{ width:"100%", padding:8, marginBottom:8 }} />
      <label>Password</label>
      <input type="password" value={password} onChange={e=>setPassword(e.target.value)} style={{ width:"100%", padding:8, marginBottom:16 }} />

      {!token ? (
        <>
          <button onClick={()=>startAuth("signup")} style={{ padding:"10px 16px", marginRight:8 }}>Sign Up</button>
          <button onClick={()=>startAuth("login")} style={{ padding:"10px 16px" }}>Log In</button>
        </>
      ) : (
        <button onClick={connectBank} style={{ padding:"10px 16px" }}>Connect bank (Plaid)</button>
      )}

      {msg && <p style={{ color:"crimson" }}>{msg}</p>}
    </main>
  );
}
