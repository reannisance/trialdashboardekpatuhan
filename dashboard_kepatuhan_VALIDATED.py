import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import plotly.express as px

st.set_page_config(page_title="🎨 Dashboard Kepatuhan Pajak Daerah", layout="wide")
st.title("🎯 Dashboard Kepatuhan Pajak Daerah")
st.markdown("Upload file Excel, pilih sheet, filter, dan lihat visualisasi yang menarik ✨")

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

    def klasifikasi(kepatuhan):
        if kepatuhan <= 33.333:
            return "Kurang Patuh"
        elif kepatuhan <= 66.666:
            return "Cukup Patuh"
        else:
            return "Patuh"

    klasifikasi_kepatuhan = kepatuhan_persen.apply(klasifikasi)

    df["Total Pembayaran"] = total_pembayaran
    df["Bulan Aktif"] = bulan_aktif
    df["Bulan Pembayaran"] = bulan_pembayaran
    df["Rata-rata Pembayaran"] = rata_rata_pembayaran
    df["Kepatuhan (%)"] = kepatuhan_persen
    df["Klasifikasi Kepatuhan"] = klasifikasi_kepatuhan

    return df, payment_cols

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    selected_sheet = st.selectbox("📄 Pilih Nama Sheet", sheet_names)
    df_input = pd.read_excel(xls, sheet_name=selected_sheet)

    # Validasi kolom penting
    required_cols = ["TMT"]
    missing_cols = [col for col in required_cols if col not in df_input.columns]

    if missing_cols:
        st.error(f"❌ Kolom wajib hilang: {', '.join(missing_cols)}. Harap periksa file Anda.")
    else:
        df_output, payment_cols = hitung_kepatuhan(df_input.copy(), tahun_pajak)

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

        # Pie Chart
        st.subheader("🧁 Pie Chart Kepatuhan WP (Warna Lucu)")
        pie_data = df_output["Klasifikasi Kepatuhan"].value_counts().reset_index()
        pie_data.columns = ["Klasifikasi", "Jumlah"]
        fig_pie = px.pie(
            pie_data,
            names="Klasifikasi",
            values="Jumlah",
            title="Distribusi Kepatuhan WP",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        # Line Chart
        st.subheader("📈 Tren Pembayaran Pajak per Bulan")
        if payment_cols:
            bulanan = df_output[payment_cols].sum().reset_index()
            bulanan.columns = ["Bulan", "Total Pembayaran"]
            bulanan["Bulan"] = pd.to_datetime(bulanan["Bulan"])
            bulanan = bulanan.sort_values("Bulan")

            fig_line = px.line(
                bulanan,
                x="Bulan",
                y="Total Pembayaran",
                title="Total Pembayaran Pajak per Bulan",
                markers=True,
                line_shape="spline",
                color_discrete_sequence=["#FFB6C1"]
            )
            st.plotly_chart(fig_line, use_container_width=True)

        # Top 20 WP Chart
        st.subheader("🏅 Top 20 Wajib Pajak Berdasarkan Total Pembayaran")
        if "Total Pembayaran" in df_output.columns and "Nama Op" in df_output.columns:
            top_wp = df_output[["Nama Op", "Total Pembayaran"]].groupby("Nama Op").sum().reset_index()
            top_wp = top_wp.sort_values("Total Pembayaran", ascending=False).head(20)
            fig_bar = px.bar(
                top_wp,
                x="Nama Op",
                y="Total Pembayaran",
                title="Top 20 WP Berdasarkan Total Pembayaran",
                color_discrete_sequence=["#A0CED9"]
            )
            st.plotly_chart(fig_bar, use_container_width=True)