from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date
import mysql.connector
import os
from dotenv import load_dotenv

# Membaca variabel lingkungan dari file .env
load_dotenv()

# Inisialisasi Aplikasi FastAPI
app = FastAPI(title="Kas RW API")

# Konfigurasi CORS agar bisa diakses oleh Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fungsi untuk menghubungkan ke database MySQL
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

# Pydantic Schema untuk Validasi Data
class TransaksiBase(BaseModel):
    tanggal: date
    keterangan: str
    jenis: str  # 'pemasukan' atau 'pengeluaran'
    jumlah: float

class TransaksiUpdate(BaseModel):
    tanggal: Optional[date] = None
    keterangan: Optional[str] = None
    jenis: Optional[str] = None
    jumlah: Optional[float] = None

# ==================== ENDPOINT / ROUTES ====================

@app.get("/")
def root():
    return {"message": "Kas RW API berjalan"}

# 1. READ ALL - Mengambil semua data transaksi
@app.get("/transaksi")
def get_all():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM transaksi ORDER BY tanggal DESC")
    rows = cursor.fetchall()
    db.close()
    return rows

# 2. READ ONE - Mengambil satu data transaksi berdasarkan ID
@app.get("/transaksi/{id}")
def get_one(id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM transaksi WHERE id = %s", (id,))
    row = cursor.fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    return row

# 3. CREATE - Menambahkan transaksi baru (Disesuaikan dengan Modul Hal 5)
@app.post("/transaksi", status_code=201)
def create(data: TransaksiBase):
    db = get_db()
    cursor = db.cursor()
    query = "INSERT INTO transaksi (tanggal, keterangan, jenis, jumlah) VALUES (%s, %s, %s, %s)"
    values = (data.tanggal, data.keterangan, data.jenis, data.jumlah)
    
    try:
        cursor.execute(query, values)
        db.commit()  
        insert_id = cursor.lastrowid
        db.close()
        # Mengikuti format return asli modul halaman 5 line 191
        return {"id": insert_id, "message": "Transaksi berhasil ditambahkan"}
    except mysql.connector.Error as err:
        db.close()
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan data: {err}")

# 4. UPDATE - Memperbarui data transaksi (Disesuaikan dengan standar logika Modul Hal 6)
@app.put("/transaksi/{id}")
def update(id: int, data: TransaksiUpdate):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Cek apakah data transaksi ada
    cursor.execute("SELECT * FROM transaksi WHERE id = %s", (id,))
    row = cursor.fetchone()
    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    
    # Logika menggabungkan data lama dengan data baru yang tidak None (Modul Hal 6 Line 200)
    updated = dict(row)
    for k, v in data.dict().items():
        if v is not None:
            updated[k] = v
            
    query = """
        UPDATE transaksi 
        SET tanggal = %s, keterangan = %s, jenis = %s, jumlah = %s 
        WHERE id = %s
    """
    values = (updated["tanggal"], updated["keterangan"], updated["jenis"], updated["jumlah"], id)
    
    try:
        cursor.execute(query, values)
        db.commit()
        db.close()
        # Mengikuti format return asli modul halaman 6 line 208
        return {"message": "Transaksi berhasil diperbarui"}
    except mysql.connector.Error as err:
        db.close()
        raise HTTPException(status_code=500, detail=f"Gagal memperbarui data: {err}")