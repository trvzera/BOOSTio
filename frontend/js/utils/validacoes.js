// Funções puras de validação. Sem fetch, sem DOM.

export function validarEmail(email) {
  const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regexEmail.test(email);
}

// Regras: mínimo 8 caracteres, 1 maiúscula, 1 número e 1 caractere especial.
export function validarSenha(senha) {
  const temTamanhoMinimo = senha.length >= 8;
  const temMaiuscula = /[A-Z]/.test(senha);
  const temNumero = /\d/.test(senha);
  const temEspecial = /[^a-zA-Z0-9]/.test(senha);

  return temTamanhoMinimo && temMaiuscula && temNumero && temEspecial;
}
