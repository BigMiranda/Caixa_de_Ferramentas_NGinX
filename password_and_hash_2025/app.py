import streamlit as st
import pandas as pd
import bcrypt
import random
import string
import io

# Configurar o título da aba do navegador e o título do app
st.set_page_config(page_title="Gerador e validador de senhas")

# Função para gerar senhas e hashes a partir do nome
def process_data_generate_password(csv_input):
    processed_list = []
    lines = csv_input.strip().split("\n")
    
    for line in lines:
        try:
            codigo, nome = line.split(";")
            codigo = codigo.strip()
            nome = nome.strip()

            # Gerar senha
            senha = generate_password(nome)

            # Gerar Hash BCrypt no padrão $2a$
            hash_senha = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt(rounds=10, prefix=b"2a")).decode("utf-8")

            # Adicionar à lista de retorno
            processed_list.append([codigo, senha, hash_senha])
        
        except Exception as e:
            st.error(f"Erro ao processar a linha: {line}, erro: {e}")

    return processed_list

# Função para gerar apenas o hash da senha fornecida
def process_data_generate_hash(csv_input):
    processed_list = []
    lines = csv_input.strip().split("\n")
    
    for line in lines:
        try:
            codigo, senha = line.split(";")
            codigo = codigo.strip()
            senha = senha.strip()

            # Gerar Hash BCrypt no padrão $2a$
            hash_senha = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt(rounds=10, prefix=b"2a")).decode("utf-8")

            # Adicionar à lista de retorno
            processed_list.append([codigo, senha, hash_senha])
        
        except Exception as e:
            st.error(f"Erro ao processar a linha: {line}, erro: {e}")

    return processed_list

# Função para gerar senha baseada no nome
def generate_password(nome):
    base = nome[:3] if len(nome) >= 3 else nome
    random_part = generate_random_alphanumeric(6)
    return base + random_part

# Função para gerar caracteres aleatórios alfanuméricos
def generate_random_alphanumeric(length):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# Função para validar se a senha corresponde ao hash fornecido
def process_data_validate_access(csv_input):
    processed_list = []
    lines = csv_input.strip().split("\n")
    
    for line in lines:
        try:
            codigo, senha, hash_fornecido = line.split(";")
            codigo = codigo.strip()
            senha = senha.strip()
            hash_fornecido = hash_fornecido.strip()

            try:
                # Tenta validar a senha em relação ao hash
                if bcrypt.checkpw(senha.encode("utf-8"), hash_fornecido.encode("utf-8")):
                    validacao = "Acesso permitido"
                else:
                    validacao = "Acesso negado"
            except Exception as e:
                # Se ocorrer algum erro (como "Invalid salt") registra o erro na validação
                validacao = f"Erro na validação: {e}"
            
            processed_list.append([codigo, senha, hash_fornecido, validacao])
        
        except Exception as e:
            st.error(f"Erro ao processar a linha: {line}, erro: {e}")

    return processed_list

# Função para converter dataframe em arquivo Excel
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Resultados")
    processed_data = output.getvalue()
    return processed_data

# ========================== STREAMLIT UI ==========================
st.title("Gerador e Validação de Senhas e Hashes")

# Criando as abas no Streamlit
aba1, aba2, aba3 = st.tabs(["Gerar Senha e Hash", "Gerar Hash de Senha Existente", "Validar Acesso"])

# Aba 1 - Gerar Senha e Hash
with aba1:
    st.subheader("Entrada: Código;Nome (Gerar Senha e Hash)")
    input_data = st.text_area("Insira os dados no formato CSV (Código;Nome), um por linha:",
                              "987654321;Ana\n123456789;João")
    if st.button("Gerar Senhas e Hashes", key="generate_password"):
        processed_data = process_data_generate_password(input_data)
        if processed_data:
            df = pd.DataFrame(processed_data, columns=["Código", "Senha", "Hash"])
            st.subheader("Resultados:")
            st.dataframe(df)
            # Botão de download do Excel
            excel_data = convert_df_to_excel(df)
            st.download_button(label="📥 Baixar Excel", 
                               data=excel_data, 
                               file_name="senhas_geradas.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Aba 2 - Gerar Hash de Senha Existente
with aba2:
    st.subheader("Entrada: Código;Senha (Gerar Apenas o Hash)")
    input_data_hash = st.text_area("Insira os dados no formato CSV (Código;Senha), um por linha:",
                                   "987654321;AnaL4nmR\n123456789;MySecretPass")
    if st.button("Gerar Apenas o Hash", key="generate_hash"):
        processed_data = process_data_generate_hash(input_data_hash)
        if processed_data:
            df = pd.DataFrame(processed_data, columns=["Código", "Senha", "Hash"])
            st.subheader("Resultados:")
            st.dataframe(df)
            # Botão de download do Excel
            excel_data = convert_df_to_excel(df)
            st.download_button(label="📥 Baixar Excel", 
                               data=excel_data, 
                               file_name="hashes_gerados.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Aba 3 - Validar Acesso
with aba3:
    st.subheader("Entrada: Código;Senha;Hash (Validar se a senha permite acesso)")
    st.info("Validação pode retornar Acesso permitido, Acesso negado ou Erro de salt. Este último se refere a um Hash fora do tamanho valido.")
    input_data_validation = st.text_area("Insira os dados no formato CSV (Código;Senha;Hash), um por linha:",
                                         "987654321;AnaL4nmR;$2a$10$hqwlUNCVLISYhIW6Yh3n0uiKkZw31W435BkUKigkv.HjNVp5S62LO\n123456789;MySecretPass;$2a$10$hqwlUNCVLISYhIW6Yh3n0uiKkZw31W435BkUKigkv.HjNVp5S62LO\n123456788;MySecretPassErro;$2a$10$EXEMPLO_DE_HASH_INVALIDO")
    if st.button("Validar Acesso", key="validate_access"):
        processed_data = process_data_validate_access(input_data_validation)
        if processed_data:
            df = pd.DataFrame(processed_data, columns=["Código", "Senha", "Hash", "Validação"])
            st.subheader("Resultados:")
            st.dataframe(df)
            # Botão de download do Excel
            excel_data = convert_df_to_excel(df)
            st.download_button(label="📥 Baixar Excel", 
                               data=excel_data, 
                               file_name="validacao_acesso.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
