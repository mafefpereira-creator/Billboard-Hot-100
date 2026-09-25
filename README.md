# Longevidade comercial de artistas no Billboard Hot 100 (1950–2025)

Este repositório reúne os dados e o código usados no TCC "Longevidade comercial de
artistas no Billboard Hot 100 (1950–2025)", do MBA em Data Science e Analytics da
USP/Esalq. A pergunta central do trabalho é simples de enunciar e difícil de
responder: o que separa os artistas que voltam a fazer sucesso décadas depois do
primeiro hit dos que emplacam só uma vez? O repositório existe para que qualquer
pessoa possa reproduzir os números do trabalho a partir da mesma base de dados,
sem depender de arquivos privados ou de uma explicação verbal do processo.

## O que tem aqui

- `data/` — os resultados agregados que cada script gera (rankings, contagens,
  médias por grupo). A planilha-mestre em si (`Billboard_Hot_100_Songs_SYM_Dataset_MASTER.xlsx`)
  e a base tratada faixa a faixa **não ficam no repositório** — só na máquina
  de quem roda os scripts. O porquê e o como estão em `data/README.md`.
- `scripts/` — seis scripts Python, numerados na ordem em que devem rodar,
  cobrindo as cinco análises centrais do TCC (cross-geracionalidade, tempo de
  carreira, reentrada após hiato, clusters sonoros via k-means e Random Forest)
  mais as análises complementares (gênero por década, solo x feat., trajetória
  ano a ano, curva de Pareto).
- `dashboard/index.html` — um painel estático com os principais números e
  gráficos do trabalho, sem backend nem build step: basta abrir o arquivo no
  navegador, ou publicar via GitHub Pages.

## Sobre esta versão do código

O código aqui **não é uma cópia literal** do pipeline original usado durante a
pesquisa (que rodou em notebooks no Google Colab e no VS Code, com curadoria
manual linha a linha registrada na coluna `OBSERVAÇÃO` da planilha). É uma
reconstrução independente e limpa, escrita depois, que aplica exatamente os
mesmos critérios metodológicos descritos no TCC — mesmos filtros, mesmos
parâmetros de modelo, mesma definição de cada métrica — partindo diretamente da
planilha-mestre já curada.

Isso tem uma vantagem: qualquer pessoa que baixe este repositório consegue
rodar os scripts do zero e chegar a números muito próximos dos publicados no
TCC, sem precisar de nenhum arquivo além do que está aqui (mais a planilha, ver
`data/README.md`). E uma ressalva honesta: alguns números batem exatamente com
o TCC e outros ficam próximos, mas não idênticos — isso é esperado, pelo motivo
explicado abaixo, e está documentado em cada script, com o valor publicado no
TCC impresso ao lado do valor recalculado. Na prática, a maior parte dos
resultados reproduz com uma diferença de casas decimais ou menos: por exemplo,
a tabela de inércia e silhouette do k-means (script `04`) bate número a número
com a Tabela do TCC, e a curva de Pareto (script `06`) reproduz os 44 hits de
Drake e os percentuais de concentração quase exatamente.

### Por que a identificação de artista foi refeita de forma programática

Uma das etapas mais trabalhosas da pesquisa original foi decidir, uma a uma,
quando duas linhas da planilha eram "o mesmo artista". Isso não é tão óbvio
quanto parece: "Andy Gibb" e "Barry Gibb" apareceram trocados numa linha por
erro do Spotify/SYM; "Total feat. Missy Elliott" e "Total" precisam contar
como o mesmo artista; uma gravação creditada de formas ligeiramente diferentes
ao longo dos anos (variação de grafia, remaster, feat. adicional) também.
Essas decisões foram tomadas manualmente, linha a linha, durante a pesquisa, e
o registro de cada uma está na coluna `OBSERVAÇÃO` da planilha — é uma
auditoria em texto livre, pensada para leitura humana, não uma tabela de
mapeamento "grafia A = grafia B" que um script possa simplesmente carregar e
aplicar.

Isso deixou duas opções para este repositório: (a) transcrever manualmente,
para um formato estruturado, cada uma das centenas de decisões de curadoria já
tomadas — o que reproduziria o resultado exato, mas na prática seria reescrever
à mão o mesmo trabalho, sem ganho de transparência sobre o que o código faz; ou
(b) escrever uma regra programática, simples e auditável, que resolve a
esmagadora maioria dos casos sozinha (normalizar acentos/maiúsculas, cortar o
que vem depois de "feat."/"featuring"/"with") e documentar, às claras, que ela
não é uma cópia da curadoria manual original.

Optei pela opção (b), em `scripts/01_carregar_dados.py`, função
`normalizar_nome_artista` / `artista_principal`. A vantagem é que qualquer
pessoa lendo o script entende exatamente o que a regra faz, sem precisar
confiar numa lista de decisões que não está (e não deveria estar) publicada
por inteiro. A consequência é a diferença mencionada acima: com essa regra
mais simples, o número de artistas distintos fica em 2.700–2.701, contra os
2.705 da curadoria manual completa — uma diferença de 4-5 casos nos quais a
regra automática não separou (ou separou) um artista do jeito que a revisão
manual fez. Isso é dito abertamente porque é exatamente o tipo de coisa que
inflaria artificialmente a credibilidade do repositório se ficasse escondida.

## Como rodar

Requisitos: Python 3.10+, com `pandas`, `numpy`, `scikit-learn` e `openpyxl`
instalados (`pip install pandas numpy scikit-learn openpyxl`). Nenhuma outra
dependência é necessária — a análise de sobrevivência (Kaplan-Meier, usada no
script `03`) está implementada diretamente com `numpy`, sem depender de um
pacote externo de análise de sobrevivência.

```bash
# 0. coloque sua copia da planilha-mestre em data/Billboard_Hot_100_Songs_SYM_Dataset_MASTER.xlsx
#    (esse arquivo nao fica no Git - ver data/README.md)
cd scripts
python3 01_carregar_dados.py          # le a planilha-mestre e gera data/base_limpa.csv
python3 02_cross_geracionalidade.py
python3 03_tempo_carreira_hiato.py
python3 04_clustering.py
python3 05_random_forest.py           # o mais lento: ~3-5 min (permutation importance)
python3 06_analises_complementares.py
```

Cada script lê o que precisa de `data/` e escreve seus resultados de volta em
`data/`, como arquivos CSV. Rodar na ordem acima é importante porque os
scripts `03` a `06` dependem do resultado do `01` (base limpa) e, em alguns
casos, do `02` (status cross-geracional por artista).

## Fonte e uso dos dados

A base combina duas fontes: o ranking anual Billboard Hot 100 Year-End
(1950–2025) e atributos técnicos de áudio do Spotify, obtidos via Sort Your
Music (SYM). Cada linha da planilha-mestre corresponde a uma posição do
ranking anual de um ano específico; os atributos de áudio (BPM, energia,
dançabilidade, volume, valência, acústica, duração, popularidade) foram
cruzados manualmente com o ranking, com o processo de verificação, correção e
inclusão/exclusão registrado na aba `Default` da planilha e na coluna
`OBSERVAÇÃO` de cada aba de ano.

Billboard e Spotify restringem a redistribuição em massa dos dados brutos das
próprias plataformas nos respectivos termos de uso. Por isso **a planilha
faixa a faixa não é publicada neste repositório** — só o código que a
processa e os resultados já agregados (contagens, médias, rankings), que são
o mesmo tipo de informação já impressa nas tabelas do TCC. Detalhes de qual
arquivo fica onde, e como reconstruir a base a partir das fontes públicas
originais caso você não tenha a planilha, estão em `data/README.md`.

## Licença

Código sob licença MIT (ver `LICENSE`). Os resultados agregados em `data/` são
disponibilizados para fins de reprodutibilidade acadêmica do TCC citado acima;
qualquer redistribuição deve preservar a citação da fonte original
(Billboard Hot 100 Year-End e Spotify via Sort Your Music).

## Citação

Pereira, M. F. *Longevidade comercial de artistas no Billboard Hot 100
(1950–2025)*. Trabalho de Conclusão de Curso — MBA em Data Science e
Analytics, USP/Esalq, 2026.
