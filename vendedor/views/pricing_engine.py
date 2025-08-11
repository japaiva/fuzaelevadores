# core/services/pricing_engine.py
from decimal import Decimal

def calcular_precos(custo_total: Decimal, params: dict) -> dict:
    """
    Aplica margem, comissão e impostos por dentro (gross-up) e deriva lista/mínimo.
    params espera chaves: 'margem', 'comissao', f'fat.{faturado_por}'
    """
    def d(x, default='0'):
        return Decimal(str(x if x is not None else default))

    m = d(params.get('margem', 0)) / Decimal('100')
    c = d(params.get('comissao', 0)) / Decimal('100')
    t = d(params.get(params.get('_chave_imposto', ''), params.get('imposto', 0))) / Decimal('100')

    # gross-up para manter margem por dentro com comissão e impostos
    denom = (Decimal('1') - c) * (Decimal('1') - t)
    preco_final = (custo_total * (Decimal('1') + m)) / (denom if denom != 0 else Decimal('1'))

    # políticas simples (ajuste se tiver regras próprias)
    fator_lista = Decimal('1.05')
    fator_min   = Decimal('0.95')

    return {
        "custo_total": custo_total.quantize(Decimal('0.01')),
        "preco_final": preco_final.quantize(Decimal('0.01')),
        "preco_lista": (preco_final * fator_lista).quantize(Decimal('0.01')),
        "preco_minimo": (preco_final * fator_min).quantize(Decimal('0.01')),
        "margem": m, "comissao": c, "impostos": t
    }