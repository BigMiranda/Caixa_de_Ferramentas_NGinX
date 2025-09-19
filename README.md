# **Projeto Caixa de Ferramentas**

Bem-vindo ao projeto **Caixa de Ferramentas**, uma coleção de aplicações utilitárias projetadas para simplificar e automatizar diversas tarefas. Este repositório é um hub central que unifica múltiplas ferramentas em uma única interface, permitindo fácil acesso e navegação.

## **Visão Geral da Arquitetura**

Este projeto utiliza uma arquitetura baseada em contêineres e um proxy reverso para orquestrar as aplicações:

* **Streamlit:** Cada ferramenta é uma aplicação Streamlit independente, otimizada para prototipagem e desenvolvimento rápido de interfaces de dados.  
* **Docker Compose:** Orquestra a execução de todos os serviços (as ferramentas Streamlit e o Nginx) em seus próprios contêineres isolados.  
* **Nginx:** Atua como um **proxy reverso**, direcionando o tráfego da porta 80 do host para a ferramenta correta, garantindo que todas as aplicações sejam acessíveis a partir de um único ponto de entrada.

## **Ferramentas Disponíveis**

1. **Gerador de Senhas e Hashes:** Para criar senhas seguras e gerenciar hashes BCrypt.  
2. **Executor de Queries GraphQL:** Uma ferramenta poderosa para interagir com APIs Pipefy e analisar dados.  
3. **Executador de Mutations do Pipefy:** Para automatizar mutações em lote e monitorar o progresso.

## **Como Executar o Projeto**

1. **Pré-requisitos:** Certifique-se de ter o Docker e o Docker Compose instalados em seu sistema.  
2. **Navegação:** Abra o terminal e navegue até a raiz do projeto (onde está o arquivo docker-compose.yml).  
3. **Inicialização:** Execute o seguinte comando para iniciar todos os serviços:  
   docker-compose up \--build \-d

4. **Acesso:** Após a inicialização, o lobby do projeto estará disponível em http://localhost/ no seu navegador.

## **Adicionando Novas Ferramentas**

Para adicionar uma nova ferramenta à sua Caixa de Ferramentas, siga as instruções detalhadas no arquivo context.md, que cobre a configuração do Docker Compose e do Nginx para garantir que a nova ferramenta seja integrada com sucesso.