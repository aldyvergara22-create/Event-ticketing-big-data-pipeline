from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum, avg, desc


def run_analytics():
    print("Iniciando SparkSession...")

    # Creo la sesión de Spark descargando el driver JDBC de PostgreSQL
    spark = (
        SparkSession.builder.appName("EventTicketingBigDataAnalytics")
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.1")
        .getOrCreate()
    )

    # Ocultar los logs de Spark para que no se vea tanta información en la consola
    spark.sparkContext.setLogLevel("ERROR")

    # Configuración de la conexión a la base de datos PostgreSQL
    jdbc_url = "jdbc:postgresql://db:5432/ticketing"
    db_properties = {
        "user": "postgres",
        "password": "password",
        "driver": "org.postgresql.Driver",
    }

    print("Extrayendo datos desde la base de datos PostgreSQL...")

    # Leer las tablas 'events' y 'purchases' como DataFrames de Spark
    events_df = spark.read.jdbc(url=jdbc_url, table="events", properties=db_properties)
    purchases_df = spark.read.jdbc(
        url=jdbc_url, table="purchases", properties=db_properties
    )

    # Transformación y cruce de datos (JOIN)
    sales_df = purchases_df.join(
        events_df, purchases_df["event_id"] == events_df["id"], "inner"
    ).select(
        purchases_df["id"].alias("purchase_id"),
        purchases_df["user_id"],
        events_df["name"].alias("event_name"),
        purchases_df["total_paid"],
        purchases_df["purchase_date"],
    )

    # Calcular las metricas de negocio
    print("\n" + "=" * 55)
    print("REPORTE ANALÍTICO DE VENTAS POR EVENTO")
    print("=" * 55)

    metrics_df = (
        sales_df.groupBy("event_name")
        .agg(
            count("purchase_id").alias("entradas_vendidas"),
            sum("total_paid").alias("ingresos_totales"),
            avg("total_paid").alias("ticket_promedio"),
        )
        .orderBy(desc("ingresos_totales"))
    )

    # mostrar la tabla resultante en consola
    metrics_df.show(truncate=False)

    # calcular el Top de compradores
    print("\n" + "=" * 55)
    print("TOP USUARIOS COMPRADORES")
    print("=" * 55)

    top_users_df = (
        sales_df.groupBy("user_id")
        .agg(
            count("purchase_id").alias("compras_realizadas"),
            sum("total_paid").alias("gasto_total"),
        )
        .orderBy(desc("gasto_total"))
        .limit(10)
    )
    # mostrar la tabla resultante en consola
    top_users_df.show(truncate=False)

    spark.stop()
    print("Procesamiento Big Data finalizado con éxito.")


if __name__ == "__main__":
    run_analytics()
