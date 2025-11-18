"""
Humanizador de texto gerado por IA.
Remove padrões óbvios de IA e torna o texto mais natural e pessoal.
"""

import ollama
import re
from typing import List

class TextHumanizer:
    def __init__(self, model: str = "llama3.2:3b"):
        """
        Inicializa o humanizador de texto.
        
        Args:
            model: Nome do modelo Ollama a usar
        """
        self.model = model
        self.client = ollama
        
        # Padrões comuns de IA que devemos evitar
        self.ai_patterns = [
            "é importante notar",
            "é fundamental",
            "vale ressaltar",
            "em conclusão",
            "no mundo de hoje",
            "na era digital",
            "é crucial",
            "além disso",
            "por outro lado",
            "desta forma",
            "portanto"
        ]
    
    def humanize(self, text: str, style: str = "brasileiro-casual") -> str:
        """
        Humaniza um texto gerado por IA.
        
        Aplica múltiplas técnicas:
        1. Reescrita com prompt específico
        2. Remoção de padrões de IA
        3. Adição de elementos naturais
        4. Ajuste de formatação
        
        Args:
            text: Texto original gerado por IA
            style: Estilo de humanização (brasileiro-casual, profissional, técnico)
            
        Returns:
            Texto humanizado
        """
        
        # Etapa 1: Reescrever com prompt de humanização
        humanized = self._rewrite_naturally(text, style)
        
        # Etapa 2: Aplicar transformações textuais
        humanized = self._apply_text_transformations(humanized, style)
        
        # Etapa 3: Ajustar formatação
        humanized = self._adjust_formatting(humanized)
        
        return humanized
    
    def _rewrite_naturally(self, text: str, style: str) -> str:
        """
        Usa o LLM para reescrever o texto de forma mais natural.
        
        Args:
            text: Texto original
            style: Estilo desejado
            
        Returns:
            Texto reescrito
        """
        
        style_instructions = {
            'brasileiro-casual': """
Reescreva esse texto de forma MUITO mais natural e casual, como um brasileiro escreveria:

CARACTERÍSTICAS OBRIGATÓRIAS:
- Use contrações naturais: "tá", "pra", "né", "tipo"
- Adicione expressões brasileiras: "sabe como é", "olha só", "pois é"
- Varie o tamanho das frases (algumas curtas, outras longas)
- Comece algumas frases de forma não tradicional
- Use primeira pessoa quando fizer sentido
- Seja conversacional, como se estivesse falando com um colega
- REMOVA completamente frases clichês tipo "é importante notar", "vale ressaltar"
- Adicione 1-2 emojis sutis se fizer sentido (não exagere!)

EVITE:
- Parágrafos perfeitamente estruturados
- Transições formais
- Linguagem corporativa genérica
- Listas numeradas muito organizadas
""",
            'profissional': """
Reescreva esse texto mantendo profissionalismo mas com naturalidade:

CARACTERÍSTICAS:
- Tom profissional porém acessível
- Evite jargões desnecessários
- Seja direto e claro
- Mantenha credibilidade
- Pode usar "nós", "nossa experiência"
- Sem emojis
""",
            'técnico': """
Reescreva esse texto com foco técnico mas compreensível:

CARACTERÍSTICAS:
- Pode usar termos técnicos quando apropriado
- Explique conceitos de forma clara
- Use exemplos práticos
- Mantenha precisão
- Tom educativo mas não condescendente
"""
        }
        
        style_guide = style_instructions.get(style, style_instructions['brasileiro-casual'])
        
        prompt = f"""
{style_guide}

TEXTO ORIGINAL:
{text}

IMPORTANTE: Mantenha a MESMA mensagem e ideia central, apenas torne mais natural.
Retorne APENAS o texto reescrito, sem explicações ou comentários.
"""
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.8,  # Mais criatividade para humanização
                    'top_p': 0.9,
                    'num_predict': 600
                }
            )
            
            return response['response'].strip()
            
        except Exception as e:
            print(f"❌ Erro ao humanizar texto: {e}")
            # Se falhar, retorna o texto original com transformações básicas
            return self._apply_text_transformations(text, style)
    
    def _apply_text_transformations(self, text: str, style: str) -> str:
        """
        Aplica transformações textuais diretas (não usa LLM).
        
        Args:
            text: Texto a transformar
            style: Estilo para guiar transformações
            
        Returns:
            Texto transformado
        """
        
        transformed = text
        
        # Remover padrões óbvios de IA
        for pattern in self.ai_patterns:
            # Remove a frase completa que contém o padrão
            transformed = re.sub(
                rf'[^.!?]*{re.escape(pattern)}[^.!?]*[.!?]',
                '',
                transformed,
                flags=re.IGNORECASE
            )
        
        if style == 'brasileiro-casual':
            # Substituições casuais brasileiras
            substitutions = {
                r'\bpara\b': 'pra',
                r'\bestá\b': 'tá',
                r'\bestão\b': 'tão',
                r'\bvocê está\b': 'você tá',
                r'\bnão é\b': 'não é mesmo',
                r'\be também\b': 'e também',
                # Adicionar "né" ocasionalmente no final de frases
                r'([.!?])\s+([A-Z])': r'\1 Né? \2',  # Apenas em algumas
            }
            
            for pattern, replacement in substitutions.items():
                # Aplicar algumas substituições aleatoriamente (não todas)
                if hash(pattern) % 3 == 0:  # ~33% das vezes
                    transformed = re.sub(pattern, replacement, transformed)
        
        return transformed
    
    def _adjust_formatting(self, text: str) -> str:
        """
        Ajusta formatação do texto para parecer mais natural.
        
        Args:
            text: Texto a formatar
            
        Returns:
            Texto formatado
        """
        
        # Remover espaços extras
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Garantir que parágrafos não sejam muito uniformes
        # Quebrar parágrafos muito longos ocasionalmente
        paragraphs = text.split('\n\n')
        adjusted_paragraphs = []
        
        for para in paragraphs:
            # Se parágrafo muito longo (>400 chars), considerar quebrar
            if len(para) > 400 and '.' in para:
                sentences = para.split('.')
                mid = len(sentences) // 2
                
                # Quebrar no meio
                part1 = '.'.join(sentences[:mid]) + '.'
                part2 = '.'.join(sentences[mid:])
                
                adjusted_paragraphs.append(part1.strip())
                adjusted_paragraphs.append(part2.strip())
            else:
                adjusted_paragraphs.append(para)
        
        text = '\n\n'.join(adjusted_paragraphs)
        
        # Remover espaços no início/fim
        text = text.strip()
        
        return text
    
    def add_personality_touches(self, text: str, 
                               add_emoji: bool = True,
                               add_question: bool = False) -> str:
        """
        Adiciona toques de personalidade ao texto.
        
        Args:
            text: Texto base
            add_emoji: Se deve adicionar emojis sutis
            add_question: Se deve adicionar pergunta engajadora no final
            
        Returns:
            Texto com personalidade
        """
        
        result = text
        
        # Adicionar emoji sutil no início (ocasionalmente)
        if add_emoji:
            relevant_emojis = ['💡', '🎯', '🚀', '💭', '📌', '✨', '🔍', '⚡']
            # Apenas se o texto ainda não tiver emoji
            if not any(emoji in result for emoji in relevant_emojis):
                # 50% de chance de adicionar
                if hash(text) % 2 == 0:
                    emoji = relevant_emojis[hash(text) % len(relevant_emojis)]
                    result = f"{emoji} {result}"
        
        # Adicionar pergunta engajadora no final
        if add_question:
            if not result.endswith('?'):
                questions = [
                    "\n\nE você, o que acha disso?",
                    "\n\nJá passou por algo parecido?",
                    "\n\nConcorda? Discorda?",
                    "\n\nQual sua experiência com isso?",
                    "\n\nO que você faria diferente?"
                ]
                question = questions[hash(text) % len(questions)]
                result += question
        
        return result
    
    def detect_ai_patterns(self, text: str) -> List[str]:
        """
        Detecta padrões típicos de IA no texto.
        Útil para validação.
        
        Args:
            text: Texto a analisar
            
        Returns:
            Lista de padrões encontrados
        """
        
        found_patterns = []
        
        for pattern in self.ai_patterns:
            if pattern.lower() in text.lower():
                found_patterns.append(pattern)
        
        # Verificar outros sinais
        # 1. Muitas listas numeradas
        if len(re.findall(r'\n\d+\.', text)) > 3:
            found_patterns.append("excesso de listas numeradas")
        
        # 2. Parágrafos muito uniformes
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        if paragraphs:
            lengths = [len(p) for p in paragraphs]
            avg_length = sum(lengths) / len(lengths)
            # Se todos parágrafos muito similares em tamanho
            if all(abs(l - avg_length) < 50 for l in lengths):
                found_patterns.append("parágrafos muito uniformes")
        
        # 3. Ausência de contrações (para português casual)
        if len(text) > 100:
            contractions = ['tá', 'pra', 'né', 'tipo', 'que nem']
            if not any(c in text.lower() for c in contractions):
                found_patterns.append("falta de contrações naturais")
        
        return found_patterns
    
    def humanize_with_validation(self, text: str, 
                                 max_attempts: int = 3) -> dict:
        """
        Humaniza o texto e valida o resultado.
        Tenta novamente se detectar muitos padrões de IA.
        
        Args:
            text: Texto original
            max_attempts: Máximo de tentativas
            
        Returns:
            Dict com texto humanizado e métricas
        """
        
        best_result = text
        best_score = float('inf')  # Quanto menor, melhor
        
        for attempt in range(max_attempts):
            print(f"Tentativa de humanização {attempt + 1}/{max_attempts}...")
            
            # Humanizar
            humanized = self.humanize(text, style="brasileiro-casual")
            
            # Validar
            ai_patterns_found = self.detect_ai_patterns(humanized)
            score = len(ai_patterns_found)
            
            if score < best_score:
                best_result = humanized
                best_score = score
            
            # Se score perfeito, pode parar
            if score == 0:
                print("✅ Texto perfeitamente humanizado!")
                break
        
        return {
            'text': best_result,
            'ai_patterns_found': self.detect_ai_patterns(best_result),
            'attempts': attempt + 1,
            'quality_score': 'excellent' if best_score == 0 else 'good' if best_score < 3 else 'needs_review'
        }


# Teste
if __name__ == "__main__":
    print("🧪 Testando humanizador de texto...")
    
    humanizer = TextHumanizer()
    
    # Texto de exemplo (muito "IA")
    ai_text = """
É importante notar que a organização de código é fundamental para o desenvolvimento de software de qualidade. No mundo de hoje, onde a complexidade dos sistemas cresce exponencialmente, é crucial manter um código limpo e bem estruturado.

Além disso, vale ressaltar que existem várias metodologias que podem auxiliar nesse processo. Por outro lado, cada projeto possui suas particularidades. Portanto, é essencial adaptar as práticas ao contexto específico.

Em conclusão, investir em organização de código traz benefícios significativos para toda a equipe de desenvolvimento.
"""
    
    print("\n📄 TEXTO ORIGINAL (muito IA):")
    print("="*60)
    print(ai_text)
    print("="*60)
    
    # Detectar padrões de IA
    print("\n🔍 PADRÕES DE IA DETECTADOS:")
    patterns = humanizer.detect_ai_patterns(ai_text)
    for pattern in patterns:
        print(f"  ❌ {pattern}")
    
    # Humanizar com validação
    print("\n🎨 HUMANIZANDO...")
    result = humanizer.humanize_with_validation(ai_text, max_attempts=2)
    
    print("\n✨ TEXTO HUMANIZADO:")
    print("="*60)
    print(result['text'])
    print("="*60)
    
    print(f"\n📊 QUALIDADE: {result['quality_score']}")
    print(f"🔄 TENTATIVAS: {result['attempts']}")
    
    if result['ai_patterns_found']:
        print("\n⚠️  Padrões de IA ainda encontrados:")
        for pattern in result['ai_patterns_found']:
            print(f"  - {pattern}")
    else:
        print("\n✅ Nenhum padrão de IA detectado!")
    
    # Teste 2: Adicionar personalidade
    print("\n" + "="*60)
    print("\n🎭 ADICIONANDO PERSONALIDADE...")
    with_personality = humanizer.add_personality_touches(
        result['text'],
        add_emoji=True,
        add_question=True
    )
    print(with_personality)
