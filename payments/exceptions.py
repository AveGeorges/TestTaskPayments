class PayoutException(Exception):
    """Base exception for payout operations"""
    pass


class PayoutValidationError(PayoutException):
    """Validation error for payout data"""
    pass


class PayoutNotFoundError(PayoutException):
    """Payout not found"""
    pass


class PayoutStatusTransitionError(PayoutException):
    """Invalid status transition"""
    pass


class PayoutAmountLimitError(PayoutException):
    """Payout amount limit exceeded"""
    pass


class PayoutProcessingError(PayoutException):
    """Payout processing error"""
    pass


class DuplicatePayoutError(PayoutException):
    """Duplicate payout error"""
    pass
