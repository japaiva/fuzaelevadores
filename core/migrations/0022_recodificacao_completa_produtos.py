# migrations/0022_recodificacao_completa_produtos.py  
# Script para recodificação completa de todos os produtos intermediários
# VERSÃO ROBUSTA - Com tratamento de erros e transações menores

from django.db import migrations, transaction
from decimal import Decimal


def recodificar_produtos_completo(apps, schema_editor):
    """
    Recodificação completa de todos os produtos intermediários
    VERSÃO ROBUSTA com tratamento de erros
    """
    # Modelos necessários
    Produto = apps.get_model('core', 'Produto')
    SubgrupoProduto = apps.get_model('core', 'SubgrupoProduto')
    GrupoProduto = apps.get_model('core', 'GrupoProduto')
    Usuario = apps.get_model('core', 'Usuario')
    
    print("🚀 Iniciando recodificação completa de produtos...")
    
    # Buscar um usuário para usar nas criações
    try:
        usuario_sistema = Usuario.objects.first()
        if not usuario_sistema:
            print("❌ Erro: Nenhum usuário encontrado no sistema.")
            return
        print(f"👤 Usando usuário: {usuario_sistema}")
    except Exception as e:
        print(f"❌ Erro ao buscar usuário: {e}")
        return
    
    # =================================================================
    # PASSO 1: BUSCAR SUBGRUPOS (SEM TRANSAÇÃO)
    # =================================================================
    subgrupos_dict = {}
    try:
        for sub in SubgrupoProduto.objects.filter(ativo=True).select_related('grupo'):
            codigo_completo = f"{sub.grupo.codigo}.{sub.codigo}"
            subgrupos_dict[codigo_completo] = sub
        
        if not subgrupos_dict:
            print("❌ ERRO: Nenhum subgrupo encontrado! Execute primeiro o script de grupos/subgrupos.")
            return
        
        print(f"📊 Subgrupos encontrados: {len(subgrupos_dict)}")
    except Exception as e:
        print(f"❌ Erro ao buscar subgrupos: {e}")
        return
    
    # =================================================================
    # PASSO 2: RECODIFICAR PRODUTOS EXISTENTES (TRANSAÇÕES PEQUENAS)
    # =================================================================
    print("\n🔄 Recodificando produtos existentes...")
    
    try:
        produtos_existentes = Produto.objects.filter(tipo='PI').order_by('codigo')
        print(f"Produtos intermediários encontrados: {produtos_existentes.count()}")
    except Exception as e:
        print(f"❌ Erro ao buscar produtos: {e}")
        return
    
    contadores_subgrupo = {}
    produtos_recodificados = 0
    
    # Processar produtos um por um (transações individuais)
    for produto in produtos_existentes:
        try:
            with transaction.atomic():
                # Identificar subgrupo atual do produto
                if not produto.subgrupo:
                    print(f"  ⚠️  Produto sem subgrupo: {produto.codigo} - {produto.nome}")
                    continue
                
                codigo_subgrupo_completo = f"{produto.grupo.codigo}.{produto.subgrupo.codigo}"
                
                # Inicializar contador do subgrupo se não existe
                if codigo_subgrupo_completo not in contadores_subgrupo:
                    contadores_subgrupo[codigo_subgrupo_completo] = 1
                
                # Gerar novo código
                novo_codigo = f"{codigo_subgrupo_completo}.{contadores_subgrupo[codigo_subgrupo_completo]:05d}"
                
                # Salvar código antigo nas observações se for diferente
                if produto.codigo != novo_codigo:
                    obs_anterior = produto.descricao or ""
                    if "Código anterior:" not in obs_anterior:
                        produto.descricao = f"{obs_anterior}\nCódigo anterior: {produto.codigo}".strip()
                    
                    print(f"  🔄 {produto.codigo} → {novo_codigo} | {produto.nome}")
                    produto.codigo = novo_codigo
                    produtos_recodificados += 1
                else:
                    print(f"  ✅ {produto.codigo} | {produto.nome} (já correto)")
                
                # Incrementar contador
                contadores_subgrupo[codigo_subgrupo_completo] += 1
                
                # Salvar produto
                produto.save()
                
        except Exception as e:
            print(f"  ❌ Erro ao recodificar {produto.codigo}: {e}")
            continue
    
    print(f"✅ {produtos_recodificados} produtos recodificados")
    
    # =================================================================
    # PASSO 3: CRIAR PRODUTOS NOVOS (LOTES PEQUENOS)
    # =================================================================  
    print(f"\n➕ Criando produtos novos identificados...")
    
    # Definição dos novos produtos (versão compacta para teste)
    novos_produtos = [
        # 04.01 - Portas de Cabina (apenas alguns para teste)
        {
            'subgrupo': '04.01', 'nome': 'Porta Pivotante INOX',
            'tipo_pi': 'MONTADO_INTERNO', 'custo_total': Decimal('256.00'),
            'obs': 'Porta pivotante fabricada internamente - Material INOX'
        },
        {
            'subgrupo': '04.01', 'nome': 'Porta Pantográfica INOX', 
            'tipo_pi': 'MONTADO_INTERNO', 'custo_total': Decimal('466.00'),
            'obs': 'Porta pantográfica fabricada internamente - Material INOX'
        },
        {
            'subgrupo': '04.01', 'nome': 'Porta Guilhotina INOX',
            'tipo_pi': 'MONTADO_INTERNO', 'custo_total': Decimal('324.00'),
            'obs': 'Porta guilhotina fabricada internamente - Material INOX'
        },
        
        # 05.01 - Arcada (alguns itens)
        {
            'subgrupo': '05.01', 'nome': 'Travessa 3mm SAE1010',
            'tipo_pi': 'COMPRADO', 'custo_total': Decimal('151.00'),
            'obs': 'Travessa estrutural 3mm - Cotação Innovalaser SAE1010 Item 01'
        },
        {
            'subgrupo': '05.01', 'nome': 'Travessa 4mm SAE1010',
            'tipo_pi': 'COMPRADO', 'custo_total': Decimal('241.00'),
            'obs': 'Travessa estrutural 4mm - Cotação Innovalaser SAE1010 Item 02'
        },
        
        # 06.01 - Painéis (alguns itens)
        {
            'subgrupo': '06.01', 'nome': 'Painel INOX 430 1,2mm',
            'tipo_pi': 'MONTADO_EXTERNO', 'custo_total': Decimal('61.76'),
            'obs': 'Painel INOX 430 espessura 1,2mm - Baseado cotação Innovalaser'
        },
        
        # 98.01 - Serviços Internos
        {
            'subgrupo': '98.01', 'nome': 'Hora Projeto',
            'tipo_pi': 'SERVICO_INTERNO', 'custo_total': Decimal('23.00'),
            'obs': 'Hora de projeto interno'
        },
        {
            'subgrupo': '98.01', 'nome': 'Hora Produção',
            'tipo_pi': 'SERVICO_INTERNO', 'custo_total': Decimal('23.33'),
            'obs': 'Hora de produção interna'
        },
        
        # 98.02 - Serviços Externos
        {
            'subgrupo': '98.02', 'nome': 'Corte e Dobra INOX',
            'tipo_pi': 'SERVICO_EXTERNO', 'custo_total': Decimal('75.03'),
            'obs': 'Serviço de corte e dobra para INOX - Baseado análise cotação'
        }
    ]
    
    # Criar produtos um por um (transações individuais)
    produtos_criados = 0
    for dados_produto in novos_produtos:
        try:
            with transaction.atomic():
                # Verificar se subgrupo existe
                if dados_produto['subgrupo'] not in subgrupos_dict:
                    print(f"  ⚠️  Subgrupo {dados_produto['subgrupo']} não encontrado, pulando...")
                    continue
                
                subgrupo = subgrupos_dict[dados_produto['subgrupo']]
                
                # Verificar próximo número sequencial disponível
                codigo_subgrupo_completo = dados_produto['subgrupo']
                if codigo_subgrupo_completo not in contadores_subgrupo:
                    contadores_subgrupo[codigo_subgrupo_completo] = 1
                
                # Gerar código
                novo_codigo = f"{dados_produto['subgrupo']}.{contadores_subgrupo[codigo_subgrupo_completo]:05d}"
                
                # Verificar se já existe produto com esse código
                if Produto.objects.filter(codigo=novo_codigo).exists():
                    print(f"  ⚠️  Código {novo_codigo} já existe, ajustando contador...")
                    # Encontrar próximo número disponível
                    contador_atual = contadores_subgrupo[codigo_subgrupo_completo]
                    while Produto.objects.filter(codigo=f"{dados_produto['subgrupo']}.{contador_atual:05d}").exists():
                        contador_atual += 1
                        if contador_atual > 99999:  # Limite de segurança
                            raise Exception(f"Limite de produtos atingido para {dados_produto['subgrupo']}")
                    
                    contadores_subgrupo[codigo_subgrupo_completo] = contador_atual
                    novo_codigo = f"{dados_produto['subgrupo']}.{contador_atual:05d}"
                
                # Distribuir custo entre material e serviço baseado no tipo_pi
                custo_material = None
                custo_servico = None
                
                if dados_produto['custo_total']:
                    if dados_produto['tipo_pi'] in ['SERVICO_INTERNO', 'SERVICO_EXTERNO']:
                        # Serviços: 100% serviço
                        custo_material = Decimal('0.00')
                        custo_servico = dados_produto['custo_total']
                    elif dados_produto['tipo_pi'] == 'COMPRADO':
                        # Comprados: 100% material
                        custo_material = dados_produto['custo_total']
                        custo_servico = Decimal('0.00')
                    else:
                        # Montados: dividir 70% material, 30% serviço
                        custo_material = dados_produto['custo_total'] * Decimal('0.70')
                        custo_servico = dados_produto['custo_total'] * Decimal('0.30')
                
                # Criar produto
                produto = Produto.objects.create(
                    codigo=novo_codigo,
                    nome=dados_produto['nome'],
                    descricao=dados_produto['obs'],
                    tipo='PI',
                    tipo_pi=dados_produto['tipo_pi'],
                    grupo=subgrupo.grupo,
                    subgrupo=subgrupo,
                    custo_material=custo_material,
                    custo_servico=custo_servico,
                    disponivel=True,
                    status='ATIVO',
                    unidade_medida='UN',
                    criado_por=usuario_sistema,
                    atualizado_por=usuario_sistema
                )
                
                produtos_criados += 1
                contadores_subgrupo[codigo_subgrupo_completo] += 1
                
                print(f"  ✅ Criado: {novo_codigo} - {dados_produto['nome']}")
                
        except Exception as e:
            print(f"  ❌ Erro ao criar produto {dados_produto['nome']}: {e}")
            continue
    
    print(f"✅ {produtos_criados} novos produtos criados")
    
    # =================================================================
    # PASSO 4: ATUALIZAR CONTADORES DOS SUBGRUPOS (TRANSAÇÕES INDIVIDUAIS)
    # =================================================================
    print("\n🔢 Atualizando contadores dos subgrupos...")
    
    for codigo_completo, contador in contadores_subgrupo.items():
        try:
            with transaction.atomic():
                if codigo_completo in subgrupos_dict:
                    subgrupo = subgrupos_dict[codigo_completo]
                    subgrupo.ultimo_numero = contador - 1  # -1 porque o contador já está no próximo
                    subgrupo.save()
                    print(f"  ✅ {codigo_completo}: último número = {subgrupo.ultimo_numero}")
        except Exception as e:
            print(f"  ❌ Erro ao atualizar contador {codigo_completo}: {e}")
            continue
    
    # =================================================================
    # PASSO 5: RELATÓRIO FINAL (SEM TRANSAÇÃO)
    # =================================================================
    print("\n📊 RELATÓRIO FINAL DE RECODIFICAÇÃO:")
    print(f"✅ Produtos existentes recodificados: {produtos_recodificados}")
    print(f"✅ Novos produtos criados: {produtos_criados}")
    
    # Estatísticas por subgrupo (sem transação)
    print("\n📋 PRODUTOS POR SUBGRUPO:")
    for codigo_subgrupo in sorted(subgrupos_dict.keys()):
        try:
            qtd_produtos = Produto.objects.filter(
                subgrupo=subgrupos_dict[codigo_subgrupo], 
                tipo='PI'
            ).count()
            subgrupo_nome = subgrupos_dict[codigo_subgrupo].nome
            print(f"  {codigo_subgrupo} - {subgrupo_nome}: {qtd_produtos} produtos")
        except Exception as e:
            print(f"  ❌ Erro ao contar produtos do subgrupo {codigo_subgrupo}: {e}")
    
    # Total geral
    try:
        total_produtos = Produto.objects.filter(tipo='PI').count()
        print(f"\n🎯 TOTAL DE PRODUTOS INTERMEDIÁRIOS: {total_produtos}")
    except Exception as e:
        print(f"❌ Erro ao contar total de produtos: {e}")
    
    print("\n🎉 Recodificação completa finalizada!")
    print("📋 Próximo passo: verificar produtos no admin e ajustar estruturas")


def reverter_recodificacao_completa(apps, schema_editor):
    """
    Reverter recodificação (rollback)
    """
    print("🔄 Revertendo recodificação...")
    
    Produto = apps.get_model('core', 'Produto')
    
    # Restaurar códigos antigos das observações
    try:
        produtos_com_codigo_anterior = Produto.objects.filter(
            descricao__icontains='Código anterior:'
        )
        
        for produto in produtos_com_codigo_anterior:
            try:
                with transaction.atomic():
                    # Extrair código anterior das observações
                    desc_lines = produto.descricao.split('\n')
                    for line in desc_lines:
                        if 'Código anterior:' in line:
                            codigo_anterior = line.replace('Código anterior:', '').strip()
                            produto.codigo = codigo_anterior
                            # Remover linha das observações
                            produto.descricao = '\n'.join([l for l in desc_lines if 'Código anterior:' not in l]).strip()
                            produto.save()
                            break
                            
            except Exception as e:
                print(f"Erro ao reverter {produto.codigo}: {e}")
    
    except Exception as e:
        print(f"Erro na reversão: {e}")
    
    print("✅ Reversão concluída")


class Migration(migrations.Migration):
    
    dependencies = [
        ('core', '0021_reorganizar_grupos_subgrupos'),
    ]
    
    operations = [
        migrations.RunPython(
            recodificar_produtos_completo,
            reverter_recodificacao_completa
        ),
    ]