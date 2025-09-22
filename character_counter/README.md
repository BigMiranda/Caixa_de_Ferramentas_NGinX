# **Contador de Texto Avançado**

Este projeto é uma ferramenta para análise de texto. Ele fornece contagens em tempo real de vários atributos de um texto digitado, ajudando em tarefas como redação, SEO, ou análise de conteúdo.

## **Funcionalidades**

* **Contagem em Tempo Real:**  
  * Caracteres  
  * Palavras  
  * Espaços  
  * Linhas  
  * Sentenças  
  * Parágrafos  
* **Análises Avançadas (disponível ao clicar no botão "Iniciar"):**  
  * Frequência de repetição de palavras (ordem decrescente)
  * Frequência de repetição de letras (ordem decrescente)

## **Como Usar**

1. Digite ou cole seu texto na caixa de entrada.  
2. As contagens básicas serão atualizadas instantaneamente.  
3. Para a análise avançada, clique em "Iniciar Análise Avançada" na seção oculta.

## **Estrutura do Projeto**

* app.py: Contém a lógica principal da aplicação Streamlit.  
* requirements.txt: Lista as dependências necessárias (apenas streamlit).

## **Instalação e Execução**

Para rodar esta ferramenta de forma independente (fora do contexto do seu projeto **Caixa de Ferramentas**), siga os passos abaixo:

1. Clone este repositório.  
2. Navegue até a pasta do projeto.  
3. Instale as dependências: pip install \-r requirements.txt  
4. Execute a aplicação: streamlit run app.py