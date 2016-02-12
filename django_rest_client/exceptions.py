# -*- coding: utf-8 -*-


"""
be_core.exceptions
"""
import logging

logger = logging.getLogger('django_rest_client')


class BaseException(Exception):

    """
    A base class for exceptions in this module...
    """

    def __init__(self, cause=None, *args, **kwargs):
        #
        # Call the base constructor.
        #
        super(Exception, self).__init__(*args, **kwargs)

        #
        # Add information about a possible inner exception.
        #
        logger.error(cause)
        self.cause = cause


class ServiceUnavailableError(BaseException):

    """
    The exception that is thrown whenever a given endpoint cannot be reached.
    """
    pass


class MalformedResponseError(BaseException):

    """
    The exception that is thrown whenever we receive a malformed response from the REST API.
    """
    pass


class UnauthorizedRequestError(BaseException):

    """
    Exception thrown whenever we get an uncaught 401 Unauthorized response
    from the REST API, potentially meaning that the user's API token has expired
    and reauthentication is needed.
    """
    pass


class UnexpectedResponseError(BaseException):

    """
    The exception that is thrown whenever we get an unexpected response from the REST API.
    """
    pass


class UnknownObjectTypeError(BaseException):

    """
    The exception that is thrown whenever we are asked to create an object of an unknown type.
    """
    pass

