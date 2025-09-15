console.log("button.js loaded");

// wait for the small green review button (with the extra class) INSIDE its wrapper
const interval = setInterval(() => {
  const target = document.querySelector(
    ".quick-analysis-loader-component .cc-button-component.cc-button-primary.cc-button-xx-large.cc-bg-primary.cc-button-full.quick-analysis-loader-background"
  );
  if (!target) return;

  clearInterval(interval);

  const wrapper = target.closest(".quick-analysis-loader-component");
  if (!wrapper) return;

  // avoid duplicates
  if (document.getElementById("my-extra-btn")) return;

  // create a sibling wrapper like the original, then our button inside it
  const myWrap = document.createElement("div");
  myWrap.className = "quick-analysis-loader-component";

  const myBtn = document.createElement("button");
  myBtn.id = "my-extra-btn";
  myBtn.textContent = "Free Review";

  myBtn.onclick = () => alert("I was clicked");

  myWrap.appendChild(myBtn);

  // insert the whole block directly AFTER the original wrapper
  wrapper.insertAdjacentElement("afterend", myWrap);

  console.log("Extra button block inserted right under the small green button");
}, 500);
