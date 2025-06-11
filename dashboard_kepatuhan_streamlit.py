
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Dashboard Kepatuhan Pajak", layout="wide")

st.title("📊 Dashboard Kepatuhan Pajak Daerah")
st.markdown("Upload file Excel format PEMECAHAN, pilih tahun pajak, lalu klik Proses.")

uploaded_file = st.file_uploader("📁 Upload File Excel", type=["xlsx"])
tahun_pajak = st.number_input("📅 Pilih Tahun Pajak", min_value=2000, max_value=2100, value=2024)

def hitung_kepatuhan(df, tahun_pajak):
    df['TMT'] = pd.to_datetime(df['TMT'])
    payment_cols = [col for col in df.columns if isinstance(col, datetime)]

    total_pembayaran = df[payment_cols].sum(axis=1)

    def hitung_bulan_aktif(tmt):
        if tmt.year < tahun_pajak:
            return 12
        elif tmt.year > tahun_pajak:
            return 0
        else:
            return 12 - tmt.month + 1

    bulan_aktif = df['TMT'].apply(hitung_bulan_aktif)
    bulan_pembayaran = df[payment_cols].gt(0).sum(axis=1)
    rata_rata_pembayaran = total_pembayaran / bulan_pembayaran.replace(0, 1)
    kepatuhan_persen = bulan_pembayaran / bulan_aktif.replace(0, 1) * 100

    def klasifikasi(bulan):
        if bulan <= 4:
            return "Kurang Patuh"
        elif bulan <= 8:
            return "Cukup Patuh"
        else:
            return "Patuh"

    klasifikasi_kepatuhan = bulan_pembayaran.apply(klasifikasi)

    df["Total Pembayaran"] = total_pembayaran
    df["Bulan Aktif"] = bulan_aktif
    df["Bulan Pembayaran"] = bulan_pembayaran
    df["Rata-rata Pembayaran"] = rata_rata_pembayaran
    df["Kepatuhan (%)"] = kepatuhan_persen
    df["Klasifikasi Kepatuhan"] = klasifikasi_kepatuhan

    return df

if uploaded_file:
    df_input = pd.read_excel(uploaded_file, sheet_name="PEMECAHAN")
    df_output = hitung_kepatuhan(df_input.copy(), tahun_pajak)

    st.success("✅ Data berhasil diproses!")
    st.dataframe(df_output.head(30), use_container_width=True)

    output = BytesIO()
    df_output.to_excel(output, index=False)
    st.download_button("⬇️ Download Hasil Excel", data=output.getvalue(), file_name="hasil_dashboard.xlsx")

    # Visualisasi Ringkas
    st.subheader("📈 Ringkasan Kepatuhan Wajib Pajak")
    klasifikasi_count = df_output["Klasifikasi Kepatuhan"].value_counts()
    st.bar_chart(klasifikasi_count)

