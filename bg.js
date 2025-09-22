// bg.js
"use strict";

const API_URL = "http://127.0.0.1:5000/run";
const API_KEY = "dev-secret";

const API = typeof browser !== "undefined" ? browser : chrome;

// Convert /analysis/game/live/123?tab=review -> https://www.chess.com/game/live/123
function canonReviewToGame(href = "") {
  try {
    const u = new URL(href);
    u.search = "";
    u.hash = "";
    u.pathname = u.pathname.replace(/^\/analysis\/game\//, "/game/");
    u.pathname = u.pathname.replace(/\/+$/, ""); // trim trailing slashes
    return u.origin + u.pathname;
  } catch {
    return href || "";
  }
}

async function postToFlask(link) {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": API_KEY
    },
    body: JSON.stringify({ link })
  });

  const text = await res.text();
  let found = false;
  let pgn = text;

  // Flask may return JSON { ok:true, found:true, pgn:"..." }
  try {
    const j = JSON.parse(text);
    if (j && typeof j === "object") {
      found = "found" in j ? Boolean(j.found) : Boolean(j.pgn);
      pgn = ("pgn" in j) ? (j.pgn || "") : text;
    }
  } catch {
    found = Boolean((text || "").trim());
  }

  return { status: res.status, text, found, pgn };
}

async function tryWithRetries(link, attempts = 3, delayMs = 500) {
  let last = null;
  for (let i = 0; i < attempts; i++) {
    last = await postToFlask(link);
    if (last.found && last.pgn) return last;
    if (i < attempts - 1) await new Promise(r => setTimeout(r, delayMs));
  }
  return last;
}

API.runtime.onMessage.addListener(async (msg, sender) => {
  // RUN_FLASK: prefer the *live arg* (from content script) FIRST to avoid SPA staleness
  if (msg?.type === "RUN_FLASK") {
    const arg = msg?.arg || msg?.link || "";
    const altLink = canonReviewToGame(arg);
    const primaryLink = sender?.tab?.url || "";

    // Try the canonicalized arg (fresh) first, then fall back to the tab URL if needed
    let result = null;
    if (altLink) {
      result = await tryWithRetries(altLink, 3, 500);
    }
    if ((!result?.found || !result.pgn) && primaryLink && primaryLink !== altLink) {
      result = await tryWithRetries(primaryLink, 3, 500);
    }

    // If we found PGN, open analysis and send pure PGN
    if (result?.found && result.pgn) {
      openAnalysisAndSendPGN(result.pgn).catch(e => console.error("[bg] open/send failed:", e));
    }

    // Return raw body to content script for its alert/log
    return { ok: Boolean(result), status: result?.status ?? 200, body: result?.text ?? "" };
  }

  // OPEN_TAB 
  if (msg?.type === "OPEN_TAB") {
    return API.tabs.create({ url: msg.url, active: Boolean(msg.active) });
  }
});

async function openAnalysisAndSendPGN(pgn) {
  const tab = await API.tabs.create({
    url: "https://wintrchess.com/analysis",
    active: true
  });

  // Wait for load (or 3s fallback) ,clean up the listener
  await new Promise(resolve => {
    const tid = tab.id;
    let done = false;

    function onUpd(id, info) {
      if (id !== tid) return;
      if (info.status === "complete") {
        API.tabs.onUpdated.removeListener(onUpd);
        done = true;
        resolve();
      }
    }

    API.tabs.onUpdated.addListener(onUpd);
    setTimeout(() => {
      if (!done) {
        try { API.tabs.onUpdated.removeListener(onUpd); } catch {}
        resolve();
      }
    }, 3000);
  });

  // Ping until inject.js replies (up to 6s)
  const deadline = Date.now() + 6000;
  while (Date.now() < deadline) {
    try {
      const pong = await API.tabs.sendMessage(tab.id, { type: "PING" });
      if (pong && pong.pong === true) break;
    } catch {
      // no listener yet
    }
    await new Promise(r => setTimeout(r, 200));
  }

  // Send pure PGN to the analysis tab
  try {
    await API.tabs.sendMessage(tab.id, { type: "INIT_PGN", pgn });
  } catch (err) {
    console.error("[bg] INIT_PGN send failed:", err);
  }
}
