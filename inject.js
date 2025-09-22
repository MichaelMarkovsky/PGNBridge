// inject.js — wintrchess.com/analysis
(() => {
  if (window.__FREE_REVIEW_INJECTED__) return;
  window.__FREE_REVIEW_INJECTED__ = true;

  const API = typeof browser !== "undefined" ? browser : chrome;
  console.log("[inject] loaded");

  // ---------- utils ----------
  function reactSafeSet(el, value) {
    if (!el) return;
    const proto = Object.getPrototypeOf(el);
    const desc = proto && Object.getOwnPropertyDescriptor(proto, "value");
    const setter =
      (desc && desc.set) ||
      HTMLTextAreaElement.prototype.__lookupSetter__?.("value") ||
      HTMLInputElement.prototype.__lookupSetter__?.("value");
    if (setter) setter.call(el, value);
    else if ("value" in el) el.value = value;
    else el.textContent = value; // contenteditable/div fallback

    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // Deep query that pierces shadow roots (space-separated descendant selectors).
  function queryDeep(selector, root = document) {
    const parts = selector.split(" ").filter(Boolean);
    function search(nodes, idx) {
      if (idx >= parts.length) return nodes;
      const next = [];
      const sel = parts[idx];
      for (const node of nodes) {
        const scopes = [node];
        if (node.shadowRoot) scopes.push(node.shadowRoot);
        for (const scope of scopes) {
          if (!scope || !scope.querySelectorAll) continue;
          const found = scope.querySelectorAll(sel);
          for (const f of found) next.push(f);
        }
      }
      return search(next, idx + 1);
    }
    return search([root], 0)[0] || null;
  }

  function findDeep(selectors) {
    for (const s of selectors) {
      const el = queryDeep(s);
      if (el) return el;
    }
    return null;
  }

  function clickHard(el) {
    if (!el) return false;
    try {
      el.focus();
      el.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true, view: window }));
      el.dispatchEvent(new MouseEvent("mouseup",   { bubbles: true, cancelable: true, view: window }));
      el.dispatchEvent(new MouseEvent("click",     { bubbles: true, cancelable: true, view: window }));
      return true;
    } catch {
      try { el.click(); return true; } catch { return false; }
    }
  }

  function nearestButtonTo(el) {
    return (
      el.closest?.("form")?.querySelector("button, [role='button']") ||
      el.parentElement?.querySelector?.("button, [role='button']") ||
      document.querySelector("button, [role='button']")
    );
  }

  // ---------- selectors ----------
  const INPUT_CANDS = [
    "textarea#pgn",
    "textarea[name='pgn']",
    "textarea.pgn-textarea",
    "textarea",
    "[contenteditable='true']",
    "input[type='text']"
  ];

  // First candidate uses both classes without space
  const BUTTON_CANDS = [
    "button.rHBNQrpvd7mwKp3HqjVQ.qgX0SwOb9DIhILObqMfd",
    ".rHBNQrpvd7mwKp3HqjVQ.qgX0SwObqMfd",
    "button[data-action='analyze']",
    "button[type='submit']",
    "button"
  ];

  // Sticky reapply for a short window to survive re-renders.
  function makeStickyApply(getInput, value, ms = 4000) {
    const mo = new MutationObserver(() => {
      const el = getInput();
      if (!el) return;
      const cur = ("value" in el ? el.value : el.textContent) || "";
      if (cur !== value) reactSafeSet(el, value);
    });
    mo.observe(document, { childList: true, subtree: true });

    const iv = setInterval(() => {
      const el = getInput();
      if (!el) return;
      const cur = ("value" in el ? el.value : el.textContent) || "";
      if (cur !== value) reactSafeSet(el, value);
    }, 250);

    setTimeout(() => { mo.disconnect(); clearInterval(iv); }, ms);
  }

  // Single listener for everything (PING + INIT_PGN)
  API.runtime.onMessage.addListener(async (msg) => {
    if (!msg || typeof msg !== "object") return;

    if (msg.type === "PING") {
      return { pong: true };
    }

    if (msg.type !== "INIT_PGN") return;

    const pgn = msg.pgn || "";
    console.log("[inject] INIT_PGN len:", pgn.length);

    // 1) find input (with a short retry window)
    let input = findDeep(INPUT_CANDS);
    if (!input) {
      const deadline = Date.now() + 5000;
      while (!input && Date.now() < deadline) {
        await new Promise(r => setTimeout(r, 200));
        input = findDeep(INPUT_CANDS);
      }
    }
    if (!input) {
      console.warn("[inject] PGN input not found");
      // As an escape hatch, copy to clipboard so the user can paste.
      try { await navigator.clipboard.writeText(pgn); } catch {}
      return { ok: false, reason: "input-not-found" };
    }

    // 2) set PGN and keep sticky briefly
    reactSafeSet(input, pgn);
    makeStickyApply(() => findDeep(INPUT_CANDS), pgn, 4000);

    // 3) small pause to allow validation/enabling
    await new Promise(r => setTimeout(r, 300));

    // 4) find analyze button
    let btn = findDeep(BUTTON_CANDS) || nearestButtonTo(input);
    if (!btn) {
      console.warn("[inject] analyze button not found; trying form submit/Enter");
      const form = input.closest?.("form");
      if (form) {
        if (form.requestSubmit) form.requestSubmit(); else form.submit();
        return { ok: true, method: "form-submit" };
      }
      input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true }));
      input.dispatchEvent(new KeyboardEvent("keyup",   { key: "Enter", code: "Enter", bubbles: true }));
      return { ok: true, method: "enter-key" };
    }

    // Wait until enabled
    let tries = 30;
    while (tries-- > 0 && (btn.disabled || btn.getAttribute("aria-disabled") === "true")) {
      await new Promise(r => setTimeout(r, 100));
    }

    const ok = clickHard(btn);
    console.log("[inject] clicked analyze:", ok);
    return { ok, method: "button-click" };
  });
})();
