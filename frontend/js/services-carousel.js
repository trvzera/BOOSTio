// Carrossel dos cards de serviço (só existe na página inicial, id "cards-grid").
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
