# Use official minimal Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy only dependency files first to leverage cache
COPY requirements.txt ./
COPY optimizer-grandes-paradas/requirements.txt ./optimizer-requirements.txt

# Install API and optimizer dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r optimizer-requirements.txt

# Copy optimize_module from optimizer-grandes-paradas
COPY optimizer-grandes-paradas/optimize_module ./optimize_module

# Copy Files folder from optimizer-grandes-paradas
COPY optimizer-grandes-paradas/Files/ ./Files/

# Copy the rest of the application
COPY app/ ./

# Expose application port
EXPOSE 8000

# Command to start the API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 