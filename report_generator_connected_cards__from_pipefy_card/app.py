import streamlit as st
import pandas as pd
import json
import re
from io import BytesIO
from pathlib import Path
from pipefy_utils import execute_graphql_query, extract_nested_lists, flatten_record_with_lists, generate_phase_report, get_pipe_phases, get_connected_cards_with_mandatory_fields, generate_final_phase_report

st.set_page_config(page_title="Pipefy Query Runner", layout="wide")
st.title("📊 Executor de Query GraphQL (Pipefy) com Suporte a Subtabelas")

QUERIES_FILE = Path("saved_queries.json")

# Carrega queries salvas
if QUERIES_FILE.exists():
    with open(QUERIES_FILE, "r", encoding="utf-8") as f:
        saved_queries = json.load(f)
else:
    saved_queries = {}

# Entradas principais
token = st.text_input("🔐 Token de Acesso (Bearer)", type="password", key="token_input")
if token:
    st.session_state['token'] = token

st.markdown("---")

# Seção de Relatório
with st.expander("📝 Gerar Relatório de Fases de Cards Conectados"):
    st.markdown("Use esta função para gerar um relatório consolidado das fases únicas dos cards conectados.")
    report_card_ids_text = st.text_area("IDs dos Cards (um por linha)", key="report_card_ids")
    
    st.markdown("---")
    
    filter_type = st.radio(
        "Selecione um filtro:",
        ("Nenhum Filtro", "Mudança de Embarque", "Desistências"),
        key="phase_report_filter_type"
    )

    if st.button("▶️ Gerar Relatório de Fases"):
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
                    with st.spinner("🔄 Gerando relatório..."):
                        report_data = generate_phase_report(card_ids, st.session_state.get('token'), filter_type)
                    
                    if report_data:
                        df_report = pd.DataFrame(report_data)
                        st.success("✅ Relatório gerado com sucesso!")
                        st.dataframe(df_report)
                        
                        # Exportar Excel
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                            df_report.to_excel(writer, index=False, sheet_name="Relatório de Fases")
                            
                        st.download_button(
                            label="📤 Baixar Relatório em Excel",
                            data=output.getvalue(),
                            file_name="relatorio_fases.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                        # Exportar CSV
                        csv_output = df_report.to_csv(index=False)
                        st.download_button(
                            label="📥 Baixar Relatório em CSV",
                            data=csv_output,
                            file_name="relatorio_fases.csv",
                            mime="text/csv"
                        )
                        
                    else:
                        st.info("ℹ️ Nenhum dado encontrado para os IDs e filtros fornecidos.")
                except Exception as e:
                    st.error("❌ Erro ao gerar o relatório.")
                    st.exception(e)

st.markdown("---")

# Nova seção de Relatório de Campos Obrigatórios
with st.expander("📝 Gerar Relatório de Cards com Campos Obrigatórios"):
    st.markdown("Use esta função para encontrar todos os cards conectados que estão em fases com campos obrigatórios.")
    mandatory_report_card_ids = st.text_area("IDs dos Cards (um por linha)", key="mandatory_report_card_ids")
    
    if st.button("▶️ Gerar Relatório de Obrigatórios"):
        if not mandatory_report_card_ids:
            st.warning("⚠️ Por favor, insira pelo menos um Card ID.")
        elif not st.session_state.get('token'):
            st.warning("⚠️ O Token de Acesso é obrigatório.")
        else:
            card_ids = mandatory_report_card_ids.strip().splitlines()
            if not card_ids:
                st.warning("⚠️ Por favor, insira IDs válidos.")
            else:
                try:
                    with st.spinner("🔄 Gerando relatório..."):
                        report_data = get_connected_cards_with_mandatory_fields(card_ids, st.session_state.get('token'))
                    
                    if report_data:
                        df_report = pd.DataFrame(report_data)
                        st.success("✅ Relatório gerado com sucesso!")
                        st.dataframe(df_report)
                        
                        # Exportar Excel
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                            df_report.to_excel(writer, index=False, sheet_name="Relatório Obrigatórios")
                            
                        st.download_button(
                            label="📤 Baixar Relatório em Excel",
                            data=output.getvalue(),
                            file_name="relatorio_obrigatorios.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.info("ℹ️ Nenhum dado encontrado para os IDs fornecidos.")
                except Exception as e:
                    st.error("❌ Erro ao gerar o relatório.")
                    st.exception(e)

st.markdown("---")

# Nova seção de Relatório de Fases Finais
with st.expander("📝 Gerar Relatório com IDs de Fases Finais"):
    st.markdown("Use esta função para encontrar os IDs de fases finais ('Mudança de Embarque' ou 'Desistências') para cada card conectado.")
    special_phase_card_ids = st.text_area("IDs dos Cards (um por linha)", key="special_phase_card_ids")
    
    st.markdown("---")
    
    special_phase_filter_type = st.radio(
        "Selecione o tipo de fase a ser buscada:",
        ("Mudança de Embarque", "Desistências"),
        key="special_phase_filter_type"
    )
    
    if st.button("▶️ Gerar Relatório de Fases Finais"):
        if not special_phase_card_ids:
            st.warning("⚠️ Por favor, insira pelo menos um Card ID.")
        elif not st.session_state.get('token'):
            st.warning("⚠️ O Token de Acesso é obrigatório.")
        else:
            card_ids = special_phase_card_ids.strip().splitlines()
            if not card_ids:
                st.warning("⚠️ Por favor, insira IDs válidos.")
            else:
                try:
                    with st.spinner("🔄 Gerando IDs de fases..."):
                        report_data = generate_final_phase_report(card_ids, st.session_state.get('token'), special_phase_filter_type)
                    
                    if report_data:
                        df_report = pd.DataFrame(report_data)
                        st.success("✅ Relatório de IDs gerado com sucesso!")
                        st.dataframe(df_report)
                        
                        # Exportar Excel
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                            df_report.to_excel(writer, index=False, sheet_name="IDs de Fases")
                            
                        st.download_button(
                            label="📤 Baixar Relatório em Excel",
                            data=output.getvalue(),
                            file_name="relatorio_fases_especificas.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                        # Exportar CSV
                        csv_output = df_report.to_csv(index=False)
                        st.download_button(
                            label="📥 Baixar Relatório em CSV",
                            data=csv_output,
                            file_name="relatorio_fases_especificas.csv",
                            mime="text/csv"
                        )
                        
                    else:
                        st.info("ℹ️ Nenhum dado encontrado para os IDs fornecidos.")
                except Exception as e:
                    st.error("❌ Erro ao gerar o relatório.")
                    st.exception(e)

st.markdown("---")

query_names = list(saved_queries.keys())
selected_query = st.selectbox("📂 Escolher uma query salva", [""] + query_names)
query_text = saved_queries.get(selected_query, "")

# Extração de parâmetros variáveis
param_matches = re.findall(r"\$\$([^$]+)\$\$|\$([^$\n]+)\$", query_text)
params = [m[0] if m[0] else m[1] for m in param_matches]
param_values = {}
if params:
    st.subheader("🧩 Campos Variáveis da Query")
    for p in params:
        if f"$$" + p + "$$" in query_text:
            param_values[p] = st.text_area(f"{p} (multilinha)")
        else:
            param_values[p] = st.text_input(f"{p}")

# Substituir campos na query
final_query = query_text
for k, v in param_values.items():
    final_query = final_query.replace(f"$$" + k + "$$", v).replace(f"$" + k + "$", v)

with st.expander("⚙️ Configurações Avançadas"):
    edited_query = st.text_area("✍️ Editar Query GraphQL", value=final_query, height=300)
    with st.expander("💾 Salvar esta query"):
        new_name = st.text_input("Nome para salvar a query")
        if st.button("Salvar query"):
            if new_name:
                saved_queries[new_name] = edited_query
                with open(QUERIES_FILE, "w", encoding="utf-8") as f:
                    json.dump(saved_queries, f, indent=2, ensure_ascii=False)
                st.success(f"Query '{new_name}' salva!")
            else:
                st.warning("⚠️ Informe um nome válido.")
    col_limit = st.number_input("🔧 Limite máximo de colunas antes de criar subtabela", min_value=1, max_value=50, value=6, step=1)

# Executar a query
if st.button("▶️ Executar Query"):
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
