# Кастомные исключения для системы оплаты


class PaymentError(Exception):
    """Базовое исключение для ошибок платежей"""


class PaymentCreationError(PaymentError):
    """Ошибка при создании платежа"""


class PaymentCaptureError(PaymentError):
    """Ошибка подтверждения платежа"""


class WebhookValidationError(PaymentError):
    """Ошибка валидации вебхука"""


class PaymentStatusError(PaymentError):
    """Ошибка при получении статуса платежа"""


class PaymentCancelError(PaymentError):
    """Ошибка при получении статуса платежа"""
