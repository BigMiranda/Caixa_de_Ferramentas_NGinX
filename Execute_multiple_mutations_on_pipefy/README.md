# Executador de Mutations do Pipefy

Este projeto foi desenvolvido para automatizar a execução de mutações em lote no **Pipefy** utilizando **GraphQL**. O sistema divide a query em **super-lotes** e **sub-lotes**, permitindo a execução de várias mutações de maneira eficiente. Ele também exibe o progresso da execução e mantém um log dinâmico com informações detalhadas de cada etapa.

## Funcionalidades

- **Divisão de Mutações**: Divide a query em super-lotes e sub-lotes com base no tamanho do lote.
- **Exibição de Preview**: Mostra os sub-lotes antes da execução para o usuário verificar.
- **Execução com Progresso Dinâmico**: Mostra o progresso da execução em tempo real.
- **Log de Execução**: Exibe um log contínuo com o status de cada sub-lote.

## Requisitos

- **Python 3.x**
- **Streamlit**: Para a construção da interface.
- **Requests**: Para realizar as requisições HTTP para o Pipefy.
- **Docker (opcional)**: Para rodar o projeto via Docker Compose.

## Instalação

### Usando Docker Compose

1. Clone este repositório:
   ```
   git clone <url-do-repositório>
   cd <diretório-do-repositório>
   ```
2. Inicie o aplicativo com Docker Compose:

	docker-compose up -d

	Isso irá iniciar o aplicativo em um contêiner Docker, usando a configuração do Docker Compose.

3. Acesse a interface do Streamlit no navegador:

	http://localhost:8501

### Sem Docker Compose

1. Clone este repositório:
	```
	git clone <url-do-repositório>
	cd <diretório-do-repositório>
	```

2. Instale as dependências:

	pip install -r requirements.txt

3. Execute o aplicativo:

	streamlit run app.py

4. O aplicativo será iniciado no navegador, e você poderá interagir com a interface de execução das mutações.

# Uso

1. Na interface do Streamlit, insira seu Bearer Token do Pipefy e cole a query GraphQL que você deseja executar.

2. Selecione o tamanho do lote e clique em Mostrar Preview para ver os sub-lotes.

3. Quando estiver pronto, clique em Iniciar Execução para rodar os sub-lotes sequencialmente, acompanhando o progresso e o log de execução.

# Licença

Este projeto está sob a licença MIT - veja o arquivo LICENSE para mais detalhes.

Agora você pode copiar e colar o conteúdo do `README.md` diretamente no seu repositório no GitHub!