from datetime import datetime
from typing import Dict
from db import get_connection


# --------- Dueños ---------

def crear_dueno(nombre: str, telefono: str, correo: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO duenos (nombre, telefono, correo) VALUES (?, ?, ?);",
        (nombre, telefono, correo)
    )
    conn.commit()
    dueno_id = cur.lastrowid
    conn.close()
    return dueno_id


def contar_duenos() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM duenos;")
    c = cur.fetchone()["c"]
    conn.close()
    return int(c or 0)


# --------- Mascotas ---------

def crear_mascota(
    nombre: str,
    tipo: str,
    raza: str,
    edad: int,
    peso: float,
    dueno_id: int
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    
    # MODIFICADO: Calculamos la fecha en Python y la enviamos explícitamente
    # Esto asegura que se guarde la fecha aunque la BD no tenga el DEFAULT configurado tras la migración.
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute(
        """INSERT INTO mascotas (nombre, tipo, raza, edad, peso, dueno_id, fecha_registro)
           VALUES (?, ?, ?, ?, ?, ?, ?);""",
        (nombre, tipo, raza, edad, peso, dueno_id, fecha_actual)
    )
    conn.commit()
    mascota_id = cur.lastrowid
    conn.close()
    return mascota_id


def listar_mascotas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.id, m.nombre, m.tipo, d.nombre AS dueno
        FROM mascotas m
        JOIN duenos d ON m.dueno_id = d.id
        ORDER BY m.nombre;
    """)
    filas = cur.fetchall()
    conn.close()
    return filas


def listar_pacientes_detalle():
    """
    Lista todos los pacientes con toda su información y la del responsable.
    """
    conn = get_connection()
    cur = conn.cursor()
    # Incluimos fecha_registro en la consulta
    cur.execute("""
        SELECT m.id,
               m.nombre,
               m.tipo,
               m.raza,
               m.edad,
               m.peso,
               m.fecha_registro,
               d.nombre   AS dueno,
               d.telefono AS dueno_telefono,
               d.correo   AS dueno_correo
        FROM mascotas m
        JOIN duenos d ON m.dueno_id = d.id
        ORDER BY m.nombre;
    """)
    filas = cur.fetchall()
    conn.close()
    return filas


def contar_mascotas() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM mascotas;")
    c = cur.fetchone()["c"]
    conn.close()
    return int(c or 0)


# --------- Veterinarios ---------

def listar_veterinarios():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre, especialidad, telefono
        FROM veterinarios
        ORDER BY nombre;
    """)
    filas = cur.fetchall()
    conn.close()
    return filas


# --------- Citas ---------

def crear_cita(
    mascota_id: int,
    vet_id: int,
    fecha_hora: datetime,
    tipo_servicio: str,
    sintomas: str,
    urgencia: str
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO citas 
           (mascota_id, vet_id, fecha_hora, tipo_servicio, sintomas, urgencia, estado)
           VALUES (?, ?, ?, ?, ?, ?, 'pendiente');""",
        (mascota_id, vet_id, fecha_hora.isoformat(), tipo_servicio, sintomas, urgencia)
    )
    conn.commit()
    cita_id = cur.lastrowid
    conn.close()
    return cita_id


def listar_citas_hoy():
    hoy = datetime.now().date().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id,
               c.fecha_hora,
               c.tipo_servicio,
               c.urgencia,
               c.sintomas,
               m.nombre AS mascota,
               d.nombre AS dueno,
               v.nombre AS vet
        FROM citas c
        JOIN mascotas m ON c.mascota_id = m.id
        JOIN duenos d   ON m.dueno_id = d.id
        JOIN veterinarios v ON c.vet_id = v.id
        WHERE date(c.fecha_hora) = ?
        ORDER BY c.fecha_hora;
    """, (hoy,))
    filas = cur.fetchall()
    conn.close()
    return filas


def listar_citas_todas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id,
               c.fecha_hora,
               c.tipo_servicio,
               c.urgencia,
               c.sintomas,
               c.estado,
               m.nombre      AS mascota,
               m.tipo        AS tipo_mascota,
               d.nombre      AS dueno,
               v.nombre      AS vet,
               c.mascota_id  AS mascota_id,
               c.vet_id      AS vet_id
        FROM citas c
        JOIN mascotas m ON c.mascota_id = m.id
        JOIN duenos d   ON m.dueno_id = d.id
        JOIN veterinarios v ON c.vet_id = v.id
        ORDER BY c.fecha_hora;
    """)
    filas = cur.fetchall()
    conn.close()
    return filas


def obtener_cita_por_id(cita_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id,
               c.fecha_hora,
               c.tipo_servicio,
               c.urgencia,
               c.sintomas,
               c.estado,
               m.nombre AS mascota,
               m.tipo   AS tipo_mascota,
               d.nombre AS dueno,
               d.telefono AS dueno_telefono,
               d.correo   AS dueno_correo,
               v.nombre   AS vet,
               v.especialidad AS vet_especialidad,
               v.telefono     AS vet_telefono
        FROM citas c
        JOIN mascotas m ON c.mascota_id = m.id
        JOIN duenos d   ON m.dueno_id = d.id
        JOIN veterinarios v ON c.vet_id = v.id
        WHERE c.id = ?;
    """, (cita_id,))
    fila = cur.fetchone()
    conn.close()
    return fila


def obtener_cita_cruda(cita_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id,
               mascota_id,
               vet_id,
               fecha_hora,
               tipo_servicio,
               sintomas,
               urgencia,
               estado
        FROM citas
        WHERE id = ?;
    """, (cita_id,))
    fila = cur.fetchone()
    conn.close()
    return fila


def actualizar_cita(
    cita_id: int,
    mascota_id: int,
    vet_id: int,
    fecha_hora: datetime,
    tipo_servicio: str,
    sintomas: str,
    urgencia: str
) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE citas
        SET mascota_id = ?,
            vet_id = ?,
            fecha_hora = ?,
            tipo_servicio = ?,
            sintomas = ?,
            urgencia = ?
        WHERE id = ?;
    """, (mascota_id, vet_id, fecha_hora.isoformat(), tipo_servicio, sintomas, urgencia, cita_id))
    conn.commit()
    conn.close()


def eliminar_cita(cita_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM citas WHERE id = ?;", (cita_id,))
    conn.commit()
    conn.close()


def contar_citas_hoy() -> int:
    hoy = datetime.now().date().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM citas WHERE date(fecha_hora) = ?;", (hoy,))
    c = cur.fetchone()["c"]
    conn.close()
    return int(c or 0)


def contar_citas_urgencia_hoy() -> Dict[str, int]:
    hoy = datetime.now().date().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(urgencia, ''), COUNT(*) AS c
        FROM citas
        WHERE date(fecha_hora) = ?
        GROUP BY urgencia;
    """, (hoy,))
    filas = cur.fetchall()
    conn.close()
    return {row[0] or "": int(row[1]) for row in filas}


def existe_cita_en_horario(vet_id: int, fecha_hora: datetime, excluir_id: int | None = None) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    if excluir_id is None:
        cur.execute("""
            SELECT COUNT(*) AS c
            FROM citas
            WHERE vet_id = ? AND fecha_hora = ?;
        """, (vet_id, fecha_hora.isoformat()))
    else:
        cur.execute("""
            SELECT COUNT(*) AS c
            FROM citas
            WHERE vet_id = ? AND fecha_hora = ? AND id != ?;
        """, (vet_id, fecha_hora.isoformat(), excluir_id))
    c = cur.fetchone()["c"]
    conn.close()
    return bool(c and c > 0)


# --------- Lógica de urgencia ---------

def analizar_urgencia(sintomas: str) -> str:
    texto = (sintomas or "").lower()
    palabras_alta = [
        "sangra", "sangrado", "hemorragia",
        "no respira", "dificultad para respirar", "ahogando",
        "convulsiona", "convulsión", "convulsiones",
        "muy débil", "muy debil",
        "no se mueve", "inconsciente" 
    ]
    for p in palabras_alta:
        if p in texto:
            return "alta"

    if "herida" in texto or "puntos" in texto or "sutura" in texto or "post operatorio" in texto or "post-operatorio" in texto:
        if "sangra" in texto or "sangrado" in texto or "hemorragia" in texto:
            return "alta"
        if "abrió" in texto or "abrio" in texto or "abierta" in texto or "abierto" in texto or "se le abrió" in texto:
            return "media"
        return "media"

    palabras_media = [
        "no quiere jugar", "triste", "no bebe",
        "apatía", "apatico", "apática",
        "diarrea", "tos", "cojea", "cojera",
        "dolor", "molestia", "no apoya la pata"
    ]
    for p in palabras_media:
        if p in texto:
            return "media"

    return "baja"


# ... (imports existentes)
# Añade este import si no lo tienes, aunque solo usaremos SQL aquí
from db import get_connection 

# ... (Resto del código de services.py igual que antes...)

# --------- USUARIOS Y AUTENTICACIÓN (NUEVO) ---------

def obtener_usuario_por_username(username: str):
    """
    Busca un usuario en la BD por su nombre de usuario.
    Devuelve la fila completa (incluyendo password hasheado) o None.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    return user

def crear_usuario(username, password_hash, rol="secretaria"):
    """
    Función útil por si en el futuro quieres crear más usuarios desde la web.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
            (username, password_hash, rol)
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()