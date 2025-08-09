# migrations/0021_reorganizar_grupos_subgrupos.py
# Script para reorganizar grupos e subgrupos conforme nova estrutura definida
# ADAPTADO PARA A ESTRUTURA REAL DOS MODELOS FUZA

from django.db import migrations, transaction
from django.db import models

def reorganizar_grupos_subgrupos(apps, schema_editor):
    """
    Reorganiza grupos e subgrupos para nova estrutura FUZA
    ADAPTADO para funcionar com os modelos reais
    """
    # Modelos necessários
    GrupoProduto = apps.get_model('core', 'GrupoProduto')
    SubgrupoProduto = apps.get_model('core', 'SubgrupoProduto')
    Produto = apps.get_model('core', 'Produto')
    Usuario = apps.get_model('core', 'Usuario')  # Modelo customizado
    
    print("🚀 Iniciando reorganização de grupos e subgrupos...")
    
    # Buscar um usuário para usar como criador
    try:
        usuario_sistema = Usuario.objects.first()
        if not usuario_sistema:
            print("❌ Erro: Nenhum usuário encontrado no sistema. Crie um usuário primeiro.")
            return
        print(f"👤 Usando usuário: {usuario_sistema}")
    except Exception as e:
        print(f"❌ Erro ao buscar usuário: {e}")
        return
    
    with transaction.atomic():
        
        # =================================================================
        # PASSO 1: INATIVAR GRUPOS/SUBGRUPOS ANTIGOS
        # =================================================================
        print("🗑️  Inativando estrutura antiga...")
        
        # Inativar todos os grupos e subgrupos existentes
        GrupoProduto.objects.all().update(ativo=False)
        SubgrupoProduto.objects.all().update(ativo=False)
        
        # =================================================================
        # PASSO 2: CRIAR NOVA ESTRUTURA DE GRUPOS
        # =================================================================
        print("📊 Criando nova estrutura de grupos...")
        
        grupos_definicao = {
            '04': {
                'nome': 'PORTAS',
                'tipo_produto': 'PI'  # Produto Intermediário
            },
            '05': {
                'nome': 'ESTRUTURA', 
                'tipo_produto': 'PI'
            },
            '06': {
                'nome': 'CABINE',
                'tipo_produto': 'PI'
            },
            '07': {
                'nome': 'MOTORES',
                'tipo_produto': 'MP'  # Matéria Prima
            },
            '08': {
                'nome': 'TRAÇÃO',
                'tipo_produto': 'MP'
            },
            '98': {
                'nome': 'SERVIÇOS',
                'tipo_produto': 'PI'
            }
        }
        
        grupos_criados = {}
        for codigo, dados in grupos_definicao.items():
            # Tentar buscar grupo existente ou criar novo
            grupo, created = GrupoProduto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nome': dados['nome'],
                    'tipo_produto': dados['tipo_produto'],
                    'ativo': True,
                    'criado_por': usuario_sistema
                }
            )
            
            # Se existia mas estava inativo, reativar e atualizar
            if not created:
                grupo.nome = dados['nome']
                grupo.tipo_produto = dados['tipo_produto']
                grupo.ativo = True
                grupo.save()
            
            grupos_criados[codigo] = grupo
            status = "✅ Criado" if created else "🔄 Reativado/Atualizado"
            print(f"  {status}: Grupo {codigo} - {dados['nome']} ({dados['tipo_produto']})")
        
        # =================================================================
        # PASSO 3: CRIAR NOVA ESTRUTURA DE SUBGRUPOS  
        # =================================================================
        print("📋 Criando nova estrutura de subgrupos...")
        
        subgrupos_definicao = {
            # 04 - PORTAS
            '04.01': {
                'grupo': '04', 'nome': 'Portas de Cabina',
                'codigo_sub': '01'
            },
            '04.02': {
                'grupo': '04', 'nome': 'Portas de Pavimento', 
                'codigo_sub': '02'
            },
            '04.03': {
                'grupo': '04', 'nome': 'Acessórios de Porta',
                'codigo_sub': '03'
            },
            
            # 05 - ESTRUTURA  
            '05.01': {
                'grupo': '05', 'nome': 'Arcada',
                'codigo_sub': '01'
            },
            '05.02': {
                'grupo': '05', 'nome': 'Plataforma',
                'codigo_sub': '02'
            },
            
            # 06 - CABINE
            '06.01': {
                'grupo': '06', 'nome': 'Painéis',
                'codigo_sub': '01'
            },
            '06.02': {
                'grupo': '06', 'nome': 'Acessórios de Cabine', 
                'codigo_sub': '02'
            },
            
            # 07 - MOTORES
            '07.01': {
                'grupo': '07', 'nome': 'Motores Elétricos',
                'codigo_sub': '01'
            },
            '07.02': {
                'grupo': '07', 'nome': 'Motorfreios e Acionamentos',
                'codigo_sub': '02'
            },
            '07.03': {
                'grupo': '07', 'nome': 'Máquinas Completas',
                'codigo_sub': '03'
            },
            '07.04': {
                'grupo': '07', 'nome': 'Redutores',
                'codigo_sub': '04'
            },
            
            # 08 - TRAÇÃO
            '08.01': {
                'grupo': '08', 'nome': 'Kit Polia',
                'codigo_sub': '01'
            },
            '08.02': {
                'grupo': '08', 'nome': 'Contrapeso',
                'codigo_sub': '02'
            },
            '08.03': {
                'grupo': '08', 'nome': 'Cabos de Aço',
                'codigo_sub': '03'
            },
            '08.04': {
                'grupo': '08', 'nome': 'Componentes de Transmissão',
                'codigo_sub': '04'
            },
            
            # 98 - SERVIÇOS
            '98.01': {
                'grupo': '98', 'nome': 'Serviços Internos',
                'codigo_sub': '01'
            },
            '98.02': {
                'grupo': '98', 'nome': 'Serviços Externos',
                'codigo_sub': '02'
            }
        }
        
        subgrupos_criados = {}
        for codigo_completo, dados in subgrupos_definicao.items():
            grupo_pai = grupos_criados[dados['grupo']]
            
            # Tentar buscar subgrupo existente ou criar novo
            subgrupo, created = SubgrupoProduto.objects.get_or_create(
                codigo=dados['codigo_sub'],
                grupo=grupo_pai,
                defaults={
                    'nome': dados['nome'],
                    'ativo': True,
                    'ultimo_numero': 0,
                    'criado_por': usuario_sistema
                }
            )
            
            # Se existia mas estava inativo, reativar e atualizar
            if not created:
                subgrupo.nome = dados['nome']
                subgrupo.ativo = True
                subgrupo.save()
            
            subgrupos_criados[codigo_completo] = subgrupo
            status = "✅ Criado" if created else "🔄 Reativado/Atualizado"
            print(f"    {status}: Subgrupo {codigo_completo} - {dados['nome']}")
        
        # =================================================================
        # PASSO 4: ATUALIZAR PRODUTOS ÓRFÃOS (sem quebrar referências)
        # =================================================================
        print("🔗 Corrigindo produtos órfãos...")
        
        # Buscar produtos que apontam para grupos/subgrupos inativos
        produtos_orfaos = Produto.objects.filter(
            models.Q(grupo__ativo=False) | 
            models.Q(subgrupo__ativo=False) |
            models.Q(grupo__isnull=True) |
            models.Q(subgrupo__isnull=True)
        )
        
        print(f"    Encontrados {produtos_orfaos.count()} produtos órfãos")
        
        produtos_corrigidos = 0
        produtos_nao_classificados = []
        
        for produto in produtos_orfaos:
            try:
                # Tentar identificar subgrupo baseado no nome/padrões
                novo_subgrupo = None
                nome_upper = produto.nome.upper()
                
                # Regras de mapeamento inteligente baseado no nome
                if any(palavra in nome_upper for palavra in ['MOTOR', 'CV', 'KW', 'HP']):
                    novo_subgrupo = subgrupos_criados.get('07.01')
                elif any(palavra in nome_upper for palavra in ['PAINEL', 'CHAPA INOX', 'CHAPA']):
                    novo_subgrupo = subgrupos_criados.get('06.01')
                elif any(palavra in nome_upper for palavra in ['LONGARINA', 'TRAVESSA', 'PERFIL', 'VIGA']):
                    novo_subgrupo = subgrupos_criados.get('05.01')
                elif any(palavra in nome_upper for palavra in ['CORTE', 'DOBRA', 'SERVIÇO', 'SOLDAGEM']):
                    novo_subgrupo = subgrupos_criados.get('98.02')
                elif any(palavra in nome_upper for palavra in ['PORTA']):
                    novo_subgrupo = subgrupos_criados.get('04.01')
                elif any(palavra in nome_upper for palavra in ['MAQUINA', 'TRACAO', 'TRAÇÃO']):
                    novo_subgrupo = subgrupos_criados.get('07.03')
                elif any(palavra in nome_upper for palavra in ['REDUTOR']):
                    novo_subgrupo = subgrupos_criados.get('07.04')
                elif any(palavra in nome_upper for palavra in ['CABO', 'AÇO']):
                    novo_subgrupo = subgrupos_criados.get('08.03')
                elif any(palavra in nome_upper for palavra in ['POLIA', 'ROLDANA']):
                    novo_subgrupo = subgrupos_criados.get('08.01')
                elif any(palavra in nome_upper for palavra in ['CONTRAPESO', 'PESO']):
                    novo_subgrupo = subgrupos_criados.get('08.02')
                elif any(palavra in nome_upper for palavra in ['CORRIMAO', 'CORRIMÃO', 'QUEBRA', 'LUZ']):
                    novo_subgrupo = subgrupos_criados.get('06.02')
                else:
                    # Não conseguiu classificar
                    produtos_nao_classificados.append(f"{produto.codigo} - {produto.nome}")
                    continue
                
                if novo_subgrupo:
                    # Atualizar tipo do produto baseado no grupo
                    produto.subgrupo = novo_subgrupo
                    produto.grupo = novo_subgrupo.grupo
                    produto.tipo = novo_subgrupo.grupo.tipo_produto
                    produto.save()
                    produtos_corrigidos += 1
                    print(f"      ✅ Corrigido: {produto.codigo} → {novo_subgrupo.grupo.codigo}.{novo_subgrupo.codigo}")
                
            except Exception as e:
                print(f"      ❌ Erro ao corrigir {produto.codigo}: {e}")
        
        print(f"    ✅ {produtos_corrigidos} produtos órfãos corrigidos automaticamente")
        
        if produtos_nao_classificados:
            print(f"    ⚠️  {len(produtos_nao_classificados)} produtos precisam classificação manual:")
            for produto_info in produtos_nao_classificados[:10]:  # Mostrar apenas os primeiros 10
                print(f"        {produto_info}")
            if len(produtos_nao_classificados) > 10:
                print(f"        ... e mais {len(produtos_nao_classificados) - 10} produtos")
        
        # =================================================================
        # PASSO 5: RELATÓRIO FINAL
        # =================================================================
        print("\n📊 RELATÓRIO FINAL:")
        print(f"✅ Grupos criados/atualizados: {len(grupos_criados)}")
        print(f"✅ Subgrupos criados/atualizados: {len(subgrupos_criados)}")
        print(f"✅ Produtos órfãos corrigidos: {produtos_corrigidos}")
        print(f"⚠️  Produtos para classificação manual: {len(produtos_nao_classificados)}")
        
        # Listar grupos e subgrupos criados
        print("\n📋 ESTRUTURA FINAL:")
        for codigo_grupo, grupo in grupos_criados.items():
            print(f"  {codigo_grupo} - {grupo.nome} ({grupo.tipo_produto})")
            
            # Listar subgrupos deste grupo
            subgrupos_do_grupo = [
                (codigo, sub) for codigo, sub in subgrupos_criados.items() 
                if sub.grupo.codigo == codigo_grupo
            ]
            
            for codigo_sub, subgrupo in subgrupos_do_grupo:
                # Contar produtos neste subgrupo
                qtd_produtos = Produto.objects.filter(subgrupo=subgrupo).count()
                print(f"    {codigo_sub} - {subgrupo.nome} ({qtd_produtos} produtos)")
        
        print("\n🎉 Reorganização de grupos e subgrupos concluída!")
        print("🔄 Próximo passo: verificar produtos não classificados no admin")


def reverter_reorganizacao_grupos_subgrupos(apps, schema_editor):
    """
    Reverter reorganização (rollback)
    """
    print("🔄 Revertendo reorganização...")
    
    GrupoProduto = apps.get_model('core', 'GrupoProduto')
    SubgrupoProduto = apps.get_model('core', 'SubgrupoProduto')
    
    # Reativar todos os grupos e subgrupos
    GrupoProduto.objects.all().update(ativo=True)
    SubgrupoProduto.objects.all().update(ativo=True)
    
    print("✅ Reversão concluída - todos os grupos/subgrupos reativados")


class Migration(migrations.Migration):
    
    dependencies = [
        ('core', '0020_produto_custo_material_produto_custo_servico_and_more'),
    ]
    
    operations = [
        migrations.RunPython(
            reorganizar_grupos_subgrupos,
            reverter_reorganizacao_grupos_subgrupos
        ),
    ]