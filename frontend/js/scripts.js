const container_profile = document.querySelector("#profile");
const profile_check = document.querySelector("#profile-check");

document.addEventListener("click", (e) => {
  if (!container_profile.contains(e.target)) {
    profile_check.checked = false;
  }
});


const burgerMenu = document.querySelector("#burger-menu");
const burgerCheck = document.querySelector("#burger-check");

document.addEventListener("click", (e) => {
  if (!burgerMenu.contains(e.target)) {
    burgerCheck.checked = false;
  }
});
