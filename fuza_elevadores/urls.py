# fuza_elevadores/urls.py - ESTRUTURA FINAL
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core.views import home_view, perfil, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Views de autenticação compartilhadas
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('perfil/', perfil, name='perfil'),
    path('logout/', logout_view, name='logout'),
    
    # Página inicial do site
    path('', home_view, name='home'),
    
    # 🏭 PORTAIS FINAIS (3 portais)
    path('gestor/', include('gestor.urls')),      # 👔 Gestão executiva
    path('vendedor/', include('vendedor.urls')),  # 💼 Vendas e simulações  
    path('producao/', include('producao.urls')),  # 🏭 Produção + Compras
    
    # APIs e configurações - COMENTADO TEMPORARIAMENTE
    # path('configuracao/', include('configuracao.urls')),  # ⚙️ Configurações
    # path('api/', include('api.urls', namespace='api')),
]

# Servir mídia durante desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Configuração do Admin
admin.site.site_header = 'Sistema Elevadores FUZA'
admin.site.site_title = 'FUZA Admin'
admin.site.index_title = 'Administração do Sistema'