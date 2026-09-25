"""
03 - Tempo de carreira e reentrada apos hiato

Duas analises sobre a trajetoria de cada artista no chart:

  (a) Tempo de carreira: primeiro ao ultimo ano no chart, para todos os
      artistas exceto os 3 "perenes sazonais" (Brenda Lee, Burl Ives, Wham!),
      que inflam artificialmente a duracao via reentrada anual de um hit
      natalino, nao por carreira ativa (ver nota da secao 1 do TCC).

  (b) Reentrada apos hiato: entre artistas com hit em 2+ anos-calendario
      distintos, quantos anos de silencio (sem hit) se passam entre uma
      aparicao e a seguinte, e com que probabilidade esse hiato "fecha"
      (reentrada) ao longo do tempo. Isso e estimado com Kaplan-Meier.

      unidade: o hiato (intervalo de silencio entre dois hits do mesmo artista)
      origem do tempo: primeiro ano sem hit apos um hit
      evento: reentrada (o artista volta a ter hit)
      censura: hiato ainda aberto em 2025, a ultima janela observavel

Este script implementa o estimador de Kaplan-Meier manualmente (formula
produto-limite classica + erro-padrao de Greenwood), em vez de depender do
pacote "lifelines" - o calculo fica em ~20 linhas e assim o pipeline roda com
so pandas/numpy, sem dependencia externa adicional so para essa etapa.

Entrada:  data/base_limpa.csv
Saida:    data/resultado_03_tempo_carreira.csv
          data/resultado_03_hiatos.csv
          data/resultado_03_kaplan_meier.csv
"""

import numpy as np
import pandas as pd

CAMINHO_ENTRADA = "data/base_limpa.csv"
ULTIMO_ANO_OBSERVADO = 2025

PERENES_SAZONAIS = {"brenda lee", "burl ives", "wham"}


def eh_perene_sazonal(chave_artista: str) -> bool:
    return any(p in chave_artista for p in PERENES_SAZONAIS)


def kaplan_meier(duracoes: np.ndarray, eventos: np.ndarray) -> pd.DataFrame:
    """Estimador produto-limite classico.

    duracoes: tempo ate o evento ou ate a censura, por observacao
    eventos:  1 se reentrada observada, 0 se censurado (hiato ainda aberto)

    Retorna uma tabela com S(t) (probabilidade de o hiato continuar aberto
    apos t anos) e o erro-padrao de Greenwood, para cada tempo de evento.
    """
    tempos_evento = np.unique(duracoes[eventos == 1])
    s = 1.0
    var_acumulada = 0.0
    linhas = []
    for t in tempos_evento:
        em_risco = (duracoes >= t).sum()
        falhas = ((duracoes == t) & (eventos == 1)).sum()
        if em_risco == 0:
            continue
        s *= 1 - falhas / em_risco
        if em_risco > falhas:
            var_acumulada += falhas / (em_risco * (em_risco - falhas))
        erro_padrao = s * np.sqrt(var_acumulada)
        linhas.append({"tempo": t, "sobrevida": s, "erro_padrao": erro_padrao, "em_risco": em_risco, "eventos": falhas})
    return pd.DataFrame(linhas)


def main():
    df = pd.read_csv(CAMINHO_ENTRADA)

    por_artista = (
        df.groupby("ARTISTA_CHAVE")
        .agg(
            artista_nome=("ARTISTA_PRINCIPAL", "first"),
            primeiro_ano=("ANO_CHART", "min"),
            ultimo_ano=("ANO_CHART", "max"),
            anos_com_hit=("ANO_CHART", lambda s: sorted(s.unique())),
        )
        .reset_index()
    )
    por_artista["perene_sazonal"] = por_artista["ARTISTA_CHAVE"].apply(eh_perene_sazonal)
    por_artista["duracao_carreira"] = por_artista["ultimo_ano"] - por_artista["primeiro_ano"] + 1

    # --- (a) Tempo de carreira, excluindo os perenes sazonais ---
    carreira = por_artista[~por_artista["perene_sazonal"]].copy()
    carreira_mediana = carreira["duracao_carreira"].median()
    carreira_media = carreira["duracao_carreira"].mean()
    pct_um_ano = (carreira["duracao_carreira"] == 1).mean()
    mais_longa = carreira.sort_values("duracao_carreira", ascending=False).iloc[0]

    print("=== Tempo de carreira (perenes sazonais excluidos) ===")
    print(f"N = {len(carreira)} (TCC: 2.702)")
    print(f"Mediana: {carreira_mediana:.0f} ano(s)  (TCC: 1 ano)")
    print(f"Media: {carreira_media:.1f} anos  (TCC: 2,3 anos)")
    print(f"% com carreira de 1 ano: {pct_um_ano:.1%}  (TCC: 60,0%)")
    print(f"Carreira mais longa: {mais_longa['artista_nome']}, {mais_longa['duracao_carreira']} anos"
          f" ({mais_longa['primeiro_ano']}-{mais_longa['ultimo_ano']})  (TCC: Elton John, 50 anos)")

    carreira.to_csv("data/resultado_03_tempo_carreira.csv", index=False)

    # --- (b) Hiatos e reentrada ---
    hiatos = []
    for _, row in por_artista.iterrows():
        anos = row["anos_com_hit"]
        if isinstance(anos, str):
            anos = eval(anos)
        if len(anos) < 2:
            continue
        for a, b in zip(anos, anos[1:]):
            # anos sem hit ESTRITAMENTE entre a e b (hit em anos consecutivos = 0 hiato)
            duracao_hiato = b - a - 1
            if duracao_hiato <= 0:
                continue
            hiatos.append({
                "artista": row["artista_nome"],
                "ano_inicio_hiato": a,
                "ano_reentrada": b,
                "duracao": duracao_hiato,
                "evento": 1,  # todo hiato entre dois hits observados ja "fechou" -> reentrada certa
                "perene_sazonal": row["perene_sazonal"],
            })
        # hiato aberto no fim: do ultimo hit ate o fim da janela observada, se o artista
        # nao tem hit em ULTIMO_ANO_OBSERVADO (censura)
        ultimo = anos[-1]
        if ultimo < ULTIMO_ANO_OBSERVADO:
            hiatos.append({
                "artista": row["artista_nome"],
                "ano_inicio_hiato": ultimo,
                "ano_reentrada": None,
                "duracao": ULTIMO_ANO_OBSERVADO - ultimo,
                "evento": 0,  # censurado - ainda pode reentrar apos 2025
                "perene_sazonal": row["perene_sazonal"],
            })

    hiatos_df = pd.DataFrame(hiatos)
    hiatos_fechados = hiatos_df[hiatos_df["evento"] == 1]

    n_artistas_com_2mais = (por_artista["anos_com_hit"].apply(
        lambda anos: len(eval(anos) if isinstance(anos, str) else anos)
    ) >= 2).sum()
    n_com_hiato = hiatos_df.loc[hiatos_df["artista"].isin(
        hiatos_fechados["artista"]) | (hiatos_df["evento"] == 0), "artista"].nunique()

    print("\n=== Reentrada apos hiato ===")
    print(f"Artistas com hit em 2+ anos distintos: {n_artistas_com_2mais}  (TCC: 1.081)")
    print(f"Hiatos identificados (fechados + censurados): {len(hiatos_df)}  (TCC: 1.121 hiatos fechados)")
    print(f"Mediana dos hiatos fechados: {hiatos_fechados['duracao'].median():.0f} anos  (TCC: 2 anos)")

    hiatos_df.to_csv("data/resultado_03_hiatos.csv", index=False)

    # Kaplan-Meier sobre TODOS os hiatos (fechados = evento, abertos em 2025 = censura)
    km = kaplan_meier(hiatos_df["duracao"].to_numpy(), hiatos_df["evento"].to_numpy())
    km.to_csv("data/resultado_03_kaplan_meier.csv", index=False)

    def sobrevida_em(t):
        sub = km[km["tempo"] <= t]
        return sub["sobrevida"].iloc[-1] if len(sub) else 1.0

    print(f"\nKaplan-Meier - probabilidade de o hiato SEGUIR aberto (nao reentrar):")
    print(f"  em 2 anos: {sobrevida_em(2):.1%}  -> reentrada acumulada {1 - sobrevida_em(2):.1%}  (TCC: 80,6% em 2 anos)")
    print(f"  em 5 anos: {sobrevida_em(5):.1%}  -> reentrada acumulada {1 - sobrevida_em(5):.1%}  (TCC: 73,8% em 5)")
    print(f"  platô de longo prazo (>=20 anos): {sobrevida_em(20):.1%} segue aberto  (TCC: ~69,2%)")
    print("\nResultados salvos em data/resultado_03_*.csv")


if __name__ == "__main__":
    main()
