import streamlit as st
import json
import os
import time
import pandas as pd
import sqlite3
import random
import string
from datetime import datetime

# Konfigurasi Halaman (Lebar Penuh)
st.set_page_config(page_title="LulusCAT - Platform Persiapan Seleksi ASN", layout="wide")

# CSS Styling Modern & Elegan ala LulusCAT
st.markdown("""
    <style>
    .brand-title {font-size: 32px; font-weight: bold; color: #1f4e78; text-decoration: none;}
    .main-header {background-color: #1f4e78; color: white; padding: 12px; border-radius: 5px; font-weight: bold; text-align: center; font-size: 18px;}
    .card-soal {background-color: #f9f9f9; padding: 20px; border-radius: 5px; border: 1px solid #ddd;}
    .timer-badge {background-color: #262626; color: #00ff00; padding: 8px 15px; border-radius: 5px; font-weight: bold; text-align: center; font-size: 20px;}
    .free-badge {background-color: #2e7d32; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;}
    .premium-badge {background-color: #d81b60; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;}
    .exam-card {background-color: white; padding: 30px; border-radius: 10px; border: 1px solid #ddd; max-width: 700px; margin: 0 auto; box-shadow: 0px 4px 10px rgba(0,0,0,0.05);}
    .exam-header {background-color: #1f4e78; color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -30px -30px 20px -30px;}
    .pembahasan-box {background-color: #eef2f7; padding: 12px; border-radius: 5px; border-left: 4px solid #1f4e78; margin-top: 10px;}
    
    .package-card {
        background-color: white; 
        border: 1px solid #e0e0e0; 
        border-radius: 12px; 
        padding: 22px; 
        text-align: center; 
        box-shadow: 0 3px 8px rgba(0,0,0,0.04); 
        margin-bottom: 20px;
    }
    .package-card h4 {
        font-size: 18px !important;
        color: #1f4e78;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .package-card p {
        font-size: 13px !important;
        color: #555555;
        line-height: 1.4;
    }

    .product-card {
        background-color: white; 
        border: 1px solid #e0e0e0; 
        border-radius: 12px; 
        padding: 18px; 
        text-align: left; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.03); 
        margin-bottom: 20px; 
        height: 100%;
    }
    
    .hero-section {
        background: linear-gradient(135deg, #1f4e78 0%, #2c689f 100%);
        color: white;
        padding: 55px;
        border-radius: 16px;
        margin-bottom: 30px;
        box-shadow: 0px 6px 15px rgba(31, 78, 120, 0.2);
    }
    .hero-section h1 {
        font-size: 42px !important;
        font-weight: 800;
        color: white;
        line-height: 1.2;
    }
    .hero-section p {
        font-size: 17px !important;
        color: #f0f4f8;
        line-height: 1.6;
    }
    
    div.stButton > button {
        background-color: #1f4e78;
        color: white;
        border: none;
        font-weight: 600;
        font-size: 14px;
        padding: 6px 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-radius: 6px;
    }
    div.stButton > button:hover {
        background-color: #2c689f;
        color: white;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI DATABASE SQLITE LOKAL ---
DB_NAME = "luluscat_system.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            email TEXT,
            no_wa TEXT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'FREE',
            free_token TEXT,
            active_token TEXT DEFAULT '-',
            device_id TEXT DEFAULT '-'
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN no_wa TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'UNUSED',
            used_by TEXT DEFAULT '-',
            device_id TEXT DEFAULT '-'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS digital_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT NOT NULL,
            kategori TEXT,
            harga TEXT,
            harga_coret TEXT,
            deskripsi TEXT,
            format_file TEXT DEFAULT 'PDF Digital',
            link_lynk TEXT,
            gambar_url TEXT
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE digital_products ADD COLUMN harga_coret TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE digital_products ADD COLUMN link_lynk TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE digital_products ADD COLUMN gambar_url TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            nama TEXT,
            no_wa TEXT,
            paket TEXT,
            skor_twk INTEGER,
            skor_tiu INTEGER,
            skor_tkp INTEGER,
            total_skor INTEGER,
            waktu TEXT
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM digital_products")
    if cursor.fetchone()[0] == 0:
        default_prods = [
            ("Taklukkan TWK SKD CPNS & Sekolah Kedinasan 2026", "E-Book TWK", "Rp 39.000", "Rp 150.000", "Ringkasan Materi + 300 Soal Latihan & Pembahasan.", "PDF E-Book", "https://lynk.id/asnacademy/vw3rypxjwrlq", "https://i.imgur.com/example.jpg")
        ]
        cursor.executemany("INSERT INTO digital_products (judul, kategori, harga, harga_coret, deskripsi, format_file, link_lynk, gambar_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", default_prods)

    cursor.execute("SELECT COUNT(*) FROM tokens")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR IGNORE INTO tokens (token, status) VALUES ('LULUSCAT-2026-DEMO', 'UNUSED')")
    
    conn.commit()
    conn.close()

init_db()

def load_questions():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "soal.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return []

# --- FUNGSI PEMUAT MATERI JSON SKD ---
def load_materi(modul_nama):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filename = f"materi_skd_{modul_nama.lower()}.json"
    file_path = os.path.join(base_dir, filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return None

if 'soal_list' not in st.session_state:
    st.session_state.soal_list = load_questions()

if 'user_session' not in st.session_state:
    st.session_state.user_session = None

if 'jawaban' not in st.session_state:
    st.session_state.jawaban = {}

if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

if 'ujian_selesai' not in st.session_state:
    st.session_state.ujian_selesai = False

if 'start_time' not in st.session_state:
    st.session_state.start_time = None

if 'page_mode' not in st.session_state:
    st.session_state.page_mode = "HOME"

if 'selected_paket' not in st.session_state:
    st.session_state.selected_paket = "TryOut Gratis 55 Soal"

if 'device_id' not in st.session_state:
    st.session_state.device_id = f"dev_{int(time.time())}_{os.urandom(3).hex()}"

if 'last_registered_token' not in st.session_state:
    st.session_state.last_registered_token = None

if 'bimbel_modul' not in st.session_state:
    st.session_state.bimbel_modul = None

if 'bimbel_state' not in st.session_state:
    st.session_state.bimbel_state = "HOME"

if 'edit_product_id' not in st.session_state:
    st.session_state.edit_product_id = None

# --- STRUKTUR NAVBAR ATAS (LOGIN & DAFTAR DI KANAN) ---
_, col_login, col_daftar = st.columns([7.2, 1.4, 1.4])

with col_login:
    if st.session_state.user_session is None:
        if st.button("🔑 Login", use_container_width=True):
            st.session_state.page_mode = "LOGIN"
            st.rerun()
    else:
        if st.button(f"👤 {st.session_state.user_session['username']}", use_container_width=True):
            if st.session_state.user_session['role'] == 'ADMIN':
                st.session_state.page_mode = "ADMIN_DASHBOARD"
            else:
                st.session_state.page_mode = "PROFIL"
            st.rerun()

with col_daftar:
    if st.session_state.user_session is None:
        if st.button("✨ Daftar Akun", use_container_width=True, type="primary"):
            st.session_state.page_mode = "REGISTRASI"
            st.rerun()
    else:
        if st.button("🚪 Keluar", use_container_width=True):
            st.session_state.user_session = None
            st.session_state.page_mode = "HOME"
            st.success("Berhasil keluar akun.")
            st.rerun()

st.write("") 

# =========================================================================
# HALAMAN LOGIN MEMBER
# =========================================================================
if st.session_state.page_mode == "LOGIN":
    st.markdown("## 🔑 Masuk ke Akun LulusCAT")
    st.write("Masukkan username dan password Anda untuk masuk ke sistem.")
    st.write("")

    with st.form("form_login_member"):
        l_user = st.text_input("Username")
        l_pass = st.text_input("Password", type="password")
        btn_l = st.form_submit_button("Masuk Sekarang", type="primary")

        if btn_l:
            clean_u = l_user.strip()
            clean_p = l_pass.strip()
            if not clean_u or not clean_p:
                st.error("Username dan password wajib diisi!")
            else:
                if clean_u == "admin" and clean_p == "bkn2026":
                    st.session_state.user_session = {
                        "id": 0,
                        "nama": "Administrator Utama",
                        "email": "admin@luluscat.com",
                        "no_wa": "-",
                        "username": "admin",
                        "role": "ADMIN",
                        "free_token": "-",
                        "active_token": "-",
                        "device_id": st.session_state.device_id
                    }
                    st.success("Login Admin Berhasil!")
                    time.sleep(1)
                    st.session_state.page_mode = "ADMIN_DASHBOARD"
                    st.rerun()
                else:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, nama, email, no_wa, username, role, free_token, active_token, device_id FROM users WHERE username = ? AND password = ?", (clean_u, clean_p))
                    user_row = cursor.fetchone()
                    conn.close()

                    if user_row:
                        st.session_state.user_session = {
                            "id": user_row[0],
                            "nama": user_row[1],
                            "email": user_row[2],
                            "no_wa": user_row[3],
                            "username": user_row[4],
                            "role": user_row[5],
                            "free_token": user_row[6],
                            "active_token": user_row[7],
                            "device_id": user_row[8]
                        }
                        st.success(f"Selamat datang kembali, {user_row[1]}!")
                        time.sleep(1)
                        st.session_state.page_mode = "HOME"
                        st.rerun()
                    else:
                        st.error("Username atau Password salah!")

    st.write("")
    if st.button("⬅️ Kembali ke Beranda"):
        st.session_state.page_mode = "HOME"
        st.rerun()

# =========================================================================
# DASHBOARD ADMINISTRATOR
# =========================================================================
elif st.session_state.page_mode == "ADMIN_DASHBOARD":
    if st.session_state.user_session is None or st.session_state.user_session['role'] != 'ADMIN':
        st.warning("Akses ditolak. Silakan login sebagai admin.")
        if st.button("Ke Halaman Login"):
            st.session_state.page_mode = "LOGIN"
            st.rerun()
    else:
        st.markdown("## 🛠️ Dashboard Administrator LulusCAT")
        st.write("Kelola rekap analitik nilai, token lisensi premium, serta data kontak WhatsApp member untuk analisis pasar.")
        st.write("")

        tab_admin_produk, tab_admin_nilai, tab_admin_token, tab_admin_user = st.tabs(["📦 Kelola Buku & Harga", "📊 Rekap Nilai & Analisis Pasar", "🔑 Manajemen Token", "👥 Data Member & WA"])
        
        with tab_admin_produk:
            if st.session_state.edit_product_id is not None:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("SELECT judul, kategori, harga, harga_coret, format_file, link_lynk, gambar_url, deskripsi FROM digital_products WHERE id = ?", (st.session_state.edit_product_id,))
                prod_data = cursor.fetchone()
                conn.close()

                if prod_data:
                    st.markdown(f"### ✏️ Edit Produk: {prod_data[0]}")
                    with st.form("form_edit_digital"):
                        e_judul = st.text_input("Judul Buku", value=prod_data[0])
                        e_kat = st.selectbox("Kategori", ["E-Book SKD", "E-Book TWK", "E-Book TIU", "E-Book TKP", "Modul SKB JF", "Bundling"], index=["E-Book SKD", "E-Book TWK", "E-Book TIU", "E-Book TKP", "Modul SKB JF", "Bundling"].index(prod_data[1]) if prod_data[1] in ["E-Book SKD", "E-Book TWK", "E-Book TIU", "E-Book TKP", "Modul SKB JF", "Bundling"] else 0)
                        e_harga = st.text_input("Harga Diskon / Jual", value=prod_data[2] if prod_data[2] else "")
                        e_harga_coret = st.text_input("Harga Normal / Coret", value=prod_data[3] if prod_data[3] else "")
                        e_format = st.selectbox("Format", ["PDF Digital", "Akses Web", "Paket Lengkap"], index=["PDF Digital", "Akses Web", "Paket Lengkap"].index(prod_data[4]) if prod_data[4] in ["PDF Digital", "Akses Web", "Paket Lengkap"] else 0)
                        e_lynk = st.text_area("Link Checkout Lynk.id", value=prod_data[5] if prod_data[5] else "")
                        e_img = st.text_input("Link URL Gambar Cover", value=prod_data[6] if prod_data[6] else "")
                        e_desc = st.text_area("Deskripsi Singkat Buku", value=prod_data[7] if prod_data[7] else "")
                        
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            btn_update = st.form_submit_button("💾 Simpan Perubahan", type="primary")
                        with col_e2:
                            btn_batal = st.form_submit_button("❌ Batal")

                        if btn_update:
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE digital_products 
                                SET judul=?, kategori=?, harga=?, harga_coret=?, deskripsi=?, format_file=?, link_lynk=?, gambar_url=? 
                                WHERE id=?
                            """, (e_judul, e_kat, e_harga, e_harga_coret, e_desc, e_format, e_lynk, e_img, st.session_state.edit_product_id))
                            conn.commit()
                            conn.close()
                            st.session_state.edit_product_id = None
                            st.success("Produk berhasil diperbarui!")
                            st.rerun()
                        
                        if btn_batal:
                            st.session_state.edit_product_id = None
                            st.rerun()
                else:
                    st.session_state.edit_product_id = None
                    st.rerun()
            else:
                st.markdown("### 📥 Tambah Buku / E-Book Baru")
                with st.form("form_tambah_digital"):
                    d_judul = st.text_input("Judul Buku")
                    d_kat = st.selectbox("Kategori", ["E-Book SKD", "E-Book TWK", "E-Book TIU", "E-Book TKP", "Modul SKB JF", "Bundling"])
                    d_harga = st.text_input("Harga Diskon / Jual (Contoh: Rp 39.000)")
                    d_harga_coret = st.text_input("Harga Normal / Coret (Contoh: Rp 150.000 - Kosongkan jika tidak ada)")
                    d_format = st.selectbox("Format", ["PDF Digital", "Akses Web", "Paket Lengkap"])
                    d_lynk = st.text_area("Link Checkout Lynk.id (Tempel link lengkap Lynk.id produk ini)")
                    d_img = st.text_input("Link URL Gambar Cover (Contoh: https://i.imgur.com/contoh.jpg)")
                    d_desc = st.text_area("Deskripsi Singkat Buku")
                    btn_simpan_prod = st.form_submit_button("💾 Simpan Buku", type="primary")

                    if btn_simpan_prod:
                        if d_judul and d_harga:
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO digital_products (judul, kategori, harga, harga_coret, deskripsi, format_file, link_lynk, gambar_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                         (d_judul, d_kat, d_harga, d_harga_coret, d_desc, d_format, d_lynk, d_img))
                            conn.commit()
                            conn.close()
                            st.success("Buku berhasil ditambahkan ke katalog!")
                            st.rerun()
                        else:
                            st.error("Judul dan Harga wajib diisi!")

            st.markdown("---")
            st.markdown("### 📋 Daftar Buku di Katalog")
            conn = sqlite3.connect(DB_NAME)
            df_prod = pd.read_sql("SELECT id, judul, harga, link_lynk FROM digital_products", conn)
            conn.close()
            if not df_prod.empty:
                for idx, row in df_prod.iterrows():
                    col_p1, col_p2, col_p3, col_p4 = st.columns([2.5, 2.5, 1, 1])
                    col_p1.text(f"{row['judul']} ({row['harga']})")
                    col_p2.text(row['link_lynk'] if row['link_lynk'] else "-")
                    
                    with col_p3:
                        if st.button("✏️ Edit", key=f"edit_prod_{row['id']}"):
                            st.session_state.edit_product_id = row['id']
                            st.rerun()
                            
                    with col_p4:
                        if st.button("❌ Hapus", key=f"del_prod_{row['id']}"):
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM digital_products WHERE id = ?", (row['id'],))
                            conn.commit()
                            conn.close()
                            st.success("Buku dihapus!")
                            st.rerun()
            else:
                st.info("Belum ada buku.")

        with tab_admin_nilai:
            st.markdown("### 📊 Analisis Pasar & Rekap Nilai Peserta")
            conn = sqlite3.connect(DB_NAME)
            df_exam = pd.read_sql("SELECT username, nama, no_wa, paket, skor_twk, skor_tiu, skor_tkp, total_skor, waktu FROM exam_history", conn)
            conn.close()

            if df_exam.empty:
                st.info("Belum ada data peserta ujian yang masuk.")
            else:
                total_ujian_dikerjakan = len(df_exam)
                total_peserta_unik = df_exam['username'].nunique()
                rata_rata_skor_nasional = int(df_exam['total_skor'].mean())
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Peserta Ujian", total_peserta_unik)
                m2.metric("Total Sesi Pengerjaan", total_ujian_dikerjakan)
                m3.metric("Rata-Rata Skor Nasional", rata_rata_skor_nasional)
                
                st.markdown("---")
                st.markdown("#### 🔄 Frekuensi Pengerjaan & Performa per Peserta")
                df_analisis_peserta = df_exam.groupby(['username', 'nama', 'no_wa', 'paket']).agg(
                    jumlah_mengerjakan=('total_skor', 'count'),
                    rata_rata_skor=('total_skor', 'mean'),
                    skor_tertinggi=('total_skor', 'max')
                ).reset_index()
                df_analisis_peserta['rata_rata_skor'] = df_analisis_peserta['rata_rata_skor'].astype(int)
                
                st.dataframe(df_analisis_peserta, use_container_width=True)

                st.markdown("---")
                st.markdown("#### 📋 Riwayat Lengkap Seluruh Sesi Ujian")
                st.dataframe(df_exam, use_container_width=True)

                csv_exam = df_exam.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Laporan Analisis Ujian (CSV)", data=csv_exam, file_name="analisis_pasar_luluscat.csv", mime="text/csv")
        
        with tab_admin_token:
            st.markdown("### Generator & Database Token Lisensi Premium")
            with st.form("form_generate_token"):
                st.markdown("#### ⚡ Buat Token Premium Baru")
                jumlah_buat = st.number_input("Jumlah Token yang Ingin Dibuat", min_value=1, max_value=100, value=10)
                prefix_token = st.text_input("Awalan Token (Prefix)", value="LULUSCAT-2026")
                btn_gen = st.form_submit_button("🚀 Generate & Simpan Token")
                
                if btn_gen:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    berhasil_buat = 0
                    for _ in range(jumlah_buat):
                        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                        kode_token = f"{prefix_token}-{suffix}"
                        try:
                            cursor.execute("INSERT INTO tokens (token, status) VALUES (?, 'UNUSED')", (kode_token,))
                            berhasil_buat += 1
                        except sqlite3.IntegrityError:
                            pass
                    conn.commit()
                    conn.close()
                    st.success(f"Berhasil membuat dan menyimpan {berhasil_buat} token baru!")
                    st.rerun()

            st.markdown("---")
            st.markdown("#### 📋 Daftar Token Premium, Status, & Download untuk Lynk.id")
            
            conn = sqlite3.connect(DB_NAME)
            df_tokens = pd.read_sql("SELECT token, status, used_by FROM tokens", conn)
            conn.close()

            if not df_tokens.empty:
                csv_tokens = df_tokens.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Semua Token (CSV untuk Lynk.id)", data=csv_tokens, file_name="daftar_token_luluscat.csv", mime="text/csv")
                st.write("")

                for idx, row in df_tokens.iterrows():
                    col_t1, col_t2, col_t3, col_t4 = st.columns([2, 1, 2, 1])
                    col_t1.text(row['token'])
                    col_t2.text(row['status'])
                    col_t3.text(row['used_by'])
                    
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM tokens WHERE token = ?", (row['token'],))
                    t_id_row = cursor.fetchone()
                    conn.close()
                    
                    if t_id_row:
                        r_id = t_id_row[0]
                        if col_t4.button("❌ Hapus", key=f"del_tok_{r_id}"):
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM tokens WHERE id = ?", (r_id,))
                            conn.commit()
                            conn.close()
                            st.success("Token dihapus!")
                            st.rerun()
            else:
                st.info("Belum ada token premium.")

        with tab_admin_user:
            st.markdown("### Daftar Member Terdaftar, No. WhatsApp & Token")
            conn = sqlite3.connect(DB_NAME)
            df_users = pd.read_sql("SELECT id, nama, email, no_wa, username, role, free_token, active_token FROM users", conn)
            conn.close()
            if not df_users.empty:
                st.dataframe(df_users, use_container_width=True)
                csv_users = df_users.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Data Member & WhatsApp (CSV)", data=csv_users, file_name="data_member_luluscat.csv", mime="text/csv")
            else:
                st.info("Belum ada member terdaftar.")

    st.write("")
    if st.button("⬅️ Kembali ke Beranda"):
        st.session_state.page_mode = "HOME"
        st.rerun()

# =========================================================================
# HALAMAN PENDAFTARAN AKUN BARU
# =========================================================================
elif st.session_state.page_mode == "REGISTRASI":
    st.markdown("## 📝 Pendaftaran Akun Baru LulusCAT")
    st.write("Daftar akun untuk mendapatkan **Token Tryout Gratis** secara instan dan akses penuh ke platform.")
    st.write("")

    with st.form("form_daftar_member"):
        d_nama = st.text_input("Nama Lengkap")
        d_email = st.text_input("Email Aktif")
        d_wa = st.text_input("Nomor WhatsApp (Contoh: 081234567890)")
        d_user = st.text_input("Buat Username")
        d_pass = st.text_input("Buat Password", type="password")
        btn_d = st.form_submit_button("Daftar & Ambil Token Gratis", type="primary")

        if btn_d:
            c_nama = d_nama.strip()
            c_email = d_email.strip()
            c_wa = d_wa.strip()
            c_user = d_user.strip()
            c_pass = d_pass.strip()

            if not c_nama or not c_email or not c_wa or not c_user or not c_pass:
                st.error("Semua kolom (Nama, Email, No. WhatsApp, Username, Password) wajib diisi!")
            elif "@" not in c_email or "." not in c_email:
                st.error("Format email tidak valid.")
            else:
                free_tok_code = f"FREE-{c_user.upper()}-{ ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) }"
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO users (nama, email, no_wa, username, password, role, free_token) 
                        VALUES (?, ?, ?, ?, ?, 'FREE', ?)
                    """, (c_nama, c_email, c_wa, c_user, c_pass, free_tok_code))
                    conn.commit()
                    
                    cursor.execute("SELECT id, nama, email, no_wa, username, role, free_token, active_token, device_id FROM users WHERE username = ?", (c_user,))
                    user_row = cursor.fetchone()
                    conn.close()

                    if user_row:
                        st.session_state.user_session = {
                            "id": user_row[0],
                            "nama": user_row[1],
                            "email": user_row[2],
                            "no_wa": user_row[3],
                            "username": user_row[4],
                            "role": user_row[5],
                            "free_token": user_row[6],
                            "active_token": user_row[7],
                            "device_id": user_row[8]
                        }

                    st.session_state.last_registered_token = free_tok_code
                    st.success("🎉 Pendaftaran Berhasil & Auto-Login Aktif!")
                except sqlite3.IntegrityError:
                    st.error("Username sudah digunakan, silakan gunakan username lain.")

    if st.session_state.get('last_registered_token'):
        st.info("Token Tryout Gratis Anda (simpan atau salin token ini):")
        st.code(st.session_state.last_registered_token, language="text")
        
        if st.button("🚀 Lanjutkan ke Konfirmasi Token Tryout", type="primary"):
            st.session_state.page_mode = "KONFIRMASI_TOKEN_GRATIS"
            st.rerun()

    st.write("")
    if st.button("⬅️ Kembali ke Beranda"):
        st.session_state.page_mode = "HOME"
        st.rerun()

# =========================================================================
# HALAMAN PROFIL & AKTIVASI TOKEN
# =========================================================================
elif st.session_state.page_mode == "PROFIL":
    st.markdown("## 👤 Profil Anggota LulusCAT")
    
    if st.session_state.user_session is None:
        st.warning("Silakan login terlebih dahulu.")
        if st.button("Ke Halaman Login"):
            st.session_state.page_mode = "LOGIN"
            st.rerun()
    else:
        usr = st.session_state.user_session
        st.markdown(f"### Halo, {usr['nama']}")
        st.write(f"**Email:** `{usr['email']}`")
        st.write(f"**No. WhatsApp:** `{usr.get('no_wa', '-')}`")
        st.write(f"**Username:** `{usr['username']}`")
        badge_html = f'<span class="premium-badge">PREMIUM (Akses Penuh)</span>' if usr['role'] == 'PREMIUM' else f'<span class="free-badge">FREE MEMBER</span>'
        st.markdown(f"**Status Akun:** {badge_html}", unsafe_allow_html=True)
        st.markdown(f"**Token Tryout Gratis Anda:** `{usr['free_token']}` *(Gunakan token ini untuk masuk ke menu tryout gratis)*")
        st.write(f"**Token Premium Aktif:** `{usr['active_token']}`")

        st.markdown("---")
        st.markdown("### 💎 Masukkan Token Lisensi (Gratis / Premium)")
        st.write("Masukkan token gratis Anda untuk mulai tryout gratis, atau token premium untuk membuka seluruh paket soal.")

        with st.form("form_aktivasi_token"):
            input_token_user = st.text_input("Kode Token Lisensi", type="password")
            btn_aktif = st.form_submit_button("Verifikasi & Aktifkan Token", type="primary", use_container_width=True)

            if btn_aktif:
                clean_tok = input_token_user.strip().upper()
                if not clean_tok:
                    st.error("Token tidak boleh kosong!")
                else:
                    if clean_tok == usr['free_token'].upper():
                        st.success("✅ Token Gratis terverifikasi! Anda sekarang dapat mengerjakan Tryout Gratis.")
                        time.sleep(1)
                        st.session_state.page_mode = "LIST_PAKET_SKD"
                        st.rerun()
                    else:
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("SELECT status, used_by, device_id FROM tokens WHERE token = ?", (clean_tok,))
                        t_row = cursor.fetchone()

                        if t_row:
                            t_status, t_by, t_dev = t_row
                            if t_status == 'UNUSED':
                                cursor.execute("UPDATE tokens SET status = 'USED', used_by = ?, device_id = ? WHERE token = ?", (usr['username'], st.session_state.device_id, clean_tok))
                                cursor.execute("UPDATE users SET role = 'PREMIUM', active_token = ?, device_id = ? WHERE username = ?", (clean_tok, st.session_state.device_id, usr['username']))
                                conn.commit()
                                conn.close()

                                st.session_state.user_session['role'] = 'PREMIUM'
                                st.session_state.user_session['active_token'] = clean_tok
                                st.session_state.user_session['device_id'] = st.session_state.device_id

                                st.success("🎉 Berhasil! Akun Anda kini telah berstatus PREMIUM. Membuka daftar paket...")
                                time.sleep(1.2)
                                st.session_state.page_mode = "LIST_PAKET_SKD"
                                st.rerun()
                            elif t_status == 'USED' and t_by == usr['username']:
                                conn.close()
                                st.info("Token ini sudah aktif di akun Anda. Membuka daftar paket...")
                                time.sleep(1)
                                st.session_state.page_mode = "LIST_PAKET_SKD"
                                st.rerun()
                            else:
                                conn.close()
                                st.error("❌ Token ini sudah digunakan oleh akun atau perangkat lain!")
                        else:
                            conn.close()
                            st.error("❌ Token lisensi tidak valid atau tidak ditemukan!")

        st.write("")
        st.link_button("🛒 Belum punya token? Beli Token Premium di Sini", "https://lynk.id/luluscat", use_container_width=False)

    st.write("")
    if st.button("⬅️ Kembali ke Beranda"):
        st.session_state.page_mode = "HOME"
        st.rerun()

# =========================================================================
# HALAMAN PILIHAN FORMASI TRYOUT SKB CAT
# =========================================================================
elif st.session_state.page_mode == "LIST_SKB_FOROMASI":
    st.markdown("## 🎯 Pilih Formasi Tryout SKB Jabatan Fungsional")
    st.write("Pilih formasi jabatan spesifik untuk memulai simulasi kompetensi bidang sesuai bidang keahlian Anda.")
    st.write("")

    skb_formasi_list = [
        {"judul": "SKB Widyaiswara Ahli Pertama / Muda", "desc": "Fokus materi: Andragogi, Kurikulum Diklat, dan Analisis Kebutuhan Diklat."},
        {"judul": "SKB Analis Kebijakan", "desc": "Fokus materi: Perumusan, Implementasi, dan Evaluasi Kebijakan Publik."},
        {"judul": "SKB Analis SDM Aparatur", "desc": "Fokus materi: Manajemen ASN, Rekrutmen, Penilaian Kinerja, & Pengembangan Karier."},
        {"judul": "SKB Perencana Ahli Pertama / Muda", "desc": "Fokus materi: Perencanaan Pembangunan Nasional, RPJMN, dan APBN/APBD."},
        {"judul": "SKB Pranata Komputer / IT", "desc": "Fokus materi: Tata Kelola TI, Jaringan, Database, dan Sistem Pemerintahan Berbasis Elektronik (SPBE)."},
        {"judul": "SKB Penyuluh Kesehatan / Pertanian", "desc": "Fokus materi: Teknik Penyuluhan Lapangan, Kebijakan Sektoral, & Pemberdayaan Masyarakat."}
    ]

    skb_cols = st.columns(2)
    for i, formasi in enumerate(skb_formasi_list):
        with skb_cols[i % 2]:
            st.markdown(f"""
                <div class="package-card" style="text-align: left; border-top: 5px solid #d81b60;">
                    <h4 style="color: #d81b60; font-size: 20px;">{formasi['judul']}</h4>
                    <p style="color: #555; font-size: 14px;">{formasi['desc']}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Mulai {formasi['judul']}", key=f"btn_skb_f_{i}", use_container_width=True, type="primary"):
                st.session_state.selected_paket = formasi['judul']
                if st.session_state.user_session and st.session_state.user_session['role'] == 'PREMIUM':
                    st.session_state.page_mode = "UJIAN"
                    st.session_state.ujian_selesai = False
                    st.session_state.jawaban = {}
                    st.session_state.current_index = 0
                    st.session_state.start_time = time.time()
                    st.rerun()
                else:
                    st.warning("Silakan masukkan token lisensi SKB formasi ini di menu Profil untuk membuka soal.")
                    st.session_state.page_mode = "PROFIL"
                    st.rerun()

    st.write("")
    if st.button("⬅️ Kembali ke Beranda"):
        st.session_state.page_mode = "HOME"
        st.rerun()

# =========================================================================
# HALAMAN BIMBEL ONLINE (MENU UTAMA BIMBEL)
# =========================================================================
elif st.session_state.page_mode == "BIMBEL_ONLINE":
    st.markdown("""
        <div class="hero-section" style="padding: 35px;">
            <h2 style="color: white; margin-bottom: 8px; font-size: 32px;">Bimbingan Belajar LulusCAT</h2>
            <p style="font-size: 16px; color: #f0f4f8; margin: 0;">Pilih jalur bimbingan belajar sesuai kebutuhan persiapan seleksi ASN Anda.</p>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.bimbel_state == "HOME":
        bc1, bc2 = st.columns(2)
        
        with bc1:
            st.markdown("""
                <div class="package-card" style="border-top: 5px solid #1f4e78;">
                    <h3 style="color: #1f4e78; font-size: 22px;">Modul Belajar SKD</h3>
                    <p>Materi terstruktur Tes Wawasan Kebangsaan (TWK), Tes Inteligensi Umum (TIU), dan Tes Karakteristik Pribadi (TKP) beserta kuis latihan.</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Buka Modul SKD", use_container_width=True, type="primary"):
                st.session_state.bimbel_state = "SKD_LIST"
                st.rerun()

        with bc2:
            st.markdown("""
                <div class="package-card" style="border-top: 5px solid #d81b60;">
                    <h3 style="color: #d81b60; font-size: 22px;">Modul Belajar SKB</h3>
                    <p>Materi dan ringkasan pilihan Jabatan Fungsional spesifik seperti Widyaiswara, Analis Kebijakan, Perencana, dll.</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Buka Modul SKB", use_container_width=True, type="primary"):
                st.session_state.bimbel_state = "SKB_LIST"
                st.rerun()

        st.write("")
        st.write("")
        if st.button("⬅️ Kembali ke Beranda"):
            st.session_state.page_mode = "HOME"
            st.rerun()

    elif st.session_state.bimbel_state == "SKD_LIST":
        st.markdown("### 📚 Pilih Modul Belajar SKD")
        st.write("Total Modul: 3 | Estimasi Waktu Baca & Latihan: 135 Menit")
        st.write("")

        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.markdown("""
                <div class="package-card">
                    <span style="color: #1f4e78; font-weight: bold; font-size: 13px;">MODUL 1</span>
                    <h4 style="color: #1f4e78; margin-top: 5px; font-size: 18px;">Tes Wawasan Kebangsaan (TWK)</h4>
                    <p style="font-size: 13px; color: #666;">⏱️ ~45 Menit Baca | 📝 25 Soal Kuis</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Mulai Belajar TWK", key="btn_twk", use_container_width=True, type="primary"):
                st.session_state.bimbel_modul = "TWK"
                st.session_state.bimbel_state = "MATERI"
                st.rerun()

        with bc2:
            st.markdown("""
                <div class="package-card">
                    <span style="color: #1f4e78; font-weight: bold; font-size: 13px;">MODUL 2</span>
                    <h4 style="color: #1f4e78; margin-top: 5px; font-size: 18px;">Tes Inteligensi Umum (TIU)</h4>
                    <p style="font-size: 13px; color: #666;">⏱️ ~45 Menit Baca | 📝 25 Soal Kuis</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Mulai Belajar TIU", key="btn_tiu", use_container_width=True, type="primary"):
                st.session_state.bimbel_modul = "TIU"
                st.session_state.bimbel_state = "MATERI"
                st.rerun()

        with bc3:
            st.markdown("""
                <div class="package-card">
                    <span style="color: #1f4e78; font-weight: bold; font-size: 13px;">MODUL 3</span>
                    <h4 style="color: #1f4e78; margin-top: 5px; font-size: 18px;">Tes Karakteristik Pribadi (TKP)</h4>
                    <p style="font-size: 13px; color: #666;">⏱️ ~45 Menit Baca | 📝 25 Soal Kuis</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Mulai Belajar TKP", key="btn_tkp", use_container_width=True, type="primary"):
                st.session_state.bimbel_modul = "TKP"
                st.session_state.bimbel_state = "MATERI"
                st.rerun()

        st.write("")
        if st.button("⬅️ Kembali ke Menu Bimbel"):
            st.session_state.bimbel_state = "HOME"
            st.rerun()

    elif st.session_state.bimbel_state == "SKB_LIST":
        st.markdown("### 🏆 Pilih Modul Belajar SKB Jabatan Fungsional")
        st.write("Modul ringkasan materi kompetensi bidang spesifik untuk persiapan ujian instansi.")
        st.write("")

        skb_modul_list = [
            ("Modul Widyaiswara Ahli Pertama/Muda", "Materi pedagogi, andragogi, perancangan kurikulum diklat, dan evaluasi pembelajaran kedinasan."),
            ("Modul Analis Kebijakan", "Materi metodologi perumusan kebijakan, analisis isu strategis publik, dan advokasi kebijakan pemerintah."),
            ("Modul Analis SDM Aparatur", "Materi pengelolaan kepegawaian ASN berdasar UU ASN, formasi, asesmen, dan pengembangan karier."),
            ("Modul Perencana Ahli", "Materi siklus perencanaan pembangunan nasional, penganggaran berbasis kinerja, dan evaluasi program.")
        ]

        for judul_m, desc_m in skb_modul_list:
            st.markdown(f"""
                <div class="package-card" style="text-align: left; padding: 18px; border-left: 4px solid #d81b60;">
                    <h4 style="color: #1f4e78; margin-bottom: 5px; font-size: 18px;">{judul_m}</h4>
                    <p style="color: #555; font-size: 14px; margin: 0;">{desc_m}</p>
                </div>
            """, unsafe_allow_html=True)

        st.write("")
        if st.button("⬅️ Kembali ke Menu Bimbel"):
            st.session_state.bimbel_state = "HOME"
            st.rerun()

    elif st.session_state.bimbel_state == "MATERI":
        modul = st.session_state.bimbel_modul

        # Muat file JSON materi secara utuh
        materi_data = load_materi(modul)
        
        if materi_data and "bab" in materi_data:
            daftar_bab = materi_data['bab']
            total_slide = len(daftar_bab)

            # Inisialisasi indeks slide aktif di session state jika belum ada
            if 'slide_index' not in st.session_state:
                st.session_state.slide_index = 0

            # Validasi batas indeks slide agar tidak error
            if st.session_state.slide_index >= total_slide:
                st.session_state.slide_index = total_slide - 1
            if st.session_state.slide_index < 0:
                st.session_state.slide_index = 0

            idx_slide = st.session_state.slide_index
            slide_aktif = daftar_bab[idx_slide]

            # Header Topik Utama & Progress Bar yang Padat ke Atas
            st.markdown(f"## 📚 Modul {modul}: {slide_aktif['sub_kategori']}")
            st.progress((idx_slide + 1) / total_slide)
            st.write("")

            # Styling CSS Khusus untuk Teks E-Learning (Font Besar, Bersih, Profesional)
            st.markdown("""
                <style>
                .elearning-card {
                    background-color: white;
                    padding: 40px;
                    border-radius: 12px;
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.04);
                    margin-bottom: 25px;
                }
                .elearning-card p, .elearning-card li {
                    font-size: 18px !important;
                    line-height: 1.8 !important;
                    color: #2c3e50 !important;
                }
                .elearning-card h3, .elearning-card h4 {
                    color: #1f4e78 !important;
                    margin-top: 15px;
                    margin-bottom: 10px;
                }
                </style>
            """, unsafe_allow_html=True)

            # Konten Materi E-Learning (Tanpa Kotak Kosong Terpisah)
            st.markdown('<div class="elearning-card">', unsafe_allow_html=True)
            st.markdown(slide_aktif['isi'])
            st.markdown('</div>', unsafe_allow_html=True)

            st.write("")

            # Tombol Navigasi E-Learning (Sebelumnya & Lanjutkan)
            col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

            with col_nav1:
                if idx_slide > 0:
                    if st.button("⬅️ Sebelumnya", use_container_width=True):
                        st.session_state.slide_index -= 1
                        st.rerun()

            with col_nav3:
                if idx_slide < total_slide - 1:
                    if st.button("Lanjutkan ➡️", use_container_width=True, type="primary"):
                        st.session_state.slide_index += 1
                        st.rerun()
                else:
                    # Tombol di slide terakhir untuk masuk ke kuis
                    if st.button("📝 Mulai Kuis Uji Pemahaman", use_container_width=True, type="primary"):
                        st.session_state.bimbel_state = "KUIS"
                        st.session_state.bimbel_index = 0
                        st.session_state.bimbel_jawaban = {}
                        st.session_state.slide_index = 0  # Reset slide
                        st.rerun()

            st.markdown("---")
            if st.button("⬅️ Keluar ke Daftar Modul SKD"):
                st.session_state.slide_index = 0
                st.session_state.bimbel_state = "SKD_LIST"
                st.rerun()

        else:
            st.warning(f"File materi_skd_{modul.lower()}.json belum ditemukan atau formatnya kosong.")

    elif st.session_state.bimbel_state == "KUIS":
        modul = st.session_state.bimbel_modul
        filtered_soal = [s for s in st.session_state.soal_list if s.get('kategori', '').upper() == modul]
        if not filtered_soal:
            filtered_soal = st.session_state.soal_list[:25]
        
        max_soal = min(25, len(filtered_soal))
        idx = st.session_state.get('bimbel_index', 0)
        
        if idx >= max_soal:
            st.markdown("### 🎉 Selamat! Anda Telah Menyelesaikan Kuis Modul ini.")
            score = 0
            for i, soal in enumerate(filtered_soal[:max_soal]):
                s_id = soal.get('id', i+1)
                user_ans = st.session_state.bimbel_jawaban.get(s_id)
                if modul == "TKP":
                    score += soal.get('bobot', {}).get(user_ans, 0)
                else:
                    if user_ans and user_ans == soal.get('kunci'):
                        score += 5
            
            st.metric("Total Poin Kuis Anda", score)
            if st.button("Selesai & Kembali ke Menu Bimbel"):
                st.session_state.bimbel_state = "HOME"
                st.rerun()
        else:
            soal_data = filtered_soal[idx]
            s_id = soal_data.get('id', idx+1)
            
            st.markdown(f"### Uji Pemahaman {modul} — Soal No. {idx+1} dari {max_soal}")
            st.markdown(f"<div class='card-soal'>{soal_data['soal']}</div>", unsafe_allow_html=True)

            if 'gambar_soal' in soal_data:
                st.markdown(soal_data['gambar_soal'], unsafe_allow_html=True)
            st.write("")

            current_ans = st.session_state.bimbel_jawaban.get(s_id, None)

            if 'pilihan_gambar' in soal_data:
                options_list = list(soal_data['pilihan_gambar'].keys())
                cols_opsi = st.columns(len(options_list))
                for i, huruf in enumerate(options_list):
                    with cols_opsi[i]:
                        st.markdown(soal_data['pilihan_gambar'][huruf], unsafe_allow_html=True)
                        st.markdown(f"<div style='text-align:center;font-weight:bold;'>{huruf}</div>", unsafe_allow_html=True)
                st.write("")
                selected_opt = st.radio(
                    "Pilih Jawaban:",
                    options_list,
                    format_func=lambda x: f"Pilihan {x}",
                    index=options_list.index(current_ans) if current_ans in options_list else None,
                    horizontal=True,
                    key=f"b_radio_{s_id}"
                )
            else:
                options_list = list(soal_data['pilihan'].keys())
                selected_opt = st.radio(
                    "Pilih Jawaban:",
                    options_list,
                    format_func=lambda x: f"{x}. {soal_data['pilihan'][x]}",
                    index=options_list.index(current_ans) if current_ans in options_list else None,
                    key=f"b_radio_{s_id}"
                )

            bk1, bk2 = st.columns(2)
            with bk1:
                if st.button("Simpan & Lanjut"):
                    if selected_opt:
                        st.session_state.bimbel_jawaban[s_id] = selected_opt
                    st.session_state.bimbel_index += 1
                    st.rerun()
            with bk2:
                if st.button("Kembali ke Materi"):
                    st.session_state.bimbel_state = "MATERI"
                    st.rerun()

# =========================================================================
# HALAMAN UTAMA (HOME) — DENGAN 5 MENU UTAMA BERJAJAR
# =========================================================================
elif st.session_state.page_mode == "HOME":
    st.markdown("""
        <div class="hero-section">
            <span style="background-color: rgba(255,255,255,0.25); padding: 5px 12px; border-radius: 6px; font-size: 13px; font-weight: bold; color: white;">Platform Persiapan Seleksi ASN</span>
            <h1 style="color: white; margin-top: 12px; margin-bottom: 12px;">Persiapkan Diri.<br>Taklukkan Tes ASN.</h1>
            <p>LulusCAT hadir untuk membantu Anda meraih mimpi menjadi ASN melalui tryout SKD, Tryout SKB Jabatan Fungsional, bank soal, e-book, hingga bimbel online terpercaya.</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    
    # 1. Tryout SKD CAT
    with c1:
        st.markdown("""
            <div class="package-card">
                <h4>🎯 Tryout SKD CAT</h4>
                <p>Simulasi CAT SKD lengkap & ranking nasional.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Mulai Sekarang", key="btn_tryout_skd", use_container_width=True, type="primary"):
            st.session_state.page_mode = "LIST_PAKET_SKD"
            st.rerun()

    # 2. Tryout SKB CAT
    with c2:
        st.markdown("""
            <div class="package-card">
                <h4>🏆 Tryout SKB CAT</h4>
                <p>Simulasi kompetensi bidang spesifik Jabatan Fungsional.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Pilih Formasi", key="btn_tryout_skb", use_container_width=True, type="primary"):
            st.session_state.page_mode = "LIST_SKB_FOROMASI"
            st.rerun()

    # 3. Bimbel Online
    with c3:
        st.markdown("""
            <div class="package-card">
                <h4>🎓 Bimbel Online</h4>
                <p>Program belajar terarah micro-learning intensif.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Mulai Sekarang", key="btn_bimbel", use_container_width=True):
            st.session_state.page_mode = "BIMBEL_ONLINE"
            st.session_state.bimbel_state = "HOME"
            st.rerun()

    # 4. Bank Soal
    with c4:
        st.markdown("""
            <div class="package-card">
                <h4>📝 Bank Soal</h4>
                <p>Kumpulan soal SKD & SKB lengkap dengan pembahasan.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Mulai Sekarang", key="btn_bank_soal", use_container_width=True):
            st.session_state.page_mode = "KATEGORI_SOAL"
            st.rerun()

    # 5. E-Book Digital
    with c5:
        st.markdown("""
            <div class="package-card">
                <h4>📚 E-Book Digital</h4>
                <p>Panduan lengkap PDF modul persiapan seleksi ASN.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Lihat Katalog", key="btn_ebook", use_container_width=True):
            st.session_state.page_mode = "KATALOG_DIGITAL"
            st.rerun()

    st.markdown("---")
    st.markdown("### 🔥 Produk E-Book & Digital Terlaris LulusCAT")
    
    conn = sqlite3.connect(DB_NAME)
    df_top = pd.read_sql("SELECT judul, harga, harga_coret, link_lynk, gambar_url FROM digital_products LIMIT 4", conn)
    conn.close()

    p_cols = st.columns(4)
    for i, row in df_top.iterrows():
        with p_cols[i % 4]:
            st.markdown(f'<div class="product-card">', unsafe_allow_html=True)
            img_val = str(row['gambar_url']).strip() if row['gambar_url'] else ""
            if img_val and img_val.startswith("http"):
                st.image(img_val, use_container_width=True)
            
            coret_html = f"<span style='text-decoration: line-through; color: #888; font-size: 13px; margin-right: 8px;'>{row['harga_coret']}</span>" if row['harga_coret'] else ""
            
            st.markdown(f"""
                <h5 style="font-size: 18px; color: #1f4e78; margin-bottom: 8px; font-weight: 700;">{row['judul']}</h5>
                <p style="font-size: 15px; color: #d81b60; font-weight: bold; margin-bottom: 6px;">{coret_html} {row['harga']}</p>
                <p style="font-size: 13px; color: #666;">⭐ 4.9 (Terlaris)</p>
            </div>
            """, unsafe_allow_html=True)
            lynk_url = row['link_lynk'] if row['link_lynk'] else "https://lynk.id/luluscat"
            st.link_button("🛒 Beli Sekarang", lynk_url, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎯 Coba Latihan Soal Gratis Hari Ini!")
    
    if st.session_state.soal_list:
        current_minute_index = int(time.time() // 60) % len(st.session_state.soal_list)
        active_latihan = st.session_state.soal_list[current_minute_index]
    else:
        active_latihan = {
            "id": 1,
            "kategori": "TKP",
            "soal": "Kemudahan mengakses informasi via internet saat ini, membuat saya...",
            "pilihan": {
                "A": "tergantung pada pemakainya",
                "B": "mengganggu kinerja secara umum",
                "C": "mengganggu hubungan interpersonal",
                "D": "mempermudah belajar secara mandiri",
                "E": "memperluas wawasan dan meningkatkan keilmuan"
            },
            "kunci": "E",
            "bobot": {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5},
            "pembahasan": "Memperluas wawasan dan meningkatkan keilmuan mencerminkan nilai Berorientasi Pelayanan secara positif."
        }

    with st.container():
        st.markdown(f'<span class="free-badge">FREE</span> Latihan Soal {active_latihan.get("kategori", "SKD")}', unsafe_allow_html=True)
        st.write("")
        st.markdown(f"**{active_latihan['soal']}**")

        if 'gambar_soal' in active_latihan:
            st.markdown(active_latihan['gambar_soal'], unsafe_allow_html=True)

        if 'pilihan_gambar' in active_latihan:
            options_free = active_latihan['pilihan_gambar']
            cols_opsi = st.columns(len(options_free))
            for i, huruf in enumerate(options_free.keys()):
                with cols_opsi[i]:
                    st.markdown(options_free[huruf], unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center;font-weight:bold;'>{huruf}</div>", unsafe_allow_html=True)
            selected_free = st.radio("Pilih jawaban latihan:", list(options_free.keys()), format_func=lambda x: f"Pilihan {x}", horizontal=True, key=f"free_radio_{current_minute_index}")
        else:
            options_free = active_latihan['pilihan']
            selected_free = st.radio("Pilih jawaban latihan:", list(options_free.keys()), format_func=lambda x: f"{x}. {options_free[x]}", key=f"free_radio_{current_minute_index}")
        
        if st.button("Lihat Pembahasan & Poin"):
            st.markdown("---")
            kat_latihan = active_latihan.get('kategori', '').upper()
            if kat_latihan == "TKP":
                poin_didapat = active_latihan.get('bobot', {}).get(selected_free, 0)
                st.markdown(f"⭐ **Poin Pilihan Anda ({selected_free}): {poin_didapat}** (Maksimal: 5)")
            else:
                kunci_benar = active_latihan.get('kunci')
                if selected_free == kunci_benar:
                    st.success(f"✅ Jawaban Anda Benar! Kunci: {kunci_benar}")
                else:
                    st.error(f"❌ Jawaban Anda Kurang Tepat. Kunci Benar: {kunci_benar}")
            
            teks_pembahasan = active_latihan.get('pembahasan', 'Pembahasan sesuai dengan kisi-kisi resmi BKN.')
            st.markdown(f"<div class='pembahasan-box'><b>Pembahasan:</b> {teks_pembahasan}</div>", unsafe_allow_html=True)

# =========================================================================
# HALAMAN KATEGORI (SKD vs SKB)
# =========================================================================
elif st.session_state.page_mode == "KATEGORI_SOAL":
    st.markdown("## 📂 Kategori Bank Soal LulusCAT")
    st.write("Pilih kategori ujian yang ingin Anda pelajari.")
    st.write("")

    col_skd, col_skb = st.columns(2)
    
    with col_skd:
        st.markdown("""
            <div class="package-card" style="border-top: 5px solid #1f4e78;">
                <h3 style="color: #1f4e78; margin-bottom: 10px; font-size: 22px;">📝 SKD CPNS</h3>
                <p style="font-size: 15px; color: #666;">Seleksi Kompetensi Dasar meliputi materi TWK, TIU, dan TKP sesuai kisi-kisi resmi BKN.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Buka Bank Soal SKD", use_container_width=True, type="primary"):
            st.session_state.page_mode = "LIST_PAKET_SKD"
            st.rerun()

    with col_skb:
        st.markdown("""
            <div class="package-card" style="border-top: 5px solid #d81b60;">
                <h3 style="color: #d81b60; margin-bottom: 10px; font-size: 22px;">💼 SKB Jabatan Fungsional</h3>
                <p style="font-size: 15px; color: #666;">Seleksi Kompetensi Bidang spesifik sesuai formasi instansi.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Buka Pilihan SKB", use_container_width=True, type="primary"):
            st.session_state.page_mode = "LIST_SKB_FOROMASI"
            st.rerun()

    st.write("")
    if st.button("⬅️ Kembali ke Beranda"):
        st.session_state.page_mode = "HOME"
        st.rerun()

# =========================================================================
# HALAMAN DAFTAR PAKET SKD
# =========================================================================
elif st.session_state.page_mode == "LIST_PAKET_SKD":
    st.markdown("## 📚 Daftar Paket Tryout CAT BKN")
    st.write("Pilih paket latihan atau tryout sesuai kebutuhan Anda.")
    st.write("")

    is_premium = False
    if st.session_state.user_session and st.session_state.user_session['role'] == 'PREMIUM':
        is_premium = True

    st.markdown("### 🟢 Paket Akses Gratis")
    if st.button("📝 Kerjakan TryOut Gratis (55 Soal • 50 Menit)", use_container_width=True, type="primary"):
        if st.session_state.user_session is None:
            st.session_state.page_mode = "REGISTRASI"
            st.rerun()
        else:
            st.session_state.selected_paket = "TryOut Gratis 55 Soal"
            st.session_state.page_mode = "KONFIRMASI_TOKEN_GRATIS"
            st.rerun()

    st.markdown("---")
    st.markdown("### 💎 Paket Premium (110 Soal Standar BKN • 100 Menit)")
    
    daftar_paket = [
        {"id": "TryOut SKD 01", "judul": "TryOut SKD 01", "kesulitan": "Sedang"},
        {"id": "TryOut SKD 02", "judul": "TryOut SKD 02", "kesulitan": "Sedang"},
        {"id": "TryOut SKD 03", "judul": "TryOut SKD 03", "kesulitan": "Sulit"},
        {"id": "TryOut SKD 04", "judul": "TryOut SKD 04", "kesulitan": "HOTS"},
        {"id": "TryOut SKD 05", "judul": "TryOut SKD 05", "kesulitan": "Nasional"}
    ]

    col_p_list = st.columns(3)
    for i, pkt in enumerate(daftar_paket):
        with col_p_list[i % 3]:
            st.markdown(f"""
                <div class="package-card">
                    <h4 style="font-size: 20px; color: #1f4e78; margin-bottom: 6px; font-weight: 700;">{pkt['judul']}</h4>
                    <p style="font-size: 14px; color: #666;">Tingkat: <b>{pkt['kesulitan']}</b></p>
                    <hr style="border:0; border-top:1px solid #eee;">
                    <p style="font-size: 15px;">📝 110 Soal<br>⏱️ 100 Menit</p>
                </div>
            """, unsafe_allow_html=True)
            
            if is_premium:
                if st.button(f"Mulai {pkt['judul']}", key=f"p_open_{i}", use_container_width=True):
                    st.session_state.selected_paket = pkt['id']
                    st.session_state.ujian_selesai = False
                    st.session_state.jawaban = {}
                    st.session_state.current_index = 0
                    st.session_state.start_time = time.time()
                    st.session_state.page_mode = "UJIAN"
                    st.rerun()
            else:
                if st.button(f"🔒 Terkunci (Buka Token)", key=f"p_lock_{i}", use_container_width=True):
                    if st.session_state.user_session is None:
                        st.session_state.page_mode = "REGISTRASI"
                        st.rerun()
                    else:
                        st.session_state.page_mode = "PROFIL"
                        st.rerun()

    st.write("")
    if st.button("⬅️ Kembali ke Kategori"):
        st.session_state.page_mode = "KATEGORI_SOAL"
        st.rerun()

# =========================================================================
# HALAMAN KONFIRMASI TOKEN UNTUK TRYOUT GRATIS
# =========================================================================
elif st.session_state.page_mode == "KONFIRMASI_TOKEN_GRATIS":
    st.markdown("""
        <div class="exam-card">
            <div class="exam-header">
                <div style="font-size: 15px; opacity: 0.8;">Verifikasi Token Akses</div>
                <div style="font-size: 26px; font-weight: bold;">TryOut Gratis (55 Soal)</div>
            </div>
    """, unsafe_allow_html=True)

    usr = st.session_state.user_session
    st.write(f"Halo **{usr['nama']}**, masukkan Token TryOut Gratis Anda untuk memulai simulasi.")
    st.markdown(f"*(Token gratis Anda: `{usr['free_token']}`)*")

    with st.form("form_konfirmasi_free_token"):
        input_f_token = st.text_input("Masukkan Token Gratis Anda", type="password")
        btn_mulai_free = st.form_submit_button("🚀 Mulai TryOut Gratis Sekarang", use_container_width=True, type="primary")

        if btn_mulai_free:
            if input_f_token.strip().upper() == usr['free_token'].upper():
                st.success("Token valid! Memuat soal...")
                time.sleep(1)
                st.session_state.ujian_selesai = False
                st.session_state.jawaban = {}
                st.session_state.current_index = 0
                st.session_state.start_time = time.time()
                st.session_state.page_mode = "UJIAN"
                st.rerun()
            else:
                st.error("❌ Token gratis salah! Periksa kembali token yang tertera di profil Anda.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    if st.button("⬅️ Kembali ke Daftar Paket"):
        st.session_state.page_mode = "LIST_PAKET_SKD"
        st.rerun()

# =========================================================================
# PROSES UJIAN CAT BKN
# =========================================================================
elif st.session_state.page_mode == "UJIAN" and not st.session_state.ujian_selesai:
    if st.session_state.selected_paket == "TryOut Gratis 55 Soal":
        list_twk = [s for s in st.session_state.soal_list if s.get('kategori', '').upper() == "TWK"]
        list_tiu = [s for s in st.session_state.soal_list if s.get('kategori', '').upper() == "TIU"]
        list_tkp = [s for s in st.session_state.soal_list if s.get('kategori', '').upper() == "TKP"]
        
        sample_twk = list_twk[:15] if len(list_twk) >= 15 else list_twk
        sample_tiu = list_tiu[:15] if len(list_tiu) >= 15 else list_tiu
        sample_tkp = list_tkp[:25] if len(list_tkp) >= 25 else list_tkp
        
        active_soal_list = sample_twk + sample_tiu + sample_tkp
        TOTAL_DURATION = 50 * 60
    else:
        paket_soal_penuh = [s for s in st.session_state.soal_list if s.get('paket', 'TryOut SKD 01') == st.session_state.selected_paket]
        active_soal_list = paket_soal_penuh if paket_soal_penuh else st.session_state.soal_list
        TOTAL_DURATION = 100 * 60

    elapsed_time = int(time.time() - st.session_state.start_time)
    remaining_time = TOTAL_DURATION - elapsed_time

    if remaining_time <= 0:
        st.warning("Waktu ujian habis!")
        st.session_state.ujian_selesai = True
        st.session_state.page_mode = "SELESAI"
        st.rerun()

    rem_mins, rem_secs = divmod(remaining_time, 60)
    rem_hours, rem_mins = divmod(rem_mins, 60)
    timer_str = f"{rem_hours:02d}:{rem_mins:02d}:{rem_secs:02d}"

    nama_peserta = st.session_state.user_session['nama'] if st.session_state.user_session else "Tamu"

    st.markdown(f'<div class="main-header">CAT BKN - {st.session_state.selected_paket}</div>', unsafe_allow_html=True)
    st.write("")

    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
    with c1:
        st.markdown(f"**Peserta:** {nama_peserta}<br>**Akses:** {st.session_state.selected_paket}", unsafe_allow_html=True)
    with c2:
        st.markdown(f"**Durasi**<br>{int(TOTAL_DURATION/60)} Menit", unsafe_allow_html=True)
    with c3:
        st.markdown(f"**Total Soal**<br>{len(active_soal_list)}", unsafe_allow_html=True)
    with c4:
        terjawab = len(st.session_state.jawaban)
        st.markdown(f"**Dijawab**<br>{terjawab}", unsafe_allow_html=True)
    with c5:
        st.markdown(f"**Belum**<br>{len(active_soal_list) - terjawab}", unsafe_allow_html=True)

    st.markdown("---")

    idx = st.session_state.current_index
    if idx >= len(active_soal_list):
        idx = 0
        st.session_state.current_index = 0
    soal_data = active_soal_list[idx]

    col_s, col_n = st.columns([3, 1])

    with col_s:
        st.markdown(f"**Soal No. {idx+1} ({soal_data.get('kategori', 'UMUM')})**")
        st.markdown(f"<div class='card-soal'>{soal_data['soal']}</div>", unsafe_allow_html=True)

        # Render gambar pola soal (khusus soal figural visual: analogi/seri/matriks gambar)
        if 'gambar_soal' in soal_data:
            st.markdown(soal_data['gambar_soal'], unsafe_allow_html=True)
        st.write("")

        s_unique_id = soal_data.get('id', idx+1)
        current_ans = st.session_state.jawaban.get(s_unique_id, None)

        if 'pilihan_gambar' in soal_data:
            # Soal figural dengan pilihan berupa gambar (Analogi, Seri, Matriks Gambar)
            options_list = list(soal_data['pilihan_gambar'].keys())
            cols_opsi = st.columns(len(options_list))
            for i, huruf in enumerate(options_list):
                with cols_opsi[i]:
                    st.markdown(soal_data['pilihan_gambar'][huruf], unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center;font-weight:bold;'>{huruf}</div>", unsafe_allow_html=True)
            st.write("")
            selected_option = st.radio(
                "Pilih Jawaban:",
                options_list,
                format_func=lambda x: f"Pilihan {x}",
                index=options_list.index(current_ans) if current_ans in options_list else None,
                horizontal=True,
                key=f"radio_soal_{idx}_{s_unique_id}"
            )
        else:
            # Soal biasa (teks) atau Ketidaksamaan Gambar (pilihan tetap berupa teks label "Gambar N")
            options_list = list(soal_data['pilihan'].keys())
            selected_option = st.radio(
                "Pilih Jawaban:",
                options_list,
                format_func=lambda x: f"{x}. {soal_data['pilihan'][x]}",
                index=options_list.index(current_ans) if current_ans in options_list else None,
                key=f"radio_soal_{idx}_{s_unique_id}"
            )

        b1, b2 = st.columns(2)
        with b1:
            if st.button("SIMPAN DAN LANJUTKAN"):
                if selected_option:
                    st.session_state.jawaban[s_unique_id] = selected_option
                if st.session_state.current_index < len(active_soal_list) - 1:
                    st.session_state.current_index += 1
                    st.rerun()
        with b2:
            if st.button("LEWATKAN SOAL"):
                if st.session_state.current_index < len(active_soal_list) - 1:
                    st.session_state.current_index += 1
                    st.rerun()

    with col_n:
        st.markdown("#### Waktu Mundur")
        st.markdown(f"<div class='timer-badge'>{timer_str}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("#### Navigasi Soal")
        
        cols = st.columns(5)
        for i, soal in enumerate(active_soal_list):
            s_id = soal.get('id', i+1)
            is_answered = s_id in st.session_state.jawaban
            btn_color = "🟢" if is_answered else "🔴"
            
            with cols[i % 5]:
                if st.button(f"{btn_color} {i+1}", key=f"nav_gratis_{i}_{s_id}"):
                    st.session_state.current_index = i
                    st.rerun()

        st.markdown("---")
        if st.button("SELESAI UJIAN", type="primary"):
            st.session_state.ujian_selesai = True
            st.session_state.page_mode = "SELESAI"
            st.rerun()

    st.stop()

# =========================================================================
# HALAMAN EVALUASI & PEMBAHASAN (DENGAN PASSING GRADE)
# =========================================================================
elif st.session_state.page_mode == "SELESAI" or st.session_state.ujian_selesai:
    st.subheader(f"Hasil Evaluasi & Rekapitulasi: {st.session_state.selected_paket}")
    
    if st.session_state.selected_paket == "TryOut Gratis 55 Soal":
        list_twk = [s for s in st.session_state.soal_list if s.get('kategori', '').upper() == "TWK"]
        list_tiu = [s for s in st.session_state.soal_list if s.get('kategori', '').upper() == "TIU"]
        list_tkp = [s for s in st.session_state.soal_list if s.get('kategori', '').upper() == "TKP"]
        
        sample_twk = list_twk[:15] if len(list_twk) >= 15 else list_twk
        sample_tiu = list_tiu[:15] if len(list_tiu) >= 15 else list_tiu
        sample_tkp = list_tkp[:25] if len(list_tkp) >= 25 else list_tkp
        
        active_soal_list = sample_twk + sample_tiu + sample_tkp
    else:
        paket_soal_penuh = [s for s in st.session_state.soal_list if s.get('paket', 'TryOut SKD 01') == st.session_state.selected_paket]
        active_soal_list = paket_soal_penuh if paket_soal_penuh else st.session_state.soal_list

    skor_twk, skor_tiu, skor_tkp = 0, 0, 0
    for soal in active_soal_list:
        s_id = soal.get('id', 1)
        ans = st.session_state.jawaban.get(s_id)
        kat = soal.get('kategori', '').upper()
        if kat == "TWK":
            if ans and ans == soal.get('kunci'):
                skor_twk += 5
        elif kat == "TIU":
            if ans and ans == soal.get('kunci'):
                skor_tiu += 5
        elif kat == "TKP":
            if ans and 'bobot' in soal:
                skor_tkp += soal['bobot'].get(ans, 0)

    total_skor = skor_twk + skor_tiu + skor_tkp
    usr_obj = st.session_state.user_session
    nama_peserta = usr_obj['nama'] if usr_obj else "Tamu"
    username_peserta = usr_obj['username'] if usr_obj else "tamu"
    wa_peserta = usr_obj.get('no_wa', '-') if usr_obj else "-"
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO exam_history (username, nama, no_wa, paket, skor_twk, skor_tiu, skor_tkp, total_skor, waktu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username_peserta, nama_peserta, wa_peserta, st.session_state.selected_paket, skor_twk, skor_tiu, skor_tkp, total_skor, waktu_sekarang))
    conn.commit()
    conn.close()

    st.metric(label="Total Skor Anda", value=total_skor)
    
    ca, cb, cc = st.columns(3)
    
    with ca:
        st.metric("Skor TWK", skor_twk)
        if skor_twk >= 65:
            st.caption("Passing Grade: 65 (✅ Lulus)")
        else:
            st.caption("Passing Grade: 65 (❌ Belum Lulus)")
            
    with cb:
        st.metric("Skor TIU", skor_tiu)
        if skor_tiu >= 80:
            st.caption("Passing Grade: 80 (✅ Lulus)")
        else:
            st.caption("Passing Grade: 80 (❌ Belum Lulus)")
            
    with cc:
        st.metric("Skor TKP", skor_tkp)
        if skor_tkp >= 166:
            st.caption("Passing Grade: 166 (✅ Lulus)")
        else:
            st.caption("Passing Grade: 166 (❌ Belum Lulus)")

    st.markdown("---")
    st.markdown("### 📚 Kunci Jawaban & Pembahasan Lengkap")
    
    for i, soal in enumerate(active_soal_list, 1):
        s_id = soal.get('id', i)
        user_choice = st.session_state.jawaban.get(s_id, "Tidak dijawab")
        kat = soal.get('kategori', 'UMUM')
        
        with st.expander(f"Soal No. {i} ({kat}) - Pilihan Anda: {user_choice}"):
            st.markdown(f"**Soal:** {soal['soal']}")
            if 'gambar_soal' in soal:
                st.markdown(soal['gambar_soal'], unsafe_allow_html=True)
            st.write("")

            pilihan_dict = soal.get('pilihan_gambar', soal.get('pilihan', {}))
            is_gambar = 'pilihan_gambar' in soal

            if is_gambar:
                cols_review = st.columns(len(pilihan_dict))
                for i2, (opt_key, opt_val) in enumerate(pilihan_dict.items()):
                    marker = ""
                    if opt_key == soal.get('kunci'):
                        marker = " ✅"
                    if opt_key == user_choice and opt_key != soal.get('kunci'):
                        marker = " ❌"
                    elif opt_key == user_choice and opt_key == soal.get('kunci'):
                        marker = " ✅⭐"
                    with cols_review[i2]:
                        st.markdown(opt_val, unsafe_allow_html=True)
                        st.markdown(f"<div style='text-align:center;font-weight:bold;'>{opt_key}{marker}</div>", unsafe_allow_html=True)
            else:
                for opt_key, opt_val in pilihan_dict.items():
                    marker = ""
                    if kat == "TKP":
                        bobot_val = soal.get('bobot', {}).get(opt_key, 0)
                        if opt_key == user_choice:
                            marker = f" ⭐ *(Pilihan Anda - Poin: {bobot_val})*"
                        else:
                            marker = f" (Poin: {bobot_val})"
                    else:
                        if opt_key == soal.get('kunci'):
                            marker = " ✅ *(Kunci Benar)*"
                        if opt_key == user_choice and opt_key != soal.get('kunci'):
                            marker = " ❌ *(Pilihan Anda)*"
                        elif opt_key == user_choice and opt_key == soal.get('kunci'):
                            marker = " ✅ ⭐ *(Pilihan Anda & Kunci Benar)*"

                    st.markdown(f"- **{opt_key}.** {opt_val}{marker}")

            st.markdown("---")
            if kat != "TKP":
                kunci_benar = soal.get('kunci')
                if is_gambar:
                    st.markdown(f"💡 **Kunci Jawaban Benar:** `{kunci_benar}`")
                else:
                    teks_kunci = pilihan_dict.get(kunci_benar, '')
                    st.markdown(f"💡 **Kunci Jawaban Benar:** `{kunci_benar}. {teks_kunci}`")
                teks_pembahasan = soal.get('pembahasan', 'Pembahasan sesuai dengan kisi-kisi resmi BKN.')
                st.markdown(f"<div class='pembahasan-box'><b>Pembahasan:</b> {teks_pembahasan}</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Keluar / Kembali ke Daftar Paket"):
        st.session_state.jawaban = {}
        st.session_state.current_index = 0
        st.session_state.ujian_selesai = False
        st.session_state.start_time = None
        st.session_state.page_mode = "LIST_PAKET_SKD"
        st.rerun()
