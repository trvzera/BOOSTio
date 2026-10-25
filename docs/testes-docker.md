# Validação com Docker — 25/10/2026

## Escopo

Teste local em Docker Desktop, Linux ARM64, com as imagens reais dos Dockerfiles do projeto: Python 3.12/Gunicorn, Nginx, MySQL 8.4 e Redis 7. O Compose de produção foi validado com credenciais descartáveis. Para a execução, foi derivada uma stack separada (`boostio-validacao`), sem Traefik, com rede própria e portas vinculadas apenas a 127.0.0.1. Credenciais de Google, Gemini e e-mail eram fictícias. Nenhuma publicação foi realizada.

## Correções encontradas

- `deploy/nginx.conf`: `absolute_redirect off` faz o redirecionamento inicial usar `Location: /pages/index.html`, preservando o protocolo e a porta usados pelo cliente. Antes, o Nginx gerava uma URL HTTP absoluta com sua porta interna, causando falha no acesso local e podendo provocar passagem por HTTP atrás do Traefik.
- `backend/tests/services/test_limites_entrada.py`: o teste de HTTP 413 agora configura banco em memória e chave próprios; dependia implicitamente do `.env` privado da máquina e falhava na imagem limpa.
- `Dockerfile.api`: atualização explícita do pip herdado da imagem Python (25.0.1) para 26.2.2. A auditoria encontrou alertas conhecidos na versão antiga; a imagem corrigida passou na auditoria de pacotes Python. Não foi uma auditoria de todos os pacotes do sistema operacional/imagens MySQL, Redis e Nginx.

## Evidências

- Build das imagens API/frontend concluído.
- 784 testes do backend e 20 subtestes passaram no Linux/Python 3.12.
- 587 testes do frontend passaram.
- MySQL/Redis/API saudáveis, Nginx em execução.
- Esquema criado no MySQL vazio e catálogo populado pelo comando real.
- 34 verificações HTTP passaram: cadastro de duas contas, login/logout, senha inválida, sessão, atributos Secure/HttpOnly/SameSite dos cookies, CSRF, CORS, rejeição de Host inválido, limite do corpo HTTP, proibição de acesso a dados de outra conta, catálogo, orçamento, builds manuais, exigência de e-mail verificado e limite de três builds, exclusão e rate limit real no Redis.
- A verificação de e-mail da conta descartável foi habilitada diretamente no banco para testar builds sem disparar e-mails reais. Isso não valida a entrega de e-mail.
- 21 verificações Nginx/frontend passaram: páginas publicadas, configuração pública da API, bloqueio de `.env`/`.git`, ausência dos testes na imagem, manifesto vazio de imagens e redirecionamento inicial.
- 51 referências locais de páginas a imagens, fontes, scripts, estilos e links responderam sem falhas.
- Após recriar os quatro containers, contas e builds permaneceram; o limite do Redis também persistiu. Uma imagem de teste e o manifesto no volume compartilhado continuaram disponíveis pelo Nginx.
- Dump MySQL restaurado em banco separado: duas contas e duas builds recuperadas.
- Com Redis parado, `/health` respondeu HTTP 503 sem detalhes internos. Após reinício, voltou a HTTP 200.
- Auditoria dos pacotes Python da imagem corrigida: nenhuma vulnerabilidade conhecida encontrada.

## O que ainda exige validação de produção

O resultado aprova os fluxos locais exercitados; não certifica toda a segurança nem todas as integrações. Ainda faltam o Traefik real da VPS, DNS, certificados/HTTPS, comportamento dos cookies no navegador com os dois domínios, login Google com cliente válido, entrega/recuperação de e-mail, geração real com Gemini, consultas reais às lojas e os limites de recursos sob carga. A coleta de imagens/preços e as integrações de IA/benchmark são cobertas por testes automatizados, mas não foram executadas contra provedores reais nesta validação.

Também não foi executado um teste visual completo de todas as telas em navegadores/dispositivos nem um teste de invasão. As respostas HTTP dos atributos de cookies foram verificadas; o script de integração transportou os cookies explicitamente por HTTP interno para testar a API no modo produção sem desativar Secure.

Os containers de validação foram parados ao final; os volumes descartáveis foram preservados para inspeção. As correções ficaram no checkout, sem push nem deploy.

Arquivos temporários de execução e logs: `/tmp/boostio-validacao`. O arquivo de configuração de teste contém apenas segredos descartáveis e fica com permissão 600. Não use essa configuração em produção. Consulte `configuracao-producao.md` para implantar com as variáveis e o proxy reais.
