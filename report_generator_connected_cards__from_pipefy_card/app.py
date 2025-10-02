import streamlit as st
import pandas as pd
import json
import re
from io import BytesIO
from pathlib import Path
from pipefy_utils import (
    execute_graphql_query, 
    extract_nested_lists, 
    flatten_record_with_lists, 
    generate_phase_report, 
    get_connected_cards_with_mandatory_fields, 
    generate_final_phase_report,
    get_phase_movement_report_generic,
    get_phase_movement_report_filtered
)

st.set_page_config(page_title="Pipefy Query Runner", layout="wide")
st.title("📊 Executor de Query GraphQL (Pipefy)")

QUERIES_FILE = Path("saved_queries.json")

# Carrega queries salvas
if QUERIES_FILE.exists():
    with open(QUERIES_FILE, "r", encoding="utf-8") as f:
        saved_queries = json.load(f)
else:
    saved_queries = {}

# Entradas principais - Token (Item 5)
token = st.text_input("🔐 Token de Acesso (Bearer)", type="password", key="token_input")
if token:
    st.session_state['token'] = token

st.markdown("---")

# Definição das abas (Item 5)
tab1, tab2 = st.tabs([
    "📝 Relatórios de Desistências, Mudanças de Embarque e Limpezas", 
    "⚙️ Queries personalizadas de cards conectados"
])

# --- TAB 1: Relatórios de Desistências, Mudanças de Embarque e Limpezas ---
with tab1:
    
    # INPUTS UNIFICADOS (Item 7)
    st.subheader("Entradas de Dados e Filtro de Desativação")
    
    # Radio Button para inclusão dos cards originais (Item 7)
    include_original_cards = st.radio(
        "Incluir cards de origem (os IDs que você insere) nos relatórios de cards conectados?",
        options=["Sim", "Não"],
        index=0,  # 'Sim' por padrão
        key="include_original_cards_tab1"
    ) == "Sim"

    # Campo de texto unificado para Card IDs (Item 7)
    report_card_ids_text = st.text_area("IDs dos Cards para Análise (um por linha)", key="report_card_ids_unified")
    
    # Radio Button para o tipo de desativação (Item 7)
    deactivation_filter_type = st.radio(
        "Selecione o tipo de desativação para o filtro:",
        ("Desistências", "Mudança de Embarque", "Limpeza"),
        key="deactivation_filter_type_unified"
    )
    
    st.markdown("---")
    st.subheader("Processamento Completo e Verificação")

    # Função auxiliar para gerar e baixar o Excel com múltiplos relatórios
    def generate_full_report(card_ids, token, filter_type, include_original):
        
        # Inicia o log de status
        status_placeholder = st.empty()
        
        # 1. Gerar Relatório de Fases de Cards Conectados (Report 1)
        status_placeholder.info("🔄 Gerando Relatório de Fases (1/3)...")
        report_data_1 = generate_phase_report(card_ids, token, filter_type, include_original)
        df_1 = pd.DataFrame(report_data_1)
        # Ordenação: Pipe ID crescente, depois Fase ID crescente
        df_1 = df_1.sort_values(by=['Pipe ID', 'Fase ID'], ascending=[True, True])
        
        # 2. Gerar Relatório de Cards com Campos Obrigatórios (Report 2)
        status_placeholder.info("🔄 Gerando Relatório de Obrigatórios (2/3)...")
        report_data_2 = get_connected_cards_with_mandatory_fields(card_ids, token, include_original)
        df_2 = pd.DataFrame(report_data_2)
        
        # 3. Gerar Relatório com IDs de Fases Finais (Report 3)
        status_placeholder.info("🔄 Gerando Relatório de Fases Finais (3/3)...")
        report_data_3 = generate_final_phase_report(card_ids, token, filter_type, include_original)
        df_3 = pd.DataFrame(report_data_3)
        
        # Ordenação do Report 3 (Item 1): Deixar 'Seleção de universidades' por último
        NORM_PIPE_TO_REORDER = "selecao de universidades"
        df_3['Sort Key'] = df_3['Pipe Normalizado'].apply(
            lambda x: 1 if NORM_PIPE_TO_REORDER in x else 0
        )
        df_3 = df_3.sort_values(by=['Sort Key', 'Pipe ID', 'Fase Atual ID'], ascending=[True, True, True]).drop(columns=['Sort Key', 'Pipe Normalizado'])


        # Geração do arquivo Excel
        output = BytesIO()
        # Nomes das abas (Item 6)
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_1.to_excel(writer, index=False, sheet_name="R1_Fases_Pipes")
            df_2.to_excel(writer, index=False, sheet_name="R2_Cards_Obrigatorios")
            df_3.to_excel(writer, index=False, sheet_name="R3_Fases_Finais")
            
        status_placeholder.success("✅ Relatórios concluídos: (3/3)")
        
        return output.getvalue()

    # Botões do Processo Completo (Item 6)
    col_prep, col_verify = st.columns(2)
    
    with col_prep:
        if st.button("📦 Preparar Relatórios (3 em 1)"):
            if not report_card_ids_text:
                st.warning("⚠️ Por favor, insira pelo menos um Card ID.")
            elif not st.session_state.get('token'):
                st.warning("⚠️ O Token de Acesso é obrigatório.")
            else:
                card_ids = report_card_ids_text.strip().splitlines()
                if not card_ids:
                    st.warning("⚠️ Por favor, insira IDs válidos.")
                else:
                    try:
                        excel_data = generate_full_report(
                            card_ids, 
                            st.session_state.get('token'), 
                            deactivation_filter_type, 
                            include_original_cards
                        )
                        st.download_button(
                            label="📤 Baixar Excel de Relatórios Completos",
                            data=excel_data,
                            file_name=f"relatorios_completos_{deactivation_filter_type.replace(' ', '_').lower()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.error("❌ Erro ao gerar os relatórios.")
                        st.exception(e)

    with col_verify:
        if st.button("🚨 Verificação Pós-Execução (Fases Habilitadas)"):
            if not report_card_ids_text:
                st.warning("⚠️ Por favor, insira pelo menos um Card ID.")
            elif not st.session_state.get('token'):
                st.warning("⚠️ O Token de Acesso é obrigatório.")
            else:
                card_ids = report_card_ids_text.strip().splitlines()
                if not card_ids:
                    st.warning("⚠️ Por favor, insira IDs válidos.")
                else:
                    try:
                        with st.spinner(f"🔄 Verificando movimentações para '{deactivation_filter_type}'..."):
                            report_data = get_phase_movement_report_filtered(
                                card_ids, 
                                st.session_state.get('token'), 
                                include_original_cards,
                                deactivation_filter_type
                            )
                        
                        if report_data:
                            # Filtra apenas o que está habilitado para mostrar apenas os problemas (Verificação)
                            df_report = pd.DataFrame([row for row in report_data if row['Habilitada'] == 'Sim'])
                            
                            if not df_report.empty:
                                st.error("🚨 Problemas encontrados! Movimentações indesejadas habilitadas:")
                                st.dataframe(df_report)
                                
                                # Exportar CSV
                                csv_output = df_report.to_csv(index=False)
                                st.download_button(
                                    label="📥 Baixar Verificação em CSV",
                                    data=csv_output,
                                    file_name=f"verificacao_habilitada_{deactivation_filter_type.replace(' ', '_').lower()}.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.info("🎉 Excelente! Nenhuma movimentação não desejada foi encontrada para o filtro selecionado.")
                            
                        else:
                            st.info("ℹ️ Nenhum dado de movimentação encontrado.")
                            
                    except Exception as e:
                        st.error("❌ Erro ao realizar a verificação.")
                        st.exception(e)
    
    st.markdown("---")

    # Setor de "Métodos Separados" (Item 4)
    with st.expander("🧩 Métodos Separados (Relatórios Individuais)"):

        # Gerar Relatório de Fases de Cards Conectados
        st.subheader("Relatório 1: Fases de Cards Conectados")
        st.markdown(f"Filtra **Pipes** que contêm alguma fase de **'{deactivation_filter_type}'** e lista todas as fases desses Pipes.")
        
        if st.button("▶️ Gerar Relatório de Fases (Individual)"):
            if not report_card_ids_text:
                st.warning("⚠️ Por favor, insira pelo menos um Card ID.")
            elif not st.session_state.get('token'):
                st.warning("⚠️ O Token de Acesso é obrigatório.")
            else:
                card_ids = report_card_ids_text.strip().splitlines()
                if not card_ids:
                    st.warning("⚠️ Por favor, insira IDs válidos.")
                else:
                    try:
                        with st.spinner("🔄 Gerando relatório 1..."):
                            report_data = generate_phase_report(
                                card_ids, 
                                st.session_state.get('token'), 
                                deactivation_filter_type, # Usa o filtro unificado
                                include_original_cards
                            )
                        
                        if report_data:
                            df_report = pd.DataFrame(report_data)
                            df_report = df_report.sort_values(by=['Pipe ID', 'Fase ID'], ascending=[True, True])
                            st.success("✅ Relatório 1 gerado com sucesso!")
                            st.dataframe(df_report)
                        else:
                            st.info("ℹ️ Nenhum dado encontrado para os IDs e filtros fornecidos.")
                    except Exception as e:
                        st.error("❌ Erro ao gerar o relatório 1.")
                        st.exception(e)
        
        st.markdown("---")

        # Gerar Relatório de Cards com Campos Obrigatórios
        st.subheader("Relatório 2: Cards em Fases com Campos Obrigatórios")
        st.markdown("Encontra cards conectados em fases com campos obrigatórios, **excluindo o Pipe ID 302440540**.")
        
        if st.button("▶️ Gerar Relatório de Obrigatórios (Individual)"):
            if not report_card_ids_text:
                st.warning("⚠️ Por favor, insira pelo menos um Card ID.")
            elif not st.session_state.get('token'):
                st.warning("⚠️ O Token de Acesso é obrigatório.")
            else:
                card_ids = report_card_ids_text.strip().splitlines()
                if not card_ids:
                    st.warning("⚠️ Por favor, insira IDs válidos.")
                else:
                    try:
                        with st.spinner("🔄 Gerando relatório 2..."):
                            report_data = get_connected_cards_with_mandatory_fields(
                                card_ids, 
                                st.session_state.get('token'),
                                include_original_cards
                            )
                        
                        if report_data:
                            df_report = pd.DataFrame(report_data)
                            st.success("✅ Relatório 2 gerado com sucesso!")
                            st.dataframe(df_report)
                        else:
                            st.info("ℹ️ Nenhum dado encontrado para os IDs fornecidos ou foram excluídos pelo filtro de pipe.")
                    except Exception as e:
                        st.error("❌ Erro ao gerar o relatório 2.")
                        st.exception(e)
        
        st.markdown("---")

        # Gerar Relatório com IDs de Fases Finais
        st.subheader("Relatório 3: IDs de Fases de Fim de Processo")
        st.markdown(f"Busca o ID da fase de **'{deactivation_filter_type}'** em cada Pipe conectado, card por card.")

        if st.button("▶️ Gerar Relatório de Fases Finais (Individual)"):
            if not report_card_ids_text:
                st.warning("⚠️ Por favor, insira pelo menos um Card ID.")
            elif not st.session_state.get('token'):
                st.warning("⚠️ O Token de Acesso é obrigatório.")
            else:
                card_ids = report_card_ids_text.strip().splitlines()
                if not card_ids:
                    st.warning("⚠️ Por favor, insira IDs válidos.")
                else:
                    try:
                        with st.spinner("🔄 Gerando relatório 3..."):
                            report_data = generate_final_phase_report(
                                card_ids, 
                                st.session_state.get('token'), 
                                deactivation_filter_type, # Usa o filtro unificado
                                include_original_cards
                            )
                        
                        if report_data:
                            df_report = pd.DataFrame(report_data)
                            
                            # Ordenação do Report 3 (Item 1)
                            NORM_PIPE_TO_REORDER = "selecao de universidades"
                            df_report['Sort Key'] = df_report['Pipe Normalizado'].apply(
                                lambda x: 1 if NORM_PIPE_TO_REORDER in x else 0
                            )
                            # Remove colunas auxiliares antes de mostrar
                            df_report = df_report.sort_values(by=['Sort Key', 'Pipe ID', 'Fase Atual ID'], ascending=[True, True, True]).drop(columns=['Sort Key', 'Pipe Normalizado'])
                            
                            st.success("✅ Relatório 3 gerado com sucesso!")
                            st.dataframe(df_report)
                        else:
                            st.info("ℹ️ Nenhum dado encontrado para os IDs fornecidos.")
                    except Exception as e:
                        st.error("❌ Erro ao gerar o relatório 3.")
                        st.exception(e)
                        
        st.markdown("---")
        
        # Novo Relatório 4 (Genérico) (Item 2 - Função Genérica)
        st.subheader("Relatório 4: Opções de Movimentação de Fases (Genérico)")
        st.markdown("Lista **TODAS** as transições possíveis de cada fase dos cards conectados.")

        if st.button("▶️ Gerar Relatório de Movimentação (Genérico)"):
            if not report_card_ids_text:
                st.warning("⚠️ Por favor, insira pelo menos um Card ID.")
            elif not st.session_state.get('token'):
                st.warning("⚠️ O Token de Acesso é obrigatório.")
            else:
                card_ids = report_card_ids_text.strip().splitlines()
                if not card_ids:
                    st.warning("⚠️ Por favor, insira IDs válidos.")
                else:
                    try:
                        with st.spinner("🔄 Gerando relatório 4..."):
                            report_data = get_phase_movement_report_generic(
                                card_ids, 
                                st.session_state.get('token'), 
                                include_original_cards
                            )
                        
                        if report_data:
                            df_report = pd.DataFrame(report_data)
                            st.success("✅ Relatório 4 gerado com sucesso!")
                            st.dataframe(df_report)
                        else:
                            st.info("ℹ️ Nenhum dado de movimentação encontrado.")
                    except Exception as e:
                        st.error("❌ Erro ao gerar o relatório 4.")
                        st.exception(e)

        # Novo Relatório 5 (Filtrado) (Item 2 - Função Específica)
        st.subheader("Relatório 5: Opções de Movimentação Habilitadas (Verificação)")
        st.markdown(f"Filtra o relatório 4 para mostrar **apenas** transições **Habilitadas** que levam a fases de **'{deactivation_filter_type}'** (e suas variações), excluindo cards que já estão em fases de desativação.")

        if st.button("▶️ Gerar Relatório de Movimentação (Verificação)"):
            if not report_card_ids_text:
                st.warning("⚠️ Por favor, insira pelo menos um Card ID.")
            elif not st.session_state.get('token'):
                st.warning("⚠️ O Token de Acesso é obrigatório.")
            else:
                card_ids = report_card_ids_text.strip().splitlines()
                if not card_ids:
                    st.warning("⚠️ Por favor, insira IDs válidos.")
                else:
                    try:
                        with st.spinner("🔄 Gerando relatório 5..."):
                            report_data = get_phase_movement_report_filtered(
                                card_ids, 
                                st.session_state.get('token'), 
                                include_original_cards,
                                deactivation_filter_type # Usa o filtro unificado
                            )
                        
                        if report_data:
                            # Filtra apenas o que está habilitado para mostrar apenas os problemas
                            df_report = pd.DataFrame([row for row in report_data if row['Habilitada'] == 'Sim'])
                            
                            if not df_report.empty:
                                st.error("🚨 Problemas encontrados! Movimentações indesejadas habilitadas:")
                                st.dataframe(df_report)
                            else:
                                st.info("🎉 Excelente! Nenhuma movimentação indesejada foi encontrada.")

                        else:
                            st.info("ℹ️ Nenhum dado de movimentação encontrado.")
                    except Exception as e:
                        st.error("❌ Erro ao gerar o relatório 5.")
                        st.exception(e)

# --- TAB 2: Queries personalizadas de cards conectados ---
with tab2:
    st.subheader("Queries personalizadas de cards conectados")
    st.markdown("Use esta aba para executar consultas GraphQL diretas no Pipefy.")

    query_names = list(saved_queries.keys())
    selected_query = st.selectbox("📂 Escolher uma query salva", [""] + query_names, key="selected_query_tab2")
    query_text = saved_queries.get(selected_query, "")

    # Extração de parâmetros variáveis
    param_matches = re.findall(r"\$\$([^$]+)\$\$|\$([^$\n]+)\$", query_text)
    params = [m[0] if m[0] else m[1] for m in param_matches]
    param_values = {}
    if params:
        st.subheader("🧩 Campos Variáveis da Query")
        for p in params:
            if f"$$" + p + "$$" in query_text:
                param_values[p] = st.text_area(f"{p} (multilinha)", key=f"param_area_{p}")
            else:
                param_values[p] = st.text_input(f"{p}", key=f"param_input_{p}")

    # Substituir campos na query
    final_query = query_text
    for k, v in param_values.items():
        final_query = final_query.replace(f"$$" + k + "$$", v).replace(f"$" + k + "$", v)

    with st.expander("⚙️ Configurações Avançadas"):
        edited_query = st.text_area("✍️ Editar Query GraphQL", value=final_query, height=300, key="edited_query_tab2")
        with st.expander("💾 Salvar esta query"):
            new_name = st.text_input("Nome para salvar a query", key="new_query_name")
            if st.button("Salvar query", key="save_query_button"):
                if new_name:
                    saved_queries[new_name] = edited_query
                    with open(QUERIES_FILE, "w", encoding="utf-8") as f:
                        json.dump(saved_queries, f, indent=2, ensure_ascii=False)
                    st.success(f"Query '{new_name}' salva!")
                else:
                    st.warning("⚠️ Informe um nome válido.")
        col_limit = st.number_input("🔧 Limite máximo de colunas antes de criar subtabela", min_value=1, max_value=50, value=6, step=1, key="col_limit_tab2")

    # Executar a query
    if st.button("▶️ Executar Query", key="execute_query_tab2"):
        if not st.session_state.get('token') or not edited_query.strip():
            st.warning("⚠️ Token e query são obrigatórios.")
        else:
            try:
                with st.spinner("🔄 Executando query..."):
                    result = execute_graphql_query(edited_query, st.session_state.get('token'))
                st.success("✅ Query executada com sucesso.")

                with st.expander("🔍 Logs de Execução"):
                    with st.expander("📥 Resposta bruta"):
                        st.json(result)
                    st.write("🔎 Buscando listas aninhadas (ex: parent_relations[*].cards[*])...")
                    nested_list = extract_nested_lists(result.get("data", {}))

                    if nested_list:
                        st.write(f"✅ Lista extraída com sucesso: {len(nested_list)} registros encontrados.")
                        st.write("🧾 Preview do primeiro item:")
                        st.json(nested_list[0])
                    else:
                        st.warning("❌ Nenhuma sublista encontrada com chave 'cards'.")
                        st.stop()
                
                # Flatten com subtabelas
                flattened_rows = []
                all_sub_tables = {}
                for rec in nested_list:
                    flat, sub = flatten_record_with_lists(rec, list_field_limit=col_limit)
                    flattened_rows.append(flat)
                    for subname, rows in sub.items():
                        all_sub_tables.setdefault(subname, []).extend(rows)

                df_main = pd.DataFrame(flattened_rows)
                st.subheader("📊 Tabela Principal")
                st.dataframe(df_main)
                for sub_name, sub_data in all_sub_tables.items():
                    df_sub = pd.DataFrame(sub_data)
                    st.markdown(f"#### 📄 Subtabela: `{sub_name}`")
                    st.dataframe(df_sub)

                # Exportar Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df_main.to_excel(writer, index=False, sheet_name="Principal")
                    for tab_name, sub_data in all_sub_tables.items():
                        df_sub = pd.DataFrame(sub_data)
                        df_sub.to_excel(writer, index=False, sheet_name=tab_name[:31])
                st.download_button(
                    label="📤 Baixar resultado em Excel",
                    data=output.getvalue(),
                    file_name="resultado_pipefy.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error("❌ Erro ao executar a query.")
                st.exception(e)
