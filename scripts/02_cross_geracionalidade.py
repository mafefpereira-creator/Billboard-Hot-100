"""
02 - Cross-geracionalidade

Um artista e "cross-geracional" quando tem hits no Hot 100 Year-End em
2 ou mais decadas-calendario distintas (decada = ano // 10 * 10). A escolha
da decada-calendario (em vez de uma janela movel de 10 anos) segue a
periodizacao usada pela critica musical, conforme a Metodologia do TCC.

Entrada:  data/base_limpa.csv
Saida:    data/resultado_02_cross_geracionalidade.csv (uma linha por artista)
          Impressao no terminal com o resumo agregado.
"""

import pandas as pd

CAMINHO_ENTRADA = "data/base_limpa.csv"
CAMINHO_SAIDA = "data/resultado_02_cross_geracionalidade.csv"

PERENES_SAZONAIS = {"brenda lee", "burl ives", "wham"}


def eh_perene_sazonal(chave_artista: str) -> bool:
    return any(p in chave_artista for p in PERENES_SAZONAIS)


def main():
    df = pd.read_csv(CAMINHO_ENTRADA)

    df["DECADA"] = (df["ANO_CHART"] // 10) * 10

    por_artista = (
        df.groupby("ARTISTA_CHAVE")
        .agg(
            artista_nome=("ARTISTA_PRINCIPAL", "first"),
            primeiro_ano=("ANO_CHART", "min"),
            ultimo_ano=("ANO_CHART", "max"),
            n_hits=("TITLE", "count"),
            n_decadas=("DECADA", "nunique"),
            n_anos_distintos=("ANO_CHART", "nunique"),
        )
        .reset_index()
    )

    por_artista["cross_geracional"] = por_artista["n_decadas"] >= 2
    por_artista["perene_sazonal"] = por_artista["ARTISTA_CHAVE"].apply(eh_perene_sazonal)

    n_total = len(por_artista)
    n_cross = por_artista["cross_geracional"].sum()
    taxa = n_cross / n_total

    # +1 porque "carreira de 1 ano" no TCC significa emplacar no mesmo ano-calendario
    # (primeiro ano = ultimo ano conta como 1, nao 0)
    carreira_mediana = (por_artista["ultimo_ano"] - por_artista["primeiro_ano"] + 1).median()

    print(f"Artistas distintos: {n_total}")
    print(f"Cross-geracionais (2+ decadas): {n_cross} ({taxa:.2%})")
    print(f"  -> valor publicado no TCC: 501 artistas, 18,52%")
    print(f"Carreira mediana (contando ano de estreia): {carreira_mediana:.0f} ano(s)")
    print(f"  -> valor publicado no TCC: mediana de 1 ano")

    perenes = por_artista[por_artista["perene_sazonal"]]
    if len(perenes):
        print("\nCasos de 'perene sazonal' identificados (excluidos do ranking de carreira, secao 2):")
        for _, row in perenes.iterrows():
            print(f"  {row['artista_nome']}: {row['primeiro_ano']}-{row['ultimo_ano']}"
                  f" ({row['ultimo_ano'] - row['primeiro_ano']} anos de hiato bruto)")

    por_artista.to_csv(CAMINHO_SAIDA, index=False)
    print(f"\nResultado salvo em {CAMINHO_SAIDA}")


if __name__ == "__main__":
    main()
