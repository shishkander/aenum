"""Python Advanced Enumerations & NameTuples"""

import sys as _sys
from collections import OrderedDict

__all__ = [
        'Constant', 'constant', 'skip'
        'Enum', 'IntEnum', 'AutoNumberEnum', 'OrderedEnum', 'UniqueEnum', 'enum', 'extend_enum', 'unique',
        'NamedTuple',
        ]

version = 1, 3, 0

pyver = float('%s.%s' % _sys.version_info[:2])

try:
    any
except NameError:
    def any(iterable):
        for element in iterable:
            if element:
                return True
        return False

try:
    basestring
except NameError:
    # In Python 2 basestring is the ancestor of both str and unicode
    # in Python 3 it's just str, but was missing in 3.1
    basestring = str

try:
    unicode
except NameError:
    # In Python 3 unicode no longer exists (it's just str)
    unicode = str

try:
    long
    baseinteger = int, long
except NameError:
    baseinteger = int
# deprecated
baseint = baseinteger

try:
    NoneType
except NameError:
    NoneType = type(None)


class _RouteClassAttributeToGetattr(object):
    """Route attribute access on a class to __getattr__.

    This is a descriptor, used to define attributes that act differently when
    accessed through an instance and through a class.  Instance access remains
    normal, but access to an attribute through a class will be routed to the
    class's __getattr__ method; this is done by raising AttributeError.
    """
    def __init__(self, fget=None):
        self.fget = fget

    def __get__(self, instance, ownerclass=None):
        if instance is None:
            raise AttributeError()
        return self.fget(instance)

    def __set__(self, instance, value):
        raise AttributeError("can't set attribute")

    def __delete__(self, instance):
        raise AttributeError("can't delete attribute")


class skip(object):
    """
    Protects item from becaming an Enum member during class creation.
    """
    def __init__(self, value):
        self.value = value

    def __get__(self, instance, ownerclass=None):
        return self.value


def _is_descriptor(obj):
    """Returns True if obj is a descriptor, False otherwise."""
    return (
            hasattr(obj, '__get__') or
            hasattr(obj, '__set__') or
            hasattr(obj, '__delete__'))


def _is_dunder(name):
    """Returns True if a __dunder__ name, False otherwise."""
    return (name[:2] == name[-2:] == '__' and
            name[2:3] != '_' and
            name[-3:-2] != '_' and
            len(name) > 4)


def _is_sunder(name):
    """Returns True if a _sunder_ name, False otherwise."""
    return (name[0] == name[-1] == '_' and
            name[1:2] != '_' and
            name[-2:-1] != '_' and
            len(name) > 2)


def _make_class_unpicklable(cls):
    """Make the given class un-picklable."""
    def _break_on_call_reduce(self, protocol=None):
        raise TypeError('%r cannot be pickled' % self)
    cls.__reduce_ex__ = _break_on_call_reduce
    cls.__module__ = '<unknown>'


# metaclass and class dict for Constant

class _ConstantDict(dict):
    """Track enum member order and ensure member names are not reused.

    ConstantMeta will use the names found in self._names as the
    enumeration member names.
    """
    def __init__(self):
        super(_ConstantDict, self).__init__()
        self._names = []

    def __setitem__(self, key, value):
        """Changes anything not dundered or not a descriptor.

        If an enum member name is used twice, an error is raised; duplicate
        values are not checked for.

        Single underscore (sunder) names are reserved.

        Note:   in 3.x __order__ is simply discarded as a not necessary piece
                leftover from 2.x
        """
        if _is_sunder(key):
            raise ValueError('_names_ are reserved for future Constant use')
        elif _is_dunder(key):
            pass
        elif key in self._names:
            # overwriting an existing constant?
            raise TypeError('Attempted to reuse name: %r' % key)
        elif not _is_descriptor(value):
            if key in self:
                # overwriting a descriptor?
                raise TypeError('%s already defined as: %r' % (key, self[key]))
            self._names.append(key)
        super(_ConstantDict, self).__setitem__(key, value)


class ConstantMeta(type):
    """
    Block attempts to reassign Constant attributes.
    """
    def __new__(metacls, cls, bases, clsdict):
        _ConstantCache = {}
        if type(clsdict) is dict:
            original_dict = clsdict
            clsdict = _ConstantDict()
            for k, v in original_dict.items():
                clsdict[k] = v
        newdict = {}
        for name, obj in clsdict.items():
            if name in clsdict._names:
                actual_type = type(obj)
                value = obj
                obj_type = _ConstantCache.get(actual_type)
                if obj_type is None:
                    obj_type = type(cls, (Constant, type(obj)), {})
                    _ConstantCache[type(obj)] = obj_type
                obj = actual_type.__new__(obj_type, obj)
                obj._name_ = name
                obj._value_ = value
            elif isinstance(obj, skip):
                obj = obj.value
            newdict[name] = obj
        return super(ConstantMeta, metacls).__new__(metacls, cls, bases, newdict)

    def __setattr__(cls, name, value):
        """Block attempts to reassign Constants.
        """
        cur_obj = cls.__dict__.get(name)
        if isinstance(cur_obj, Constant):
            raise AttributeError('Cannot rebind constant <%s.%s>' % (cur_obj.__class__.__name__, cur_obj._name_))
        super(ConstantMeta, cls).__setattr__(name, value)

temp_constant_dict = {}
temp_constant_dict['__doc__'] = "Constants protection.\n\n    Derive from this class to lock Constants.\n\n"

def __new__(cls, value):
    raise ValueError("cannot create new instances of %s" % (cls.__name__, ))
temp_constant_dict['__new__'] = __new__
del __new__

def __repr__(self):
    return "<%s.%s: %r>" % (
            self.__class__.__name__, self._name_, self._value_)
temp_constant_dict['__repr__'] = __repr__
del __repr__

Constant = ConstantMeta('Constant', (object, ), temp_constant_dict)
del temp_constant_dict

class constant(object):
    def __init__(self, value):
        self.value = value

    def __get__(self, *args):
        return self.value

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.value)


# Dummy value for Enum as EnumMeta explicity checks for it, but of course until
# EnumMeta finishes running the first time the Enum class doesn't exist.  This
# is also why there are checks in EnumMeta like `if Enum is not None`
Enum = None

class enum(object):
    """
    Helper class to track args, kwds.
    """
    def __init__(self, *args, **kwds):
        self.args = args
        self.kwds = kwds

    def __repr__(self):
        final = []
        args = ', '.join(['%r' % a for a in self.args])
        if args:
            final.append(args)
        kwds = ', '.join([('%s=%r') % (k, v) for k, v in sorted(self.kwds.items())])
        if kwds:
            final.append(kwds)
        return 'enum(%s)' % ', '.join(final)

class _EnumDict(dict):
    """Track enum member order and ensure member names are not reused.

    EnumMeta will use the names found in self._member_names as the
    enumeration member names.
    """
    def __init__(self, locked=True):
        super(_EnumDict, self).__init__()
        self._member_names = []
        self._value = 0
        self._locked = locked

    def __getitem__(self, key):
        if self._locked or _is_dunder(key) or key in self:
            return super(_EnumDict, self).__getitem__(key)
        try:
            # try to generate the next value
            value = self._value + 1
            self.__setitem__(key, value)
            return value
        except:
            # couldn't work the magic, report error
            raise KeyError('%s not found' % key)

    def __setitem__(self, key, value):
        """Changes anything not dundered or not a descriptor.

        If an enum member name is used twice, an error is raised; duplicate
        values are not checked for.

        Single underscore (sunder) names are reserved.

        Note:   in 3.x __order__ is simply discarded as a not necessary piece
                leftover from 2.x
        """
        if _is_sunder(key):
            raise ValueError('_names_ are reserved for future Enum use')
        elif _is_dunder(key):
            # __order__, if present, should be first
            pass
        elif key in self._member_names:
            # descriptor overwriting an enum?
            raise TypeError('Attempted to reuse name: %r' % key)
        elif not _is_descriptor(value):
            if key in self:
                # enum overwriting a descriptor?
                raise TypeError('%s already defined as: %r' % (key, self[key]))
            self._member_names.append(key)
            self._value = value
        else:
            # not a new member, turn off the autoassign magic
            self._locked = True
        super(_EnumDict, self).__setitem__(key, value)


class EnumMeta(type):
    """Metaclass for Enum"""
    @classmethod
    def __prepare__(metacls, cls, bases, auto=False, init=None):
        return _EnumDict(locked=not auto)

    def __init__(cls, *args , **kwds):
        super(EnumMeta, cls).__init__(*args)

    def __new__(metacls, cls, bases, clsdict, auto=False, init=''):
        # an Enum class is final once enumeration items have been defined; it
        # cannot be mixed with other types (int, float, etc.) if it has an
        # inherited __new__ unless a new __new__ is defined (or the resulting
        # class will fail).
        if type(clsdict) is dict:
            original_dict = clsdict
            clsdict = _EnumDict()
            for k, v in original_dict.items():
                clsdict[k] = v
        else:
            clsdict._locked = True

        # check for clash between class and init
        if init and clsdict.get('__init__'):
            raise TypeError('cannot specify init and define an __init__ method')

        member_type, first_enum = metacls._get_mixins_(bases)
        __new__, save_new, use_args = metacls._find_new_(clsdict, member_type,
                                                        first_enum)
        # save enum items into separate mapping so they don't get baked into
        # the new class
        members = dict((k, clsdict[k]) for k in clsdict._member_names)
        for name in clsdict._member_names:
            del clsdict[name]

        # py2 support for definition order
        __order__ = clsdict.get('__order__')
        if __order__ is None:
            if pyver < 3.0:
                try:
                    __order__ = [name for (name, value) in sorted(members.items(), key=lambda item: item[1])]
                except TypeError:
                    __order__ = [name for name in sorted(members.keys())]
            else:
                __order__ = clsdict._member_names

        else:
            del clsdict['__order__']
            __order__ = __order__.replace(',', ' ').split()
            aliases = [name for name in members if name not in __order__]
            if pyver >= 3.0:
                unique_members = [n for n in clsdict._member_names if n in __order__]
                if __order__ != unique_members:
                    raise TypeError('member order does not match __order__')
            __order__ += aliases

        # check for illegal enum names (any others?)
        invalid_names = set(members) & set(['mro'])
        if invalid_names:
            raise ValueError('Invalid enum member name(s): %s' % (
                ', '.join(invalid_names), ))

        # save attributes from super classes so we know if we can take
        # the shortcut of storing members in the class dict
        base_attributes = set([a for b in bases for a in b.__dict__])
        # create our new Enum type
        enum_class = super(EnumMeta, metacls).__new__(metacls, cls, bases, clsdict)
        enum_class._auto_init_ = init.replace(',',' ').split()
        enum_class._member_names_ = []               # names in random order
        enum_class._member_map_ = OrderedDict()
        enum_class._member_type_ = member_type

        # Reverse value->name map for hashable values.
        enum_class._value2member_map_ = {}

        # instantiate them, checking for duplicates as we go
        # we instantiate first instead of checking for duplicates first in case
        # a custom __new__ is doing something funky with the values -- such as
        # auto-numbering ;)
        if __new__ is None:
            __new__ = enum_class.__new__
        for member_name in __order__:
            value = members[member_name]
            kwds = {}
            if isinstance(value, enum):
                args = value.args
                kwds = value.kwds
            elif not isinstance(value, tuple):
                args = (value, )
            else:
                args = value
            if member_type is tuple:   # special case for tuple enums
                args = (args, )     # wrap it one more time
            if not use_args or not (args or kwds):
                enum_member = __new__(enum_class)
                if not hasattr(enum_member, '_value_'):
                    enum_member._value_ = value
            else:
                enum_member = __new__(enum_class, *args, **kwds)
                if not hasattr(enum_member, '_value_'):
                    enum_member._value_ = member_type(*args)
            value = enum_member._value_
            enum_member._name_ = member_name
            enum_member.__objclass__ = enum_class
            enum_member.__init__(*args, **kwds)
            # If another member with the same value was already defined, the
            # new member becomes an alias to the existing one.
            for name, canonical_member in enum_class._member_map_.items():
                if canonical_member.value == enum_member._value_:
                    enum_member = canonical_member
                    break
            else:
                # Aliases don't appear in member names (only in __members__).
                enum_class._member_names_.append(member_name)
            # performance boost for any member that would not shadow
            # a DynamicClassAttribute (aka _RouteClassAttributeToGetattr)
            if member_name not in base_attributes:
                setattr(enum_class, member_name, enum_member)
            # now add to _member_map_
            enum_class._member_map_[member_name] = enum_member
            try:
                # This may fail if value is not hashable. We can't add the value
                # to the map, and by-value lookups for this value will be
                # linear.
                enum_class._value2member_map_[value] = enum_member
            except TypeError:
                pass


        # If a custom type is mixed into the Enum, and it does not know how
        # to pickle itself, pickle.dumps will succeed but pickle.loads will
        # fail.  Rather than have the error show up later and possibly far
        # from the source, sabotage the pickle protocol for this class so
        # that pickle.dumps also fails.
        #
        # However, if the new class implements its own __reduce_ex__, do not
        # sabotage -- it's on them to make sure it works correctly.  We use
        # __reduce_ex__ instead of any of the others as it is preferred by
        # pickle over __reduce__, and it handles all pickle protocols.
        unpicklable = False
        if '__reduce_ex__' not in clsdict:
            if member_type is not object:
                methods = ('__getnewargs_ex__', '__getnewargs__',
                        '__reduce_ex__', '__reduce__')
                if not any(m in member_type.__dict__ for m in methods):
                    _make_class_unpicklable(enum_class)
                    unpicklable = True


        # double check that repr and friends are not the mixin's or various
        # things break (such as pickle)
        for name in ('__repr__', '__str__', '__format__', '__reduce_ex__'):
            class_method = getattr(enum_class, name)
            obj_method = getattr(member_type, name, None)
            enum_method = getattr(first_enum, name, None)
            if name not in clsdict and class_method is not enum_method:
                if name == '__reduce_ex__' and unpicklable:
                    continue
                setattr(enum_class, name, enum_method)

        # method resolution and int's are not playing nice
        # Python's less than 2.6 use __cmp__

        if pyver < 2.6:

            if issubclass(enum_class, int):
                setattr(enum_class, '__cmp__', getattr(int, '__cmp__'))

        elif pyver < 3.0:

            if issubclass(enum_class, int):
                for method in (
                        '__le__',
                        '__lt__',
                        '__gt__',
                        '__ge__',
                        '__eq__',
                        '__ne__',
                        '__hash__',
                        ):
                    setattr(enum_class, method, getattr(int, method))

        # replace any other __new__ with our own (as long as Enum is not None,
        # anyway) -- again, this is to support pickle
        if Enum is not None:
            # if the user defined their own __new__, save it before it gets
            # clobbered in case they subclass later
            if save_new:
                setattr(enum_class, '__member_new__', enum_class.__dict__['__new__'])
            setattr(enum_class, '__new__', Enum.__dict__['__new__'])
        return enum_class

    def __call__(cls, value, names=None, module=None, type=None, start=1):
        """Either returns an existing member, or creates a new enum class.

        This method is used both when an enum class is given a value to match
        to an enumeration member (i.e. Color(3)) and for the functional API
        (i.e. Color = Enum('Color', names='red green blue')).

        When used for the functional API: `module`, if set, will be stored in
        the new class' __module__ attribute; `type`, if set, will be mixed in
        as the first base class.

        Note: if `module` is not set this routine will attempt to discover the
        calling module by walking the frame stack; if this is unsuccessful
        the resulting class will not be pickleable.
        """
        if names is None:  # simple value lookup
            return cls.__new__(cls, value)
        # otherwise, functional API: we're creating a new Enum type
        return cls._create_(value, names, module=module, type=type, start=start)

    def __contains__(cls, member):
        return isinstance(member, cls) and member.name in cls._member_map_

    def __delattr__(cls, attr):
        # nicer error message when someone tries to delete an attribute
        # (see issue19025).
        if attr in cls._member_map_:
            raise AttributeError(
                    "%s: cannot delete Enum member." % cls.__name__)
        super(EnumMeta, cls).__delattr__(attr)

    def __dir__(self):
        return (['__class__', '__doc__', '__members__', '__module__'] +
                self._member_names_)

    @property
    def __members__(cls):
        """Returns a mapping of member name->value.

        This mapping lists all enum members, including aliases. Note that this
        is a copy of the internal mapping.
        """
        return cls._member_map_.copy()

    def __getattr__(cls, name):
        """Return the enum member matching `name`

        We use __getattr__ instead of descriptors or inserting into the enum
        class' __dict__ in order to support `name` and `value` being both
        properties for enum members (which live in the class' __dict__) and
        enum members themselves.
        """
        if _is_dunder(name):
            raise AttributeError(name)
        try:
            return cls._member_map_[name]
        except KeyError:
            raise AttributeError(name)

    def __getitem__(cls, name):
        return cls._member_map_[name]

    def __iter__(cls):
        return (cls._member_map_[name] for name in cls._member_names_)

    def __reversed__(cls):
        return (cls._member_map_[name] for name in reversed(cls._member_names_))

    def __len__(cls):
        return len(cls._member_names_)

    def __repr__(cls):
        return "<enum %r>" % cls.__name__

    def __setattr__(cls, name, value):
        """Block attempts to reassign Enum members/constants.

        A simple assignment to the class namespace only changes one of the
        several possible ways to get an Enum member from the Enum class,
        resulting in an inconsistent Enumeration.
        """
        member_map = cls.__dict__.get('_member_map_', {})
        if name in member_map:
            raise AttributeError('Cannot rebind %s.' % name)
        cur_obj = cls.__dict__.get(name)
        if isinstance(cur_obj, constant):
            raise AttributeError('Cannot rebind %r' % cur_obj)
        super(EnumMeta, cls).__setattr__(name, value)

    def _create_(cls, class_name, names=None, module=None, type=None, start=1):
        """Convenience method to create a new Enum class.

        `names` can be:

        * A string containing member names, separated either with spaces or
          commas.  Values are auto-numbered from 1.
        * An iterable of member names.  Values are auto-numbered from 1.
        * An iterable of (member name, value) pairs.
        * A mapping of member name -> value.
        """
        if pyver < 3.0:
            # if class_name is unicode, attempt a conversion to ASCII
            if isinstance(class_name, unicode):
                try:
                    class_name = class_name.encode('ascii')
                except UnicodeEncodeError:
                    raise TypeError('%r is not representable in ASCII' % class_name)
        metacls = cls.__class__
        if type is None:
            bases = (cls, )
        else:
            bases = (type, cls)
        clsdict = metacls.__prepare__(class_name, bases)
        __order__ = []

        # special processing needed for names?
        if isinstance(names, basestring):
            names = names.replace(',', ' ').split()
        if isinstance(names, (tuple, list)) and isinstance(names[0], basestring):
            names = [(e, i+start) for (i, e) in enumerate(names)]

        # Here, names is either an iterable of (name, value) or a mapping.
        item = None  # in case names is empty
        for item in names:
            if isinstance(item, basestring):
                member_name, member_value = item, names[item]
            else:
                member_name, member_value = item
            clsdict[member_name] = member_value
            __order__.append(member_name)
        # only set __order__ in clsdict if name/value was not from a mapping
        if not isinstance(item, basestring):
            clsdict['__order__'] = ' '.join(__order__)
        enum_class = metacls.__new__(metacls, class_name, bases, clsdict)

        # TODO: replace the frame hack if a blessed way to know the calling
        # module is ever developed
        if module is None:
            try:
                module = _sys._getframe(2).f_globals['__name__']
            except (AttributeError, KeyError):
                pass
        if module is None:
            _make_class_unpicklable(enum_class)
        else:
            enum_class.__module__ = module

        return enum_class

    @staticmethod
    def _get_mixins_(bases):
        """Returns the type for creating enum members, and the first inherited
        enum class.

        bases: the tuple of bases that was given to __new__
        """
        if not bases or Enum is None:
            return object, Enum


        # double check that we are not subclassing a class with existing
        # enumeration members; while we're at it, see if any other data
        # type has been mixed in so we can use the correct __new__
        member_type = first_enum = None
        for base in bases:
            if  (base is not Enum and
                    issubclass(base, Enum) and
                    base._member_names_):
                raise TypeError("Cannot extend enumerations via subclassing.")
        # base is now the last base in bases
        if not issubclass(base, Enum):
            raise TypeError("new enumerations must be created as "
                    "`ClassName([mixin_type,] enum_type)`")

        # get correct mix-in type (either mix-in type of Enum subclass, or
        # first base if last base is Enum)
        if not issubclass(bases[0], Enum):
            member_type = bases[0]     # first data type
            first_enum = bases[-1]  # enum type
        else:
            for base in bases[0].__mro__:
                # most common: (IntEnum, int, Enum, object)
                # possible:    (<Enum 'AutoIntEnum'>, <Enum 'IntEnum'>,
                #               <class 'int'>, <Enum 'Enum'>,
                #               <class 'object'>)
                if issubclass(base, Enum):
                    if first_enum is None:
                        first_enum = base
                else:
                    if member_type is None:
                        member_type = base

        return member_type, first_enum

    if pyver < 3.0:
        @staticmethod
        def _find_new_(clsdict, member_type, first_enum):
            """Returns the __new__ to be used for creating the enum members.

            clsdict: the class dictionary given to __new__
            member_type: the data type whose __new__ will be used by default
            first_enum: enumeration to check for an overriding __new__
            """
            # now find the correct __new__, checking to see of one was defined
            # by the user; also check earlier enum classes in case a __new__ was
            # saved as __member_new__
            __new__ = clsdict.get('__new__', None)
            if __new__:
                return None, True, True      # __new__, save_new, use_args

            N__new__ = getattr(None, '__new__')
            O__new__ = getattr(object, '__new__')
            if Enum is None:
                E__new__ = N__new__
            else:
                E__new__ = Enum.__dict__['__new__']
            # check all possibles for __member_new__ before falling back to
            # __new__
            for method in ('__member_new__', '__new__'):
                for possible in (member_type, first_enum):
                    try:
                        target = possible.__dict__[method]
                    except (AttributeError, KeyError):
                        target = getattr(possible, method, None)
                    if target not in [
                            None,
                            N__new__,
                            O__new__,
                            E__new__,
                            ]:
                        if method == '__member_new__':
                            clsdict['__new__'] = target
                            return None, False, True
                        if isinstance(target, staticmethod):
                            target = target.__get__(member_type)
                        __new__ = target
                        break
                if __new__ is not None:
                    break
            else:
                __new__ = object.__new__

            # if a non-object.__new__ is used then whatever value/tuple was
            # assigned to the enum member name will be passed to __new__ and to the
            # new enum member's __init__
            if __new__ is object.__new__:
                use_args = False
            else:
                use_args = True

            return __new__, False, use_args
    else:
        @staticmethod
        def _find_new_(clsdict, member_type, first_enum):
            """Returns the __new__ to be used for creating the enum members.

            clsdict: the class dictionary given to __new__
            member_type: the data type whose __new__ will be used by default
            first_enum: enumeration to check for an overriding __new__
            """
            # now find the correct __new__, checking to see of one was defined
            # by the user; also check earlier enum classes in case a __new__ was
            # saved as __member_new__
            __new__ = clsdict.get('__new__', None)

            # should __new__ be saved as __member_new__ later?
            save_new = __new__ is not None

            if __new__ is None:
                # check all possibles for __member_new__ before falling back to
                # __new__
                for method in ('__member_new__', '__new__'):
                    for possible in (member_type, first_enum):
                        target = getattr(possible, method, None)
                        if target not in (
                                None,
                                None.__new__,
                                object.__new__,
                                Enum.__new__,
                                ):
                            __new__ = target
                            break
                    if __new__ is not None:
                        break
                else:
                    __new__ = object.__new__

            # if a non-object.__new__ is used then whatever value/tuple was
            # assigned to the enum member name will be passed to __new__ and to the
            # new enum member's __init__
            if __new__ is object.__new__:
                use_args = False
            else:
                use_args = True

            return __new__, save_new, use_args


########################################################
# In order to support Python 2 and 3 with a single
# codebase we have to create the Enum methods separately
# and then use the `type(name, bases, dict)` method to
# create the class.
########################################################
temp_enum_dict = {}
temp_enum_dict['__doc__'] = "Generic enumeration.\n\n    Derive from this class to define new enumerations.\n\n"

def __init__(self, *args, **kwds):
    # auto-init method
    _auto_init_ = self._auto_init_
    if _auto_init_:
        for name, arg in zip(_auto_init_, args):
            setattr(self, name, arg)
        if len(args) < len(_auto_init_):
            remaining_args = _auto_init_[len(args):]
            for name in remaining_args:
                value = kwds.pop(name, undefined)
                if value is undefined:
                    raise TypeError('invalid keyword: %r' % name)
                setattr(self, name, value)
            if kwds:
                # too many keyword arguments
                raise TypeError('invalid keyword(s): %s' % ', '.join(kwds.keys()))
temp_enum_dict['__init__'] = __init__
del __init__

def __new__(cls, value):
    # all enum instances are actually created during class construction
    # without calling this method; this method is called by the metaclass'
    # __call__ (i.e. Color(3) ), and by pickle
    if type(value) is cls:
        # For lookups like Color(Color.red)
        value = value.value
        #return value
    # by-value search for a matching enum member
    # see if it's in the reverse mapping (for hashable values)
    try:
        if value in cls._value2member_map_:
            return cls._value2member_map_[value]
    except TypeError:
        # not there, now do long search -- O(n) behavior
        for member in cls._member_map_.values():
            if member.value == value:
                return member
    raise ValueError("%s is not a valid %s" % (value, cls.__name__))
temp_enum_dict['__new__'] = __new__
del __new__

def __repr__(self):
    return "<%s.%s: %r>" % (
            self.__class__.__name__, self._name_, self._value_)
temp_enum_dict['__repr__'] = __repr__
del __repr__

def __str__(self):
    return "%s.%s" % (self.__class__.__name__, self._name_)
temp_enum_dict['__str__'] = __str__
del __str__

if pyver >= 3.0:
    def __dir__(self):
        added_behavior = [
                m
                for cls in self.__class__.mro()
                for m in cls.__dict__
                if m[0] != '_' and m not in self._member_map_
                ]
        return (['__class__', '__doc__', '__module__', ] + added_behavior)
    temp_enum_dict['__dir__'] = __dir__
    del __dir__

def __format__(self, format_spec):
    # mixed-in Enums should use the mixed-in type's __format__, otherwise
    # we can get strange results with the Enum name showing up instead of
    # the value

    # pure Enum branch
    if self._member_type_ is object:
        cls = str
        val = str(self)
    # mix-in branch
    else:
        cls = self._member_type_
        val = self.value
    return cls.__format__(val, format_spec)
temp_enum_dict['__format__'] = __format__
del __format__


####################################
# Python's less than 2.6 use __cmp__

if pyver < 2.6:

    def __cmp__(self, other):
        if type(other) is self.__class__:
            if self is other:
                return 0
            return -1
        return NotImplemented
        raise TypeError("unorderable types: %s() and %s()" % (self.__class__.__name__, other.__class__.__name__))
    temp_enum_dict['__cmp__'] = __cmp__
    del __cmp__

else:

    def __le__(self, other):
        raise TypeError("unorderable types: %s() <= %s()" % (self.__class__.__name__, other.__class__.__name__))
    temp_enum_dict['__le__'] = __le__
    del __le__

    def __lt__(self, other):
        raise TypeError("unorderable types: %s() < %s()" % (self.__class__.__name__, other.__class__.__name__))
    temp_enum_dict['__lt__'] = __lt__
    del __lt__

    def __ge__(self, other):
        raise TypeError("unorderable types: %s() >= %s()" % (self.__class__.__name__, other.__class__.__name__))
    temp_enum_dict['__ge__'] = __ge__
    del __ge__

    def __gt__(self, other):
        raise TypeError("unorderable types: %s() > %s()" % (self.__class__.__name__, other.__class__.__name__))
    temp_enum_dict['__gt__'] = __gt__
    del __gt__


def __eq__(self, other):
    if type(other) is self.__class__:
        return self is other
    return NotImplemented
temp_enum_dict['__eq__'] = __eq__
del __eq__

def __ne__(self, other):
    if type(other) is self.__class__:
        return self is not other
    return NotImplemented
temp_enum_dict['__ne__'] = __ne__
del __ne__

def __hash__(self):
    return hash(self._name_)
temp_enum_dict['__hash__'] = __hash__
del __hash__

def __bool__(self):
    return bool(self._value_)
if pyver < 3.0:
    temp_enum_dict['__nonzero__'] = __bool__
else:
    temp_enum_dict['__bool__'] = __bool__
    del __bool__

def __reduce_ex__(self, proto):
    return self.__class__, (self._value_, )
temp_enum_dict['__reduce_ex__'] = __reduce_ex__
del __reduce_ex__

# _RouteClassAttributeToGetattr is used to provide access to the `name`
# and `value` properties of enum members while keeping some measure of
# protection from modification, while still allowing for an enumeration
# to have members named `name` and `value`.  This works because enumeration
# members are not set directly on the enum class -- __getattr__ is
# used to look them up.

@_RouteClassAttributeToGetattr
def name(self):
    return self._name_
temp_enum_dict['name'] = name
del name

@_RouteClassAttributeToGetattr
def value(self):
    return self._value_
temp_enum_dict['value'] = value
del value

@classmethod
def _convert(cls, name, module, filter, source=None):
    """
    Create a new Enum subclass that replaces a collection of global constants
    """
    # convert all constants from source (or module) that pass filter() to
    # a new Enum called name, and export the enum and its members back to
    # module;
    # also, replace the __reduce_ex__ method so unpickling works in
    # previous Python versions
    module_globals = vars(_sys.modules[module])
    if source:
        source = vars(source)
    else:
        source = module_globals
    members = dict((name, value) for name, value in source.items() if filter(name))
    cls = cls(name, members, module=module)
    cls.__reduce_ex__ = _reduce_ex_by_name
    module_globals.update(cls.__members__)
    module_globals[name] = cls
    return cls
temp_enum_dict['_convert'] = _convert
del _convert

def _reduce_ex_by_name(self, proto):
    return self.name

Enum = EnumMeta('Enum', (object, ), temp_enum_dict)
del temp_enum_dict

# Enum has now been created
###########################

class IntEnum(int, Enum):
    """Enum where members are also (and must be) ints"""

class AutoNumberEnum(Enum):
    """
    Automatically assign increasing values to members.

    Py3: numbers match creation order
    Py2: numbers are randomly assigned
    """
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

class UniqueEnum(Enum):
    """
    Ensure no duplicate values exist.
    """
    def __init__(self, *args):
        cls = self.__class__
        if any(self.value == e.value for e in cls):
            a = self.name
            e = cls(self.value).name
            raise ValueError(
                    "aliases not allowed in UniqueEnum:  %r --> %r"
                    % (a, e))

class OrderedEnum(Enum):
    """
    Add ordering based on values of Enum members.
    """
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self._value_ >= other._value_
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self._value_ > other._value_
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self._value_ <= other._value_
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self._value_ < other._value_
        return NotImplemented

def convert(enum, name, module, filter, source=None):
    """
    Create a new Enum subclass that replaces a collection of global constants

    enum: Enum, IntEnum, ...
    name: name of new Enum
    module: name of module (__name__ in global context)
    filter: function that returns True if name should be converted to Enum member
    source: namespace to check (defaults to 'module')
    """
    # convert all constants from source (or module) that pass filter() to
    # a new Enum called name, and export the enum and its members back to
    # module;
    # also, replace the __reduce_ex__ method so unpickling works in
    # previous Python versions
    module_globals = vars(_sys.modules[module])
    if source:
        source = vars(source)
    else:
        source = module_globals
    members = dict((name, value) for name, value in source.items() if filter(name))
    enum = enum(name, members, module=module)
    enum.__reduce_ex__ = _reduce_ex_by_name
    module_globals.update(enum.__members__)
    module_globals[name] = enum

def export(enumeration, namespace):
    """
    Export the enumeration's members into the target namespace.
    """
    try:
        data = enumeration.__members__.items()
    except AtttributeError:
        raise TypeError('%r is not a supported Enum' % enumeration)
    for n, m in data:
        namespace[n] = m

def extend_enum(enumeration, name, *args):
    """
    Add a new member to an existing Enum.
    """
    try:
        _member_map_ = enumeration._member_map_
        _member_names_ = enumeration._member_names_
        _member_type_ = enumeration._member_type_
        _value2member_map_ = enumeration._value2member_map_
    except AttributeError:
        raise TypeError('%r is not a supported Enum' % enumeration)
    _new = getattr(enumeration, '__new_member__', object.__new__)
    if _new is object.__new__:
        use_args = False
    else:
        use_args = True
    if len(args) == 1:
        [value] = args
    else:
        value = args
    if _member_type_ is tuple:
        args = (args, )
    if not use_args:
        new_member = _new(enumeration)
        if not hasattr(new_member, '_value_'):
            new_member._value_ = value
    else:
        new_member = _new(enumeration, *args)
        if not hasattr(new_member, '_value_'):
            new_member._value_ = _member_type_(*args)
    value = new_member._value_
    new_member._name_ = name
    new_member.__objclass__ = enumeration.__class__
    new_member.__init__(*args)
    for canonical_member in _member_map_.values():
        if canonical_member._value_ == new_member._value_:
            new_member = canonical_member
            break
    else:
        _member_names_.append(name)
    _member_map_[name] = new_member
    try:
        _value2member_map_[value] = new_member
    except TypeError:
        pass

def unique(enumeration):
    """
    Class decorator that ensures only unique members exist in an enumeration.
    """
    duplicates = []
    for name, member in enumeration.__members__.items():
        if name != member.name:
            duplicates.append((name, member.name))
    if duplicates:
        duplicate_names = ', '.join(
                ["%s -> %s" % (alias, name) for (alias, name) in duplicates]
                )
        raise ValueError('duplicate names found in %r: %s' %
                (enumeration, duplicate_names)
                )
    return enumeration

# now for a NamedTuple

class _NamedTupleDict(OrderedDict):
    """Track field order and ensure field names are not reused.

    NamedTupleMeta will use the names found in self._field_names to translate
    to indices.
    """
    def __init__(self, *args, **kwds):
        self._field_names = []
        super(_NamedTupleDict, self).__init__(*args, **kwds)

    def __setitem__(self, key, value):
        """Records anything not dundered or not a descriptor.

        If a field name is used twice, an error is raised.

        Single underscore (sunder) names are reserved.

        Note:   in 3.x __order__ is simply discarded as a not necessary piece
                leftover from 2.x
        """
        if pyver >= 3.0 and key == '__order__':
                return
        if _is_sunder(key):
            if key != '_size_':
                raise ValueError('_names_ are reserved for future NamedTuple use')
        elif _is_dunder(key):
            pass
        elif key in self._field_names:
            # overwriting a field?
            raise TypeError('Attempted to reuse field name: %r' % key)
        elif not _is_descriptor(value):
            if key in self:
                # field overwriting a descriptor?
                raise TypeError('%s already defined as: %r' % (key, self[key]))
            self._field_names.append(key)
        super(_NamedTupleDict, self).__setitem__(key, value)


class _TupleAttributeAtIndex(object):

    def __init__(self, name, index, doc, default):
        self.name = name
        self.index = index
        if doc is undefined:
            doc = None
        self.__doc__ = doc
        self.default = default

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if len(instance) <= self.index:
            raise AttributeError('%s instance has no value for %s' % (instance.__class__.__name__, self.name))
        return instance[self.index]

    def __repr__(self):
        return '%s(%d)' % (self.__class__.__name__, self.index)


class undefined(object):
    def __repr__(self):
        return 'undefined'
    def __bool__(self):
        return False
    __nonzero__ = __bool__
undefined = undefined()


class TupleSize(Enum):
    fixed = 'tuple length is static'
    minimum = 'tuple must be at least x long (x is calculated during creation'
    variable = 'tuple length can be anything'

class NamedTupleMeta(type):
    """Metaclass for NamedTuple"""

    @classmethod
    def __prepare__(metacls, cls, bases, size=undefined):
        return _NamedTupleDict()

    def __init__(cls, *args , **kwds):
        super(NamedTupleMeta, cls).__init__(*args)

    def __new__(metacls, cls, bases, clsdict, size=undefined):
        if bases == (object, ):
            bases = (tuple, object)
        elif tuple not in bases:
            if object in bases:
                index = bases.index(object)
                bases = bases[:index] + (tuple, ) + bases[index:]
            else:
                bases = bases + (tuple, )
        # include any fields from base classes
        base_dict = _NamedTupleDict()
        namedtuple_bases = []
        for base in bases:
            if isinstance(base, NamedTupleMeta):
                namedtuple_bases.append(base)
        i = 0
        if namedtuple_bases:
            for name, index, doc, default in metacls._convert_fields(*namedtuple_bases):
                base_dict[name] = index, doc, default
                i = max(i, index)
        # construct properly ordered dict with normalized indexes
        for k, v in clsdict.items():
            base_dict[k] = v
        original_dict = base_dict
        if size is not undefined and '_size_' in original_dict:
            raise TypeError('_size_ cannot be set if "size" is passed in header')
        add_order = isinstance(clsdict, _NamedTupleDict)
        clsdict = _NamedTupleDict()
        clsdict.setdefault('_size_', size or TupleSize.fixed)
        unnumbered = OrderedDict()
        numbered = OrderedDict()
        __order__ = original_dict.pop('__order__', [])
        if __order__ :
            __order__ = __order__.replace(',',' ').split()
            add_order = False
        # and process this class
        for k, v in original_dict.items():
            if k not in original_dict._field_names:
                clsdict[k] = v
            else:
                # TODO:normalize v here
                if isinstance(v, baseinteger):
                    # assume an offset
                    v = v, undefined, undefined
                    i = v[0] + 1
                    target = numbered
                elif isinstance(v, basestring):
                    # assume a docstring
                    if add_order:
                        v = i, v, undefined
                        i += 1
                        target = numbered
                    else:
                        v = undefined, v, undefined
                        target = unnumbered
                elif isinstance(v, tuple) and len(v) in (2, 3) and isinstance(v[0], baseinteger) and isinstance(v[1], (basestring, NoneType)):
                    # assume an offset, a docstring, and (maybe) a default
                    if len(v) == 2:
                        v = v + (undefined, )
                    v = v
                    i = v[0] + 1
                    target = numbered
                elif isinstance(v, tuple) and len(v) in (1, 2) and isinstance(v[0], (basestring, NoneType)):
                    # assume a docstring, and (maybe) a default
                    if len(v) == 1:
                        v = v + (undefined, )
                    if add_order:
                        v = (i, ) + v
                        i += 1
                        target = numbered
                    else:
                        v = (undefined, ) + v
                        target = unnumbered
                else:
                    # refuse to guess further
                    raise ValueError('not sure what to do with %s=%r (should be OFFSET [, DOC [, DEFAULT]])' % (k, v))
                target[k] = v
        # all index values have been normalized
        # deal with __order__ (or lack thereof)
        fields = []
        aliases = []
        seen = set()
        max_len = 0
        if not __order__:
            if unnumbered:
                raise ValueError("__order__ not specified and OFFSETs not declared for %r" % unnumbered.keys())
            for name, (index, doc, default) in sorted(numbered.items(), key=lambda nv: (nv[1][0], nv[0])):
                if index in seen:
                    aliases.append(name)
                else:
                    fields.append(name)
                    seen.add(index)
                    max_len = max(max_len, index + 1)
            offsets = numbered
        else:
            # check if any unnumbered not in __order__
            missing = set(unnumbered) - set(__order__)
            if missing:
                raise ValueError("unable to order fields: %s (use __order__ or specify OFFSET" % missing)
            offsets = OrderedDict()
            # if any unnumbered, number them from their position in __order__
            i = 0
            for k in __order__:
                try:
                    index, doc, default = unnumbered.pop(k, None) or numbered.pop(k)
                except IndexError:
                    raise ValueError('%s (from __order__) not found in %s' % (k, cls))
                if index is not undefined:
                    i = index
                if i in seen:
                    aliases.append(k)
                else:
                    fields.append(k)
                    seen.add(i)
                offsets[k] = i, doc, default
                i += 1
                max_len = max(max_len, i)
            # now handle anything in numbered
            for k, (index, doc, default) in sorted(numbered.items(), key=lambda nv: (nv[1][0], nv[0])):
                if index in seen:
                    aliases.append(k)
                else:
                    fields.append(k)
                    seen.add(index)
                offsets[k] = index, doc, default
                max_len = max(max_len, index+1)

        # at this point fields and aliases should be ordered lists, offsets should be an
        # OrdededDict with each value an int, str or None or undefined, default or None or undefined
        assert len(fields) + len(aliases) == len(offsets), "number of fields + aliases != number of offsets"
        assert set(fields) & set(offsets) == set(fields), "some fields are not in offsets: %s" % set(fields) & set(offsets)
        assert set(aliases) & set(offsets) == set(aliases), "some aliases are not in offsets: %s" % set(aliases) & set(offsets)
        for name, (index, doc, default) in offsets.items():
            assert isinstance(index, baseinteger), "index for %s is not an int (%s:%r)" % (name, type(index), index)
            assert isinstance(doc, (basestring, NoneType)) or doc is undefined, "doc is not a str, None, nor undefined (%s:%r)" % (name, type(doc), doc)

        # create descriptors for fields
        for name, (index, doc, default) in offsets.items():
            clsdict[name] = _TupleAttributeAtIndex(name, index, doc, default)
        clsdict['__slots__'] = ()

        # create our new NamedTuple type
        namedtuple_class = super(NamedTupleMeta, metacls).__new__(metacls, cls, bases, clsdict)
        namedtuple_class._fields_ = fields
        namedtuple_class._aliases_ = aliases
        namedtuple_class._defined_len_ = max_len
        return namedtuple_class

    @staticmethod
    def _convert_fields(*namedtuples):
        "create list of index, doc, default triplets for cls in namedtuples"
        all_fields = []
        for cls in namedtuples:
            base = len(all_fields)
            for field in cls._fields_:
                desc = getattr(cls, field)
                all_fields.append((field, base+desc.index, desc.__doc__, desc.default))
        return all_fields

    def __add__(cls, other):
        "A new NamedTuple is created by concatenating the _fields_ and adjusting the descriptors"
        if not isinstance(other, NamedTupleMeta):
            return NotImplemented
        # new_fields = cls._convert_fields(*(cls, other))
        return NamedTupleMeta('%s%s' % (cls.__name__, other.__name__), (cls, other), {})

    def __call__(cls, *args, **kwds):
        """Creates a new NamedTuple class or an instance of a NamedTuple subclass.

        NamedTuple should have args of (class_name, names, module)

            `names` can be:

                * A string containing member names, separated either with spaces or
                  commas.  Values are auto-numbered from 1.
                * An iterable of member names.  Values are auto-numbered from 1.
                * An iterable of (member name, value) pairs.
                * A mapping of member name -> value.

                `module`, if set, will be stored in the new class' __module__ attribute;

                Note: if `module` is not set this routine will attempt to discover the
                calling module by walking the frame stack; if this is unsuccessful
                the resulting class will not be pickleable.

        subclass should have whatever arguments and/or keywords will be used to create an
        instance of the subclass
        """
        if cls is NamedTuple:
            original_args = args
            original_kwds = kwds.copy()
            # create a new subclass
            try:
                if 'class_name' in kwds:
                    class_name = kwds.pop('class_name')
                else:
                    class_name, args = args[0], args[1:]
                if 'names' in kwds:
                    names = kwds.pop('names')
                else:
                    names, args = args[0], args[1:]
                if 'module' in kwds:
                    module = kwds.pop('module')
                elif args:
                    module, args = args[0], args[1:]
                else:
                    module = None
                if 'type' in kwds:
                    type = kwds.pop('type')
                elif args:
                    type, args = args[0], args[1:]
                else:
                    type = None

            except IndexError:
                raise TypeError('too few arguments to NamedTuple: %s, %s' % (original_args, original_kwds))
            if args or kwds:
                raise TypeError('too many arguments to NamedTuple: %s, %s' % (original_args, original_kwds))
            if pyver < 3.0:
                # if class_name is unicode, attempt a conversion to ASCII
                if isinstance(class_name, unicode):
                    try:
                        class_name = class_name.encode('ascii')
                    except UnicodeEncodeError:
                        raise TypeError('%r is not representable in ASCII' % class_name)
            # quick exit if names is a NamedTuple
            if isinstance(names, NamedTupleMeta):
                names.__name__ = class_name
                if type is not None and type not in names.__bases__:
                    names.__bases__ = (type, ) + bases
                return names

            metacls = cls.__class__
            bases = (cls, )
            clsdict = metacls.__prepare__(class_name, bases)

            # special processing needed for names?
            if isinstance(names, basestring):
                names = names.replace(',', ' ').split()
            if isinstance(names, (tuple, list)) and isinstance(names[0], basestring):
                names = [(e, i) for (i, e) in enumerate(names)]
            # Here, names is either an iterable of (name, index) or (name, index, doc, default) or a mapping.
            item = None  # in case names is empty
            for item in names:
                if isinstance(item, basestring):
                    # mapping
                    field_name, field_index = item, names[item]
                else:
                    # non-mapping
                    if len(item) == 2:
                        field_name, field_index = item
                    else:
                        field_name, field_index = item[0], item[1:]
                clsdict[field_name] = field_index
            if type is not None:
                if not isinstance(type, tuple):
                    type = (type, )
                bases = type + bases
            namedtuple_class = metacls.__new__(metacls, class_name, bases, clsdict)

            # TODO: replace the frame hack if a blessed way to know the calling
            # module is ever developed
            if module is None:
                try:
                    module = _sys._getframe(2).f_globals['__name__']
                except (AttributeError, KeyError):
                    pass
            if module is None:
                _make_class_unpicklable(namedtuple_class)
            else:
                namedtuple_class.__module__ = module

            return namedtuple_class
        else:
            # instantiate a subclass
            namedtuple_instance = cls.__new__(cls, *args, **kwds)
            if isinstance(namedtuple_instance, cls):
                namedtuple_instance.__init__(*args, **kwds)
            return namedtuple_instance

    @property
    def __fields__(cls):
        return list(cls._fields_)
    # collections.namedtuple compatibility
    _fields = __fields__

    @property
    def __aliases__(cls):
        return list(cls._aliases_)

    def __repr__(cls):
        return "<NamedTuple %r>" % cls.__name__

temp_namedtuple_dict = {}
temp_namedtuple_dict['__doc__'] = "NamedTuple base class.\n\n    Derive from this class to define new NamedTuples.\n\n"

def __new__(cls, *args, **kwds):
    if cls._size_ is TupleSize.fixed and len(args) > cls._defined_len_:
        raise TypeError('%d fields expected, %d received' % (cls._defined_len_, len(args)))
    unknown = set(kwds) - set(cls._fields_) - set(cls._aliases_)
    if unknown:
        raise TypeError('unknown fields: %r' % unknown)
    final_args = list(args) + [undefined] * (len(cls.__fields__) - len(args))
    for field, value in kwds.items():
        index = getattr(cls, field).index
        if final_args[index] != undefined:
            raise TypeError('field %s specified more than once' % field)
        final_args[index] = value
    missing = []
    for index, value in enumerate(final_args):
        if value is undefined:
            # look for default values
            name = cls.__fields__[index]
            default = getattr(cls, name).default
            if default is undefined:
                missing.append(name)
            else:
                final_args[index] = default
    if missing:
        if cls._size_ in (TupleSize.fixed, TupleSize.minimum):
            raise TypeError('values not provided for field(s): %s' % ', '.join(missing))
        while final_args and final_args[-1] is undefined:
            final_args.pop()
            missing.pop()
        if cls._size_ is not TupleSize.variable or undefined in final_args:
            raise TypeError('values not provided for field(s): %s' % ', '.join(missing))
    return tuple.__new__(cls, tuple(final_args))

temp_namedtuple_dict['__new__'] = __new__
del __new__

def __reduce_ex__(self, proto):
    return self.__class__, tuple(getattr(self, f) for f in self._fields_)
temp_namedtuple_dict['__reduce_ex__'] = __reduce_ex__
del __reduce_ex__

def __repr__(self):
    if len(self) == len(self._fields_):
        return "%s(%s)" % (
                self.__class__.__name__, ', '.join(['%s=%r' % (f, o) for f, o in zip(self._fields_, self)])
                )
    else:
        return '%s(%s)' % (self.__class__.__name__, ', '.join([repr(o) for o in self]))
temp_namedtuple_dict['__repr__'] = __repr__
del __repr__

def __str__(self):
    return "%s(%s)" % (
            self.__class__.__name__, ', '.join(['%r' % (getattr(self, f)) for f in self._fields_])
            )
temp_namedtuple_dict['__str__'] = __str__
del __str__

# compatibility methods with stdlib namedtuple
@property
def __aliases__(self):
    return list(self.__class__._aliases_)
temp_namedtuple_dict['__aliases__'] = __aliases__
del __aliases__

@property
def __fields__(self):
    return list(self.__class__._fields_)
temp_namedtuple_dict['__fields__'] = __fields__
temp_namedtuple_dict['_fields'] = __fields__
del __fields__

def _make(cls, iterable, new=None, len=None):
    return cls.__new__(cls, *iterable)
temp_namedtuple_dict['_make'] = classmethod(_make)
del _make

def _asdict(self):
    return OrderedDict(zip(self._fields_, self))
temp_namedtuple_dict['_asdict'] = _asdict
del _asdict

def _replace(self, **kwds):
    current = self._asdict()
    current.update(kwds)
    return self.__class__(**current)
temp_namedtuple_dict['_replace'] = _replace
del _replace

NamedTuple = NamedTupleMeta('NamedTuple', (object, ), temp_namedtuple_dict)
del temp_namedtuple_dict


class module(object):

    def __init__(self, cls, *args):
        self.__name__ = cls.__name__
        self._parent_module = cls.__module__
        self.__all__ = []
        all_objects = cls.__dict__
        if not args:
            args = [k for k, v in all_objects.items() if isinstance(v, (Constant, Enum))]
        for name in args:
            self.__dict__[name] = all_objects[name]
            self.__all__.append(name)

    def register(self):
        _sys.modules["%s.%s" % (self._parent_module, self.__name__)] = self

