# 1. Imagem base: usamos uma versão leve (slim) do Python
FROM python:3.10-slim

# 2. Define o diretório de trabalho dentro do container
WORKDIR /app

# 3. Copia todos os arquivos do seu projeto para dentro do container
# O primeiro '.' é a sua pasta local, o segundo '.' é a pasta /app no container
COPY . .

# 4. (Opcional) Se tivéssemos dependências externas, usaríamos:
# RUN pip install -r requirements.txt
# Como estamos usando apenas bibliotecas padrão (sqlite3, os, datetime), não precisamos.

# 5. Comando que será executado quando o container subir
CMD ["python", "main.py"]