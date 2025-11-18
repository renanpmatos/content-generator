"""
LinkedIn Content Generator - Interface Principal
Aplicação Streamlit para geração de conteúdo para LinkedIn
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

# Imports dos nossos módulos
from core.content_generator import ContentGenerator
from core.humanizer import TextHumanizer
from core.image_finder import ImageFinder
from core.topic_suggester import TopicSuggester
from database.db_manager import DatabaseManager

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="LinkedIn Content Generator",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhorar visual
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .post-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'generated_posts' not in st.session_state:
    st.session_state.generated_posts = []
if 'selected_images' not in st.session_state:
    st.session_state.selected_images = {}
if 'config' not in st.session_state:
    # Carregar configuração
    config_path = Path("config/config.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            st.session_state.config = json.load(f)
    else:
        st.session_state.config = {
            "profile": {
                "name": "Seu Nome",
                "area": "Sua Área",
                "interests": ["Tecnologia"],
                "tone": "casual-profissional"
            }
        }

def save_config():
    """Salva configurações no arquivo."""
    config_path = Path("config/config.json")
    config_path.parent.mkdir(exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.config, f, indent=2, ensure_ascii=False)

def init_components():
    """Inicializa os componentes do sistema."""
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager()
    
    if 'generator' not in st.session_state:
        model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
        st.session_state.generator = ContentGenerator(model=model)
    
    if 'humanizer' not in st.session_state:
        model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
        st.session_state.humanizer = TextHumanizer(model=model)
    
    if 'image_finder' not in st.session_state:
        st.session_state.image_finder = ImageFinder()
    
    if 'topic_suggester' not in st.session_state:
        model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
        user_area = st.session_state.config['profile']['area']
        st.session_state.topic_suggester = TopicSuggester(model=model, user_area=user_area)

# Sidebar - Configurações
def render_sidebar():
    """Renderiza a barra lateral com configurações."""
    with st.sidebar:
        st.title("⚙️ Configurações")
        
        with st.expander("👤 Perfil", expanded=False):
            st.session_state.config['profile']['name'] = st.text_input(
                "Nome",
                value=st.session_state.config['profile']['name']
            )
            
            st.session_state.config['profile']['area'] = st.text_input(
                "Área Profissional",
                value=st.session_state.config['profile']['area']
            )
            
            st.session_state.config['profile']['tone'] = st.selectbox(
                "Tom de Voz",
                options=['formal', 'casual', 'casual-profissional'],
                index=['formal', 'casual', 'casual-profissional'].index(
                    st.session_state.config['profile']['tone']
                )
            )
            
            if st.button("💾 Salvar Configurações"):
                save_config()
                st.success("✅ Configurações salvas!")
                st.rerun()
        
        # Estatísticas
        st.divider()
        st.subheader("📊 Estatísticas")
        
        stats = st.session_state.db.get_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Posts", stats['total_posts'])
            st.metric("Publicados", stats['posted'])
        with col2:
            st.metric("Rascunhos", stats['drafts'])
            st.metric("Favoritos", stats['favorites'])

# Aba 1: Gerar Post
def render_generate_tab():
    """Renderiza a aba de geração de posts."""
    st.header("✍️ Gerar Novo Post")
    
    # Seção de sugestões de tópicos
    with st.expander("💡 Precisa de ideias? Veja sugestões de tópicos", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            suggestion_type = st.radio(
                "Tipo de sugestão",
                ["Geral", "Por categoria", "Baseado em tendência"],
                horizontal=True
            )
        
        with col2:
            num_suggestions = st.number_input("Quantidade", min_value=1, max_value=10, value=5)
        
        if suggestion_type == "Por categoria":
            category_filter = st.selectbox(
                "Categoria",
                ["dica", "experiencia", "reflexao", "pergunta"]
            )
        else:
            category_filter = None
        
        if suggestion_type == "Baseado em tendência":
            trend_keyword = st.text_input("Palavra-chave da tendência", "Inteligência Artificial")
        
        if st.button("🔍 Gerar Sugestões"):
            with st.spinner("Gerando sugestões..."):
                if suggestion_type == "Baseado em tendência":
                    suggestions = st.session_state.topic_suggester.suggest_based_on_trend(trend_keyword)
                else:
                    suggestions = st.session_state.topic_suggester.suggest_topics(
                        num_topics=num_suggestions,
                        category=category_filter if suggestion_type == "Por categoria" else None
                    )
                
                for i, suggestion in enumerate(suggestions, 1):
                    with st.container():
                        st.markdown(f"""
                        **{i}. {suggestion['topic']}**  
                        📝 {suggestion['description']}  
                        🏷️ Categoria: `{suggestion['category']}` | ⭐ Relevância: `{suggestion['relevance']}`
                        """)
                        if st.button(f"Usar este tópico", key=f"use_topic_{i}"):
                            st.session_state.selected_topic = suggestion['topic']
                            st.rerun()
    
    st.divider()
    
    # Formulário de geração
    col1, col2 = st.columns([2, 1])
    
    with col1:
        topic = st.text_area(
            "📌 Sobre o que você quer escrever?",
            value=st.session_state.get('selected_topic', ''),
            height=100,
            placeholder="Ex: Minha experiência aprendendo Python, Dicas de produtividade, etc."
        )
    
    with col2:
        category = st.selectbox(
            "🏷️ Categoria",
            ["dica", "experiencia", "reflexao", "pergunta"],
            help="Tipo de post que você quer criar"
        )
        
        tone = st.selectbox(
            "🎭 Tom",
            ["formal", "casual", "casual-profissional"],
            index=2
        )
        
        num_versions = st.slider(
            "📝 Versões",
            min_value=1,
            max_value=5,
            value=3,
            help="Quantas versões diferentes gerar"
        )
    
    # Experiência pessoal (opcional)
    with st.expander("➕ Adicionar contexto pessoal (opcional)"):
        personal_exp = st.text_area(
            "Descreva brevemente sua experiência ou contexto pessoal",
            height=100,
            placeholder="Ex: Recentemente mudei de carreira para desenvolvimento web e aprendi muito sobre..."
        )
    
    # Botão de gerar
    if st.button("🚀 Gerar Posts", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("❌ Por favor, insira um tópico!")
            return
        
        with st.spinner("🎨 Gerando conteúdo mágico..."):
            user_area = st.session_state.config['profile']['area']
            
            # Gerar versões
            versions = []
            progress_bar = st.progress(0)
            
            for i in range(num_versions):
                # Gerar post
                post = st.session_state.generator.generate_post(
                    topic=topic,
                    category=category,
                    tone=tone,
                    personal_experience=personal_exp if personal_exp.strip() else None,
                    user_area=user_area
                )
                
                # Humanizar
                humanized_result = st.session_state.humanizer.humanize_with_validation(
                    post,
                    max_attempts=2
                )
                
                # Adicionar personalidade
                final_post = st.session_state.humanizer.add_personality_touches(
                    humanized_result['text'],
                    add_emoji=(tone != 'formal'),
                    add_question=(category == 'pergunta')
                )
                
                versions.append({
                    'content': final_post,
                    'quality': humanized_result['quality_score'],
                    'ai_patterns': humanized_result['ai_patterns_found']
                })
                
                progress_bar.progress((i + 1) / num_versions)
            
            # Gerar hashtags
            hashtags = st.session_state.generator.generate_hashtags(topic, user_area)
            
            # Buscar imagens
            images = st.session_state.image_finder.search_images(topic, num_images=3)
            
            # Salvar no session state
            st.session_state.generated_posts = versions
            st.session_state.current_hashtags = hashtags
            st.session_state.current_images = images
            st.session_state.current_topic = topic
            st.session_state.current_category = category
            
            st.success("✅ Posts gerados com sucesso!")
            st.rerun()
    
    # Mostrar posts gerados
    if st.session_state.generated_posts:
        st.divider()
        st.subheader("📋 Posts Gerados")
        
        for i, post_data in enumerate(st.session_state.generated_posts, 1):
            with st.container():
                st.markdown(f"### Versão {i}")
                
                # Indicador de qualidade
                quality = post_data['quality']
                quality_colors = {
                    'excellent': '🟢',
                    'good': '🟡',
                    'needs_review': '🟠'
                }
                st.markdown(f"{quality_colors.get(quality, '⚪')} Qualidade: `{quality}`")
                
                # Mostrar post
                st.markdown("**Preview do Post:**")
                st.markdown(f'<div class="post-card">{post_data["content"]}</div>', 
                           unsafe_allow_html=True)
                
                # Hashtags
                if st.session_state.current_hashtags:
                    hashtag_str = " ".join([f"#{tag}" for tag in st.session_state.current_hashtags])
                    st.markdown(f"**Hashtags:** {hashtag_str}")
                
                # Avisos de IA (se houver)
                if post_data['ai_patterns']:
                    with st.expander("⚠️ Padrões de IA detectados"):
                        for pattern in post_data['ai_patterns']:
                            st.warning(f"• {pattern}")
                
                # Ações
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"📋 Copiar", key=f"copy_{i}"):
                        st.code(post_data['content'], language=None)
                
                with col2:
                    if st.button(f"💾 Salvar", key=f"save_{i}"):
                        post_id = st.session_state.db.save_post(
                            content=post_data['content'],
                            topic=st.session_state.current_topic,
                            category=st.session_state.current_category,
                            tone=tone,
                            hashtags=st.session_state.current_hashtags
                        )
                        
                        # Salvar imagens
                        for img in st.session_state.current_images:
                            st.session_state.db.save_image(
                                post_id=post_id,
                                url=img['url'],
                                source=img['source']
                            )
                        
                        st.success(f"✅ Post #{post_id} salvo!")
                
                with col3:
                    if st.button(f"✏️ Editar", key=f"edit_{i}"):
                        st.session_state.editing_post = post_data['content']
                        st.rerun()
                
                st.divider()
        
        # Mostrar imagens
        if st.session_state.current_images:
            st.subheader("🖼️ Imagens Sugeridas")
            
            cols = st.columns(3)
            for idx, img in enumerate(st.session_state.current_images):
                with cols[idx]:
                    st.image(img['url'], use_container_width=True)
                    st.caption(f"📷 {img['photographer']}")
                    
                    if st.button(f"⬇️ Baixar", key=f"download_img_{idx}"):
                        with st.spinner("Baixando..."):
                            filepath = st.session_state.image_finder.download_image(img)
                            if filepath:
                                st.success(f"✅ Salva em: {filepath}")

# Aba 2: Histórico
def render_history_tab():
    """Renderiza a aba de histórico."""
    st.header("📚 Histórico de Posts")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.selectbox(
            "Status",
            ["Todos", "Publicados", "Rascunhos", "Favoritos"]
        )
    
    with col2:
        filter_category = st.selectbox(
            "Categoria",
            ["Todas", "dica", "experiencia", "reflexao", "pergunta"]
        )
    
    with col3:
        sort_order = st.selectbox(
            "Ordenar por",
            ["Mais recentes", "Mais antigos"]
        )
    
    # Buscar posts
    posts = st.session_state.db.get_all_posts(limit=50)
    
    # Aplicar filtros
    if filter_status != "Todos":
        if filter_status == "Publicados":
            posts = [p for p in posts if p['posted']]
        elif filter_status == "Rascunhos":
            posts = [p for p in posts if not p['posted']]
        elif filter_status == "Favoritos":
            posts = [p for p in posts if p['favorite']]
    
    if filter_category != "Todas":
        posts = [p for p in posts if p['category'] == filter_category]
    
    if sort_order == "Mais antigos":
        posts = list(reversed(posts))
    
    # Mostrar posts
    st.write(f"**{len(posts)} post(s) encontrado(s)**")
    
    for post in posts:
        with st.expander(
            f"{'⭐' if post['favorite'] else '📄'} "
            f"{'✅' if post['posted'] else '📝'} "
            f"{post['topic'][:50]}... - {post['created_at'][:10]}"
        ):
            # Conteúdo
            st.markdown(post['content'])
            
            # Hashtags
            if post['hashtags']:
                hashtags = " ".join([f"#{tag}" for tag in post['hashtags']])
                st.markdown(f"**Hashtags:** {hashtags}")
            
            # Metadados
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"🏷️ {post['category']}")
            with col2:
                st.caption(f"🎭 {post['tone']}")
            with col3:
                st.caption(f"📅 {post['created_at'][:16]}")
            
            # Ações
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📋 Copiar", key=f"hist_copy_{post['id']}"):
                    st.code(post['content'], language=None)
            
            with col2:
                if not post['posted']:
                    if st.button("✅ Marcar como Postado", key=f"mark_{post['id']}"):
                        st.session_state.db.mark_as_posted(post['id'])
                        st.success("✅ Marcado!")
                        st.rerun()
            
            with col3:
                fav_label = "💔 Desfavoritar" if post['favorite'] else "⭐ Favoritar"
                if st.button(fav_label, key=f"fav_{post['id']}"):
                    st.session_state.db.toggle_favorite(post['id'])
                    st.rerun()
            
            with col4:
                if st.button("🗑️ Deletar", key=f"del_{post['id']}"):
                    st.session_state.db.delete_post(post['id'])
                    st.warning("🗑️ Post deletado!")
                    st.rerun()
            
            # Mostrar imagens associadas
            images = st.session_state.db.get_post_images(post['id'])
            if images:
                st.markdown("**🖼️ Imagens:**")
                img_cols = st.columns(min(len(images), 3))
                for idx, img in enumerate(images[:3]):
                    with img_cols[idx]:
                        st.image(img['url'], use_container_width=True)

# Aba 3: Programação
def render_schedule_tab():
    """Renderiza a aba de programação semanal."""
    st.header("📅 Programação Semanal")
    
    st.info("💡 Sugestões de quando e o que postar durante a semana")
    
    if st.button("🔄 Gerar Nova Programação"):
        with st.spinner("Gerando programação..."):
            schedule = st.session_state.topic_suggester.get_weekly_schedule()
            st.session_state.weekly_schedule = schedule
            st.success("✅ Programação gerada!")
    
    if 'weekly_schedule' in st.session_state:
        for day_plan in st.session_state.weekly_schedule:
            with st.expander(f"📌 {day_plan['day']} - {day_plan['category'].upper()}", expanded=True):
                st.markdown(f"**⏰ Melhor horário:** {day_plan['best_time']}")
                
                st.markdown("**💡 Sugestões:**")
                for i, topic in enumerate(day_plan['suggested_topics'][:2], 1):
                    st.markdown(f"{i}. **{topic['topic']}**")
                    st.markdown(f"   _{topic['description']}_")
                    
                    if st.button(f"Usar este tópico", key=f"sched_{day_plan['day']}_{i}"):
                        st.session_state.selected_topic = topic['topic']
                        st.session_state.selected_tab = 0  # Ir para aba de geração
                        st.rerun()

# Main
def main():
    """Função principal."""
    
    # Inicializar componentes
    init_components()
    
    # Renderizar sidebar
    render_sidebar()
    
    # Título principal
    st.title("💼 LinkedIn Content Generator")
    st.markdown("*Gere conteúdo profissional de forma rápida e autêntica*")
    
    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["✍️ Gerar Post", "📚 Histórico", "📅 Programação"])
    
    with tab1:
        render_generate_tab()
    
    with tab2:
        render_history_tab()
    
    with tab3:
        render_schedule_tab()
    
    # Footer
    st.divider()
    st.caption("💡 Dica: Sempre revise e personalize os posts antes de publicar!")

if __name__ == "__main__":
    main()
