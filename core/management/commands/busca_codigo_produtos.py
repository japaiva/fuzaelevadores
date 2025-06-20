# core/management/commands/buscar_codigos.py

"""
Django Management Command para buscar códigos de produtos

Uso:
python manage.py buscar_codigos
python manage.py buscar_codigos --arquivo outro_arquivo.xlsx
python manage.py buscar_codigos --verbose
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import pandas as pd
import re
from difflib import SequenceMatcher
from core.models import Produto
import os

class Command(BaseCommand):
    help = 'Busca códigos de produtos na planilha buscacod.xlsx'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--arquivo',
            type=str,
            default='buscacod.xlsx',
            help='Nome do arquivo Excel (padrão: buscacod.xlsx)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostra informações detalhadas durante o processo'
        )
        parser.add_argument(
            '--limite',
            type=float,
            default=0.6,
            help='Limite mínimo de similaridade (0.0 a 1.0, padrão: 0.6)'
        )
    
    def normalizar_texto(self, texto):
        """Normaliza texto para comparação"""
        if pd.isna(texto) or texto is None:
            return ""
        
        texto = str(texto).strip().upper()
        
        # Remove acentos
        replacements = {
            'Á': 'A', 'À': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
            'Ó': 'O', 'Ò': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
            'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ç': 'C'
        }
        
        for old, new in replacements.items():
            texto = texto.replace(old, new)
        
        # Remove pontuação e normaliza espaços
        texto = re.sub(r'[^\w\s]', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        return texto
    
    def calcular_similaridade(self, texto1, texto2):
        """Calcula similaridade entre dois textos"""
        return SequenceMatcher(None, 
                             self.normalizar_texto(texto1), 
                             self.normalizar_texto(texto2)).ratio()
    
    def buscar_produto_por_nome(self, nome_sugerido, produtos_cache, limite_similaridade=0.6):
        """Busca produto pelo nome com diferentes estratégias"""
        if pd.isna(nome_sugerido) or not nome_sugerido:
            return None, 0, "Nome vazio"
        
        nome_normalizado = self.normalizar_texto(nome_sugerido)
        melhor_match = None
        melhor_score = 0
        metodo_usado = ""
        
        # Estratégia 1: Busca exata
        for produto in produtos_cache:
            produto_nome_norm = self.normalizar_texto(produto['nome'])
            if produto_nome_norm == nome_normalizado:
                return produto, 1.0, "Busca exata"
        
        # Estratégia 2: Busca por palavras-chave principais
        palavras_chave = nome_normalizado.split()
        if len(palavras_chave) >= 2:
            for produto in produtos_cache:
                produto_nome_norm = self.normalizar_texto(produto['nome'])
                
                matches = 0
                for palavra in palavras_chave[:3]:  # Usar até 3 palavras principais
                    if len(palavra) > 2 and palavra in produto_nome_norm:
                        matches += 1
                
                if matches >= min(2, len(palavras_chave)):
                    score = matches / len(palavras_chave)
                    if score > melhor_score:
                        melhor_match = produto
                        melhor_score = score
                        metodo_usado = "Palavras-chave"
        
        # Estratégia 3: Similaridade fuzzy
        for produto in produtos_cache:
            score = self.calcular_similaridade(nome_sugerido, produto['nome'])
            if score > melhor_score and score >= limite_similaridade:
                melhor_match = produto
                melhor_score = score
                metodo_usado = "Similaridade fuzzy"
        
        # Estratégia 4: Busca parcial (mais permissiva)
        if melhor_score < limite_similaridade:
            limite_baixo = max(0.5, limite_similaridade - 0.1)
            for produto in produtos_cache:
                score = self.calcular_similaridade(nome_sugerido, produto['nome'])
                if score > melhor_score and score >= limite_baixo:
                    melhor_match = produto
                    melhor_score = score
                    metodo_usado = "Busca parcial"
        
        return melhor_match, melhor_score, metodo_usado
    
    def handle(self, *args, **options):
        arquivo = options['arquivo']
        verbose = options['verbose']
        limite = options['limite']
        
        self.stdout.write("🚀 INICIANDO BUSCA DE CÓDIGOS - SISTEMA FUZA")
        self.stdout.write("=" * 60)
        
        # Verificar se arquivo existe
        if not os.path.exists(arquivo):
            self.stdout.write(
                self.style.ERROR(f"✗ Arquivo não encontrado: {arquivo}")
            )
            return
        
        # 1. Carregar planilha
        try:
            df = pd.read_excel(arquivo)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Planilha carregada: {len(df)} linhas")
            )
            if verbose:
                self.stdout.write(f"Colunas: {list(df.columns)}")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erro ao carregar planilha: {e}")
            )
            return
        
        # 2. Carregar produtos do banco
        try:
            produtos_queryset = Produto.objects.filter(
                status='ATIVO'
            ).values('codigo', 'nome', 'tipo', 'grupo__codigo', 'subgrupo__codigo')
            
            produtos_cache = list(produtos_queryset)
            self.stdout.write(
                self.style.SUCCESS(f"✓ {len(produtos_cache)} produtos carregados do banco")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erro ao carregar produtos: {e}")
            )
            return
        
        # 3. Verificar/criar colunas necessárias
        if 'CODIGO' not in df.columns:
            df['CODIGO'] = None
        
        df['CODIGO_ENCONTRADO'] = None
        df['SCORE_BUSCA'] = None
        df['METODO_BUSCA'] = None
        df['STATUS_BUSCA'] = None
        
        # 4. Processar cada linha
        self.stdout.write(f"\n=== PROCESSANDO {len(df)} LINHAS ===")
        
        encontrados = 0
        nao_encontrados = 0
        resultado_detalhado = []
        
        for index, row in df.iterrows():
            nome_sugerido = row.get('NOME_SUGERIDO', '')
            
            if verbose and index % 10 == 0:
                self.stdout.write(f"Processando linha {index + 1}...")
            
            produto, score, metodo = self.buscar_produto_por_nome(
                nome_sugerido, produtos_cache, limite
            )
            
            if produto and score >= limite:
                codigo_encontrado = produto['codigo']
                df.at[index, 'CODIGO'] = codigo_encontrado
                df.at[index, 'CODIGO_ENCONTRADO'] = codigo_encontrado
                df.at[index, 'SCORE_BUSCA'] = f"{score:.2f}"
                df.at[index, 'METODO_BUSCA'] = metodo
                df.at[index, 'STATUS_BUSCA'] = 'ENCONTRADO'
                
                encontrados += 1
                
                resultado_detalhado.append({
                    'linha': index + 2,
                    'nome_sugerido': nome_sugerido,
                    'produto_encontrado': produto['nome'],
                    'codigo': codigo_encontrado,
                    'score': score,
                    'metodo': metodo
                })
                
                if verbose and score >= 0.9:
                    self.stdout.write(
                        f"  ✓ Linha {index + 2}: {nome_sugerido} → {codigo_encontrado} (Score: {score:.2f})"
                    )
            else:
                df.at[index, 'STATUS_BUSCA'] = 'NÃO ENCONTRADO'
                nao_encontrados += 1
                
                if verbose and nome_sugerido:
                    self.stdout.write(
                        f"  ✗ Linha {index + 2}: {nome_sugerido} (Score máximo: {score:.2f})"
                    )
        
        # 5. Mostrar estatísticas
        self.stdout.write(f"\n=== RESULTADO FINAL ===")
        self.stdout.write(
            self.style.SUCCESS(f"✓ Encontrados: {encontrados}")
        )
        self.stdout.write(
            self.style.WARNING(f"✗ Não encontrados: {nao_encontrados}")
        )
        
        total = encontrados + nao_encontrados
        if total > 0:
            taxa_sucesso = (encontrados / total) * 100
            self.stdout.write(f"📊 Taxa de sucesso: {taxa_sucesso:.1f}%")
        
        # 6. Salvar resultados
        try:
            # Arquivo principal com todos os dados
            base_name = arquivo.replace('.xlsx', '')
            arquivo_saida = f'{base_name}_com_codigos.xlsx'
            df.to_excel(arquivo_saida, index=False)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Resultado completo salvo em: {arquivo_saida}")
            )
            
            # Apenas os encontrados
            if encontrados > 0:
                df_encontrados = df[df['STATUS_BUSCA'] == 'ENCONTRADO'].copy()
                arquivo_encontrados = f'{base_name}_encontrados.xlsx'
                df_encontrados.to_excel(arquivo_encontrados, index=False)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Produtos encontrados salvos em: {arquivo_encontrados}")
                )
            
            # Apenas os não encontrados
            if nao_encontrados > 0:
                df_nao_encontrados = df[df['STATUS_BUSCA'] == 'NÃO ENCONTRADO'].copy()
                arquivo_nao_encontrados = f'{base_name}_nao_encontrados.xlsx'
                df_nao_encontrados.to_excel(arquivo_nao_encontrados, index=False)
                self.stdout.write(
                    self.style.WARNING(f"✓ Produtos não encontrados salvos em: {arquivo_nao_encontrados}")
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erro ao salvar arquivos: {e}")
            )
            return
        
        # 7. Mostrar alguns exemplos se verbose
        if verbose and resultado_detalhado:
            self.stdout.write(f"\n=== EXEMPLOS DE PRODUTOS ENCONTRADOS ===")
            for item in resultado_detalhado[:5]:  # Mostrar apenas os primeiros 5
                self.stdout.write(f"Linha {item['linha']}: {item['nome_sugerido']}")
                self.stdout.write(f"  → {item['codigo']} - {item['produto_encontrado']}")
                self.stdout.write(f"  → Score: {item['score']:.2f} - Método: {item['metodo']}")
                self.stdout.write("")
        
        # 8. Estatísticas por método
        if resultado_detalhado:
            metodos = {}
            for item in resultado_detalhado:
                metodo = item['metodo']
                metodos[metodo] = metodos.get(metodo, 0) + 1
            
            self.stdout.write(f"\n=== ESTATÍSTICAS POR MÉTODO ===")
            for metodo, count in metodos.items():
                self.stdout.write(f"{metodo}: {count} produtos")
        
        self.stdout.write(
            self.style.SUCCESS("\n✅ PROCESSO CONCLUÍDO!")
        )