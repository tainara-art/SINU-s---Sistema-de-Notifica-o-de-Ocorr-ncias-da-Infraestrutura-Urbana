from django.db import transaction
from django.utils import timezone

from Ocorrencias.models import (
    Ocorrencia,
    RegistroProtocolo,
    SequenciaProtocolo,
)


class ProtocoloService:
    """
    Responsável pela geração e pelo registro dos protocolos.

    Formato:
        AAAAMM-SIGLA-SEQUENCIA

    Exemplo:
        202610-OBR-001
    """

    SIGLA_PILOTO = "OBR"

    @classmethod
    def _gerar_codigo(cls):
        """
        Gera o próximo número da competência.

        Deve ser chamado dentro de uma transação.
        """

        competencia = timezone.localdate().strftime("%Y%m")
        sigla = cls.SIGLA_PILOTO

        # Bloqueia a sequência durante a atualização
        # em bancos que suportam SELECT FOR UPDATE.
        sequencia, _ = (
            SequenciaProtocolo.objects
            .select_for_update()
            .get_or_create(
                competencia=competencia,
                sigla=sigla,
                defaults={"ultimo_numero": 0},
            )
        )

        sequencia.ultimo_numero += 1
        sequencia.save(update_fields=["ultimo_numero"])

        # :03d garante ao menos três dígitos:
        # 001, 002, ..., 999, 1000...
        return (
            f"{competencia}-"
            f"{sigla}-"
            f"{sequencia.ultimo_numero:03d}"
        )

    @classmethod
    @transaction.atomic
    def registrar_criacao(cls, ocorrencia, responsavel=None):
        """
        Cria o protocolo inicial de uma ocorrência.

        A ocorrência precisa já ter sido salva no banco.
        """

        if not ocorrencia.pk:
            raise ValueError(
                "A ocorrência deve ser salva antes de receber um protocolo."
            )

        # Bloqueia a ocorrência para impedir duas gerações
        # simultâneas no mesmo registro.
        ocorrencia_db = (
            Ocorrencia.objects
            .select_for_update()
            .get(pk=ocorrencia.pk)
        )

        if ocorrencia_db.protocolo:
            raise ValueError(
                "Esta ocorrência já possui um protocolo."
            )

        codigo = cls._gerar_codigo()

        # Primeiro evento da timeline.
        registro = RegistroProtocolo.objects.create(
            ocorrencia=ocorrencia_db,
            codigo=codigo,
            tipo_acao=RegistroProtocolo.TipoAcao.CRIACAO,
            visibilidade=RegistroProtocolo.Visibilidade.PUBLICA,
            responsavel=responsavel,
            observacao="Ocorrência registrada no sistema.",
        )

        # O protocolo inicial permanece vinculado à ocorrência.
        Ocorrencia.objects.filter(
            pk=ocorrencia_db.pk
        ).update(protocolo=codigo)

        # Atualiza também o objeto Python recebido.
        ocorrencia.protocolo = codigo

        return registro

    @classmethod
    @transaction.atomic
    def registrar_movimentacao(
        cls,
        ocorrencia,
        tipo_acao,
        responsavel=None,
        observacao="",
        visibilidade=RegistroProtocolo.Visibilidade.PUBLICA,
    ):
        """
        Registra uma nova movimentação sem alterar
        o protocolo inicial da ocorrência.
        """

        ocorrencia_db = (
            Ocorrencia.objects
            .select_for_update()
            .get(pk=ocorrencia.pk)
        )

        if not ocorrencia_db.protocolo:
            raise ValueError(
                "A ocorrência ainda não possui protocolo inicial."
            )

        if tipo_acao not in (
            RegistroProtocolo.TipoAcao.ENCAMINHAMENTO,
            RegistroProtocolo.TipoAcao.STATUS,
            RegistroProtocolo.TipoAcao.OBSERVACAO,
        ):
            raise ValueError("Tipo de movimentação inválido.")

        if visibilidade not in (
            RegistroProtocolo.Visibilidade.PUBLICA,
            RegistroProtocolo.Visibilidade.INTERNA,
        ):
            raise ValueError("Visibilidade inválida.")

        codigo = cls._gerar_codigo()

        return RegistroProtocolo.objects.create(
            ocorrencia=ocorrencia_db,
            codigo=codigo,
            tipo_acao=tipo_acao,
            visibilidade=visibilidade,
            responsavel=responsavel,
            observacao=observacao,
        )