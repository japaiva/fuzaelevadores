# core/models/usuarios.py

"""
Models relacionados a usuários e perfis
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from .base import NIVEL_USUARIO_CHOICES


class Usuario(AbstractUser):
    """Modelo customizado de usuário"""

    nivel = models.CharField(max_length=20, choices=NIVEL_USUARIO_CHOICES)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    codigo_loja = models.CharField(
        max_length=3, 
        blank=True, 
        null=True, 
        help_text="Código de 3 dígitos da loja"
    )
    codigo_vendedor = models.CharField(
        max_length=3, 
        blank=True, 
        null=True, 
        help_text="Código de 3 dígitos do vendedor"
    )
    
    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'


class PerfilUsuario(models.Model):
    """
    Perfil estendido do usuário

    ⚠️ DEPRECADO - Este modelo será removido em breve ⚠️

    Motivo: Duplica dados do modelo Usuario (nivel, telefone) sem necessidade.
    Todos os dados devem estar diretamente no modelo Usuario.

    Ação recomendada:
    - NÃO use este modelo em código novo
    - Use request.user.nivel e request.user.telefone diretamente
    - Execute: python manage.py remover_perfil_usuario (quando disponível)
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    telefone = models.CharField(max_length=20, blank=True, null=True)
    nivel = models.CharField(
        max_length=20,
        choices=NIVEL_USUARIO_CHOICES,
        default='vendedor'
    )

    def __str__(self):
        return f"{self.usuario.username} - {self.get_nivel_display()} [DEPRECADO]"

    class Meta:
        verbose_name = "Perfil de Usuário (DEPRECADO)"
        verbose_name_plural = "Perfis de Usuários (DEPRECADO)"