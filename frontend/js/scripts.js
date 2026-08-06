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

document.addEventListener("DOMContentLoaded", () => {
  const cardsGrid = document.getElementById("cards-grid");
  const cards = Array.from(document.querySelectorAll(".card-service"));
  const dots = Array.from(document.querySelectorAll(".scroll-dots .dot"));

  if (!cardsGrid || cards.length === 0) return;

  function isCarouselMode() {
    return getComputedStyle(cardsGrid).display === "flex";
  }

  function centerCard(card) {
    const target =
      card.offsetLeft + card.offsetWidth / 2 - cardsGrid.clientWidth / 2;
    cardsGrid.scrollTo({ left: target, behavior: "smooth" });
  }

  cards.forEach((card) => {
    card.addEventListener("click", () => {
      if (!isCarouselMode()) return;
      centerCard(card);
    });
  });

  dots.forEach((dot, index) => {
    dot.addEventListener("click", () => centerCard(cards[index]));
  });

  cardsGrid.addEventListener("scroll", updateActiveDot, { passive: true });

  function updateActiveDot() {
    if (!isCarouselMode() || dots.length === 0) return;
    const gridCenter = cardsGrid.scrollLeft + cardsGrid.clientWidth / 2;
    let closestIndex = 0;
    let closestDistance = Infinity;

    cards.forEach((card, index) => {
      const cardCenter = card.offsetLeft + card.offsetWidth / 2;
      const distance = Math.abs(cardCenter - gridCenter);
      if (distance < closestDistance) {
        closestDistance = distance;
        closestIndex = index;
      }
    });

    dots.forEach((dot, index) =>
      dot.classList.toggle("active", index === closestIndex),
    );
  }

  window.addEventListener("resize", updateActiveDot);
  updateActiveDot();
});
