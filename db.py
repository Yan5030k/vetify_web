import sqlite3
from werkzeug.security import generate_password_hash # Necesario para crear el admin seguro

DB_NAME = "vetify_web.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Tabla Usuarios (NUEVA)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        rol TEXT NOT NULL DEFAULT 'secretaria'
    );
    """)

    # Dueños
    cur.execute("""
    CREATE TABLE IF NOT EXISTS duenos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT NOT NULL,
        correo TEXT NOT NULL
    );
    """)

    # Mascotas
    cur.execute("""
    CREATE TABLE IF NOT EXISTS mascotas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo TEXT NOT NULL,
        raza TEXT,
        edad INTEGER,
        peso REAL,
        dueno_id INTEGER NOT NULL,
        fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dueno_id) REFERENCES duenos(id)
    );
    """)

    # Veterinarios
    cur.execute("""
    CREATE TABLE IF NOT EXISTS veterinarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        especialidad TEXT NOT NULL,
        telefono TEXT NOT NULL
    );
    """)

    # Citas
    cur.execute("""
    CREATE TABLE IF NOT EXISTS citas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mascota_id INTEGER NOT NULL,
        vet_id INTEGER NOT NULL,
        fecha_hora TEXT NOT NULL,
        tipo_servicio TEXT NOT NULL,
        sintomas TEXT,
        urgencia TEXT,
        estado TEXT NOT NULL DEFAULT 'pendiente',
        FOREIGN KEY (mascota_id) REFERENCES mascotas(id),
        FOREIGN KEY (vet_id) REFERENCES veterinarios(id)
    );
    """)
    
    conn.commit()

    # --- BLOQUE DE MIGRACIÓN DE MASCOTAS (IGUAL QUE ANTES) ---
    try:
        cur.execute("PRAGMA table_info(mascotas)")
        columnas = [col[1] for col in cur.fetchall()]

        if "fecha_registro" not in columnas:
            print(" Actualizando estructura de BD (Mascotas)...")
            cur.execute("ALTER TABLE mascotas ADD COLUMN fecha_registro TEXT")
            cur.execute("UPDATE mascotas SET fecha_registro = datetime('now', 'localtime') WHERE fecha_registro IS NULL")
            conn.commit()
            print(" Columna 'fecha_registro' agregada.")
    except Exception as e:
        print(f"Nota sobre migración: {e}")
    # -------------------------------------

    conn.close()


def seed_veterinarios():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='veterinarios';")
    if cur.fetchone():
        cur.execute("SELECT COUNT(*) AS c FROM veterinarios;")
        c = cur.fetchone()["c"]
        if c == 0:
            vets = [
                ("Dr. Pérez", "Perros", "7777-0001"),
                ("Dra. López", "Gatos", "7777-0002"),
                ("Dr. Martínez", "Aves", "7777-0003"),
                ("Dra. Rivera", "General", "7777-0004"),
            ]
            cur.executemany(
                "INSERT INTO veterinarios (nombre, especialidad, telefono) VALUES (?, ?, ?);",
                vets
            )
            conn.commit()
    conn.close()

# --- NUEVA FUNCIÓN: Crear Admin por defecto ---
def seed_admin():
    conn = get_connection()
    cur = conn.cursor()
    
    # Verificar si ya existe algún usuario
    cur.execute("SELECT COUNT(*) AS c FROM usuarios;")
    c = cur.fetchone()["c"]
    
    if c == 0:
        print(" Creando usuario administrador por defecto...")
        # Creamos usuario 'admin' con contraseña 'admin123' (encriptada)
        password_hash = generate_password_hash("admin123")
        cur.execute(
            "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?);",
            ("admin", password_hash, "admin")
        )
        conn.commit()
        print(" Usuario 'admin' creado. Contraseña: 'admin123'")
    
    conn.close()