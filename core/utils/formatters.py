# =============================================================================
# ARQUIVO: core/utils/formatters.py (LIMPO)
# =============================================================================

from typing import Any, Dict, Union
from .decimal_helpers import safe_decimal, safe_float, safe_int

def formato_seguro(valor: Any, decimais: int = 2) -> float:
    """
    Formata um número com segurança, tratando possíveis erros
    
    Args:
        valor: Valor a ser formatado
        decimais: Número de casas decimais
        
    Returns:
        float: Valor formatado
    """
    try:
        numero = float(valor)
        return round(numero, decimais)
    except (ValueError, TypeError):
        return 0.0


def formato_negrito(texto: str) -> str:
    """
    Formata texto com negrito de maneira compatível com PDF e HTML
    
    Args:
        texto: Texto a ser formatado
        
    Returns:
        str: Texto formatado
    """
    return f"<strong>{texto}</strong>"


def formato_moeda_br(valor: Union[int, float, str], incluir_simbolo: bool = True) -> str:
    """
    Formata valores monetários no padrão brasileiro
    
    Args:
        valor: Valor a ser formatado
        incluir_simbolo: Se deve incluir o símbolo R$
        
    Returns:
        str: Valor formatado
    """
    try:
        if valor is None:
            return "R$ 0,00" if incluir_simbolo else "0,00"
        
        # Usar safe_float para conversão segura
        valor_float = safe_float(valor)
        
        # Formatar o número
        formatted = f"{valor_float:,.2f}"
        
        # Troca vírgula e ponto para padrão brasileiro
        formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
        
        if incluir_simbolo:
            return f"R$ {formatted}"
        return formatted
        
    except Exception:
        return "R$ 0,00" if incluir_simbolo else "0,00"


def formato_numero_br(valor: Union[int, float, str]) -> str:
    """
    Formata números para o padrão brasileiro (vírgula para decimal, ponto para milhares)
    
    Args:
        valor: Valor a ser formatado
        
    Returns:
        str: Número formatado
    """
    try:
        if valor is None:
            return "0,00"
        
        valor_float = safe_float(valor)
        formatted = f"{valor_float:,.2f}"
        
        # Troca vírgula e ponto para padrão brasileiro
        formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
        
        return formatted
        
    except Exception:
        return "0,00"


def formato_percentual_br(valor: Union[int, float, str]) -> str:
    """
    Formata percentuais no padrão brasileiro
    
    Args:
        valor: Valor a ser formatado
        
    Returns:
        str: Percentual formatado
    """
    try:
        if valor is None:
            return "0,0%"
        
        valor_float = safe_float(valor)
        formatted = f"{valor_float:.1f}".replace('.', ',')
        return f"{formatted}%"
        
    except Exception:
        return "0,0%"


def extrair_especificacoes_do_pedido(pedido) -> Dict[str, Any]:
    """
    Converte um objeto Pedido em especificações compatíveis com o sistema de cálculo
    
    Args:
        pedido: Objeto Pedido do Django
        
    Returns:
        Dict: Especificações formatadas
    """
    especificacoes = {}
    
    # === DADOS DO CLIENTE ===
    especificacoes["Solicitante"] = pedido.cliente.nome
    especificacoes["Empresa"] = pedido.cliente.nome_fantasia or ""
    especificacoes["Telefone"] = pedido.cliente.telefone or ""
    especificacoes["Email"] = pedido.cliente.email or ""
    especificacoes["Faturado por"] = pedido.faturado_por
    
    # === DADOS DO ELEVADOR ===
    especificacoes["Modelo do Elevador"] = pedido.modelo_elevador
    especificacoes["Capacidade"] = safe_float(pedido.capacidade)
    especificacoes["Capacidade (pessoas)"] = safe_int(pedido.capacidade_pessoas)
    especificacoes["Acionamento"] = pedido.acionamento
    especificacoes["Tração"] = pedido.tracao or ""
    especificacoes["Contrapeso"] = pedido.contrapeso or ""
    especificacoes["Largura do Poço"] = safe_float(pedido.largura_poco)
    especificacoes["Comprimento do Poço"] = safe_float(pedido.comprimento_poco)
    especificacoes["Altura do Poço"] = safe_float(pedido.altura_poco)
    especificacoes["Pavimentos"] = safe_int(pedido.pavimentos)
    
    # === DADOS DAS PORTAS ===
    # Porta da Cabine
    especificacoes["Modelo Porta"] = pedido.modelo_porta_cabine
    especificacoes["Material Porta"] = pedido.material_porta_cabine
    if pedido.material_porta_cabine == "Outro":
        especificacoes["Material Porta Outro Nome"] = pedido.material_porta_cabine_outro or ""
        especificacoes["Material Porta Outro Valor"] = safe_float(pedido.valor_porta_cabine_outro)
    especificacoes["Folhas Porta"] = pedido.folhas_porta_cabine or ""
    especificacoes["Largura Porta"] = safe_float(pedido.largura_porta_cabine)
    especificacoes["Altura Porta"] = safe_float(pedido.altura_porta_cabine)
    
    # Porta do Pavimento
    especificacoes["Modelo Porta Pavimento"] = pedido.modelo_porta_pavimento
    especificacoes["Material Porta Pavimento"] = pedido.material_porta_pavimento
    if pedido.material_porta_pavimento == "Outro":
        especificacoes["Material Porta Pavimento Outro Nome"] = pedido.material_porta_pavimento_outro or ""
        especificacoes["Material Porta Pavimento Outro Valor"] = safe_float(pedido.valor_porta_pavimento_outro)
    especificacoes["Folhas Porta Pavimento"] = pedido.folhas_porta_pavimento or ""
    especificacoes["Largura Porta Pavimento"] = safe_float(pedido.largura_porta_pavimento)
    especificacoes["Altura Porta Pavimento"] = safe_float(pedido.altura_porta_pavimento)
    
    # === DADOS DA CABINE ===
    especificacoes["Material"] = pedido.material_cabine
    if pedido.material_cabine == "Outro":
        especificacoes["Material Outro Nome"] = pedido.material_cabine_outro or ""
        especificacoes["Material Outro Valor"] = safe_float(pedido.valor_cabine_outro)
    especificacoes["Espessura"] = pedido.espessura_cabine
    especificacoes["Saída"] = pedido.saida_cabine
    especificacoes["Altura da Cabine"] = safe_float(pedido.altura_cabine)
    
    # Piso da Cabine
    especificacoes["Piso"] = pedido.piso_cabine
    especificacoes["Material Piso Cabine"] = pedido.material_piso_cabine or ""
    if pedido.material_piso_cabine == "Outro":
        especificacoes["Material Piso Outro Nome"] = pedido.material_piso_cabine_outro or ""
        especificacoes["Material Piso Outro Valor"] = safe_float(pedido.valor_piso_cabine_outro)
    
    return especificacoes

def agrupar_respostas_por_pagina(respostas: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Agrupa as respostas de acordo com cada página, para exibir no resumo
    
    Args:
        respostas: Dicionário com as respostas
        
    Returns:
        Dict: Respostas agrupadas por página
    """
    def get_unidade(campo: str, valor: Any, modelo: str) -> str:
        unidades = {
            "Capacidade": "pessoas" if "passageiro" in modelo.lower() else "kg",
            "Pavimentos": "",
            "Altura do Poço": "m",
            "Largura do Poço": "m", 
            "Comprimento do Poço": "m",
            "Altura da Cabine": "m",
            "Espessura": "mm",
            "Altura Porta": "m",
            "Largura Porta": "m",
            "Altura Porta Pavimento": "m",
            "Largura Porta Pavimento": "m"
        }
        return unidades.get(campo, "")

    paginas = {
        "Cliente": ["Solicitante", "Empresa", "Telefone", "Email", "Faturado por"],
        "Elevador": [
            "Modelo do Elevador", "Capacidade", "Acionamento", "Tração", "Contrapeso",
            "Largura do Poço", "Comprimento do Poço", "Altura do Poço", "Pavimentos"
        ],
        "Portas": [
            "Modelo Porta", "Material Porta", "Folhas Porta", "Altura Porta", "Largura Porta",
            "Modelo Porta Pavimento", "Material Porta Pavimento", "Folhas Porta Pavimento", 
            "Altura Porta Pavimento", "Largura Porta Pavimento"
        ],
        "Cabine": [
            "Material", "Tipo de Inox", "Espessura", "Saída", "Altura da Cabine",
            "Piso", "Material Piso Cabine"
        ]
    }

    modelo_elevador = respostas.get("Modelo do Elevador", "").lower()

    respostas_agrupadas = {}
    for pagina, campos in paginas.items():
        dados_pagina = {}
        for campo in campos:
            if campo in respostas:
                valor = respostas[campo]

                # Formatação de materiais personalizados (Outro)
                if campo in ["Material", "Material Porta", "Material Porta Pavimento"] and valor == "Outro":
                    outro_nome = respostas.get(f"{campo} Outro Nome", "")
                    outro_valor = respostas.get(f"{campo} Outro Valor", "")
                elif campo == "Material Piso Cabine" and valor == "Outro":
                    outro_nome = respostas.get("Material Piso Outro Nome", "")
                    outro_valor = respostas.get("Material Piso Outro Valor", "")
                else:
                    outro_nome, outro_valor = "", ""

                if valor == "Outro" and (outro_nome or outro_valor):
                    try:
                        # Using the local formato_moeda_br to format the 'Outro' value
                        outro_valor_formatado = formato_moeda_br(outro_valor, incluir_simbolo=False)
                    except Exception:
                        outro_valor_formatado = str(outro_valor)
                    valor = f"Outro ({outro_nome} - {outro_valor_formatado})"

                unidade = get_unidade(campo, valor, modelo_elevador)
                if unidade:
                    valor = f"{valor} {unidade}"
                
                # Special handling for 'Capacidade' to use 'Capacidade (pessoas)' if applicable
                if campo == "Capacidade" and "passageiro" in modelo_elevador:
                    if "Capacidade (pessoas)" in respostas:
                        dados_pagina["Capacidade (pessoas)"] = f"{safe_int(respostas['Capacidade (pessoas)'])} pessoas"
                    continue # Skip the general capacity if 'Capacidade (pessoas)' is more specific

                dados_pagina[campo] = valor

        if dados_pagina:
            respostas_agrupadas[pagina] = dados_pagina

    return respostas_agrupadas