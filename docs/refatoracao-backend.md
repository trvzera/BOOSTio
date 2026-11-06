# Refatoração incremental do backend

Base: código local anterior à reorganização, incluindo importadores, requisitos
mínimos e melhorias de associação que ainda não estavam commitados. O primeiro
commit preserva essa base; não representa mudanças de algoritmo da refatoração.
Snapshots externos, bancos, credenciais e anexos não fazem parte desse commit.

Etapas: 1 base de comparação; 2 controllers funcionais; 3 regras OAuth Google;
4 estado de builds; 5 contexto/catálogo/custos/prompts; 6 seleção de plataforma;
7 validações; 8 geração/aparência/persistência; 9 apresentação de peças;
10 ofertas/enriquecimento; 11 descoberta/worker/seed; 12 limpeza; 13 verificação.

Contratos congelados: hashes de quatro prompts, dados da seed e DDL de todas as
tabelas/índices para SQLite e MySQL. Testes de comportamento existentes continuam
obrigatórios. A comparação não chama IA nem APIs externas.
