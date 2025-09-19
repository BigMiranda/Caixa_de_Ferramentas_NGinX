# Usa a imagem oficial do Python como base
FROM python:3.9

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Copia os arquivos do projeto para o contêiner
COPY . /app

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta usada pelo Streamlit
EXPOSE 8501

# Comando para rodar o Streamlit no contêiner
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
