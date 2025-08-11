# core/services/calculo_pedido_yaml.py
from decimal import Decimal
from typing import Any, Dict, List, Optional
import math
import yaml

from core.models import Produto
from core.models.regras_yaml import RegraYAML

# ------------------------------------------------------------
# Loader das regras (DB -> dict)
# ------------------------------------------------------------
class ConfigRepoDB:
    def load(self, nome: str) -> Dict[str, Any]:
        obj = (RegraYAML.objects
               .filter(tipo=nome, ativa=True)
               .order_by("-atualizado_em")
               .first())
        if not obj:
            return {}
        return yaml.safe_load(obj.conteudo_yaml) or {}

# ------------------------------------------------------------
# Utilitários p/ fórmulas (whitelist)
# ------------------------------------------------------------
SAFE_FUNCS = {
    "abs": abs,
    "ceil": math.ceil,
    "floor": math.floor,
    "min": min,
    "max": max,
    "round": round,
}
def case(*args):
    # case(cond1, val1, cond2, val2, ..., default)
    if not args:
        return None
    if len(args) % 2 == 0:
        args = (*args, None)
    *pairs, default = args
    for i in range(0, len(pairs), 2):
        if pairs[i]:
            return pairs[i+1]
    return default
SAFE_FUNCS["case"] = case

def _eval_formula(expr: str, ctx: Dict[str, Any]) -> Decimal:
    if not expr:
        return Decimal("0")
    class DotDict(dict):
        __getattr__ = dict.get
    safe_ctx = {k: DotDict(v) if isinstance(v, dict) else v for k, v in ctx.items()}
    safe_ctx.update(SAFE_FUNCS)
    val = eval(expr, {"__builtins__": {}}, safe_ctx)  # ambiente fechado
    return Decimal(str(val))

# ------------------------------------------------------------
# Resolvers de regras
# ------------------------------------------------------------
def _resolve_painel_catalogo(cfg: Dict[str, Any], material: str, esp: str) -> Optional[str]:
    for row in (cfg.get("painel_catalogo") or []):
        if str(row.get("material")) == str(material) and str(row.get("espessura")) == str(esp):
            return row.get("codigo_produto")
    return None

def _resolve_by_capacidade(rules, cap: float) -> Optional[str]:
    for r in (rules or []):
        mn, mx = r.get("min"), r.get("max")
        if (mn is None or cap >= mn) and (mx is None or cap <= mx):
            return r.get("codigo_produto")
    return None

def _resolve_by_cap_vel(rules, cap: float, vel: float) -> Optional[str]:
    for r in (rules or []):
        ok_cap = (r.get("cap_min") is None or cap >= r["cap_min"]) and (r.get("cap_max") is None or cap <= r["cap_max"])
        ok_vel = (r.get("vel_max") is None or vel <= r["vel_max"])
        if ok_cap and ok_vel:
            return r.get("codigo_produto")
    return None

def _resolve_by_tipo_vao(rules, tipo: str, vao: float, folhas: int) -> Optional[str]:
    for r in (rules or []):
        if (r.get("tipo") == tipo) and \
           (r.get("vao_min") is None or vao >= r["vao_min"]) and (r.get("vao_max") is None or vao <= r["vao_max"]) and \
           (r.get("folhas") is None or folhas == r["folhas"]):
            return r.get("codigo_produto")
    return None

def _resolve_by_linha(rules, linha: str) -> Optional[str]:
    for r in (rules or []):
        if r.get("linha") == linha:
            return r.get("codigo_produto")
    return None

# ------------------------------------------------------------
# Agregador de itens
# ------------------------------------------------------------
def _add_item(itens, custos_db, codigo: str, qtd: Decimal, origem: str, trace: List[Dict[str, Any]]):
    if not codigo or qtd <= 0:
        return
    prod = custos_db.get(codigo) or Produto.objects.filter(codigo=codigo).first()
    if not prod:
        trace.append({"origem": origem, "codigo": codigo, "qtd": str(qtd), "motivo": "produto_nao_encontrado"})
        return
    vu = Decimal(str(getattr(prod, "custo_total", "0")))
    if codigo not in itens:
        itens[codigo] = {
            "codigo": codigo,
            "descricao": getattr(prod, "nome", ""),
            "quantidade": Decimal("0"),
            "valor_unitario": vu,
            "valor_total": Decimal("0"),
        }
    itens[codigo]["quantidade"] += qtd
    itens[codigo]["valor_total"] = (itens[codigo]["quantidade"] * itens[codigo]["valor_unitario"]).quantize(Decimal("0.01"))
    trace.append({"origem": origem, "codigo": codigo, "qtd": str(qtd), "motivo": "ok"})

# ------------------------------------------------------------
# Cálculo de cada bloco
# ------------------------------------------------------------
def _calc_cabine(cfg: Dict[str, Any], ctx: Dict[str, Any], custos_db) -> Dict[str, Any]:
    cab = cfg.get("cabine") or {}
    itens, trace = {}, []

    # 1) PAINEL (lookup material+espessura)
    codigo = _resolve_painel_catalogo(cab, ctx["ped"].get("material_cabine"), ctx["ped"].get("espessura_cabine"))
    if codigo:
        qtd = Decimal(str(
            (ctx["pnl"].get("lateral",0) or 0) +
            (ctx["pnl"].get("fundo",0)   or 0) +
            (ctx["pnl"].get("teto",0)    or 0)
        ))
        _add_item(itens, custos_db, codigo, qtd, "cabine.painel", trace)

    # 2) FIXAÇÃO PAINÉIS
    node = cab.get("fixacao_paineis") or {}
    codigo = node.get("codigo_produto")
    if codigo:
        qtd = _eval_formula(node.get("qty_formula","0"), ctx)
        _add_item(itens, custos_db, codigo, qtd, "cabine.fixacao_paineis", trace)

    # 3) PISO (empresa/cliente + antiderrapante)
    piso = cab.get("piso") or {}
    if ctx["ped"].get("piso_cabine") == "Por conta da empresa":
        codigo = piso.get("empresa_antiderrapante") if ctx["ped"].get("material_piso_cabine") == "Antiderrapante" else piso.get("empresa_outros")
    else:
        codigo = piso.get("cliente")
    if codigo:
        qtd = Decimal(str(ctx["chp"].get("piso",0) or 0))
        _add_item(itens, custos_db, codigo, qtd, "cabine.piso", trace)

    # 4) FIXAÇÃO PISO
    node = cab.get("fixacao_piso") or {}
    codigo = node.get("codigo_produto")
    if codigo:
        qtd = _eval_formula(node.get("qty_formula","0"), ctx)
        _add_item(itens, custos_db, codigo, qtd, "cabine.fixacao_piso", trace)

    subtotal = sum((v["valor_total"] for v in itens.values()), Decimal("0.00"))
    return {"itens": itens, "subtotal": subtotal, "trace": trace}

def _calc_generico(nome_bloco: str, cfg: Dict[str, Any], ctx: Dict[str, Any], custos_db) -> Dict[str, Any]:
    bloco = cfg.get(nome_bloco) or {}
    itens, trace = {}, []
    dim, ped = ctx.get("dim", {}), ctx.get("ped", {})

    for sub, node in bloco.items():
        codigo = None
        if "codigo_produto" in node:
            codigo = node["codigo_produto"]
        elif "by_capacidade" in node:
            codigo = _resolve_by_capacidade(node["by_capacidade"], float(dim.get("capacidade", 0)))
        elif "by_capacidade_e_velocidade" in node:
            codigo = _resolve_by_cap_vel(
                node["by_capacidade_e_velocidade"], float(dim.get("capacidade", 0)), float(dim.get("velocidade", 0))
            )
        elif "by_tipo_e_vao" in node:
            codigo = _resolve_by_tipo_vao(
                node["by_tipo_e_vao"], ped.get("tipo_porta"), float(dim.get("vao_porta", 0)), int(dim.get("folhas_porta", 0))
            )
        elif "by_linha" in node:
            codigo = _resolve_by_linha(node["by_linha"], ped.get("linha_produto"))

        if not codigo:
            trace.append({"origem": f"{nome_bloco}.{sub}", "motivo": "nao_resolvido"})
            continue

        expr = node.get("qty_formula", "1")
        qtd = _eval_formula(expr, ctx) if isinstance(expr, str) else Decimal(str(expr))
        _add_item(itens, custos_db, codigo, qtd, f"{nome_bloco}.{sub}", trace)

    subtotal = sum((v["valor_total"] for v in itens.values()), Decimal("0.00"))
    return {"itens": itens, "subtotal": subtotal, "trace": trace}

# ------------------------------------------------------------
# Serviço unificado (substitui o calculo_pedido antigo)
# ------------------------------------------------------------
class CalculoPedidoYAMLService:
    """
    Serviço único: lê regras YAML do banco (cabine, carrinho, tracao, sistemas),
    executa os cálculos e retorna o resultado consolidado.
    """

    def __init__(self, custos_db: Optional[Dict[str, Any]] = None, repo: Optional[ConfigRepoDB] = None):
        self.custos_db = custos_db or {}
        self.repo = repo or ConfigRepoDB()

    def _build_ctx(self, pedido, dimm: Dict[str, Any]) -> Dict[str, Any]:
        pnl = dimm.get("paineis", {}) or {}
        chp = {"piso": dimm.get("chapas_piso", 0)}
        dim = {
            "capacidade": getattr(pedido, "capacidade", None) or dimm.get("capacidade"),
            "velocidade": getattr(pedido, "velocidade", None) or dimm.get("velocidade"),
            "paradas": dimm.get("paradas"),
            "curso": dimm.get("curso"),
            "vao_porta": dimm.get("vao_porta"),
            "folhas_porta": dimm.get("folhas_porta"),
            "comprimento_cabine": dimm.get("comprimento_cabine"),
        }
        ped = {
            "material_cabine": getattr(pedido, "material_cabine", None),
            "espessura_cabine": getattr(pedido, "espessura_cabine", None),
            "piso_cabine": getattr(pedido, "piso_cabine", None),
            "material_piso_cabine": getattr(pedido, "material_piso_cabine", None),
            "tipo_porta": getattr(pedido, "tipo_porta", None),
            "linha_produto": getattr(pedido, "linha_produto", None),
        }
        return {"pnl": pnl, "chp": chp, "dim": dim, "ped": ped, "fix": {}}

    def calcular(self, pedido, dimensionamento: Dict[str, Any]) -> Dict[str, Any]:
        ctx = self._build_ctx(pedido, dimensionamento)

        resultado_por_bloco: Dict[str, Dict[str, Any]] = {}
        total_geral = Decimal("0.00")
        trace_all: List[Dict[str, Any]] = []

        # CABINE
        cfg_cab = self.repo.load("cabine")
        res = _calc_cabine(cfg_cab, ctx, self.custos_db)
        resultado_por_bloco["cabine"] = res
        total_geral += res["subtotal"]; trace_all += res["trace"]

        # CARRINHO
        cfg_car = self.repo.load("carrinho")
        res = _calc_generico("carrinho", cfg_car, ctx, self.custos_db)
        resultado_por_bloco["carrinho"] = res
        total_geral += res["subtotal"]; trace_all += res["trace"]

        # TRAÇÃO
        cfg_tr = self.repo.load("tracao")
        res = _calc_generico("tracao", cfg_tr, ctx, self.custos_db)
        resultado_por_bloco["tracao"] = res
        total_geral += res["subtotal"]; trace_all += res["trace"]

        # SISTEMAS
        cfg_sys = self.repo.load("sistemas")
        res = _calc_generico("sistemas", cfg_sys, ctx, self.custos_db)
        resultado_por_bloco["sistemas"] = res
        total_geral += res["subtotal"]; trace_all += res["trace"]

        # consolidação por código
        itens_consolidados: Dict[str, Dict[str, Any]] = {}
        for res in resultado_por_bloco.values():
            for codigo, item in res["itens"].items():
                if codigo not in itens_consolidados:
                    itens_consolidados[codigo] = item.copy()
                else:
                    itens_consolidados[codigo]["quantidade"] += item["quantidade"]
                    itens_consolidados[codigo]["valor_total"] = (
                        itens_consolidados[codigo]["quantidade"] * itens_consolidados[codigo]["valor_unitario"]
                    ).quantize(Decimal("0.01"))

        return {
            "itens_consolidados": itens_consolidados,
            "subtotal_por_bloco": {k: v["subtotal"] for k, v in resultado_por_bloco.items()},
            "total_geral": total_geral.quantize(Decimal("0.01")),
            "trace": trace_all,
        }