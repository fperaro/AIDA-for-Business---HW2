

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

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

plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def colori_per_ateneo(nomi):
    return [COLORE_BERGAMO if n == BERGAMO else COLORE_ALTRI for n in nomi]


def grafico_1_serie_storica():
    df = pd.read_csv(DATA_DIR / "risultato_2_andamento_temporale.csv")
    fig, ax = plt.subplots(figsize=(10, 6))

    for ateneo, gruppo in df.groupby("nome_ateneo"):
        gruppo = gruppo.sort_values("anno")
        if ateneo == BERGAMO:
            ax.plot(gruppo["anno"], gruppo["n_pubblicazioni"], color=COLORE_BERGAMO,
                    linewidth=3, marker="o", label=ateneo, zorder=5)
        else:
            ax.plot(gruppo["anno"], gruppo["n_pubblicazioni"], color=colore_ateneo(ateneo),
                    linewidth=1.8, alpha=0.9, label=ateneo, zorder=2)

    ax.set_title("Andamento delle pubblicazioni per ateneo, 2015-2025\n(articoli e review, copertura OpenAlex affidabile)")
    ax.set_xlabel("Anno")
    ax.set_ylabel("Numero di pubblicazioni")
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_1_serie_storica.png", dpi=150)
    plt.close(fig)


def grafico_2_area_disciplinare():
    df = pd.read_csv(DATA_DIR / "risultato_1_area_disciplinare.csv")
    pivot = df.pivot(index="nome_ateneo", columns="area_disciplinare", values="n_pubblicazioni").fillna(0)

    # Bergamo per ultimo = barra piu' in basso, la prima che si legge
    ordine = [a for a in pivot.index if a != BERGAMO] + [BERGAMO]
    pivot = pivot.loc[ordine]

    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    colori_aree = ["#1F2A44", "#5B7A9D", "#9BB3CC", "#D8DEE9", "#C0392B"]
    pivot_pct.plot(kind="barh", stacked=True, ax=ax, color=colori_aree[:len(pivot_pct.columns)])

    ax.set_title("Distribuzione della produzione per area disciplinare\n(quota percentuale sul totale di ciascun ateneo)")
    ax.set_xlabel("Quota percentuale")
    ax.set_ylabel("")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_2_area_disciplinare.png", dpi=150)
    plt.close(fig)


def grafico_3_open_access():
    df = pd.read_csv(DATA_DIR / "risultato_3_open_access.csv")
    df = df.sort_values("tasso_oa_percentuale", ascending=True)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.barh(df["nome_ateneo"], df["tasso_oa_percentuale"], color=colori_per_ateneo(df["nome_ateneo"]))
    for y, val in enumerate(df["tasso_oa_percentuale"]):
        ax.text(val + 1, y, f"{val:.1f}%", va="center", fontsize=9)

    ax.set_title("Tasso di accesso aperto (open access) per ateneo")
    ax.set_xlabel("Percentuale di pubblicazioni ad accesso aperto")
    ax.set_xlim(0, 100)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_3_open_access.png", dpi=150)
    plt.close(fig)


def grafico_4_produttivita_con_senza_medica():
    df4 = pd.read_csv(DATA_DIR / "risultato_4_normalizzato.csv")
    df4b = pd.read_csv(DATA_DIR / "risultato_4b_normalizzato_senza_medica.csv")
    df = df4.merge(df4b[["nome_ateneo", "pubblicazioni_per_docente_senza_medica"]], on="nome_ateneo")
    df = df.sort_values("pubblicazioni_per_docente", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    y = range(len(df))
    h = 0.35
    ax.barh([i + h/2 for i in y], df["pubblicazioni_per_docente"], height=h,
            color="#9BB3CC", label="Totale (con area medica)")
    ax.barh([i - h/2 for i in y], df["pubblicazioni_per_docente_senza_medica"], height=h,
            color=COLORE_BERGAMO, label="Escludendo l'area medica")
    ax.set_yticks(list(y))
    ax.set_yticklabels(df["nome_ateneo"])

    ax.set_title("Pubblicazioni per docente, con e senza l'area medica\n(2015-2025, articoli e review)")
    ax.set_xlabel("Pubblicazioni per docente")
    ax.legend(loc="lower right", frameon=False, fontsize=9)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_4_produttivita_con_senza_medica.png", dpi=150)
    plt.close(fig)


def grafico_5_carico_vs_produttivita():
    df = pd.read_csv(DATA_DIR / "risultato_4_normalizzato.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

    for ax, colonna_x, titolo_x in [
        (ax1, "iscritti_per_docente", "Iscritti per docente (carico didattico)"),
        (ax2, "iscritti_per_pta", "Iscritti per addetto PTA (carico amministrativo)"),
    ]:
        for _, riga in df.iterrows():
            colore = COLORE_BERGAMO if riga["nome_ateneo"] == BERGAMO else COLORE_ALTRI
            dimensione_bolla = riga["iscritti_2024"] / 15
            ax.scatter(riga[colonna_x], riga["pubblicazioni_per_docente"],
                       s=dimensione_bolla, color=colore, edgecolor="white", linewidth=1.5, zorder=3)
            ax.annotate(riga["nome_ateneo"], (riga[colonna_x], riga["pubblicazioni_per_docente"]),
                        xytext=(6, 6), textcoords="offset points", fontsize=8.5)
        ax.set_xlabel(titolo_x)
        ax.set_ylabel("Pubblicazioni per docente (2015-2025)")

    fig.suptitle("Produttività scientifica contro carico didattico e carico amministrativo\n(dimensione della bolla = iscritti 2024/25)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_5_carico_vs_produttivita.png", dpi=150)
    plt.close(fig)


def grafico_6_serie_storica_per_docente():
    df = pd.read_csv(DATA_DIR / "risultato_2b_produttivita_annuale.csv")
    df = df.dropna(subset=["pubblicazioni_per_docente"])

    fig, ax = plt.subplots(figsize=(10, 6))
    for ateneo, gruppo in df.groupby("nome_ateneo"):
        gruppo = gruppo.sort_values("anno")
        if ateneo == BERGAMO:
            ax.plot(gruppo["anno"], gruppo["pubblicazioni_per_docente"], color=COLORE_BERGAMO,
                    linewidth=3, marker="o", label=ateneo, zorder=5)
        else:
            ax.plot(gruppo["anno"], gruppo["pubblicazioni_per_docente"], color=colore_ateneo(ateneo),
                    linewidth=1.8, alpha=0.9, label=ateneo, zorder=2)

    ax.set_title("Pubblicazioni per docente, anno per anno (2015-2024)\n(articoli e review, copertura OpenAlex affidabile)")
    ax.set_xlabel("Anno")
    ax.set_ylabel("Pubblicazioni per docente")
    ax.set_ylim(0, 5)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_6_serie_storica_per_docente.png", dpi=150)
    plt.close(fig)


def grafico_7_serie_storica_senza_medica():
    df = pd.read_csv(DATA_DIR / "risultato_2c_produttivita_annuale_senza_medica.csv")
    df = df.dropna(subset=["pubblicazioni_per_docente_senza_medica"])

    fig, ax = plt.subplots(figsize=(10, 6))
    for ateneo, gruppo in df.groupby("nome_ateneo"):
        gruppo = gruppo.sort_values("anno")
        if ateneo == BERGAMO:
            ax.plot(gruppo["anno"], gruppo["pubblicazioni_per_docente_senza_medica"], color=COLORE_BERGAMO,
                    linewidth=3, marker="o", label=ateneo, zorder=5)
        else:
            ax.plot(gruppo["anno"], gruppo["pubblicazioni_per_docente_senza_medica"], color=colore_ateneo(ateneo),
                    linewidth=1.8, alpha=0.9, label=ateneo, zorder=2)

    ax.set_title("Pubblicazioni per docente, anno per anno, escludendo l'area medica\n(2015-2024)")
    ax.set_xlabel("Anno")
    ax.set_ylabel("Pubblicazioni per docente (senza area medica)")
    ax.set_ylim(0, 5)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_7_serie_storica_senza_medica.png", dpi=150)
    plt.close(fig)


def grafico_8_carico_nel_tempo():
    master_path = DATA_DIR / "master_normalizzazione_7_atenei.json"
    if not master_path.exists():
        print(f"ATTENZIONE: non trovo {master_path}, salto grafico_8. "
              f"Aggiorna il percorso in cima alla funzione se la tua struttura di cartelle è diversa.")
        return

    with open(master_path, encoding="utf-8") as f:
        master = json.load(f)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

    for ateneo, dati in master.items():
        colore = colore_ateneo(ateneo)
        linewidth = 3 if ateneo == BERGAMO else 1.8
        zorder = 5 if ateneo == BERGAMO else 2

        anni = sorted(int(a) for a in dati["serie_docenti_2015_2024"].keys())
        iscritti_per_docente = []
        iscritti_per_pta = []
        for anno in anni:
            doc = dati["serie_docenti_2015_2024"][str(anno)]["narrow"]
            pta = dati["serie_pta_2015_2024"][str(anno)]["PTA"]
            isc = dati["serie_iscritti_2015_2024"].get(f"{anno}/{anno+1}")
            iscritti_per_docente.append(isc / doc if isc and doc else None)
            iscritti_per_pta.append(isc / pta if isc and pta else None)

        ax1.plot(anni, iscritti_per_docente, color=colore, linewidth=linewidth, marker="o",
                 markersize=4, label=ateneo, zorder=zorder)
        ax2.plot(anni, iscritti_per_pta, color=colore, linewidth=linewidth, marker="o",
                 markersize=4, label=ateneo, zorder=zorder)

    ax1.set_title("Carico didattico nel tempo\n(iscritti per docente)")
    ax1.set_xlabel("Anno")
    ax1.set_ylabel("Iscritti per docente")
    ax1.legend(loc="upper right", fontsize=8, frameon=False)

    ax2.set_title("Carico amministrativo nel tempo\n(iscritti per addetto PTA)")
    ax2.set_xlabel("Anno")
    ax2.set_ylabel("Iscritti per addetto PTA")

    fig.suptitle("Bergamo ha il carico più alto del gruppo (livello 2024) - qui l'andamento nel tempo")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_8_carico_nel_tempo.png", dpi=150)
    plt.close(fig)


def grafico_9_vqr():
    # VQR 2020-2024, presentazione ufficiale ANVUR 16/04/2026
    dati_vqr = {
        "Bergamo": {"R1_2": 1.002, "R4": 1.213},
        "Brescia": {"R1_2": 1.015, "R4": 0.819},
        "Ferrara": {"R1_2": 1.019, "R4": 1.094},
        "Modena e Reggio Emilia": {"R1_2": 1.002, "R4": 1.055},
        "Pavia": {"R1_2": 1.033, "R4": 1.051},
        "Trieste": {"R1_2": 1.010, "R4": 1.176},
        "Ca' Foscari Venezia": {"R1_2": 1.031, "R4": 1.197},
    }
    df = pd.DataFrame(dati_vqr).T.reset_index().rename(columns={"index": "nome_ateneo"})
    df = df.sort_values("R4", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    y = range(len(df))
    h = 0.35
    ax.barh([i + h/2 for i in y], df["R1_2"], height=h, color="#9BB3CC", label="R1_2 - qualità della ricerca")
    ax.barh([i - h/2 for i in y], df["R4"], height=h,
            color=[COLORE_BERGAMO if a == BERGAMO else "#5B7A9D" for a in df["nome_ateneo"]],
            label="R4 - valorizzazione della conoscenza")
    ax.axvline(1.0, color=COLORE_ACCENTO, linewidth=1, linestyle="--", zorder=1)
    ax.text(1.0, len(df) - 0.3, "media nazionale", color=COLORE_ACCENTO, fontsize=8, ha="left")

    ax.set_yticks(list(y))
    ax.set_yticklabels(df["nome_ateneo"])
    ax.set_title("VQR 2020-2024: qualità della ricerca e valorizzazione della conoscenza\n(fonte: ANVUR, presentazione ufficiale 16/04/2026)")
    ax.set_xlabel("Indicatore R (1,0 = media nazionale)")
    ax.legend(loc="lower right", fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_9_vqr.png", dpi=150)
    plt.close(fig)


def main():
    grafico_1_serie_storica()
    grafico_2_area_disciplinare()
    grafico_3_open_access()
    grafico_4_produttivita_con_senza_medica()
    grafico_5_carico_vs_produttivita()
    grafico_6_serie_storica_per_docente()
    grafico_7_serie_storica_senza_medica()
    grafico_8_carico_nel_tempo()
    grafico_9_vqr()
    print(f"9 grafici salvati in {OUT_DIR}")


if __name__ == "__main__":
    main()
