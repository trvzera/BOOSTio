# Prompt para o diagrama de classes da BOOSTio

Copie o texto abaixo para gerar a imagem. Confira os nomes, as heranças e as
multiplicidades da imagem antes de adicioná-la ao repositório: geradores de imagens
podem omitir texto ou trocar as pontas das relações.

---

Gere uma imagem de um diagrama de classes UML do domínio da BOOSTio, plataforma
de montagem de computadores em Python, Flask e SQLAlchemy.

Use fundo branco, texto escuro e azul nos títulos. Priorize legibilidade,
resolução alta, classes organizadas por área e linhas sem sobreposição. Mostre
atributos principais, métodos e multiplicidades. Não invente classes, tabelas
ou relacionamentos.

## Classes base

- ModeloBase «abstract»: id: Integer, criado_em: DateTime, atualizado_em: DateTime.
  Métodos: salvar(), deletar().
- Peca «abstract», herda ModeloBase: fabricante, modelo, part_number,
  consumo_energia, preco, preco_atualizado_em, esgotado, imagem_url, kabum_external.
  Métodos: buscar_por_id(), mostrar_pecas(), atualizar_preco(), to_catalogo().
- Periferico «abstract», herda Peca: conexao, iluminacao.

## Conta

- Usuario, herda ModeloBase: nome, email, senha, verificado, ativo, login_google,
  google_sub, versao_sessao, budget, usar_budget. Métodos: buscar_por_email(),
  atualizar_dados(), atualizar_budget(), desativar().
- Codigo, herda ModeloBase: usuario_id, codigo, email_destino, tentativas,
  data_expiracao, usado.
- TokenRecuperacao, herda ModeloBase: usuario_id, token_hash, email_destino,
  versao_sessao, data_expiracao, usado.

## Configurações

- Build, herda ModeloBase: usuario_id, nome, quantidade_ram, quantidade_ssd,
  quantidade_hd, quantidade_fan. Métodos: criar_gerada(), quantidade_de(),
  listar_por_usuario(), to_dict().
- BuildSalva, herda ModeloBase: usuario_id, build_original_id: Integer opcional
  e único, estado: JSON, LIMITE = 3. Métodos: verificar_espaco(), criar_limitada(),
  listar_por_usuario(), buscar(), buscar_publica(), validar_estado().
- Ao lado de BuildSalva, coloque uma nota: “estado armazena título, descrição,
  visibilidade, tranca, orçamento, componentes e quantidades; são dados JSON,
  não colunas individuais. Pode existir sem uma Build original.”

## Componentes: todos herdam Peca

- Processador: soquete, nucleo, thread, clockbase, clockmax, videointegrado, cooler.
- PlacaMae: socket, chipset, formato, tipo_memoria, quantidade_slots_ram,
  memoria_maxima_gb, quantidade_slots_m2.
- MemoriaRAM: capacidade_gb, ddr, frequencia_mhz, quantidade_pentes.
- PlacaVideo: memoria_gb, tipo_memoria, consumo_w, quantidade_fans.
- SSD: capacidade_gb, tipo, interface, formato.
- HD: capacidade_gb, velocidade_rpm, interface.
- Fonte: potencia_w, formato.
- Gabinete: formato, formatos_placa_mae, fans_inclusos, tamanho_max_gpu_mm,
  tamanho_max_cooler_mm.
- AirCooler: compatibilidade, dimensoes.
- WaterCooler: compatibilidade, tamanho_radiador_mm, quantidade_fans.
- Fan: tamanho_mm, quantidade, iluminacao.
- PlacaRede: interface, padrao_wifi, velocidade_mbps, bluetooth.
- CaboRede: categoria, comprimento_m, conector.

## Periféricos: herdam Periferico

- Monitor: tamanho_polegadas, resolucao, taxa_atualizacao_hz.
- Teclado: layout, switch, mecanico.
- Mouse: dpi_max, botoes, sensor.
- Fone: tipo, microfone, cancelamento_ruido.

## Relacionamentos

- Cada Build pertence a 1 Usuario; um Usuario possui 0..* Builds.
- Cada BuildSalva pertence a 1 Usuario; um Usuario possui 0..* BuildsSalvas.
  Nota: “limite de negócio: três configurações salvas por conta”.
- Uma BuildSalva referencia 0..1 Build original; uma Build possui 0..1
  BuildSalva associada.
- Cada Codigo e TokenRecuperacao pertence a 1 Usuario; um Usuario pode possuir
  0..* de cada.
- Cada Build referencia exatamente 1 Processador, PlacaMae, MemoriaRAM,
  Fonte e Gabinete.
- Cada Build referencia 0..1 de cada um dos demais componentes e periféricos.
- Cada componente pode ser referenciado por 0..* Builds.
- Nota: “Em Build, quantidades representam unidades do modelo referenciado.
  Em BuildSalva, o JSON também permite múltiplos modelos de RAM,
  armazenamento e fans.”

Use triângulo vazio para herança e associações simples para referências.
Não use composição, pois as peças do catálogo existem independentemente das
builds. Não desenhe relações SQL diretas entre BuildSalva e componentes:
nesse modelo, eles são referenciados dentro do JSON.

Título: “BOOSTio — Diagrama de classes do domínio”.
Não inclua Controllers, Services, APIs externas ou classes futuras: este é o
diagrama do domínio, não da arquitetura. Esta é uma seleção das entidades
de domínio e seus atributos principais, não todas as tabelas auxiliares.
