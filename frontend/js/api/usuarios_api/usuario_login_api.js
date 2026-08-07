export async function logar_usuario(email,senha) {
  const response = await fetch('http://127.0.0.1:5000/usuarios/entrar', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      "email":email,
      "senha":senha
    })
  });
  
  const resultado = await response.json();
  
  return resultado
}