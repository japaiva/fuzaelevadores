#!/usr/bin/env python3
"""
Script para buscar códigos de produtos no sistema Django Fuza Elevadores
e preencher a planilha buscacod.xlsx com os códigos encontrados.

INSTRUÇÕES DE USO:
1. Salve este arquivo como 'busca_codigo_produtos.py' na raiz do projeto Django
2. Instale dependências: pip install pandas openpyxl
3. Execute: python busca_codigo_produtos.py

Dependências:
- Django configurado
- pandas
- openpyxl
"""

import os
import sys
from pathlib import Path
import re
from difflib import SequenceMatcher

# Primeiro verificar se estamos no diretório correto
current_dir = Path(__file__).parent
manage_py = current_dir / 'manage.py'

if not manage_py.exists():
    print("✗ ERRO: Arquivo manage.py não encontrado!")
    print("Este script deve ser executado na raiz do projeto Django (onde está o manage.py)")
    print(f"Diretório atual: {current_dir}")
    sys.exit(1)

# Adicionar o diretório do projeto ao Python path
sys.path.insert(0, str(current_dir))

# Configurar Django ANTES de importar qualquer coisa do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuza_elevadores.settings')

# Verificar se o módulo de settings existe
try:
    import fuza_elevadores.settings
    print("✓ Módulo de settings encontrado")
except ImportError as e:
    print(f"✗ ERRO: Não foi possível importar fuza_elevadores.settings: {e}")
    print("Verifique se você está no diretório correto e se o projeto Django está configurado")
    sys.exit(1)

# Agora configurar o Django
import django
try:
    django.setup()
    print("✓ Django configurado com sucesso")
except Exception as e:
    print(f"✗ ERRO ao configurar Django: {e}")
    sys.exit(1)

# Agora podemos importar pandas e os modelos Django
try:
    import pandas as pd
    print("✓ Pandas importado")
except ImportError:
    print("✗ ERRO: pandas não encontrado. Execute: pip install pandas openpyxl")
    sys.exit(1)

try:
    from core.models import Produto
    print("✓ Modelo Produto importado")
except ImportError as e:
    print(f"✗ ERRO ao importar modelo Produto: {e}")
    sys.exit(1)

class BuscadorCodigoProdutos:
    """
    Classe para buscar códigos de produtos e preencher planilha
    """
    
    def normalizar_texto(self, texto):
        """Normaliza texto para comparação"""
        if pd.isna(texto) or texto is None:
            return ""
        
        texto = str(texto).strip().upper()
        # Remove acentos e caracteres especiais
        texto = re.sub(r'[ÁÀÂÃÄ]', 'A', texto)
        texto = re.sub(r'[ÉÈÊË]', 'E', texto)
        texto = re.sub(r'[ÍÌÎÏ]', 'I', texto)
        texto = re.sub(r'[ÓÒÔÕÖ]', 'O', texto)
        texto = re.sub(r'[ÚÙÛÜ]', 'U', texto)
        texto = re.sub(r'[Ç]', 'C', texto)
        # Remove pontuação e espaços extras
        texto = re.sub(r'[^\w\s]', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        return texto
    
    def calcular_similaridade(self, texto1, texto2):
        """Calcula similaridade entre dois textos"""
        return SequenceMatcher(None, 
                             self.normalizar_texto(texto1), 
                             self.normalizar_texto(texto2)).ratio()
    
    def buscar_produto_por_nome(self, nome_sugerido, produtos_cache, limite_similaridade=0.8):
        """
        Busca produto pelo nome com diferentes estratégias
        """
        if pd.isna(nome_sugerido) or not nome_sugerido:
            return None, 0, "Nome vazio"
        
        nome_normalizado = self.normalizar_texto(nome_sugerido)
        melhor_match = None
        melhor_score = 0
        metodo_usado = ""
        
        # Estratégia 1: Busca exata (ignorando case)
        for produto in produtos_cache:
            produto_nome_norm = self.normalizar_texto(produto['nome'])
            if produto_nome_norm == nome_normalizado:
                return produto, 1.0, "Busca exata"
        
        # Estratégia 2: Busca por palavras-chave principais
        palavras_chave = nome_normalizado.split()
        if len(palavras_chave) >= 2:
            for produto in produtos_cache:
                produto_nome_norm = self.normalizar_texto(produto['nome'])
                palavras_produto = produto_nome_norm.split()
                
                # Verificar se as palavras principais estão presentes
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
        
        # Estratégia 4: Busca parcial flexível (mais permissiva)
        if melhor_score < limite_similaridade:
            for produto in produtos_cache:
                score = self.calcular_similaridade(nome_sugerido, produto['nome'])
                if score > melhor_score and score >= 0.6:  # Limite mais baixo
                    melhor_match = produto
                    melhor_score = score
                    metodo_usado = "Busca parcial"
        
        return melhor_match, melhor_score, metodo_usado


def main():
    """Função principal"""
    print("\n🚀 INICIANDO BUSCA DE CÓDIGOS - SISTEMA FUZA")
    print("=" * 60)
    
    arquivo_excel = 'buscacod.xlsx'
    
    # Verificar se o arquivo Excel existe
    if not os.path.exists(arquivo_excel):
        print(f"✗ ERRO: Arquivo {arquivo_excel} não encontrado!")
        print("Certifique-se de que o arquivo está na raiz do projeto")
        return 1
    
    # 1. Carregar planilha
    try:
        df = pd.read_excel(arquivo_excel)
        print(f"✓ Planilha carregada: {len(df)} linhas")
        print(f"Colunas: {list(df.columns)}")
    except Exception as e:
        print(f"✗ Erro ao carregar planilha: {e}")
        return 1
    
    # 2. Carregar produtos do banco
    try:
        produtos_queryset = Produto.objects.filter(status='ATIVO').values(
            'codigo', 'nome', 'tipo', 'grupo__codigo', 'subgrupo__codigo'
        )
        produtos_cache = list(produtos_queryset)
        print(f"✓ {len(produtos_cache)} produtos carregados do banco")
    except Exception as e:
        print(f"✗ Erro ao carregar produtos: {e}")
        return 1
    
    # 3. Verificar/criar colunas necessárias
    if 'CODIGO' not in df.columns:
        df['CODIGO'] = None
    
    df['CODIGO_ENCONTRADO'] = None
    df['SCORE_BUSCA'] = None
    df['METODO_BUSCA'] = None
    df['STATUS_BUSCA'] = None
    
    # 4. Processar cada linha
    print(f"\n=== PROCESSANDO {len(df)} LINHAS ===")
    
    buscador = BuscadorCodigoProdutos()
    encontrados = 0
    nao_encontrados = 0
    resultado_detalhado = []
    
    for index, row in df.iterrows():
        nome_sugerido = row.get('NOME_SUGERIDO', '')
        
        if index % 10 == 0:
            print(f"Processando linha {index + 1}...")
        
        produto, score, metodo = buscador.buscar_produto_por_nome(nome_sugerido, produtos_cache)
        
        if produto and score >= 0.6:
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
            
            if score >= 0.9:
                print(f"  ✓ Linha {index + 2}: {nome_sugerido} → {codigo_encontrado} (Score: {score:.2f})")
        else:
            df.at[index, 'STATUS_BUSCA'] = 'NÃO ENCONTRADO'
            nao_encontrados += 1
    
    # 5. Mostrar estatísticas
    print(f"\n=== RESULTADO FINAL ===")
    print(f"✓ Encontrados: {encontrados}")
    print(f"✗ Não encontrados: {nao_encontrados}")
    
    total = encontrados + nao_encontrados
    if total > 0:
        taxa_sucesso = (encontrados / total) * 100
        print(f"📊 Taxa de sucesso: {taxa_sucesso:.1f}%")
    
    # 6. Salvar resultados
    try:
        # Arquivo principal com todos os dados
        arquivo_saida = 'buscacod_com_codigos.xlsx'
        df.to_excel(arquivo_saida, index=False)
        print(f"✓ Resultado completo salvo em: {arquivo_saida}")
        
        # Apenas os encontrados
        if encontrados > 0:
            df_encontrados = df[df['STATUS_BUSCA'] == 'ENCONTRADO'].copy()
            arquivo_encontrados = 'buscacod_encontrados.xlsx'
            df_encontrados.to_excel(arquivo_encontrados, index=False)
            print(f"✓ Produtos encontrados salvos em: {arquivo_encontrados}")
        
        # Apenas os não encontrados
        if nao_encontrados > 0:
            df_nao_encontrados = df[df['STATUS_BUSCA'] == 'NÃO ENCONTRADO'].copy()
            arquivo_nao_encontrados = 'buscacod_nao_encontrados.xlsx'
            df_nao_encontrados.to_excel(arquivo_nao_encontrados, index=False)
            print(f"✓ Produtos não encontrados salvos em: {arquivo_nao_encontrados}")
        
    except Exception as e:
        print(f"✗ Erro ao salvar arquivos: {e}")
        return 1
    
    # 7. Mostrar alguns exemplos
    if resultado_detalhado:
        print(f"\n=== EXEMPLOS DE PRODUTOS ENCONTRADOS ===")
        for item in resultado_detalhado[:10]:
            print(f"Linha {item['linha']}: {item['nome_sugerido']}")
            print(f"  → {item['codigo']} - {item['produto_encontrado']}")
            print(f"  → Score: {item['score']:.2f} - Método: {item['metodo']}")
            print()
    
    # 8. Estatísticas por método
    if resultado_detalhado:
        metodos = {}
        for item in resultado_detalhado:
            metodo = item['metodo']
            metodos[metodo] = metodos.get(metodo, 0) + 1
        
        print(f"\n=== ESTATÍSTICAS POR MÉTODO ===")
        for metodo, count in metodos.items():
            print(f"{metodo}: {count} produtos")
    
    print(f"\n✅ PROCESSO CONCLUÍDO!")
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Processo interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)