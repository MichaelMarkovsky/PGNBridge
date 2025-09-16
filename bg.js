// bg.js
const API_URL = "http://127.0.0.1:5000/run";
const API_KEY = "dev-secret";

browser.runtime.onMessage.addListener(async (msg, sender) => {
  if (msg?.type !== "RUN_FLASK") return;

  // if link wasn't provided, fall back to the tab URL
  const link = msg.link || sender?.tab?.url || "";

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Api-Key": API_KEY
      },
      body: JSON.stringify({ link })  // send the link to Flask
    });
    const text = await res.text();
    return { ok: true, status: res.status, body: text };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});
