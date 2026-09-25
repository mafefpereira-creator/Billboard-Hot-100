"""
01 - Carregar e limpar a base

Le as 76 abas de ano (1950-2025) da planilha-mestre e monta um unico dataframe
limpo, aplicando os mesmos filtros e regras de identificacao de artista
descritos na secao de Metodologia do TCC.

Entrada:  data/Billboard_Hot_100_Songs_SYM_Dataset_MASTER.xlsx
Saida:    data/base_limpa.csv

Como a curadoria manual original (unificacao de grafias, correcao de
titulo/artista linha a linha) foi feita por revisao humana registrada na
coluna OBSERVACAO da planilha, este script nao repete esse trabalho -
ele consome o resultado ja curado (RELEASE verificado, INCLUIR_ANALISE,
GENERO) e aplica por cima uma normalizacao programatica simples para
juntar grafias obviamente equivalentes do mesmo artista (espacos duplos,
maiusculas/minusculas, "The" no inicio, etc.). Isso e uma reconstrucao
independente da regra descrita no TCC, nao uma copia do mapeamento manual
da autora - os numeros finais devem ficar proximos dos publicados, mas nao
sao garantidos como identicos casa a casa.
"""

import re
import unicodedata
import pandas as pd
import openpyxl

CAMINHO_PLANILHA = "data/Billboard_Hot_100_Songs_SYM_Dataset_MASTER.xlsx"
CAMINHO_SAIDA = "data/base_limpa.csv"

COLUNAS = [
    "#", "TITLE", "ARTIST", "RELEASE", "BPM", "ENERGY", "DANCE", "LOUD",
    "VALENCE", "LENGTH", "ACOUSTIC", "POP.", "A.SEP", "RND",
    "INCLUIR_ANALISE", "OBSERVACAO", "RELEASE_VERIFICADO",
    "RELEASE_PRECISAO", "RELEASE_FONTE", "ADDED", "GENERO",
    "GENERO_CONFIANCA", "GENERO_FONTE",
]

FEATURES_AUDIO_KMEANS = ["BPM", "ENERGY", "DANCE", "LOUD", "VALENCE", "ACOUSTIC"]
FEATURES_AUDIO_RF = FEATURES_AUDIO_KMEANS + ["LENGTH_SEG", "POP.", "POSICAO_ESTREIA"]


def normalizar_nome_artista(nome: str) -> str:
    """Chave de agrupamento para juntar grafias equivalentes do mesmo artista.

    Minusculiza, remove acentos, colapsa espacos e tira pontuacao leve.
    Nao separa feat./participacoes aqui - isso e tratado depois, com a
    regra (c) da Metodologia (participacoes creditadas ao artista principal).
    """
    if nome is None:
        return ""
    s = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s&]", "", s)
    return s


def artista_principal(nome: str) -> str:
    """Aplica a regra (c): 'feat.' e participacoes creditadas ao artista principal.

    Ex.: "Total feat. Missy Elliott" -> "Total"
         "Lose Control (feat. Ciara & Fat Man Scoop)" -> "Lose Control" (tratado a parte via TITLE)
    """
    if nome is None:
        return ""
    s = str(nome)
    s = re.split(r"\s+feat\.?\s+|\s+featuring\s+|\s+ft\.?\s+", s, flags=re.IGNORECASE)[0]
    s = re.split(r"\s+with\s+", s, flags=re.IGNORECASE)[0]
    s = s.strip()
    return s


def carregar_planilha(caminho: str) -> pd.DataFrame:
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    anos = [nome for nome in wb.sheetnames if nome.isdigit()]
    linhas = []
    for ano in anos:
        ws = wb[ano]
        cabecalho = None
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                cabecalho = row
                continue
            if row is None or all(v is None for v in row):
                continue
            registro = dict(zip(COLUNAS, row))
            registro["ANO_CHART"] = int(ano)
            linhas.append(registro)
    wb.close()
    return pd.DataFrame(linhas)


def segundos_de_duracao(valor):
    """A coluna LENGTH vem como datetime.time (HH:MM:SS) na planilha."""
    if valor is None:
        return None
    try:
        return valor.hour * 3600 + valor.minute * 60 + valor.second
    except AttributeError:
        return None


def main():
    print("Lendo as 76 abas de ano da planilha-mestre...")
    df = carregar_planilha(CAMINHO_PLANILHA)
    print(f"  {len(df)} linhas lidas (base bruta do chart, 1950-2025).")

    # Regra (c) da Metodologia: participacoes creditadas ao artista principal
    df["ARTISTA_PRINCIPAL"] = df["ARTIST"].apply(artista_principal)
    df["TEVE_FEAT"] = df["ARTIST"] != df["ARTISTA_PRINCIPAL"]

    # Chave de identidade unica (normalizada) - regra (a)
    df["ARTISTA_CHAVE"] = df["ARTISTA_PRINCIPAL"].apply(normalizar_nome_artista)

    # Duracao em segundos, para uso no Random Forest (feature LENGTH_SEG)
    df["LENGTH_SEG"] = df["LENGTH"].apply(segundos_de_duracao)

    df["INCLUIR_ANALISE_BOOL"] = df["INCLUIR_ANALISE"].astype(str).str.strip().str.lower() == "sim"

    n_artistas = df["ARTISTA_CHAVE"].nunique()
    n_validos = df["INCLUIR_ANALISE_BOOL"].sum()
    print(f"  {n_artistas} artistas distintos (apos normalizacao de identidade).")
    print(f"  {n_validos} faixas com INCLUIR_ANALISE = Sim ({n_validos/len(df):.2%}).")

    df.to_csv(CAMINHO_SAIDA, index=False)
    print(f"Base limpa salva em {CAMINHO_SAIDA}")


if __name__ == "__main__":
    main()
