export class AICreditClient {
  constructor({ apiKey, baseUrl = process.env.AI_CREDIT_BASE_URL || "https://api.yourdomain.com/v1" }) {
    this.apiKey = apiKey || process.env.AI_CREDIT_API_KEY;
    this.baseUrl = baseUrl;
    this.usage = {
      record: (payload) => this._request("/usage/record", { method: "POST", body: payload }),
    };
    this.payments = {
      createTopupIntent: (payload) => this._request("/payments/topup-intent", { method: "POST", body: payload }),
    };
    this.credits = {
      balance: () => this._request("/credits/balance", { method: "GET" }),
      ledger: () => this._request("/credits/ledger", { method: "GET" }),
    };
  }

  async _request(path, { method, body }) {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": this.apiKey,
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      throw new Error(`API error ${response.status}: ${await response.text()}`);
    }
    return response.json();
  }
}
