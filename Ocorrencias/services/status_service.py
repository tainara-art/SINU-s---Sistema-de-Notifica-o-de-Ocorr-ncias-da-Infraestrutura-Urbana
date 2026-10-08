from django.core.exceptions import ValidationError
from django.db import transaction

from Ocorrencias.models import (
    Ocorrencia,
    HistoricoStatus,
    RegistroProtocolo,
    StatusOcorrencia,
)

from .protocolo_service import ProtocoloService


class StatusOcorrenciaService:
    """
    Centraliza as mudanças de status das ocorrências.

    Responsabilidades:
    - Validar o novo status;
    - Atualizar a ocorrência;
    - Registrar o histórico;
    - Gerar uma movimentação de protocolo.
    """

    @staticmethod
    @transaction.atomic
    def atualizar(ocorrencia_id, novo_status, responsavel=None):

        # 1. Verifica se o status informado existe.
        if novo_status not in StatusOcorrencia.values:
            raise ValidationError("Status inválido.")

        # 2. Busca e bloqueia a ocorrência durante a operação.
        oc = Ocorrencia.objects.select_for_update().get(
            pk=ocorrencia_id
        )

        status_anterior = oc.status

        # 3. Evita criar movimentações desnecessárias.
        if status_anterior == novo_status:
            return oc, False

        # Ocorrências anteriores à implantação do protocolo
        # precisarão ser regularizadas separadamente.
        if not oc.protocolo:
            raise ValidationError(
                "Esta ocorrência ainda não possui protocolo."
            )

        descricao = (
            f"Status alterado de "
            f"{StatusOcorrencia(status_anterior).label} "
            f"para {StatusOcorrencia(novo_status).label}."
        )

        # 4. Atualiza o status da ocorrência.
        oc.status = novo_status
        oc.save(update_fields=["status", "date_update"])

        # 5. Registra a alteração no histórico existente.
        HistoricoStatus.objects.create(
            ocorrencia=oc,
            status_anterior=status_anterior,
            status_novo=novo_status,
            observacao=descricao,
            responsavel=responsavel,
        )

        # 6. Gera um novo protocolo para essa movimentação.
        ProtocoloService.registrar_movimentacao(
            ocorrencia=oc,
            tipo_acao=RegistroProtocolo.TipoAcao.STATUS,
            responsavel=responsavel,
            observacao=descricao,
        )

        return oc, True