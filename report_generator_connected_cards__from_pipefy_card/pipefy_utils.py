import requests
from collections import defaultdict
import json
import re

def execute_graphql_query(query, token):
    """
    Executa uma query GraphQL na API do Pipefy e lida com a resposta.

    Esta função faz a chamada HTTP para a API do Pipefy usando um token de acesso
    e uma query GraphQL. É a função central para comunicação com o serviço.

    Args:
        query (str): A string da query GraphQL a ser executada.
        token (str): O token de acesso Bearer para autenticação.

    Returns:
        dict: O resultado da requisição em formato JSON, se bem-sucedida.
    
    Raises:
        requests.exceptions.HTTPError: Se a resposta da API for um erro HTTP.
        Exception: Para outros erros inesperados na execução.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post("https://api.pipefy.com/graphql", json={"query": query}, headers=headers)
    response.raise_for_status()
    return response.json()

def extract_nested_lists(obj):
    """
    Extrai listas aninhadas, como `cards`, da resposta bruta da API de forma recursiva.

    Esta função percorre a resposta JSON para encontrar e consolidar todas as listas
    de `cards` aninhadas, tornando-as mais fáceis de processar na aplicação.

    Args:
        obj (dict or list): O objeto (resposta JSON da API) a ser inspecionado.

    Returns:
        list: Uma lista consolidada de todos os dicionários de cards encontrados.
    """
    collected_cards = []
    if isinstance(obj, dict):
        for value in obj.values():
            collected_cards.extend(extract_nested_lists(value))
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict) and 'cards' in item and isinstance(item['cards'], list):
                collected_cards.extend(item['cards'])
            collected_cards.extend(extract_nested_lists(item))
    return collected_cards

def flatten_record_with_lists(record, parent_key='', sep='_', list_field_limit=6):
    """
    Achata um registro aninhado em um dicionário de nível único.

    Esta função converte um registro aninhado da API em um dicionário simples
    (uma "linha" de tabela). Ela lida com listas de dicionários, seja achatando-as
    em colunas separadas ou criando subtabelas, dependendo do `list_field_limit`.

    Args:
        record (dict): O registro a ser achatado.
        parent_key (str, opcional): A chave pai para prefixar as novas chaves.
        sep (str, opcional): Separador entre as chaves aninhadas.
        list_field_limit (int, opcional): Limite de colunas para achatamento de listas.
                                        Acima deste limite, uma subtabela é criada.

    Returns:
        tuple: Uma tupla contendo o dicionário achatado (tabela principal) e um
               dicionário de subtabelas.
    """
    items = {}
    sub_tables = defaultdict(list)

    for k, v in record.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            sub_items, sub_sub_tables = flatten_record_with_lists(v, new_key, sep, list_field_limit)
            items.update(sub_items)
            for subk, subv in sub_sub_tables.items():
                sub_tables[subk].extend(subv)
        elif isinstance(v, list) and all(isinstance(i, dict) for i in v) and v:
            total_fields = len(v[0].keys())
            max_items = max(len(v), 1)
            estimated_columns = total_fields * max_items
            if estimated_columns <= list_field_limit:
                for idx, entry in enumerate(v):
                    for subk, subv in entry.items():
                        col_name = f"{new_key}_{idx}_{subk}"
                        items[col_name] = subv
            else:
                sub_table_name = new_key
                entry_ids = []
                previews = []
                sub_rows = []
                for idx, entry in enumerate(v):
                    row = {"__parent_id__": record.get("id", parent_key), "__local_id__": entry.get("id", f"{new_key}_{idx}")}
                    for subk, subv in entry.items():
                        row[subk] = subv
                    sub_rows.append(row)
                    preview = entry.get("name") or entry.get("title") or str(entry)
                    previews.append(preview)
                    entry_ids.append(row["__local_id__"])
                items[f"{new_key}_refs"] = entry_ids
                items[f"{new_key}_preview[]"] = previews
                sub_tables[sub_table_name].extend(sub_rows)
        else:
            items[new_key] = v
    return dict(items), dict(sub_tables)

def get_pipe_phases(pipe_id, token):
    """
    Busca todas as fases de um pipe específico na API do Pipefy.

    Args:
        pipe_id (str): O ID do pipe.
        token (str): O token de acesso Bearer para autenticação.

    Returns:
        dict: Um dicionário com o nome do pipe e uma lista de suas fases.
    """
    query = f"""
    query {{
      pipe(id: "{pipe_id}") {{
        name
        phases {{
          id
          name
        }}
      }}
    }}
    """
    try:
        result = execute_graphql_query(query, token)
        pipe_data = result.get("data", {}).get("pipe", {})
        return {
            "name": pipe_data.get("name", "Nome do Pipe"),
            "phases": pipe_data.get("phases", [])
        }
    except Exception as e:
        print(f"Erro ao buscar fases para o pipe {pipe_id}: {e}")
        return {"name": "Nome do Pipe", "phases": []}

def generate_phase_report(card_ids, token, filter_type):
    """
    Gera um relatório de fases e pipes de cards conectados, com filtro por pipe.

    Este é o método principal para a geração do relatório. Ele:
    1. Obtém os cards conectados para cada ID fornecido, incluindo o nome e ID da fase.
    2. Identifica os pipes únicos desses cards.
    3. Para cada pipe único, busca todas as suas fases para verificar se ele se enquadra no filtro.
    4. Filtra os pipes com base nas regras de nome de fase ("Mudança..." ou "Desistências").
    5. Consolida as fases *dos cards originais* que pertencem aos pipes filtrados.

    Args:
        card_ids (list): Uma lista de IDs de card para buscar.
        token (str): O token de acesso Bearer para autenticação.
        filter_type (str): O tipo de filtro a ser aplicado ("Nenhum Filtro", "Mudança de Embarque" ou "Desistências").

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa uma linha do relatório.
    """
    
    # 1. Obter cards conectados para cada ID fornecido
    all_connected_cards = []
    card_query_template = """
    query {{
      card(id: "{}") {{
        parent_relations {{
          cards {{
            id
            pipe {{
              id
              name
            }}
            current_phase {{
              id
              name
            }}
          }}
        }}
      }}
    }}
    """
    for card_id in card_ids:
        try:
            query = card_query_template.format(card_id.strip())
            result = execute_graphql_query(query, token)
            connected_cards = extract_nested_lists(result.get("data", {}))
            all_connected_cards.extend(connected_cards)
        except Exception as e:
            print(f"Erro ao processar o card ID {card_id}: {e}")
            continue

    # 2. Identificar pipes únicos para buscar todas as suas fases
    unique_pipe_ids = set(card.get("pipe", {}).get("id") for card in all_connected_cards if card.get("pipe", {}).get("id"))
    
    # Dicionário para armazenar todos os pipes que passam no filtro
    filtered_pipes = {}
    
    for pipe_id in unique_pipe_ids:
        pipe_data = get_pipe_phases(pipe_id, token)
        if pipe_data:
            phases = pipe_data["phases"]
            
            should_include_pipe = False
            
            if filter_type == "Nenhum Filtro":
                should_include_pipe = True
            else:
                for phase in phases:
                    phase_name = phase.get("name", "")
                    if filter_type == "Mudança de Embarque" and phase_name.startswith("Mudança") and phase_name.endswith("Embarque"):
                        should_include_pipe = True
                        break
                    elif filter_type == "Desistências" and phase_name.startswith("Desist"):
                        should_include_pipe = True
                        break
            
            if should_include_pipe:
                filtered_pipes[pipe_id] = pipe_data["name"]

    # 3. Construir o relatório final apenas com as fases dos cards que pertencem aos pipes filtrados
    final_report = []
    processed_phases = set()
    
    for card in all_connected_cards:
        pipe_id = card.get("pipe", {}).get("id")
        phase_id = card.get("current_phase", {}).get("id")
        
        # Garante que a fase não seja duplicada no relatório final
        if pipe_id in filtered_pipes and (pipe_id, phase_id) not in processed_phases:
            final_report.append({
                "Pipe ID": pipe_id,
                "Pipe Nome": filtered_pipes[pipe_id],
                "Fase ID": phase_id,
                "Fase Nome": card.get("current_phase", {}).get("name")
            })
            processed_phases.add((pipe_id, phase_id))
            
    return final_report

def check_phase_for_mandatory_fields(phase_id, token):
    """
    Verifica se uma fase possui campos obrigatórios.

    Args:
        phase_id (str): O ID da fase a ser verificada.
        token (str): O token de acesso Bearer para autenticação.

    Returns:
        bool: True se a fase tem pelo menos um campo obrigatório, False caso contrário.
    """
    query = f"""
    query {{
      phase(id: "{phase_id}") {{
        fields {{
          required
        }}
      }}
    }}
    """
    try:
        result = execute_graphql_query(query, token)
        fields = result.get("data", {}).get("phase", {}).get("fields", [])
        return any(field.get("required") for field in fields)
    except Exception as e:
        print(f"Erro ao verificar campos obrigatórios para a fase {phase_id}: {e}")
        return False

def get_connected_cards_with_mandatory_fields(card_ids, token):
    """
    Obtém uma lista de cards conectados cujas fases possuem campos obrigatórios.

    Args:
        card_ids (list): Uma lista de IDs de card para buscar.
        token (str): O token de acesso Bearer para autenticação.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa um card conectado que passou no filtro.
    """
    # 1. Obter todos os cards conectados com seus dados de fase
    all_connected_cards = []
    card_query_template = """
    query {{
      card(id: "{}") {{
        parent_relations {{
          cards {{
            id
            title
            pipe {{
              id
              name
            }}
            current_phase {{
              id
              name
            }}
          }}
        }}
      }}
    }}
    """
    for card_id in card_ids:
        try:
            query = card_query_template.format(card_id.strip())
            result = execute_graphql_query(query, token)
            connected_cards = extract_nested_lists(result.get("data", {}))
            all_connected_cards.extend(connected_cards)
        except Exception as e:
            print(f"Erro ao processar o card ID {card_id}: {e}")
            continue

    # 2. Identificar fases únicas e verificar se possuem campos obrigatórios
    unique_phases = {}
    for card in all_connected_cards:
        phase_id = card.get("current_phase", {}).get("id")
        if phase_id and phase_id not in unique_phases:
            unique_phases[phase_id] = {
                "name": card.get("current_phase", {}).get("name"),
                "has_mandatory_fields": False
            }

    for phase_id in unique_phases.keys():
        has_mandatory = check_phase_for_mandatory_fields(phase_id, token)
        unique_phases[phase_id]["has_mandatory_fields"] = has_mandatory

    # 3. Filtrar os cards conectados originais com base nas fases que têm campos obrigatórios
    filtered_cards = []
    for card in all_connected_cards:
        phase_id = card.get("current_phase", {}).get("id")
        if phase_id in unique_phases and unique_phases[phase_id]["has_mandatory_fields"]:
            filtered_cards.append({
                "Card ID": card.get("id"),
                "Card Título": card.get("title"),
                "Pipe ID": card.get("pipe", {}).get("id"),
                "Pipe Nome": card.get("pipe", {}).get("name"),
                "Fase ID": phase_id,
                "Fase Nome": card.get("current_phase", {}).get("name")
            })

    return filtered_cards

def generate_final_phase_report(card_ids, token, filter_type):
    """
    Gera um relatório de cards conectados, incluindo a fase de fim de processo.

    Para cada card conectado, este método encontra a fase de fim de processo
    (Mudança de Embarque ou Desistências) no pipe do card e a adiciona ao relatório.

    Args:
        card_ids (list): Uma lista de IDs de card para buscar.
        token (str): O token de acesso Bearer para autenticação.
        filter_type (str): O tipo de filtro a ser aplicado ("Mudança de Embarque" ou "Desistências").

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa uma linha do relatório.
    """
    
    # Dicionário para cache das fases por pipe para evitar múltiplas chamadas à API
    pipe_phases_cache = {}
    
    # 1. Obter cards conectados para cada ID fornecido
    all_connected_cards = []
    card_query_template = """
    query {{
      card(id: "{}") {{
        title
        parent_relations {{
          cards {{
            id
            title
            pipe {{
              id
              name
            }}
            current_phase {{
              id
              name
            }}
          }}
        }}
      }}
    }}
    """
    for card_id in card_ids:
        try:
            query = card_query_template.format(card_id.strip())
            result = execute_graphql_query(query, token)
            connected_cards = extract_nested_lists(result.get("data", {}))
            all_connected_cards.extend(connected_cards)
        except Exception as e:
            print(f"Erro ao processar o card ID {card_id}: {e}")
            continue

    # 2. Construir o relatório final card por card
    final_report = []
    
    for card in all_connected_cards:
        pipe_id = card.get("pipe", {}).get("id")
        
        end_phase_id = "N/A"
        end_phase_name = "N/A"
        
        if pipe_id:
            # Busca as fases do pipe do cache, ou da API se não estiver no cache
            if pipe_id not in pipe_phases_cache:
                pipe_phases_cache[pipe_id] = get_pipe_phases(pipe_id, token)["phases"]

            phases_of_pipe = pipe_phases_cache[pipe_id]
            
            # Encontra a fase de "fim de processo"
            for phase in phases_of_pipe:
                phase_name = phase.get("name", "")
                
                # Usando expressões regulares para uma busca mais robusta e case-insensitive
                if filter_type == "Mudança de Embarque" and re.search(r'mudanca.*embarque', phase_name, re.IGNORECASE):
                    end_phase_id = phase.get("id", "N/A")
                    end_phase_name = phase_name
                    break
                elif filter_type == "Desistências" and re.search(r'desist', phase_name, re.IGNORECASE):
                    end_phase_id = phase.get("id", "N/A")
                    end_phase_name = phase_name
                    break
        
        final_report.append({
            "Card ID": card.get("id"),
            "Card Título": card.get("title"),
            "Pipe ID": pipe_id,
            "Pipe Nome": card.get("pipe", {}).get("name"),
            "Fase Atual ID": card.get("current_phase", {}).get("id"),
            "Fase Atual Nome": card.get("current_phase", {}).get("name"),
            "ID da Fase de Fim de Processo": end_phase_id,
            "Nome da Fase de Fim de Processo": end_phase_name
        })
            
    return final_report
