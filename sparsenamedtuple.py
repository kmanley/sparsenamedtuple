from operator import itemgetter as _itemgetter
from keyword import iskeyword as _iskeyword
from collections import OrderedDict
import sys as _sys

__all__ = ['sparsenamedtuple']

################################################################################
### sparsenamedtuple
################################################################################

_class_template = '''\
class {typename}(tuple):
    '{typename}({arg_list})'

    __slots__ = ()
    _fields = {field_names!r}
    _nfields = len(_fields)

    def __new__(_cls, **kwargs):
        return _cls._make(**kwargs)

    @classmethod
    def _make(_cls, **kwargs):
        'Make a new {typename} object from a sequence or iterable'
        indexes = []
        values = []
        for key, value in kwargs.iteritems():
            if value != None:
                indexes.append(_cls._fields.index(key))
                values.append(value)
        values.append(tuple(indexes))
        return _tuple.__new__(_cls, values)        

    def __repr__(self):
        'Return a nicely formatted representation string'
        return '{typename}({repr_fmt})' % tuple(self[x] for x in range(self._nfields))

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values'
        return OrderedDict((self._fields[x], self[x]) for x in range(self._nfields))
        
    def _asnamedtuple(self):
        return tuple(self[x] for x in range(self._nfields))
        
    def __eq__(self, other):
        return self._asnamedtuple() == other
        
    def __ne__(self, other):
        return not self.__eq__(other)

    __dict__ = property(_asdict)

    def _replace(_self, **kwargs):
        'Return a new {typename} object replacing specified fields with new values'
        vars = _self._asdict()
        vars.update(kwargs)
        return {typename}._make(**vars)

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return tuple(self)
        
    def __getitem__(self, n):
        if n < 0: 
            n = self._nfields + n
        elif n >= self._nfields:
            raise IndexError("tuple index out of range")
        try:
            pos = _tuple.__getitem__(self, -1).index(n)
        except ValueError:
            return None
        else:
            return _tuple.__getitem__(self, pos)

{field_defs}
'''

_repr_template = '{name}=%r'

_field_template = '''\
    {name} = _property(_itemgetter({index:d}), doc='Alias for field number {index:d}')
'''

def sparsenamedtuple(typename, field_names, verbose=False, rename=False):
    """Returns a new subclass of tuple with named fields.

    # sparsenamedtuples are defined similar to namedtuples
    >>> from collections import namedtuple
    >>> from sparsenamedtuple import sparsenamedtuple
    >>> Customer = namedtuple('Customer', 'username first middle last city state zip bday')
    >>> CustomerS = sparsenamedtuple('Customer', 'username first middle last city state zip bday')

    # __doc__ works the same
    >>> Customer.__doc__
    'Customer(username, first, middle, last, city, state, zip, bday)'
    >>> CustomerS.__doc__
    'Customer(username, first, middle, last, city, state, zip, bday)'

    # unlike namedtuples, sparsenamedtuples are always created by passing kwargs
    # Note that we don't pass the names of any None values
    >>> c1 = Customer('jdoe', None, None, None, None, 'NY', None, None)
    >>> c2 = CustomerS(username='jdoe', state='NY')
    
    # repr looks the same
    >>> c1
    Customer(username='jdoe', first=None, middle=None, last=None, city=None, state='NY', zip=None, bday=None)
    >>> c2
    Customer(username='jdoe', first=None, middle=None, last=None, city=None, state='NY', zip=None, bday=None)
    
    # but the sparsenamedtuple takes up less space in memory
    >>> import sys
    >>> sys.getsizeof(c1)
    56
    >>> sys.getsizeof(c2)
    36
    
    # _asdict works the same
    >>> c1._asdict()
    OrderedDict([('username', 'jdoe'), ('first', None), ('middle', None), ('last', None), ('city', None), ('state', 'NY'), ('zip', None), ('bday', None)])
    >>> c2._asdict()
    OrderedDict([('username', 'jdoe'), ('first', None), ('middle', None), ('last', None), ('city', None), ('state', 'NY'), ('zip', None), ('bday', None)])
    
    # indexing works the same as with namedtuple
    >>> c1[0]
    'jdoe'
    >>> c2[0]
    'jdoe'
    >>> c1[1]
    >>> c2[1]

    # accessing values by field name works the same as with namedtuple
    >>> c1.middle
    >>> c2.middle
    >>> c1.state
    'NY'
    >>> c2.state
    'NY'

    # here we can see how it works; in sparsenamedtuple the indexes of the specified values are stashed
    # in the last element of the tuple. For this reason, unfortunately you can't use tuple unpacking
    # in the same way that you would with a regular namedtuple
    >>> tuple(c1)
    ('jdoe', None, None, None, None, 'NY', None, None)
    >>> tuple(c2)
    ('jdoe', 'NY', (0, 5))
    
    # you can use _asnamedtuple to convert a sparsenamedtuple into its namedtuple equivalent tuple;
    # this allows tuple unpacking similar to namedtuple
    >>> c2._asnamedtuple()
    ('jdoe', None, None, None, None, 'NY', None, None)

    # equality of sparsenamedtuple and namedtuple works...
    >>> c2 == c1
    True
    
    # but is not symmetrical; you have to specify the sparsenamedtuple as the lvalue
    >>> c1 == c2
    False
    """

    # Validate the field names.  At the user's option, either generate an error
    # message or automatically replace the field name with a valid name.
    if isinstance(field_names, basestring):
        field_names = field_names.replace(',', ' ').split()
    field_names = map(str, field_names)
    if rename:
        seen = set()
        for index, name in enumerate(field_names):
            if (not all(c.isalnum() or c=='_' for c in name)
                or _iskeyword(name)
                or not name
                or name[0].isdigit()
                or name.startswith('_')
                or name in seen):
                field_names[index] = '_%d' % index
            seen.add(name)
    for name in [typename] + field_names:
        if not all(c.isalnum() or c=='_' for c in name):
            raise ValueError('Type names and field names can only contain '
                             'alphanumeric characters and underscores: %r' % name)
        if _iskeyword(name):
            raise ValueError('Type names and field names cannot be a '
                             'keyword: %r' % name)
        if name[0].isdigit():
            raise ValueError('Type names and field names cannot start with '
                             'a number: %r' % name)
    seen = set()
    for name in field_names:
        if name.startswith('_') and not rename:
            raise ValueError('Field names cannot start with an underscore: '
                             '%r' % name)
        if name in seen:
            raise ValueError('Encountered duplicate field name: %r' % name)
        seen.add(name)

    # Fill-in the class template
    class_definition = _class_template.format(
        typename = typename,
        field_names = tuple(field_names),
        num_fields = len(field_names),
        arg_list = repr(tuple(field_names)).replace("'", "")[1:-1],
        repr_fmt = ', '.join(_repr_template.format(name=name)
                             for name in field_names),
        field_defs = '\n'.join(_field_template.format(index=index, name=name)
                               for index, name in enumerate(field_names))
    )
    if verbose:
        print class_definition

    # Execute the template string in a temporary namespace and support
    # tracing utilities by setting a value for frame.f_globals['__name__']
    namespace = dict(_itemgetter=_itemgetter, __name__='sparsenamedtuple_%s' % typename,
                     OrderedDict=OrderedDict, _property=property, _tuple=tuple)
    try:
        exec class_definition in namespace
    except SyntaxError as e:
        raise SyntaxError(e.message + ':\n' + class_definition)
    result = namespace[typename]

    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the named tuple is created.  Bypass this step in enviroments where
    # sys._getframe is not defined (Jython for example) or sys._getframe is not
    # defined for arguments greater than 0 (IronPython).
    try:
        result.__module__ = _sys._getframe(1).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass

    return result

if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False)