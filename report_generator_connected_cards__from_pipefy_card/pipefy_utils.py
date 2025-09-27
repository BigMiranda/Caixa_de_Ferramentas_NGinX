import requests
from collections import defaultdict
import json
import re

def normalize_string(text):
    """
    Remove acentos, cedilha e converte a string para minúsculas para permitir
    comparações robustas (case-insensitive e accent-insensitive).
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    replacements = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'õ': 'o', 'ô': 'o',
        'ú': 'u',
        'ç': 'c',
    }
    for accented, unaccented in replacements.items():
        text = text.replace(accented, unaccented)
    return text

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

    Args:
        record (dict): O registro a ser achatado.
        parent_key (str, opcional): A chave pai para prefixar as novas chaves.
        sep (str, opcional): Separador entre as chaves aninhadas.
        list_field_limit (int, opcional): Limite de colunas para achatamento de listas.

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

def get_card_details(card_id, token):
    """
    Busca detalhes essenciais de um único card.
    
    Args:
        card_id (str): O ID do card.
        token (str): O token de acesso Bearer para autenticação.

    Returns:
        dict: Dados do card (id, title, pipe, current_phase) ou None.
    """
    query = f"""
    query {{
      card(id: "{card_id}") {{
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
    """
    try:
        result = execute_graphql_query(query, token)
        return result.get("data", {}).get("card")
    except Exception as e:
        print(f"Erro ao buscar detalhes do card {card_id}: {e}")
        return None

def generate_phase_report(card_ids, token, filter_type, include_original_cards):
    """
    Gera um relatório de fases e pipes de cards conectados, com filtro por pipe.

    Args:
        card_ids (list): Uma lista de IDs de card para buscar.
        token (str): O token de acesso Bearer para autenticação.
        filter_type (str): O tipo de filtro a ser aplicado ("Nenhum Filtro", "Mudança de Embarque" ou "Desistências").
        include_original_cards (bool): Se deve incluir os cards de origem no relatório.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa uma linha do relatório.
    """
    
    all_connected_cards = []

    # 1A. Incluir cards de origem se solicitado
    if include_original_cards:
        for card_id in card_ids:
            original_card_data = get_card_details(card_id.strip(), token)
            if original_card_data:
                all_connected_cards.append(original_card_data)

    # 1B. Obter cards conectados
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

    # 2. Identificar pipes únicos e aplicar filtro
    unique_pipe_ids = set(card.get("pipe", {}).get("id") for card in all_connected_cards if card.get("pipe", {}).get("id"))
    filtered_pipes = {}

    # Normaliza os alvos de filtro
    norm_target_mudanca = normalize_string("Mudança de Embarque")
    norm_target_desist = normalize_string("Desist")
    
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
                    norm_phase_name = normalize_string(phase_name)
                    
                    # FILTRO ROBUSTO: Verifica se o nome normalizado contém o alvo normalizado
                    if filter_type == "Mudança de Embarque" and norm_target_mudanca in norm_phase_name:
                        should_include_pipe = True
                        break
                    # FILTRO ROBUSTO: Verifica se o nome normalizado começa com o alvo normalizado
                    elif filter_type == "Desistências" and norm_phase_name.startswith(norm_target_desist):
                        should_include_pipe = True
                        break
            
            if should_include_pipe:
                filtered_pipes[pipe_id] = pipe_data["name"]

    # 3. Construir o relatório final
    final_report = []
    processed_phases = set()
    
    for card in all_connected_cards:
        pipe_id = card.get("pipe", {}).get("id")
        phase_id = card.get("current_phase", {}).get("id")
        
        # Garante que a fase não seja duplicada no relatório final e pertence a um pipe filtrado
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

def get_connected_cards_with_mandatory_fields(card_ids, token, include_original_cards):
    """
    Obtém uma lista de cards conectados cujas fases possuem campos obrigatórios.
    **EXCLUI O PIPE ID "302440540"**

    Args:
        card_ids (list): Uma lista de IDs de card para buscar.
        token (str): O token de acesso Bearer para autenticação.
        include_original_cards (bool): Se deve incluir os cards de origem no relatório.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa um card conectado que passou no filtro.
    """
    
    all_connected_cards = []
    
    # 1A. Incluir cards de origem se solicitado
    if include_original_cards:
        for card_id in card_ids:
            original_card_data = get_card_details(card_id.strip(), token)
            if original_card_data:
                all_connected_cards.append(original_card_data)
                
    # 1B. Obter cards conectados
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

    # 3. Filtrar os cards: por campos obrigatórios E excluir pipe "302440540"
    filtered_cards = []
    PIPE_ID_EXCLUSAO = "302440540"
    
    for card in all_connected_cards:
        pipe_id = card.get("pipe", {}).get("id")

        # FILTRO: Excluir pipe ID específico
        if pipe_id == PIPE_ID_EXCLUSAO:
            continue
            
        phase_id = card.get("current_phase", {}).get("id")
        if phase_id in unique_phases and unique_phases[phase_id]["has_mandatory_fields"]:
            filtered_cards.append({
                "Card ID": card.get("id"),
                "Card Título": card.get("title"),
                "Pipe ID": pipe_id,
                "Pipe Nome": card.get("pipe", {}).get("name"),
                "Fase ID": phase_id,
                "Fase Nome": card.get("current_phase", {}).get("name")
            })

    return filtered_cards

def generate_final_phase_report(card_ids, token, filter_type, include_original_cards):
    """
    Gera um relatório de cards conectados, incluindo a fase de fim de processo.

    Args:
        card_ids (list): Uma lista de IDs de card para buscar.
        token (str): O token de acesso Bearer para autenticação.
        filter_type (str): O tipo de filtro a ser aplicado ("Mudança de Embarque" ou "Desistências").
        include_original_cards (bool): Se deve incluir os cards de origem no relatório.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa uma linha do relatório.
    """
    
    pipe_phases_cache = {}
    all_connected_cards = []
    
    # 1A. Incluir cards de origem se solicitado
    if include_original_cards:
        for card_id in card_ids:
            original_card_data = get_card_details(card_id.strip(), token)
            if original_card_data:
                all_connected_cards.append(original_card_data)

    # 1B. Obter cards conectados
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

    # Normaliza os alvos de filtro
    norm_target_mudanca = normalize_string("Mudança de Embarque")
    norm_target_desist = normalize_string("Desist")
    
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
                norm_phase_name = normalize_string(phase_name)
                
                # FILTRO ROBUSTO: Verifica se o nome normalizado contém o alvo normalizado
                if filter_type == "Mudança de Embarque" and norm_target_mudanca in norm_phase_name:
                    end_phase_id = phase.get("id", "N/A")
                    end_phase_name = phase_name
                    break
                # FILTRO ROBUSTO: Verifica se o nome normalizado começa com o alvo normalizado
                elif filter_type == "Desistências" and norm_phase_name.startswith(norm_target_desist):
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
