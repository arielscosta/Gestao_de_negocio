# 1. Imagem base: usamos uma versão leve (slim) do Python
FROM python:3.10-slim

# 2. Define o diretório de trabalho dentro do container
WORKDIR /app

# 3. Copia todos os arquivos do seu projeto para dentro do container
# O primeiro '.' é a sua pasta local, o segundo '.' é a pasta /app no container
COPY . .

# 4. Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Comando que será executado quando o container subir
CMD ["python", "main.py"]