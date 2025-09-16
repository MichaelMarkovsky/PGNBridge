console.log("button.js loaded");

// check every 500ms until i find the review link
const interval = setInterval(() => {
  const wrapper = document.querySelector(".game-over-modal-buttons");
  if (!wrapper) return;

  const reviewLink = wrapper.querySelector('a[href*="tab=review"]');
  if (!reviewLink) return;

  // avoid duplicates
  if (document.getElementById("my-extra-btn")) return;

  clearInterval(interval);

  // create button
  const myBtn = document.createElement("button");
  myBtn.id = "my-extra-btn";
  myBtn.textContent = "Free Review";
  myBtn.onclick = () => alert("I was clicked");

  // insert right after the existing review link
  reviewLink.insertAdjacentElement("afterend", myBtn);

  console.log("Extra button inserted right after the review link");
}, 500);
