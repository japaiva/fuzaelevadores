# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import PerfilUsuario, Usuario
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404, render
from .forms import UsuarioForm

@login_required
def perfil(request):
    usuario = request.user
    
    # Obter ou criar perfil ao carregar a página
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=usuario)
    
    # Obter o contexto atual do usuário
    app_context = request.session.get('app_context', 'home')
    
    # Determinar para onde voltar com base no contexto
    if app_context == 'gestor':
        back_url = 'gestor:dashboard'
    elif app_context == 'vendedor':
        back_url = 'vendedor:dashboard'
    elif app_context == 'compras':
        back_url = 'compras:dashboard'
    else:
        back_url = 'home'
    
    if request.method == 'POST':
        # Atualizar informações básicas
        usuario.first_name = request.POST.get('first_name', '')
        usuario.last_name = request.POST.get('last_name', '')
        usuario.email = request.POST.get('email', '')
        
        # Atualizar telefone no usuário e no perfil
        telefone = request.POST.get('telefone', '')
        usuario.telefone = telefone
        perfil.telefone = telefone
        
        # Processar senha
        nova_senha = request.POST.get('nova_senha')
        if nova_senha:
            usuario.set_password(nova_senha)
        
        # Salvar alterações
        usuario.save()
        perfil.save()
        
        messages.success(request, 'Perfil atualizado com sucesso!')
        
        # Após salvar, redirecionar para a URL de retorno
        return redirect(back_url)
    
    return render(request, 'perfil.html', {'usuario': usuario, 'back_url': back_url})

def home_view(request):
    """
    View para a página inicial do site.
    Redireciona para o dashboard apropriado se o usuário estiver autenticado,
    caso contrário, mostra a página inicial genérica.
    """
    if request.user.is_authenticated:
        # Redireciona para o portal adequado com base no nível do usuário
        if request.user.nivel in ['admin', 'gestor']:
            return redirect('gestor:dashboard')
        elif request.user.nivel == 'vendedor':
            return redirect('vendedor:dashboard')
        elif request.user.nivel == 'compras':
            return redirect('compras:dashboard')
        else:
            # Nível de usuário não reconhecido, redireciona para a página inicial padrão
            return render(request, 'home.html')
    else:
        # Usuário não autenticado, mostra a página inicial padrão
        return render(request, 'home.html')
    
def logout_view(request):
    """
    View para realizar o logout do usuário.
    """
    # Obter o contexto antes de fazer logout
    app_context = request.session.get('app_context', 'home')
    
    # Realizar o logout
    logout(request)
    
    # Mensagem de sucesso
    messages.success(request, 'Você foi desconectado com sucesso.')
    
    # Redirecionar com base no contexto
    if app_context == 'gestor':
        return redirect('gestor:login')
    elif app_context == 'vendedor':
        return redirect('vendedor:login')
    elif app_context == 'compras':
        return redirect('compras:login')
    else:
        return redirect('home')

class GestorLoginView(LoginView):
    template_name = 'gestor/login.html'
    
    def form_valid(self, form):
        # Definir contexto da aplicação
        self.request.session['app_context'] = 'gestor'
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('gestor:dashboard')
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_name'] = 'Portal do Gestor - Sistema de Elevadores FUZA'
        return context