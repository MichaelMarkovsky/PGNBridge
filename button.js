// button.js - chess.com
"use strict";

(function () {
  if (window.__FREE_REVIEW_BUTTON__) return;
  window.__FREE_REVIEW_BUTTON__ = true;

  const API = typeof browser !== "undefined" ? browser : chrome;
  const WRAP_SEL = ".game-over-modal-buttons";
  const REVIEW_SEL = 'a[href*="tab=review"]';
  const BTN_ID = "my-extra-btn";

  function getCurrentReviewHref() {
    const wrapper = document.querySelector(WRAP_SEL);
    const a = wrapper && wrapper.querySelector(REVIEW_SEL);
    return a ? a.href : null;
  }

  async function startFlask() {
    try {
      const r = await API.runtime.sendMessage({ type: "START_FLASK" });
      if (!r?.ok) throw new Error(r?.message || "failed to start");
      return true;
    } catch (e) {
      console.error("[button] START_FLASK failed:", e);
      return false;
    }
  }

  async function stopFlask() {
    try {
      const r = await API.runtime.sendMessage({ type: "STOP_FLASK" });
      if (!r?.ok) throw new Error(r?.message || "failed to stop");
      return true;
    } catch (e) {
      console.warn("[button] STOP_FLASK:", e);
      return false;
    }
  }

  function insertButton() {
    if (document.getElementById(BTN_ID)) return false;

    const wrapper = document.querySelector(WRAP_SEL);
    if (!wrapper) return false;

    const reviewLink = wrapper.querySelector(REVIEW_SEL);
    if (!reviewLink) return false;

    const myBtn = document.createElement("button");
    myBtn.id = BTN_ID;
    myBtn.textContent = "Free Review";

    myBtn.addEventListener("click", async () => {
      const original = myBtn.textContent;
      myBtn.disabled = true;
      myBtn.textContent = "Starting..";

      let serverStarted = false;

      try {
        serverStarted = await startFlask();
        if (!serverStarted) {
          alert("Could not start local server. Check background console.");
          return;
        }

        const liveHref = getCurrentReviewHref();
        if (!liveHref) {
          alert("Can't find current Review link yet. Try again in a second.");
          return;
        }

        myBtn.textContent = "Fetching..";
        const resp = await API.runtime.sendMessage({ type: "RUN_FLASK", arg: liveHref });

        if (!resp || !resp.ok) {
          console.error("[button] Background fetch error:", resp && resp.error);
          alert("Request failed. See console for details.");
          return;
        }

        let shown = resp.body || "";
        try {
          const j = JSON.parse(resp.body);
          if (j && typeof j === "object" && "pgn" in j) shown = j.pgn || "";
        } catch {}
        console.log("[button] status:", resp.status);
        console.log("[button] preview:", (shown || "").slice(0, 300));
        //alert(shown || "(empty)");
      } catch (e) {
        console.error("[button] Messaging failed:", e);
        alert("Messaging failed. See console for details.");
      } finally {
        if (serverStarted) {
          myBtn.textContent = "Stopping..";
          await stopFlask();
        }
        myBtn.disabled = false;
        myBtn.textContent = original;
      }
    });

    reviewLink.insertAdjacentElement("afterend", myBtn);
    console.log("[button] Extra button inserted next to the Review link");
    return true;
  }

  const interval = setInterval(() => {
    if (insertButton()) clearInterval(interval);
  }, 500);

  const obs = new MutationObserver(() => insertButton());
  obs.observe(document.documentElement || document.body, { childList: true, subtree: true });
})();
