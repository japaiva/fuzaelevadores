# core/services/config_repo_db.py - CORRIGIDO
import yaml
from functools import lru_cache
from typing import Dict, Any
from core.models.regras_yaml import RegraYAML

class ConfigRepoDB:
    @lru_cache(maxsize=16)
    def load(self, nome: str) -> Dict[str, Any]:
        """
        ✅ CORRIGIDO: Campo é 'ativa' não 'ativo'
        """
        obj = (RegraYAML.objects
               .filter(tipo=nome, ativa=True)  # ✅ 'ativa' não 'ativo'
               .order_by("-atualizado_em")
               .first())
        if not obj:
            return {}
        return yaml.safe_load(obj.conteudo_yaml) or {}

    def clear_cache(self):
        try:
            self.load.cache_clear()  # type: ignore[attr-defined]
        except Exception:
            pass