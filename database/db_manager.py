"""
Gerenciador do banco de dados SQLite.
Responsável por criar tabelas e fazer operações CRUD.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "database/posts.db"):
        """
        Inicializa o gerenciador de banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco SQLite
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Cria e retorna uma conexão com o banco."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
        return conn
    
    def init_database(self):
        """Cria as tabelas se não existirem."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de posts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                topic VARCHAR(255),
                category VARCHAR(50),
                tone VARCHAR(50),
                hashtags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                posted BOOLEAN DEFAULT 0,
                posted_at TIMESTAMP NULL,
                favorite BOOLEAN DEFAULT 0
            )
        """)
        
        # Tabela de imagens
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                url TEXT,
                local_path TEXT,
                source VARCHAR(50),
                selected BOOLEAN DEFAULT 0,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
            )
        """)
        
        # Tabela de histórico de tópicos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic VARCHAR(255),
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success_score INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    
    def save_post(self, content: str, topic: str, category: str, 
                  tone: str, hashtags: List[str]) -> int:
        """
        Salva um novo post no banco.
        
        Args:
            content: Conteúdo do post
            topic: Tema do post
            category: Categoria (dica, experiencia, reflexao)
            tone: Tom do post (formal, casual, profissional)
            hashtags: Lista de hashtags
            
        Returns:
            ID do post criado
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        hashtags_str = json.dumps(hashtags)
        
        cursor.execute("""
            INSERT INTO posts (content, topic, category, tone, hashtags)
            VALUES (?, ?, ?, ?, ?)
        """, (content, topic, category, tone, hashtags_str))
        
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return post_id
    
    def save_image(self, post_id: int, url: str, source: str, 
                   local_path: Optional[str] = None):
        """
        Salva informações de uma imagem associada a um post.
        
        Args:
            post_id: ID do post
            url: URL da imagem
            source: Fonte (unsplash, pexels, etc)
            local_path: Caminho local se foi baixada
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO images (post_id, url, source, local_path)
            VALUES (?, ?, ?, ?)
        """, (post_id, url, source, local_path))
        
        conn.commit()
        conn.close()
    
    def get_all_posts(self, limit: int = 50) -> List[Dict]:
        """
        Retorna todos os posts, ordenados do mais recente.
        
        Args:
            limit: Número máximo de posts a retornar
            
        Returns:
            Lista de dicionários com dados dos posts
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM posts 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        posts = []
        for row in cursor.fetchall():
            post = dict(row)
            # Converter string JSON de hashtags para lista
            post['hashtags'] = json.loads(post['hashtags']) if post['hashtags'] else []
            posts.append(post)
        
        conn.close()
        return posts
    
    def get_post_images(self, post_id: int) -> List[Dict]:
        """
        Retorna todas as imagens de um post específico.
        
        Args:
            post_id: ID do post
            
        Returns:
            Lista de dicionários com dados das imagens
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM images 
            WHERE post_id = ?
        """, (post_id,))
        
        images = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return images
    
    def mark_as_posted(self, post_id: int):
        """Marca um post como publicado."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE posts 
            SET posted = 1, posted_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (post_id,))
        
        conn.commit()
        conn.close()
    
    def toggle_favorite(self, post_id: int):
        """Alterna o status de favorito de um post."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE posts 
            SET favorite = NOT favorite 
            WHERE id = ?
        """, (post_id,))
        
        conn.commit()
        conn.close()
    
    def delete_post(self, post_id: int):
        """
        Deleta um post e suas imagens associadas.
        
        Args:
            post_id: ID do post a deletar
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # SQLite com CASCADE vai deletar imagens automaticamente
        cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """
        Retorna estatísticas sobre o uso do app.
        
        Returns:
            Dicionário com estatísticas
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total de posts
        cursor.execute("SELECT COUNT(*) as total FROM posts")
        total = cursor.fetchone()['total']
        
        # Posts publicados
        cursor.execute("SELECT COUNT(*) as posted FROM posts WHERE posted = 1")
        posted = cursor.fetchone()['posted']
        
        # Posts favoritos
        cursor.execute("SELECT COUNT(*) as favorites FROM posts WHERE favorite = 1")
        favorites = cursor.fetchone()['favorites']
        
        # Categoria mais usada
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM posts 
            GROUP BY category 
            ORDER BY count DESC 
            LIMIT 1
        """)
        top_category = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_posts': total,
            'posted': posted,
            'drafts': total - posted,
            'favorites': favorites,
            'top_category': dict(top_category) if top_category else None
        }


# Teste rápido
if __name__ == "__main__":
    db = DatabaseManager()
    print("Testando banco de dados...")
    
    # Testar salvamento
    post_id = db.save_post(
        content="Esse é um post de teste!",
        topic="Teste",
        category="dica",
        tone="casual",
        hashtags=["teste", "python"]
    )
    print(f"Post criado com ID: {post_id}")
    
    # Testar recuperação
    posts = db.get_all_posts(limit=5)
    print(f"Total de posts: {len(posts)}")
    
    # Estatísticas
    stats = db.get_stats()
    print(f"Estatísticas: {stats}")
