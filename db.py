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
    conn.close()


def seed_veterinarios():
    conn = get_connection()
    cur = conn.cursor()

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
