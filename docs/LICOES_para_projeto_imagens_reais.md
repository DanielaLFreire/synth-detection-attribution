# Lições e informações operacionais para o projeto novo
## "Imagens reais de datasets públicos como aumento do CITRA"

Documento de transferência, escrito em 2026-09-16 no fechamento do projeto
`synth-detection-attribution` (tag `v1.0-experimento-fechado`). Destina-se
ao knowledge de um projeto Claude NOVO, sem memória da conversa anterior.
Tudo aqui foi verificado no código ou nos resultados; nada é suposição.

---

## 1. A pergunta do projeto novo

> Ao adicionar imagens **reais e anotadas** de datasets públicos de
> monitoramento ao treino do CITRA-3D-Real, **com o mesmo orçamento de
> otimização**, quais características dessas imagens determinam o ganho
> (ou perda) de recall no CITRA — e, antes disso, **adicionar imagens
> públicas sem seleção ajuda ou atrapalha?**

## 2. Decisões já tomadas (pelo pesquisador, 2026-09-16)

1. **Baseline próprio.** O projeto novo treina seu próprio baseline
   CITRA-só sob o protocolo novo (passos fixos). Nenhum número do projeto
   anterior é reaproveitado como baseline — só como referência de
   sanidade. A avaliação no split de teste do CITRA acontece **uma vez**,
   ao final, sobre uma lista fixa de modelos pré-registrada como
   experimento distinto (o teste já foi avaliado uma vez pelo projeto
   anterior; a segunda passada é defensável porque nenhuma seleção de
   modelo foi feita sobre o teste em nenhum dos dois projetos).
2. **O piloto de passos fixos vem antes do fatorial.** É o que separa
   "mais dados" de "mais passos". Se CITRA-só com os passos de CITRA×2
   empatar com CITRA×2, o +1,2 pp observado antes era passos, não dados.

## 3. O que o projeto anterior estabeleceu (e restringe o desenho)

### 3.1 Achados confirmados no teste (401 imagens, 1.247 caixas, 80 % small)
- Composição sintética por recorte-e-colagem **não supera repetir o real**:
  −1,75 pp vs real×2, 12/12 comparações pareadas; ≈ real×1. Acelera o
  sobreajuste sem elevar o teto.
- Nenhuma característica manipulada do crop (escala, contraste) muda isso.
- **Proxies de detectabilidade não predizem utilidade de treino**: a feature
  mais forte para "o detector reconhece o objeto colado" (contraste) teve
  efeito nulo como fator de treino. → **Nunca usar um ranking observacional
  sobre um proxy como etapa decisória.** Manipular e treinar.
- **O que ajudou foi sinal real**: real×2 supera real×1 em +1,18 pp
  (3/3 seeds, teste) — **confundido com 2× passos**. Ver §2, decisão 2.
- Fonte (identidade) não tem efeito próprio: 94 % da sua importância
  desaparece quando propriedades mensuráveis são controladas. → Selecionar
  imagens por **propriedade mensurável**, com **fontes balanceadas**.
- Geometria (tamanho da caixa) domina a detectabilidade (58 % da
  variância). O prior mais forte para imagens inteiras é o **perfil de
  tamanho dos objetos a 640 px**.
- Efeitos < 2,0 pp não são confiáveis mesmo com direção consistente em
  3 seeds (P5b' em val não replicou no teste). O piso funciona.
- Efeito de seed em val (F = 11,8) não generalizou ao teste (F = 0,05):
  **nunca decidir nada em val**.

### 3.2 Regras de método que valem como estão
- 3 seeds (42, 123, 2024), sempre. Bloco por seed na análise.
- Piso de ruído medido em piloto (foi 2,0 pp = maior amplitude entre
  braços na época fixa). **Deve ser re-medido** sob o protocolo de passos
  fixos — não reaproveitar.
- Checkpoint fixo, nunca `best.pt` (é seleção por validação).
- Pré-registro lacrado (SHA-256 em `hashes.json` + commit público) ANTES
  de qualquer treino; correções em novo adendo, nunca por edição.
- Cada previsão deve listar **explicitamente as execuções que a testam**
  (erro anterior: P6' exigia 36 treinos não orçados).
- Critério de viabilidade das células declarado ANTES de verificar; se
  falhar, novo adendo (foi assim que um 3×2 foi rejeitado antes de gastar
  GPU).
- Geometria SEMPRE no referencial letterbox 640 (`area × (640/max(W,H))²`),
  o do detector e do perfil do alvo — nunca em pixels nativos (erro
  cometido e corrigido).
- Resultados de treino copiados para o Drive ao final de CADA execução;
  conclusão verificada por "N épocas exatas + last.pt".
- Toda decisão vai para `docs/CHANGELOG_metodologico.md` no momento em
  que é tomada, com o motivo.

### 3.3 Novo no projeto novo: protocolo de PASSOS fixos
Todos os braços treinam o mesmo número total de passos de otimização S.
`epochs_braço = round(S × batch / n_imagens_braço)`. Warmup já é em
passos absolutos (500) no protocolo V2; estender ao total é trivial.
Proposta inicial: S ≈ 25.000 (≈ o que CITRA×2 recebeu em 150 épocas:
2.696/16 ≈ 169 passos/época × 150). Registrar S no adendo.

## 4. Números de referência (não são baseline; são sanidade)

| Item | Valor |
|---|---|
| CITRA-3D-Real | train 1.348 img / 4.489 caixas; val 332 / 1.267; test 401 / 1.247 |
| Fração small a 640 | Fase 0 (val) 82,2 %; val 85,7 %; test 79,9 % |
| Resolução das imagens do CITRA | grandes (fator 640/max(W,H) ≈ 1/3 ou menor) — ler pelo cabeçalho |
| B2 (real×1, 150 ép., yolo11n) recall | val 0,688; **teste 0,719** ± 0,005 |
| real×2 (150 ép.) recall | val 0,705; **teste 0,731** ± 0,006 |
| Piso de ruído (época fixa) | 2,0 pp (amplitude), dp ≈ 0,6–1,1 pp |
| Tempo | ≈ 8,5 it/s em A100 (batch 16, 640) → ~38 s por 331 passos |

## 5. Inventário operacional

### 5.1 Drive (`/content/drive/MyDrive/PROJETO_MARINHA/`)
- `Datasets/CITRA-3D-Real/{train,val,test}/images` e `.../labels_final`
  (YOLO, classe única `0`; manifesto de hash). **Test: só tocar na
  avaliação final.**
- `Datasets/_zips/`: `smd_clean.zip`, `SeaShips_voc.zip`, `ABOships.zip`,
  `dataset_25k_v2.zip` (InaTechShips). Originais dos públicos.
- `EXPERIMENTO_ATRIBUICAO_CAUSAL/` (projeto anterior): crops SAM 3,
  manifestos de extração por caixa (`crops_sam3/manifesto_extracao_bruta_*.csv`,
  com `imagem_origem`, coordenadas e tamanhos), embeddings CLIP de crops,
  runs das Fases 1 e 3, `fase4/teste_avaliado.json` (**marcador: não
  apagar**). O projeto novo usa uma raiz NOVA e um marcador NOVO de teste.

### 5.2 Datasets públicos — o que existe e o que falta
| Fonte | Formato original | Imagens | Observações |
|---|---|---|---|
| SMD (on-shore) | YOLO (smd_clean) | 914 | frames de vídeo (quase-duplicatas); 7.043 caixas |
| SeaShips | VOC XML | 6.979 | frames de vídeo; objetos grandes; dedup necessário |
| ABOShips | CSV | ~9,9 mil | objetos pequenos (38 % dos crops < 20 px); mais parecido com o CITRA em aparência |
| InaTechShips | YOLO, splits train/val/test | 27.796 | fotos próximas, objetos grandes; muito distinto do CITRA |

**Faltam** imagens inteiras + labels YOLO materializados dos públicos: o
projeto anterior extraiu CROPS. Primeira tarefa técnica: materializar
`{fonte}/images` + `labels_final` (classe única) a partir dos zips,
reutilizando os parsers de `src/extraction/` (`extrair_crops_yolo/voc/csv`
já leem cada formato) e `src/materialize/labels_final.py` (hash +
validação). Deduplicar frames de vídeo (SMD, SeaShips) por conteúdo
(`src/evaluation/isolamento.py::hashes_imagens`).

### 5.3 Repositório a importar (não reescrever)
`github.com/DanielaLFreire/synth-detection-attribution`, tag
`v1.0-experimento-fechado`. Reaproveitar como dependência ou cópia:
- `src/train/protocol.py` (V2), `src/train/trainlist.py`,
  `src/train/executar.py` (executor retomável + verificação rigorosa).
- `src/factorial/analise.py` (ANOVA com bloco, contrastes pareados, piso,
  Holm) e `celulas.py` (viabilidade com fontes balanceadas — adaptar de
  "caixa" para "imagem").
- `src/evaluation/` (trava de avaliação única; isolamento por md5).
- `src/attribution/clip_features.py` + `scripts/extrair_clip_estagio_a.py`
  (adaptar para embutir o frame inteiro).
- `scripts/lacrar_adendo.py` (lacração com salvaguardas).
- Ambiente local: Python 3.12 + `requirements.txt`; no Colab, `shap`
  (numpy ≥ 2) e `sam3` (numpy < 2) não coexistem — SAM não é necessário
  neste projeto.

## 6. Esqueleto do desenho (a pré-registrar; nada aqui está fechado)

**Piloto (obrigatório, antes de tudo)**: CITRA-só, S passos, 3 seeds →
piso de ruído sob o protocolo novo; e CITRA×2 com os mesmos S passos →
decide se "mais real" tem valor além de "mais passos".

**Fatorial 2×2**, volume fixo de imagens públicas por célula (proposta:
1.348 = 1× CITRA), fontes balanceadas:
- A — perfil de escala da imagem pública a 640: `small-dominante` vs
  `grande-dominante` (prior forte: small ajuda mais).
- B — proximidade de aparência do frame inteiro ao CITRA (CLIP, corte
  na mediana): `perto` vs `longe` (prior nulo; exploratória se preferir).

**Controles**: C0 CITRA-só (S passos); C1 mistura ALEATÓRIA de públicas,
mesmo volume (a pergunta prática: "ajuda sem seleção?").

**Previsões candidatas**: A: small > grande por > piso. C1 vs C0: direção
positiva, magnitude incerta. Melhor célula vs C1: > piso (é o que
justifica selecionar). B: sem direção.

**Custo**: 6 braços × 3 seeds = 18 execuções × ~1 h (S ≈ 25 mil passos)
≈ 18–20 h de GPU.

**Viabilidade a verificar antes** (CPU): quantas imagens `small-dominante`
existem em SeaShips/InaTechShips — pode não haver o bastante para
balancear fontes (a mesma surpresa aconteceu no 3×2 anterior).

## 7. Ordem de execução recomendada

1. Materializar imagens + labels dos públicos; dedup por conteúdo; perfil
   por imagem (n caixas, fração small a 640, W×H). CPU.
2. CLIP de frame inteiro (públicos + CITRA train). GPU leve (~10 min).
3. Piloto de passos fixos (3 + 3 execuções, ~6 h GPU). Piso re-medido.
4. Verificação de viabilidade das células com fontes balanceadas. CPU.
5. Adendo pré-registrado (fatores, níveis, volume, S, seeds, previsões
   com lista de execuções, famílias de Holm, critério de viabilidade já
   satisfeito, lista fixa de modelos para o teste). Lacrar. Commit.
6. Treino retomável (18 execuções). Análise por seed. Val como métrica
   primária durante o experimento.
7. Uma avaliação no teste, lista fixa, marcador novo. Documento de
   resultados: vereditos pela letra separados da leitura substantiva.

## 8. Armadilhas conhecidas (todas já custaram tempo)
- Colab desconecta: `/content` some; tudo que importa vai para o Drive ao
  terminar; scripts de preparação são re-executáveis.
- Escrever milhares de arquivos soltos no Drive (FUSE) falha: um zip por
  saída.
- `transformers` novo retorna objeto em `get_image_features`; crops com
  lado = 3 px confundem o canal (irrelevante aqui, imagens inteiras).
- O compositor grava saída mesmo sem colagem (não se aplica aqui, mas o
  padrão "conferir N sintético/aumento = pré-registrado, com assert" vale).
- Sessões CPU e GPU são separadas; preparação leve pode rodar na sessão
  de GPU.
- `results.csv` parcial existe quando o treino é interrompido: verificar
  época final + `last.pt`, não a existência do arquivo.
