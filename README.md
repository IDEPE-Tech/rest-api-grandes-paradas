# Grandes Paradas API

FastAPI application that provides six endpoints used by the **Grandes Paradas** project for managing maintenance calendars and optimization parameters.

The project ships with a ready-to-use **Dockerfile**, so you can build and run the service without installing Python locally.

---

## 📥 Cloning the repository

This repository uses Git submodules. When cloning, you need to include the submodules:

### First-time clone (with submodules):

```bash
# Clone repository with submodules
git clone --recurse-submodules https://github.com/IDEPE-Tech/rest-api-grandes-paradas.git
cd rest-api-grandes-paradas
```

Alternatively, if you've already cloned without submodules:

```bash
# Initialize and update submodules
git submodule update --init --recursive
```

### Updating submodules:

To update the submodules to their latest commits:

```bash
# Update all submodules to latest commits
git submodule update --remote --recursive
```

To update a specific submodule:

```bash
# Update only the optimizer-grandes-paradas submodule
git submodule update --remote optimizer-grandes-paradas
```

---

## 📦 Building the Docker image

```bash
# Clone the repository (skip if you have it already)
# git clone https://github.com/IDEPE-Tech/rest-api-grandes-paradas.git
# cd rest-api-grandes-paradas

# Build the image (the period is important)
docker build -t grandes-paradas-api .
```

* `-t grandes-paradas-api` tags the resulting image so you can reference it later.
* The build will install `uvicorn`, `fastapi`, and other dependencies listed in `requirements.txt`.

## ⬇️ Pulling container from Dockerhub
The container is also available on Dockerhub. Run this commmand to get it already prepared to run and tag it with the tag we are using in this instructions file:

```bash
docker pull idepetech/grandes-paradas:0.2.0
docker tag idepetech/grandes-paradas:0.2.0 grandes-paradas-api:latest
```

You can follow the runnning section to use the API methods.

## 🚀 Running with Docker Compose (Recommended)

The easiest way to run the application is using Docker Compose:

```bash
# Build and run in one command
docker compose up --build -d
```

* `--build` builds the image before starting
* `-d` runs the container in the background (detached mode)

After the container starts, the API will be reachable at **<http://localhost:8000>**.

### Managing the container:

```bash
# Stop the container
docker compose down

# View logs
docker compose logs -f

# Restart the container
docker compose restart
```

## 🐳 Alternative: Running with Docker directly

If you prefer to use Docker directly:

```bash
docker run -d --name grandes-paradas-api -p 8000:8000 grandes-paradas-api
```

* `-d` runs the container in the background.
* `--name` gives it an easy-to-remember name.
* `-p 8000:8000` maps the container's port **8000** (exposed by the Dockerfile) to your host.

To stop and remove the container:

```bash
docker rm -f grandes-paradas-api
```

---

## 🛣️ Available endpoints

| Method | Path                        | Description                                       |
|--------|-----------------------------|---------------------------------------------------|
| GET    | `/hello`                    | Health-check endpoint. Returns a greeting.        |
| GET    | `/ug/{ug_number}`           | Returns information for a specific UG.            |
| POST   | `/optimizer-parameters`     | Receives optimization parameters and returns acknowledgment. |
| PUT    | `/calendar/edit-maintenance`| Edits maintenance days in saved calendar.         |
| POST   | `/optimize`                 | Busy-loop for **n** seconds and returns stats.    |
| GET    | `/calendar`                 | Generates or retrieves randomized UG maintenance periods. |

### 1. Health-check: `/hello`

```bash
curl http://localhost:8000/hello
# => {"message": "hello"}
```

### 2. UG Information: `/ug/{ug_number}`

Returns detailed information for a specific generating unit (UG).

Path parameter:
* `ug_number` – integer – UG number (1-50)

Example:
```bash
curl http://localhost:8000/ug/1
# => {"ug": 1, "cf": 1, "portico": 1, "island": 1, "bladesNumber": 5, "voltage": 525, "localization": "MD", "producer": "GE"}
```

### 3. Optimization Parameters: `/optimizer-parameters`

Receives optimization parameters in JSON format and returns acknowledgment.

Request body (JSON):
```json
{
  "any_parameter": "any_value",
  "custom_field": 123
}
```

Example:
```bash
curl -X POST "http://localhost:8000/optimizer-parameters" \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "genetic", "iterations": 1000}'
# => {"status": "received", "message": "Parâmetros de otimização recebidos com sucesso. Processamento será implementado em breve."}
```

### 4. Edit Maintenance: `/calendar/edit-maintenance`

Edits maintenance days for a specific UG and maintenance type in the saved calendar.

Request body (JSON):
```json
{
  "ug": "01",
  "maintenance": "AR",
  "old_days": [10, 11, 12, 13, 14, 15],
  "new_days": [12, 13, 14, 15, 16, 17]
}
```

Example:
```bash
curl -X PUT "http://localhost:8000/calendar/edit-maintenance" \
  -H "Content-Type: application/json" \
  -d '{"ug": "01", "maintenance": "AR", "old_days": [45, 46, 47], "new_days": [50, 51, 52]}'
# => {"status": "success", "message": "Manutenção 'AR' da UG '01' editada com sucesso. Substituídos 3 dias por 3 novos dias."}
```

### 5. Performance test: `/optimize`

Query parameter:

* `n` – integer – number of seconds to keep the CPU busy.

Example (run for 5 seconds):

```bash
curl -X POST "http://localhost:8000/optimize?n=5"
# => {"n": 135372443, "elapsed_seconds": 5.000819}
```

### 6. Maintenance calendar: `/calendar`

Generates or retrieves randomized UG maintenance periods. The calendar is automatically saved to `calendario_manutencao.json`.

Query parameter:
* `generate` – boolean (default: false) – If true, generates a new calendar; if false, returns the saved calendar.

Behavior:
- `generate=false` (default): Returns the saved calendar from `calendario_manutencao.json`
- `generate=true`: Generates a new random calendar, saves it, and returns it

Each item contains:
- `ug`: string, zero-padded from "01" to "50"
- `maintenance`: string, one of the values defined in the `maintenance` list
- `days`: list of integers, continuous days in the range 1..365

Rules used to generate data (when `generate=true`):
- For each UG, 1–5 maintenance specifications are randomly selected.
- For each selected spec, 1–2 independent periods are generated.
- Each period has a continuous duration between 20 and 100 days.
- Periods may overlap across UGs or even within the same UG/spec.

Examples:

```bash
# Retrieve saved calendar
curl http://localhost:8000/calendar
# => [{"ug": "01", "maintenance": "AR", "days": [12, 13, 14, 15, 300, 301, 302]}, ...]

# Generate new calendar
curl http://localhost:8000/calendar?generate=true
# => [{"ug": "01", "maintenance": "AR", "days": [45, 46, 47, 48, 200, 201, 202]}, ...]
```

Example response snippet:

```json
[
  {"ug": "01", "maintenance": "AR", "days": [12, 13, 14, 15, 300, 301, 302]},
  {"ug": "01", "maintenance": "CM", "days": [200, 201, 202]},
  {"ug": "02", "maintenance": "TRF", "days": [50, 51, 52, 53, 172, 173, 174]}
]
```

## 📁 Calendar File Management

The API automatically manages a calendar file (`calendario_manutencao.json`) that contains:

- `generated_at`: ISO timestamp when the calendar was created
- `last_modified`: ISO timestamp when the calendar was last edited
- `total_activities`: Number of maintenance activities
- `activities`: Array of all maintenance activities

### File Operations:

1. **Generate new calendar**: `GET /calendar?generate=true`
2. **Retrieve saved calendar**: `GET /calendar`
3. **Edit maintenance days**: `PUT /calendar/edit-maintenance`

### Error Handling:

- **404**: Calendar file not found (use `generate=true` first)
- **400**: Invalid edit parameters (old days don't match current calendar)
- **500**: File system errors

---

## 🧹 Cleaning up

### Using Docker Compose:

```bash
# Stop and remove containers, networks
docker compose down

# Remove everything including volumes and images
docker compose down --rmi all --volumes --remove-orphans
```

### Using Docker directly:

```bash
# Stop and remove container
docker rm -f grandes-paradas-api

# Remove image
docker image rm grandes-paradas-api
```

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
