# **Analisador de Strings**

Uma ferramenta multifuncional para análise de texto. Permite contagem em tempo real de caracteres, palavras e linhas, além de análises avançadas de frequência, inspeção de caracteres e limpeza de texto.

### **Funcionalidades**

* **Contagem Básica:** Contagem de caracteres, palavras, espaços, linhas, sentenças e parágrafos.  
* **Frequência de Ocorrências:** Análise de repetição de palavras e letras em formato de tabela, com opções de exportação para Excel ou CSV.  
* **Análise Char a Char:** Apresenta cada caractere com seu código decimal, hexadecimal e octal.  
* **Comparação de Textos:** Analisa os caracteres de dois textos lado a lado.  
* **Limpeza e Normalização:** Corrige espaçamentos, caracteres estranhos e corrompidos. Inclui um modo de formatação para nomes.

### **Como Executar**

A ferramenta foi projetada para rodar em um ambiente Docker e pode ser integrada a um ecossistema com Nginx para proxy reverso.

1. Certifique-se de que o **Python** e o **Streamlit** estão instalados no seu ambiente.  
2. Instale as dependências com o comando:  
   pip install \-r requirements.txt

3. Execute a aplicação localmente:  
   streamlit run app.py

Para integração com o seu ambiente completo, adicione o serviço ao docker-compose.yml e configure o Nginx para rotear o tráfego para a aplicação.