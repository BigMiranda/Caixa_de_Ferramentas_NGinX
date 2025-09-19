# **Instruções de Contexto e Manutenção**

Este documento fornece instruções detalhadas para a manutenção e a expansão do projeto **Caixa de Ferramentas**, garantindo que as configurações de rede e proxy permaneçam funcionais e organizadas à medida que novas aplicações são adicionadas.

### **Adicionando Novas Ferramentas ao Docker Compose**

Cada nova ferramenta Streamlit que você adicionar deve ter seu próprio serviço no arquivo docker-compose.yml. Siga os passos abaixo:

1. **Crie a pasta:** Crie um novo diretório para sua aplicação, por exemplo, minha-nova-app.  
2. **Crie um Dockerfile:** Dentro do novo diretório, crie um Dockerfile para a sua aplicação Streamlit.  
   FROM python:3.9-slim

   WORKDIR /app

   COPY requirements.txt .  
   RUN pip install \--no-cache-dir \-r requirements.txt

   COPY . .

   EXPOSE 8501

   CMD \["streamlit", "run", "app.py"\]

3. **Adicione um novo serviço:** Abra o arquivo docker-compose.yml e adicione um novo serviço, seguindo o padrão dos serviços já existentes.  
   * Escolha um nome de serviço (por exemplo, nova-app).  
   * Defina a build para o caminho da sua nova pasta.  
   * Defina uma porta para o contêiner. É crucial que cada aplicação Streamlit use uma porta interna diferente (por exemplo, 8504:8501, 8505:8501 etc.).

\# Exemplo para uma nova ferramenta  
nova-app:  
  build: ./minha-nova-app  
  ports:  
    \- "8504:8501"  
  volumes:  
    \- ./minha-nova-app:/app  
  environment:  
    \- PYTHONUNBUFFERED=1

4. **Atualize as dependências do Nginx:** Adicione o nome do seu novo serviço (por exemplo, nova-app) à lista de depends\_on do serviço nginx para garantir que o proxy só inicie após a nova aplicação estar pronta.  
   depends\_on:  
     \- streamlit-app  
     \- password-app  
     \- mutations-app  
     \- nova-app

### **Adicionando Novas Ferramentas ao Nginx**

Após configurar o Docker Compose, o Nginx precisa saber como rotear o tráfego para a nova aplicação.

1. **Adicione um novo upstream:** No arquivo nginx.conf, defina um novo upstream para o seu novo serviço. O nome do servidor deve corresponder ao nome do serviço definido no docker-compose.yml.  
   upstream nova\_app {  
       server nova-app:8501;  
   }

2. **Adicione uma nova location:** Crie um novo bloco location para a sua aplicação, seguindo o mesmo padrão dos existentes.  
   * O caminho da location deve ser um prefixo único para a sua ferramenta, por exemplo, /nova-app/.  
   * O proxy\_pass deve apontar para o upstream que você acabou de criar. Lembre-se de **não incluir a barra / no final do proxy\_pass** para evitar loops de redirecionamento.  
   * Inclua as diretivas de cabeçalho para garantir que as conexões WebSocket funcionem corretamente.

location /nova-app/ {  
    rewrite ^/nova-app/(.\*) /$1 break;  
    proxy\_pass http://nova\_app;  
    proxy\_set\_header Host $host;  
    proxy\_set\_header X-Real-IP $remote\_addr;  
    proxy\_set\_header X-Forwarded-For $proxy\_add\_x\_forwarded\_for;  
    proxy\_set\_header X-Forwarded-Proto $scheme;  
    proxy\_http\_version 1.1;  
    proxy\_set\_header Upgrade $http\_upgrade;  
    proxy\_set\_header Connection "upgrade";  
}

### **Testando a Adição**

Depois de fazer as alterações nos arquivos docker-compose.yml e nginx.conf, você deve reconstruir e reiniciar os contêineres:

docker-compose down  
docker-compose up \--build \-d

A sua nova ferramenta agora deve estar acessível em http://localhost/nova-app/.