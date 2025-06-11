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
    
    # Desabilitar relacionamentos explicitamente
    groups = None
    user_permissions = None
    
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
    """Perfil estendido do usuário"""
    
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
        return f"{self.usuario.username} - {self.get_nivel_display()}"
    
    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"