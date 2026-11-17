import { itensCategoria, informacoesRam } from "../build/estado.js";
import { avaliarBuild } from "../build/compatibilidade.js";
import { hardwareBenchmark } from "./hardware.js";

const bloquear = (codigo,motivo) => ({permitido:false,codigo,motivo});

// Regras de entrada da estimativa, sem confundir dados físicos pendentes com incompatibilidade.
export function avaliarDisponibilidadeFps(build,catalogo) {
  if (!build?.componentes || Array.isArray(build.componentes) || !Array.isArray(catalogo))
    return bloquear("build-invalida","Abra uma build válida antes de consultar o FPS.");
  const encontrar = categoria => catalogo.find(p => p?.categoria === categoria && p.id === itensCategoria(build,categoria)[0]?.id);
  const cpu = encontrar("processador"), gpu = encontrar("placa_video");
  if (!cpu) return bloquear("cpu-nao-identificada","Identifique o modelo do processador no catálogo para consultar o FPS desta build.");
  if (!gpu) return bloquear(cpu.videointegrado === true ? "video-integrado" : "gpu-nao-identificada",
    cpu.videointegrado === true
      ? "Esta build usa vídeo integrado. A integração atual de FPS ainda não oferece uma correspondência verificada para ele. Você pode consultar o Blender pelo processador."
      : "Adicione ou identifique a placa de vídeo da build para consultar o FPS. Peças próprias sem modelo confirmado não podem ser estimadas.");
  const hardware = hardwareBenchmark(cpu,gpu);
  if (hardware.motivo) return bloquear("hardware-nao-suportado",hardware.motivo);
  if (itensCategoria(build,"memoria_ram").some(item => !item || typeof item !== "object"))
    return bloquear("ram-nao-identificada","Revise os modelos e as quantidades de memória da build antes de consultar o FPS.");
  const ram = informacoesRam(build,catalogo);
  if (!ram.itens.length || ram.itens.some(({item,peca}) => !peca || !Number.isInteger(peca.capacidade_gb) || peca.capacidade_gb <= 0
    || !Number.isInteger(item.quantidade ?? 1) || (item.quantidade ?? 1) < 1 || (item.quantidade ?? 1) > 64)
    || !Number.isInteger(ram.capacidade) || ram.capacidade <= 0 || ram.capacidade > 4096)
    return bloquear("ram-nao-identificada","Identifique todas as memórias e suas quantidades para confirmar a RAM antes de consultar o FPS.");
  let avaliacao;
  try { avaliacao = avaliarBuild(build,catalogo); }
  catch { return bloquear("build-invalida","Revise os componentes e as quantidades da build antes de consultar o FPS."); }
  if (avaliacao.erros.length) return bloquear("incompativel","Resolva os conflitos de compatibilidade antes de consultar o FPS: " + avaliacao.erros.join(" "));
  if (avaliacao.faltam.length) return bloquear("build-incompleta","Complete a montagem antes de consultar o FPS. Falta adicionar: " + avaliacao.faltam.join(", ") + ".");
  return {permitido:true,codigo:"disponivel",motivo:"",hardware,memoriaGb:ram.capacidade};
}

export function motivoRequisitosFps(ficha) {
  if (!ficha) return ""; // Sem ficha oficial, a estimativa não certifica os requisitos do jogo.
  if (ficha.ram?.atendeMinimo === false) return "A RAM da build está abaixo do mínimo deste jogo. Nenhum FPS foi consultado.";
  if (ficha.impedimentosMinimos?.length) return "A build não atende aos requisitos mínimos verificados: " + ficha.impedimentosMinimos.join(" ") + " Nenhum FPS foi consultado.";
  if (ficha.ram?.completa === false || ficha.ram?.status === "nao_informada")
    return "A RAM da build salva ainda não está totalmente identificada. Revise as memórias e salve a build antes de consultar o FPS.";
  return "";
}
