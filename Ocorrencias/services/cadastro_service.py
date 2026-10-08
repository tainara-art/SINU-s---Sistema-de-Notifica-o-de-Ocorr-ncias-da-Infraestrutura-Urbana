from django.db import transaction

from Ocorrencias.models import HistoricoStatus, RegistroProtocolo
from .protocolo_service import ProtocoloService


class CadastroOcorrenciaService:
    """
    Executa as ações obrigatórias após o cadastro:
    protocolo inicial, histórico e encaminhamento.
    """

    @staticmethod
    @transaction.atomic
    def registrar(ocorrencia):
        if not ocorrencia.pk:
            raise ValueError("A ocorrência ainda não foi salva.")

        # Evita cadastrar duas vezes o histórico inicial.
        if ocorrencia.protocolo:
            raise ValueError("A ocorrência já possui protocolo.")

        responsavel = (
            None if ocorrencia.anonima else ocorrencia.usuario
        )

        # 1. Gera o protocolo inicial.
        ProtocoloService.registrar_criacao(
            ocorrencia,
            responsavel=responsavel
        )

        # 2. Registra a abertura no histórico existente.
        HistoricoStatus.objects.create(
            ocorrencia=ocorrencia,
            status_anterior="",
            status_novo=ocorrencia.status,
            observacao="Ocorrência registrada.",
            responsavel=responsavel
        )

        # 3. Se houver secretaria responsável,
        # registra também o encaminhamento.
        if ocorrencia.secretaria_id:
            ProtocoloService.registrar_movimentacao(
                ocorrencia=ocorrencia,
                tipo_acao=RegistroProtocolo.TipoAcao.ENCAMINHAMENTO,
                responsavel=responsavel,
                observacao=(
                    f"Ocorrência encaminhada à secretaria "
                    f"{ocorrencia.secretaria.name}."
                )
            )

        return ocorrencia