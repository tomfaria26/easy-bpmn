# Usar uma imagem Python leve
FROM python:3.10-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o projeto
COPY . .

# Expor a porta padrão do Streamlit
EXPOSE 8501

# Rodar o Streamlit no container
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
