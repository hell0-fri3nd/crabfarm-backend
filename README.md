# CrabFarm Backend

Backend server for the **CrabFarm Web Application** built with **FastAPI**.  
This service provides API endpoints for managing crab farm data and integrates with the frontend application.

---

# 📦 Requirements

Before running the project, install the required dependencies.

```bash
pip install -r requirements.txt
```

---

# ⚙️ Database Migration (Alembic)

This project uses **Alembic** for database version control and migrations.

## Create a Migration

```bash
alembic revision --autogenerate -m "Initial migration"
```

## Apply Migration

```bash
alembic upgrade 33e05a5b7d66
```

---

# 🚀 Running the Application

Start the FastAPI application using **Uvicorn**.

> ⚠️ Note: Replace the host IP with your machine's actual IP address if needed.

```bash
uvicorn App:app --reload --host 0.0.0.0 --port 4572
```

### Server Parameters

| Parameter | Description |
|----------|-------------|
| `--reload` | Automatically reloads the server when code changes |
| `--host` | Host IP address |
| `--port` | Port where the API will run |

---

# 📚 API Documentation

FastAPI automatically generates interactive API documentation.

### Swagger UI

```
http://127.0.0.1:4572/docs
```

### ReDoc

```
http://127.0.0.1:4572/redoc
```

---

# 🛠 Tech Stack

- **FastAPI** – Web framework for building APIs
- **Uvicorn** – ASGI server
- **Alembic** – Database migrations
- **Docker / Podman / Containers** – Application containerization

---

# 📂 Project Structure

```
crabfarm-backend
│
├── App
│   ├── main.py
│   ├── models
│   ├── routers
│   ├── services
│   └── database
│
├── alembic
├── requirements.txt
└── README.md
```

---

# 👨‍💻 Development Notes

- Ensure all dependencies are installed before running the server.
- Always run migrations when database models change.
- Use the interactive API docs (`/docs`) to test endpoints.

---

# 📄 License

This project is for internal development and deployment of the CrabFarm system.