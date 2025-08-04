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
| GET    | `/calendar`   | Generates a 50×365 maintenance calendar matrix.   |

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

Returns a 50×365 matrix (list of lists) in which **1** indicates that the generating unit (GU) is under maintenance on that day.

```bash
curl http://localhost:8000/calendar | jq
# => {
#      "calendar": [[0, 1, 1, 0, ...], ...]
#    }
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
