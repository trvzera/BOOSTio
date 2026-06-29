const container_profile = document.querySelector("#profile");
const profile_check = document.querySelector("#profile-check");

document.addEventListener("click", (e) => {
  if (!container_profile.contains(e.target)) {
    profile_check.checked = false;
  }
});
