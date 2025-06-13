Hotel Booking Platform – Milestone 2

Overview:
A Dockerized hotel booking web app supporting MariaDB (SQL) and MongoDB (NoSQL). Features customer login, room booking, full/installment payment, analytics report, and one-click migration from SQL to NoSQL.

Quick Start:

Install Docker & Docker Compose.

Clone the project and navigate to the directory.

Start all services:

docker-compose up --build
Access in browser:

App: http://localhost:5000

Adminer: http://localhost:8080 (MariaDB)

Mongo Express: http://localhost:8081 (MongoDB)

Database Setup & Data Import:

MariaDB is seeded automatically on first run.

To generate demo data: use “Import Random Data” button or run:

    python mariadb_seeder.py

NoSQL Migration:
    Migrate data with “Migrate to MongoDB” in the web UI or run:

    python migrate_sql_to_nosql.py

The backend uses MongoDB after migration.

Analytics Report:

Access via “Analytics Report” in the app.

Filter bookings by date, see hotel-level stats (customers, bookings, rooms, revenue, average value).

Project Structure:

app.py – Main backend

mariadb_seeder.py – Seed MariaDB with random data

migrate_sql_to_nosql.py – SQL→Mongo migration

create_indexes.py – Add MongoDB indexes

analyze_pipeline_stats.py – Analyze MongoDB query stats

templates/ – Frontend HTML

docker-compose.yml, Dockerfile, requirements.txt

Author:
Shogofa Nawrozy