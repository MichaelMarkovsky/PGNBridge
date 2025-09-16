// bg.js
browser.runtime.onMessage.addListener(async (msg) => {
  if (msg?.type !== "RUN_FLASK") return;

  try {
    const res = await fetch("http://127.0.0.1:5000/run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Api-Key": "dev-secret"
      },
      body: JSON.stringify({ arg: msg.arg ?? "" })
    });
    const text = await res.text(); // return raw so we can show errors plainly
    return { ok: true, status: res.status, body: text };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});
