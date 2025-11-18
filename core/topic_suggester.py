"""
Sugestor de tópicos para posts do LinkedIn.
Gera ideias baseadas em:
- Área de atuação do usuário
- Tendências
- Calendário de datas relevantes
- Histórico de posts
"""

import ollama
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

class TopicSuggester:
    def __init__(self, 
                 model: str = "llama3.2:3b",
                 user_area: str = "Tecnologia"):
        """
        Inicializa o sugestor de tópicos.
        
        Args:
            model: Nome do modelo Ollama
            user_area: Área de atuação do usuário
        """
        self.model = model
        self.client = ollama
        self.user_area = user_area
        
        # Carregar calendário de datas especiais
        self.special_dates = self._load_special_dates()
        
        print(f"💡 TopicSuggester inicializado para área: {user_area}")
    
    def suggest_topics(self, 
                      num_topics: int = 5,
                      category: Optional[str] = None,
                      avoid_recent: bool = True) -> List[Dict]:
        """
        Sugere tópicos para posts.
        
        Args:
            num_topics: Número de tópicos a sugerir
            category: Filtrar por categoria específica (opcional)
            avoid_recent: Evitar tópicos usados recentemente
            
        Returns:
            Lista de dicionários com tópicos sugeridos
        """
        
        suggestions = []
        
        # 1. Verificar datas especiais de hoje
        today_topics = self._get_today_special_topics()
        if today_topics:
            suggestions.extend(today_topics)
            print(f"📅 {len(today_topics)} tópico(s) especial(is) de hoje")
        
        # 2. Gerar tópicos com IA
        remaining = num_topics - len(suggestions)
        if remaining > 0:
            ai_topics = self._generate_ai_topics(remaining, category)
            suggestions.extend(ai_topics)
            print(f"🤖 {len(ai_topics)} tópico(s) gerado(s) por IA")
        
        # 3. Adicionar metadados
        for topic in suggestions:
            topic['suggested_at'] = datetime.now().isoformat()
            topic['user_area'] = self.user_area
        
        return suggestions[:num_topics]
    
    def _get_today_special_topics(self) -> List[Dict]:
        """
        Retorna tópicos baseados em datas especiais de hoje.
        
        Returns:
            Lista de tópicos relacionados a datas especiais
        """
        today = datetime.now()
        today_key = today.strftime("%m-%d")  # Formato: "11-18"
        
        topics = []
        
        # Verificar se hoje tem alguma data especial
        if today_key in self.special_dates:
            for event in self.special_dates[today_key]:
                topics.append({
                    'topic': f"{event['name']} - Como isso impacta {self.user_area}",
                    'description': event['description'],
                    'category': 'reflexao',
                    'relevance': 'high',
                    'source': 'calendar',
                    'event_name': event['name']
                })
        
        # Verificar datas próximas (próximos 3 dias)
        for i in range(1, 4):
            future_date = today + timedelta(days=i)
            future_key = future_date.strftime("%m-%d")
            
            if future_key in self.special_dates:
                for event in self.special_dates[future_key]:
                    topics.append({
                        'topic': f"Preparando para {event['name']}",
                        'description': f"Em {i} dia(s): {event['description']}",
                        'category': 'dica',
                        'relevance': 'medium',
                        'source': 'calendar_upcoming',
                        'event_name': event['name'],
                        'days_until': i
                    })
        
        return topics
    
    def _generate_ai_topics(self, num_topics: int, 
                           category: Optional[str] = None) -> List[Dict]:
        """
        Gera tópicos usando IA.
        
        Args:
            num_topics: Quantidade de tópicos
            category: Categoria específica (opcional)
            
        Returns:
            Lista de tópicos gerados
        """
        
        category_filter = f"da categoria '{category}'" if category else ""
        
        prompt = f"""
Você é um assistente especializado em gerar ideias de conteúdo para LinkedIn.

CONTEXTO:
- Área profissional: {self.user_area}
- Data atual: {datetime.now().strftime("%d/%m/%Y")}
- Objetivo: Gerar {num_topics} ideias de posts {category_filter}

INSTRUÇÕES:
1. Gere {num_topics} ideias ESPECÍFICAS e PRÁTICAS
2. Cada ideia deve ser relevante para profissionais de {self.user_area}
3. Varie entre temas técnicos e comportamentais
4. Evite tópicos muito genéricos ou clichês
5. Pense em tendências atuais da área

CATEGORIAS DISPONÍVEIS:
- dica: Dicas práticas e conselhos aplicáveis
- experiencia: Histórias e cases pessoais
- reflexao: Opiniões e análises sobre tendências
- pergunta: Perguntas para gerar discussão

Retorne APENAS um JSON array com este formato:
[
  {{
    "topic": "Título do tópico específico",
    "description": "Breve descrição do que abordar (1 frase)",
    "category": "dica|experiencia|reflexao|pergunta",
    "relevance": "high|medium",
    "angle": "Ângulo único ou perspectiva diferente"
  }}
]

IMPORTANTE: Retorne APENAS o JSON, sem explicações extras.
"""
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.8,  # Mais criatividade
                    'num_predict': 800
                }
            )
            
            # Extrair JSON da resposta
            response_text = response['response'].strip()
            
            # Remover possíveis markdown ou texto extra
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            # Parse JSON
            topics = json.loads(response_text.strip())
            
            # Adicionar metadados
            for topic in topics:
                topic['source'] = 'ai_generated'
            
            return topics
            
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao parsear JSON: {e}")
            print(f"Resposta recebida: {response_text[:200]}")
            return self._get_fallback_topics(num_topics)
        except Exception as e:
            print(f"❌ Erro ao gerar tópicos: {e}")
            return self._get_fallback_topics(num_topics)
    
    def _get_fallback_topics(self, num_topics: int) -> List[Dict]:
        """
        Retorna tópicos de fallback caso a IA falhe.
        
        Args:
            num_topics: Quantidade de tópicos
            
        Returns:
            Lista de tópicos genéricos mas úteis
        """
        
        fallback_topics = [
            {
                'topic': f'Principais tendências em {self.user_area} para 2024-2025',
                'description': 'Analise as tendências emergentes na sua área',
                'category': 'reflexao',
                'relevance': 'high',
                'source': 'fallback'
            },
            {
                'topic': f'Minha jornada de aprendizado em {self.user_area}',
                'description': 'Compartilhe sua trajetória e lições aprendidas',
                'category': 'experiencia',
                'relevance': 'high',
                'source': 'fallback'
            },
            {
                'topic': f'3 erros comuns que iniciantes cometem em {self.user_area}',
                'description': 'Ajude outros profissionais evitando armadilhas',
                'category': 'dica',
                'relevance': 'medium',
                'source': 'fallback'
            },
            {
                'topic': 'Como equilibrar vida pessoal e profissional',
                'description': 'Compartilhe estratégias de work-life balance',
                'category': 'reflexao',
                'relevance': 'medium',
                'source': 'fallback'
            },
            {
                'topic': f'Qual habilidade em {self.user_area} você mais valoriza?',
                'description': 'Inicie uma discussão sobre competências essenciais',
                'category': 'pergunta',
                'relevance': 'medium',
                'source': 'fallback'
            },
            {
                'topic': 'Ferramenta/recurso que mudou minha produtividade',
                'description': 'Recomende uma ferramenta útil que você usa',
                'category': 'dica',
                'relevance': 'high',
                'source': 'fallback'
            },
            {
                'topic': f'Desafios atuais em {self.user_area} e como superá-los',
                'description': 'Discuta obstáculos da área e possíveis soluções',
                'category': 'reflexao',
                'relevance': 'high',
                'source': 'fallback'
            }
        ]
        
        return fallback_topics[:num_topics]
    
    def _load_special_dates(self) -> Dict:
        """
        Carrega calendário de datas especiais.
        
        Returns:
            Dicionário com datas especiais {MM-DD: [eventos]}
        """
        
        # Datas relevantes para profissionais (especialmente tech)
        special_dates = {
            # Janeiro
            "01-01": [{"name": "Ano Novo", "description": "Planejamento e metas para o ano"}],
            
            # Fevereiro
            "02-11": [{"name": "Dia Internacional das Mulheres e Meninas na Ciência", 
                      "description": "Diversidade em STEM"}],
            
            # Março
            "03-08": [{"name": "Dia Internacional da Mulher", 
                      "description": "Mulheres no mercado de trabalho"}],
            
            # Abril
            "04-22": [{"name": "Dia da Terra", "description": "Sustentabilidade e tecnologia verde"}],
            "04-28": [{"name": "Dia Mundial da Segurança e Saúde no Trabalho", 
                      "description": "Bem-estar no ambiente profissional"}],
            
            # Maio
            "05-01": [{"name": "Dia do Trabalho", "description": "Reflexões sobre o mundo do trabalho"}],
            "05-17": [{"name": "Dia Mundial das Telecomunicações", 
                      "description": "Conectividade e transformação digital"}],
            
            # Junho
            "06-05": [{"name": "Dia Mundial do Meio Ambiente", 
                      "description": "Tecnologia e sustentabilidade"}],
            
            # Julho
            "07-17": [{"name": "Dia Mundial dos Emojis", "description": "Comunicação digital"}],
            
            # Agosto
            "08-19": [{"name": "Dia Mundial da Fotografia", 
                      "description": "Visual storytelling profissional"}],
            
            # Setembro
            "09-05": [{"name": "Dia da Amazônia", "description": "Tecnologia e preservação ambiental"}],
            "09-13": [{"name": "Dia do Programador", 
                      "description": "Celebração dos desenvolvedores (256º dia do ano)"}],
            
            # Outubro
            "10-05": [{"name": "Dia dos Professores", "description": "Educação e compartilhamento de conhecimento"}],
            "10-24": [{"name": "Dia do Desenvolvedor", "description": "Profissionais de desenvolvimento"}],
            
            # Novembro
            "11-20": [{"name": "Dia da Consciência Negra", 
                      "description": "Diversidade e inclusão no trabalho"}],
            
            # Dezembro
            "12-03": [{"name": "Dia Internacional da Pessoa com Deficiência", 
                      "description": "Acessibilidade e inclusão"}],
        }
        
        return special_dates
    
    def get_weekly_schedule(self) -> List[Dict]:
        """
        Gera uma programação semanal de posts sugeridos.
        
        Returns:
            Lista com sugestões para cada dia da semana
        """
        
        schedule = []
        days = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
        categories = ['dica', 'experiencia', 'reflexao', 'dica', 'pergunta']
        
        for day, category in zip(days, categories):
            topics = self.suggest_topics(num_topics=2, category=category)
            
            schedule.append({
                'day': day,
                'category': category,
                'suggested_topics': topics,
                'best_time': self._get_best_posting_time(day)
            })
        
        return schedule
    
    def _get_best_posting_time(self, day: str) -> str:
        """
        Retorna horário sugerido para postar baseado no dia.
        
        Args:
            day: Dia da semana
            
        Returns:
            Horário sugerido
        """
        
        # Baseado em estudos de engajamento no LinkedIn
        best_times = {
            'Segunda': '08:00 - 09:00',
            'Terça': '09:00 - 10:00',
            'Quarta': '08:00 - 09:00',
            'Quinta': '09:00 - 10:00',
            'Sexta': '08:00 - 09:00'
        }
        
        return best_times.get(day, '08:00 - 10:00')
    
    def suggest_based_on_trend(self, trend_keyword: str) -> List[Dict]:
        """
        Gera tópicos baseados em uma tendência ou palavra-chave específica.
        
        Args:
            trend_keyword: Palavra-chave da tendência
            
        Returns:
            Lista de tópicos relacionados
        """
        
        prompt = f"""
Gere 3 ideias de posts para LinkedIn sobre a tendência: "{trend_keyword}"

CONTEXTO:
- Área profissional: {self.user_area}
- Perspectiva: Como essa tendência impacta profissionais da área

INSTRUÇÕES:
- Seja específico e prático
- Conecte a tendência com a realidade de {self.user_area}
- Varie as categorias (dica, reflexao, pergunta)

Retorne APENAS um JSON array:
[
  {{
    "topic": "Título específico conectando {trend_keyword} com {self.user_area}",
    "description": "O que abordar",
    "category": "dica|reflexao|pergunta",
    "relevance": "high",
    "angle": "Perspectiva única"
  }}
]
"""
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={'temperature': 0.7, 'num_predict': 500}
            )
            
            response_text = response['response'].strip()
            
            # Limpar markdown
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            
            topics = json.loads(response_text.strip())
            
            for topic in topics:
                topic['source'] = 'trend_based'
                topic['trend_keyword'] = trend_keyword
            
            return topics
            
        except Exception as e:
            print(f"❌ Erro ao gerar tópicos de tendência: {e}")
            return [{
                'topic': f'{trend_keyword} e o impacto em {self.user_area}',
                'description': f'Análise sobre como {trend_keyword} está mudando a área',
                'category': 'reflexao',
                'relevance': 'high',
                'source': 'trend_fallback',
                'trend_keyword': trend_keyword
            }]
    
    def expand_topic(self, topic: str) -> Dict:
        """
        Expande um tópico simples em uma estrutura completa com sugestões.
        
        Args:
            topic: Tópico básico
            
        Returns:
            Dicionário com tópico expandido e sugestões de abordagem
        """
        
        prompt = f"""
Expanda este tópico para um post do LinkedIn: "{topic}"

CONTEXTO:
- Área: {self.user_area}

Retorne JSON:
{{
  "topic": "{topic}",
  "expanded_title": "Título mais específico e chamativo",
  "key_points": ["ponto 1", "ponto 2", "ponto 3"],
  "suggested_structure": "Como estruturar o post",
  "call_to_action": "CTA sugerido",
  "category": "dica|experiencia|reflexao|pergunta"
}}
"""
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={'temperature': 0.6, 'num_predict': 400}
            )
            
            response_text = response['response'].strip()
            
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            
            return json.loads(response_text.strip())
            
        except Exception as e:
            print(f"❌ Erro ao expandir tópico: {e}")
            return {
                'topic': topic,
                'expanded_title': topic,
                'key_points': ['Introduzir o tema', 'Desenvolver a ideia', 'Concluir'],
                'suggested_structure': 'Estrutura livre',
                'call_to_action': 'Compartilhe sua opinião nos comentários',
                'category': 'reflexao'
            }


# Teste
if __name__ == "__main__":
    print("🧪 Testando sugestor de tópicos...")
    
    suggester = TopicSuggester(user_area="Desenvolvedor Python")
    
    # Teste 1: Sugestões gerais
    print("\n💡 Teste 1: Sugestões gerais (5 tópicos)")
    print("="*60)
    topics = suggester.suggest_topics(num_topics=5)
    
    for i, topic in enumerate(topics, 1):
        print(f"\n{i}. {topic['topic']}")
        print(f"   📝 {topic['description']}")
        print(f"   🏷️  Categoria: {topic['category']}")
        print(f"   ⭐ Relevância: {topic['relevance']}")
        print(f"   📍 Fonte: {topic['source']}")
    
    # Teste 2: Sugestões por categoria
    print("\n\n💡 Teste 2: Apenas 'dicas' (3 tópicos)")
    print("="*60)
    dicas = suggester.suggest_topics(num_topics=3, category="dica")
    
    for i, topic in enumerate(dicas, 1):
        print(f"\n{i}. {topic['topic']}")
        print(f"   📝 {topic['description']}")
    
    # Teste 3: Programação semanal
    print("\n\n📅 Teste 3: Programação semanal")
    print("="*60)
    schedule = suggester.get_weekly_schedule()
    
    for day_schedule in schedule:
        print(f"\n{day_schedule['day']} ({day_schedule['category'].upper()})")
        print(f"⏰ Melhor horário: {day_schedule['best_time']}")
        print(f"💡 Sugestão: {day_schedule['suggested_topics'][0]['topic']}")
    
    # Teste 4: Baseado em tendência
    print("\n\n🔥 Teste 4: Tópicos baseados em tendência")
    print("="*60)
    trend_topics = suggester.suggest_based_on_trend("Inteligência Artificial Generativa")
    
    for i, topic in enumerate(trend_topics, 1):
        print(f"\n{i}. {topic['topic']}")
        print(f"   📝 {topic['description']}")
    
    # Teste 5: Expandir tópico
    print("\n\n📖 Teste 5: Expandir tópico simples")
    print("="*60)
    expanded = suggester.expand_topic("Clean Code em Python")
    
    print(f"\nTópico original: {expanded['topic']}")
    print(f"Título expandido: {expanded['expanded_title']}")
    print(f"\nPontos-chave:")
    for point in expanded['key_points']:
        print(f"  • {point}")
    print(f"\nEstrutura sugerida: {expanded['suggested_structure']}")
    print(f"CTA: {expanded['call_to_action']}")
