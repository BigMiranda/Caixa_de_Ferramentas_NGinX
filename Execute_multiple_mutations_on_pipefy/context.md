# Contexto do Projeto: Executador de Mutations do Pipefy

Este projeto foi desenvolvido para automatizar a execução de mutações em lote no **Pipefy** utilizando **GraphQL**. O principal objetivo é permitir a execução de várias mutações em lotes de maneira eficiente, dividindo as consultas em **super-lotes** e **sub-lotes**, com controle de execução e exibição dinâmica de progresso.

## Funcionalidade

1. **Divisão de Mutações**:
   - A query fornecida é dividida em **super-lotes**, onde cada super-lote contém uma ou mais mutações. Cada super-lote é então subdividido em **sub-lotes**, com base no tamanho do lote especificado pelo usuário.
   
2. **Exibição de Preview**:
   - O sistema permite ao usuário visualizar os sub-lotes antes de iniciar a execução. A visualização é feita de forma interativa, com um painel expansível para cada super-lote e seus respectivos sub-lotes.

3. **Execução em Lote**:
   - Após a visualização, o usuário pode iniciar a execução. O sistema executa os sub-lotes sequencialmente, enviando mutações para o Pipefy e atualizando o progresso em tempo real.

4. **Progresso Dinâmico**:
   - Durante a execução, a porcentagem de progresso é calculada e exibida para informar ao usuário quanto do processo foi concluído.

5. **Log de Execução**:
   - O log de execução é exibido em tempo real, mostrando o status de cada sub-lote executado, e indicando se a execução foi bem-sucedida ou se houve erro.

6. **Interface Interativa**:
   - A interface é construída usando **Streamlit**, proporcionando uma experiência de usuário fluída e interativa, com a capacidade de visualizar e controlar o progresso da execução das mutações.

## Arquitetura

1. **Entrada do Usuário**: 
   - O usuário insere o **Bearer Token** e a **query GraphQL**. O tamanho do lote também pode ser ajustado.
   
2. **Processamento**:
   - A query fornecida é processada e dividida em super-lotes e sub-lotes. Cada sub-lote é enviado para o Pipefy de forma sequencial.

3. **Exibição de Resultados**:
   - O progresso é exibido com a porcentagem de execução, e o log de execução é atualizado conforme o sistema avança.

---

## Requisitos do Projeto

- **Streamlit**: Para construir a interface interativa e dinâmica.
- **Requests**: Para fazer as requisições HTTP para a API GraphQL do Pipefy.

Este projeto facilita o gerenciamento e a execução de mutações em lote no Pipefy, garantindo uma execução mais eficiente e controle em tempo real.
