import sqlite3

DB_NAME = "vetify_web.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # acceder por nombre de columna
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Dueños
    cur.execute("""
    CREATE TABLE IF NOT EXISTS duenos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT NOT NULL,
        correo TEXT NOT NULL
    );
    """)

    # Mascotas (Para nuevas instalaciones sí dejamos el DEFAULT)
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

    # --- BLOQUE DE MIGRACIÓN CORREGIDO ---
    try:
        cur.execute("PRAGMA table_info(mascotas)")
        columnas = [col[1] for col in cur.fetchall()]

        if "fecha_registro" not in columnas:
            print("⚠️ Actualizando estructura de BD (sin borrar datos)...")
            
            # Paso 1: Agregar columna SIN default dinámico (para evitar el error de SQLite)
            cur.execute("ALTER TABLE mascotas ADD COLUMN fecha_registro TEXT")
            
            # Paso 2: Llenar las filas existentes con la fecha actual
            cur.execute("UPDATE mascotas SET fecha_registro = datetime('now', 'localtime') WHERE fecha_registro IS NULL")
            
            conn.commit()
            print("✅ Columna 'fecha_registro' agregada y datos actualizados.")
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