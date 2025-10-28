# core/utils/permissions.py

"""
Decorators e Mixins para controle de permissões
Sistema de Elevadores FUZA
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin


# ========================================
# DECORATORS PARA VIEWS BASEADAS EM FUNÇÃO
# ========================================

def require_nivel(*niveis_permitidos):
    """
    Decorator para exigir nível específico de usuário

    Uso:
        @require_nivel('admin', 'gestor')
        def minha_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'nivel'):
                raise PermissionDenied("Usuário sem nível definido")

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if request.user.nivel not in niveis_permitidos:
                messages.error(
                    request,
                    f'Acesso negado. Seu nível ({request.user.nivel}) não tem permissão para acessar esta página.'
                )
                raise PermissionDenied(
                    f"Nível de acesso insuficiente. Requer: {', '.join(niveis_permitidos)}"
                )

            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_permission(*permissions):
    """
    Decorator para exigir permissões específicas

    Uso:
        @require_permission('core.aprovar_desconto_10')
        def aprovar_desconto(request, proposta_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Verificar se tem TODAS as permissões
            for perm in permissions:
                if not request.user.has_perm(perm):
                    messages.error(
                        request,
                        f'Você não tem permissão para realizar esta ação.'
                    )
                    raise PermissionDenied(f"Permissão necessária: {perm}")

            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_any_permission(*permissions):
    """
    Decorator para exigir pelo menos UMA das permissões listadas

    Uso:
        @require_any_permission('core.aprovar_desconto_5', 'core.aprovar_desconto_10')
        def aprovar_desconto(request, proposta_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Verificar se tem PELO MENOS UMA permissão
            tem_permissao = any(request.user.has_perm(perm) for perm in permissions)

            if not tem_permissao:
                messages.error(
                    request,
                    'Você não tem permissão para realizar esta ação.'
                )
                raise PermissionDenied(
                    f"Requer pelo menos uma permissão: {', '.join(permissions)}"
                )

            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_nivel_and_permission(niveis, permissions):
    """
    Decorator combinado: exige nível E permissões

    Uso:
        @require_nivel_and_permission(['admin', 'gestor'], ['core.aprovar_proposta'])
        def aprovar_proposta(request, proposta_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Verificar nível
            if not hasattr(request.user, 'nivel') or request.user.nivel not in niveis:
                messages.error(
                    request,
                    f'Acesso negado. Nível insuficiente.'
                )
                raise PermissionDenied(f"Nível requerido: {', '.join(niveis)}")

            # Verificar permissões
            for perm in permissions:
                if not request.user.has_perm(perm):
                    messages.error(
                        request,
                        'Você não tem permissão para realizar esta ação.'
                    )
                    raise PermissionDenied(f"Permissão necessária: {perm}")

            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


# ========================================
# MIXINS PARA CLASS-BASED VIEWS
# ========================================

class NivelRequiredMixin(AccessMixin):
    """
    Mixin para exigir nível específico em Class-Based Views

    Uso:
        class MinhaView(NivelRequiredMixin, View):
            niveis_permitidos = ['admin', 'gestor']
    """
    niveis_permitidos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'nivel'):
            messages.error(request, 'Usuário sem nível definido.')
            return self.handle_no_permission()

        if request.user.nivel not in self.niveis_permitidos:
            messages.error(
                request,
                f'Acesso negado. Seu nível ({request.user.nivel}) não tem permissão para acessar esta página.'
            )
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class PermissionRequiredMixin(AccessMixin):
    """
    Mixin aprimorado para exigir permissões em Class-Based Views
    Substitui o padrão do Django com mensagens mais amigáveis

    Uso:
        class MinhaView(PermissionRequiredMixin, View):
            permission_required = 'core.aprovar_proposta'
            # ou
            permission_required = ['core.aprovar_proposta', 'core.editar_proposta']
    """
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        if not self.has_permission():
            messages.error(
                request,
                'Você não tem permissão para acessar esta página.'
            )
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        """Verifica se o usuário tem as permissões necessárias"""
        perms = self.permission_required
        if isinstance(perms, str):
            perms = [perms]

        return all(self.request.user.has_perm(perm) for perm in perms)


class AnyPermissionRequiredMixin(AccessMixin):
    """
    Mixin para exigir pelo menos UMA permissão

    Uso:
        class MinhaView(AnyPermissionRequiredMixin, View):
            permissions_required = ['core.aprovar_desconto_5', 'core.aprovar_desconto_10']
    """
    permissions_required = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        tem_permissao = any(
            request.user.has_perm(perm) for perm in self.permissions_required
        )

        if not tem_permissao:
            messages.error(
                request,
                'Você não tem permissão para acessar esta página.'
            )
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class NivelAndPermissionMixin(AccessMixin):
    """
    Mixin combinado: exige nível E permissões

    Uso:
        class MinhaView(NivelAndPermissionMixin, View):
            niveis_permitidos = ['admin', 'gestor']
            permission_required = 'core.aprovar_proposta'
    """
    niveis_permitidos = []
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Verificar nível
        if not hasattr(request.user, 'nivel') or request.user.nivel not in self.niveis_permitidos:
            messages.error(
                request,
                f'Acesso negado. Nível insuficiente.'
            )
            return self.handle_no_permission()

        # Verificar permissões
        perms = self.permission_required
        if perms:
            if isinstance(perms, str):
                perms = [perms]

            if not all(request.user.has_perm(perm) for perm in perms):
                messages.error(
                    request,
                    'Você não tem permissão para acessar esta página.'
                )
                return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


# ========================================
# HELPER FUNCTIONS
# ========================================

def get_max_desconto_percentual(user):
    """
    Retorna o percentual máximo de desconto que o usuário pode aprovar

    Returns:
        Decimal: percentual máximo (5.0, 10.0, 15.0, etc.) ou 0 se não tiver permissão
    """
    if user.is_superuser or user.has_perm('core.aprovar_desconto_ilimitado'):
        return 100.0

    if user.has_perm('core.aprovar_desconto_20'):
        return 20.0

    if user.has_perm('core.aprovar_desconto_15'):
        return 15.0

    if user.has_perm('core.aprovar_desconto_10'):
        return 10.0

    if user.has_perm('core.aprovar_desconto_5'):
        return 5.0

    return 0.0


def get_max_valor_orcamento(user):
    """
    Retorna o valor máximo de orçamento que o usuário pode aprovar

    Returns:
        Decimal: valor máximo ou None se ilimitado
    """
    if user.is_superuser or user.has_perm('core.aprovar_orcamento_ilimitado'):
        return None  # Ilimitado

    if user.has_perm('core.aprovar_orcamento_ate_50000'):
        return 50000.0

    if user.has_perm('core.aprovar_orcamento_ate_10000'):
        return 10000.0

    if user.has_perm('core.aprovar_orcamento_ate_5000'):
        return 5000.0

    return 0.0


def pode_aprovar_desconto(user, percentual):
    """
    Verifica se o usuário pode aprovar um desconto de X%

    Args:
        user: usuário Django
        percentual: percentual de desconto (Decimal ou float)

    Returns:
        bool: True se pode aprovar
    """
    max_desconto = get_max_desconto_percentual(user)
    return percentual <= max_desconto


def pode_aprovar_orcamento(user, valor):
    """
    Verifica se o usuário pode aprovar um orçamento de valor X

    Args:
        user: usuário Django
        valor: valor do orçamento (Decimal)

    Returns:
        bool: True se pode aprovar
    """
    max_valor = get_max_valor_orcamento(user)
    if max_valor is None:  # Ilimitado
        return True
    return valor <= max_valor
