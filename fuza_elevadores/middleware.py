# fuza_elevadores/middleware.py

import logging
import time
from django.db import models


class AppContextMiddleware:
    """
    Middleware para detectar e definir o contexto da aplicação baseado na URL
    Específico para o Sistema Elevadores Fuza
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Detectar o contexto da aplicação com base na URL
        path = request.path
        
        # Determinar o contexto baseado no caminho da URL
        if '/vendedor/' in path:
            request.session['app_context'] = 'vendedor'
            request.session['portal_name'] = 'Portal do Vendedor'
            request.session['portal_color'] = 'success'
        elif '/producao/' in path:
            request.session['app_context'] = 'producao'
            request.session['portal_name'] = 'Portal de Produção'
            request.session['portal_color'] = 'info'
        elif '/gestor/' in path:
            request.session['app_context'] = 'gestor'
            request.session['portal_name'] = 'Portal do Gestor'
            request.session['portal_color'] = 'primary'
        elif '/configuracao/' in path:
            request.session['app_context'] = 'configuracao'
            request.session['portal_name'] = 'Configurações'
            request.session['portal_color'] = 'warning'
        elif '/admin/' in path:
            request.session['app_context'] = 'admin'
            request.session['portal_name'] = 'Administração'
            request.session['portal_color'] = 'danger'
        else:
            # Não alterar o contexto se não estiver em uma URL específica
            pass
        
        response = self.get_response(request)
        return response


class SimulacaoContextMiddleware:
    """
    Middleware para gerenciar contexto de simulações em andamento
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Verificar se há simulação em andamento
            simulacao_id = request.session.get('simulacao_ativa')
            if simulacao_id:
                try:
                    from core.models import SimulacaoElevador
                    simulacao = SimulacaoElevador.objects.get(
                        id=simulacao_id,
                        criado_por=request.user,
                        status__in=['rascunho', 'simulado']
                    )
                    request.simulacao_ativa = simulacao
                except SimulacaoElevador.DoesNotExist:
                    # Limpar simulação inválida da sessão
                    del request.session['simulacao_ativa']
                    request.simulacao_ativa = None
            else:
                request.simulacao_ativa = None
        else:
            request.simulacao_ativa = None
        
        response = self.get_response(request)
        return response


class ComponenteDisponibilidadeMiddleware:
    """
    Middleware para verificar disponibilidade de componentes em tempo real
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Adicionar informações de disponibilidade se necessário
        if request.user.is_authenticated and hasattr(request.user, 'nivel') and request.user.nivel in ['vendedor', 'compras', 'producao', 'gestor', 'admin', 'financeiro', 'vistoria', 'engenharia', 'almoxarifado']:
            # Verificar se há produtos com estoque baixo
            try:
                from core.models import Produto
                produtos_baixo_estoque = Produto.objects.filter(
                    status='ATIVO',
                    controla_estoque=True,
                    estoque_atual__lte=models.F('estoque_minimo')
                ).count()
                
                request.produtos_baixo_estoque = produtos_baixo_estoque
            except Exception:
                request.produtos_baixo_estoque = 0
        else:
            request.produtos_baixo_estoque = 0
        
        response = self.get_response(request)
        return response


class FuzaLogMiddleware:
    """
    Middleware para logging específico do sistema Fuza
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Iniciar timing
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Calcular tempo de resposta
        duration = time.time() - start_time
        
        # Log para ações importantes
        if request.user.is_authenticated:
            # Log de ações do vendedor
            if '/vendedor/' in request.path and request.method == 'POST':
                logger = logging.getLogger('fuza.vendedor')
                logger.info(f"Ação vendedor: {request.user.username} - {request.path} - {duration:.2f}s")
            
            # Log de ações de produção
            elif '/producao/' in request.path and request.method == 'POST':
                logger = logging.getLogger('fuza.producao')
                logger.info(f"Ação produção: {request.user.username} - {request.path} - {duration:.2f}s")
            
            # Log de mudanças de configuração
            elif '/configuracao/' in request.path and request.method in ['POST', 'PUT', 'DELETE']:
                logger = logging.getLogger('fuza.configuracao')
                logger.info(f"Configuração alterada: {request.user.username} - {request.path}")
            
            # Log de ações do gestor
            elif '/gestor/' in request.path and request.method == 'POST':
                logger = logging.getLogger('fuza.gestor')
                logger.info(f"Ação gestor: {request.user.username} - {request.path} - {duration:.2f}s")
            
            # Log de simulações
            elif 'simulacao' in request.path.lower() and request.method == 'POST':
                logger = logging.getLogger('fuza.simulacoes')
                logger.info(f"Simulação: {request.user.username} - {request.path}")
        
        return response


class PermissaoPortalMiddleware:
    """
    Middleware para verificar permissões de acesso aos portais
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar permissões apenas para usuários autenticados
        if request.user.is_authenticated:
            path = request.path
            
            # Se é superuser, permitir tudo
            if request.user.is_superuser:
                response = self.get_response(request)
                return response
            
            # Se não tem atributo nivel, permitir acesso (compatibilidade)
            if not hasattr(request.user, 'nivel'):
                response = self.get_response(request)
                return response
            
            user_nivel = request.user.nivel
            
            # Definir permissões por portal
            portal_permissions = {
                '/gestor/': ['admin', 'gestor', 'financeiro'],
                '/vendedor/': ['admin', 'gestor', 'vendedor', 'engenharia', 'vistoria'],
                '/producao/': ['admin', 'gestor', 'producao', 'compras', 'engenharia', 'almoxarifado'],
                '/configuracao/': ['admin', 'gestor'],
            }
            
            # Verificar se o usuário tem permissão para acessar o portal
            for portal_path, allowed_levels in portal_permissions.items():
                if path.startswith(portal_path):
                    if user_nivel not in allowed_levels:
                        from django.http import HttpResponseForbidden
                        return HttpResponseForbidden(
                            f"Acesso negado. Seu nível ({user_nivel}) não tem permissão para acessar este portal."
                        )
                    break
        
        response = self.get_response(request)
        return response