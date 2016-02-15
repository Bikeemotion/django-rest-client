=====
Django Rest Client
=====

Django Rest Client App

Quick start
-----------

1. Add "django_rest_client" to INSTALLED_APPS:
  INSTALLED_APPS = {
    ...
    'django_rest_client'
  }

2. Define settings:
    LISTS_NUMBER_OF_ENTRIES_PER_PAGE

    API_BASE_URL

3. Example of RestClient:

class AuthApiClient(RestClientBase):
    namespace = '<base-endpoint>'

    def login(self, email, password):
        data = {
            'authId': email,
            'password': password
        }

        response = self.post(endpoint='/auth', data=data)

        if response.status_code == 200:
            return True
        elif response.status_code == requests.codes.unauthorized:
            return

        self.handle(response)


4. Example of Model

class ExampleMappedFieldDataObject(MappedFieldDataObject):
    class Meta:
        field_mapping = {
            'attribute_one': 'someKey',
            'attribute_two': lambda x: x.get('anotherKey') or False
        }
        reverse_field_mapping = {
            'someKey': 'attribute_one',
            'anotherKey': 'attribute_two'
        }
        filters_mapping = {
            'someKey': 'filter_one',
        }
