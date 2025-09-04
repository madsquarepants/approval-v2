import Script from "next/script";
import { useState } from "react";
import { api } from "../lib/api";

export default function Connect() {
  const [err, setErr] = useState<string>("");

  const start = async () => {
    try {
      const t = localStorage.getItem("token") || "";
      if (!t) { window.location.href = "/"; return; }

      // 1) Create Link token from our API
      const { link_token } = await api("/plaid/link_token", { method: "POST" }, t);

      // 2) Open Plaid Link
      const handler = (window as any).Plaid.create({
        token: link_token,
        onSuccess: async (public_token: string) => {
          // 3) Exchange public_token -> access_token on server
          await api("/plaid/exchange", {
            method: "POST",
            body: JSON.stringify({ public_token }),
          }, t);

          // 4) Trigger a real scan to pull subs
          await api("/subscriptions/scan_real", { method: "POST" }, t);

          // 5) Go back to dashboard
          window.location.href = "/dashboard";
        },
        onExit: (e: any) => {
          if (e) setErr(e?.error_message || "Exited.");
        },
      });
      handler.open();
    } catch (e: any) {
      setErr(e?.message || "Something went wrong.");
    }
  };

  return (
    <main style={{ maxWidth: 520, margin: "48px auto", fontFamily: "system-ui" }}>
      <Script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js" strategy="afterInteractive" />
      <h1>Connect your bank</h1>
      <p>Click the button below, choose <b>First Platypus Bank</b> (Sandbox), and finish the flow.</p>
      <button type="button" onClick={start}>Connect bank</button>
      {err && <p style={{ color: "crimson", marginTop: 12 }}>{err}</p>}
    </main>
  );
}
