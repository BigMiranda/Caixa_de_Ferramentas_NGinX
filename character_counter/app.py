import streamlit as st
import re
from collections import Counter

# Título da aplicação
st.title("Contador de Texto Avançado")

# Explicação da ferramenta
st.write("Digite seu texto na caixa abaixo para obter contagens detalhadas em tempo real.")

# Campo de entrada de texto
text_input = st.text_area(
    "Insira seu texto aqui", 
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

# --- Análises Avançadas ---

st.markdown("---")
with st.expander("Análises Avançadas de Texto"):
    st.write(
        "Clique no botão abaixo para gerar relatórios detalhados sobre a repetição de palavras e letras. "
        "Esta análise é computada apenas quando o botão é clicado para otimizar o desempenho."
    )
    if st.button("Iniciar Análise Avançada"):
        if not text_input:
            st.warning("Por favor, digite um texto para iniciar a análise.")
        else:
            # Contagem de repetição de palavras (ordenada)
            st.subheader("Frequência de Palavras")
            word_counts = Counter(words)
            sorted_word_counts = sorted(word_counts.items(), key=lambda item: item[1], reverse=True)
            st.write(sorted_word_counts)

            # Contagem de repetição de letras (ordenada)
            st.subheader("Frequência de Letras")
            letters = [c for c in text_input.lower() if c.isalpha()]
            letter_counts = Counter(letters)
            sorted_letter_counts = sorted(letter_counts.items(), key=lambda item: item[1], reverse=True)
            st.write(sorted_letter_counts)
