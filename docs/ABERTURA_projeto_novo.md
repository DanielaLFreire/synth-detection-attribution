# Abertura do projeto novo no Claude — o que levar e o que escrever

Preparado em 2026-09-16 no fechamento de `synth-detection-attribution`
(tag `v1.0-experimento-fechado`). Copie cada bloco para o campo indicado.

---

## A. Nome do projeto

`Aumento do CITRA com imagens reais públicas — atribuição causal`

## B. Descrição do projeto (campo "descrição", curto)

Experimento pré-registrado para responder: ao adicionar imagens reais e
anotadas de datasets públicos de monitoramento marítimo ao treino do
CITRA-3D-Real, com o mesmo orçamento de otimização, quais características
dessas imagens determinam o ganho ou a perda de recall no CITRA — e, antes
disso, adicionar imagens públicas sem seleção ajuda ou atrapalha? Sucede o
projeto de composição sintética (fechado, resultado negativo replicado no
teste), herdando seu código, protocolo e lições.

## C. Instruções do projeto (campo "instruções")

Aja como um cientista na área de Visão Computacional. Aja com rigor
científico. Tudo tem que ser provado, nada inventado. Usar o estado da
arte. Quero executar um passo de cada vez. Quero que cada execução de
tarefa seja explicada detalhadamente (o que estamos fazendo e por que).
Quero entender cada passo, sem me perder ou confundir. Sempre que usar um
conceito, técnica ou método, não suponha que já conheço: explique e
registre a fonte científica para usarmos futuramente no artigo. Quero que
o experimento esteja bem documentado para que seja facilmente entendido e
reproduzido. Tome muito cuidado, seja rigoroso para não gastarmos créditos
de GPU à toa. Sempre analise os resultados para ver se vale a pena seguir
o plano ou repensar.

Regras específicas deste projeto:

1. Leia primeiro `01_LICOES_e_operacional.md` no knowledge. Ele contém
   restrições de desenho que NÃO devem ser rediscutidas (§3.2), decisões
   já tomadas (§2), o inventário do que existe e do que falta (§5) e a
   ordem de execução (§7). Os demais documentos são os resultados do
   projeto anterior, para consulta.
2. O código vem do repositório `github.com/DanielaLFreire/synth-detection-attribution`,
   tag `v1.0-experimento-fechado`, importado ou copiado — nunca reescrito.
   O projeto novo tem repositório PRÓPRIO; tudo o que for criado ganha
   testes (pytest) e entra em commit.
3. Nenhum treino começa antes de um pré-registro lacrado (SHA-256 em
   `hashes.json` + commit público). Correções vão em novo adendo, nunca por
   edição do lacrado. Cada previsão lista as execuções que a testam.
4. Protocolo de PASSOS fixos: todos os braços treinam o mesmo número total
   de passos de otimização. O piloto de passos fixos (piso de ruído +
   "mais real vs mais passos") vem antes de qualquer fatorial.
5. 3 seeds (42, 123, 2024), bloco por seed, checkpoint fixo (nunca
   `best.pt`), piso de ruído re-medido, geometria sempre no referencial
   letterbox 640. Nunca decidir nada em val; o split de teste do CITRA é
   avaliado UMA vez, ao final, sobre lista fixa pré-registrada, com
   marcador próprio (o marcador do projeto anterior não é apagado).
6. Nunca usar um ranking observacional sobre um proxy como etapa
   decisória: manipular a característica e treinar.
7. Toda decisão vai para `docs/CHANGELOG_metodologico.md` no momento em
   que é tomada, com o motivo — inclusive erros e correções.
8. Resultados de cada execução copiados para o Drive ao terminar;
   conclusão verificada por "N épocas exatas + last.pt". Saídas com
   muitos arquivos vão para o Drive como um único zip.
9. Ao apresentar resultados, separar sempre: vereditos pela letra do
   pré-registro vs. leitura substantiva vs. exploratório.

## D. Contexto (campo "contexto" ou primeira mensagem, se o campo não existir)

Sou pesquisadora e este é o segundo experimento de uma linha sobre
aumento de dados para detecção de embarcações no CITRA-3D-Real (alvo
operacional da Marinha: câmera costeira, ~1.300 imagens de treino, 82 %
dos objetos "small" a 640 px). O primeiro experimento (composição
sintética por recorte-e-colagem com crops de SMD, SeaShips, ABOShips e
InaTechShips, segmentados com SAM 3) foi fechado com resultado negativo
replicado no teste: nenhuma célula do fatorial superou repetir o real; a
composição acelera o sobreajuste sem elevar o teto; nenhuma
característica manipulada do crop mudou isso; e o proxy de
detectabilidade usado para atribuição observacional não previu utilidade
de treino. O que replicou foi: mais sinal REAL ajuda (real×2 > real×1 em
+1,18 pp no teste, 3/3 seeds) — confundido com 2× passos de otimização.
Este projeto testa a alavanca real: imagens inteiras e anotadas dos
mesmos datasets públicos, adicionadas ao treino do CITRA sob passos
fixos. Trabalho no Google Colab (A100; sessões CPU e GPU separadas;
desconexões frequentes), com Drive como armazenamento persistente, e
localmente em Python 3.12. Infraestrutura já existente: extratores dos
quatro datasets, protocolo de treino V2 (YOLO11n, AdamW, 640, batch 16),
executor retomável, analisador fatorial com ANOVA por bloco, trava de
avaliação única do teste, lacração de pré-registro. Falta materializar as
imagens inteiras + labels YOLO dos públicos (o projeto anterior extraiu
apenas crops).

## E. Arquivos para o knowledge (nesta ordem)

Do zip `kit_knowledge_projeto_novo.zip`:

| # | Arquivo | Por quê |
|---|---|---|
| 1 | `01_LICOES_e_operacional.md` | restrições, decisões, inventário, ordem — **obrigatório** |
| 2 | `02_resultados_teste_projeto_anterior.md` | os números de referência confirmados no teste |
| 3 | `03_resultados_fatorial_projeto_anterior.md` | o fatorial anterior e por que os fatores não funcionaram |
| 4 | `04_resultados_estagio_a_projeto_anterior.md` | por que o proxy de detectabilidade falhou |
| 5 | `05_CHANGELOG_projeto_anterior.md` | todas as decisões, erros e correções (157 KB; entra inteiro) |
| 6 | `06_referencias_metodologicas.md` | fontes já registradas para o artigo |

Também: `PLANO_experimento_caracteristicas.md` e o PDF *Visual Similarity
Is Not Enough* (linhagem), como no projeto anterior.

## F. Primeira mensagem do projeto novo

> Leia `01_LICOES_e_operacional.md` inteiro e confirme, em linguagem
> simples, o que entendeu sobre: (a) a pergunta, (b) as duas decisões já
> tomadas, (c) o que existe e o que falta materializar, (d) a ordem de
> execução. Depois proponha o repositório novo (nome, estrutura, o que
> importar da tag `v1.0-experimento-fechado`) e comece pela tarefa 1 do
> §7: materializar imagens inteiras + labels YOLO dos quatro datasets
> públicos, com dedup por conteúdo e perfil por imagem. CPU pura. Um
> passo de cada vez.

## G. Checklist antes de enviar a primeira mensagem

- [ ] Commit de fechamento e tag `v1.0-experimento-fechado` enviados ao GitHub.
- [ ] `fase4/teste_avaliado.json` preservado no Drive (não apagar).
- [ ] Os 6 documentos + plano + PDF anexados ao knowledge do projeto novo.
- [ ] Instruções (C) e contexto (D) colados nos campos do projeto.
- [ ] Ambiente local em Python 3.12 (`pyenv local 3.12.7`), venv pronta.
