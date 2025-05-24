# core/validators.py

from django.core.exceptions import ValidationError
from django.db import models
import re

def validar_cpf(cpf):
    """
    Valida CPF brasileiro
    """
    # Remove caracteres não numéricos
    cpf = re.sub(r'\D', '', str(cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        raise ValidationError('CPF deve conter exatamente 11 dígitos.')
    
    # Verifica se não é uma sequência de números iguais
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')
    
    # Validação do primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    
    resto = soma % 11
    if resto < 2:
        digito1 = 0
    else:
        digito1 = 11 - resto
    
    if int(cpf[9]) != digito1:
        raise ValidationError('CPF inválido.')
    
    # Validação do segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    
    resto = soma % 11
    if resto < 2:
        digito2 = 0
    else:
        digito2 = 11 - resto
    
    if int(cpf[10]) != digito2:
        raise ValidationError('CPF inválido.')
    
    return cpf

def validar_cnpj(cnpj):
    """
    Valida CNPJ brasileiro
    """
    # Remove caracteres não numéricos
    cnpj = re.sub(r'\D', '', str(cnpj))
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        raise ValidationError('CNPJ deve conter exatamente 14 dígitos.')
    
    # Verifica se não é uma sequência de números iguais
    if cnpj == cnpj[0] * 14:
        raise ValidationError('CNPJ inválido.')
    
    # Validação do primeiro dígito verificador
    sequencia = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = 0
    for i in range(12):
        soma += int(cnpj[i]) * sequencia[i]
    
    resto = soma % 11
    if resto < 2:
        digito1 = 0
    else:
        digito1 = 11 - resto
    
    if int(cnpj[12]) != digito1:
        raise ValidationError('CNPJ inválido.')
    
    # Validação do segundo dígito verificador
    sequencia = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = 0
    for i in range(13):
        soma += int(cnpj[i]) * sequencia[i]
    
    resto = soma % 11
    if resto < 2:
        digito2 = 0
    else:
        digito2 = 11 - resto
    
    if int(cnpj[13]) != digito2:
        raise ValidationError('CNPJ inválido.')
    
    return cnpj

def formatar_cpf(cpf):
    """
    Formata CPF para exibição: 000.000.000-00
    """
    cpf = re.sub(r'\D', '', str(cpf))
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf

def formatar_cnpj(cnpj):
    """
    Formata CNPJ para exibição: 00.000.000/0000-00
    """
    cnpj = re.sub(r'\D', '', str(cnpj))
    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return cnpj

def validar_cpf_cnpj_unico(value, instance=None, model_class=None):
    """
    Valida se CPF/CNPJ é único no banco de dados
    """
    if not value or not model_class:
        return
    
    # Remove caracteres não numéricos
    value_clean = re.sub(r'\D', '', str(value))
    
    # Busca no banco por CPF/CNPJ iguais
    queryset = model_class.objects.filter(
        models.Q(cpf_cnpj__icontains=value_clean) |
        models.Q(cpf_cnpj=value)
    )
    
    # Se está editando, exclui o próprio registro
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    
    if queryset.exists():
        raise ValidationError('Este CPF/CNPJ já está cadastrado no sistema.')