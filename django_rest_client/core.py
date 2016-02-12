# -*- coding: utf-8 -*-


import json
import logging

from django.conf import settings
from requests.exceptions import ConnectionError
from requests.sessions import Session
from uritemplate.template import URITemplate

from .exceptions import (MalformedResponseError, ServiceUnavailableError,
    UnexpectedResponseError, UnauthorizedRequestError)
from .models import ListPage

logger = logging.getLogger('django_rest_client')


class RestClientBase(object):
    """
    Base class for REST clients.
    """
    def __init__(self, user=None):
        #
        # Create a new 'requests' session.
        #
        self._session = Session()
        self._user = user

    def delete(self, *args, **kwargs):
        """
        Attempts to dispatch a 'DELETE' request.
        """
        return self.dispatch('delete', *args, **kwargs)

    def deserialize(
        self, response, key=None, model=None, page=None, first=0, last=None):
        """
        Returns a "data object" representing the specified response's JSON content.
        """
        if not key:
            return self.deserialize_response_data(
                self.json(response), model, page, first, last)
        else:
            return self.deserialize_response_data(
                self.json(response)[key], model, page, first, last)

    def deserialize_response_data(
        self, data, model=None, page=None, first=None, last=None):
        """
        Returns a "data object" representing the specified JSON data.
        """
        #
        # If we've got a 'dict', we first check to see if it has 'total'
        # and 'results' fields.
        # If it does, we save 'total' and recurse into 'results'.
        # Otherwise, 'model' certainly knows how to deserialize 'data'.
        #
        if isinstance(data, dict):
            if 'total' in data and 'results' in data:
                return ListPage(
                    data.get('total'), page, first, last,
                    self.deserialize_response_data(data.get('results'), model))
            if model:
                return model.deserialize(data)
            else:
                return data

        #
        # If we've got a 'list', we apply 'deserialize_response_data'
        # recursively.
        #
        elif isinstance(data, list):
            return [self.deserialize_response_data(e, model) for e in data]

        #
        # If neither 'dict' nor 'list', and no model was specified,
        # return 'data'.
        #
        elif not model:
            return data

        #
        # Indicate that we cannot deserialize 'data'.
        #
        raise MalformedResponseError()

    def url(self, endpoint='', params={}):
        #
        # Force conversion of 'params' values to string.
        #
        params = {key: str(value) for key, value in params.iteritems()}

        #
        # Build a URITemplate corresponding to the specified endpoint.
        #
        url = URITemplate(settings.API_BASE_URL + getattr(self, 'namespace', '') + endpoint)

        return url.expand(**params)

    def dispatch(self, method, endpoint='', **kwargs):
        """
        Attempts to dispatch an HTTP request to the specified endpoint.
        """

        #
        # Call the appropriate method on the appropriate URL.
        #
        try:
            response = getattr(self._session, method)(self.url(endpoint), **kwargs)
            if settings.DEBUG:
                logger.info('{0} request - {1} - {2}'.format(method, self.url(endpoint), kwargs.pop('data', '[]')))
                logger.info('response - {0} - {1}'.format(response.status_code, response.content))
            return response
        except ConnectionError as error:
            raise ServiceUnavailableError(cause=error)

    def get(self, *args, **kwargs):
        """
        Attempts to dispatch a 'GET' request.
        """
        return self.dispatch('get', *args, **kwargs)

    def handle(self, response):
        """
        Handles a response that could not be handled by its originating method.
        """
        cause = '{0} - {1}'.format(response.status_code, response.content)

        if response.status_code == 401:
            raise UnauthorizedRequestError(cause)

        raise UnexpectedResponseError(cause)

    def json(self, response):
        """
        Attempts to parse the given response's contents as JSON.
        """
        try:
            return response.json()
        except ValueError:
            raise MalformedResponseError()

    def post(self, *args, **kwargs):
        """
        Attempts to dispatch a 'POST' request.
        """
        return self.dispatch('post', data=json.dumps(kwargs.pop('data')), headers={'Content-Type': 'application/json'}, *args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Attempts to dispatch a 'PUT' request.
        """
        return self.dispatch('put', data=json.dumps(kwargs.pop('data')), headers={'Content-Type': 'application/json'}, *args, **kwargs)


class FetchableEntityApiMixin(object):
    def _fetch(self, id, entity_model=None):
        response = self.get(endpoint='/{id}'.format(id=id))
        if response.status_code == 200:
            return self.deserialize(response, model=entity_model)

        self.handle(response)


class ListableEntityApiMixin(object):
    def _list(self, page=1, limit=settings.LISTS_NUMBER_OF_ENTRIES_PER_PAGE,
              entity_model=None, endpoint='/', params={}, **kwargs):

        if entity_model is not None:
            params.update(entity_model.deserialize_filters(kwargs))

        params['limit'] = params.get('limit', limit)
        start = self.get_start(params.pop('start', None), page, params['limit'])
        params['start'] = start

        sort_by = kwargs.pop('sort_by', None)
        params.update(self.get_sort_by(sort_by))

        response = self.get(endpoint=endpoint, params=params)
        if settings.DEBUG:
            logger.info('list params - {0}'.format(params))

        if response.status_code == 200:
            return self.deserialize(
                response, page=page, first=start, model=entity_model)

        self.handle(response)

    @staticmethod
    def get_sort_by(sort_by):
        params = {}
        if sort_by is not None and sort_by != '':
            if sort_by[0] == '-':
                params['sortOrder'] = 'DESC'
                sort_by = sort_by[1:]
            else:
                params['sortOrder'] = 'ASC'
            params['orderBy'] = sort_by

        return params

    @staticmethod
    def get_start(start, page, limit):
        if start is None:
            start = (page - 1) * limit

        return start
