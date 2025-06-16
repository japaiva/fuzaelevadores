# vendedor/views/dashboard.py

import logging
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from core.models import Proposta

logger = logging.getLogger(__name__)


@login_required
def home(request):
    """Página inicial - redireciona para dashboard"""
    return redirect('vendedor:dashboard')


@login_required
def dashboard(request):
    context = {}
    return render(request, 'vendedor/dashboard.html', context)