# core/services/calculo_pedido_yaml.py
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

import yaml
from jinja2 import Environment, BaseLoader, StrictUndefined

from core.models import Produto

logger = logging.getLogger(__name__)
__PARSER_VERSION__ = "yaml-v1.2.0 (cabine condicoes)"

# =============================================================================
# Utils
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
    
# core/services/calculo_pedido_yaml.py - CORRIGIR FUNÇÃO _get_unit_cost

def _get_unit_cost(produto: Any) -> Decimal:
    """
    ✅ CORRIGIDO: Busca custo do produto nos campos corretos do modelo FUZA
    """
    # 1. PRIORIDADE: custo_total (property que soma custo_material + custo_servico)
    if hasattr(produto, 'custo_total') and produto.custo_total:
        return d(produto.custo_total)
    
    # 2. FALLBACK: custo_material (campo principal)
    if hasattr(produto, 'custo_material') and produto.custo_material:
        return d(produto.custo_material)
    
    # 3. FALLBACK: custo_medio (campo legacy)
    if hasattr(produto, 'custo_medio') and produto.custo_medio:
        return d(produto.custo_medio)
    
    # 4. FALLBACK: custo_total_legacy (property dos campos legacy)
    if hasattr(produto, 'custo_total_legacy') and produto.custo_total_legacy:
        return d(produto.custo_total_legacy)
    
    # 5. FALLBACK: outros campos possíveis
    for field in ("preco_custo", "preco", "valor", "price", "cost"):
        if hasattr(produto, field):
            try:
                valor = getattr(produto, field)
                if valor:
                    return d(valor)
            except Exception:
                continue
    
    # 6. Se nada funcionar, retornar zero
    return Decimal("0.00")
# =============================================================================
# Templates
# =============================================================================
class TemplateProcessor:
    def __init__(self) -> None:
        self.env = Environment(loader=BaseLoader(), undefined=StrictUndefined, autoescape=False)
        self.env.filters["d"] = d
        self.env.filters["float"] = safe_float
        self.env.filters["string"] = lambda x: "" if x is None else str(x)

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
# Processadores
# =============================================================================
class RegraProcessor:
    def __init__(self, template_proc: TemplateProcessor, custos_db: Dict[str, Produto]) -> None:
        self.template_proc = template_proc
        self.custos_db = custos_db

    def _valor_para_condicao(self, var: str, context: Dict[str, Any]) -> Any:
        ctx = context.get("ctx", {}) or {}
        for key in (var, f"{var}_cabine", f"{var}_painel"):
            if key in ctx:
                return ctx.get(key)
        return context.get(var)

    def _resolver_por_condicoes(self, regra: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        conds = regra.get("condicoes")
        if not conds:
            return out
        for cond in conds:
            q = cond.get("quando", {}) or {}
            bateu = True
            for var, esperado in q.items():
                atual = self._valor_para_condicao(var, context)
                if str(atual).strip() != str(esperado).strip():
                    bateu = False
                    break
            if bateu:
                if "codigo_produto" in cond:
                    out["codigo_produto"] = self.template_proc.render(cond["codigo_produto"], context)
                if "descricao" in cond:
                    out["descricao"] = self.template_proc.render(cond["descricao"], context)
                break
        return out

    def process_regra(self, regra: Dict[str, Any], subcat_padrao_unid: Optional[str], context: Dict[str, Any]) -> Dict[str, Any]:
        erros: List[str] = []
        nome = regra.get("nome", "")
        unidade_regra = regra.get("unidade") or subcat_padrao_unid or "un"

        escolhido = self._resolver_por_condicoes(regra, context)
        codigo_produto = escolhido.get("codigo_produto")
        if not codigo_produto and regra.get("codigo_produto"):
            codigo_produto = self.template_proc.render(regra["codigo_produto"], context).strip() or None

        qtd_expr = regra.get("quantidade", "0")
        qtd_str = self.template_proc.render(str(qtd_expr), context)
        try:
            quantidade = d(qtd_str)
        except Exception:
            quantidade = Decimal("0.00")
            erros.append(f"Quantidade inválida para '{nome}': '{qtd_str}'")

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
        }

class SubcategoriaProcessor:
    def __init__(self, template_proc: TemplateProcessor, custos_db: Dict[str, Produto]) -> None:
        self.template_proc = template_proc
        self.custos_db = custos_db
        self.regra_proc = RegraProcessor(template_proc, custos_db)

    def process_subcategoria(self, nome_subcat: str, subdef: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        unidade = subdef.get("unidade", "un")
        regras = subdef.get("regras", []) or []

        itens: List[Dict[str, Any]] = []
        erros: List[str] = []
        total_sub = Decimal("0.00")

        for regra in regras:
            item = self.regra_proc.process_regra(regra, unidade, context)
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
# Contexto
# =============================================================================

# core/services/calculo_pedido_yaml.py - CONTEXTO CORRIGIDO

class ContextBuilder:
    @staticmethod
    def build(pedido: Any, dimensionamento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constrói contexto completo e debugado para templates YAML
        ✅ CORRIGIDO: Mapeamento correto das variáveis para o YAML da cabine
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Extrair dados do dimensionamento
        cab = dimensionamento.get("cab", {}) or {}
        
        # ✅ GARANTIR que todas as sub-estruturas existam
        cab.setdefault("pnl", {})
        cab.setdefault("chp", {})
        
        # ✅ GARANTIR valores padrão para painéis (pnl)
        for k in ("lateral", "fundo", "teto"):
            cab["pnl"].setdefault(k, 0)
        
        # ✅ GARANTIR valores padrão para chapas (chp)  
        for k in ("corpo", "piso"):
            cab["chp"].setdefault(k, 0)

        # ✅ MAPEAMENTO CORRETO das variáveis do pedido para o YAML
        ctx = {
            # === MATERIAL DA CABINE ===
            "material": getattr(pedido, "material_cabine", ""),  # ← YAML usa "material"
            "material_cabine": getattr(pedido, "material_cabine", ""),  # ← Compatibilidade
            
            # === ESPESSURA ===
            "espessura": getattr(pedido, "espessura_cabine", ""),  # ← YAML usa "espessura"
            "espessura_cabine": getattr(pedido, "espessura_cabine", ""),  # ← Compatibilidade
            
            # === PISO ===
            "piso_cabine": getattr(pedido, "piso_cabine", ""),
            "material_piso_cabine": getattr(pedido, "material_piso_cabine", ""),
            
            # === OUTROS CAMPOS IMPORTANTES ===
            "capacidade": getattr(pedido, "capacidade", ""),
            "modelo_elevador": getattr(pedido, "modelo_elevador", ""),
            "acionamento": getattr(pedido, "acionamento", ""),
            
            # === ALIASES EXTRAS PARA COMPATIBILIDADE ===
            "material_painel": getattr(pedido, "material_cabine", ""),
            "espessura_painel": getattr(pedido, "espessura_cabine", ""),
        }

        # ✅ DEBUG: Log das variáveis principais
        logger.info(f"=== CONTEXTO PARA YAML CABINE ===")
        logger.info(f"📊 DIMENSIONAMENTO:")
        logger.info(f"  - cab.chp.corpo: {cab['chp']['corpo']}")
        logger.info(f"  - cab.chp.piso: {cab['chp']['piso']}")
        logger.info(f"  - cab.pnl.lateral: {cab['pnl']['lateral']}")
        logger.info(f"  - cab.pnl.fundo: {cab['pnl']['fundo']}")
        logger.info(f"  - cab.pnl.teto: {cab['pnl']['teto']}")
        logger.info(f"")
        logger.info(f"🎨 ESPECIFICAÇÕES:")
        logger.info(f"  - ctx.material: '{ctx['material']}'")
        logger.info(f"  - ctx.espessura: '{ctx['espessura']}'")
        logger.info(f"  - ctx.piso_cabine: '{ctx['piso_cabine']}'")
        logger.info(f"  - ctx.material_piso_cabine: '{ctx['material_piso_cabine']}'")

        # ✅ ESTRUTURA FINAL DO CONTEXTO
        context = {
            "ctx": ctx,
            "cab": cab,
            "chp": cab["chp"],  # ← ACESSO DIRETO para templates
            "pnl": cab["pnl"],  # ← ACESSO DIRETO para templates
            "pedido": pedido,
            "dimensionamento": dimensionamento,
        }
        
        return context

# =============================================================================
# Serviço principal
# =============================================================================
class CalculoPedidoYAMLService:
    def __init__(self, custos_db: Dict[str, Produto]) -> None:
        self.custos_db = custos_db
        self.template_proc = TemplateProcessor()
        self.subcat_proc = SubcategoriaProcessor(self.template_proc, custos_db)
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
            registro = (
                RegraYAML.objects.filter(ativa=True, nome__icontains=slug)
                .order_by("-atualizado_em")
                .first()
            )
        if not registro:
            raise ValueError(f"Nenhum YAML encontrado para a categoria '{slug}' (tipo/nome).")

        raw = getattr(registro, "conteudo_yaml", None)
        if not raw or not str(raw).strip():
            raise ValueError(f"Registro YAML '{registro.id}' não possui 'conteudo_yaml'.")

        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            raise ValueError("Estrutura YAML raiz não é dict.")
        return data

    # ---------- calcular apenas 1 categoria (ex.: 'cabine') -------------------
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

        context = ContextBuilder.build(pedido, dimensionamento)

        resultado_subcats: Dict[str, Any] = {}
        erros_cat: List[str] = []
        total_categoria = Decimal("0.00")
        itens_flat: List[Dict[str, Any]] = []

        for nome_subcat, subdef in subcats.items():
            subres = self.subcat_proc.process_subcategoria(nome_subcat, subdef, context)
            resultado_subcats[nome_subcat] = subres
            total_categoria += d(subres.get("total_subcategoria", 0))
            if not subres.get("sucesso", True):
                erros_cat.extend(subres.get("erros", []))
            itens_flat.extend(subres.get("itens", []))

        return {
            "categoria": nome_categoria,
            "subcategorias": resultado_subcats,
            "itens": itens_flat,
            "total_categoria": float(total_categoria),
            "erros": erros_cat,
            "sucesso": len(erros_cat) == 0,
        }

    # ---------- calcular várias categorias (lista de slugs) -------------------
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

    # ---------- helpers conveniência ------------------------------------------
    def calcular_somente(self, categorias: List[str], pedido: Any, dimensionamento: Dict[str, Any]) -> Dict[str, Any]:
        categorias = categorias or ["cabine"]
        return self.calcular_completo(pedido, dimensionamento, categorias=categorias)

    def calcular_somente_cabine(self, pedido: Any, dimensionamento: Dict[str, Any]) -> Dict[str, Any]:
        return self.calcular_somente(["cabine"], pedido, dimensionamento)