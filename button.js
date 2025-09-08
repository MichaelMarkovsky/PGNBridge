console.log("button.js loaded");

// keep checking until the target button exists
const interval = setInterval(() => {
  const target = document.querySelector(
    ".cc-button-component.cc-button-primary.cc-button-xx-large.cc-bg-primary.cc-button-full"
  );

  if (target) {
    clearInterval(interval);
    console.log("Found target button:", target);

    // avoid duplicates
    if (document.getElementById("my-extra-btn")) return;

    // make button
    const myBtn = document.createElement("button");
    myBtn.id = "my-extra-btn";
    myBtn.textContent = "My Extra Button";

    // what happens when clicked
    myBtn.onclick = () => alert("My button clicked!");

    // put it after the original button
    target.after(myBtn);
    console.log("Extra button added");
  }
}, 500);
