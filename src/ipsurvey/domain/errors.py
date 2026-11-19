"""Exceções do domínio."""


class DomainError(Exception):
    """Base de todos os erros do domínio."""


class DataValidationError(DomainError):
    """Dado de entrada inválido. Não é repetido pelo orquestrador: vai para quarentena."""


class CRSMismatchError(DomainError):
    """Operação entre objetos em sistemas de referência diferentes."""


class InsufficientPointsError(DomainError):
    """Pontos insuficientes para o ajuste geométrico solicitado."""
