"""
HW2 - Query di analisi sul DW (datawarehouse.db dell'HW1).

Scelte chiave:
- filtro sempre a article+review (copertura OpenAlex 84% su Bergamo, per gli altri prodotti è molto meno)
- LEFT JOIN su Fact_Personale_Ateneo: la fonte USTAT si ferma al 2024, il 2025 resta NULL
- nelle query "senza medica" il denominatore (docenti) resta il totale ateneo:
  limite già dichiarato non risolvibile con i dati disponibili
- carico amministrativo = iscritti/PTA (e' il volume di studenti a generare il lavoro)

"""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "datawarehouse.db"

FILTRO_TIPO_AFFIDABILE = """
    AND tp.indicizzazione_affidabile = 1
"""


def connetti():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Non trovo {DB_PATH} - metti questo script nella stessa cartella del "
            "database, o aggiorna DB_PATH in cima al file."
        )
    return sqlite3.connect(DB_PATH)


def domanda_1_area_disciplinare(conn) -> pd.DataFrame:
    query = f"""
        SELECT
            a.nome_ateneo,
            COALESCE(ad.domain, 'Non classificato') AS area_disciplinare,
            COUNT(*) AS n_pubblicazioni
        FROM Fact_Pubblicazione_OpenAlex f
        JOIN Dim_Ateneo a ON f.ateneo_id = a.ateneo_id
        JOIN Dim_Tipo_Pubblicazione tp ON f.tipo_id = tp.tipo_id
        LEFT JOIN Dim_Area_Disciplinare ad ON f.area_id = ad.area_id
        WHERE 1=1 {FILTRO_TIPO_AFFIDABILE}
        GROUP BY a.nome_ateneo, area_disciplinare
        ORDER BY a.nome_ateneo, n_pubblicazioni DESC
    """
    return pd.read_sql_query(query, conn)


def domanda_2_andamento_temporale(conn) -> pd.DataFrame:
    query = f"""
        SELECT
            a.nome_ateneo,
            f.anno,
            COUNT(*) AS n_pubblicazioni
        FROM Fact_Pubblicazione_OpenAlex f
        JOIN Dim_Ateneo a ON f.ateneo_id = a.ateneo_id
        JOIN Dim_Tipo_Pubblicazione tp ON f.tipo_id = tp.tipo_id
        WHERE 1=1 {FILTRO_TIPO_AFFIDABILE}
        GROUP BY a.nome_ateneo, f.anno
        ORDER BY a.nome_ateneo, f.anno
    """
    return pd.read_sql_query(query, conn)


def domanda_2b_produttivita_annuale(conn) -> pd.DataFrame:
    query = f"""
        SELECT
            a.nome_ateneo,
            f.anno,
            COUNT(*) AS n_pubblicazioni,
            p.docenti_ricercatori_narrow AS docenti,
            ROUND(1.0 * COUNT(*) / NULLIF(p.docenti_ricercatori_narrow, 0), 2) AS pubblicazioni_per_docente
        FROM Fact_Pubblicazione_OpenAlex f
        JOIN Dim_Ateneo a ON f.ateneo_id = a.ateneo_id
        JOIN Dim_Tipo_Pubblicazione tp ON f.tipo_id = tp.tipo_id
        LEFT JOIN Fact_Personale_Ateneo p ON p.ateneo_id = a.ateneo_id AND p.anno = f.anno
        WHERE 1=1 {FILTRO_TIPO_AFFIDABILE}
        GROUP BY a.nome_ateneo, f.anno, p.docenti_ricercatori_narrow
        ORDER BY a.nome_ateneo, f.anno
    """
    return pd.read_sql_query(query, conn)


def domanda_3_tasso_open_access(conn) -> pd.DataFrame:
    query = f"""
        SELECT
            a.nome_ateneo,
            COUNT(*) AS n_pubblicazioni,
            SUM(f.is_oa) AS n_open_access,
            ROUND(100.0 * SUM(f.is_oa) / COUNT(*), 1) AS tasso_oa_percentuale
        FROM Fact_Pubblicazione_OpenAlex f
        JOIN Dim_Ateneo a ON f.ateneo_id = a.ateneo_id
        JOIN Dim_Tipo_Pubblicazione tp ON f.tipo_id = tp.tipo_id
        WHERE 1=1 {FILTRO_TIPO_AFFIDABILE}
        GROUP BY a.nome_ateneo
        ORDER BY tasso_oa_percentuale DESC
    """
    return pd.read_sql_query(query, conn)


def domanda_4_normalizzato_per_dimensione(conn) -> pd.DataFrame:
    query = f"""
        SELECT
            a.nome_ateneo,
            COUNT(*) AS n_pubblicazioni_totali,
            p.docenti_ricercatori_narrow AS docenti_2024,
            p.iscritti AS iscritti_2024,
            p.pta AS pta_2024,
            a.laureati_2025,
            ROUND(1.0 * COUNT(*) / NULLIF(p.docenti_ricercatori_narrow, 0), 1) AS pubblicazioni_per_docente,
            ROUND(1.0 * COUNT(*) / NULLIF(a.laureati_2025, 0), 2) AS pubblicazioni_per_laureato,
            ROUND(1.0 * p.iscritti / NULLIF(p.docenti_ricercatori_narrow, 0), 1) AS iscritti_per_docente,
            ROUND(1.0 * p.iscritti / NULLIF(p.pta, 0), 1) AS iscritti_per_pta
        FROM Fact_Pubblicazione_OpenAlex f
        JOIN Dim_Ateneo a ON f.ateneo_id = a.ateneo_id
        JOIN Dim_Tipo_Pubblicazione tp ON f.tipo_id = tp.tipo_id
        JOIN Fact_Personale_Ateneo p ON p.ateneo_id = a.ateneo_id AND p.anno = 2024
        WHERE 1=1 {FILTRO_TIPO_AFFIDABILE}
        GROUP BY a.nome_ateneo, p.docenti_ricercatori_narrow, p.iscritti, p.pta, a.laureati_2025
        ORDER BY pubblicazioni_per_docente DESC
    """
    return pd.read_sql_query(query, conn)


def domanda_2c_produttivita_annuale_senza_medica(conn) -> pd.DataFrame:
    query = f"""
        SELECT
            a.nome_ateneo,
            f.anno,
            COUNT(*) AS n_pubblicazioni_senza_area_medica,
            p.docenti_ricercatori_narrow AS docenti,
            ROUND(1.0 * COUNT(*) / NULLIF(p.docenti_ricercatori_narrow, 0), 2) AS pubblicazioni_per_docente_senza_medica
        FROM Fact_Pubblicazione_OpenAlex f
        JOIN Dim_Ateneo a ON f.ateneo_id = a.ateneo_id
        JOIN Dim_Tipo_Pubblicazione tp ON f.tipo_id = tp.tipo_id
        JOIN Dim_Area_Disciplinare ad ON f.area_id = ad.area_id
        LEFT JOIN Fact_Personale_Ateneo p ON p.ateneo_id = a.ateneo_id AND p.anno = f.anno
        WHERE (ad.domain IS NULL OR ad.domain != 'Health Sciences') {FILTRO_TIPO_AFFIDABILE}
        GROUP BY a.nome_ateneo, f.anno, p.docenti_ricercatori_narrow
        ORDER BY a.nome_ateneo, f.anno
    """
    return pd.read_sql_query(query, conn)


def domanda_4b_normalizzato_senza_area_medica(conn) -> pd.DataFrame:
    query = f"""
        SELECT
            a.nome_ateneo,
            COUNT(*) AS n_pubblicazioni_senza_area_medica,
            p.docenti_ricercatori_narrow AS docenti_2024,
            ROUND(1.0 * COUNT(*) / NULLIF(p.docenti_ricercatori_narrow, 0), 1) AS pubblicazioni_per_docente_senza_medica
        FROM Fact_Pubblicazione_OpenAlex f
        JOIN Dim_Ateneo a ON f.ateneo_id = a.ateneo_id
        JOIN Dim_Tipo_Pubblicazione tp ON f.tipo_id = tp.tipo_id
        JOIN Dim_Area_Disciplinare ad ON f.area_id = ad.area_id
        JOIN Fact_Personale_Ateneo p ON p.ateneo_id = a.ateneo_id AND p.anno = 2024
        WHERE (ad.domain IS NULL OR ad.domain != 'Health Sciences') {FILTRO_TIPO_AFFIDABILE}
        GROUP BY a.nome_ateneo, p.docenti_ricercatori_narrow
        ORDER BY pubblicazioni_per_docente_senza_medica DESC
    """
    return pd.read_sql_query(query, conn)


def main():
    conn = connetti()

    print("=" * 70)
    print("DOMANDA 1 - Distribuzione per area disciplinare")
    print("=" * 70)
    df1 = domanda_1_area_disciplinare(conn)
    print(df1.to_string(index=False))

    print()
    print("=" * 70)
    print("DOMANDA 2 - Andamento temporale 2015-2025")
    print("=" * 70)
    df2 = domanda_2_andamento_temporale(conn)
    print(df2.to_string(index=False))

    print()
    print("=" * 70)
    print("DOMANDA 2b - Produttività per docente, anno per anno")
    print("=" * 70)
    df2b = domanda_2b_produttivita_annuale(conn)
    print(df2b.to_string(index=False))

    print()
    print("=" * 70)
    print("DOMANDA 2c - Produttività per docente, anno per anno, senza area medica")
    print("=" * 70)
    df2c = domanda_2c_produttivita_annuale_senza_medica(conn)
    print(df2c.to_string(index=False))

    print()
    print("=" * 70)
    print("DOMANDA 3 - Tasso di open access per ateneo")
    print("=" * 70)
    df3 = domanda_3_tasso_open_access(conn)
    print(df3.to_string(index=False))

    print()
    print("=" * 70)
    print("DOMANDA 4 - Normalizzato per dimensione dell'ateneo")
    print("=" * 70)
    df4 = domanda_4_normalizzato_per_dimensione(conn)
    print(df4.to_string(index=False))

    print()
    print("=" * 70)
    print("DOMANDA 4b - Normalizzato, escludendo l'area medica")
    print("=" * 70)
    df4b = domanda_4b_normalizzato_senza_area_medica(conn)
    print(df4b.to_string(index=False))

    out_dir = Path(__file__).parent
    df1.to_csv(out_dir / "risultato_1_area_disciplinare.csv", index=False)
    df2.to_csv(out_dir / "risultato_2_andamento_temporale.csv", index=False)
    df2b.to_csv(out_dir / "risultato_2b_produttivita_annuale.csv", index=False)
    df2c.to_csv(out_dir / "risultato_2c_produttivita_annuale_senza_medica.csv", index=False)
    df3.to_csv(out_dir / "risultato_3_open_access.csv", index=False)
    df4.to_csv(out_dir / "risultato_4_normalizzato.csv", index=False)
    df4b.to_csv(out_dir / "risultato_4b_normalizzato_senza_medica.csv", index=False)
    print("\nRisultati salvati anche come CSV in questa cartella.")

    conn.close()


if __name__ == "__main__":
    main()
