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
    get_phase_movement_report_filtered,
    normalize_string # Necessário para a ordenação do DataFrame
)

st.set_page_config(page_title="Pipefy Query Runner", layout="wide")
st.title("📊 Executor de Query GraphQL (Pipefy)")

QUERIES_FILE = Path("saved_queries.json")

# Carrega queries salvas
try:
    if QUERIES_FILE.exists():
        with open(QUERIES_FILE, "r", encoding="utf-8") as f:
            saved_queries = json.load(f)
    else:
        saved_queries = {}
except Exception:
    saved_queries = {}


# Entradas principais - Token
token = st.text_input("🔐 Token de Acesso (Bearer)", type="password", key="token_input")
if token:
    st.session_state['token'] = token

st.markdown("---")

# Definição das abas
tab1, tab2 = st.tabs([
    "📝 Relatórios de Desistências, Mudanças de Embarque e Limpezas", 
    "⚙️ Queries personalizadas de cards conectados"
])

# Função auxiliar para download de DataFrame em Excel (Item 3)
def to_excel(df, sheet_name="Relatorio"):
    """Converte um DataFrame para um objeto BytesIO do Excel."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Garante que o nome da aba não exceda 31 caracteres
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31]) 
    return output.getvalue()


# --- TAB 1: Relatórios de Desistências, Mudanças de Embarque e Limpezas ---
with tab1:
    
    st.subheader("Entradas de Dados e Filtro de Desativação")
    
    # Radio Button para inclusão dos cards originais
    include_original_cards = st.radio(
        "Incluir cards de origem (os IDs que você insere) nos relatórios de cards conectados?",
        options=["Sim", "Não"],
        index=0,  # 'Sim' por padrão
        key="include_original_cards_tab1"
    ) == "Sim"

    # Campo de texto unificado para Card IDs
    report_card_ids_text = st.text_area("IDs dos Cards para Análise (um por linha)", key="report_card_ids_unified")
    
    # Radio Button para o tipo de desativação
    deactivation_filter_type = st.radio(
        "Selecione o tipo de desativação para o filtro:",
        ("Desistências", "Mudança de Embarque", "Limpeza"),
        key="deactivation_filter_type_unified"
    )
    
    st.markdown("---")
    st.subheader("Processamento Completo e Verificação")

    # Função para gerar e baixar o Excel com múltiplos relatórios (Relatórios 1, 2, 3)
    def generate_full_report(card_ids, token, filter_type, include_original):
        
        # Inicia o log de status
        status_placeholder = st.empty()
        
        # 1. Gerar Relatório de Fases de Cards Conectados (Report 1)
        status_placeholder.info("🔄 Gerando Relatório de Fases (1/3)...")
        report_data_1 = generate_phase_report(card_ids, token, filter_type, include_original)
        df_1 = pd.DataFrame(report_data_1)
        df_1 = df_1.sort_values(by=['Pipe ID', 'Fase ID'], ascending=[True, True])
        
        # 2. Gerar Relatório de Cards com Campos Obrigatórios (Report 2)
        status_placeholder.info("🔄 Gerando Relatório de Obrigatórios (2/3)...")
        report_data_2 = get_connected_cards_with_mandatory_fields(card_ids, token, include_original)
        df_2 = pd.DataFrame(report_data_2)
        
        # 3. Gerar Relatório com IDs de Fases Finais (Report 3)
        status_placeholder.info("🔄 Gerando Relatório de Fases Finais (3/3)...")
        report_data_3 = generate_final_phase_report(card_ids, token, filter_type, include_original)
        df_3 = pd.DataFrame(report_data_3)
        
        # Ordenação do Report 3: Deixar 'Seleção de universidades' por último
        NORM_PIPE_TO_REORDER = "selecao de universidades"
        df_3['Sort Key'] = df_3['Pipe Normalizado'].apply(
            lambda x: 1 if NORM_PIPE_TO_REORDER in x else 0
        )
        df_3 = df_3.sort_values(by=['Sort Key', 'Pipe ID', 'Fase Atual ID'], ascending=[True, True, True]).drop(columns=['Sort Key', 'Pipe Normalizado'])


        # Geração do arquivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_1.to_excel(writer, index=False, sheet_name="R1_Fases_Pipes")
            df_2.to_excel(writer, index=False, sheet_name="R2_Cards_Obrigatorios")
            df_3.to_excel(writer, index=False, sheet_name="R3_Movimentacoes")
            
        status_placeholder.success("✅ Relatórios concluídos: (3/3)")
        
        return output.getvalue()

    # Função para gerar o relatório de verificação pós-execução (Item 1)
    def generate_post_execution_verification_report(card_ids, token, filter_type, include_original):
        
        status_placeholder = st.empty()
        
        # Parte 1: Relatório 3 com comparação de fases
        status_placeholder.info("🔄 Gerando Relatório de Fases Finais com Comparação...")
        # CORREÇÃO DO TYPERROR APLICADA: Passando 'filter_type' como o 3º argumento
        report_data_3 = generate_final_phase_report(card_ids, token, filter_type, include_original)
        df_report_3 = pd.DataFrame(report_data_3)
        
        # Adicionar coluna de comparação (Item 1a)
        def check_movement_status(row):
            current_id = row['Fase Atual ID']
            final_id = row['ID da Fase de Fim de Processo']
            # Verifica se o ID da fase final foi encontrado (não é 'N/A') e se a fase atual é a final
            if final_id != 'N/A' and current_id == final_id:
                return "Movimentação OK"
            elif final_id != 'N/A':
                return "Movimentação Pendente"
            else:
                return "Fase de Fim Não Encontrada"
        
        df_report_3.insert(len(df_report_3.columns), "Status de Movimentação", df_report_3.apply(check_movement_status, axis=1))
        # Remove a coluna auxiliar de ordenação
        df_report_3 = df_report_3.drop(columns=['Pipe Normalizado'])


        # Parte 2: Relatório de Movimentação Genérica (Relatório 4) (Item 1b)
        status_placeholder.info("🔄 Gerando Relatório de Movimentação Genérica...")
        report_data_4 = get_phase_movement_report_generic(card_ids, token, include_original)
        df_report_4 = pd.DataFrame(report_data_4)

        # Parte 3: Relatório de Movimentação Filtrada (para a mensagem/Relatório 5)
        status_placeholder.info(f"🔄 Verificando Movimentações Habilitadas para '{filter_type}'...")
        report_data_filtered = get_phase_movement_report_filtered(
            card_ids, 
            token, 
            include_original,
            filter_type
        )
        df_report_filtered_enabled = pd.DataFrame([
            row for row in report_data_filtered if row['Habilitada'] == 'Sim'
        ])
        
        # 4. Geração do Excel com as duas abas
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_report_3.to_excel(writer, index=False, sheet_name="R3_Comp_Fases")
            df_report_4.to_excel(writer, index=False, sheet_name="R4_Mov_Generica")
            
        status_placeholder.success("✅ Relatórios de Verificação concluídos. Baixe o Excel abaixo.")
        
        return output.getvalue(), df_report_filtered_enabled

    # Botões do Processo Completo
    col_prep, col_verify = st.columns(2)
    
    if 'full_report_excel_data' not in st.session_state:
        st.session_state['full_report_excel_data'] = None

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
                        st.session_state['full_report_excel_data'] = generate_full_report(
                            card_ids, 
                            st.session_state.get('token'), 
                            deactivation_filter_type, 
                            include_original_cards
                        )
                        st.success("Relatórios 1, 2 e 3 processados. Pronto para download!")

                    except Exception as e:
                        st.session_state['full_report_excel_data'] = None
                        st.error("❌ Erro ao gerar os relatórios. Verifique o console para mais detalhes.")
                        st.exception(e)
    
    # Bloco de Descrição das Abas (Nova Melhoria)
    if st.session_state.get('full_report_excel_data'):
        st.markdown("---")
        st.markdown("#### 📚 Descrição e Propósito dos Relatórios (Abas do Excel)")
        st.info("Este arquivo Excel é customizado para ser usado com suas **Macros VBA**. Siga os passos definidos nelas.")
        
        st.markdown(f"""
            <div class="p-4 rounded-lg bg-blue-50 border border-blue-200 mt-4 space-y-3 text-sm">
                <p><strong>Aba R1_Fases_Pipes:</strong> Serve para <strong>habilitar</strong> (no início) e <strong>desabilitar</strong> (ao final) nas fases atuais suas respectivas movimentações para as fases de destino manualmente.</p>
                <p><strong>Aba R2_Cards_Obrigatorios:</strong> Serve para <strong>atualizar o campo `update`</strong> (via query) com um valor específico para ocultar todos os campos daquele card, pois ele está numa fase que possui campos obrigatórios. Ao final, o valor deve ser <strong>revertido para `null`</strong>.</p>
                <p><strong>Aba R3_Movimentacoes:</strong> Mostra em qual fase cada card conectado está atualmente e onde ele deverá estar após a execução da query de movimentação (Fase de Fim de Processo).</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.download_button(
            label="📤 Baixar Excel de Relatórios Completos",
            data=st.session_state['full_report_excel_data'],
            file_name=f"relatorios_completos_{deactivation_filter_type.replace(' ', '_').lower()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown("---")

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
                        excel_data, df_report_filtered_enabled = generate_post_execution_verification_report(
                            card_ids, 
                            st.session_state.get('token'), 
                            deactivation_filter_type, 
                            include_original_cards
                        )
                        
                        # Mensagem do relatório de fases habilitadas específico (Item 1c)
                        if not df_report_filtered_enabled.empty:
                            st.error("🚨 Problemas encontrados! Movimentações indesejadas HABILITADAS:")
                            st.dataframe(df_report_filtered_enabled)
                        else:
                            st.info("🎉 Excelente! Nenhuma movimentação não desejada foi encontrada para o filtro selecionado.")
                        
                        st.markdown("---")
                        st.markdown("#### Conteúdo do Arquivo de Verificação:")
                        st.markdown("Este arquivo contém o **Relatório 3** (comparando Fase Atual vs. Fase de Fim) e o **Relatório 4** (Todas as transições).")
                        
                        # Botão de download (Excel com R3 Comparado e R4 Genérico)
                        st.download_button(
                            label="📤 Baixar Excel de Verificação Completa (R3 Comparado + R4 Genérico)",
                            data=excel_data,
                            file_name=f"verificacao_completa_{deactivation_filter_type.replace(' ', '_').lower()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        st.markdown("---")

                    except Exception as e:
                        st.error("❌ Erro ao realizar a verificação. Verifique o console para mais detalhes.")
                        st.exception(e)
    
    st.markdown("---")

    # Setor de "Métodos Separados"
    with st.expander("🧩 Métodos Separados (Relatórios Individuais)"):

        # Relatório 1
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
                                deactivation_filter_type, 
                                include_original_cards
                            )
                        
                        if report_data:
                            df_report = pd.DataFrame(report_data)
                            df_report = df_report.sort_values(by=['Pipe ID', 'Fase ID'], ascending=[True, True])
                            st.success("✅ Relatório 1 gerado com sucesso!")
                            st.dataframe(df_report)
                            
                            # Botão de Exportar (Item 3)
                            st.download_button(
                                label="📥 Exportar R1 em Excel",
                                data=to_excel(df_report, sheet_name="R1_Fases"),
                                file_name="relatorio_fases_pipes.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_r1"
                            )

                        else:
                            st.info("ℹ️ Nenhum dado encontrado para os IDs e filtros fornecidos.")
                    except Exception as e:
                        st.error("❌ Erro ao gerar o relatório 1. Verifique o console para mais detalhes.")
                        st.exception(e)
        
        st.markdown("---")

        # Relatório 2
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

                            # Botão de Exportar (Item 3)
                            st.download_button(
                                label="📥 Exportar R2 em Excel",
                                data=to_excel(df_report, sheet_name="R2_Cards_Obrigatorios"),
                                file_name="relatorio_cards_obrigatorios.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_r2"
                            )
                        else:
                            st.info("ℹ️ Nenhum dado encontrado para os IDs fornecidos ou foram excluídos pelo filtro de pipe.")
                    except Exception as e:
                        st.error("❌ Erro ao gerar o relatório 2. Verifique o console para mais detalhes.")
                        st.exception(e)
        
        st.markdown("---")

        # Relatório 3
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
                                deactivation_filter_type, # Argumento de filtro
                                include_original_cards # Argumento de inclusão
                            )
                        
                        if report_data:
                            df_report = pd.DataFrame(report_data)
                            
                            # Ordenação e remoção de colunas auxiliares
                            NORM_PIPE_TO_REORDER = "selecao de universidades"
                            df_report['Sort Key'] = df_report['Pipe Normalizado'].apply(
                                lambda x: 1 if NORM_PIPE_TO_REORDER in x else 0
                            )
                            df_report = df_report.sort_values(by=['Sort Key', 'Pipe ID', 'Fase Atual ID'], ascending=[True, True, True]).drop(columns=['Sort Key', 'Pipe Normalizado'])
                            
                            st.success("✅ Relatório 3 gerado com sucesso!")
                            st.dataframe(df_report)

                            # Botão de Exportar (Item 3)
                            st.download_button(
                                label="📥 Exportar R3 em Excel",
                                data=to_excel(df_report, sheet_name="R3_Fases_Finais"),
                                file_name="relatorio_fases_finais.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_r3"
                            )

                        else:
                            st.info("ℹ️ Nenhum dado encontrado para os IDs fornecidos.")
                    except Exception as e:
                        st.error("❌ Erro ao gerar o relatório 3. Verifique o console para mais detalhes.")
                        st.exception(e)
                        
        st.markdown("---")
        
        # Relatório 4 (Corrigido)
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

                            # Botão de Exportar (Item 3)
                            st.download_button(
                                label="📥 Exportar R4 em Excel",
                                data=to_excel(df_report, sheet_name="R4_Mov_Generica"),
                                file_name="relatorio_movimentacao_generica.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_r4"
                            )
                        else:
                            st.info("ℹ️ Nenhum dado de movimentação encontrado.")
                    except Exception as e:
                        st.error("❌ Erro ao gerar o relatório 4. Verifique o console para mais detalhes.")
                        st.exception(e)

        # Relatório 5
        st.subheader("Relatório 5: Opções de Movimentação Habilitadas (Verificação)")
        st.markdown(f"Filtra o relatório 4 para mostrar **apenas** transições **Habilitadas** que levam a fases de **'{deactivation_filter_type}'**, excluindo cards que já estão em fases de desativação.")

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
                                deactivation_filter_type
                            )
                        
                        if report_data:
                            # Filtra apenas o que está habilitado para mostrar apenas os problemas
                            df_report = pd.DataFrame([row for row in report_data if row['Habilitada'] == 'Sim'])
                            
                            if not df_report.empty:
                                st.error("🚨 Problemas encontrados! Movimentações indesejadas habilitadas:")
                                st.dataframe(df_report)
                            else:
                                st.info("🎉 Excelente! Nenhuma movimentação indesejada foi encontrada.")

                            # Botão de Exportar (Item 3) - Exporta o relatório filtrado COMPLETO
                            st.download_button(
                                label="📥 Exportar R5 em Excel",
                                data=to_excel(pd.DataFrame(report_data), sheet_name="R5_Mov_Filtrada"),
                                file_name="relatorio_movimentacao_filtrada.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_r5"
                            )

                        else:
                            st.info("ℹ️ Nenhum dado de movimentação encontrado.")
                    except Exception as e:
                        st.error("❌ Erro ao gerar o relatório 5. Verifique o console para mais detalhes.")
                        st.exception(e)

# --- TAB 2: Queries personalizadas de cards conectados ---
with tab2:
    st.subheader("Queries personalizadas de cards conectados")
    st.markdown("Use esta aba para executar consultas GraphQL diretas no Pipefy.")

    query_names = list(saved_queries.keys())
    
    # Seletor com um callback que atualiza o text_area através do session state
    selected_query = st.selectbox(
        "📂 Escolher uma query salva", 
        [""] + query_names, 
        key="selected_query_tab2",
        on_change=lambda: st.session_state.update(
            edited_query_tab2_content=saved_queries.get(st.session_state.selected_query_tab2, "")
        )
    )

    # Inicializa ou carrega o conteúdo do editor com base na seleção
    query_text = saved_queries.get(selected_query, "")
    if 'edited_query_tab2_content' not in st.session_state:
        st.session_state['edited_query_tab2_content'] = query_text

    
    # Extração de parâmetros variáveis usa o valor mais recente
    current_query_content = st.session_state.get('edited_query_tab2_content', query_text)
    param_matches = re.findall(r"\$\$([^$]+)\$\$|\$([^$\n]+)\$", current_query_content)
    params = [m[0] if m[0] else m[1] for m in param_matches]
    param_values = {}
    
    if params:
        st.subheader("🧩 Campos Variáveis da Query")
        for p in params:
            # Check for multi-line parameter ($$param$$)
            if f"$$" + p + "$$" in current_query_content:
                param_values[p] = st.text_area(f"{p} (multilinha)", key=f"param_area_{p}", height=100)
            # Check for single-line parameter ($param$)
            else:
                param_values[p] = st.text_input(f"{p}", key=f"param_input_{p}")

    # Substituir campos na query
    final_query = current_query_content
    for k, v in param_values.items():
        final_query = final_query.replace(f"$$" + k + "$$", v).replace(f"$" + k + "$", v)

    with st.expander("⚙️ Configurações Avançadas"):
        # O text_area permite edição e o callback acima o preenche
        edited_query = st.text_area(
            "✍️ Editar Query GraphQL", 
            value=final_query, 
            height=300, 
            key="edited_query_tab2_editor"
        )
        # Sincroniza o estado do editor (Item 4)
        st.session_state['edited_query_tab2_content'] = edited_query
        
        with st.expander("💾 Salvar esta query"):
            new_name = st.text_input("Nome para salvar a query", key="new_query_name")
            if st.button("Salvar query", key="save_query_button"):
                if new_name and st.session_state.get('edited_query_tab2_content', "").strip():
                    saved_queries[new_name] = st.session_state['edited_query_tab2_content']
                    try:
                        with open(QUERIES_FILE, "w", encoding="utf-8") as f:
                            json.dump(saved_queries, f, indent=2, ensure_ascii=False)
                        st.success(f"Query '{new_name}' salva! Recarregue a página para ver no seletor.")
                    except Exception as e:
                        st.error(f"Erro ao salvar o arquivo: {e}")
                else:
                    st.warning("⚠️ Informe um nome válido e preencha o editor de query.")
        
        col_limit = st.number_input("🔧 Limite máximo de colunas antes de criar subtabela", min_value=1, max_value=50, value=6, step=1, key="col_limit_tab2")

    # Executar a query
    if st.button("▶️ Executar Query", key="execute_query_tab2"):
        query_to_execute = st.session_state['edited_query_tab2_content']
        
        if not st.session_state.get('token') or not query_to_execute.strip():
            st.warning("⚠️ Token e query são obrigatórios.")
        else:
            try:
                with st.spinner("🔄 Executando query..."):
                    result = execute_graphql_query(query_to_execute, st.session_state.get('token'))
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
                
                # Flatten com subtabelas
                flattened_rows = []
                all_sub_tables = {}
                for rec in nested_list:
                    # Garantir que o limite de coluna seja passado para o flatten
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

                # Exportar Excel (Mantém a capacidade de exportação individual)
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
                st.error("❌ Erro ao executar a query. Verifique o console para mais detalhes.")
                st.exception(e)
