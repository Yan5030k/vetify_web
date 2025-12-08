import sqlite3

conn = sqlite3.connect("vetify_web.db")
cur = conn.cursor()

try:
    # Agregamos la columna a la tabla existente
    cur.execute("ALTER TABLE mascotas ADD COLUMN fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP")
    conn.commit()
    print("¡Columna agregada con éxito!")
except sqlite3.OperationalError as e:
    print("Nota:", e) # Probablemente dirá que la columna ya existe si lo corres dos veces

conn.close()