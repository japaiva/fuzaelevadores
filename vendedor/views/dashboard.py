# vendedor/views/dashboard.py

import logging
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.decorators import portal_vendedor

from core.models import Proposta

logger = logging.getLogger(__name__)


@portal_vendedor
def home(request):
    """Página inicial - redireciona para dashboard"""
    return redirect('vendedor:dashboard')


@portal_vendedor
def dashboard(request):
    context = {}
    return render(request, 'vendedor/dashboard.html', context)