import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import plotly.express as px

st.set_page_config(page_title="Dashboard Kepatuhan Pajak", layout="wide")
st.title("📊 Dashboard Kepatuhan Pajak Daerah")
st.markdown("Upload file Excel, pilih sheet, filter data, dan visualisasi kepatuhan pajak.")

uploaded_file = st.file_uploader("📁 Upload File Excel", type=["xlsx"])
tahun_pajak = st.number_input("📅 Pilih Tahun Pajak", min_value=2000, max_value=2100, value=2024)

def hitung_kepatuhan(df, tahun_pajak):
    df['TMT'] = pd.to_datetime(df['TMT'], errors='coerce')
    payment_cols = [col for col in df.columns if isinstance(col, datetime)]

    total_pembayaran = df[payment_cols].sum(axis=1)

    def hitung_bulan_aktif(tmt):
        if pd.isna(tmt): return 0
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
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    selected_sheet = st.selectbox("📄 Pilih Nama Sheet", sheet_names)
    df_input = pd.read_excel(xls, sheet_name=selected_sheet)
    df_output = hitung_kepatuhan(df_input.copy(), tahun_pajak)

    # Filter interaktif
    with st.sidebar:
        st.header("🔍 Filter Data")
        if "Nm Unit" in df_output.columns:
            selected_unit = st.selectbox("🏢 Pilih UPPPD", ["Semua"] + sorted(df_output["Nm Unit"].dropna().unique().tolist()))
            if selected_unit != "Semua":
                df_output = df_output[df_output["Nm Unit"] == selected_unit]

        if "KLASIFIKASI" in df_output.columns:
            selected_klasifikasi = st.selectbox("📂 Pilih Klasifikasi Pajak", ["Semua"] + sorted(df_output["KLASIFIKASI"].dropna().unique().tolist()))
            if selected_klasifikasi != "Semua":
                df_output = df_output[df_output["KLASIFIKASI"] == selected_klasifikasi]

    st.success("✅ Data berhasil diproses dan difilter!")
    st.dataframe(df_output.head(30), use_container_width=True)

    output = BytesIO()
    df_output.to_excel(output, index=False)
    st.download_button("⬇️ Download Hasil Excel", data=output.getvalue(), file_name="hasil_dashboard.xlsx")

    # Visualisasi Pie Chart
    st.subheader("📊 Visualisasi Kepatuhan Wajib Pajak")
    klasifikasi_count = df_output["Klasifikasi Kepatuhan"].value_counts().reset_index()
    klasifikasi_count.columns = ["Klasifikasi", "Jumlah"]
    fig = px.pie(klasifikasi_count, names="Klasifikasi", values="Jumlah", title="Distribusi Kepatuhan WP")
    st.plotly_chart(fig, use_container_width=True)

    # Visualisasi Line Chart Jumlah Pembayaran per WP
    st.subheader("📈 Tren Total Pembayaran per WP")
    if "Total Pembayaran" in df_output.columns and "Nama Op" in df_output.columns:
        chart_data = df_output[["Nama Op", "Total Pembayaran"]].sort_values("Total Pembayaran", ascending=False).head(20)
        fig_line = px.bar(chart_data, x="Nama Op", y="Total Pembayaran", title="Top 20 WP berdasarkan Total Pembayaran")
        st.plotly_chart(fig_line, use_container_width=True)