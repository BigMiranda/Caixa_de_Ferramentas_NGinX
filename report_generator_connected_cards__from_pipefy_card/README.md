# **📊 Pipefy Query Runner**

Uma aplicação web em Streamlit para executar queries GraphQL na API do Pipefy, visualizar os dados em tabelas e exportá-los para Excel.

### **✨ Funcionalidades**

* **Execução de Queries GraphQL**: Execute queries personalizadas na API do Pipefy com suporte a variáveis.  
* **Leitura de Dados Aninhados**: Identifica e "achata" dados aninhados (como cards conectados) em um formato de tabela fácil de ler.  
* **Relatório de Fases**: Gere um relatório com as fases e pipes dos cards conectados, com a opção de filtrar por tipo de pipe (ex: "Mudança de Embarque" ou "Desistências").  
* **Relatório de Campos Obrigatórios**: Encontre cards conectados que estão em fases com campos obrigatórios.  
* **Exportação para Excel**: Exporte os resultados para um arquivo Excel com múltiplas abas para a tabela principal e as subtabelas.  
* **Salvamento de Queries**: Salve suas queries mais usadas em um arquivo local para acesso rápido.

### **⚙️ Como Usar**

1. **Clone o repositório:**  
   git clone \[https://github.com/your-repo/pipefy-query-runner.git\](https://github.com/your-repo/pipefy-query-runner.git)  
   cd pipefy-query-runner

2. **Instale as dependências:**  
   pip install \-r requirements.txt

3. **Execute a aplicação:**  
   streamlit run app.py

4. Abra a aplicação no seu navegador, insira seu token de acesso da API do Pipefy e comece a executar queries ou gerar relatórios.

### **🔑 Requisitos**

* Python 3.9+  
* Um token de acesso válido da API do Pipefy.

### **📂 Estrutura do Projeto**

.  
├── app.py                   \# Código principal do Streamlit  
├── pipefy\_utils.py          \# Funções utilitárias para a API e relatórios  
├── saved\_queries.json       \# Queries salvas  
├── requirements.txt         \# Dependências do projeto  
└── README.md                \# Documentação do projeto  