const BASE_URL = "https://api.billbridge.in/v1";

const snippets = {
  signupCmd: [
    `# PowerShell`,
    `Invoke-RestMethod -Method POST -Uri "${BASE_URL}/onboarding/signup" -ContentType "application/json" -Body '{"account_name":"acme","username":"owner","email":"owner@acme.com","password":"replace-me-123"}'`,
  ].join("\n"),
  balanceCmd: [
    `Invoke-RestMethod -Method GET -Uri "${BASE_URL}/credits/balance" -Headers @{ "X-API-Key" = "<your_api_key>" }`,
  ].join("\n"),
  usageCmd: [
    `Invoke-RestMethod -Method POST -Uri "${BASE_URL}/usage/record" -Headers @{ "X-API-Key" = "<your_api_key>" } -ContentType "application/json" -Body '{"event_id":"evt_001","model":"gpt-4.1","input_token":1200,"output_token":600}'`,
    ``,
    `Invoke-RestMethod -Method POST -Uri "${BASE_URL}/payments/topup-intent" -Headers @{ "X-API-Key" = "<your_api_key>"; "Idempotency-Key" = "<uuid>" } -ContentType "application/json" -Body '{"credits":5000}'`,
    ``,
    `Invoke-RestMethod -Method POST -Uri "${BASE_URL}/api-keys" -Headers @{ "X-API-Key" = "<your_api_key>" } -ContentType "application/json" -Body '{"name":"prod-key"}'`,
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
