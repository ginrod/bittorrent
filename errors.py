
class RequestError(Exception):
    """Raised when the request format is not valid"""
    pass

class UrlError(RequestError):
    """Raised when the url provided is not valid"""
    pass
