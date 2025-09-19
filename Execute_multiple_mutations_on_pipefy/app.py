import streamlit as st
import requests
import json
import time

# Função para fazer a requisição GraphQL
def execute_graphql_mutation(bearer_token, mutation_query):
    url = "https://api.pipefy.com/graphql"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json={"query": mutation_query})
    return response

# Função para dividir a query em super-lotes e sub-lotes
def partition_query(mutation_query, batch_size):
    # Dividir em mutações completas por "mutation{ ... }"
    queries = mutation_query.strip().split('mutation{')[1:]
    
    super_lotes = []
    
    # Para cada query completa, dividir em sub-lotes
    for query in queries:
        query_parts = query.strip().split("}")
        query_parts = [part.strip() + "}" for part in query_parts if part.strip()]
        
        # Dividir em sub-lotes, com base no tamanho do lote
        query_batches = [f"mutation{{{' '.join(query_parts[i:i + batch_size])}}}" for i in range(0, len(query_parts), batch_size)]
        
        super_lotes.append(query_batches)
    
    return super_lotes

# Função para mostrar o log de execução dinamicamente
def update_log(log_message):
    # Usamos st.empty() para atualizar dinamicamente o campo de log
    if 'log' not in st.session_state:
        st.session_state['log'] = []
    
    # Adicionar o novo log no topo (inverter a ordem)
    st.session_state['log'].insert(0, log_message)
    
    # Exibir log atualizado de forma dinâmica
    log_text = "\n".join(st.session_state['log'])
    
    # A chave única será baseada em timestamp para evitar duplicação
    log_placeholder.text_area("Log de Execução", value=log_text, height=300, max_chars=None, key=f"log_area_{time.time()}", disabled=True)

# Função para mostrar todos os previews em compartimentos expansíveis
def show_all_previews(super_lotes):
    with st.expander("Preview"):
        # Para cada super-lote, criar um compartimento expansível
        for i, query_batches in enumerate(super_lotes):
            with st.expander(f"Super-Lote {i + 1}"):
                # Para cada sub-lote do super-lote, adicionar um compartimento expansível
                for j, sub_lote in enumerate(query_batches):
                    with st.expander(f"Sub-Lote {i + 1}-{j + 1}"):
                        st.code(sub_lote, language='graphql')

# Função para executar os sub-lotes com razão de progresso
def execute_batches(bearer_token, super_lotes):
    total_sub_lotes = sum(len(batch) for batch in super_lotes)  # Total de sub-lotes
    executed_sub_lotes = 0  # Contador de sub-lotes executados

    for i, query_batches in enumerate(super_lotes):
        # Iniciar execução do Super-Lote
        update_log(f"\n{'-'*40}\nIniciando execução do Super-Lote {i + 1}\n{'-'*40}\n")
        
        for idx, batch in enumerate(query_batches):
            executed_sub_lotes += 1  # Incrementa o contador de sub-lotes executados
            
            # Calcular a porcentagem de conclusão
            progress = (executed_sub_lotes / total_sub_lotes) * 100
            
            # Exibir o progresso
            update_log(f"Sub-Lote {i + 1}-{idx + 1} : Iniciando execução ...")
            update_log(f"Progresso: {executed_sub_lotes}/{total_sub_lotes} ({progress:.2f}%)")
            
            response = execute_graphql_mutation(bearer_token, batch)
            if response.status_code == 200:
                update_log(f"Sub-Lote {i + 1}-{idx + 1} : Executado com sucesso!")
            else:
                update_log(f"Sub-Lote {i + 1}-{idx + 1} : Erro - {response.text}")
            time.sleep(1)  # Pausa para evitar sobrecarga nas requisições


# Configuração do Streamlit
st.title("Executador de Mutations do Pipefy")

# Campo para o Bearer Token
bearer_token = st.text_input("Digite o seu Bearer Token", type="password")

# Campo para a query completa
mutation_query = st.text_area("Cole sua query GraphQL completa aqui", height=300)

# Tamanho do lote (alterando o valor padrão para 25)
batch_size = st.slider("Selecione o tamanho do lote de mutations", min_value=1, max_value=50, value=25)

#MM - dobro o tamanho batch_size para orrigir mecânica.
batch_size = 2 * batch_size

# Criar o componente vazio para o log
log_placeholder = st.empty()

# Botão para processar e mostrar todos os previews
if st.button("Mostrar Preview"):
    super_lotes = partition_query(mutation_query, batch_size)
    show_all_previews(super_lotes)

# Botão para iniciar a execução dos batches
if st.button("Iniciar Execução"):
    if not bearer_token or not mutation_query:
        st.error("Por favor, preencha o Bearer Token e a Query!")
    else:
        update_log("Iniciando execução...")
        super_lotes = partition_query(mutation_query, batch_size)
        execute_batches(bearer_token, super_lotes)

# Exibição do log (dinâmico e atualizado)
if 'log' in st.session_state:
    log_text = "\n".join(st.session_state['log'])
    log_placeholder.text_area("Log de Execução", value=log_text, height=300, max_chars=None, key=f"log_area_{time.time()}", disabled=True)
else:
    log_placeholder.text_area("Log de Execução", value="Nenhum log gerado ainda.", height=300, max_chars=None, key=f"log_area_{time.time()}", disabled=True)
