import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Mengizinkan akses dari Frontend React

# --- KONFIGURASI DATABASE ---
DB_CONFIG = {
    "dbname": "result_cleansing",
    "user": "postgres",
    "password": "2lNyRKW3oc9kan8n",
    "host": "103.183.92.158",
    "port": "5432"
}

def get_db_connection():
    """
    Membuat dan mengembalikan koneksi ke database PostgreSQL.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        # print("✅ Koneksi database berhasil dibuat.")
        return conn
    except Exception as e:
        print(f"❌ Gagal menyambung ke database: {str(e)}")
        return None

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "Server Berjalan", "message": "Gunakan endpoint /api/data?table=nama_tabel_cl"})

@app.route('/api/data', methods=['GET'])
def get_data():
    """
    Endpoint untuk mengambil data dari tabel spesifik di schema 'kesehatan'.
    Contoh call: GET /api/data?table=ahh_cl
    """
    table_name = request.args.get('table')
    
    # Validasi sederhana keamanan: Pastikan tabel berakhiran '_cl'
    if not table_name or not table_name.endswith('_cl'):
        return jsonify({"error": "Nama tabel tidak valid atau dilarang (harus akhiran _cl)."}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Gagal koneksi ke database"}), 500

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query dinamis ke schema 'kesehatan'
        # Menggunakan f-string dengan hati-hati. Pastikan table_name valid.
        query = f'SELECT * FROM kesehatan."{table_name}" ORDER BY tahun ASC'
        
        cur.execute(query)
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify(rows)
        
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"error": f"Terjadi kesalahan query: {str(e)}"}), 500

if __name__ == '__main__':
    # Jalankan server di port 5000
    print("🚀 Server berjalan di http://localhost:5000")
    app.run(debug=True, port=5000)