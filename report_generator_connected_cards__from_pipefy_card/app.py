import streamlit as st
import pandas as pd
import json
import re
from io import BytesIO
from pathlib import Path
from pipefy_utils import execute_graphql_query, extract_nested_lists, flatten_record_with_lists

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
token = st.text_input("🔐 Token de Acesso (Bearer)", type="password")
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
    if not token or not edited_query.strip():
        st.warning("⚠️ Token e query são obrigatórios.")
    else:
        try:
            with st.spinner("🔄 Executando query..."):
                result = execute_graphql_query(edited_query, token)
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
