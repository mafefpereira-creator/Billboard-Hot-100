"""
06 - Analises complementares

Quatro analises que nao substituem as centrais (02-05), mas dao contexto
adicional, conforme descrito na Metodologia do TCC:

  (a) Generos musicais por decada, e cruzamento com cross-geracionalidade
  (b) Solo x participacao (feat.), incluindo featuring novato x veterano
  (c) Trajetoria ano a ano: taxa de artistas que desaparecem no ano seguinte
  (d) Curva de concentracao (Pareto): quanto dos hits vem de poucos artistas

Entrada:  data/base_limpa.csv, data/resultado_02_cross_geracionalidade.csv
Saida:    data/resultado_06_generos_por_decada.csv
          data/resultado_06_solo_vs_feat.csv
          data/resultado_06_pareto.csv
"""

import pandas as pd

CAMINHO_BASE = "data/base_limpa.csv"
CAMINHO_CROSS = "data/resultado_02_cross_geracionalidade.csv"


def main():
    df = pd.read_csv(CAMINHO_BASE)
    cross = pd.read_csv(CAMINHO_CROSS)[["ARTISTA_CHAVE", "cross_geracional"]]
    df = df.merge(cross, on="ARTISTA_CHAVE", how="left")
    df["DECADA"] = (df["ANO_CHART"] // 10) * 10

    # --- (a) Generos por decada ---
    generos = (
        df[df["GENERO"].notna()]
        .groupby(["DECADA", "GENERO"])
        .size()
        .reset_index(name="n_faixas")
        .sort_values(["DECADA", "n_faixas"], ascending=[True, False])
    )
    generos.to_csv("data/resultado_06_generos_por_decada.csv", index=False)
    print("Genero dominante por decada:")
    for decada, grupo in generos.groupby("DECADA"):
        top = grupo.iloc[0]
        print(f"  {decada}s: {top['GENERO']} ({top['n_faixas']} faixas)")

    # cruzamento genero x cross-geracionalidade (por artista, genero mais frequente do artista)
    genero_artista = (
        df[df["GENERO"].notna()]
        .groupby("ARTISTA_CHAVE")["GENERO"]
        .agg(lambda s: s.value_counts().idxmax())
        .reset_index()
    )
    cruzamento = genero_artista.merge(cross, on="ARTISTA_CHAVE", how="inner")
    tabela_cruzamento = (
        cruzamento.groupby("GENERO")["cross_geracional"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "taxa_cross_geracional", "count": "n_artistas"})
        .sort_values("taxa_cross_geracional", ascending=False)
    )
    print("\nTaxa de cross-geracionalidade por genero predominante do artista:")
    print(tabela_cruzamento.round(3))

    # --- (b) Solo x feat ---
    por_artista_feat = df.groupby("ARTISTA_CHAVE").agg(
        n_hits=("TITLE", "count"),
        n_com_feat=("TEVE_FEAT", "sum"),
    ).reset_index()
    por_artista_feat["perfil"] = por_artista_feat.apply(
        lambda r: "so com feat." if r["n_com_feat"] == r["n_hits"]
        else ("nunca com feat." if r["n_com_feat"] == 0 else "misto"),
        axis=1,
    )
    resumo_feat = por_artista_feat.merge(cross, on="ARTISTA_CHAVE", how="inner")
    tabela_feat = resumo_feat.groupby("perfil")["cross_geracional"].agg(["mean", "count"])
    print("\nCross-geracionalidade por perfil solo/feat.:")
    print(tabela_feat.round(3))
    resumo_feat.to_csv("data/resultado_06_solo_vs_feat.csv", index=False)

    # --- (c) Trajetoria ano a ano: taxa de desaparecimento no ano seguinte ---
    anos_por_artista = df.groupby("ARTISTA_CHAVE")["ANO_CHART"].apply(lambda s: sorted(s.unique()))
    desaparece_ano_seguinte = 0
    total_aparicoes_nao_finais = 0
    for anos in anos_por_artista:
        for a, b in zip(anos, anos[1:]):
            total_aparicoes_nao_finais += 1
            if b > a + 1:
                desaparece_ano_seguinte += 1
    if total_aparicoes_nao_finais:
        taxa_desaparecimento = desaparece_ano_seguinte / total_aparicoes_nao_finais
        print(f"\nDas aparicoes seguidas de outro hit, {taxa_desaparecimento:.1%} nao repetem no ano seguinte"
              " (norma do Hot 100 e o desaparecimento no ano seguinte).")

    # --- (d) Curva de Pareto ---
    entradas_por_artista = df.groupby("ARTISTA_CHAVE").size().sort_values(ascending=False).reset_index(name="n_entradas")
    entradas_por_artista["artista"] = entradas_por_artista["ARTISTA_CHAVE"]
    n_artistas = len(entradas_por_artista)
    total_entradas = entradas_por_artista["n_entradas"].sum()

    def pct_topo(fracao):
        n = max(1, round(n_artistas * fracao))
        return entradas_por_artista["n_entradas"].iloc[:n].sum() / total_entradas, n

    pct1, n1 = pct_topo(0.01)
    pct10, n10 = pct_topo(0.10)
    pct50, n50 = pct_topo(0.50)

    print(f"\nCurva de Pareto ({n_artistas} artistas, {total_entradas} posicoes no total):")
    print(f"  topo 1% ({n1} artistas): {pct1:.1%} das posicoes  (TCC: 27 artistas, 9,9%)")
    print(f"  topo 10% ({n10} artistas): {pct10:.1%} das posicoes  (TCC: 40,8%)")
    print(f"  metade com mais entradas ({n50} artistas): {pct50:.1%} das posicoes  (TCC: 80,9%)")
    lider = entradas_por_artista.iloc[0]
    print(f"  lider: {lider['artista']}, {lider['n_entradas']} entradas  (TCC: Drake, 44 entradas)")

    entradas_por_artista.to_csv("data/resultado_06_pareto.csv", index=False)
    print("\nResultados salvos em data/resultado_06_*.csv")


if __name__ == "__main__":
    main()
