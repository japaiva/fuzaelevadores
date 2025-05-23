# fuza_elevadores/urls.py
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
    
    # Portais específicos
    path('gestor/', include('gestor.urls')),
    
    # ⚠️ COMENTAR ESTAS LINHAS TEMPORARIAMENTE ⚠️
    # path('producao/', include('producao.urls')),  # ← URLs ainda não criadas
    # path('vendedor/', include('vendedor.urls')),  # ← App ainda não criado
    
    # APIs e outros apps
    # path('api/', include('api.urls', namespace='api')),  # ← Se não tiver ainda
]

# Adicionar URLs para servir mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Configuração do Admin
admin.site.site_header = 'Sistema Elevadores FUZA'
admin.site.site_title = 'FUZA Admin'
admin.site.index_title = 'Administração do Sistema'