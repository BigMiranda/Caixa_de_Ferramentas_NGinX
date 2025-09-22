import streamlit as st

# Título do Lobby
st.title("Projeto Caixa de Ferramentas")

# Descrição geral
st.write("Bem-vindo! Use a barra de pesquisa ou navegue pelas ferramentas disponíveis abaixo.")

# Dados dos projetos em uma estrutura de lista para facilitar a busca
projetos = [
    {
        "titulo": "Gerador de Senhas e Hashes + Validador de Senhas",
        "descricao": """
Este projeto gera senhas e hashes usando Streamlit e BCrypt. Ele permite gerar senhas aleatórias baseadas em nomes e criar hashes de senhas fornecidas pelo usuário. Também valida se uma senha acessa um hash, ambos fornecidos pelo usuário.
""",
        "link": "http://localhost/password-app/"
    },
    {
        "titulo": "Executor de Queries de busca de cards conectados via GraphQL do Pipefy com Subtabelas",
        "descricao": """
Este projeto permite a execução de **queries GraphQL genéricas** contra a API do Pipefy, com foco em análise de dados estruturados. A aplicação identifica listas aninhadas automaticamente (como `parent_relations.cards`) e trata campos complexos de forma inteligente, exibindo os dados em tabelas interativas e exportáveis em Excel.

Você poderá:
- Substituir campos variáveis da query de forma prática
- Visualizar resultados em tabela principal e subtabelas
- Ver prévias de campos complexos e listas de objetos
- Exportar todos os dados para Excel com múltiplas abas
- Salvar e reutilizar queries nomeadas
""",
        "link": "http://localhost/report-generator/"
    },
    {
        "titulo": "Executador de Mutations do Pipefy",
        "descricao": """
Este projeto foi desenvolvido para automatizar a execução de mutações em lote no **Pipefy** utilizando **GraphQL**. O sistema divide a query em **super-lotes** e **sub-lotes**, permitindo a execução de várias mutações de maneira eficiente. Ele também exibe o progresso da execução e mantém um log dinâmico com informações detalhadas de cada etapa.
""",
        "link": "http://localhost/mutations-app/"
    },
    {
        "titulo": "Analisador de Strings (textos) Avançado",
        "descricao": """
Uma ferramenta multifuncional para análise de texto. Permite contagem em tempo real de caracteres, palavras e linhas, além de análises avançadas de frequência, inspeção de caracteres e limpeza de texto.
""",
        "link": "http://localhost/character-app/"
    }
]

# Barra de pesquisa
termo_busca = st.text_input("Pesquisar ferramenta...", placeholder="Digite o nome ou uma palavra-chave...", key="search_bar")

# Filtra os projetos com base no termo de busca
projetos_filtrados = [
    p for p in projetos
    if termo_busca.lower() in p["titulo"].lower() or termo_busca.lower() in p["descricao"].lower()
]

# Exibe os projetos filtrados
if projetos_filtrados:
    for projeto in projetos_filtrados:
        st.markdown("---")
        st.header(projeto["titulo"])
        st.write(projeto["descricao"])
        
        # Cria um botão de link que abre na mesma aba
        st.markdown(f'<a href="{projeto["link"]}" target="_self" style="display: inline-block; padding: 8px 16px; background-color: #004ec8; color: white; text-align: center; text-decoration: none; font-weight: bold; border-radius: 0.5rem;">Acessar ferramenta</a>', unsafe_allow_html=True)
else:
    st.info("Nenhuma ferramenta encontrada com esse termo de busca.")
