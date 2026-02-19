class HANERMABaseException(Exception):
    """Base exception for all framework errors."""
    pass

class HallucinationDetectedError(HANERMABaseException):
    """Raised by Deep 2 when a claim mathematically contradicts HCMS memory."""
    pass

class InfiniteLoopBoundError(HANERMABaseException):
    """Raised when an agent attempts to hand off tasks in a recursive circle."""
    pass
