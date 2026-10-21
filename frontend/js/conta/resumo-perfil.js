const reais = new Intl.NumberFormat("pt-BR",{style:"currency",currency:"BRL"});

export function textoBuildsSalvas(builds) {
  if (!Array.isArray(builds)) throw new Error("Não foi possível consultar suas builds.");
  return builds.length + (builds.length === 1 ? " build salva" : " builds salvas");
}

export function textoBudgetPerfil(usuario) {
  if (!usuario || !Number.isInteger(usuario.id) || usuario.id <= 0) return "Budget indisponível";
  if (usuario.budget == null) return "Budget não definido";
  const valor = usuario.budget;
  if (typeof valor !== "number" || !Number.isFinite(valor) || valor < 0 || valor > 1000000) return "Budget indisponível";
  return "Budget: " + reais.format(valor);
}
