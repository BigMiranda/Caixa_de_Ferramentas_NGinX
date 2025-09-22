# **Contexto da Ferramenta de Contagem**

Este documento fornece informações de contexto e instruções para a integração da ferramenta **Contador de Texto Avançado** ao projeto principal **Caixa de Ferramentas**.

### **Nginx e Docker Compose**

Conforme a sua solicitação, as configurações de Nginx e Docker Compose já foram ajustadas para esta ferramenta.

* **Nome do serviço no docker-compose.yml:** character-counter-app  
* **Porta interna:** 8501 (padrão do Streamlit)  
* **Porta externa:** 8504  
* **Caminho da URL:** /character-counter-app/

### **Adicionando ao Lobby**

Para que a ferramenta apareça na página principal do lobby, você deve adicionar o seguinte objeto ao array tools no arquivo lobby/app.py.

{  
    "title": "Contador de Texto Avançado",  
    "icon": "📝",  
    "description": "Uma ferramenta para contagem em tempo real de caracteres, palavras, linhas e mais. Inclui análise de frequência de palavras e letras.",  
    "url": "/character-counter-app/",  
},

Após adicionar este objeto, salve o arquivo app.py do lobby e reinicie os contêineres para que as alterações sejam aplicadas.