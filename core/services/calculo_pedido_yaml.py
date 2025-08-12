# core/services/calculo_pedido_yaml.py - PARSER AVANÇADO

import logging
import math
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

import yaml
from jinja2 import Environment, BaseLoader, StrictUndefined

from core.models import Produto

logger = logging.getLogger(__name__)
__PARSER_VERSION__ = "yaml-v2.0.0 (avançado com ranges e operadores)"

# =============================================================================
# Utils Avançados
# =============================================================================
def d(x: Any, default: str = "0.00") -> Decimal:
    if x is None or x == "":
        return Decimal(default)
    if isinstance(x, Decimal):
        return x
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal(default)

def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default

def safe_int(x: Any, default: int = 0) -> int:
    try:
        if x is None or x == "":
            return default
        return int(float(x))  # Converte via float primeiro para aceitar "2.0"
    except Exception:
        return default

def _get_unit_cost(produto: Any) -> Decimal:
    """Busca custo do produto nos campos corretos do modelo FUZA"""
    if hasattr(produto, 'custo_total') and produto.custo_total:
        return d(produto.custo_total)
    if hasattr(produto, 'custo_material') and produto.custo_material:
        return d(produto.custo_material)
    if hasattr(produto, 'custo_medio') and produto.custo_medio:
        return d(produto.custo_medio)
    if hasattr(produto, 'custo_total_legacy') and produto.custo_total_legacy:
        return d(produto.custo_total_legacy)
    return Decimal("0.00")

# =============================================================================
# Comparadores Avançados
# =============================================================================
class AdvancedComparator:
    """Classe para comparações avançadas em condições YAML"""
    
    @staticmethod
    def compare_value(actual_value: Any, expected_condition: str) -> bool:
        """
        Compara valor real com condição YAML avançada
        
        Suporta:
        - "1000" (exato)
        - "<=1000" (menor ou igual)
        - ">=1000" (maior ou igual)  
        - ">1000" (maior que)
        - "<1000" (menor que)
        - "!=Motor" (diferente)
        - "Motor" (exato string)
        """
        try:
            condition_str = str(expected_condition).strip()
            
            # Operadores de comparação
            if condition_str.startswith("<="):
                threshold = float(condition_str[2:])
                return float(actual_value) <= threshold
            elif condition_str.startswith(">="):
                threshold = float(condition_str[2:])
                return float(actual_value) >= threshold
            elif condition_str.startswith("!="):
                expected = condition_str[2:].strip()
                return str(actual_value).strip() != expected
            elif condition_str.startswith(">"):
                threshold = float(condition_str[1:])
                return float(actual_value) > threshold
            elif condition_str.startswith("<"):
                threshold = float(condition_str[1:])
                return float(actual_value) < threshold
            else:
                # Comparação exata (string ou numérica)
                try:
                    # Tentar comparação numérica
                    return float(actual_value) == float(condition_str)
                except (ValueError, TypeError):
                    # Comparação string
                    return str(actual_value).strip() == condition_str.strip()
                    
        except (ValueError, TypeError) as e:
            logger.warning(f"Erro na comparação: {actual_value} vs {expected_condition}: {e}")
            return False

# =============================================================================
# Templates Avançados
# =============================================================================
class AdvancedTemplateProcessor:
    def __init__(self) -> None:
        self.env = Environment(loader=BaseLoader(), undefined=StrictUndefined, autoescape=False)
        self.env.filters["d"] = d
        self.env.filters["float"] = safe_float
        self.env.filters["int"] = safe_int
        self.env.filters["string"] = lambda x: "" if x is None else str(x)
        
        # ✅ FILTROS MATEMÁTICOS AVANÇADOS
        self.env.filters["round"] = self._advanced_round
        self.env.filters["ceil"] = lambda x: math.ceil(float(x))
        self.env.filters["floor"] = lambda x: math.floor(float(x))
        self.env.filters["abs"] = lambda x: abs(float(x))
        self.env.filters["max"] = lambda x, y: max(float(x), float(y))
        self.env.filters["min"] = lambda x, y: min(float(x), float(y))

    def _advanced_round(self, value: Any, precision: int = 0, method: str = 'round') -> float:
        """
        Filtro de arredondamento avançado
        method: 'round', 'ceil', 'floor'
        """
        try:
            val = float(value)
            if method == 'ceil':
                return math.ceil(val * (10 ** precision)) / (10 ** precision)
            elif method == 'floor':
                return math.floor(val * (10 ** precision)) / (10 ** precision)
            else:  # 'round'
                return round(val, precision)
        except Exception:
            return 0.0

    def render(self, tpl: Any, context: Dict[str, Any]) -> str:
        if tpl is None:
            return ""
        if not isinstance(tpl, str):
            return str(tpl)
        try:
            return self.env.from_string(tpl).render(**context)
        except Exception as e:
            logger.error(f"[TPL] Erro ao renderizar '{tpl}': {e}")
            return ""

# =============================================================================
# Processadores Avançados
# =============================================================================
class AdvancedRegraProcessor:
    def __init__(self, template_proc: AdvancedTemplateProcessor, custos_db: Dict[str, Produto]) -> None:
        self.template_proc = template_proc
        self.custos_db = custos_db
        self.comparator = AdvancedComparator()

    def _valor_para_condicao(self, var: str, context: Dict[str, Any]) -> Any:
        """Busca valor da variável no contexto, com fallbacks"""
        ctx = context.get("ctx", {}) or {}
        cab = context.get("cab", {}) or {}
        
        # ✅ BUSCA EXPANDIDA
        search_keys = [
            var,
            f"{var}_cabine",
            f"{var}_painel",
            f"ctx.{var}",
            f"cab.{var}"
        ]
        
        # Buscar em ctx primeiro
        for key in search_keys:
            if key in ctx and ctx[key] is not None:
                return ctx[key]
        
        # Buscar em cab
        if var in cab and cab[var] is not None:
            return cab[var]
            
        # Buscar no context geral
        if var in context and context[var] is not None:
            return context[var]
            
        return None

    def _resolver_por_condicoes(self, regra: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve condições avançadas com operadores"""
        out: Dict[str, Any] = {}
        conds = regra.get("condicoes")
        if not conds:
            return out
            
        for cond in conds:
            q = cond.get("quando", {}) or {}
            bateu = True
            
            # ✅ COMPARAÇÕES AVANÇADAS
            for var, esperado in q.items():
                atual = self._valor_para_condicao(var, context)
                if atual is None:
                    logger.warning(f"Variável '{var}' não encontrada no contexto")
                    bateu = False
                    break
                    
                # ✅ USAR COMPARADOR AVANÇADO
                if not self.comparator.compare_value(atual, esperado):
                    bateu = False
                    break
                    
            if bateu:
                if "codigo_produto" in cond:
                    out["codigo_produto"] = self.template_proc.render(cond["codigo_produto"], context)
                if "descricao" in cond:
                    out["descricao"] = self.template_proc.render(cond["descricao"], context)
                break  # Primeira condição que bater
                
        return out

    def process_regra(self, regra: Dict[str, Any], subcat_padrao_unid: Optional[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Processa regra com lógica avançada"""
        erros: List[str] = []
        nome = regra.get("nome", "")
        unidade_regra = regra.get("unidade") or subcat_padrao_unid or "un"

        # ✅ RESOLVER CONDIÇÕES AVANÇADAS
        escolhido = self._resolver_por_condicoes(regra, context)
        codigo_produto = escolhido.get("codigo_produto")
        
        # Fallback para código direto
        if not codigo_produto and regra.get("codigo_produto"):
            codigo_produto = self.template_proc.render(regra["codigo_produto"], context).strip() or None

        # ✅ QUANTIDADE COM TEMPLATES AVANÇADOS
        qtd_expr = regra.get("quantidade", "0")
        qtd_str = self.template_proc.render(str(qtd_expr), context)
        try:
            quantidade = d(qtd_str)
            # ✅ PROTEÇÃO: Se quantidade for 0, não adicionar item
            if quantidade <= 0:
                return {
                    "nome": nome,
                    "codigo": codigo_produto or "",
                    "quantidade": 0,
                    "valor_total": 0,
                    "sucesso": True,
                    "skip": True  # ✅ FLAG para pular item
                }
        except Exception as e:
            quantidade = Decimal("0.00")
            erros.append(f"Quantidade inválida para '{nome}': '{qtd_str}' - {e}")

        explicacao_tpl = regra.get("explicacao")
        explicacao = self.template_proc.render(explicacao_tpl, context) if explicacao_tpl else ""
        descricao_forcada = escolhido.get("descricao")

        produto = None
        valor_unitario = Decimal("0.00")
        if codigo_produto:
            produto = self.custos_db.get(codigo_produto)
            if not produto:
                erros.append(f"Código '{codigo_produto}' não encontrado")
            else:
                valor_unitario = _get_unit_cost(produto)
        else:
            if quantidade > 0:  # Só reclamar se quantidade > 0
                erros.append(f"Regra '{nome}': nenhum código de produto determinado")

        valor_total = (quantidade * valor_unitario).quantize(Decimal("0.01"))

        if descricao_forcada:
            descricao_final = descricao_forcada
        else:
            if produto and hasattr(produto, "nome") and getattr(produto, "nome"):
                descricao_final = produto.nome
            elif produto and hasattr(produto, "descricao") and getattr(produto, "descricao"):
                descricao_final = produto.descricao
            else:
                descricao_final = nome or (codigo_produto or "")

        return {
            "nome": nome,
            "codigo": codigo_produto or "",
            "descricao": descricao_final,
            "quantidade": float(quantidade),
            "unidade": unidade_regra,
            "valor_unitario": float(valor_unitario),
            "valor_total": float(valor_total),
            "explicacao": explicacao,
            "sucesso": len(erros) == 0,
            "erros": erros,
            "skip": False
        }

class AdvancedSubcategoriaProcessor:
    def __init__(self, template_proc: AdvancedTemplateProcessor, custos_db: Dict[str, Produto]) -> None:
        self.template_proc = template_proc
        self.custos_db = custos_db
        self.regra_proc = AdvancedRegraProcessor(template_proc, custos_db)

    def process_subcategoria(self, nome_subcat: str, subdef: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        unidade = subdef.get("unidade", "un")
        regras = subdef.get("regras", []) or []

        itens: List[Dict[str, Any]] = []
        erros: List[str] = []
        total_sub = Decimal("0.00")

        for regra in regras:
            item = self.regra_proc.process_regra(regra, unidade, context)
            
            # ✅ PULAR ITENS COM QUANTIDADE 0
            if not item.get("skip", False):
                itens.append(item)
                total_sub += d(item.get("valor_total", 0))
                
            if not item.get("sucesso", True):
                erros.extend(item.get("erros", []))

        return {
            "nome": nome_subcat,
            "unidade": unidade,
            "itens": itens,
            "total_subcategoria": float(total_sub),
            "erros": erros,
            "sucesso": len(erros) == 0,
        }

# =============================================================================
# Context Builder Avançado
# =============================================================================
class AdvancedContextBuilder:
    @staticmethod
    def build(pedido: Any, dimensionamento: Dict[str, Any]) -> Dict[str, Any]:
        """Constrói contexto completo e detalhado para TODOS os YAMLs avançados"""
        import logging
        logger = logging.getLogger(__name__)
        
        cab = dimensionamento.get("cab", {}) or {}
        cab.setdefault("pnl", {})
        cab.setdefault("chp", {})
        
        for k in ("lateral", "fundo", "teto"):
            cab["pnl"].setdefault(k, 0)
        for k in ("corpo", "piso"):
            cab["chp"].setdefault(k, 0)

        # ✅ CONTEXTO COMPLETO E DETALHADO
        ctx = {
            # === CABINE ===
            "material": getattr(pedido, "material_cabine", ""),
            "material_cabine": getattr(pedido, "material_cabine", ""),
            "espessura": getattr(pedido, "espessura_cabine", ""),
            "espessura_cabine": getattr(pedido, "espessura_cabine", ""),
            "piso_cabine": getattr(pedido, "piso_cabine", ""),
            "material_piso_cabine": getattr(pedido, "material_piso_cabine", ""),
            
            # === DADOS BÁSICOS ===
            "capacidade": float(getattr(pedido, "capacidade", 0) or 0),
            "modelo_elevador": getattr(pedido, "modelo_elevador", ""),
            "acionamento": getattr(pedido, "acionamento", ""),
            "tracao": getattr(pedido, "tracao", ""),
            "contrapeso": getattr(pedido, "contrapeso", ""),
            
            # === DIMENSÕES POÇO ===
            "largura_poco": float(getattr(pedido, "largura_poco", 0) or 0),
            "comprimento_poco": float(getattr(pedido, "comprimento_poco", 0) or 0),
            "altura_poco": float(getattr(pedido, "altura_poco", 0) or 0),
            "pavimentos": int(getattr(pedido, "pavimentos", 0) or 0),
            
            # === DIMENSÕES CALCULADAS ===
            "largura_cabine": float(cab.get('largura', 0) or 0),
            "comprimento_cabine": float(cab.get('compr', 0) or 0),
            "capacidade_cabine": float(cab.get('capacidade', 0) or 0),
            "tracao_cabine": float(cab.get('tracao', 0) or 0),
        }

        # ✅ DEBUG COMPLETO
        logger.info(f"=== CONTEXTO AVANÇADO PARA TODOS OS YAMLs ===")
        logger.info(f"📊 DIMENSIONAMENTO: capacidade={cab.get('capacidade')}, largura={cab.get('largura')}, compr={cab.get('compr')}")
        logger.info(f"🎨 ESPECIFICAÇÕES: acionamento='{ctx['acionamento']}', tracao='{ctx['tracao']}', contrapeso='{ctx['contrapeso']}'")
        logger.info(f"📏 POÇO: {ctx['largura_poco']}x{ctx['comprimento_poco']}x{ctx['altura_poco']}m, {ctx['pavimentos']} pavimentos")

        context = {
            "ctx": ctx,
            "cab": cab,
            "chp": cab["chp"],
            "pnl": cab["pnl"],
            "pedido": pedido,
            "dimensionamento": dimensionamento,
        }
        
        return context

# =============================================================================
# Serviço Principal Avançado
# =============================================================================
class CalculoPedidoYAMLService:
    def __init__(self, custos_db: Dict[str, Produto]) -> None:
        self.custos_db = custos_db
        self.template_proc = AdvancedTemplateProcessor()
        self.subcat_proc = AdvancedSubcategoriaProcessor(self.template_proc, custos_db)
        logger.info(f"[CalculoPedidoYAMLService] carregado {__PARSER_VERSION__}")

    def _load_yaml_dict(self, categoria_slug: str) -> Dict[str, Any]:
        from core.models.regras_yaml import RegraYAML
        slug = (categoria_slug or "").strip().lower()

        registro = (
            RegraYAML.objects.filter(ativa=True, tipo__iexact=slug)
            .order_by("-atualizado_em")
            .first()
        )
        if not registro:
            raise ValueError(f"Nenhum YAML encontrado para a categoria '{slug}'.")

        raw = getattr(registro, "conteudo_yaml", None)
        if not raw or not str(raw).strip():
            raise ValueError(f"Registro YAML '{registro.id}' não possui conteúdo.")

        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            raise ValueError("Estrutura YAML raiz não é dict.")
        return data

    def calcular_categoria(self, categoria_slug: str, pedido: Any, dimensionamento: Dict[str, Any]) -> Dict[str, Any]:
        slug = (categoria_slug or "").strip().lower()
        if not slug:
            raise ValueError("Categoria não informada.")

        yaml_dict = self._load_yaml_dict(slug)
        cat_def = yaml_dict[slug] if slug in yaml_dict else yaml_dict
        if not isinstance(cat_def, dict):
            raise ValueError(f"Bloco da categoria '{slug}' inválido.")

        nome_categoria = (cat_def.get("categoria") or slug).upper()
        subcats = cat_def.get("subcategorias", {}) or {}
        if not isinstance(subcats, dict):
            raise ValueError(f"Categoria '{nome_categoria}' sem 'subcategorias' válidas.")

        # ✅ USAR CONTEXT BUILDER AVANÇADO
        context = AdvancedContextBuilder.build(pedido, dimensionamento)

        resultado_subcats: Dict[str, Any] = {}
        erros_cat: List[str] = []
        total_categoria = Decimal("0.00")
        itens_flat: List[Dict[str, Any]] = []

        for nome_subcat, subdef in subcats.items():
            subres = self.subcat_proc.process_subcategoria(nome_subcat, subdef, context)
            
            # ✅ CONVERTER para compatibilidade com template
            if 'itens' in subres and isinstance(subres['itens'], list):
                itens_lista = subres['itens']
                itens_dict = {}
                for item in itens_lista:
                    codigo = item.get('codigo', item.get('nome', f'item_{len(itens_dict)}'))
                    itens_dict[codigo] = item
                subres['itens'] = itens_dict
            
            resultado_subcats[nome_subcat] = subres
            total_categoria += d(subres.get("total_subcategoria", 0))
            if not subres.get("sucesso", True):
                erros_cat.extend(subres.get("erros", []))
            itens_flat.extend(subres.get("itens", []) if isinstance(subres.get("itens", []), list) else list(subres.get("itens", {}).values()))

        return {
            "categoria": nome_categoria,
            "subcategorias": resultado_subcats,
            "itens": itens_flat,
            "total_categoria": float(total_categoria),
            "erros": erros_cat,
            "sucesso": len(erros_cat) == 0,
        }

    def calcular_completo(self, pedido: Any, dimensionamento: Dict[str, Any], categorias: Optional[List[str]] = None) -> Dict[str, Any]:
        if not categorias:
            categorias = ["cabine"]
        resumo: Dict[str, float] = {}
        erros_totais: List[str] = []
        categorias_dict: Dict[str, Any] = {}
        total_geral = Decimal("0.00")

        for slug in categorias:
            r = self.calcular_categoria(slug, pedido, dimensionamento)
            categorias_dict[r["categoria"]] = r
            total_geral += d(r.get("total_categoria", 0))
            resumo[r["categoria"]] = float(r.get("total_categoria", 0))
            if not r.get("sucesso", True):
                erros_totais.extend(r.get("erros", []))

        return {
            "categorias": categorias_dict,
            "total_geral": float(total_geral),
            "resumo": resumo,
            "erros": erros_totais,
            "sucesso": len(erros_totais) == 0,
        }