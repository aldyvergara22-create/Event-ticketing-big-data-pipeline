# 🎟️ Event Ticketing Big Data Pipeline

End-to-end backend system and data engineering pipeline for an event ticketing platform. Built with a layered architecture combining synchronous REST API transactions, asynchronous background workers, and batch analytics.

## 🏗️ System Architecture

The application is divided into specialized layers orchestrated with **Docker Compose**:

1. **Ingestion REST API (`Flask`):** Receives and validates event creation and ticket purchase requests via JSON payloads, checking ticket availability in real time.
2. **Relational Database (`PostgreSQL`):** Stores transactional data across two core tables: `events` and `purchases`.
3. **Asynchronous Task Queue (`Redis` + `Celery`):** Decouples post-purchase operations from API response times. Once Flask records a purchase, Celery processes background jobs (`app.send_ticket_email`) via Redis to simulate ticket generation and email confirmation without blocking the client.
4. **Batch Analytics Engine (`Apache Spark`):** PySpark processing job (`analytics.py`) executed on-demand via Docker Compose profiles to read sales history via JDBC and compute business intelligence metrics.

```text
[ Client / Thunder Client ] ──▶ [ Flask REST API ] ──┬──▶ [ PostgreSQL ] ──(JDBC)──▶ [ Apache Spark ] ──▶ [ Summary Tables ]
                                                     └──▶ [ Redis Broker ] ──▶ [ Celery Worker ] (Email & Ticket Simulation)
```

## 🛠️ Tech Stack

* **Backend & REST API:** Python, Flask
* **Database:** PostgreSQL
* **Task Queue & Message Broker:** Celery, Redis
* **Big Data Processing:** Apache Spark (PySpark)
* **Containerization:** Docker & Docker Compose (with service profiles)

## 🚀 Getting Started

### Prerequisites

* [Docker](https://docker.com) and [Docker Compose](https://docker.com) installed.

### 1. Start Core Services (API, DB & Workers)

Launch Flask, PostgreSQL, Redis, and the Celery worker in detached mode:

```bash
docker compose up -d
```

* **API Health Check:** Visit `http://localhost:5000` (returns `{"message": "La API de ticketing esta en marcha!"}`).
* **Simulate Purchases:** Send `POST` requests with JSON payloads using **Thunder Client**, Postman, or `curl`.
* **Monitor Background Workers:** Watch Celery process ticket confirmation emails asynchronously:
  ```bash
  docker compose logs -f celery
  ```

### 2. Run Spark Batch Analytics

Execute the PySpark analytics job on-demand using the `analytics` profile. The `--rm` flag removes the temporary Spark container once the reports are printed:

```bash
docker compose --profile analytics run --rm spark_analytics
```

## 📊 Business Metrics Computed (Spark)

The PySpark job joins the `events` and `purchases` tables via JDBC and prints two analytical reports to the console:

1. **Event Sales Performance (`REPORTE ANALÍTICO DE VENTAS POR EVENTO`):**
   * **Tickets Sold (`entradas_vendidas`):** Total count of purchases per event.
   * **Total Revenue (`ingresos_totales`):** Cumulative revenue per event, ranked from highest to lowest.
   * **Average Ticket Value (`ticket_promedio`):** Mean spend per transaction for each event.

2. **Top 10 Buyers (`TOP USUARIOS COMPRADORES`):**
   * **Purchases Made (`compras_realizadas`):** Total number of orders placed per user.
   * **Total Spend (`gasto_total`):** Cumulative amount spent per user, highlighting the top 10 highest-value customers.
