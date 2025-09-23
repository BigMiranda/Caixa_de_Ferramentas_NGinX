# **Contexto do Projeto: Analisador de Strings**

Este documento fornece um guia para futuras modificações no código da aplicação.

### **Objetivo**

O app.py é um aplicativo Streamlit que serve como uma ferramenta de análise de texto. Ele é dividido em seções claras: contagens básicas, análises avançadas (frequência, análise char a char, comparação) e limpeza de texto. O código foi otimizado para uma UI intuitiva e interativa.

### **Dependências Principais**

* streamlit: Framework principal para o front-end. O código é re-executado a cada interação, o que facilita a análise em tempo real.  
* pandas: Usado para criar DataFrames que formatam os resultados das análises em tabelas, tornando-as interativas e fáceis de exportar.  
* re (built-in): Usado para expressões regulares, cruciais para a contagem de palavras, sentenças e para a limpeza do texto.  
* collections.Counter: Eficiente para a contagem de frequência de palavras e letras.

### **Design e Lógica**

1. **UI Modular:** As seções são separadas por st.markdown("---") e st.expander ou st.container, permitindo uma navegação limpa.  
2. **Lógica Otimizada:** As contagens básicas são feitas a cada interação do usuário, garantindo uma resposta rápida. As análises avançadas são disparadas apenas por um clique de botão para evitar sobrecarga de processamento.  
3. **Exportação de Dados:** O uso de pandas e io permite a criação de arquivos CSV e Excel em memória, que são então oferecidos ao usuário para download.  
4. **Limpeza de Texto:** A função de limpeza utiliza uma abordagem modular, onde cada ajuste é aplicado com base em um checkbox. O modo "Arrumar para nomes" foi cuidadosamente projetado para tratar casos especiais como preposições e "d'Ávila".

### **Pontos de Atenção para Futuras Modificações**

* **Adicionar Novas Análises:** Para adicionar uma nova análise, crie um novo st.button ou expander na seção "Análises Avançadas" e implemente a lógica correspondente. Lembre-se de usar DataFrames para exibir os resultados em formato de tabela.  
* **Melhorar a Performance:** Para textos muito longos, a análise avançada pode ser lenta. Considere implementar cache (com @st.cache\_data) se a análise for baseada em dados que não mudam frequentemente, embora para esta ferramenta não seja necessário.  
* **Expandir a Limpeza:** Novas regras de normalização ou substituição de caracteres podem ser adicionadas facilmente à função de limpeza.  
* **Interface:** A UI pode ser melhorada com customização de CSS (colocando o CSS no app.py com \<style\>\</style\>).