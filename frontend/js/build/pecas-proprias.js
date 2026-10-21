const tipos = {
  "placa-mae":"placa_mae", "placa-video":"placa_video", memoria:"memoria_ram",
  cooler:"air_cooler", "water-cooler":"water_cooler", fans:"fan", headset:"fone",
};

export function pecasPropriasFormulario(respostas) {
  const escolhidas = [...(respostas.pecas || []),...(respostas.perifericos === "alguns-perifericos" ? respostas.perifericosProprios || [] : [])];
  return Object.fromEntries(escolhidas.filter(peca => peca !== "nenhuma")
    .map(peca => [tipos[peca] || peca,respostas.pecasDetalhes?.[peca]?.trim()])
    .filter(([,modelo]) => modelo));
}
