# core/services/dimensionamento.py

import math
import logging

logger = logging.getLogger(__name__)


class DimensionamentoService:
    """
    Serviço responsável pelos cálculos de dimensionamento de elevadores
    """
    
    @staticmethod
    def calcular_dimensionamento_completo(especificacoes: dict):
        """
        Calcula o dimensionamento completo baseado nas especificações
        
        Args:
            especificacoes (dict): Dicionário com todas as especificações do elevador
            
        Returns:
            tuple: (dimensionamento, explicacao_texto)
        """
        try:
            # Extrair dados das especificações
            altura = float(especificacoes.get("Altura da Cabine", 0))
            largura_poco = float(especificacoes.get("Largura do Poço", 0))
            comprimento_poco = float(especificacoes.get("Comprimento do Poço", 0))
            modelo_porta = especificacoes.get("Modelo Porta", "")
            folhas_porta = especificacoes.get("Folhas Porta", "")
            contrapeso = especificacoes.get("Contrapeso", "")
            modelo = especificacoes.get("Modelo do Elevador", "")
            capacidade_original = float(especificacoes.get("Capacidade", 0))
            capacidade_pessoas = especificacoes.get("Capacidade (pessoas)", 0)
            saida = especificacoes.get("Saída", "")
            
            # Calcular largura
            largura = DimensionamentoService._calcular_largura_cabine(
                largura_poco, contrapeso
            )
            
            # Calcular comprimento
            comprimento = DimensionamentoService._calcular_comprimento_cabine(
                comprimento_poco, modelo_porta, folhas_porta, saida, contrapeso
            )
            
            # Arredondar dimensões
            largura = round(largura, 2)
            comprimento = round(comprimento, 2)
            

            # Calcular capacidade e tração com base em número de pessoas, se disponível
            capacidade_cabine, tracao_cabine = DimensionamentoService._calcular_capacidade_tracao(
                capacidade_original=capacidade_original,
                modelo=modelo,
                capacidade_pessoas=capacidade_pessoas
            )

            # Calcular chapas
            chapas_info = ChapasService.calcular_chapas_cabine(altura, largura, comprimento)
            
            # Gerar explicação
            explicacao_texto = DimensionamentoService._gerar_explicacao(
                largura_poco, comprimento_poco, altura, largura, comprimento,
                modelo_porta, folhas_porta, contrapeso, saida, modelo,
                capacidade_original, capacidade_cabine, tracao_cabine, chapas_info
            )
            
            # Montar resultado
            dimensionamento = {
                "cab": {
                    "altura": altura,
                    "largura": largura,
                    "compr": comprimento,
                    "capacidade": capacidade_cabine,
                    "tracao": tracao_cabine,
                    "chp": {
                        "corpo": chapas_info.get("num_chapatot", 0) if isinstance(chapas_info, dict) else 0,
                        "piso": chapas_info.get("num_chapa_piso", 0) if isinstance(chapas_info, dict) else 0
                    },
                    "pnl": {
                        "lateral": chapas_info.get("num_paineis_lateral", 0) if isinstance(chapas_info, dict) else 0,
                        "fundo": chapas_info.get("num_paineis_fundo", 0) if isinstance(chapas_info, dict) else 0,
                        "teto": chapas_info.get("num_paineis_teto", 0) if isinstance(chapas_info, dict) else 0
                    }
                }
            }
            
            return dimensionamento, explicacao_texto
            
        except Exception as e:
            logger.error(f"Erro no cálculo de dimensionamento: {str(e)}")
            raise ValueError(f"Erro nos cálculos de dimensionamento: {str(e)}")
    
    @staticmethod
    def _calcular_largura_cabine(largura_poco, contrapeso):
        """Calcula a largura da cabine"""
        sub_largura = 0.42 if largura_poco <= 1.5 else 0.48
        largura = largura_poco - sub_largura
        
        if contrapeso == "Lateral":
            largura -= 0.23
            
        return largura
    
    @staticmethod
    def _calcular_comprimento_cabine(comprimento_poco, modelo_porta, folhas_porta, saida, contrapeso):
        """Calcula o comprimento da cabine"""
        comprimento = comprimento_poco - 0.10
        
        # Calcular ajuste da porta
        ajuste_porta = 0.0
        if modelo_porta == "Automática":
            if folhas_porta == "Central":
                ajuste_porta = 0.138
            elif folhas_porta == "2":
                ajuste_porta = 0.21
            elif folhas_porta == "3":
                ajuste_porta = 0.31
        elif modelo_porta == "Pantográfica":
            ajuste_porta = 0.13
        elif modelo_porta == "Pivotante":
            ajuste_porta = 0.04
        
        # Multiplicar por 2 se saída for oposta
        if saida == "Oposta":
            ajuste_porta *= 2
        
        comprimento -= ajuste_porta
        
        if contrapeso == "Traseiro":
            comprimento -= 0.23
            
        return comprimento
        
    @staticmethod
    def _calcular_capacidade_tracao(capacidade_original, modelo,capacidade_pessoas):
        """Calcula capacidade e tração da cabine"""
        if "Passageiro" in modelo:
            capacidade_cabine = capacidade_pessoas * 80  # 80 kg por pessoa

        else:
            capacidade_cabine = capacidade_original

        tracao_cabine = capacidade_cabine / 2 + 500
        
        return capacidade_cabine, tracao_cabine
        
    @staticmethod
    def _gerar_explicacao(largura_poco, comprimento_poco, altura, largura, comprimento,
                         modelo_porta, folhas_porta, contrapeso, saida, modelo,
                         capacidade_original, capacidade_cabine, tracao_cabine, chapas_info):
        """Gera explicação detalhada dos cálculos"""
        from core.utils.formatters import formato_seguro, formato_negrito
        
        explicacoes = []
        
        # Dimensões da cabine
        explicacoes.append(f"\n{formato_negrito('Dimensões Cabine:')}")
        
        sub_largura = 0.42 if largura_poco <= 1.5 else 0.48
        explicacoes.append(f"Largura: Poço = {formato_seguro(largura_poco)}m - ({formato_seguro(sub_largura)}m)"
                          f"{' -Contrapeso lateral (0,23m),' if contrapeso == 'Lateral' else ''} = {formato_seguro(largura)}m")
        
        ajuste_porta = 0.0
        if modelo_porta == "Automática":
            if folhas_porta == "Central":
                ajuste_porta = 0.138
            elif folhas_porta == "2":
                ajuste_porta = 0.21
            elif folhas_porta == "3":
                ajuste_porta = 0.31
        elif modelo_porta == "Pantográfica":
            ajuste_porta = 0.13
        elif modelo_porta == "Pivotante":
            ajuste_porta = 0.04
            
        if saida == "Oposta":
            ajuste_porta *= 2
        
        explicacoes.append(f"Comprimento: Poço = {formato_seguro(comprimento_poco)}m - (0,10m) - "
                          f"Ajuste de porta {modelo_porta} {f'({folhas_porta} folhas)' if folhas_porta else ''} "
                          f"{'(x2 pois saída é oposta)' if saida == 'Oposta' else ''} ({formato_seguro(ajuste_porta)}m)"
                          f"{' - Contrapeso traseiro (0,23m)' if contrapeso == 'Traseiro' else ''} = {formato_seguro(comprimento)}m")
        
        explicacoes.append(f"Altura: Informada pelo usuário = {formato_seguro(altura)}m")
        
        # Capacidade e tração
        explicacoes.append(f"\n{formato_negrito('Capacidade e Tração Cabine:')}")

        if "Passageiro" in modelo:
            # Extrair capacidade_pessoas das especificações
            capacidade_pessoas = capacidade_original/80  # Este é o número de pessoas no caso de elevadores de passageiros
            explicacoes.append(f"Capacidade: {int(capacidade_pessoas)} pessoas * 80 kg = {formato_seguro(capacidade_cabine)} kg")
        else:
            explicacoes.append(f"Capacidade: {formato_seguro(capacidade_original)} kg (valor informado)")
            
        
        
        explicacoes.append(f"Tração: (Capacidade Cabine / 2) + 500 = {formato_seguro(tracao_cabine)} kg")

        # Informações sobre painéis e chapas
        if isinstance(chapas_info, dict):
            explicacoes.append(f"\n{formato_negrito('Painéis Corpo Cabine:')}")
            explicacoes.append(f"Laterais: {chapas_info['num_paineis_lateral']} de "
                              f"{formato_seguro(chapas_info['largura_painel_lateral']*100)}cm "
                              f"(com dobras {formato_seguro((chapas_info['largura_painel_lateral']+0.085)*100)}cm), "
                              f"{formato_seguro(chapas_info['altura_painel_lateral'])}m altura")
            
            explicacoes.append(f"Fundo: {chapas_info['num_paineis_fundo']} de "
                              f"{formato_seguro(chapas_info['largura_painel_fundo']*100)}cm "
                              f"(com dobras {formato_seguro((chapas_info['largura_painel_fundo']+0.085)*100)}cm), "
                              f"{formato_seguro(chapas_info['altura_painel_fundo'])}m altura")
            
            explicacoes.append(f"Teto: {chapas_info['num_paineis_teto']} de "
                              f"{formato_seguro(chapas_info['largura_painel_teto']*100)}cm "
                              f"(com dobras {formato_seguro((chapas_info['largura_painel_teto']+0.085)*100)}cm), "
                              f"{formato_seguro(chapas_info['altura_painel_teto'])}m altura")
            
            explicacoes.append(f"\n{formato_negrito('Chapas Corpo Cabine:')}")
            explicacoes.append(f"Laterais e Teto: {chapas_info['num_chapalt']} chapas, "
                              f"sobra/chapa = {formato_seguro(chapas_info['sobra_chapalt']*100)} cm")
            explicacoes.append(f"Fundo: {chapas_info['num_chapaf']} chapas, "
                              f"sobra/chapa = {formato_seguro(chapas_info['sobra_chapaf']*100)} cm")
            explicacoes.append(f"Reserva: 2 chapas. Total: {chapas_info['num_chapatot']} chapas")
            
            explicacoes.append(f"\n{formato_negrito('Chapas Piso Cabine:')}")
            explicacoes.append(f"{chapas_info['num_chapa_piso']} chapa(s)")
        else:
            explicacoes.append(f"Erro no cálculo de chapas: {chapas_info}")
        
        return "\n".join(explicacoes)


class ChapasService:
    """
    Serviço para cálculos relacionados a chapas e painéis
    """
    
    @staticmethod
    def calcular_largura_painel(dimensao):
        """Calcula a largura ideal do painel, entre 25 e 33 cm, não excedendo 40 cm com as dobras."""
        for divisoes in range(10, 1, -1):
            largura_base = dimensao / divisoes
            if .25 <= largura_base <= .33 and largura_base + .085 <= .40:
                return largura_base, divisoes
        return None, None
    
    @staticmethod
    def calcular_chapas_cabine(altura, largura, comprimento):
        """Calcula o número de chapas e painéis necessários para a cabine do elevador."""
        try:
            # Dimensões da Chapa de Aço Bruta
            chapa_largura = 1.20
            chapa_comprimento = 3.00

            # Cálculo para as paredes laterais
            largura_painel_lateral, num_paineis_lateral = ChapasService.calcular_largura_painel(comprimento)
            if largura_painel_lateral is None:
                return "Erro: Não foi possível calcular uma largura de painel adequada para as laterais."
            
            # Cálculo para a parede do fundo
            largura_painel_fundo, num_paineis_fundo = ChapasService.calcular_largura_painel(largura)
            if largura_painel_fundo is None:
                return "Erro: Não foi possível calcular uma largura de painel adequada para o fundo."

            # Ajustes para o número total de painéis
            num_paineis_lateral *= 2  # Duas laterais
            num_paineis_teto = num_paineis_lateral // 2

            # Cálculo do número de Chapas de Aço Brutas (CAB) necessárias
            paineis_por_chapa_lt = math.floor(chapa_largura / (largura_painel_lateral + 0.085))
            paineis_por_chapa_f = math.floor(chapa_largura / (largura_painel_fundo + 0.085))

            num_chapalt = math.ceil((num_paineis_lateral + num_paineis_teto) / paineis_por_chapa_lt)
            num_chapaf = math.ceil(num_paineis_fundo / paineis_por_chapa_f)

            # Cálculo das chapas do piso
            area_piso = largura * comprimento
            area_chapa = chapa_largura * chapa_comprimento
            num_chapapiso = math.ceil(area_piso / area_chapa)

            # Cálculo da sobra da chapa do piso
            area_utilizada_piso = area_piso
            sobra_chapapiso = (num_chapapiso * area_chapa) - area_utilizada_piso

            num_chapamargem = 2
            num_chapatot = num_chapalt + num_chapaf + num_chapamargem

            # Cálculo das sobras
            sobra_chapalt = (0.40 - (largura_painel_lateral + 0.085)) * num_chapalt
            sobra_chapaf = (0.40 - (largura_painel_fundo + 0.085)) * num_chapaf

            return {
                "num_paineis_lateral": num_paineis_lateral,
                "largura_painel_lateral": largura_painel_lateral,
                "altura_painel_lateral": altura,
                "num_paineis_fundo": num_paineis_fundo,
                "largura_painel_fundo": largura_painel_fundo,
                "altura_painel_fundo": altura,
                "num_paineis_teto": num_paineis_teto,
                "largura_painel_teto": largura_painel_lateral,
                "altura_painel_teto": largura,
                "num_chapalt": num_chapalt,
                "sobra_chapalt": sobra_chapalt,
                "num_chapaf": num_chapaf,
                "sobra_chapaf": sobra_chapaf,
                "num_chapa_piso": num_chapapiso,
                "sobra_chapapiso": sobra_chapapiso,
                "num_chapatot": num_chapatot
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo de chapas: {str(e)}")
            return f"Erro no cálculo de chapas: {str(e)}"