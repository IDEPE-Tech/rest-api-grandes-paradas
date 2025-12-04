# Usa imagem oficial mínima do Python
FROM python:3.11-slim

# Define diretório de trabalho dentro do container
WORKDIR /app

# Copia somente arquivos de dependências primeiro para aproveitar cache
COPY requirements.txt ./
COPY optimizer-grandes-paradas/requirements.txt ./optimizer-requirements.txt

# Instala dependências da API e do optimizer
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r optimizer-requirements.txt

# Copia o diretório optimizer-grandes-paradas
COPY optimizer-grandes-paradas/ ./optimizer-grandes-paradas/

# Copia o restante da aplicação
COPY app/ ./

# Expõe a porta da aplicação
EXPOSE 8000

# Comando para iniciar a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 