// Mantém a colagem nativa e distribui códigos completos, inclusive autofill de SMS.
export function iniciarCodigoVerificacao(campos, aoAlterar) {
  const inputs = Array.from(campos);
  inputs.forEach((input, indice) => {
    input.addEventListener("input", () => {
      const digitos = input.value.replace(/\D/g, "");
      if (digitos.length > 1) distribuir(digitos, indice);
      else {
        input.value = digitos;
        if (digitos && indice < inputs.length - 1) inputs[indice + 1].focus();
        aoAlterar();
      }
    });
    input.addEventListener("keydown", evento => {
      if (evento.key === "Backspace" && !input.value && indice > 0) inputs[indice - 1].focus();
    });
    input.addEventListener("paste", evento => {
      const texto = evento.clipboardData?.getData("text") || "";
      const digitos = texto.replace(/\D/g, "");
      if (!digitos || input.disabled) return;
      setTimeout(() => { if (input.isConnected && !input.disabled) distribuir(digitos, indice); }, 0);
    });
  });
  function distribuir(texto, indice) {
    const inicio = texto.length >= inputs.length ? 0 : indice;
    const digitos = texto.slice(0, inputs.length - inicio);
    for (const [offset, digito] of [...digitos].entries()) inputs[inicio + offset].value = digito;
    inputs[Math.min(inicio + digitos.length, inputs.length - 1)].focus();
    aoAlterar();
  }
}
