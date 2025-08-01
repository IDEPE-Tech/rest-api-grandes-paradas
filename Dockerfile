# Usa imagem oficial mínima do Python
FROM python:3.11-slim

# Define diretório de trabalho dentro do container
WORKDIR /app

# Copia somente arquivos de dependências primeiro para aproveitar cache
COPY rest-api-grandes-paradas/requirements.txt ./

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante da aplicação
COPY rest-api-grandes-paradas/ ./

# Expõe a porta da aplicação
EXPOSE 8000

# Comando para iniciar a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 