# Grandes Paradas API

FastAPI application that provides eight endpoints used by the **Grandes Paradas** project for managing maintenance calendars and optimization parameters. All endpoints require a `user` parameter to identify the requester and maintain isolated data per user.

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
| POST   | `/optimize/set-parameters`   | Sets optimization parameters and saves to database. |
| GET    | `/optimize/get-parameters`  | Gets current optimization parameters for the user. |
| PUT    | `/calendar/edit-maintenance`| Edits maintenance days in saved calendar.         |
| POST   | `/optimize`                 | Starts optimization in background and returns immediately. |
| GET    | `/optimize/get-status`     | Gets the current status and progress of the optimization. |
| GET    | `/calendar`                 | Generates or retrieves randomized UG maintenance periods. |

**Note:** All endpoints require a `user` query parameter to identify the requester. Each user has isolated data (calendars and optimizer parameters).

### 1. Health-check: `/hello`

Query parameter:
* `user` – string (required) – User identifier

Example:
```bash
curl "http://localhost:8000/hello?user=lucas"
# => {"message": "hello"}
```

### 2. UG Information: `/ug/{ug_number}`

Returns detailed information for a specific generating unit (UG).

Path parameter:
* `ug_number` – integer – UG number (1-50)

Query parameter:
* `user` – string (required) – User identifier

Example:
```bash
curl "http://localhost:8000/ug/1?user=lucas"
# => {"ug": 1, "cf": 1, "portico": 1, "island": 1, "bladesNumber": 5, "voltage": 525, "localization": "MD", "producer": "GE"}
```

### 3. Set Optimization Parameters: `/optimize/set-parameters`

Sets optimization parameters in JSON format and saves to database.

Query parameter:
* `user` – string (required) – User identifier

Request body (JSON):
```json
{
  "method": "AG",
  "mode": "time",
  "n_pop": 50,
  "n_gen": null,
  "n_ants": 30,
  "n_iter": null,
  "time": 1800
}
```

Parameters:
* `method` – string (required) – "AG" (Genetic Algorithm) or "ACO" (Ant Colony Optimization)
* `mode` – string (required) – "params" (by parameters) or "time" (by time limit)
* `n_pop` – integer (optional, required for AG) – Population size
* `n_gen` – integer (optional, required for AG + params mode) – Number of generations
* `n_ants` – integer (optional, required for ACO) – Number of ants
* `n_iter` – integer (optional, required for ACO + params mode) – Number of iterations
* `time` – integer (optional, required for time mode) – Time limit in seconds

Example:
```bash
curl -X POST "http://localhost:8000/optimize/set-parameters?user=lucas" \
  -H "Content-Type: application/json" \
  -d '{"method": "AG", "mode": "time", "n_pop": 50, "time": 1800}'
# => {"status": "success", "message": "Optimization parameters saved successfully to database."}
```

### 4. Get Optimization Parameters: `/optimize/get-parameters`

Gets the current optimization parameters for a specific user.

Query parameter:
* `user` – string (required) – User identifier

Example:
```bash
curl "http://localhost:8000/optimize/get-parameters?user=lucas"
# => {"method": "AG", "mode": "time", "n_pop": 50, "n_gen": null, "n_ants": 30, "n_iter": null, "time": 1800}
```

### 5. Edit Maintenance: `/calendar/edit-maintenance`

Edits maintenance days for a specific UG and maintenance type in the saved calendar.

Query parameter:
* `user` – string (required) – User identifier

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
curl -X PUT "http://localhost:8000/calendar/edit-maintenance?user=lucas" \
  -H "Content-Type: application/json" \
  -d '{"ug": "01", "maintenance": "AR", "old_days": [45, 46, 47], "new_days": [50, 51, 52]}'
# => {"status": "success", "message": "Manutenção 'AR' da UG '01' editada com sucesso. Substituídos 3 dias por 3 novos dias."}
```

### 6. Start Optimization: `/optimize`

Starts the optimization process in background and returns immediately. The optimization runs asynchronously using the parameters set via `/optimize/set-parameters`.

Query parameter:
* `user` – string (required) – User identifier

**Note:** If the user already has an optimization running, it will be cancelled and replaced by the new one.

Example:
```bash
curl -X POST "http://localhost:8000/optimize?user=lucas"
# => {"status": "started", "message": "Optimization started. Use /optimize/get-status to check progress."}
```

### 7. Get Optimization Status: `/optimize/get-status`

Gets the current status and progress of the optimization process.

Query parameter:
* `user` – string (required) – User identifier

Response:
* `status` – string – "running", "completed", "error", or "not_found"
* `elapsed_seconds` – float – Elapsed time in seconds
* `time` – integer or null – Total time limit in seconds
* `progress_percentage` – float or null – Progress percentage (0-100)

Example:
```bash
curl "http://localhost:8000/optimize/get-status?user=lucas"
# => {"status": "running", "elapsed_seconds": 45.2, "time": 1800, "progress_percentage": 2.51}
```

### 8. Maintenance calendar: `/calendar`

Generates or retrieves randomized UG maintenance periods. The calendar is automatically saved to the database.

Query parameters:
* `generate` – boolean (default: false) – If true, generates a new calendar; if false, returns the saved calendar.
* `user` – string (required) – User identifier

Behavior:
- `generate=false` (default): Returns the saved calendar from database for the user
- `generate=true`: Generates a new random calendar, saves it to database, and returns it

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
curl "http://localhost:8000/calendar?user=lucas"
# => [{"ug": "01", "maintenance": "AR", "days": [12, 13, 14, 15, 300, 301, 302]}, ...]

# Generate new calendar
curl "http://localhost:8000/calendar?generate=true&user=lucas"
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

## 📁 Calendar and User Data Management

The API automatically manages calendars and optimizer parameters in a PostgreSQL database. Each user has isolated data:

- **Calendars**: Each user has their own calendar with maintenance activities
- **Optimizer Parameters**: Each user has their own optimizer configuration
- **Default User**: A "default" user is created automatically with default values
- **User Initialization**: When a new user makes their first request, their data is automatically copied from the default user

### Database Operations:

1. **Generate new calendar**: `GET /calendar?generate=true&user=<user_id>`
2. **Retrieve saved calendar**: `GET /calendar?user=<user_id>`
3. **Edit maintenance days**: `PUT /calendar/edit-maintenance?user=<user_id>`
4. **Set optimizer parameters**: `POST /optimize/set-parameters?user=<user_id>`
5. **Get optimizer parameters**: `GET /optimize/get-parameters?user=<user_id>`

### Error Handling:

- **404**: Calendar not found for user (use `generate=true` first)
- **400**: Invalid parameters (validation errors)
- **500**: Database or server errors

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
