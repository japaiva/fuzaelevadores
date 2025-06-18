# core/services/pricing.py

import logging
from typing import Dict, Any
from decimal import Decimal # Import Decimal

logger = logging.getLogger(__name__)


class PricingService:
    """
    Serviço responsável por cálculos de formação de preço
    """
    
    # Parâmetros padrão (depois podem vir do banco de dados)
    DEFAULT_PARAMS = {
        'comissao': 3.0,
        'margem': 30.0,
        'fat.Elevadores': 10.0,
        'fat.Fuza': 8.0,
        'fat.Manutenção': 5.0,
        'desc.alcada1': 5.0
    }
    
    @classmethod
    def calcular_formacao_preco(cls, custo_total: Decimal, tipo_faturamento: str = "Elevadores") -> Dict[str, Any]: # Changed custo_total type hint
        """
        Calcula a formação de preço completa
        
        Args:
            custo_total (Decimal): Custo total de produção
            tipo_faturamento (str): Tipo de faturamento (Elevadores, Fuza, Manutenção)
            
        Returns:
            Dict: Dicionário com todos os componentes da formação de preço
        """
        try:
            # Buscar parâmetros (por enquanto usa defaults, depois pode integrar com BD)
            parametros = cls._get_parametros()
            
            # Mapeamento para chaves
            mapeamento_chaves = {
                'Elevadores': 'fat.Elevadores',
                'Fuza': 'fat.Fuza',
                'Manutenção': 'fat.Manutenção',
            }
            
            # Percentuais dos parâmetros
            percentual_comissao = parametros.get('comissao', 3.0)
            percentual_margem = parametros.get('margem', 30.0)
            
            # Busca a chave exata no mapeamento
            chave_imposto = mapeamento_chaves.get(tipo_faturamento, 'fat.Elevadores')
            percentual_impostos = parametros.get(chave_imposto, 10.0)
            
            # Alçada de desconto
            alcada_desconto = parametros.get('desc.alcada1', 5.0)
            
            # Criar instância de FormacaoPreco
            formacao = FormacaoPreco(
                custo_producao=custo_total,
                percentual_margem=percentual_margem,
                percentual_comissao=percentual_comissao,
                percentual_impostos=percentual_impostos
            )
            
            # Retornar o modelo formatado
            resultado = formacao.get_display_model()
            resultado['alcada_desconto'] = alcada_desconto
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro no cálculo de formação de preço: {str(e)}")
            raise ValueError(f"Erro nos cálculos de preço: {str(e)}")
    
    @classmethod
    def recalcular_com_desconto(cls, formacao_preco: Dict[str, Any], preco_final_sem_impostos: Decimal) -> Dict[str, Any]: # Changed preco_final_sem_impostos type hint
        """
        Recalcula a formação de preço baseado em um preço final ajustado
        
        Args:
            formacao_preco (Dict): Formação de preço original
            preco_final_sem_impostos (Decimal): Novo preço final sem impostos
            
        Returns:
            Dict: Formação de preço atualizada
        """
        try:
            # Criar nova instância com valores atuais
            formacao = FormacaoPreco(
                custo_producao=Decimal(str(formacao_preco['custo_producao'])), # Convert to Decimal
                percentual_margem=formacao_preco['percentual_margem'],
                percentual_comissao=formacao_preco['percentual_comissao'],
                percentual_impostos=formacao_preco['percentual_impostos']
            )
            
            # Definir novo preço sem impostos
            formacao.definir_preco_sem_impostos(preco_final_sem_impostos)
            
            # Obter modelo atualizado
            nova_formacao = formacao.get_display_model()
            
            # Incluir alçada de desconto se existir
            if 'alcada_desconto' in formacao_preco:
                nova_formacao['alcada_desconto'] = formacao_preco['alcada_desconto']
            
            return nova_formacao
            
        except Exception as e:
            logger.error(f"Erro no recálculo com desconto: {str(e)}")
            raise ValueError(f"Erro no recálculo de preço: {str(e)}")
    
    @classmethod
    def _get_parametros(cls) -> Dict[str, float]:
        """
        Busca parâmetros de precificação
        Futuramente pode buscar do banco de dados
        """
        try:
            # TODO: Integrar com modelo Parametro do banco
            # from core.models import Parametro
            # return {param.parametro: param.valor for param in Parametro.objects.all()}
            
            # Por enquanto retorna defaults
            return cls.DEFAULT_PARAMS.copy()
            
        except Exception as e:
            logger.warning(f"Erro ao buscar parâmetros, usando defaults: {str(e)}")
            return cls.DEFAULT_PARAMS.copy()


class FormacaoPreco:
    """
    Classe para cálculos detalhados de formação de preço
    """
    
    def __init__(self, custo_producao: Decimal, percentual_margem: float = 30.0, # Changed type hint
                 percentual_comissao: float = 3.0, percentual_impostos: float = 10.0, 
                 valor_desconto: float = 0.0):
        self.custo_producao = custo_producao # Keep as Decimal
        self.percentual_margem = Decimal(str(percentual_margem)) # Convert to Decimal
        self.percentual_comissao = Decimal(str(percentual_comissao)) # Convert to Decimal
        self.percentual_impostos = Decimal(str(percentual_impostos)) # Convert to Decimal
        self.valor_desconto = Decimal(str(valor_desconto)) # Convert to Decimal
        self.preco_sem_impostos_solicitado = None

    @property
    def valor_margem(self) -> Decimal: # Changed return type
        return self.custo_producao * (self.percentual_margem / 100)

    @property
    def preco_com_margem(self) -> Decimal: # Changed return type
        return self.custo_producao + self.valor_margem

    @property
    def base_calculo_comissao(self) -> Decimal: # Changed return type
        """Base para cálculo da comissão: preço com margem menos desconto"""
        if self.preco_sem_impostos_solicitado:
            # Se tiver preço solicitado, a base de cálculo deve ser recalculada
            return self.preco_sem_impostos_solicitado / (Decimal('1') + self.percentual_comissao / 100) # Use Decimal('1')
        return self.preco_com_margem - self.valor_desconto

    @property
    def valor_comissao(self) -> Decimal: # Changed return type
        return self.base_calculo_comissao * (self.percentual_comissao / 100)

    @property
    def preco_sem_impostos(self) -> Decimal: # Changed return type
        """Preço sem impostos: base de cálculo + comissão"""
        if self.preco_sem_impostos_solicitado:
            return self.preco_sem_impostos_solicitado
        return self.base_calculo_comissao + self.valor_comissao

    @property
    def valor_impostos(self) -> Decimal: # Changed return type
        return self.preco_sem_impostos * (self.percentual_impostos / 100)

    @property
    def preco_com_impostos(self) -> Decimal: # Changed return type
        return self.preco_sem_impostos + self.valor_impostos

    @property
    def percentual_desconto_real(self) -> Decimal: # Changed return type
        """Calcula o percentual real de desconto"""
        if self.preco_sem_impostos_solicitado:
            # Qual seria o preço sem impostos sem desconto
            preco_sem_desconto = self.custo_producao + self.valor_margem + self.valor_comissao
            
            # Calculamos o desconto real
            desconto_real = preco_sem_desconto - self.preco_sem_impostos_solicitado
            
            # Retorna como percentual
            if preco_sem_desconto == Decimal('0'): # Use Decimal('0')
                return Decimal('0.0')
            return (desconto_real / preco_sem_desconto) * 100
        else:
            # Se não houver preço solicitado, usamos o desconto original
            preco_sem_desconto = self.custo_producao + self.valor_margem
            if preco_sem_desconto == Decimal('0'): # Use Decimal('0')
                return Decimal('0.0')
            return (self.valor_desconto / preco_sem_desconto) * 100

    def definir_preco_sem_impostos(self, preco: Decimal): # Changed type hint
        """Define um novo preço sem impostos solicitado"""
        self.preco_sem_impostos_solicitado = preco # Keep as Decimal

    def definir_desconto(self, valor_desconto: Decimal): # Changed type hint
        """Define um valor de desconto"""
        self.valor_desconto = valor_desconto # Keep as Decimal
        # Limpa o preço solicitado, pois vamos calcular com base no desconto
        self.preco_sem_impostos_solicitado = None

    def get_display_model(self) -> Dict[str, Any]:
        """Retorna um dicionário com os valores formatados para exibição"""
        return {
            'custo_producao': float(self.custo_producao),
            'percentual_margem': float(self.percentual_margem),
            'valor_margem': float(self.valor_margem),
            'percentual_desconto': float(self.percentual_desconto_real),
            'valor_desconto': float(self.valor_desconto if self.preco_sem_impostos_solicitado is None else 
                               (self.custo_producao + self.valor_margem + self.valor_comissao - self.preco_sem_impostos_solicitado)), # Fixed conditional to reflect None check
            'base_calculo_comissao': float(self.base_calculo_comissao),
            'percentual_comissao': float(self.percentual_comissao),
            'valor_comissao': float(self.valor_comissao),
            'preco_sem_impostos': float(self.preco_sem_impostos),
            'percentual_impostos': float(self.percentual_impostos),
            'valor_impostos': float(self.valor_impostos),
            'preco_com_impostos': float(self.preco_com_impostos)
        }