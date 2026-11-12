
import { formatarReal } from "../utils/formatarMoeda.js";

const lojas = {mercado_livre: "Mercado Livre", shopee: "Shopee"};
const situacoes = {em_revisao: "Em revisão", pendente: "Pendente", rejeitado: "Rejeitada", importado: "Aceita"};
const categorias = {
  processador: "Processador", placa_mae: "Placa-mãe", placa_video: "Placa de vídeo", memoria_ram: "Memória RAM",
  ssd: "SSD", hd: "HD", fonte: "Fonte", gabinete: "Gabinete", water_cooler: "Water cooler", air_cooler: "Air cooler",
  fan: "Ventoinha", fone: "Fone", teclado: "Teclado", mouse: "Mouse", monitor: "Monitor",
  adaptador_wifi: "Adaptador Wi-Fi", cabo_rede: "Cabo de rede",
};

export const rotuloLoja = loja => lojas[loja] || String(loja || "");
export const rotuloSituacao = status => situacoes[status] || String(status || "");
export const rotuloCategoria = categoria => categorias[categoria] || String(categoria || "").replace(/_/g, " ");

export function formatarFaixaPreco(preco) {
  if (!preco || !Number.isFinite(preco.minimo)) return "Preço não informado";
  if (!Number.isFinite(preco.maximo) || preco.maximo === preco.minimo) return formatarReal(preco.minimo);
  return `${formatarReal(preco.minimo)} a ${formatarReal(preco.maximo)}`;
}


export function linkSeguro(url) {
  try {
    const endereco = new URL(url);
    return endereco.protocol === "https:" && !endereco.username && !endereco.password ? endereco.href : null;
  } catch { return null; }
}


export function candidatoSelecionavel(candidato) {

  return Array.isArray(candidato?.conflitos) && candidato.conflitos.length === 0 && !candidato.vinculada_a_outro_catalogo;
}

export function descreverCandidato(candidato) {
  const nome = [candidato.fabricante, candidato.modelo].filter(Boolean).join(" ") || candidato.peca;
  const codigo = candidato.part_number ? ` · ${candidato.part_number}` : "";
  const ficha = Array.isArray(candidato.ficha) && candidato.ficha.length ? ` — ${candidato.ficha.join(" · ")}` : "";
  return `${nome}${codigo}${ficha}`;
}

export function textoRestricoes(candidato) {
  const conflitos = (candidato.conflitos || []).map(c => String(c).replace(/_/g, " "));
  const pendencias = (candidato.pendencias || []).map(p => String(p).replace(/_/g, " "));
  return {conflitos, pendencias};
}
