import { itensCategoria, informacoesRam } from "../build/estado.js";
import { avaliarBuild } from "../build/compatibilidade.js";
import { hardwareBenchmark, hardwareBlender, slugVideo } from "./hardware.js";

const bloquear = (codigo,motivo) => ({permitido:false,codigo,motivo});

function conferirMontagem(build,catalogo,{destino = "o FPS",ignorarGpu = false} = {}) {
  if (itensCategoria(build,"memoria_ram").some(item => !item || typeof item !== "object"))
    return bloquear("ram-nao-identificada","Revise os modelos e as quantidades de memória da build antes de consultar " + destino + ".");
  const ram = informacoesRam(build,catalogo);
  if (!ram.itens.length || ram.itens.some(({item,peca}) => !peca || !Number.isInteger(peca.capacidade_gb) || peca.capacidade_gb <= 0
    || !Number.isInteger(item.quantidade ?? 1) || (item.quantidade ?? 1) < 1 || (item.quantidade ?? 1) > 64)
    || !Number.isInteger(ram.capacidade) || ram.capacidade <= 0 || ram.capacidade > 4096)
    return bloquear("ram-nao-identificada","Identifique todas as memórias e suas quantidades para confirmar a RAM antes de consultar " + destino + ".");
  let avaliacao;
  try { avaliacao = avaliarBuild(build,catalogo); }
  catch { return bloquear("build-invalida","Revise os componentes e as quantidades da build antes de consultar " + destino + "."); }
  if (avaliacao.erros.length) return bloquear("incompativel","Resolva os conflitos de compatibilidade antes de consultar " + destino + ": " + avaliacao.erros.join(" "));
  const faltam = avaliacao.faltam.filter(nome => !ignorarGpu || nome !== "Placa de vídeo");
  if (faltam.length) return bloquear("build-incompleta","Complete a montagem antes de consultar " + destino + ". Falta adicionar: " + faltam.join(", ") + ".");
  return {permitido:true,memoriaGb:ram.capacidade};
}

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
  const base = conferirMontagem(build,catalogo);
  return base.permitido ? {...base,codigo:"disponivel",motivo:"",hardware} : base;
}

export function avaliarDisponibilidadeBlender(build,catalogo) {
  if (!build?.componentes || Array.isArray(build.componentes) || !Array.isArray(catalogo)) {
    const erro = bloquear("build-invalida","Abra uma build válida antes de consultar o Blender.");
    return {cpu:erro,gpu:erro};
  }
  const encontrar = tipo => catalogo.find(p => p?.categoria === tipo && p.id === itensCategoria(build,tipo)[0]?.id);
  const cpu = encontrar("processador"), gpu = encontrar("placa_video"), nomes = hardwareBlender(cpu,gpu);
  return Object.fromEntries(["cpu","gpu"].map(tipo => {
    const peca = tipo === "cpu" ? cpu : gpu;
    if (!peca) return [tipo,bloquear("dispositivo-nao-identificado",tipo === "cpu"
      ? "Identifique o processador no catálogo para consultar a renderização pela CPU."
      : "Identifique uma GPU dedicada para consultar a renderização pela GPU. O teste de CPU não exige uma GPU dedicada.")];
    if (!nomes[tipo]) return [tipo,bloquear("hardware-nao-suportado","Não conseguimos identificar o modelo exato desta " + tipo.toUpperCase() + " para o Blender. Confira o cadastro; isso ainda não confirma ausência de resultados na fonte.")];
    const base = conferirMontagem(build,catalogo,{destino:"o Blender",ignorarGpu:tipo === "cpu"});
    return [tipo,base.permitido ? {...base,codigo:"disponivel",motivo:"",dispositivo:nomes[tipo]} : base];
  }));
}

export function avaliarReferenciaGpu(build,catalogo) {
  const item = build?.componentes && itensCategoria(build,"placa_video")[0];
  const gpu = Array.isArray(catalogo) && catalogo.find(p=>p?.categoria === "placa_video" && p.id === item?.id);
  const slug = gpu && slugVideo(gpu);
  return slug ? {permitido:true,hardware:{gpu:slug}} : bloquear("gpu-nao-suportada","A referência também precisa de uma GPU com correspondência exata cadastrada.");
}

export function motivoRequisitosFps(ficha) {
  if (!ficha) return ""; // Sem ficha oficial, a estimativa não certifica os requisitos do jogo.
  if (ficha.ram?.atendeMinimo === false) return "A RAM da build está abaixo do mínimo deste jogo. Nenhum FPS foi consultado.";
  if (ficha.impedimentosMinimos?.length) return "A build não atende aos requisitos mínimos verificados: " + ficha.impedimentosMinimos.join(" ") + " Nenhum FPS foi consultado.";
  if (ficha.ram?.completa === false || ficha.ram?.status === "nao_informada")
    return "A RAM da build salva ainda não está totalmente identificada. Revise as memórias e salve a build antes de consultar o FPS.";
  return "";
}
