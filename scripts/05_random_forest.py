"""
05 - Random Forest: o audio da estreia preve a longevidade?

Pergunta: usando so o perfil sonoro do hit de ESTREIA de um artista, da para
prever se ele vai virar cross-geracional (2+ decadas)? Mesma configuracao da
Metodologia do TCC:

  RandomForestClassifier(n_estimators=500, random_state=42), profundidade
  livre. Alvo: status cross-geracional (definido no script 02). Preditores:
  BPM, Dancabilidade, Energia, Acustica, Valencia, Volume, Duracao,
  Popularidade (do Spotify) e posicao de estreia no chart - 9 variaveis.
  Validacao cruzada estratificada, 5 folds, separacao no nivel do artista
  (cada artista aparece so uma vez: o hit de estreia).

  Uma arvore de decisao rasa (profundidade 3) e treinada em paralelo como
  versao didatica/visual do mesmo resultado.

Entrada:  data/base_limpa.csv, data/resultado_02_cross_geracionalidade.csv
Saida:    data/resultado_05_importancia_variaveis.csv
          data/resultado_05_metricas.csv
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import StratifiedKFold
from sklearn.tree import DecisionTreeClassifier

CAMINHO_BASE = "data/base_limpa.csv"
CAMINHO_CROSS = "data/resultado_02_cross_geracionalidade.csv"

FEATURES_AUDIO = ["BPM", "ENERGY", "DANCE", "LOUD", "VALENCE", "ACOUSTIC"]
FEATURES_RF = FEATURES_AUDIO + ["LENGTH_SEG", "POP.", "POSICAO_ESTREIA"]
RANDOM_STATE = 42


def main():
    df = pd.read_csv(CAMINHO_BASE)
    for col in FEATURES_AUDIO + ["LENGTH_SEG", "POP.", "#"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    cross = pd.read_csv(CAMINHO_CROSS)[["ARTISTA_CHAVE", "cross_geracional"]]

    validas = df[df["INCLUIR_ANALISE_BOOL"] & df[FEATURES_AUDIO].notna().all(axis=1)].copy()
    validas = validas.sort_values(["ARTISTA_CHAVE", "ANO_CHART"])
    estreia = validas.groupby("ARTISTA_CHAVE").first().reset_index()
    estreia["POSICAO_ESTREIA"] = estreia["#"]

    base_rf = estreia.merge(cross, on="ARTISTA_CHAVE", how="inner")
    base_rf = base_rf[base_rf[FEATURES_RF].notna().all(axis=1)].copy()
    print(f"Artistas com perfil de audio valido na estreia: {len(base_rf)}  (TCC: 2.644)")

    X = base_rf[FEATURES_RF].to_numpy()
    y = base_rf["cross_geracional"].astype(int).to_numpy()
    taxa_base = y.mean()
    print(f"Taxa-base de cross-geracionais nesta amostra: {taxa_base:.1%}  (TCC: 18,9%)")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    aucs_rf, aucs_arvore = [], []
    importancias_permutacao = []
    for treino_idx, teste_idx in cv.split(X, y):
        X_tr, X_te = X[treino_idx], X[teste_idx]
        y_tr, y_te = y[treino_idx], y[teste_idx]

        rf = RandomForestClassifier(n_estimators=500, random_state=RANDOM_STATE)
        rf.fit(X_tr, y_tr)
        p_rf = rf.predict_proba(X_te)[:, 1]
        aucs_rf.append(roc_auc_score(y_te, p_rf))

        perm = permutation_importance(rf, X_te, y_te, scoring="roc_auc", n_repeats=30, random_state=RANDOM_STATE)
        importancias_permutacao.append(perm.importances_mean)

        arvore = DecisionTreeClassifier(max_depth=3, random_state=RANDOM_STATE)
        arvore.fit(X_tr, y_tr)
        p_arvore = arvore.predict_proba(X_te)[:, 1]
        aucs_arvore.append(roc_auc_score(y_te, p_arvore))

    print(f"\nRandom Forest - AUC-ROC (5 folds): {np.mean(aucs_rf):.3f} (+/- {np.std(aucs_rf):.3f})"
          f"  (TCC: 0,549 +/- 0,010)")
    print(f"Arvore de decisao (prof. 3) - AUC-ROC (5 folds): {np.mean(aucs_arvore):.3f} (+/- {np.std(aucs_arvore):.3f})"
          f"  (TCC: 0,531 +/- 0,013)")

    # Random Forest final, na base completa, para reportar a importancia por impureza (MDI)
    rf_final = RandomForestClassifier(n_estimators=500, random_state=RANDOM_STATE)
    rf_final.fit(X, y)
    importancia_mdi = pd.Series(rf_final.feature_importances_, index=FEATURES_RF).sort_values(ascending=False)
    print("\nImportancia por impureza (MDI), base completa:")
    print(importancia_mdi.round(3))

    importancia_perm_media = pd.Series(np.mean(importancias_permutacao, axis=0), index=FEATURES_RF).sort_values(ascending=False)
    print("\nImportancia por permutacao (queda de AUC-ROC, media entre folds):")
    print(importancia_perm_media.round(3))

    resumo = pd.DataFrame({
        "variavel": FEATURES_RF,
        "importancia_mdi": [importancia_mdi[f] for f in FEATURES_RF],
        "importancia_permutacao": [importancia_perm_media[f] for f in FEATURES_RF],
    })
    resumo.to_csv("data/resultado_05_importancia_variaveis.csv", index=False)

    metricas = pd.DataFrame([{
        "auc_roc_rf_medio": np.mean(aucs_rf),
        "auc_roc_rf_desvio": np.std(aucs_rf),
        "auc_roc_arvore_medio": np.mean(aucs_arvore),
        "auc_roc_arvore_desvio": np.std(aucs_arvore),
        "n_artistas": len(base_rf),
        "taxa_base_cross_geracional": taxa_base,
    }])
    metricas.to_csv("data/resultado_05_metricas.csv", index=False)
    print("\nResultados salvos em data/resultado_05_*.csv")


if __name__ == "__main__":
    main()
