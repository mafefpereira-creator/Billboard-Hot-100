# Sobre os dados desta pasta

Esta pasta tem dois tipos de arquivo, e só um deles fica no GitHub.

## O que É versionado (fica no repositório)

Os resultados **agregados** de cada script — contagens, médias, rankings por
artista/ano/gênero/cluster. Nenhum desses arquivos permite reconstruir a base
de áudio faixa a faixa; eles resumem o que já está publicado, em forma de
tabela, no próprio TCC:

- `resultado_02_cross_geracionalidade.csv`, `resultado_03_tempo_carreira.csv`,
  `resultado_03_hiatos.csv`, `resultado_03_kaplan_meier.csv` — nível artista/hiato.
- `resultado_04_inercia_silhouette.csv` — só os números agregados de k=2 a 8.
- `resultado_05_importancia_variaveis.csv`, `resultado_05_metricas.csv`.
- `resultado_06_generos_por_decada.csv`, `resultado_06_pareto.csv`,
  `resultado_06_solo_vs_feat.csv`.

## O que NÃO é versionado (fica só na sua máquina, via `.gitignore`)

- `Billboard_Hot_100_Songs_SYM_Dataset_MASTER.xlsx` — a planilha-mestre completa.
- `base_limpa.csv` — a base tratada, uma linha por faixa, com os atributos de
  áudio do Spotify.
- `resultado_04_clusters_k2.csv` e `resultado_04_clusters_k5.csv` — também uma
  linha por faixa (cluster atribuído + os 6 atributos de áudio usados).

**Por quê:** tanto o Billboard quanto o Spotify restringem a redistribuição em
massa dos dados brutos das próprias plataformas nos termos de uso. Publicar a
base faixa a faixa (com BPM, energia, dançabilidade etc. de cada uma das ~7 mil
músicas) seria redistribuir esse conteúdo em massa. Publicar só os agregados —
quantos artistas em cada situação, médias por grupo, rankings — não é: é
exatamente o tipo de informação que já está impressa nas tabelas do TCC.

## Como rodar os scripts mesmo assim

Os arquivos que faltam são fáceis de recriar:

1. Coloque sua cópia da planilha-mestre em
   `data/Billboard_Hot_100_Songs_SYM_Dataset_MASTER.xlsx` (ela não vai para o
   Git, mas o `python3 scripts/01_carregar_dados.py` precisa dela localmente).
2. Rode os scripts na ordem do README principal. Cada um recria os arquivos
   que faltam a partir da planilha.

## Reconstruindo a base do zero, sem a planilha-mestre

Quem não tiver a planilha (por exemplo, alguém de fora clonando o repositório)
pode montar uma equivalente a partir das fontes públicas originais, seguindo a
mesma lógica da Metodologia do TCC:

1. Rankings anuais: Billboard Hot 100 Year-End, 1950–2025, disponíveis em
   billboard.com (a partir de meados dos anos 2000) e, para os anos mais
   antigos, via Wayback Machine ou compilações como o dataset do Harvard
   Dataverse (Perot, 2025) usado como cross-check no TCC.
2. Atributos de áudio: cruzar cada faixa com seus atributos técnicos via Sort
   Your Music (sortyourmusic.playlistmachinery.com) ou diretamente pela API do
   Spotify (endpoint de audio features), buscando por título + artista.
3. Aplicar os mesmos critérios de inclusão/exclusão e identificação de artista
   descritos na Metodologia do TCC e replicados em
   `scripts/01_carregar_dados.py`.

Esse processo é manual e demorado (é o que a curadoria original documentou,
linha a linha, na coluna `OBSERVAÇÃO` da planilha) — por isso ele não está
automatizado aqui. O que este repositório garante é que, tendo a planilha
tratada em mãos, qualquer pessoa reproduz os cálculos a partir dela de forma
transparente e auditável.
