# Grandes Paradas API

FastAPI application that provides three simple endpoints used by the **Grandes Paradas** project.

The project ships with a ready-to-use **Dockerfile**, so you can build and run the service without installing Python locally.

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
docker pull idepetech/grandes-paradas:0.1.0
docker tag idepetech/grandes-paradas:0.1.0 grandes-paradas-api:latest
```

You can follow the runnning section to use the API methods.

## 🚀 Running the container

```bash
docker run -d --name grandes-paradas-api -p 8000:8000 grandes-paradas-api
```

* `-d` runs the container in the background.
* `--name` gives it an easy-to-remember name.
* `-p 8000:8000` maps the container’s port **8000** (exposed by the Dockerfile) to your host.

After the container starts, the API will be reachable at **<http://localhost:8000>**.

To stop and remove the container:

```bash
docker rm -f grandes-paradas-api
```

---

## 🛣️ Available endpoints

| Method | Path          | Description                                       |
|--------|---------------|---------------------------------------------------|
| GET    | `/hello`      | Health-check endpoint. Returns a greeting.        |
| POST   | `/optimize`   | Busy-loop for **n** seconds and returns stats.    |
| GET    | `/calendar`   | Generates randomized UG maintenance periods.      |

### 1. Health-check: `/hello`

```bash
curl http://localhost:8000/hello
# => {"message": "hello"}
```

### 2. Performance test: `/optimize`

Query parameter:

* `n` – integer – number of seconds to keep the CPU busy.

Example (run for 5 seconds):

```bash
curl -X POST "http://localhost:8000/optimize?n=5"
# => {"n": 135372443, "elapsed_seconds": 5.000819}
```

### 3. Maintenance calendar: `/calendar`

Returns a JSON list of maintenance periods. Each item contains:

- `ug`: string, zero-padded from "01" to "50"
- `maintenance`: string, one of the values defined in the `maintenance` list
- `days`: list of integers, continuous days in the range 1..365

Rules used to generate data:

- For each UG, 1–5 maintenance specifications are randomly selected.
- For each selected spec, 1–2 independent periods are generated.
- Each period has a continuous duration between 20 and 100 days.
- Periods may overlap across UGs or even within the same UG/spec.

Example response snippet:

```json
[
  {"ug": "01", "maintenance": "AR", "days": [12, 13, 14, 15, 300, 301, 302]},
  {"ug": "01", "maintenance": "CM", "days": [200, 201, 202]},
  {"ug": "02", "maintenance": "TRF", "days": [50, 51, 52, 53, 172, 173, 174]}
]
```

---

## 🧹 Cleaning up

If you no longer need the image:

```bash
docker image rm grandes-paradas-api
```

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
