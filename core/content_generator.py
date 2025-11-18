"""
Gerador de conteúdo usando Ollama.
Responsável por criar posts baseados em tópicos ou experiências.
"""

import ollama
import json
from typing import Dict, List, Optional

class ContentGenerator:
    def __init__(self, model: str = "llama3.2:3b"):
        """
        Inicializa o gerador de conteúdo.
        
        Args:
            model: Nome do modelo Ollama a usar
        """
        self.model = model
        self.client = ollama
        
        # Verificar se modelo está disponível
        try:
            models = ollama.list()
            model_names = [m['name'] for m in models.get('models', [])]
            if model not in model_names:
                print(f"⚠️  Modelo {model} não encontrado!")
                print(f"Modelos disponíveis: {model_names}")
        except Exception as e:
            print(f"⚠️  Erro ao verificar modelos: {e}")
    
    def generate_post(self, 
                     topic: str,
                     category: str = "dica",
                     tone: str = "casual-profissional",
                     personal_experience: Optional[str] = None,
                     user_area: str = "Tecnologia") -> str:
        """
        Gera um post do LinkedIn baseado nos parâmetros.
        
        Args:
            topic: Tema principal do post
            category: Tipo de post (dica, experiencia, reflexao, pergunta)
            tone: Tom do post (formal, casual, casual-profissional)
            personal_experience: Experiência pessoal opcional para incluir
            user_area: Área de atuação do usuário
            
        Returns:
            Texto do post gerado
        """
        
        # Construir o prompt baseado na categoria
        prompt = self._build_prompt(topic, category, tone, personal_experience, user_area)
        
        try:
            # Fazer a chamada para o Ollama
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.7,  # Criatividade moderada
                    'top_p': 0.9,
                    'num_predict': 500   # Máximo de tokens
                }
            )
            
            content = response['response'].strip()
            return content
            
        except Exception as e:
            print(f"❌ Erro ao gerar conteúdo: {e}")
            return ""
    
    def _build_prompt(self, topic: str, category: str, tone: str, 
                     personal_experience: Optional[str], user_area: str) -> str:
        """
        Constrói o prompt otimizado para cada tipo de post.
        
        Args:
            topic: Tema do post
            category: Categoria do post
            tone: Tom desejado
            personal_experience: Experiência pessoal
            user_area: Área profissional
            
        Returns:
            Prompt formatado
        """
        
        # Definir características do tom
        tone_instructions = {
            'formal': 'Use linguagem profissional e técnica. Evite gírias.',
            'casual': 'Use linguagem descontraída, pode usar gírias leves e emojis ocasionais.',
            'casual-profissional': 'Equilibre profissionalismo com naturalidade. Seja acessível mas competente.'
        }
        
        tone_guide = tone_instructions.get(tone, tone_instructions['casual-profissional'])
        
        # Templates base por categoria
        category_templates = {
            'dica': f"""
Você é um profissional de {user_area} escrevendo um post no LinkedIn.

TAREFA: Escrever uma DICA PRÁTICA sobre: {topic}

INSTRUÇÕES:
- Comece direto no ponto, sem introduções genéricas
- Dê uma dica ESPECÍFICA e APLICÁVEL
- Use exemplos concretos se possível
- Mantenha entre 100-150 palavras
- {tone_guide}
- NÃO use frases clichês como "no mundo de hoje", "é fundamental"
- Termine com uma pergunta ou call-to-action sutil

{self._add_experience_context(personal_experience)}

Escreva APENAS o post, sem títulos ou explicações extras.
""",
            
            'experiencia': f"""
Você é um profissional de {user_area} compartilhando uma experiência no LinkedIn.

TAREFA: Contar uma EXPERIÊNCIA sobre: {topic}

INSTRUÇÕES:
- Use storytelling: conte o que aconteceu
- Seja específico sobre contexto, desafio e resultado
- Mostre aprendizado ou insight obtido
- Mantenha entre 120-180 palavras
- {tone_guide}
- Use primeira pessoa (eu/meu/minha)
- Seja autêntico, não exagere

{self._add_experience_context(personal_experience)}

Escreva APENAS o post, sem títulos ou explicações extras.
""",
            
            'reflexao': f"""
Você é um profissional de {user_area} compartilhando uma reflexão no LinkedIn.

TAREFA: Escrever uma REFLEXÃO sobre: {topic}

INSTRUÇÕES:
- Apresente uma perspectiva ou opinião interessante
- Baseie-se em observações ou tendências
- Provoque pensamento, não apenas afirme o óbvio
- Mantenha entre 100-140 palavras
- {tone_guide}
- Pode questionar status quo ou trazer ângulo diferente
- Termine provocando reflexão no leitor

{self._add_experience_context(personal_experience)}

Escreva APENAS o post, sem títulos ou explicações extras.
""",
            
            'pergunta': f"""
Você é um profissional de {user_area} fazendo uma pergunta engajadora no LinkedIn.

TAREFA: Fazer uma PERGUNTA sobre: {topic}

INSTRUÇÕES:
- Dê contexto breve antes da pergunta (2-3 frases)
- Faça uma pergunta ESPECÍFICA, não genérica
- A pergunta deve gerar discussão interessante
- Mantenha entre 80-120 palavras
- {tone_guide}
- Evite perguntas de sim/não, prefira abertas
- Demonstre genuína curiosidade

{self._add_experience_context(personal_experience)}

Escreva APENAS o post, sem títulos ou explicações extras.
"""
        }
        
        return category_templates.get(category, category_templates['dica'])
    
    def _add_experience_context(self, experience: Optional[str]) -> str:
        """Adiciona contexto de experiência pessoal ao prompt."""
        if experience:
            return f"\nCONTEXTO PESSOAL DO AUTOR:\n{experience}\n\nIncorpore esse contexto naturalmente no post."
        return ""
    
    def generate_hashtags(self, topic: str, user_area: str, max_tags: int = 5) -> List[str]:
        """
        Gera hashtags relevantes para o post.
        
        Args:
            topic: Tema do post
            user_area: Área profissional
            max_tags: Número máximo de hashtags
            
        Returns:
            Lista de hashtags (sem o #)
        """
        
        prompt = f"""
Gere {max_tags} hashtags RELEVANTES para um post do LinkedIn sobre: {topic}
Área profissional: {user_area}

REGRAS:
- Hashtags em português brasileiro
- Sem espaços, use PascalCase se necessário (#DesenvolvedorPython)
- Mix de hashtags específicas e populares
- Relevantes para o tema E para a área
- NÃO use # no início

Retorne APENAS as hashtags separadas por vírgula.
Exemplo: Python, Programacao, DesenvolvimentoWeb, TecnologiaBrasil, CarreiraTech
"""
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={'temperature': 0.5, 'num_predict': 100}
            )
            
            tags_text = response['response'].strip()
            # Limpar e processar
            tags = [tag.strip().replace('#', '') for tag in tags_text.split(',')]
            tags = [tag for tag in tags if tag]  # Remover vazios
            
            return tags[:max_tags]
            
        except Exception as e:
            print(f"❌ Erro ao gerar hashtags: {e}")
            return ["LinkedIn", "Tecnologia", user_area.replace(' ', '')]
    
    def generate_multiple_versions(self, topic: str, category: str, 
                                   tone: str, user_area: str, 
                                   num_versions: int = 3) -> List[str]:
        """
        Gera múltiplas versões de um post.
        
        Args:
            topic: Tema do post
            category: Categoria
            tone: Tom
            user_area: Área profissional
            num_versions: Quantas versões gerar
            
        Returns:
            Lista de posts gerados
        """
        versions = []
        
        for i in range(num_versions):
            print(f"Gerando versão {i+1}/{num_versions}...")
            post = self.generate_post(topic, category, tone, None, user_area)
            if post:
                versions.append(post)
        
        return versions


# Teste
if __name__ == "__main__":
    print("🧪 Testando gerador de conteúdo...")
    
    generator = ContentGenerator()
    
    # Teste 1: Gerar post simples
    print("\n📝 Teste 1: Post de dica")
    post = generator.generate_post(
        topic="Como organizar melhor o código Python",
        category="dica",
        tone="casual-profissional",
        user_area="Desenvolvedor Python"
    )
    print(post)
    print("\n" + "="*50)
    
    # Teste 2: Gerar hashtags
    print("\n🏷️  Teste 2: Hashtags")
    hashtags = generator.generate_hashtags(
        topic="Organização de código Python",
        user_area="Desenvolvedor Python"
    )
    print(", ".join([f"#{tag}" for tag in hashtags]))
