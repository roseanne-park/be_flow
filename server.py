import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash 

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "290922",
    "host": "localhost",
    "port": "5431"
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Gagal menyambung ke database: {str(e)}")
        return None

# --- INISIALISASI TABEL USERS ---
def init_user_table():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Memastikan schema 'kesehatan' ada
            cur.execute("CREATE SCHEMA IF NOT EXISTS kesehatan;")
            
            # Membuat tabel users di dalam schema 'kesehatan'
            cur.execute("""
                CREATE TABLE IF NOT EXISTS kesehatan.users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("✅ Tabel 'kesehatan.users' siap.")
        except Exception as e:
            print(f"❌ Gagal init tabel users: {e}")

init_user_table()

# --- ROOT ROUTE ---
@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "Server is running", "message": "Welcome to the Health Profile API"})

# --- AUTH ROUTES ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username dan password wajib diisi"}), 400

    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database error"}), 500

    try:
        cur = conn.cursor()
        
        # 'pbkdf2:sha256'
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Insert ke schema kesehatan.users
        cur.execute("INSERT INTO kesehatan.users (username, password) VALUES (%s, %s) RETURNING id", (username, hashed_pw))
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Registrasi berhasil", "user_id": user_id}), 201
    except psycopg2.errors.UniqueViolation:
        if conn: conn.rollback()
        return jsonify({"error": "Username sudah dipakai"}), 409
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database error"}), 500

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Select dari schema kesehatan.users
        cur.execute("SELECT * FROM kesehatan.users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            return jsonify({
                "message": "Login sukses",
                "user": {"id": user['id'], "username": user['username']}
            }), 200
        else:
            return jsonify({"error": "Username atau password salah"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DATA ROUTES ---

@app.route('/api/data', methods=['GET'])
def get_data():
    table_name = request.args.get('table')
    if not table_name or not table_name.endswith('_cl'):
        return jsonify({"error": "Nama tabel tidak valid"}), 400

    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Error"}), 500

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = f'SELECT * FROM kesehatan."{table_name}" ORDER BY tahun ASC'
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Server berjalan di http://localhost:5000")
    app.run(debug=True, port=5000)