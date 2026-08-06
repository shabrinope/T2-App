import pandas as pd
import numpy as np


def analisis_hotelling(df):
    """
    Melakukan cleaning data dan menghitung nilai Hotelling T².

    Parameters
    ----------
    df : pandas.DataFrame
        Data hasil upload dari Streamlit.

    Returns
    -------
    pandas.DataFrame
        Data yang telah ditambahkan kolom T² dan Status.
    """
    hasil = df.copy()

    hasil["flow Distribusi"] = (
        hasil["flow Distribusi"]
        .astype(str)
        .str.replace(r"[^0-9.-]", "", regex=True)
    )

    hasil["pressure Distribusi"] = (
        hasil["pressure Distribusi"]
        .astype(str)
        .str.replace(r"[^0-9.-]", "", regex=True)
    )

    hasil["flow Distribusi"] = pd.to_numeric(
        hasil["flow Distribusi"],
        errors="coerce"
    )

    hasil["pressure Distribusi"] = pd.to_numeric(
        hasil["pressure Distribusi"],
        errors="coerce"
    )
    hasil = hasil.dropna(
        subset=["flow Distribusi", "pressure Distribusi"]
    ).reset_index(drop=True)

    mu = np.array([
        3.917612,
        1.370727
    ])
    # Inverse Covariance Matrix
    Sinv = np.array([
        [55.31965, 26.51486],
        [26.51486, 30.63063]
    ])
    # Upper Control Limit
    UCL = 4.42802

    hasil["Hour"] = hasil["Time"].dt.strftime("%H:%M")
    x = hasil[
        [
            "flow Distribusi",
            "pressure Distribusi"
        ]
    ]
    T2 = []
    for _, row in x.iterrows():

        d = row.values - mu

        t2 = d.T @ Sinv @ d

        T2.append(t2)
    hasil["T2"] = T2

    hasil["Status"] = np.where(
        hasil["T2"] > UCL,
        "OOC",
        "IC"
    )
    ooc = hasil.loc[
        hasil["Status"] == "OOC",
        [
            "Hour",
            "flow Distribusi",
            "pressure Distribusi",
            "T2"
        ]
    ]
    flow_mean = hasil["flow Distribusi"].mean()
    flow_min = hasil["flow Distribusi"].min()
    flow_max = hasil["flow Distribusi"].max()

    pressure_mean = hasil["pressure Distribusi"].mean()
    pressure_min = hasil["pressure Distribusi"].min()
    pressure_max = hasil["pressure Distribusi"].max()

    return {
    "hasil": hasil,
    "ooc": ooc,
    "ucl": UCL,
    "jumlah_ooc": len(ooc),
    "jumlah_ic": (hasil["Status"] == "IC").sum(),

    "flow_mean": flow_mean,
    "flow_min": flow_min,
    "flow_max": flow_max,

    "pressure_mean": pressure_mean,
    "pressure_min": pressure_min,
    "pressure_max": pressure_max
    }