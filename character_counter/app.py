import streamlit as st
import re
import pandas as pd
from collections import Counter
import io

st.set_page_config(layout="wide")

# Título da aplicação
st.title("Analisador de Strings")

# Explicação da ferramenta
st.write("Digite seu texto na caixa abaixo para obter contagens detalhadas e análises avançadas.")

# Campo de entrada de texto principal
text_input = st.text_area(
    "Insira seu texto principal aqui", 
    height=250, 
    placeholder="Comece a digitar..."
)

# --- Contagens Básicas ---

# Separadores para contagens
sentences = re.split(r'[.!?]+', text_input)
paragraphs = re.split(r'\n\n+', text_input)
words = re.findall(r'\b\w+\b', text_input.lower())

# Contagens simples
char_count = len(text_input)
word_count = len(words)
line_count = len(text_input.split('\n'))
sentence_count = len([s for s in sentences if s.strip()])
paragraph_count = len([p for p in paragraphs if p.strip()])
space_count = text_input.count(' ')

st.markdown("---")
st.subheader("Contagem de Atributos do Texto")

# Exibição das contagens básicas
col1, col2, col3 = st.columns(3)
col1.metric("Caracteres", char_count)
col2.metric("Palavras", word_count)
col3.metric("Espaços", space_count)

col1, col2, col3 = st.columns(3)
col1.metric("Linhas", line_count)
col2.metric("Sentenças", sentence_count)
col3.metric("Parágrafos", paragraph_count)


# --- Seção de Análises Avançadas ---
st.markdown("---")
st.header("Análises Avançadas")

# --------------------------
# Frequência de Ocorrências
# --------------------------
st.subheader("Frequência de Ocorrências")
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Analisar Frequência de Palavras"):
            if not text_input:
                st.warning("Por favor, digite um texto para iniciar a análise.")
            else:
                word_counts = Counter(words)
                df_words = pd.DataFrame(word_counts.items(), columns=["Palavra", "Frequência"])
                df_words = df_words.sort_values(by="Frequência", ascending=False).reset_index(drop=True)
                st.write("### Frequência de Palavras")
                st.dataframe(df_words, use_container_width=True)
                
                # Botões de download
                st.download_button(
                    label="Exportar para CSV",
                    data=df_words.to_csv(index=False),
                    file_name="frequencia_palavras.csv",
                    mime="text/csv",
                )
                
                output = io.BytesIO()
                df_words.to_excel(output, index=False)
                st.download_button(
                    label="Exportar para Excel",
                    data=output.getvalue(),
                    file_name="frequencia_palavras.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    with col2:
        if st.button("Analisar Frequência de Letras"):
            if not text_input:
                st.warning("Por favor, digite um texto para iniciar a análise.")
            else:
                letters = [c for c in text_input.lower() if c.isalpha()]
                letter_counts = Counter(letters)
                df_letters = pd.DataFrame(letter_counts.items(), columns=["Letra", "Frequência"])
                df_letters = df_letters.sort_values(by="Frequência", ascending=False).reset_index(drop=True)
                st.write("### Frequência de Letras")
                st.dataframe(df_letters, use_container_width=True)

                # Botões de download
                st.download_button(
                    label="Exportar para CSV",
                    data=df_letters.to_csv(index=False),
                    file_name="frequencia_letras.csv",
                    mime="text/csv",
                )
                
                output = io.BytesIO()
                df_letters.to_excel(output, index=False)
                st.download_button(
                    label="Exportar para Excel",
                    data=output.getvalue(),
                    file_name="frequencia_letras.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# --------------------------
# Análise Caractere por Caractere
# --------------------------
st.markdown("---")
st.subheader("Análise Caractere por Caractere")

def analyze_chars(text):
    if not text:
        return pd.DataFrame()
    char_data = []
    for char in text:
        char_data.append({
            "Caractere": char,
            "Código Decimal": ord(char),
            "Hexadecimal": hex(ord(char)),
            "Octal": oct(ord(char)),
            "URL Unicode": f"https://www.compart.com/en/unicode/U+{ord(char):04X}",
        })
    return pd.DataFrame(char_data)

with st.container(border=True):
    if st.button("Gerar Análise Char a Char"):
        if not text_input:
            st.warning("Por favor, digite um texto para gerar a análise.")
        else:
            df_chars = analyze_chars(text_input)
            st.write("### Análise Char a Char do Texto")
            st.dataframe(df_chars, use_container_width=True)
            
            # Botões de download
            st.download_button(
                label="Exportar para CSV",
                data=df_chars.to_csv(index=False),
                file_name="analise_caracteres.csv",
                mime="text/csv",
            )
            output = io.BytesIO()
            df_chars.to_excel(output, index=False)
            st.download_button(
                label="Exportar para Excel",
                data=output.getvalue(),
                file_name="analise_caracteres.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# --------------------------
# Comparação de Textos
# --------------------------
st.markdown("---")
st.subheader("Comparar Dois Textos")
with st.container(border=True):
    st.write("Insira dois textos abaixo para comparar a análise de seus caracteres.")
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Texto 1")
        text1 = st.text_area("Insira o primeiro texto", height=200, key="text1")
    with col2:
        st.write("### Texto 2")
        text2 = st.text_area("Insira o segundo texto", height=200, key="text2")
        
    if st.button("Comparar Textos Char a Char"):
        if not text1 or not text2:
            st.warning("Por favor, insira ambos os textos para comparar.")
        else:
            data = []
            max_len = max(len(text1), len(text2))
            shift_detected = False

            for i in range(max_len):
                char1 = text1[i] if i < len(text1) else ""
                char2 = text2[i] if i < len(text2) else ""
                
                # Check for "damaging" difference like extra space
                if char1.isspace() != char2.isspace():
                    shift_detected = True

                difference = ""
                if char1 != char2:
                    difference = "Sim"
                
                # Flag all subsequent characters if a damaging difference was found
                if shift_detected and char1 != char2:
                    difference = "Sim (deslocamento)"

                data.append({
                    "Posição": i,
                    "Caractere 1": repr(char1),
                    "Caractere 2": repr(char2),
                    "Diferença": difference
                })
            
            df_comparison = pd.DataFrame(data)
            st.write("### Tabela de Comparação de Caracteres")
            st.dataframe(df_comparison, use_container_width=True)

            st.download_button(
                label="Exportar para CSV",
                data=df_comparison.to_csv(index=False),
                file_name="comparacao_caracteres.csv",
                mime="text/csv",
            )
            output = io.BytesIO()
            df_comparison.to_excel(output, index=False)
            st.download_button(
                label="Exportar para Excel",
                data=output.getvalue(),
                file_name="comparacao_caracteres.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# --------------------------
# Limpeza e Normalização
# --------------------------
st.markdown("---")
st.subheader("Limpeza e Normalização do Texto")
with st.container(border=True):
    st.write("Selecione as opções de limpeza e normalização:")
    
    col1, col2 = st.columns(2)
    with col1:
        ajustar_espacos = st.checkbox("Ajustar espaçamentos", value=True)
        ajustar_corrompidos = st.checkbox("Ajustar caracteres corrompidos", value=True)
    with col2:
        ajustar_estranhos = st.checkbox("Ajustar caracteres estranhos", value=True)
        arrumar_nomes = st.checkbox("Arrumar para nomes", value=False)
        
    if st.button("Limpar e Normalizar Texto"):
        cleaned_text = text_input
        
        # Ajustar caracteres estranhos
        if ajustar_estranhos:
            cleaned_text = cleaned_text.replace('\u00A0', ' ').replace('\u200B', '')
            
        # Ajustar caracteres corrompidos
        if ajustar_corrompidos:
            corrupted_map = {
                'Ã': 'ã', 'á': 'à', 'À': 'Á', 'é': 'è', 'É': 'È', 'í': 'ì', 'Í': 'Ì',
                'ó': 'ò', 'Ó': 'Ò', 'ú': 'ù', 'Ú': 'Ù', 'ç': 'Ç', 'ã': 'Ã',
                'ü': 'Ü', 'ï': 'Ï', 'ñ': 'Ñ'
            }
            cleaned_text = cleaned_text.translate(str.maketrans(corrupted_map))
        
        # Ajustar espaçamentos (mantém quebras de linha)
        if ajustar_espacos:
            lines = cleaned_text.split('\n')
            cleaned_lines = [re.sub(r' +', ' ', line.strip()) for line in lines]
            cleaned_text = '\n'.join(cleaned_lines)
            
        # Arrumar para nomes
        if arrumar_nomes:
            # Lista de palavras para manter em minúsculo
            prepositions = ['de', 'da', 'do', 'dos', 'das', 'e', 'em']
            cleaned_words = []
            for word in cleaned_text.split():
                if word.lower() in prepositions:
                    cleaned_words.append(word.lower())
                elif word.lower().startswith("d'") and len(word) > 2:
                    cleaned_words.append("D'" + word[2].upper() + word[3:].lower())
                else:
                    cleaned_words.append(word.capitalize())
            cleaned_text = " ".join(cleaned_words)
        
        st.write("### Texto Corrigido")
        st.text_area(
            "Resultado da Limpeza",
            value=cleaned_text,
            height=300,
            key="cleaned_text_output"
        )
        # Adiciona o botão de copiar
        if st.button("Copiar Texto Corrigido"):
            st.session_state.cleaned_text = cleaned_text
            st.markdown(f'<script>navigator.clipboard.writeText(`{cleaned_text}`);</script>', unsafe_allow_html=True)
            st.success("Texto copiado para a área de transferência!")
