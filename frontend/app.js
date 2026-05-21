const BASE_URL = "https://api.billbridge.in/v1";

const snippets = {
  signupCmd: [
    `curl -X POST ${BASE_URL}/onboarding/signup \\`,
    `  -H "Content-Type: application/json" \\`,
    `  -d '{"account_name":"acme","username":"owner","email":"owner@acme.com","password":"replace-me-123"}'`,
  ].join("\n"),
  balanceCmd: [
    `curl -X GET ${BASE_URL}/credits/balance \\`,
    `  -H "X-API-Key: YOUR_API_KEY"`,
  ].join("\n"),
  usageCmd: [
    `curl -X POST ${BASE_URL}/usage/record \\`,
    `  -H "X-API-Key: YOUR_API_KEY" \\`,
    `  -H "Content-Type: application/json" \\`,
    `  -d '{"event_id":"evt_001","model":"gpt-4.1","input_token":1200,"output_token":600}'`,
    ``,
    `curl -X POST ${BASE_URL}/payments/topup-intent \\`,
    `  -H "X-API-Key: YOUR_API_KEY" \\`,
    `  -H "Idempotency-Key: your-idempotency-key" \\`,
    `  -H "Content-Type: application/json" \\`,
    `  -d '{"credits":5000}'`,
    ``,
    `curl -X POST ${BASE_URL}/api-keys \\`,
    `  -H "X-API-Key: YOUR_API_KEY" \\`,
    `  -H "Content-Type: application/json" \\`,
    `  -d '{"name":"prod-key"}'`,
  ].join("\n"),
  topupCmd: [
    `curl -X POST ${BASE_URL}/payments/topup-intent \\`,
    `  -H "X-API-Key: YOUR_API_KEY" \\`,
    `  -H "Idempotency-Key: your-idempotency-key" \\`,
    `  -H "Content-Type: application/json" \\`,
    `  -d '{"credits":5000}'`,
  ].join("\n"),
  webhookNote: [
    `Webhook endpoint:`,
    `POST /v1/webhooks/stripe`,
    ``,
    `Stripe event:`,
    `payment_intent.succeeded`,
    ``,
    `Result:`,
    `Credits applied idempotently to customer wallet.`,
  ].join("\n"),
  sdkCmd: [
    `# Python`,
    `pip install billbridge-ai-credit-sdk`,
    ``,
    `from ai_credit_sdk.client import AICreditClient`,
    `client = AICreditClient(api_key="<your_api_key>", base_url="${BASE_URL}")`,
    `print(client.credits.balance())`,
    ``,
    `# Node`,
    `npm install billbridge-ai-credit-sdk`,
    ``,
    `import { AICreditClient } from "billbridge-ai-credit-sdk";`,
    `const client = new AICreditClient({ apiKey: process.env.AI_CREDIT_API_KEY, baseUrl: "${BASE_URL}" });`,
    `const balance = await client.credits.balance();`,
    `console.log(balance);`,
  ].join("\n"),
};

for (const [id, value] of Object.entries(snippets)) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

const baseUrlLabel = document.getElementById("baseUrlLabel");
if (baseUrlLabel) baseUrlLabel.textContent = BASE_URL;

for (const btn of document.querySelectorAll(".copy")) {
  btn.addEventListener("click", async () => {
    const targetId = btn.getAttribute("data-copy");
    if (!targetId) return;
    const target = document.getElementById(targetId);
    if (!target) return;
    try {
      const text = target.textContent || "";
      if (!navigator.clipboard || !navigator.clipboard.writeText) {
        throw new Error("clipboard_unavailable");
      }
      await navigator.clipboard.writeText(text);
      const old = btn.textContent;
      btn.textContent = "Copied";
      setTimeout(() => {
        btn.textContent = old || "Copy";
      }, 1200);
    } catch {
      const text = target.textContent || "";
      window.prompt("Copy this command:", text);
      btn.textContent = "Manual Copy";
      setTimeout(() => {
        btn.textContent = "Copy";
      }, 1200);
    }
  });
}

const year = document.getElementById("year");
if (year) year.textContent = String(new Date().getFullYear());
