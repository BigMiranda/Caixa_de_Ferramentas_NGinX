# Gerador de Senhas e Hashes + Validador de senhas

Este projeto gera senhas e hashes usando Streamlit e BCrypt. Ele permite gerar senhas aleatórias baseadas em nomes e criar hashes de senhas fornecidas pelo usuário. Também validar se uma senha acessa um hash, ambos fornecidos pelo usuário.

## 🚀 Como Rodar com Docker Compose

### 1️⃣ Clonar o Repositório
```sh
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo
```

### 2️⃣ Rodar o Projeto com Docker Compose
```sh
docker compose up -d
```

### 3️⃣ Acessar a Aplicação no Navegador
```
http://localhost:8501
```

---

## 🛠 Como Rodar Sem Docker
Se preferir rodar sem Docker, siga os passos abaixo:

### 1️⃣ Instalar as Dependências
```sh
pip install -r requirements.txt
```

### 2️⃣ Rodar o Streamlit
```sh
streamlit run app.py
```

### 3️⃣ Acessar no Navegador
```
http://localhost:8501
```

---

## 📌 Funcionalidades

### ✅ Gerar Senha e Hash
- Entrada: `Código;Nome`
- Saída: Senha gerada automaticamente + Hash BCrypt
- Opção para **baixar os resultados em Excel**

### ✅ Gerar Hash de Senha Existente
- Entrada: `Código;Senha`
- Saída: Apenas o **hash da senha informada**
- Opção para **baixar os resultados em Excel**

---

## 📜 Estrutura do Projeto
```
/meu-projeto-streamlit
│── app.py                 # Código principal Streamlit
│── Dockerfile             # Arquivo para Docker
│── docker-compose.yml     # Arquivo para Docker Compose
│── requirements.txt       # Dependências do Python
│── README.md              # Documentação do projeto
```

---

## 📌 Tecnologias Utilizadas
- **Streamlit** - Interface Web
- **BCrypt** - Hashing Seguro de Senhas
- **Pandas** - Manipulação de Dados
- **Docker & Docker Compose** - Containerização e Deploy

---

## 📖 Licença
Este projeto é de código aberto e pode ser utilizado livremente.

Se precisar de suporte, abra uma issue no repositório! 🚀

