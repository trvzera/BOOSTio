import "../header.js";
import "../auth/auth.js";

const erros = {
  403: {
    titulo: "Acesso não autorizado",
    descricao: "Você não tem permissão para acessar este conteúdo.",
  },
  404: {
    titulo: "Página não encontrada",
    descricao:
      "O endereço pode estar incorreto ou a página pode ter sido movida.",
  },
  500: {
    titulo: "Algo não saiu como esperado",
    descricao:
      "Ocorreu um erro inesperado. Tente novamente ou volte à página inicial.",
  },
};

const parametros = new URLSearchParams(window.location.search);
const codigoRecebido = Number(parametros.get("codigo"));
const codigo = erros[codigoRecebido] ? codigoRecebido : 500;
const erro = erros[codigo];

const codigoElemento = document.querySelector("#error-code");
const tituloElemento = document.querySelector("#error-title");
const descricaoElemento = document.querySelector("#error-description");

codigoElemento.textContent = codigo;
tituloElemento.textContent = erro.titulo;
descricaoElemento.textContent = erro.descricao;
document.title = `${codigo} — ${erro.titulo}`;
