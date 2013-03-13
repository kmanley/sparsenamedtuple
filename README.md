#sparsenamedtuple#

A variant of Python's collections.namedtuple which uses less memory by not storing any None values.

##Usage##

Similar to namedtuple: 

```python
>>> from sparsenamedtuple import sparsenamedtuple
>>> Customer = sparsenamedtuple('Customer', 'username first middle last city state zip bday')
```

Instances are always created via kwargs, not positional arguments. Only specify the values that are
not None. 

```python
>>> cust1 = Customer(username='jdoe', state='NY')
```
    
sparsenamedtuples behave mostly the same as namedtuples; repr, _make, _replace, _asdict, item indexing, 
field access all work the same.

```python
>>> cust1
Customer(username='jdoe', first=None, middle=None, last=None, city=None, state='NY', zip=None, bday=None)
>>> cust1[0]
'jdoe'
cust1.state
'NY'
```
    
...but they use less memory when your data is sparse

```python
>>> ThinCustomer = sparsenamedtuple('Customer', 'username first middle last city state zip bday')
>>> FatCustomer = namedtuple('Customer', 'username first middle last city state zip bday')
>>> thin1 = ThinCustomer(username='kev')
>>> fat1 = FatCustomer('kev', None, None, None, None, None, None, None)
>>> import sys
>>> sys.getsizeof(thin1)
32
>>> sys.getsizeof(fat1)
56
```
    
How do they work? They simply store the indexes of fields that have values as the last item in the tuple.

```python
>>> tuple(fat1)
('kev', None, None, None, None, None, None, None)
>>> tuple(thin1)
('kev', (0,))
```

##Tests##
This module uses doctest. To run the tests type:

    python sparsenamedtuple.py    

#License#
Public Domain

