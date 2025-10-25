# deletar_produtos_massa.py
"""
Script para deletar produtos em massa
Com produtos já definidos no código - SEM necessidade de arquivo Excel

USO: python deletar_produtos_massa.py

REQUISITOS:
- Django configurado
- Backup do banco feito
"""

import os
import sys
import django
from pathlib import Path

# ===================================================================
# CONFIGURAR DJANGO
# ===================================================================
DJANGO_PROJECT_PATH = Path(__file__).resolve().parent
sys.path.append(str(DJANGO_PROJECT_PATH))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuza_elevadores.settings')
django.setup()

# ===================================================================
# IMPORTS DJANGO
# ===================================================================
from core.models import Produto
from django.db import transaction

# ===================================================================
# LISTA DE CÓDIGOS PARA DELETAR - 78 PRODUTOS
# ===================================================================
CODIGOS_PARA_DELETAR = [
    "01.01.00009",  # CHAPA GALVANIZADA #14 1.95MM
    "01.01.00010",  # CHAPA GALVANIZADA #14 1.9MM
    "01.01.00011",  # CHAPA GALVANIZADA #14 2MM 1200X3000
    "01.01.00016",  # CHAPA INOX 430 1.2MM
    "01.01.00020",  # CHAPA XADREZ 3.00MM 1200X3000
    "01.03.00005",  # BARRA ROSCADA 1/2" - 3M ZINCADA
    "01.03.00009",  # EIXO LINEAR 40MM - 2M
    "01.04.00006",  # PARAFUSO AUTOBROCANTE 4.2X13MM
    "01.04.00009",  # PARAFUSO CONJUNTO 1/4"
    "01.04.00013",  # PARAFUSO FRANCÊS CONJUNTO
    "01.04.00014",  # PARAFUSO PANELA PHILIPS 3/16"X2.1/2"
    "01.04.00016",  # PARAFUSO SEXTAVADO 1/4"X7/8"
    "01.04.00022",  # CHUMBADOR CBJ COM PARAFUSO MAQUINA
    "01.05.00007",  # DISCO DE CORTE 4"
    "01.05.00008",  # DISCO DE CORTE 7"
    "01.05.00013",  # ELETRODO 3.25MM HEAVY DUTY
    "02.01.00001",  # CABO 0.75MM AMARELO - 100M
    "02.01.00003",  # CABO 0.75MM AZUL - 100M
    "02.01.00005",  # CABO 0.75MM BRANCO - 100M
    "02.01.00007",  # CABO 0.75MM CINZA - 100M
    "02.01.00011",  # CABO 0.75MM PRETO - 100M
    "02.01.00013",  # CABO 0.75MM VERDE - 100M
    "02.01.00015",  # CABO 0.75MM VERMELHO - 100M
    "02.01.00023",  # CABO PP 2X0.75MM PRETO - 100M
    "02.01.00026",  # CABO PP 3X0.75MM PRETO - 100M
    "02.02.00007",  # QUADRO COMANDO MCXR-VF 15HP 220V
    "02.03.00008",  # IPD ALFAN PBSX-VM 20MM
    "02.03.00010",  # IPD MATRIZ PMC-02-VM 16P
    "02.04.00003",  # FINAL DE CURSO
    "02.06.00011",  # FUSÍVEL VIDRO 10A
    "03.01.00002",  # CLIPS GUIA T50
    "03.01.00004",  # GUIA CONTRAPESO
    "03.01.00005",  # GUIA ELEVADOR
    "03.01.00011",  # GUIA T50 COMPLETA - 5M
    "03.01.00012",  # GUIA T50 COMPLETA - 5M
    "03.01.00013",  # GUIA T50 COMPLETA - 5M
    "03.01.00014",  # GUIA T50 COMPLETA - 5M
    "03.01.00015",  # GUIA T50 COMPLETA COM CLIPS - 5M
    "03.01.00016",  # GUIA T50 COMPLETA REFILADA - 5M
    "03.01.00017",  # GUIA T50 COMPLETA REFILADA - 5M
    "03.01.00018",  # GUIA T50 CONTRAPESO COMPLETA - 5M
    "03.01.00020",  # GUIA T70 CABINA COMPLETA - 5M
    "03.01.00021",  # GUIA T70 COMPLETA - 5M
    "03.01.00022",  # GUIA T70 COMPLETA - 5M
    "03.01.00023",  # GUIA T70 COMPLETA COM CLIPS - 5M
    "03.01.00024",  # GUIA T70 COMPLETA REFILADA - 5M
    "03.01.00025",  # GUIA T70 COMPLETA REFILADA - 5M
    "03.01.00027",  # GUIA T89 CABINA COMPLETA - 5M
    "03.01.00028",  # GUIA T89 COMPLETA - 5M
    "03.01.00029",  # GUIA T89 COMPLETA - 5M
    "03.01.00030",  # GUIA T89 COMPLETA - 5M
    "03.01.00031",  # GUIA T89 COMPLETA COM CLIPS - 5M
    "03.02.00003",  # CORREDIÇA CABINA T89
    "03.02.00004",  # CORREDIÇA CONTRAPESO 5MM
    "03.02.00008",  # CORREDIÇA SUPORTE GUIA 5MM T50
    "03.02.00010",  # SUPORTE GUIA
    "03.02.00011",  # SUPORTE GUIA CONTRAPESO
    "03.03.00007",  # ROLAMENTO 6208-2RS1 SKF
    "03.04.00006",  # CABO DE AÇO POLIDO 3/8"
    "03.04.00007",  # CABO DE FREIO 5/16"
    "03.04.00013",  # CLIPS TIRANTE 3/8"
    "03.04.00014",  # GUIA CABO DE AÇO (BOLACHA)
    "03.04.00018",  # TIRANTE COM MOLA 3/8"
    "03.04.00019",  # TIRANTE COMPLETO 3/8"
    "03.05.00002",  # FREIO INSTANTÂNEO COMPLETO 1.60M
    "03.05.00004",  # LIMITADOR VELOCIDADE 0.75-45M/MIN
    "03.05.00007",  # LIMITADOR VELOCIDADE 60M/MIN
    "03.05.00008",  # POLIA TENSORA LIMITADOR 5/16"
    "03.05.00009",  # POLIA TENSORA LIMITADOR 5/16"
    "03.05.00010",  # POLIA TENSORA LIMITADOR 5/16"
    "03.06.000007", # SUPORTE CONTRAPESO
    "03.06.00005",  # PEDRA CONTRAPESO GRANDE
    "03.06.00008",  # SUPORTE CONTRAPESO ESPECIAL
    "99.03.00013",  # MALETA FERRAMENTAS
    "99.03.00014",  # MALETA FERRAMENTAS
    "99.03.00029",  # BROCA SDS PLUS 19.0MM X 210MM
    "99.03.00034",  # JOGO DE CHAVE ALLEN
    "99.05.00004",  # GARRAFÃO TÉRMICO 5L
]

# ===================================================================
# CORES PARA TERMINAL
# ===================================================================
class Cores:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(texto):
    print(f"\n{Cores.HEADER}{Cores.BOLD}{'='*70}")
    print(f"{texto}")
    print(f"{'='*70}{Cores.ENDC}\n")

def print_success(texto):
    print(f"{Cores.OKGREEN}✅ {texto}{Cores.ENDC}")

def print_warning(texto):
    print(f"{Cores.WARNING}⚠️  {texto}{Cores.ENDC}")

def print_error(texto):
    print(f"{Cores.FAIL}❌ {texto}{Cores.ENDC}")

def print_info(texto):
    print(f"{Cores.OKCYAN}ℹ️  {texto}{Cores.ENDC}")

# ===================================================================
# FUNÇÃO: CARREGAR DADOS DO BANCO
# ===================================================================
def carregar_dados():
    """Carrega e valida os produtos do banco de dados"""
    print_info(f"Buscando {len(CODIGOS_PARA_DELETAR)} produtos no banco...")
    
    produtos_para_deletar = []
    produtos_nao_encontrados = []
    produtos_utilizados = []
    
    # Buscar cada produto
    for codigo in CODIGOS_PARA_DELETAR:
        try:
            produto = Produto.objects.get(codigo=codigo)
            
            # Verificar relacionamentos perigosos
            tem_pedidos = hasattr(produto, 'itens_pedido') and produto.itens_pedido.exists()
            tem_orcamentos = hasattr(produto, 'itens_orcamento') and produto.itens_orcamento.exists()
            tem_requisicoes = hasattr(produto, 'itens_requisicao') and produto.itens_requisicao.exists()
            
            produtos_para_deletar.append({
                'codigo': codigo,
                'nome': produto.nome,
                'tipo': produto.tipo,
                'custo_material': produto.custo_material or 0,
                'custo_servico': produto.custo_servico or 0,
                'utilizado': produto.utilizado,
                'status': produto.status,
                'objeto': produto,
                'tem_pedidos': tem_pedidos,
                'tem_orcamentos': tem_orcamentos,
                'tem_requisicoes': tem_requisicoes,
            })
            
            if produto.utilizado:
                produtos_utilizados.append({
                    'codigo': codigo,
                    'nome': produto.nome,
                    'tem_pedidos': tem_pedidos,
                    'tem_orcamentos': tem_orcamentos,
                    'tem_requisicoes': tem_requisicoes,
                })
                
        except Produto.DoesNotExist:
            produtos_nao_encontrados.append(codigo)
    
    print_success(f"Busca concluída: {len(produtos_para_deletar)} produtos encontrados\n")
    
    return {
        'para_deletar': produtos_para_deletar,
        'nao_encontrados': produtos_nao_encontrados,
        'utilizados': produtos_utilizados,
    }

# ===================================================================
# FUNÇÃO: SIMULAÇÃO
# ===================================================================
def executar_simulacao(dados):
    """Executa simulação e mostra relatório detalhado"""
    
    print_header("SIMULAÇÃO - ANÁLISE DOS PRODUTOS")
    
    para_deletar = dados['para_deletar']
    nao_encontrados = dados['nao_encontrados']
    utilizados = dados['utilizados']
    
    # Total de produtos no banco
    total_banco = Produto.objects.count()
    
    # Estatísticas gerais
    print(f"📊 {Cores.BOLD}ESTATÍSTICAS GERAIS:{Cores.ENDC}")
    print(f"   Total de produtos no banco: {Cores.OKBLUE}{total_banco}{Cores.ENDC}")
    print(f"   Produtos na lista para deletar: {len(CODIGOS_PARA_DELETAR)}")
    print(f"   Produtos encontrados: {Cores.OKGREEN}{len(para_deletar)}{Cores.ENDC}")
    print(f"   Produtos NÃO encontrados: {Cores.WARNING}{len(nao_encontrados)}{Cores.ENDC}")
    print(f"   Após deleção: {Cores.OKGREEN}{total_banco - len(para_deletar)}{Cores.ENDC} produtos")
    print(f"   Percentual deletado: {Cores.WARNING}{(len(para_deletar)/total_banco*100):.1f}%{Cores.ENDC}")
    
    # Agrupar por tipo
    por_tipo = {}
    custo_total = 0
    com_custo = 0
    sem_custo = 0
    
    for p in para_deletar:
        # Por tipo
        tipo = p['tipo']
        if tipo not in por_tipo:
            por_tipo[tipo] = []
        por_tipo[tipo].append(p)
        
        # Custos
        custo = p['custo_material'] + p['custo_servico']
        custo_total += custo
        if custo > 0:
            com_custo += 1
        else:
            sem_custo += 1
    
    print(f"\n💰 {Cores.BOLD}ANÁLISE DE CUSTOS:{Cores.ENDC}")
    print(f"   Produtos com custo: {com_custo}")
    print(f"   Produtos sem custo: {sem_custo}")
    print(f"   Valor total cadastrado: {Cores.WARNING}R$ {custo_total:,.2f}{Cores.ENDC}")
    
    print(f"\n📁 {Cores.BOLD}DISTRIBUIÇÃO POR TIPO:{Cores.ENDC}")
    for tipo, produtos in sorted(por_tipo.items()):
        print(f"   {tipo}: {len(produtos)} produtos")
    
    # Produtos não encontrados
    if nao_encontrados:
        print(f"\n{Cores.WARNING}{Cores.BOLD}⚠️  PRODUTOS NÃO ENCONTRADOS NO BANCO ({len(nao_encontrados)}):{Cores.ENDC}")
        for codigo in nao_encontrados:
            print(f"   • {codigo}")
    
    # Produtos utilizados (ATENÇÃO ESPECIAL)
    if utilizados:
        print(f"\n{Cores.FAIL}{Cores.BOLD}🔥 ATENÇÃO: PRODUTOS UTILIZADOS QUE SERÃO DELETADOS:{Cores.ENDC}")
        for item in utilizados:
            avisos = []
            if item['tem_pedidos']:
                avisos.append('TEM PEDIDOS')
            if item['tem_orcamentos']:
                avisos.append('TEM ORÇAMENTOS')
            if item['tem_requisicoes']:
                avisos.append('TEM REQUISIÇÕES')
            
            aviso_str = f" [{', '.join(avisos)}]" if avisos else ""
            print(f"   • {item['codigo']} - {item['nome']}{Cores.FAIL}{aviso_str}{Cores.ENDC}")
    
    # Produtos com relacionamentos
    com_relacionamentos = [p for p in para_deletar if p['tem_pedidos'] or p['tem_orcamentos'] or p['tem_requisicoes']]
    if com_relacionamentos:
        print(f"\n{Cores.FAIL}{Cores.BOLD}🔗 PRODUTOS COM RELACIONAMENTOS ({len(com_relacionamentos)}):{Cores.ENDC}")
        for p in com_relacionamentos[:5]:  # Mostrar apenas 5
            relacionamentos = []
            if p['tem_pedidos']:
                relacionamentos.append('Pedidos')
            if p['tem_orcamentos']:
                relacionamentos.append('Orçamentos')
            if p['tem_requisicoes']:
                relacionamentos.append('Requisições')
            
            print(f"   • {p['codigo']} - {p['nome']}")
            print(f"      └─ {', '.join(relacionamentos)}")
        
        if len(com_relacionamentos) > 5:
            print(f"   ... e mais {len(com_relacionamentos) - 5} produtos")
    
    # Lista completa (primeiros 10)
    print(f"\n📋 {Cores.BOLD}PRIMEIROS 10 PRODUTOS:{Cores.ENDC}")
    for i, p in enumerate(para_deletar[:10], 1):
        custo = p['custo_material'] + p['custo_servico']
        utilizado_str = f"{Cores.WARNING}[UTILIZADO]{Cores.ENDC}" if p['utilizado'] else ""
        custo_str = f"R$ {custo:.2f}" if custo > 0 else "Sem custo"
        print(f"   {i:2d}. {p['codigo']} - {p['nome']} {utilizado_str}")
        print(f"       {custo_str}")
    
    if len(para_deletar) > 10:
        print(f"   ... e mais {len(para_deletar) - 10} produtos")
    
    print()

# ===================================================================
# FUNÇÃO: DELEÇÃO REAL
# ===================================================================
def executar_delecao(dados):
    """Executa a deleção real dos produtos"""
    
    print_header("EXECUTANDO DELEÇÃO")
    
    para_deletar = dados['para_deletar']
    
    deletados_sucesso = 0
    deletados_erro = []
    
    print_info(f"Deletando {len(para_deletar)} produtos...")
    print()
    
    with transaction.atomic():
        for i, item in enumerate(para_deletar, 1):
            codigo = item['codigo']
            nome = item['nome']
            produto = item['objeto']
            
            try:
                produto.delete()
                deletados_sucesso += 1
                print(f"   [{i:2d}/{len(para_deletar)}] ✅ {codigo} - {nome}")
                
            except Exception as e:
                deletados_erro.append({
                    'codigo': codigo,
                    'nome': nome,
                    'erro': str(e)
                })
                print(f"   [{i:2d}/{len(para_deletar)}] ❌ {codigo} - ERRO: {e}")
    
    return {
        'sucesso': deletados_sucesso,
        'erros': deletados_erro
    }

# ===================================================================
# FUNÇÃO: RELATÓRIO FINAL
# ===================================================================
def relatorio_final(dados, resultado_delecao=None):
    """Exibe relatório final"""
    
    print_header("RELATÓRIO FINAL")
    
    if resultado_delecao:
        # Deleção real
        print_success(f"Produtos deletados com sucesso: {resultado_delecao['sucesso']}")
        
        if resultado_delecao['erros']:
            print_error(f"Produtos com erro: {len(resultado_delecao['erros'])}")
            print()
            for erro in resultado_delecao['erros']:
                print(f"   {erro['codigo']}: {erro['erro']}")
        
        print()
        print_success("🎉 DELEÇÃO CONCLUÍDA COM SUCESSO!")
        
    else:
        # Apenas simulação
        print_info("Modo simulação - Nenhum produto foi deletado.")
        print_info("Para deletar de verdade, confirme na próxima etapa.")
    
    print()

# ===================================================================
# FUNÇÃO: MENU INTERATIVO
# ===================================================================
def menu_interativo(dados):
    """Menu interativo após a simulação"""
    
    while True:
        print(f"\n{Cores.BOLD}O QUE DESEJA FAZER?{Cores.ENDC}")
        print(f"  1) {Cores.OKGREEN}Executar deleção REAL{Cores.ENDC}")
        print(f"  2) {Cores.OKCYAN}Ver simulação novamente{Cores.ENDC}")
        print(f"  3) {Cores.WARNING}Ver lista completa de produtos{Cores.ENDC}")
        print(f"  4) {Cores.FAIL}Cancelar e sair{Cores.ENDC}")
        
        escolha = input(f"\n{Cores.BOLD}Digite sua escolha (1-4): {Cores.ENDC}").strip()
        
        if escolha == '1':
            # Confirmação final
            print(f"\n{Cores.FAIL}{Cores.BOLD}⚠️  ÚLTIMA CONFIRMAÇÃO ⚠️{Cores.ENDC}")
            print(f"{Cores.FAIL}Você está prestes a deletar {len(dados['para_deletar'])} produtos!{Cores.ENDC}")
            print(f"{Cores.FAIL}Esta operação é IRREVERSÍVEL!{Cores.ENDC}")
            
            confirmacao = input(f"\n{Cores.BOLD}Digite 'DELETAR' para confirmar: {Cores.ENDC}").strip()
            
            if confirmacao == 'DELETAR':
                resultado = executar_delecao(dados)
                relatorio_final(dados, resultado)
                break
            else:
                print_warning("Deleção cancelada.")
                
        elif escolha == '2':
            executar_simulacao(dados)
            
        elif escolha == '3':
            print_header("LISTA COMPLETA DE PRODUTOS")
            for i, p in enumerate(dados['para_deletar'], 1):
                custo = p['custo_material'] + p['custo_servico']
                utilizado_str = f"{Cores.WARNING}[UTILIZADO]{Cores.ENDC}" if p['utilizado'] else ""
                custo_str = f"- R$ {custo:.2f}" if custo > 0 else ""
                print(f"{i:3d}. {p['codigo']:15s} {p['nome'][:50]:50s} {custo_str} {utilizado_str}")
            
        elif escolha == '4':
            print_warning("Operação cancelada pelo usuário.")
            break
            
        else:
            print_error("Opção inválida! Digite 1, 2, 3 ou 4.")

# ===================================================================
# MAIN
# ===================================================================
def main():
    """Função principal"""
    
    print_header("DELEÇÃO EM MASSA DE PRODUTOS - FUZA ELEVADORES")
    
    print(f"{Cores.BOLD}Este script irá:{Cores.ENDC}")
    print("  1. Buscar os produtos no banco de dados")
    print("  2. Fazer uma simulação mostrando o que será deletado")
    print("  3. Perguntar se você deseja prosseguir")
    print("  4. Executar a deleção se confirmado")
    print()
    print(f"{Cores.WARNING}Total de códigos na lista: {len(CODIGOS_PARA_DELETAR)}{Cores.ENDC}")
    
    input(f"\n{Cores.BOLD}Pressione ENTER para continuar...{Cores.ENDC}")
    
    # Carregar dados
    dados = carregar_dados()
    
    # Se não há produtos para deletar, encerrar
    if not dados['para_deletar']:
        print_error("Nenhum produto para deletar foi encontrado!")
        sys.exit(0)
    
    # Executar simulação
    executar_simulacao(dados)
    
    # Menu interativo
    menu_interativo(dados)
    
    print()
    print_success("Script finalizado!")
    print()

# ===================================================================
# EXECUTAR
# ===================================================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Cores.WARNING}Operação cancelada pelo usuário (Ctrl+C){Cores.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Cores.FAIL}ERRO INESPERADO: {e}{Cores.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)