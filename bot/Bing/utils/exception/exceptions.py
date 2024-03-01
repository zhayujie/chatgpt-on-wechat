class NotAllowedToAccess(Exception):
    pass


class UnSupportLanguage(Exception):
    pass


class PromptBlocked(Exception):
    pass


class ImageCreateFailed(Exception):
    pass


class NoResultsFound(Exception):
    pass


class AuthCookieError(Exception):
    pass


class LimitExceeded(Exception):
    pass


class InappropriateContentType(Exception):
    pass


class ResponseError(Exception):
    pass


class PluginError(Exception):
    pass
