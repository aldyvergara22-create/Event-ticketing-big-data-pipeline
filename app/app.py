from flask import Flask, jsonify, request
import os
import psycopg2

app = Flask(__name__)

# Configuración de la conexión a la base de datos PostgreSQL
DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("DB_NAME", "ticketing")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")


def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    return conn


# Inicialización de la base de datos
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Tabla de eventos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                price NUMERIC(10, 2) NOT NULL);
        """)

        # Tabla de compras
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                event_id INT REFERENCES events(id),
                total_paid NUMERIC(10, 2) NOT NULL,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("Base de datos y tablas inicializadas correctamente.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")


# Ejecutamos la creación de tablas al arrancar la app
init_db()


@app.route("/")
def home():
    return jsonify({"message": "La API de ticketing esta en marcha!"})


# ENDPOINT 1: VER TODOS LOS EVENTOS
@app.route("/events", methods=["GET"])
def get_events():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price FROM events;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Convertimos los resultados a una lista de diccionarios
    events_list = []
    for row in rows:
        events_list.append({"id": row[0], "name": row[1], "price": float(row[2])})
    return jsonify(events_list)


# ENDPOINT 2: CREAR UN NUEVO EVENTO
@app.route("/events", methods=["POST"])
def create_event():
    data = request.get_json()
    name = data.get("name")
    price = data.get("price")

    if not name or price is None:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (name, price) VALUES (%s, %s) RETURNING id;", (name, price)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"id": new_id, "name": name, "price": price}), 201


# ENDPOINT 3: REALIZAR UNA COMPRA DE ENTRADA
@app.route("/purchases", methods=["POST"])
def create_purchase():
    data = request.get_json()
    user_id = data.get("user_id")
    event_id = data.get("event_id")

    # validar que lleguen los datos requeridos
    if not user_id or not event_id:
        return jsonify({"error": "Faltan datos requeridos(user_id y event_id)"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Verificar si el evento existe y se obtiene su precio
        cur.execute("SELECT id, name, price FROM events WHERE id = %s;", (event_id,))
        event = cur.fetchone()

        if not event:
            cur.close()
            conn.close()
            return jsonify({"error": "El evento seleccionado no existe"}), 404

        event_name = event[1]
        event_price = event[2]

        # Insertar la compra en la tabla de compras
        cur.execute(
            "INSERT INTO purchases (user_id, event_id, total_paid) VALUES (%s, %s, %s) RETURNING id, purchase_date;",
            (user_id, event_id, event_price),
        )
        purchase_info = cur.fetchone()
        purchase_id = purchase_info[0]
        purchase_date = purchase_info[1]

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

    # Retomar la respuesta exitosa con los detalle de la compra
    return (
        jsonify(
            {
                "message": "Compra realizada con éxito",
                "purchase_id": purchase_id,
                "user_id": user_id,
                "event_id": event_id,
                "event_name": event_name,
                "total_paid": float(event_price) if event_price is not None else 0.0,
                "date": purchase_date.strftime("%Y-%m-%d %H:%M:%S"),
            }
        ),
        201,
    )


## ENDPOINT 4: VER TODAS LAS COMPRAS
@app.route("/purchases", methods=["GET"])
def get_purchases():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # consulto las compras y hago un JOIN con events para ver el nombre del evento
        cur.execute("""
            SELECT p.id, p.user_id, p.event_id, e.name AS event_name, p.total_paid, p.purchase_date
            FROM purchases p
            JOIN events e ON p.event_id = e.id
            ORDER BY p.purchase_date DESC;
            """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Convertimos los resultados a una lista de diccionarios
        purchases_list = []
        for row in rows:
            purchases_list.append(
                {
                    "purchase_id": row[0],
                    "user_id": row[1],
                    "event_id": row[2],
                    "event_name": row[3],
                    "total_paid": float(row[4]),
                    "purchase_date": str(row[5]),
                }
            )
        return jsonify(purchases_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
