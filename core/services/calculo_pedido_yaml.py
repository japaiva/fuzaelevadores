# core/services/calculo_pedido_yaml_evolved.py
"""
Parser YAML evoluído para suportar o novo formato mais elegante
- Templates com {{ variavel }}
- Sistema switch/casos
- Lookups por painel_catalogo
- Estrutura de subcategorias
"""

from __future__ import annotations
import re
import yaml
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from jinja2 import Template, Environment, BaseLoader

from core.models import Produto
from core.models.regras_yaml import RegraYAML
from core.services.config_repo_db import ConfigRepoDB

logger = logging.getLogger(__name__)


# ============================================================================
# Helpers e Utilities
# ============================================================================

def d(x: Any, default: str = "0") -> Decimal:
    """Converte qualquer valor para Decimal, tratando None/""/inválidos como 0."""
    if x is None or x == "":
        return Decimal(default)
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal(default)


def safe_float(x: Any) -> float:
    """Converte para float; se None/erro, retorna 0.0."""
    try:
        if x is None:
            return 0.0
        return float(x)
    except Exception:
        return 0.0


def safe_int(x: Any) -> int:
    """Converte para int; se None/erro, retorna 0."""
    try:
        return int(x) if x is not None else 0
    except Exception:
        return 0


# ============================================================================
# Sistema de Templates Jinja2
# ============================================================================

class TemplateProcessor:
    """Processa templates {{ variavel }} usando Jinja2"""
    
    def __init__(self):
        self.env = Environment(loader=BaseLoader())
        # Adicionar funções helper ao ambiente
        self.env.globals.update({
            'max': max,
            'min': min,
            'round': round,
            'abs': abs,
        })
    
    def render(self, template_str: str, context: Dict[str, Any]) -> str:
        """Renderiza template com contexto"""
        try:
            if not isinstance(template_str, str):
                return str(template_str)
            
            # Se não tem template, retorna direto
            if '{{' not in template_str:
                return template_str
            
            template = self.env.from_string(template_str)
            return template.render(**context)
        except Exception as e:
            logger.warning(f"Erro ao renderizar template '{template_str}': {e}")
            return str(template_str)
    
    def render_to_number(self, template_str: str, context: Dict[str, Any]) -> Decimal:
        """Renderiza template e converte para Decimal"""
        result = self.render(template_str, context)
        return d(result)


# ============================================================================
# Sistema de Lookups
# ============================================================================

class LookupResolver:
    """Resolve lookups baseados em diferentes estratégias"""
    
    def __init__(self, custos_db: Dict[str, Any]):
        self.custos_db = custos_db
    
    def resolve_painel_catalogo(self, regra: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve lookup por painel_catalogo:
        lookup_por:
          material: "{{ ctx.material_painel }}"
          espessura: "{{ ctx.espessura_painel }}"
        """
        try:
            # Buscar configuração do catálogo no YAML (assumindo que está em cabine.painel_catalogo)
            template_proc = TemplateProcessor()
            
            lookup_config = regra.get('lookup_por', {})
            material_template = lookup_config.get('material', '')
            espessura_template = lookup_config.get('espessura', '')
            
            # Renderizar templates
            material = template_proc.render(material_template, context)
            espessura = template_proc.render(espessura_template, context)
            
            logger.debug(f"Buscando painel: material={material}, espessura={espessura}")
            
            # Buscar no catálogo (seria melhor ter isso como configuração separada)
            catalogo_paineis = [
                {"material": "Inox 430", "espessura": "1,2", "codigo_produto": "01.01.00016"},
                {"material": "Inox 430", "espessura": "1,5", "codigo_produto": "01.01.00017"},
                {"material": "Inox 430", "espessura": "2,0", "codigo_produto": "01.01.00018"},
                {"material": "Inox 304", "espessura": "1,2", "codigo_produto": "01.01.00019"},
                {"material": "Inox 304", "espessura": "1,5", "codigo_produto": "01.01.00020"},
                {"material": "Chapa Pintada", "espessura": "1,2", "codigo_produto": "01.01.00021"},
                {"material": "Chapa Pintada", "espessura": "1,5", "codigo_produto": "01.01.00022"},
            ]
            
            for item in catalogo_paineis:
                if (str(item.get("material")) == str(material) and 
                    str(item.get("espessura")) == str(espessura)):
                    return item.get("codigo_produto")
            
            # Fallback para default se configurado
            de_para = regra.get('de_para', {})
            default_codigo = de_para.get('default')
            if default_codigo:
                logger.warning(f"Usando código padrão {default_codigo} para material={material}, espessura={espessura}")
                return default_codigo
            
            return None
            
        except Exception as e:
            logger.error(f"Erro no lookup painel_catalogo: {e}")
            return None


# ============================================================================
# Sistema Switch/Casos
# ============================================================================

class SwitchProcessor:
    """Processa estruturas switch/casos do YAML"""
    
    def __init__(self, template_proc: TemplateProcessor):
        self.template_proc = template_proc
    
    def process_switch(self, switch_config: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """
        Processa switch:
          quando: "{{ ctx.piso_cabine }}"
          casos:
            "Por conta da empresa":
              inner_switch: ...
            "Por conta do cliente":
              codigo_produto: "..."
        """
        try:
            quando_template = switch_config.get('quando', '')
            valor_condicao = self.template_proc.render(quando_template, context)
            
            casos = switch_config.get('casos', {})
            
            # Verificar se há caso específico
            if valor_condicao in casos:
                caso = casos[valor_condicao]
                
                # Se tem inner_switch, processar recursivamente
                if 'inner_switch' in caso:
                    return self.process_switch(caso['inner_switch'], context)
                
                # Se tem codigo_produto direto, retornar
                if 'codigo_produto' in caso:
                    return self.template_proc.render(caso['codigo_produto'], context)
            
            # Verificar caso default
            if 'default' in casos:
                caso_default = casos['default']
                if 'codigo_produto' in caso_default:
                    return self.template_proc.render(caso_default['codigo_produto'], context)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro no processamento switch: {e}")
            return None


# ============================================================================
# Processador Principal de Regras
# ============================================================================

class RegraProcessor:
    """Processa uma regra individual do YAML"""
    
    def __init__(self, custos_db: Dict[str, Any]):
        self.custos_db = custos_db
        self.template_proc = TemplateProcessor()
        self.lookup_resolver = LookupResolver(custos_db)
        self.switch_processor = SwitchProcessor(self.template_proc)
    
    def process_regra(self, regra: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma regra e retorna item calculado
        """
        try:
            nome = regra.get('nome', 'item_sem_nome')
            codigo_produto = None
            
            # 1. Determinar código do produto
            if 'origem' in regra and regra['origem'] == 'painel_catalogo':
                codigo_produto = self.lookup_resolver.resolve_painel_catalogo(regra, context)
            
            elif 'switch' in regra:
                codigo_produto = self.switch_processor.process_switch(regra['switch'], context)
            
            elif 'codigo_produto' in regra:
                codigo_produto = self.template_proc.render(regra['codigo_produto'], context)
            
            if not codigo_produto:
                return {
                    'erro': f"Não foi possível determinar código do produto para {nome}",
                    'regra': nome
                }
            
            # 2. Calcular quantidade
            quantidade_template = regra.get('quantidade', '1')
            quantidade = self.template_proc.render_to_number(quantidade_template, context)
            
            if quantidade <= 0:
                return {
                    'erro': f"Quantidade inválida ({quantidade}) para {nome}",
                    'regra': nome
                }
            
            # 3. Buscar produto no banco
            produto = self.custos_db.get(codigo_produto)
            if not produto:
                produto = Produto.objects.filter(codigo=codigo_produto, disponivel=True).first()
            
            if not produto:
                return {
                    'erro': f"Produto {codigo_produto} não encontrado para {nome}",
                    'regra': nome,
                    'codigo': codigo_produto
                }
            
            # 4. Calcular valores
            valor_unitario = d(getattr(produto, 'custo_total', 0))
            valor_total = (quantidade * valor_unitario).quantize(Decimal('0.01'))
            
            # 5. Preparar explicação
            explicacao_template = regra.get('explicacao', '')
            explicacao = self.template_proc.render(explicacao_template, context) if explicacao_template else f"Item {nome}"
            
            return {
                'nome': nome,
                'codigo': codigo_produto,
                'descricao': getattr(produto, 'nome', ''),
                'quantidade': quantidade,
                'unidade': regra.get('unidade', 'un'),
                'valor_unitario': valor_unitario,
                'valor_total': valor_total,
                'explicacao': explicacao,
                'sucesso': True
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar regra {regra.get('nome', 'sem_nome')}: {e}")
            return {
                'erro': str(e),
                'regra': regra.get('nome', 'sem_nome')
            }


# ============================================================================
# Processador de Subcategorias
# ============================================================================

class SubcategoriaProcessor:
    """Processa subcategorias com múltiplas regras"""
    
    def __init__(self, custos_db: Dict[str, Any]):
        self.regra_processor = RegraProcessor(custos_db)
    
    def process_subcategoria(self, nome_sub: str, config_sub: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma subcategoria com suas regras
        """
        regras = config_sub.get('regras', [])
        unidade_subcategoria = config_sub.get('unidade', 'un')
        
        itens = []
        subtotal = Decimal('0.00')
        erros = []
        
        for regra in regras:
            item = self.regra_processor.process_regra(regra, context)
            
            if item.get('sucesso'):
                itens.append(item)
                subtotal += d(item.get('valor_total', 0))
            else:
                erros.append(item.get('erro', 'Erro desconhecido'))
        
        return {
            'nome': nome_sub,
            'unidade': unidade_subcategoria,
            'itens': itens,
            'subtotal': subtotal,
            'erros': erros,
            'quantidade_itens': len(itens)
        }


# ============================================================================
# Construtor de Contexto
# ============================================================================

class ContextBuilder:
    """Constrói contexto para templates a partir do pedido e dimensionamento"""
    
    @staticmethod
    def build_context(pedido, dimensionamento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constrói contexto completo para templates
        """
        # Dados do pedido
        ctx = {
            'material_painel': getattr(pedido, 'material_cabine', ''),
            'espessura_painel': getattr(pedido, 'espessura_cabine', ''),
            'piso_cabine': getattr(pedido, 'piso_cabine', ''),
            'material_piso_cabine': getattr(pedido, 'material_piso_cabine', ''),
            'capacidade': safe_float(getattr(pedido, 'capacidade', 0)),
            'modelo_elevador': getattr(pedido, 'modelo_elevador', ''),
            'acionamento': getattr(pedido, 'acionamento', ''),
        }
        
        # Dimensionamento
        cab = dimensionamento.get('cab', {})
        
        # Painéis (já calculados)
        pnl = cab.get('pnl', {})
        pnl_data = {
            'lateral': safe_int(pnl.get('lateral', 0)),
            'fundo': safe_int(pnl.get('fundo', 0)),
            'teto': safe_int(pnl.get('teto', 0)),
        }
        
        # Chapas (já calculadas)
        chp = cab.get('chp', {})
        chp_data = {
            'corpo': safe_int(chp.get('corpo', 0)),
            'piso': safe_int(chp.get('piso', 0)),
        }
        
        # Áreas calculadas
        area_paineis_m2 = d(pnl_data['lateral'] + pnl_data['fundo'] + pnl_data['teto'])
        area_piso_m2 = d(chp_data['piso'])
        
        # Contexto completo
        context = {
            'ctx': ctx,
            'pnl': pnl_data,
            'chp': chp_data,
            'dim': cab,  # Dimensionamento completo
            'area_paineis_m2': area_paineis_m2,
            'area_piso_m2': area_piso_m2,
            'pedido': pedido,  # Objeto completo disponível
        }
        
        return context


# ============================================================================
# Serviço Principal Evoluído
# ============================================================================

class CalculoPedidoYAMLService:
    """
    Serviço evoluído que suporta o novo formato YAML com:
    - Templates {{ variavel }}
    - Sistema switch/casos  
    - Lookups por painel_catalogo
    - Estrutura de subcategorias
    
    RENOMEADO: Era CalculoPedidoYAMLEvolvedService
    """
    
    def __init__(self, custos_db: Optional[Dict[str, Any]] = None):
        self.custos_db = custos_db or {}
        self.subcategoria_processor = SubcategoriaProcessor(self.custos_db)
    
    def _load_yaml_config(self, tipo: str) -> Dict[str, Any]:
        """Carrega configuração YAML do banco usando ConfigRepoDB com cache"""
        try:
            if not hasattr(self, 'config_repo'):
                self.config_repo = ConfigRepoDB()
            
            data = self.config_repo.load(tipo)
            if not data:
                logger.warning(f"Nenhuma regra YAML ativa encontrada para tipo: {tipo}")
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao carregar YAML para {tipo}: {e}")
            return {}
    
    def calcular_categoria(self, tipo: str, pedido, dimensionamento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula uma categoria específica (cabine, carrinho, tracao, sistemas)
        """
        # Carregar configuração YAML
        config = self._load_yaml_config(tipo)
        if not config:
            return {
                'erro': f'Configuração YAML não encontrada para {tipo}',
                'subcategorias': {},
                'total_categoria': Decimal('0.00')
            }
        
        # Construir contexto
        context = ContextBuilder.build_context(pedido, dimensionamento)
        
        # Processar categoria
        categoria_config = config.get(tipo, {})
        subcategorias_config = categoria_config.get('subcategorias', {})
        
        subcategorias_resultado = {}
        total_categoria = Decimal('0.00')
        erros_gerais = []
        
        for nome_sub, config_sub in subcategorias_config.items():
            try:
                resultado_sub = self.subcategoria_processor.process_subcategoria(
                    nome_sub, config_sub, context
                )
                
                subcategorias_resultado[nome_sub] = resultado_sub
                total_categoria += d(resultado_sub.get('subtotal', 0))
                
                # Coletar erros
                if resultado_sub.get('erros'):
                    erros_gerais.extend(resultado_sub['erros'])
                    
            except Exception as e:
                erro_msg = f"Erro na subcategoria {nome_sub}: {str(e)}"
                logger.error(erro_msg)
                erros_gerais.append(erro_msg)
        
        return {
            'categoria': tipo.upper(),
            'subcategorias': subcategorias_resultado,
            'total_categoria': total_categoria,
            'erros': erros_gerais,
            'sucesso': len(erros_gerais) == 0
        }
    
    def calcular_completo(self, pedido, dimensionamento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula todas as categorias e retorna resultado consolidado
        """
        categorias = ['cabine', 'carrinho', 'tracao', 'sistemas']
        resultado_completo = {}
        total_geral = Decimal('0.00')
        erros_gerais = []
        
        for categoria in categorias:
            resultado_cat = self.calcular_categoria(categoria, pedido, dimensionamento)
            
            resultado_completo[categoria.upper()] = resultado_cat
            total_geral += d(resultado_cat.get('total_categoria', 0))
            
            if resultado_cat.get('erros'):
                erros_gerais.extend(resultado_cat['erros'])
        
        return {
            'categorias': resultado_completo,
            'total_geral': total_geral,
            'erros': erros_gerais,
            'sucesso': len(erros_gerais) == 0,
            'resumo': {
                cat: float(resultado_completo[cat.upper()].get('total_categoria', 0))
                for cat in categorias
            }
        }


# ============================================================================
# Integração com o Sistema Existente
# ============================================================================

def substituir_calculo_hard_coded(pedido, dimensionamento: Dict[str, Any], custos_db: Dict[str, Any]) -> Dict[str, Any]:
    """
    Função para integrar com o calculo_pedido.py existente
    Substitui apenas o cálculo de materiais, mantendo resto igual
    """
    try:
        # Usar serviço evoluído
        service = CalculoPedidoYAMLService(custos_db)
        resultado = service.calcular_completo(pedido, dimensionamento)
        
        if not resultado['sucesso']:
            raise ValueError(f"Erros no cálculo YAML: {'; '.join(resultado['erros'])}")
        
        # Retornar no formato esperado pelo calculo_pedido.py
        componentes_consolidados = resultado['categorias']
        custos_por_categoria = {
            categoria: d(dados.get('total_categoria', 0))
            for categoria, dados in componentes_consolidados.items()
        }
        
        return {
            'componentes': componentes_consolidados,
            'custos_por_categoria': custos_por_categoria,
            'total_componentes': len(componentes_consolidados),
            'custo_materiais': resultado['total_geral'],  # Este é o valor que importa
            'yaml_usado': True,
            'erros': resultado.get('erros', [])
        }
        
    except Exception as e:
        logger.error(f"Erro no cálculo YAML: {e}")
        # Fallback para cálculo original se houver erro
        raise ValueError(f"Erro no cálculo YAML: {str(e)}")