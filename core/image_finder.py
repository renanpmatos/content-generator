"""
Buscador de imagens para complementar posts do LinkedIn.
Busca em APIs gratuitas como Unsplash e Pexels.
"""

import requests
import os
from typing import List, Dict, Optional
from pathlib import Path
from PIL import Image
from io import BytesIO
import hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class ImageFinder:
    def __init__(self, 
                 unsplash_key: Optional[str] = None,
                 pexels_key: Optional[str] = None):
        """
        Inicializa o buscador de imagens.
        
        Args:
            unsplash_key: Chave de API do Unsplash (opcional)
            pexels_key: Chave de API do Pexels (opcional)
        """
        self.unsplash_key = unsplash_key or os.getenv('UNSPLASH_ACCESS_KEY')
        self.pexels_key = pexels_key or os.getenv('PEXELS_API_KEY')
        
        # Diretório para salvar imagens
        self.images_dir = Path("assets/downloaded_images")
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # URLs das APIs
        self.unsplash_url = "https://api.unsplash.com/search/photos"
        self.pexels_url = "https://api.pexels.com/v1/search"
        
        print(f"🖼️  ImageFinder inicializado")
        print(f"   Unsplash: {'✅ Configurado' if self.unsplash_key else '⚠️  Sem chave (modo limitado)'}")
        print(f"   Pexels: {'✅ Configurado' if self.pexels_key else '⚠️  Sem chave (modo limitado)'}")
    
    def search_images(self, 
                     query: str, 
                     num_images: int = 3,
                     orientation: str = "landscape") -> List[Dict]:
        """
        Busca imagens em múltiplas fontes.
        
        Args:
            query: Termo de busca (em inglês funciona melhor)
            num_images: Número de imagens a retornar
            orientation: 'landscape', 'portrait' ou 'squarish'
            
        Returns:
            Lista de dicionários com informações das imagens
        """
        
        all_images = []
        
        # Traduzir query para inglês (melhor resultados)
        query_en = self._translate_to_english(query)
        
        # Tentar Unsplash primeiro (melhor qualidade)
        if self.unsplash_key:
            try:
                unsplash_images = self._search_unsplash(query_en, num_images, orientation)
                all_images.extend(unsplash_images)
                print(f"✅ Encontradas {len(unsplash_images)} imagens no Unsplash")
            except Exception as e:
                print(f"⚠️  Erro no Unsplash: {e}")
        
        # Se não tiver suficientes, buscar no Pexels
        if len(all_images) < num_images and self.pexels_key:
            try:
                remaining = num_images - len(all_images)
                pexels_images = self._search_pexels(query_en, remaining, orientation)
                all_images.extend(pexels_images)
                print(f"✅ Encontradas {len(pexels_images)} imagens no Pexels")
            except Exception as e:
                print(f"⚠️  Erro no Pexels: {e}")
        
        # Se ainda não tiver nenhuma, usar fallback
        if not all_images:
            print("⚠️  Usando imagens de fallback")
            all_images = self._get_fallback_images(query, num_images)
        
        return all_images[:num_images]
    
    def _search_unsplash(self, query: str, num_images: int, 
                        orientation: str) -> List[Dict]:
        """
        Busca imagens no Unsplash.
        
        Args:
            query: Termo de busca
            num_images: Quantidade
            orientation: Orientação
            
        Returns:
            Lista de imagens
        """
        
        headers = {
            'Authorization': f'Client-ID {self.unsplash_key}'
        }
        
        params = {
            'query': query,
            'per_page': num_images,
            'orientation': orientation,
            'content_filter': 'high'  # Apenas conteúdo apropriado
        }
        
        response = requests.get(self.unsplash_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        images = []
        for photo in data.get('results', []):
            images.append({
                'id': photo['id'],
                'url': photo['urls']['regular'],  # Tamanho médio
                'url_full': photo['urls']['full'],
                'url_thumb': photo['urls']['thumb'],
                'width': photo['width'],
                'height': photo['height'],
                'photographer': photo['user']['name'],
                'photographer_url': photo['user']['links']['html'],
                'source': 'unsplash',
                'download_location': photo['links']['download_location']  # Para tracking
            })
        
        return images
    
    def _search_pexels(self, query: str, num_images: int,
                      orientation: str) -> List[Dict]:
        """
        Busca imagens no Pexels.
        
        Args:
            query: Termo de busca
            num_images: Quantidade
            orientation: Orientação
            
        Returns:
            Lista de imagens
        """
        
        headers = {
            'Authorization': self.pexels_key
        }
        
        params = {
            'query': query,
            'per_page': num_images,
            'orientation': orientation
        }
        
        response = requests.get(self.pexels_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        images = []
        for photo in data.get('photos', []):
            images.append({
                'id': photo['id'],
                'url': photo['src']['large'],
                'url_full': photo['src']['original'],
                'url_thumb': photo['src']['medium'],
                'width': photo['width'],
                'height': photo['height'],
                'photographer': photo['photographer'],
                'photographer_url': photo['photographer_url'],
                'source': 'pexels'
            })
        
        return images
    
    def _translate_to_english(self, text: str) -> str:
        """
        Tradução simples de termos comuns PT->EN.
        Para queries mais complexas, pode integrar API de tradução.
        
        Args:
            text: Texto em português
            
        Returns:
            Texto em inglês (aproximado)
        """
        
        # Dicionário de traduções comuns para termos técnicos
        translations = {
            'programação': 'programming',
            'código': 'code',
            'tecnologia': 'technology',
            'computador': 'computer',
            'trabalho': 'work',
            'escritório': 'office',
            'negócios': 'business',
            'equipe': 'team',
            'reunião': 'meeting',
            'sucesso': 'success',
            'inovação': 'innovation',
            'criatividade': 'creativity',
            'aprendizado': 'learning',
            'educação': 'education',
            'liderança': 'leadership',
            'estratégia': 'strategy',
            'desenvolvimento': 'development',
            'análise': 'analysis',
            'dados': 'data',
            'inteligência artificial': 'artificial intelligence',
            'machine learning': 'machine learning',
            'python': 'python',
            'javascript': 'javascript',
        }
        
        text_lower = text.lower()
        
        # Verificar se alguma tradução se aplica
        for pt, en in translations.items():
            if pt in text_lower:
                return en
        
        # Se não encontrar, retornar original (muitas palavras são similares)
        return text
    
    def _get_fallback_images(self, query: str, num_images: int) -> List[Dict]:
        """
        Retorna imagens de fallback quando APIs não estão disponíveis.
        Usa placeholders ou imagens genéricas.
        
        Args:
            query: Query original (para gerar placeholder relevante)
            num_images: Quantidade
            
        Returns:
            Lista de imagens placeholder
        """
        
        fallback_images = []
        
        # Usar serviço de placeholder (Picsum Photos - gratuito, sem API key)
        for i in range(num_images):
            # Gerar um "seed" baseado na query para consistência
            seed = hashlib.md5(f"{query}{i}".encode()).hexdigest()[:10]
            
            fallback_images.append({
                'id': f'fallback_{i}',
                'url': f'https://picsum.photos/seed/{seed}/1200/630',
                'url_full': f'https://picsum.photos/seed/{seed}/1920/1080',
                'url_thumb': f'https://picsum.photos/seed/{seed}/400/300',
                'width': 1200,
                'height': 630,
                'photographer': 'Picsum Photos',
                'photographer_url': 'https://picsum.photos',
                'source': 'picsum',
                'is_placeholder': True
            })
        
        return fallback_images
    
    def download_image(self, image_info: Dict, 
                      custom_filename: Optional[str] = None) -> Optional[str]:
        """
        Baixa uma imagem e salva localmente.
        
        Args:
            image_info: Dicionário com informações da imagem
            custom_filename: Nome customizado (opcional)
            
        Returns:
            Caminho do arquivo salvo ou None se falhar
        """
        
        try:
            # Fazer request da imagem
            response = requests.get(image_info['url'], timeout=10)
            response.raise_for_status()
            
            # Abrir imagem com Pillow
            img = Image.open(BytesIO(response.content))
            
            # Gerar nome do arquivo
            if custom_filename:
                filename = custom_filename
            else:
                # Usar timestamp + ID da imagem
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = 'jpg'  # Padrão
                filename = f"{timestamp}_{image_info['id']}.{ext}"
            
            # Criar subdiretório por mês
            month_dir = self.images_dir / datetime.now().strftime("%Y-%m")
            month_dir.mkdir(exist_ok=True)
            
            filepath = month_dir / filename
            
            # Otimizar e salvar imagem
            img = self._optimize_image(img)
            img.save(filepath, 'JPEG', quality=85, optimize=True)
            
            print(f"✅ Imagem salva: {filepath}")
            
            # Trigger download tracking (para Unsplash)
            if image_info['source'] == 'unsplash' and 'download_location' in image_info:
                self._track_unsplash_download(image_info['download_location'])
            
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Erro ao baixar imagem: {e}")
            return None
    
    def _optimize_image(self, img: Image.Image) -> Image.Image:
        """
        Otimiza imagem para uso no LinkedIn.
        Tamanho ideal: 1200x627 pixels (ratio 1.91:1)
        
        Args:
            img: Imagem PIL
            
        Returns:
            Imagem otimizada
        """
        
        # Tamanho ideal para LinkedIn
        target_width = 1200
        target_height = 627
        
        # Converter para RGB se necessário
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Calcular novo tamanho mantendo aspecto
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            # Imagem mais larga - ajustar pela altura
            new_height = target_height
            new_width = int(new_height * img_ratio)
        else:
            # Imagem mais alta - ajustar pela largura
            new_width = target_width
            new_height = int(new_width / img_ratio)
        
        # Redimensionar
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop para tamanho exato (centralizado)
        if img.width > target_width or img.height > target_height:
            left = (img.width - target_width) // 2
            top = (img.height - target_height) // 2
            right = left + target_width
            bottom = top + target_height
            
            img = img.crop((left, top, right, bottom))
        
        return img
    
    def _track_unsplash_download(self, download_location: str):
        """
        Tracking obrigatório do Unsplash (termos de uso).
        
        Args:
            download_location: URL de tracking fornecida pela API
        """
        try:
            headers = {
                'Authorization': f'Client-ID {self.unsplash_key}'
            }
            requests.get(download_location, headers=headers)
        except:
            pass  # Não crítico se falhar
    
    def get_attribution_text(self, image_info: Dict) -> str:
        """
        Gera texto de atribuição para o fotógrafo.
        Importante para respeitar termos de uso.
        
        Args:
            image_info: Informações da imagem
            
        Returns:
            Texto de atribuição
        """
        
        photographer = image_info.get('photographer', 'Unknown')
        source = image_info.get('source', 'unknown')
        
        if source == 'unsplash':
            return f"📷 Foto: {photographer} (Unsplash)"
        elif source == 'pexels':
            return f"📷 Foto: {photographer} (Pexels)"
        else:
            return f"📷 Foto: {photographer}"


# Teste
if __name__ == "__main__":
    print("🧪 Testando buscador de imagens...")
    
    # Criar instância (sem chaves por enquanto - usará fallback)
    finder = ImageFinder()
    
    # Teste 1: Buscar imagens
    print("\n🔍 Teste 1: Buscar imagens sobre 'tecnologia'")
    images = finder.search_images(
        query="tecnologia",
        num_images=3,
        orientation="landscape"
    )
    
    print(f"\n📊 Encontradas {len(images)} imagens:")
    for i, img in enumerate(images, 1):
        print(f"\n   Imagem {i}:")
        print(f"   - URL: {img['url'][:60]}...")
        print(f"   - Fonte: {img['source']}")
        print(f"   - Fotógrafo: {img['photographer']}")
        print(f"   - Tamanho: {img['width']}x{img['height']}")
        
        # Gerar atribuição
        attribution = finder.get_attribution_text(img)
        print(f"   - Atribuição: {attribution}")
    
    # Teste 2: Baixar primeira imagem
    if images:
        print("\n💾 Teste 2: Baixar primeira imagem...")
        filepath = finder.download_image(images[0])
        if filepath:
            print(f"✅ Imagem salva em: {filepath}")
        
        # Verificar se arquivo existe
        if filepath and os.path.exists(filepath):
            print(f"✅ Arquivo confirmado: {os.path.getsize(filepath)} bytes")
    
    print("\n" + "="*60)
    print("\n💡 IMPORTANTE:")
    print("Para usar Unsplash e Pexels com melhor qualidade:")
    print("1. Crie conta gratuita em:")
    print("   - https://unsplash.com/developers")
    print("   - https://www.pexels.com/api/")
    print("2. Adicione as chaves no arquivo .env:")
    print("   UNSPLASH_ACCESS_KEY=sua_chave")
    print("   PEXELS_API_KEY=sua_chave")
    print("\nPor enquanto, usando imagens de fallback (Picsum).")
