import os
import requests
import re
import time
import streamlit as st
from docx import Document
import base64

# **📌 Obtém o caminho absoluto do script**
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "logo.png")

# **📌 Função para converter imagem para Base64 (necessário para exibição no Streamlit)**
def get_base64_of_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# **📌 Adicionando CSS personalizado para fixar a logo e melhorar o layout**
st.markdown(
    f"""
    <style>
        /* Define a posição fixa da logo no canto superior esquerdo */
        .logo-container {{
            position: fixed;
            top: 10px;
            left: 10px;
            width: 150px;
            z-index: 1000;
        }}

        /* Ajusta a margem do conteúdo para não ficar sobreposto */
        .main-content {{
            margin-left: 180px;
        }}

        /* Fundo da página */
        .main {{
            background-color: #f0f2f6;
        }}
        
        /* Cor do cabeçalho */
        .css-18e3th9 {{
            background-color: #00274D !important;
            color: white !important;
        }}

        /* Cor dos botões */
        .stButton>button {{
            background-color: #00274D !important;
            color: white !important;
            border-radius: 5px;
        }}

        /* Fonte personalizada */
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
        html, body, [class*="css"] {{
            font-family: 'Montserrat', sans-serif;
        }}
    </style>
    <div class="logo-container">
        <img src="data:image/png;base64,{get_base64_of_image(logo_path)}" width="150">
    </div>
    """,
    unsafe_allow_html=True
)

# **📌 Interface Principal**
st.markdown('<div class="main-content">', unsafe_allow_html=True)

st.title("📊 Monitoramento de Comentários do Instagram")
st.write("Insira as configurações abaixo e clique em **Executar** para analisar os comentários.")

# **Inputs do Usuário**
ACCESS_TOKEN = st.text_input("🔑 Token de Acesso (Graph API)", type="password")
IG_ACCOUNT_ID = st.text_input("🆔 ID da Conta do Instagram")
num_posts = st.number_input("📌 Quantidade de Posts a Analisar", min_value=1, max_value=500, value=25)
keywords = st.text_area("🔍 Palavras-Chave (separe por vírgula)", "CEA, C&A")

st.markdown('</div>', unsafe_allow_html=True)

# **📌 Botão para rodar o script**
if st.button("🚀 Executar Análise"):
    if not ACCESS_TOKEN or not IG_ACCOUNT_ID:
        st.error("⚠ Por favor, preencha o Token de Acesso e o ID da Conta do Instagram.")
    else:
        # Convertendo palavras-chave para lista
        keywords = [word.strip().lower() for word in keywords.split(",")]

        # **📌 Lista para armazenar os posts (ID + Link)**
        post_list = []
        log_output = []

        def log(text):
            """ Adiciona uma linha ao log e exibe na interface """
            log_output.append(text)
            st.text(text)

        # **📌 Obter IDs dos Posts Mais Recentes**
        log("\n🔍 Obtendo IDs dos posts mais recentes...")
        url_posts = f"https://graph.facebook.com/v18.0/{IG_ACCOUNT_ID}/media?fields=id,caption,media_type,permalink,timestamp&limit=25&access_token={ACCESS_TOKEN}"

        while len(post_list) < num_posts and url_posts:
            response = requests.get(url_posts)
            if response.status_code == 200:
                posts_data = response.json()
                for post in posts_data["data"]:
                    if len(post_list) >= num_posts:
                        break
                    post_list.append({"id": post["id"], "link": post["permalink"]})
                    log(f"📌 Post encontrado: {post['permalink']}")
                url_posts = posts_data.get("paging", {}).get("next")
            else:
                log(f"❌ Erro ao buscar posts: {response.json()}")
                st.error("⚠ Erro ao buscar posts! Verifique o token e o ID da conta.")
                exit()

        log(f"\n✅ Total de {len(post_list)} posts coletados!\n")

        # **📌 Dicionário para contar palavras-chave**
        keyword_count = {word: 0 for word in keywords}

        # **📌 Buscar Comentários e Respostas**
        log("🔍 Analisando comentários...")

        def analyze_comment(text, username):
            """ Analisar comentários e contar palavras-chave corretamente """
            if text:
                log(f"   💬 {username}: {text}")
                text_lower = text.lower()
                for word in keyword_count.keys():
                    occurrences = len(re.findall(fr"\b{re.escape(word)}\b", text_lower, re.IGNORECASE))
                    keyword_count[word] += occurrences  # Somar a contagem correta

        for index, post in enumerate(post_list):
            post_id = post["id"]
            post_link = post["link"]

            log(f"\n📌 Analisando Post {index+1}/{len(post_list)} - {post_link}")

            url_comments = f"https://graph.facebook.com/v18.0/{post_id}/comments?fields=id,text,username&access_token={ACCESS_TOKEN}"
            response_comments = requests.get(url_comments)

            if response_comments.status_code == 200:
                comments_data = response_comments.json()
                if "data" in comments_data and comments_data["data"]:
                    log(f"✅ {len(comments_data['data'])} comentários encontrados!")

                    for comment in comments_data["data"]:
                        comment_id = comment["id"]
                        text = comment.get("text", "")
                        username = comment.get("username", "Usuário desconhecido")

                        analyze_comment(text, username)

            time.sleep(3)

        # **📌 Criar Relatório Word**
        doc = Document()
        doc.add_heading("Relatório de Comentários do Instagram", level=1)

        for line in log_output:
            doc.add_paragraph(line)

        # **📌 Gerar Nome do Arquivo**
        keywords_str = "_".join(word.replace("&", "_") for word in keyword_count.keys())
        word_filename = f"relatorio_instagram_{keywords_str}.docx"
        doc.save(word_filename)

        log(f"\n📄 Relatório salvo como: {word_filename}")

        # **📌 Permitir Download do Relatório**
        with open(word_filename, "rb") as file:
            st.download_button("📥 Baixar Relatório Word", file, file_name=word_filename)
