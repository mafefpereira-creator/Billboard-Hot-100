"""
04 - Clusters sonoros (k-means)

Agrupa as faixas por perfil de audio (6 atributos padronizados por z-score)
para ver se existem "familias sonoras" estaveis atravessando decadas e
generos. Mesma configuracao descrita na Metodologia do TCC:

  scikit-learn KMeans, init="k-means++", n_init=10, random_state=42
  k testado de 2 a 8, escolhido por silhouette medio (amostra de 5.000
  faixas para o silhouette, por custo computacional - a base completa e
  usada para o ajuste do modelo em si) e checado por inercia (metodo do
  cotovelo) sobre a base completa.

Entrada:  data/base_limpa.csv
Saida:    data/resultado_04_inercia_silhouette.csv (k=2..8)
          data/resultado_04_clusters_k2.csv
          data/resultado_04_clusters_k5.csv
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

CAMINHO_ENTRADA = "data/base_limpa.csv"
FEATURES = ["BPM", "ENERGY", "DANCE", "LOUD", "VALENCE", "ACOUSTIC"]
RANDOM_STATE = 42
N_AMOSTRA_SILHOUETTE = 5000


def main():
    df = pd.read_csv(CAMINHO_ENTRADA)
    for col in FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    base = df[df["INCLUIR_ANALISE_BOOL"] & df[FEATURES].notna().all(axis=1)].copy()
    print(f"Faixas com os 6 atributos de audio completos: {len(base)}  (TCC: 6.923)")

    X = StandardScaler().fit_transform(base[FEATURES])

    linhas = []
    amostra_idx = None
    resultados_k = {}
    for k in range(2, 9):
        modelo = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=RANDOM_STATE)
        rotulos = modelo.fit_predict(X)
        resultados_k[k] = rotulos

        if amostra_idx is None:
            rng = np.random.RandomState(RANDOM_STATE)
            amostra_idx = rng.choice(len(X), size=min(N_AMOSTRA_SILHOUETTE, len(X)), replace=False)

        sil = silhouette_score(X[amostra_idx], rotulos[amostra_idx])
        linhas.append({"k": k, "inercia": modelo.inertia_, "silhouette_amostra_5000": sil})
        print(f"k={k}: inercia={modelo.inertia_:,.1f}  silhouette={sil:.3f}")

    pd.DataFrame(linhas).to_csv("data/resultado_04_inercia_silhouette.csv", index=False)

    for k in (2, 5):
        base_k = base.copy()
        base_k["cluster"] = resultados_k[k]
        perfil = base_k.groupby("cluster")[FEATURES].mean().round(1)
        print(f"\nPerfil medio dos clusters, k={k}:")
        print(perfil)
        base_k.to_csv(f"data/resultado_04_clusters_k{k}.csv", index=False)

    print("\nResultados salvos em data/resultado_04_*.csv")
    print("Nota: os arquetipos sonoros (nomes como 'dance-pop', 'acustico/introspectivo')")
    print("foram atribuidos no TCC por interpretacao qualitativa dos centroides de cada")
    print("cluster, nao por um rotulo automatico - por isso nao sao reproduzidos aqui,")
    print("so os valores numericos que embasaram essa leitura.")


if __name__ == "__main__":
    main()
