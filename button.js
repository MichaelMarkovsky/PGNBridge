const interval = setInterval(() => {
  const wrapper = document.querySelector(".game-over-modal-buttons");
  if (!wrapper) return;

  const reviewLink = wrapper.querySelector('a[href*="tab=review"]');
  if (!reviewLink) return;

  if (document.getElementById("my-extra-btn")) return;

  // keep interval running if you want reinjection on future games
  clearInterval(interval); 

  const myBtn = document.createElement("button");
  myBtn.id = "my-extra-btn";
  myBtn.textContent = "Free Review";


  // existing interval that finds .game-over-modal-buttons + review link ...
  myBtn.addEventListener("click", async () => {
    const original = myBtn.textContent;
    myBtn.disabled = true;
    myBtn.textContent = "Running..";
    try {
      const resp = await browser.runtime.sendMessage({
        type: "RUN_FLASK",
        arg: "hello-from-extension"
      });

      if (!resp || !resp.ok) {
        console.error("Background fetch error:", resp?.error);
        alert("Request failed. See console for details.");
      } else {
        console.log("status:", resp.status);
        console.log("raw response:", resp.body);
        alert(resp.body);
      }
    } catch (e) {
      console.error("Messaging failed:", e);
      alert("Messaging failed. See console for details.");
    } finally {
      myBtn.disabled = false;
      myBtn.textContent = original;
    }
  });


  reviewLink.insertAdjacentElement("afterend", myBtn);
  console.log("Extra button inserted right after the review link");
}, 500);
