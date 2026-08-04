import streamlit as st
import os
import pandas as pd
import matplotlib.pyplot as plt
import importlib
import pdf_report
importlib.reload(pdf_report)
from pdf_report import buat_pdf


st.set_page_config(
    page_title="Aplikasi Monitoring Flow & Pressure",
    page_icon="c:\\Users\\shyne\\OneDrive\\Documents\\ular\\T2 App\\icon.png.png",
    layout="wide"
)

_ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png.png")

_col_icon, _col_title = st.columns([1, 9])
with _col_icon:
    with open(_ICON_PATH, "rb") as _f:
        st.image(_f.read(), width=120)
with _col_title:
    st.markdown("## Dashboard Monitoring Flow & Pressure")

st.write(
    """
    Aplikasi ini digunakan untuk melakukan monitoring
    Flow dan Pressure menggunakan peta kendali Hotelling T².
    """
)
st.sidebar.header("Menu")

uploaded_file = st.sidebar.file_uploader(
    "Upload File CSV",
    type=["csv"]
)

if uploaded_file is None:
    st.info("Silakan upload file CSV terlebih dahulu.")

else:
    df = pd.read_csv(uploaded_file)

    st.success("✅ File berhasil diupload!")

    # Jumlah observasi
    n = len(df)

    st.subheader("Informasi Data")
    df["Time"] = pd.to_datetime(df["Time"])
    
    tanggal_unik = df["Time"].dt.date.unique()
    
    if len(tanggal_unik) == 1:
        tanggal = tanggal_unik[0].strftime("%d %B %Y")
        st.metric("📅 Tanggal Analisis", tanggal)
    else:
        st.error("❌ File mengandung lebih dari satu tanggal. Silakan upload data untuk satu hari saja.")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Jumlah Observasi", n)

    with col2:
        st.metric("Jumlah Kolom", len(df.columns))

    with col3:
        st.metric("Batas Kendali (UCL)", "9.1951")
    # Validasi jumlah observasi
    if n < 24:

        st.warning(
        f"Data hanya memiliki {n} observasi. "
        "Analisis tetap dijalankan."
        )
    
    elif n > 24:

        st.warning(
        f"Data memiliki {n} observasi. "
        "Memeriksa kemungkinan data duplikat..."
        )

        # hapus duplikasi Time
        before = len(df)

        df = df.drop_duplicates(subset="Time")

        after = len(df)

        if before != after:

            st.success(
            f"Ditemukan {before-after} data duplikat dan berhasil dihapus."
         )

        else:

            st.info("Tidak ditemukan data duplikat.")

         # cek lagi
        if len(df) > 24:

            st.error(
            "Jumlah observasi masih lebih dari 24. "
            "Silakan periksa kembali file yang diunggah."
         )

            st.stop()
        else:
            st.warning(
            f"⚠️ Data memiliki {n} observasi. "
            "Pastikan file yang diunggah hanya berisi data selama 1 hari (24 observasi)."
         )
    else:

        st.success("Data lengkap (24 observasi).")

    st.subheader("Preview Data")
    st.dataframe(df)

    required_columns = ["Time", "flow Distribusi", "pressure Distribusi"]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        st.error(
            f"Kolom berikut tidak ditemukan: {', '.join(missing_columns)}"
        )

        st.stop()

    else:

        st.success("✅ Format kolom sesuai.")

    missing = df[["flow Distribusi", "pressure Distribusi"]].isna().sum()

    if missing.sum() == 0:

        st.success("✅ Tidak terdapat missing value.")

    else:

        st.warning(
            f"""
            Missing Value ditemukan!

            • Flow : {missing['flow Distribusi']}
            • Pressure : {missing['pressure Distribusi']}
            """
        )

        if st.button("🗑 Hapus Missing Value"):

            df = df.dropna(subset=["flow Distribusi", "pressure Distribusi"])

            st.success("Missing value berhasil dihapus.")

            st.write(f"Jumlah observasi sekarang: {len(df)}")

    from hotelling import analisis_hotelling
    output = analisis_hotelling(df)
    st.subheader("Peta Kendali")

    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(
        output["hasil"]["Hour"],
        output["hasil"]["T2"],
        marker="o",
        linewidth=1.5,
        zorder=1
    )
    ax.axhline(
        y=output["ucl"],
        color="red",
        linestyle="--",
        linewidth=2,
        label="UCL"
    )
    ic = output["hasil"]["Status"] == "IC"
    ooc = output["hasil"]["Status"] == "OOC"

    ax.scatter(
        output["hasil"].loc[ic, "Hour"],
        output["hasil"].loc[ic, "T2"],
        color="green",
        s=50,
        label="In Control"
    )

    ax.scatter(
        output["hasil"].loc[ooc, "Hour"],
        output["hasil"].loc[ooc, "T2"],
        color="red",
        s=70,
        label="Out of Control"
    )

    ax.set_title("Hotelling T² Control Chart")

    ax.set_xlabel("Jam")

    ax.set_ylabel("Hotelling T²")

    ax.legend()

    ax.grid(
        linestyle="--",
        alpha=0.5
    )

    plt.xticks(rotation=45)

    plt.tight_layout()

    st.pyplot(fig)
    st.write("Jika ditemukan titik berwarna merah, maka observasi tersebut perlu diperiksa lebih lanjut karena berada diluar kendali.")

    st.subheader("Ringkasan Hasil Monitoring")

    n_ic_val   = output["jumlah_ic"]
    n_ooc_val  = output["jumlah_ooc"]
    n_tot_val  = len(output["hasil"])
    persen_ooc = n_ooc_val / n_tot_val * 100
    persen_ic  = 100 - persen_ooc

    col_pie, col_info = st.columns([2, 1])

    with col_pie:
        fig_pie, ax_pie = plt.subplots(figsize=(2.5, 2.5))
        wedges, texts, autotexts = ax_pie.pie(
            [n_ic_val, n_ooc_val],
            labels=["Terkendali", "Tidak Terkendali"],
            colors=["#27ae60", "#e74c3c"],
            explode=(0, 0.06),
            autopct="%1.1f%%",
            startangle=90,
            textprops={"fontsize": 9},
        )
        for at in autotexts:
            at.set_fontweight("bold")
            at.set_color("white")
        ax_pie.set_title("Proporsi Hasil Monitoring", fontsize=10, fontweight="bold", pad=10)
        plt.tight_layout()
        st.pyplot(fig_pie, use_container_width=False)
        plt.close(fig_pie)

    with col_info:
        st.markdown(
            f"""
            <div style="display:flex;flex-direction:column;gap:12px;padding-top:30px">
                <div style="background:#eafaf1;border-left:5px solid #27ae60;
                            border-radius:6px;padding:14px 18px">
                    <div style="color:#27ae60;font-weight:700;font-size:13px">🟢 Terkendali</div>
                    <div style="font-size:28px;font-weight:800;color:#1a1a1a">{n_ic_val}</div>
                    <div style="color:#888;font-size:12px">{persen_ic:.1f}% dari total observasi</div>
                </div>
                <div style="background:#fdf2f2;border-left:5px solid #e74c3c;
                            border-radius:6px;padding:14px 18px">
                    <div style="color:#e74c3c;font-weight:700;font-size:13px">🔴 Tidak Terkendali</div>
                    <div style="font-size:28px;font-weight:800;color:#1a1a1a">{n_ooc_val}</div>
                    <div style="color:#888;font-size:12px">{persen_ooc:.1f}% dari total observasi</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.subheader("Observasi Out of Control")

    if output["jumlah_ooc"] == 0:
        st.success("✅ Tidak terdapat observasi Out of Control.")

    else:
        ooc_display = output["ooc"].rename(columns={
            "flow Distribusi":     "Flow Distribusi (l/s)",
            "pressure Distribusi": "Pressure Distribusi (Bar)",
        })
        st.dataframe(ooc_display)
        st.write("Semakin jauh nilai T² dari 9.1951, semakin besar penyimpangan yang terjadi pada observasi tersebut.")
        st.warning(
            f"⚠️ Ada sebanyak {output['jumlah_ooc']} dari {len(output['hasil'])} observasi ({persen_ooc:.2f}%) berada di luar kendali yang perlu diperiksa lebih lanjut."
        )

    # ── PDF Report Download ───────────────────────────────────────────────────
    st.divider()
    st.subheader("📄 Unduh Laporan")
    st.write("Klik tombol di bawah untuk mengunduh ringkasan hasil analisis dalam format PDF.")

    pdf_bytes = buat_pdf(
        tanggal=tanggal,
        n_obs=len(df),
        output=output,
    )

    st.download_button(
        label="⬇️ Download Laporan PDF",
        data=pdf_bytes,
        file_name=f"Laporan_HotellingT2_{tanggal.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )