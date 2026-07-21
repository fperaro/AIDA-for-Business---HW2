"""
HW2 - Metriche combinate: produttività pesata per il carico di lavoro.

NOTA METODOLOGICA: le metriche costruite qui
NON sono standard - formula e pesi 50-50 sono scelte arbitrarie.
Le presento come esercizio di sensibilità della classifica alla
normalizzazione scelta, non come classifica alternativa.

Altre scelte:
- indice di carico = media di iscritti/docente e iscritti/PTA, ciascuno
  normalizzato sulla media del gruppo
- produttività aggiustata = pubblicazioni/docente senza medica x indice di carico
- VQR (ANVUR 16/04/2026) hardcoded: dato esterno, 7 valori fissi


"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

DATA_DIR = Path(__file__).parent
OUT_DIR = Path(__file__).parent

BERGAMO = "Bergamo"
COLORE_BERGAMO = "#1F2A44"
COLORE_ALTRI = "#B7C3D6"
COLORE_ACCENTO = "#C0392B"

COLORI_ATENEI = {
    "Bergamo": COLORE_BERGAMO,
    "Brescia": "#5B7A9D",
    "Ca' Foscari Venezia": "#8E7CC3",
    "Ferrara": "#C79A3B",
    "Modena e Reggio Emilia": "#4C9F70",
    "Pavia": "#D4739B",
    "Trieste": "#E08E45",
}


def colore_ateneo(nome):
    return COLORI_ATENEI.get(nome, "#999999")

VQR_R1_2 = {
    "Bergamo": 1.002,
    "Brescia": 1.015,
    "Pavia": 1.033,
    "Ferrara": 1.019,
    "Modena e Reggio Emilia": 1.002,
    "Trieste": 1.010,
    "Ca' Foscari Venezia": 1.031,
}
VQR_R4 = {
    "Bergamo": 1.213,
    "Brescia": 0.819,
    "Pavia": 1.051,
    "Ferrara": 1.094,
    "Modena e Reggio Emilia": 1.055,
    "Trieste": 1.176,
    "Ca' Foscari Venezia": 1.197,
}

plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
})


def grafico_13_numerosita_nel_tempo():
    master_path = DATA_DIR / "master_normalizzazione_7_atenei.json"
    with open(master_path, encoding="utf-8") as f:
        master = json.load(f)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16.5, 5.8))

    for ateneo, d in master.items():
        colore = colore_ateneo(ateneo)
        lw = 3 if ateneo == BERGAMO else 1.8
        zo = 5 if ateneo == BERGAMO else 2
        anni = sorted(int(a) for a in d["serie_docenti_2015_2024"].keys())
        docenti = [d["serie_docenti_2015_2024"][str(a)]["narrow"] for a in anni]
        pta = [d["serie_pta_2015_2024"][str(a)]["PTA"] for a in anni]
        iscritti = [d["serie_iscritti_2015_2024"].get(f"{a}/{a+1}") for a in anni]
        ax1.plot(anni, docenti, color=colore, linewidth=lw, marker="o", markersize=3.5, label=ateneo, zorder=zo)
        ax2.plot(anni, iscritti, color=colore, linewidth=lw, marker="o", markersize=3.5, label=ateneo, zorder=zo)
        ax3.plot(anni, pta, color=colore, linewidth=lw, marker="o", markersize=3.5, label=ateneo, zorder=zo)

    ax1.set_title("Docenti e ricercatori")
    ax2.set_title("Iscritti")
    ax3.set_title("Personale tecnico-amministrativo")
    for ax in (ax1, ax2, ax3):
        ax.set_xlabel("Anno")
    ax1.set_ylabel("Numero")
    ax1.legend(loc="upper left", fontsize=7.5, frameon=False)

    fig.suptitle("Le dimensioni degli atenei nel tempo, 2015-2024 (fonte: USTAT MUR)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_13_numerosita_nel_tempo.png", dpi=150)
    plt.close(fig)


def costruisci_metriche() -> pd.DataFrame:
    df4 = pd.read_csv(DATA_DIR / "risultato_4_normalizzato.csv")
    df4b = pd.read_csv(DATA_DIR / "risultato_4b_normalizzato_senza_medica.csv")
    df = df4.merge(df4b[["nome_ateneo", "pubblicazioni_per_docente_senza_medica"]], on="nome_ateneo")

    df["vqr_R1_2"] = df["nome_ateneo"].map(VQR_R1_2)
    df["vqr_R4"] = df["nome_ateneo"].map(VQR_R4)

    carico_did = df["iscritti_per_docente"] / df["iscritti_per_docente"].mean()
    carico_amm = df["iscritti_per_pta"] / df["iscritti_per_pta"].mean()
    df["indice_carico"] = ((carico_did + carico_amm) / 2).round(2)

    # metrica non standard, vedi nota metodologica in testa al file
    df["produttivita_aggiustata"] = (
        df["pubblicazioni_per_docente_senza_medica"] * df["indice_carico"]
    ).round(2)

    return df.sort_values("produttivita_aggiustata", ascending=False)


def grafico_10_produttivita_aggiustata(df: pd.DataFrame):
    df_plot = df.sort_values("produttivita_aggiustata", ascending=True)

    fig, ax = plt.subplots(figsize=(11, 6.5))
    y = range(len(df_plot))
    h = 0.35
    colori_agg = [COLORE_BERGAMO if a == BERGAMO else "#5B7A9D" for a in df_plot["nome_ateneo"]]

    ax.barh([i + h/2 for i in y], df_plot["pubblicazioni_per_docente_senza_medica"], height=h,
            color="#D8DEE9", label="Pubblicazioni/docente (senza area medica)")
    ax.barh([i - h/2 for i in y], df_plot["produttivita_aggiustata"], height=h,
            color=colori_agg, label="Aggiustata per il carico di lavoro")

    ax.set_yticks(list(y))
    ax.set_yticklabels(df_plot["nome_ateneo"])
    ax.set_xlabel("Pubblicazioni per docente (2015-2025)")
    ax.set_title(
        "Produttività grezza e produttività aggiustata per il carico di lavoro\n"
        "Metrica non standard, definita per questo lavoro: mostra la sensibilità della classifica alla normalizzazione scelta",
        fontsize=11,
    )
    ax.legend(loc="lower right", frameon=False, fontsize=9)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_10_produttivita_aggiustata.png", dpi=150)
    plt.close(fig)


def grafico_11_quadranti_carico_qualita(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 7.5))

    for _, r in df.iterrows():
        colore = COLORE_BERGAMO if r["nome_ateneo"] == BERGAMO else COLORE_ALTRI
        dimensione = r["iscritti_2024"] / 15
        ax.scatter(r["indice_carico"], r["vqr_R1_2"], s=dimensione,
                   color=colore, edgecolor="white", linewidth=1.5, zorder=3)
        ax.annotate(r["nome_ateneo"], (r["indice_carico"], r["vqr_R1_2"]),
                    xytext=(7, 7), textcoords="offset points", fontsize=9)

    ax.axhline(1.0, color=COLORE_ACCENTO, linestyle="--", linewidth=1, zorder=1)
    ax.axvline(1.0, color="#999999", linestyle="--", linewidth=1, zorder=1)
    ax.text(ax.get_xlim()[0] + 0.02, 1.001, "media nazionale VQR", color=COLORE_ACCENTO, fontsize=8, va="bottom")
    ax.text(1.005, ax.get_ylim()[0] + 0.001, "carico medio del gruppo", color="#666666", fontsize=8, rotation=90, va="bottom")

    ax.set_xlabel("Indice di carico complessivo (1,0 = media del gruppo)")
    ax.set_ylabel("VQR 2020-2024, indicatore R1_2 (1,0 = media nazionale)")
    ax.set_title("Carico di lavoro e qualità della ricerca\n(dimensione della bolla = iscritti 2024/25)")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_11_quadranti_carico_qualita.png", dpi=150)
    plt.close(fig)


def grafico_12_correlazione_carico_produttivita(df: pd.DataFrame):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5))

    for ax, sotto_df, titolo in [
        (ax1, df, "Tutti e 7 gli atenei"),
        (ax2, df[df["nome_ateneo"] != "Ferrara"], "Senza Ferrara"),
    ]:
        for _, r in sotto_df.iterrows():
            colore = COLORE_BERGAMO if r["nome_ateneo"] == BERGAMO else COLORE_ALTRI
            ax.scatter(r["indice_carico"], r["pubblicazioni_per_docente"],
                       s=110, color=colore, edgecolor="white", linewidth=1.3, zorder=3)
            ax.annotate(r["nome_ateneo"], (r["indice_carico"], r["pubblicazioni_per_docente"]),
                        xytext=(6, 6), textcoords="offset points", fontsize=8.5)

        r_val, p_val = stats.pearsonr(sotto_df["indice_carico"], sotto_df["pubblicazioni_per_docente"])
        coeff = np.polyfit(sotto_df["indice_carico"], sotto_df["pubblicazioni_per_docente"], 1)
        x_retta = np.linspace(sotto_df["indice_carico"].min(), sotto_df["indice_carico"].max(), 50)
        ax.plot(x_retta, np.polyval(coeff, x_retta), color=COLORE_ACCENTO, linewidth=1.2, linestyle="--", zorder=1)

        n = len(sotto_df)
        ax.text(
            0.03, 0.05,
            f"r = {r_val:.2f}   (p = {p_val:.2f}, n = {n})",
            transform=ax.transAxes, fontsize=10.5, color=COLORE_ACCENTO,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=COLORE_ACCENTO, linewidth=0.8),
        )
        ax.set_title(titolo)
        ax.set_xlabel("Indice di carico complessivo (1,0 = media del gruppo)")
        ax.set_ylabel("Pubblicazioni per docente")

    fig.suptitle("Carico di lavoro complessivo e produttività: la correlazione regge?")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_12_correlazione_carico_produttivita.png", dpi=150)
    plt.close(fig)


def costruisci_serie_temporale_aggiustata() -> pd.DataFrame:
    with open(DATA_DIR / "master_normalizzazione_7_atenei.json", encoding="utf-8") as f:
        master = json.load(f)
    pub = pd.read_csv(DATA_DIR / "risultato_2c_produttivita_annuale_senza_medica.csv")

    righe = []
    for anno in range(2015, 2025):
        carichi_anno = {}
        for ateneo, dati in master.items():
            doc = dati["serie_docenti_2015_2024"].get(str(anno), {}).get("narrow")
            pta = dati["serie_pta_2015_2024"].get(str(anno), {}).get("PTA")
            isc = dati["serie_iscritti_2015_2024"].get(f"{anno}/{anno+1}")
            if doc and pta and isc:
                carichi_anno[ateneo] = {"iscritti_per_docente": isc / doc, "iscritti_per_pta": isc / pta}

        media_did = sum(v["iscritti_per_docente"] for v in carichi_anno.values()) / len(carichi_anno)
        media_amm = sum(v["iscritti_per_pta"] for v in carichi_anno.values()) / len(carichi_anno)

        for ateneo, carico in carichi_anno.items():
            indice_carico = ((carico["iscritti_per_docente"] / media_did) + (carico["iscritti_per_pta"] / media_amm)) / 2
            riga_pub = pub[(pub["nome_ateneo"] == ateneo) & (pub["anno"] == anno)]
            if riga_pub.empty or pd.isna(riga_pub["pubblicazioni_per_docente_senza_medica"].values[0]):
                continue
            pub_docente = riga_pub["pubblicazioni_per_docente_senza_medica"].values[0]
            righe.append({
                "nome_ateneo": ateneo, "anno": anno,
                "indice_carico": round(indice_carico, 2),
                "pubblicazioni_per_docente_senza_medica": pub_docente,
                "produttivita_aggiustata": round(pub_docente * indice_carico, 2),
            })

    return pd.DataFrame(righe)


def grafico_14_serie_aggiustata_nel_tempo(df_serie: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 6))
    for ateneo, gruppo in df_serie.groupby("nome_ateneo"):
        gruppo = gruppo.sort_values("anno")
        if ateneo == BERGAMO:
            ax.plot(gruppo["anno"], gruppo["produttivita_aggiustata"], color=COLORE_BERGAMO,
                    linewidth=3, marker="o", label=ateneo, zorder=5)
        else:
            ax.plot(gruppo["anno"], gruppo["produttivita_aggiustata"], color=colore_ateneo(ateneo),
                    linewidth=1.8, alpha=0.9, label=ateneo, zorder=2)

    ax.set_title(
        "Pubblicazioni per docente, senza area medica, aggiustate per il carico di lavoro\n"
        "(2015-2024 - metrica non standard, vedi nota metodologica)"
    )
    ax.set_xlabel("Anno")
    ax.set_ylabel("Produttività aggiustata")
    ax.set_ylim(0, 5)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_14_serie_aggiustata_nel_tempo.png", dpi=150)
    plt.close(fig)


def main():
    df = costruisci_metriche()

    colonne = [
        "nome_ateneo", "pubblicazioni_per_docente", "pubblicazioni_per_docente_senza_medica",
        "iscritti_per_docente", "iscritti_per_pta", "indice_carico",
        "produttivita_aggiustata", "vqr_R1_2", "vqr_R4",
    ]
    print(df[colonne].to_string(index=False))
    df[colonne].to_csv(OUT_DIR / "risultato_5_metriche_combinate.csv", index=False)

    grafico_10_produttivita_aggiustata(df)
    grafico_11_quadranti_carico_qualita(df)
    grafico_12_correlazione_carico_produttivita(df)
    grafico_13_numerosita_nel_tempo()

    df_serie = costruisci_serie_temporale_aggiustata()
    grafico_14_serie_aggiustata_nel_tempo(df_serie)
    df_serie.to_csv(OUT_DIR / "risultato_6_serie_aggiustata_nel_tempo.csv", index=False)

    print()
    print("Salvato risultato_5_metriche_combinate.csv, risultato_6_serie_aggiustata_nel_tempo.csv e 4 grafici.")
    print()
    print("PROMEMORIA: la 'produttivita_aggiustata' è una metrica che ho definito io,")
    print("non uno standard. La presento come esercizio di sensibilità, non come")
    print("classifica alternativa da prendere per buona.")


if __name__ == "__main__":
    main()
