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
    # Usamos o placeholder definido na UI principal
    if 'log_placeholder' in st.session_state:
        log_placeholder = st.session_state['log_placeholder']
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
# Agora aceita 'delay_time' para pausar entre as requisições
def execute_batches(bearer_token, super_lotes, delay_time):
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
            
            # --- VERIFICAÇÃO DE ERRO MELHORADA ---
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "errors" in data:
                        # Erro de GraphQL detectado (operação falhou, mas HTTP foi 200)
                        error_message = json.dumps(data["errors"], indent=2)
                        update_log(f"Sub-Lote {i + 1}-{idx + 1} : Erro de GraphQL (Status 200) - {error_message}")
                    else:
                        # Execução bem-sucedida
                        update_log(f"Sub-Lote {i + 1}-{idx + 1} : Executado com sucesso!")
                except json.JSONDecodeError:
                    # Resposta não é JSON, o que pode indicar um problema inesperado no Pipefy
                    update_log(f"Sub-Lote {i + 1}-{idx + 1} : Erro - Resposta HTTP 200, mas corpo inesperado ou não JSON: {response.text}")

            else:
                # Erro HTTP tradicional (4xx, 5xx, etc.)
                update_log(f"Sub-Lote {i + 1}-{idx + 1} : Erro HTTP ({response.status_code}) - {response.text}")
            
            # Pausa configurável para evitar sobrecarga (controle de rate-limit)
            if delay_time > 0:
                update_log(f"Pausando por {delay_time}s...")
                time.sleep(delay_time) 


# Configuração do Streamlit
st.set_page_config(page_title="Executador de Mutations Pipefy", layout="wide")
st.title("Executador de Mutations do Pipefy")

# Campo para o Bearer Token
bearer_token = st.text_input("Digite o seu Bearer Token", type="password")

# Campo para a query completa
mutation_query = st.text_area("Cole sua query GraphQL completa aqui", height=300)

# Tamanho do lote (alterando o valor padrão para 25)
batch_size = st.slider("Selecione o tamanho do lote de mutations (Sub-Lote)", min_value=1, max_value=50, value=25)

# MM - dobro o tamanho batch_size para corrigir mecânica.
batch_size = 2 * batch_size

# NOVO CAMPO: Tempo de pausa entre sub-lotes
delay_time = st.slider("Tempo de Pausa (segundos) entre sub-lotes", min_value=0.0, max_value=5.0, value=0.5, step=0.1, key='delay_time_slider')

# Criar o componente vazio para o log e armazená-lo na session_state
# Isso é necessário para que a função update_log possa acessá-lo.
log_placeholder = st.empty()
st.session_state['log_placeholder'] = log_placeholder

# Botão para processar e mostrar todos os previews
if st.button("Mostrar Preview"):
    if mutation_query:
        try:
            super_lotes = partition_query(mutation_query, batch_size)
            show_all_previews(super_lotes)
        except Exception as e:
             st.error(f"Erro ao processar a query: {e}. Verifique a sintaxe da sua query.")
    else:
        st.warning("Por favor, cole sua query GraphQL completa.")


# Botão para iniciar a execução dos batches
if st.button("Iniciar Execução"):
    if not bearer_token or not mutation_query:
        st.error("Por favor, preencha o Bearer Token e a Query!")
    else:
        update_log("Iniciando execução...")
        
        try:
            super_lotes = partition_query(mutation_query, batch_size)
            
            # Passando o delay_time para a função de execução
            execute_batches(bearer_token, super_lotes, delay_time)
            
        except Exception as e:
             update_log(f"ERRO CRÍTICO NA EXECUÇÃO: {e}")
             st.error(f"Erro crítico: {e}")


# Exibição do log (dinâmico e atualizado)
if 'log' in st.session_state:
    log_text = "\n".join(st.session_state['log'])
    # Usa o placeholder para atualização final (o update_log cuida das atualizações intermediárias)
    st.session_state['log_placeholder'].text_area("Log de Execução", value=log_text, height=300, max_chars=None, key=f"log_area_final", disabled=True)
else:
    st.session_state['log_placeholder'].text_area("Log de Execução", value="Nenhum log gerado ainda.", height=300, max_chars=None, key=f"log_area_init", disabled=True)
