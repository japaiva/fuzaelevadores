# core/decorators.py
"""
Decorators para controle de acesso por nivel de usuario.

Uso:
    @nivel_required('gestor', 'admin')
    def minha_view(request):
        ...

    @portal_vendedor
    def view_vendedor(request):
        ...
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# Mapeamento de portais para niveis permitidos
PORTAL_NIVEIS = {
    'vendedor': ['vendedor', 'vistoria', 'gestor', 'admin'],
    'gestor': ['gestor', 'admin'],
    'producao': ['compras', 'engenharia', 'producao', 'almoxarifado', 'gestor', 'admin'],
}

# Mapeamento de modulos especificos
MODULO_NIVEIS = {
    # Portal Gestor - submodulos
    'cadastros': ['gestor', 'admin'],
    'estoque': ['almoxarifado', 'producao', 'gestor', 'admin'],
    'estoque_movimento': ['almoxarifado', 'gestor', 'admin'],
    'ordem_producao': ['producao', 'almoxarifado', 'gestor', 'admin'],
    'usuarios': ['gestor', 'admin'],
    'parametros': ['gestor', 'admin'],

    # Portal Producao - submodulos
    'compras': ['compras', 'gestor', 'admin'],
    'requisicao': ['compras', 'engenharia', 'producao', 'gestor', 'admin'],
    'estrutura': ['engenharia', 'producao', 'gestor', 'admin'],
    'produtos_mp': ['compras', 'engenharia', 'almoxarifado', 'gestor', 'admin'],
    'produtos_pi': ['engenharia', 'producao', 'gestor', 'admin'],
    'produtos_pa': ['engenharia', 'gestor', 'admin'],
}


def nivel_required(*niveis_permitidos):
    """
    Decorator que verifica se o usuario tem um dos niveis permitidos.

    Uso:
        @nivel_required('gestor', 'admin')
        def minha_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            # Admin e superuser sempre tem acesso
            if request.user.is_superuser or request.user.nivel == 'admin':
                return view_func(request, *args, **kwargs)

            # Verificar nivel do usuario
            if request.user.nivel in niveis_permitidos:
                return view_func(request, *args, **kwargs)

            messages.error(request, 'Voce nao tem permissao para acessar esta pagina.')
            return redirect('home')

        return wrapper
    return decorator


def portal_required(portal):
    """
    Decorator que verifica se o usuario pode acessar um portal.

    Uso:
        @portal_required('gestor')
        def minha_view(request):
            ...
    """
    niveis = PORTAL_NIVEIS.get(portal, [])
    return nivel_required(*niveis)


def modulo_required(modulo):
    """
    Decorator que verifica se o usuario pode acessar um modulo especifico.

    Uso:
        @modulo_required('estoque')
        def minha_view(request):
            ...
    """
    niveis = MODULO_NIVEIS.get(modulo, [])
    return nivel_required(*niveis)


# Decorators de atalho para portais
def portal_vendedor(view_func):
    """Acesso: vendedor, vistoria, gestor, admin"""
    return portal_required('vendedor')(view_func)


def portal_gestor(view_func):
    """Acesso: gestor, admin"""
    return portal_required('gestor')(view_func)


def portal_producao(view_func):
    """Acesso: compras, engenharia, producao, almoxarifado, gestor, admin"""
    return portal_required('producao')(view_func)


# Decorators de atalho para modulos
def modulo_cadastros(view_func):
    """Acesso: gestor, admin"""
    return modulo_required('cadastros')(view_func)


def modulo_estoque(view_func):
    """Acesso: almoxarifado, producao, gestor, admin"""
    return modulo_required('estoque')(view_func)


def modulo_estoque_movimento(view_func):
    """Acesso: almoxarifado, gestor, admin"""
    return modulo_required('estoque_movimento')(view_func)


def modulo_ordem_producao(view_func):
    """Acesso: producao, almoxarifado, gestor, admin"""
    return modulo_required('ordem_producao')(view_func)


def modulo_usuarios(view_func):
    """Acesso: gestor, admin"""
    return modulo_required('usuarios')(view_func)


def modulo_parametros(view_func):
    """Acesso: gestor, admin"""
    return modulo_required('parametros')(view_func)


def modulo_compras(view_func):
    """Acesso: compras, gestor, admin"""
    return modulo_required('compras')(view_func)


def modulo_requisicao(view_func):
    """Acesso: compras, engenharia, producao, gestor, admin"""
    return modulo_required('requisicao')(view_func)


def modulo_estrutura(view_func):
    """Acesso: engenharia, producao, gestor, admin"""
    return modulo_required('estrutura')(view_func)


def modulo_produtos_mp(view_func):
    """Acesso: compras, engenharia, almoxarifado, gestor, admin"""
    return modulo_required('produtos_mp')(view_func)


def modulo_produtos_pi(view_func):
    """Acesso: engenharia, producao, gestor, admin"""
    return modulo_required('produtos_pi')(view_func)


def modulo_produtos_pa(view_func):
    """Acesso: engenharia, gestor, admin"""
    return modulo_required('produtos_pa')(view_func)
