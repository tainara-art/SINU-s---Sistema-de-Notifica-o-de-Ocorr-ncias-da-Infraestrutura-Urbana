# core/choices.py
from django.db import models

class CategoriaOcorrencia(models.TextChoices):
    SANEAMENTO_BASICO         = 'SB', 'Saneamento Básico'
    PAVIMENTACAO_E_VIAS       = 'PV', 'Pavimentação e Vias'
    ILUMINACAO_PUBLICA        = 'IP', 'Iluminação Pública'
    LIMPEZA_URBANA            = 'LU', 'Limpeza Urbana'
    ANIMAIS_EM_SITUACAO_RISCO = 'AS', 'Animais em Risco'
    ARBORIZACAO_E_PRACAS      = 'AP', 'Arborização e Praças'
    SINALIZACAO_DE_TRANSITO   = 'ST', 'Sinalização de Trânsito'
    OBRAS_E_SERVICOS          = 'OS', 'Obras e Serviços'

