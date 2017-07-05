# -*- coding: utf-8 -*-


class BaseDataObject(object):
    """
    A base class to be subclassed by all other data objects.
    """

    def objects(self):
        return self.__dict__

    def serialize(self):
        objects = self.objects()
        return {k: v for (k, v) in objects.iteritems() if not k.startswith('_')}


class MappedFieldDataObject(BaseDataObject):
    """
    A base class somewhat simplifying deserialization using a dictionary
    to map class attributes to received or computed data fields.

    Subclasses of MappedFieldDataObject should contain a 'Meta' inner class with
    a 'field_mapping' dictionary attribute mapping from class variable to
    respective key in pre-deserialization data or a one argument callable
    receiving the data and returning a value to assign to the attribute in the
    constructed instance.

    A similar reverse mapping for serialization can be specified with the
    'reverse_field_mapping' dictionary attribute. This will only be used if
    the attribute exists and is a non-empty dictionary.

    If no value exists for some attribute then its value will be set to None.

    E.g.:

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
    """

    class Meta:
        field_mapping = {}
        reverse_field_mapping = {}
        filters_mapping = {}

    def __init__(self, *args, **kwargs):
        for d in args:
            for k, v in d.iteritems():
                self._set_field(k, v)
        for k, v in kwargs.iteritems():
            self._set_field(k, v)

    def _set_field(self, key, value):
        setattr(self, key, value)

    def serialize(self):
        if self.Meta.reverse_field_mapping:
            data = self.objects()
            result = dict([
                (k, v(data))
                if callable(v) else
                (k, data.get(v, None))
                for k, v in self.Meta.reverse_field_mapping.iteritems()])
            return {k: v for (k, v) in result.iteritems() if v is not None}
        else:
            return super(MappedFieldDataObject, self).serialize()

    @classmethod
    def deserialize_filters(cls, filters):
        if hasattr(cls.Meta, 'filters_mapping'):
            fields = dict([
                (k, v(filters))
                if callable(v) else
                (k, filters.get(v, None))
                for k, v in cls.Meta.filters_mapping.iteritems()])
        else:
            return {}

        return cls(**fields)

    @classmethod
    def deserialize(cls, data):
        fields = dict([
            (k, v(data))
            if callable(v) else
            (k, data.get(v))
            for k, v in cls.Meta.field_mapping.iteritems()])

        if not fields:
            return None

        return cls(**fields)


class MappedKeyDataObject(dict, MappedFieldDataObject):
    """
    A subclass of MappedFieldDataObject that is also a dict, assigning values to
    keys in a dictionary instead of fields in an object.
    Also overrides the __getattr__, __setattr__ and __delattr__ methods,
    meaning key-value pairs can also be accessed as fields in a regular object.

    Useful for populating Django forms, which only accept dictionaries.
    """

    def objects(self):
        return self

    def _set_field(self, key, value):
        pass

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError


# -----------------------------------------------------------------------------
# Auxiliary Data Types
# -----------------------------------------------------------------------------


class ListPage(list):

    def __init__(self, total, page=None, first=0, last=None, *args):
        self._total = total
        super(ListPage, self).__init__(*args)
        self._page = page or 1
        self._first = first + 1 if first < total else total
        self._last = last or (first + len(self))

    @property
    def page(self):
        return self._page

    @property
    def first(self):
        return self._first

    @property
    def last(self):
        return self._last

    @property
    def total(self):
        return self._total
