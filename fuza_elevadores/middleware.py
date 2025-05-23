# fuza_elevadores/middleware.py

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
        elif '/compras/' in path:
            request.session['app_context'] = 'compras'
            request.session['portal_name'] = 'Portal de Compras'
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
                    from vendedor.models import Simulacao
                    simulacao = Simulacao.objects.get(
                        id=simulacao_id,
                        vendedor=request.user,
                        status__in=['rascunho', 'em_andamento']
                    )
                    request.simulacao_ativa = simulacao
                except Simulacao.DoesNotExist:
                    # Limpar simulação inválida da sessão
                    del request.session['simulacao_ativa']
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
        if request.user.is_authenticated and request.user.nivel in ['vendedor', 'compras', 'gestor', 'admin']:
            # Verificar se há componentes com estoque baixo
            try:
                from configuracao.models import Componente
                componentes_baixo_estoque = Componente.objects.filter(
                    ativo=True,
                    estoque_atual__lte=models.F('estoque_minimo')
                ).count()
                
                if componentes_baixo_estoque > 0:
                    request.componentes_baixo_estoque = componentes_baixo_estoque
                else:
                    request.componentes_baixo_estoque = 0
            except:
                request.componentes_baixo_estoque = 0
        
        response = self.get_response(request)
        return response


class FuzaLogMiddleware:
    """
    Middleware para logging específico do sistema Fuza
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import logging
        import time
        
        # Iniciar timing
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Calcular tempo de resposta
        duration = time.time() - start_time
        
        # Log para ações importantes
        if request.user.is_authenticated:
            logger = logging.getLogger('fuza.simulacoes')
            
            # Log de simulações
            if '/vendedor/' in request.path and request.method == 'POST':
                logger.info(f"Ação vendedor: {request.user.username} - {request.path} - {duration:.2f}s")
            
            # Log de mudanças de configuração
            if '/configuracao/' in request.path and request.method in ['POST', 'PUT', 'DELETE']:
                logger = logging.getLogger('fuza.vendas')
                logger.info(f"Configuração alterada: {request.user.username} - {request.path}")
        
        return response