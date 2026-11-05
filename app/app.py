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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                price NUMERIC(10, 2) NOT NULL);
        """)
        conn.commit()
        cursor.close()
        conn.close()
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
