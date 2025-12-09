from datetime import datetime
from functools import wraps  # IMPORTANTE: Para el decorador

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session
)
from werkzeug.security import check_password_hash, generate_password_hash

# Importamos las funciones de DB y Services
from db import init_db, seed_veterinarios, seed_admin
from services import (
    crear_dueno,
    crear_mascota,
    listar_mascotas,
    listar_veterinarios,
    crear_cita,
    listar_citas_hoy,
    listar_citas_todas,
    listar_pacientes_detalle,
    contar_mascotas,
    contar_duenos,
    contar_citas_hoy,
    contar_citas_urgencia_hoy,
    analizar_urgencia,
    existe_cita_en_horario,
    obtener_cita_por_id,
    obtener_cita_cruda,
    actualizar_cita,
    eliminar_cita,
    obtener_usuario_por_username # Nueva función importada
)

app = Flask(__name__)
app.secret_key = "vetify-secret-key"

# Inicialización
init_db()
seed_veterinarios()
seed_admin() # Creamos el admin si no existe

# --- DECORADOR PARA PROTEGER RUTAS ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Debes iniciar sesión para acceder.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# --- RUTAS DE AUTENTICACIÓN ---

@app.route("/login", methods=["GET", "POST"])
def login():
    # Si ya está logueado, mandar al inicio
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = obtener_usuario_por_username(username)

        # Verificamos si el usuario existe y si la contraseña coincide con el hash
        if user and check_password_hash(user['password'], password):
            # Login exitoso
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['rol'] = user['rol']
            flash(f"Bienvenido, {user['username']}.", "success")
            return redirect(url_for('index'))
        else:
            flash("Usuario o contraseña incorrectos.", "error")
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for('login'))


# --- RUTAS DE LA APLICACIÓN (Ahora protegidas) ---

@app.route("/")
@login_required  # <--- Agregamos esto a todas las rutas protegidas
def index():
    total_mascotas = contar_mascotas()
    total_duenos = contar_duenos()
    total_citas_hoy = contar_citas_hoy()
    urgencias = contar_citas_urgencia_hoy()
    urg_altas = urgencias.get("alta", 0)

    return render_template(
        "index.html",
        total_mascotas=total_mascotas,
        total_duenos=total_duenos,
        total_citas_hoy=total_citas_hoy,
        urg_altas=urg_altas
    )


@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if request.method == "POST":
        owner_name = request.form.get("owner_name", "").strip()
        owner_phone = request.form.get("owner_phone", "").strip()
        owner_email = request.form.get("owner_email", "").strip()
        pet_name = request.form.get("pet_name", "").strip()
        pet_type = request.form.get("pet_type", "").strip() or "Otro"
        pet_breed = request.form.get("pet_breed", "").strip()
        pet_age_str = request.form.get("pet_age", "").strip() or "0"
        pet_weight_str = request.form.get("pet_weight", "").strip() or "0"

        if not owner_name or not owner_phone or not owner_email or not pet_name:
            flash("Por favor completa todos los campos obligatorios.", "error")
            return redirect(url_for("register"))

        try:
            pet_age = int(pet_age_str)
            pet_weight = float(pet_weight_str)
        except ValueError:
            flash("Revisa la edad y el peso de la mascota.", "error")
            return redirect(url_for("register"))

        dueno_id = crear_dueno(owner_name, owner_phone, owner_email)
        crear_mascota(pet_name, pet_type, pet_breed, pet_age, pet_weight, dueno_id)

        flash(f"Paciente {pet_name} registrado correctamente.", "success")
        return redirect(url_for("citas"))

    return render_template("register.html")


@app.route("/appointment", methods=["GET", "POST"])
@login_required
def appointment():
    mascotas = listar_mascotas()
    vets = listar_veterinarios()

    if not mascotas:
        flash("Primero registra un paciente.", "error")
        return redirect(url_for("register"))
    if not vets:
        flash("No hay veterinarios registrados.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        mascota_id = request.form.get("mascota_id")
        vet_id = request.form.get("vet_id")
        tipo_servicio = request.form.get("tipo_servicio", "Consulta")
        sintomas = request.form.get("sintomas", "")
        fecha_str = request.form.get("fecha_cita", "").strip()
        hora_str = request.form.get("hora_cita", "").strip()

        try:
            mascota_id = int(mascota_id)
            vet_id = int(vet_id)
        except (TypeError, ValueError):
            flash("Selecciona una mascota y un veterinario válidos.", "error")
            return redirect(url_for("appointment"))

        if not fecha_str or not hora_str:
            flash("Indica la fecha y la hora de la cita.", "error")
            return redirect(url_for("appointment"))

        try:
            fecha_hora = datetime.fromisoformat(f"{fecha_str}T{hora_str}")
        except ValueError:
            flash("Formato de fecha u hora no válido.", "error")
            return redirect(url_for("appointment"))

        if existe_cita_en_horario(vet_id, fecha_hora):
            flash("El profesional seleccionado ya tiene una cita en esa fecha y hora.", "error")
            return redirect(url_for("appointment"))

        urgencia = analizar_urgencia(sintomas)
        crear_cita(mascota_id, vet_id, fecha_hora, tipo_servicio, sintomas, urgencia)

        flash(f"Cita creada para el {fecha_str} a las {hora_str}. Urgencia: {urgencia.upper()}.", "success")
        return redirect(url_for("citas"))

    return render_template("appointment.html", mascotas=mascotas, vets=vets)


@app.route("/agenda")
@login_required
def agenda():
    citas = listar_citas_hoy()
    total_mascotas = contar_mascotas()
    total_citas_hoy = contar_citas_hoy()
    urgencias = contar_citas_urgencia_hoy()
    urg_altas = urgencias.get("alta", 0)

    return render_template(
        "agenda.html",
        citas=citas,
        total_mascotas=total_mascotas,
        total_citas_hoy=total_citas_hoy,
        urg_altas=urg_altas
    )


@app.route("/citas")
@login_required
def citas():
    urgencia_filtro = request.args.get("urg", "todas").lower()
    citas = listar_citas_todas()

    counts = {"alta": 0, "media": 0, "baja": 0}
    for c in citas:
        urg = (c["urgencia"] or "").lower()
        if urg in counts:
            counts[urg] += 1

    if urgencia_filtro in ("alta", "media", "baja"):
        citas_filtradas = [c for c in citas if (c["urgencia"] or "").lower() == urgencia_filtro]
    else:
        citas_filtradas = citas

    total_citas = len(citas_filtradas)
    grupos = []
    current_date = None
    grupo_actual = None
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    for c in citas_filtradas:
        fecha_iso = c["fecha_hora"][:10]
        if fecha_iso != current_date:
            current_date = fecha_iso
            dt = datetime.fromisoformat(fecha_iso)
            dia_nombre = dias_semana[dt.weekday()]
            fecha_label = f"{dia_nombre} {dt.day:02d}/{dt.month:02d}/{dt.year}"
            grupo_actual = {"fecha_iso": fecha_iso, "fecha_label": fecha_label, "items": []}
            grupos.append(grupo_actual)
        grupo_actual["items"].append(c)

    return render_template(
        "citas.html",
        grupos=grupos,
        total_citas=total_citas,
        counts=counts,
        urgencia_actual=urgencia_filtro
    )


@app.route("/cita/<int:cita_id>")
@login_required
def cita_detalle(cita_id: int):
    cita = obtener_cita_por_id(cita_id)
    if not cita:
        flash("La cita seleccionada no existe.", "error")
        return redirect(url_for("citas"))
    return render_template("cita_detalle.html", cita=cita)


@app.route("/cita/<int:cita_id>/editar", methods=["GET", "POST"])
@login_required
def cita_editar(cita_id: int):
    cita = obtener_cita_cruda(cita_id)
    if not cita:
        flash("La cita seleccionada no existe.", "error")
        return redirect(url_for("citas"))

    mascotas = listar_mascotas()
    vets = listar_veterinarios()

    if request.method == "POST":
        mascota_id = request.form.get("mascota_id")
        vet_id = request.form.get("vet_id")
        tipo_servicio = request.form.get("tipo_servicio", "Consulta")
        sintomas = request.form.get("sintomas", "")
        fecha_str = request.form.get("fecha_cita", "").strip()
        hora_str = request.form.get("hora_cita", "").strip()

        try:
            mascota_id = int(mascota_id)
            vet_id = int(vet_id)
        except (TypeError, ValueError):
            flash("Datos inválidos.", "error")
            return redirect(url_for("cita_editar", cita_id=cita_id))

        fecha_hora = datetime.fromisoformat(f"{fecha_str}T{hora_str}")

        if existe_cita_en_horario(vet_id, fecha_hora, excluir_id=cita_id):
            flash("El horario ya está ocupado.", "error")
            return redirect(url_for("cita_editar", cita_id=cita_id))

        urgencia = analizar_urgencia(sintomas)
        actualizar_cita(cita_id, mascota_id, vet_id, fecha_hora, tipo_servicio, sintomas, urgencia)

        flash("Cita actualizada correctamente.", "success")
        return redirect(url_for("cita_detalle", cita_id=cita_id))

    dt = datetime.fromisoformat(cita["fecha_hora"])
    fecha_cita = dt.date().isoformat()
    hora_cita = dt.time().strftime("%H:%M")

    return render_template("cita_editar.html", cita=cita, mascotas=mascotas, vets=vets, fecha_cita=fecha_cita, hora_cita=hora_cita)


@app.route("/cita/<int:cita_id>/eliminar", methods=["POST"])
@login_required
def cita_eliminar(cita_id: int):
    eliminar_cita(cita_id)
    flash("Cita eliminada correctamente.", "success")
    return redirect(url_for("citas"))


@app.route("/pacientes")
@login_required
def pacientes():
    pacientes = listar_pacientes_detalle()
    total = len(pacientes)
    return render_template("pacientes.html", pacientes=pacientes, total=total)


@app.route("/vets")
@login_required
def vets():
    veterinarios = listar_veterinarios()
    return render_template("vets.html", veterinarios=veterinarios)


if __name__ == "__main__":
    app.run(debug=True)