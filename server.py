import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash 
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "290922", 
    "host": "localhost",
    "port": "5431" 
}

logging.basicConfig(level=logging.INFO)

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ FATAL ERROR DB: {e}")
        return None

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Terjadi Error: {e}")
    response = jsonify({"error": str(e)})
    response.status_code = 500
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Backend Aktif di Port 5001!"})

@app.route('/api/register', methods=['POST'])
def register():
    # 1. Cek Koneksi DB
    conn = get_db_connection()
    if not conn: 
        raise Exception("Gagal Konek Database (Cek Terminal Python)")

    data = request.json
    try:
        cur = conn.cursor()
        
        # 2. Pastikan Schema Ada
        cur.execute("CREATE SCHEMA IF NOT EXISTS kesehatan;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kesehatan.users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 3. Proses Register
        hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
        cur.execute(
            "INSERT INTO kesehatan.users (username, password) VALUES (%s, %s) RETURNING id", 
            (data['username'], hashed_pw)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        
        return jsonify({"message": "Registrasi berhasil", "user_id": user_id}), 201

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"error": "Username sudah dipakai"}), 409
    except Exception as e:
        conn.rollback()
        raise e # Lempar ke error handler
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    if not conn: raise Exception("Gagal Konek Database")

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM kesehatan.users WHERE username = %s", (data.get('username'),))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], data.get('password')):
            return jsonify({
                "message": "Login sukses",
                "user": {"id": user['id'], "username": user['username']}
            }), 200
        else:
            return jsonify({"error": "Username atau password salah"}), 401
    except Exception as e:
        raise e
    finally:
        conn.close()

@app.route('/api/data', methods=['GET'])
def get_data():
    table_name = request.args.get('table')
    if not table_name or not table_name.endswith('_cl'):
        return jsonify({"error": "Nama tabel invalid"}), 400
    
    conn = get_db_connection()
    if not conn: raise Exception("Gagal Konek Database")
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = f'SELECT * FROM kesehatan."{table_name}" ORDER BY tahun ASC'
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        return jsonify(rows)
    except Exception as e:
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    print("🚀 Server Backend SIAP di http://localhost:5001")
    app.run(debug=True, port=5001)