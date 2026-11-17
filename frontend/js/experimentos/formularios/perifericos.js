export const MINIMO_PERCENTUAL_PERIFERICOS = 10;
export const MAXIMO_PERCENTUAL_PERIFERICOS = 40;

export const perifericosPreview = [
  ["monitor", "Monitor"],
  ["teclado", "Teclado"],
  ["mouse", "Mouse"],
  ["headset", "Headset / fone"],
];
export const acessoriosNotebook = [
  ...perifericosPreview,
  ["webcam", "Webcam externa"],
];
export function precisaPerifericos(tipo, respostas) {
  if (tipo === "notebook")
    return (
      respostas.perifericos === "escolher-extras" &&
      respostas.extrasNotebook?.length > 0
    );
  return (
    respostas.perifericos === "todos-perifericos" ||
    (respostas.perifericos === "alguns-perifericos" &&
      ((respostas.perifericosProprios || []).length <
        perifericosPreview.length ||
        respostas.incluirWebcam === true))
  );
}
export function percentualPreview(respostas, tipo = "pc") {
  return precisaPerifericos(tipo, respostas)
    ? respostas.percentualPerifericos
    : 0;
}
export function webcamSolicitada(tipo, respostas) {
  return tipo === "pc"
    ? respostas.perifericos !== "sem-perifericos" &&
        Boolean(respostas.perifericos) &&
        respostas.incluirWebcam === true
    : respostas.perifericos === "escolher-extras" &&
        respostas.extrasNotebook?.includes("webcam");
}
