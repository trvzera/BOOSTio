const tipos = {
  "placa-mae":"placa_mae", "placa-video":"placa_video", memoria:"memoria_ram",
  cooler:"air_cooler", "water-cooler":"water_cooler", fans:"fan", headset:"fone",
};

export function pecasPropriasFormulario(respostas) {
  return Object.fromEntries((respostas.pecas || []).filter(peca => peca !== "nenhuma")
    .map(peca => [tipos[peca] || peca,respostas.pecasDetalhes?.[peca]?.trim()])
    .filter(([,modelo]) => modelo));
}
