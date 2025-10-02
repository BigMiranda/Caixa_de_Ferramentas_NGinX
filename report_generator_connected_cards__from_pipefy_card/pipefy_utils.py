import requests
from collections import defaultdict
import json
import re
# Importação da biblioteca para IO (não usada diretamente aqui, mas boa prática)
# from io import BytesIO 

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
        # Adicionado parent_relations para a função de relatórios
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
    try:
        result = execute_graphql_query(query, token)
        return result.get("data", {}).get("card")
    except Exception as e:
        print(f"Erro ao buscar detalhes do card {card_id}: {e}")
        return None

def check_phase_match(phase_name, filter_type):
    """
    Verifica se o nome da fase corresponde ao tipo de filtro (Mudança, Desistências ou Limpeza),
    ignorando acentos e capitalização.
    """
    if not isinstance(phase_name, str):
        return False
        
    norm_phase_name = normalize_string(phase_name)
    
    if filter_type == "Mudança de Embarque":
        norm_target = normalize_string("Mudança de Embarque")
        return norm_target in norm_phase_name
    
    elif filter_type == "Desistências":
        # Usa 'desist' para pegar 'Desistência' e 'Desistências'
        norm_target = normalize_string("Desist") 
        return norm_phase_name.startswith(norm_target)
        
    elif filter_type == "Limpeza":
        norm_target = normalize_string("Limpeza")
        return norm_target in norm_phase_name
        
    return False

def get_connected_cards_for_report(card_ids, token, include_original_cards):
    """
    Função auxiliar para obter todos os cards conectados de uma lista de IDs de card.
    """
    all_connected_cards = []
    
    # Usar um set para garantir unicidade dos cards conectados
    unique_connected_cards = {}
    
    for card_id in card_ids:
        card_id = card_id.strip()
        if not card_id:
            continue
            
        try:
            # Busca detalhes do card principal
            original_card_data = get_card_details(card_id, token)
            
            if original_card_data:
                # 1A. Incluir cards de origem
                if include_original_cards:
                    # Remove a relação de cards conectados para não duplicar na extração
                    temp_card = original_card_data.copy()
                    temp_card.pop("parent_relations", None) 
                    unique_connected_cards[temp_card["id"]] = temp_card
                
                # 1B. Obter cards conectados (via parent_relations)
                connected_cards = extract_nested_lists(original_card_data)
                
                for card in connected_cards:
                    if card and card.get("id"):
                        unique_connected_cards[card["id"]] = card

        except Exception as e:
            # Imprimir o erro aqui para fins de diagnóstico
            print(f"Erro ao processar o card ID {card_id} ou seus conectados: {e}")
            continue
            
    return list(unique_connected_cards.values())


def generate_phase_report(card_ids, token, filter_type, include_original_cards):
    """
    Gera um relatório de fases e pipes de cards conectados, com filtro por pipe.
    (Relatório 1)
    """
    
    all_connected_cards = get_connected_cards_for_report(card_ids, token, include_original_cards)

    # 2. Identificar pipes únicos e aplicar filtro
    unique_pipe_ids = set(card.get("pipe", {}).get("id") for card in all_connected_cards if card and card.get("pipe", {}).get("id"))
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
                    if check_phase_match(phase_name, filter_type):
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
        if pipe_id in filtered_pipes and phase_id and (pipe_id, phase_id) not in processed_phases:
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
    **EXCLUI O PIPE ID "302440540"** (Relatório 2)
    """
    
    all_connected_cards = get_connected_cards_for_report(card_ids, token, include_original_cards)
    
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
    Gera um relatório de cards conectados, incluindo a fase de fim de processo
    (Mudança de Embarque, Limpeza ou Desistências). (Relatório 3/Verificação)
    """
    
    pipe_phases_cache = {}
    all_connected_cards = get_connected_cards_for_report(card_ids, token, include_original_cards)
    
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
            
            # Encontra a fase de "fim de processo" (baseado no filter_type)
            for phase in phases_of_pipe:
                phase_name = phase.get("name", "")
                
                if check_phase_match(phase_name, filter_type):
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
            "Nome da Fase de Fim de Processo": end_phase_name,
            # Campo auxiliar para ordenação
            "Pipe Normalizado": normalize_string(card.get("pipe", {}).get("name", ""))
        })
            
    return final_report

def get_phase_transitions(phase_id, token):
    """
    Busca todas as transições (movimentações) de uma fase específica.
    """
    query = f"""
    query {{
      phase(id: "{phase_id}") {{
        name
        transitions {{
          id
          name
          to_phase {{
            id
            name
          }}
          can_move_to
        }}
      }}
    }}
    """
    try:
        result = execute_graphql_query(query, token)
        phase_data = result.get("data", {}).get("phase", {})
        return {
            "name": phase_data.get("name"),
            "transitions": phase_data.get("transitions", [])
        }
    except Exception as e:
        print(f"Erro ao buscar transições para a fase {phase_id}: {e}")
        return {"name": "N/A", "transitions": []}

def get_phase_movement_report_generic(card_ids, token, include_original_cards):
    """
    Relatório genérico de todas as opções de movimentação de fases para cards conectados.
    (Relatório 4)
    """
    all_connected_cards = get_connected_cards_for_report(card_ids, token, include_original_cards)
    report = []
    phase_transition_cache = {}

    if not all_connected_cards:
        return report 

    for card in all_connected_cards:
        current_phase = card.get("current_phase", {})
        pipe = card.get("pipe", {})
        
        if not current_phase.get("id"):
            continue

        phase_id = current_phase["id"]

        # Busca do cache ou API
        if phase_id not in phase_transition_cache:
            transitions_data = get_phase_transitions(phase_id, token)
            phase_transition_cache[phase_id] = transitions_data

        transitions_data = phase_transition_cache[phase_id]
        
        # Correção do Relatório 4: Garantir que a iteração ocorra se houver dados
        if transitions_data and transitions_data.get("transitions"):
            for transition in transitions_data["transitions"]:
                to_phase = transition.get("to_phase", {})
                report.append({
                    "Card ID": card.get("id"),
                    "Card Título": card.get("title"),
                    "Pipe ID": pipe.get("id"),
                    "Pipe Nome": pipe.get("name"),
                    "Fase Atual ID": phase_id,
                    "Fase Atual Nome": current_phase.get("name"),
                    "Transição ID": transition.get("id"),
                    "Transição Nome": transition.get("name"),
                    "Fase Destino ID": to_phase.get("id"),
                    "Fase Destino Nome": to_phase.get("name"),
                    "Habilitada": "Sim" if transition.get("can_move_to") else "Não"
                })
            
    return report

def get_phase_movement_report_filtered(card_ids, token, include_original_cards, target_filter):
    """
    Relatório de movimentações para as fases de "Desativação" (Mudança, Limpeza, Desistências),
    excluindo transições de pipes que já estão em uma fase de desativação.
    (Relatório 5/Verificação)
    """
    
    # 1. Gerar o relatório genérico
    generic_report = get_phase_movement_report_generic(card_ids, token, include_original_cards)
    
    filtered_report = []
    
    # Lista de todos os filtros que indicam uma "fase de desativação"
    ALL_DEACTIVATION_FILTERS = ["Mudança de Embarque", "Desistências", "Limpeza"]

    for row in generic_report:
        current_phase_name = row["Fase Atual Nome"]
        target_phase_name = row["Fase Destino Nome"]
        
        # 2. Verificar se a fase destino corresponde ao filtro ALVO
        is_target_destination = check_phase_match(target_phase_name, target_filter)

        if not is_target_destination:
            continue # Se não for o destino que estamos verificando, ignorar

        # 3. Regra de Exclusão:
        # Excluir se a FASE ATUAL já é uma das fases de desativação (Limpeza/Desistências/Mudança de Embarque).
        is_current_phase_already_deactivation = any(
            check_phase_match(current_phase_name, deactivation_filter) 
            for deactivation_filter in ALL_DEACTIVATION_FILTERS
        )
        
        if is_current_phase_already_deactivation:
            continue # Pula as transições de fases que já são alvo de "desativação"

        # Se passou pelos filtros, adicionar ao relatório
        filtered_report.append(row)
            
    return filtered_report
