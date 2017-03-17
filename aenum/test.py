from __future__ import division
import sys
pyver = float('%s.%s' % sys.version_info[:2])
import aenum
import doctest
import unittest
from aenum import EnumMeta, Enum, IntEnum, AutoNumberEnum, OrderedEnum, UniqueEnum, Flag, IntFlag
from aenum import NamedTuple, TupleSize, NamedConstant, constant, NoAlias, AutoNumber, Unique
from aenum import _reduce_ex_by_name, unique, skip, extend_enum, auto, enum
from collections import OrderedDict
from datetime import timedelta
from pickle import dumps, loads, PicklingError, HIGHEST_PROTOCOL
from operator import or_ as _or_, and_ as _and_, xor as _xor_, inv as _inv_
from operator import abs as _abs_, add as _add_, floordiv as _floordiv_
from operator import lshift as _lshift_, rshift as _rshift_, mod as _mod_
from operator import mul as _mul_, neg as _neg_, pos as _pos_, pow as _pow_
from operator import truediv as _truediv_, sub as _sub_
if pyver < 3:
    from operator import div as _div_
try:
    import threading
except ImportError:
    threading = None

try:
    basestring
except NameError:
    # In Python 2 basestring is the ancestor of both str and unicode
    # in Python 3 it's just str, but was missing in 3.1
    basestring = str

try:
    any
except NameError:
    def any(iterable):
        for element in iterable:
            if element:
                return True
        return False

try:
    unicode
except NameError:
    unicode = str

try:
    from enum import EnumMeta as StdlibEnumMeta, Enum as StdlibEnum
    import enum as enum_module
    if hasattr(enum_module, 'version'):
        StdlibEnumMeta = StdlibEnum = None
    del enum_module
except ImportError:
    StdlibEnumMeta = StdlibEnum = None

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(aenum))
    tests.addTests(doctest.DocFileSuite(
        'doc/aenum.rst',
        package=aenum,
        optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE,
        ))
    return tests

class TestCase(unittest.TestCase):
    def __init__(self, *args, **kwds):
        regex = getattr(self, 'assertRaisesRegex', None)
        if regex is None:
            self.assertRaisesRegex = getattr(self, 'assertRaisesRegexp')
        super(TestCase, self).__init__(*args, **kwds)

# for pickle tests
try:
    class Stooges(Enum):
        LARRY = 1
        CURLY = 2
        MOE = 3
except Exception:
    Stooges = sys.exc_info()[1]

try:
    class IntStooges(int, Enum):
        LARRY = 1
        CURLY = 2
        MOE = 3
except Exception:
    IntStooges = sys.exc_info()[1]

try:
    class FloatStooges(float, Enum):
        LARRY = 1.39
        CURLY = 2.72
        MOE = 3.142596
except Exception:
    FloatStooges = sys.exc_info()[1]

try:
    class FlagStooges(Flag):
        LARRY = 1
        CURLY = 2
        MOE = 3
except Exception as exc:
    FlagStooges = exc

try:
    LifeForm = NamedTuple('LifeForm', 'branch genus species', module=__name__)
except Exception:
    LifeForm = sys.exc_info()[1]

try:
    class DeathForm(NamedTuple):
        color = 0
        rigidity = 1
        odor = 2
except Exception:
    DeathForm = sys.exc_info()[1]

# for pickle test and subclass tests
try:
    class StrEnum(str, Enum):
        'accepts only string values'
    class Name(StrEnum):
        BDFL = 'Guido van Rossum'
        FLUFL = 'Barry Warsaw'
except Exception:
    Name = sys.exc_info()[1]

try:
    Question = Enum('Question', 'who what when where why', module=__name__)
except Exception:
    Question = sys.exc_info()[1]

try:
    Answer = Enum('Answer', 'him this then there because')
except Exception:
    Answer = sys.exc_info()[1]

try:
    Theory = Enum('Theory', 'rule law supposition', qualname='spanish_inquisition')
except Exception:
    Theory = sys.exc_info()[1]

try:
    class WhatsIt(NamedTuple):
        def what(self):
            return self[0]
    class ThatsIt(WhatsIt):
        blah = 0
        bleh = 1
except Exception:
    ThatsIt = sys.exc_info()[1]

# for doctests
try:
    class Fruit(Enum):
        tomato = 1
        banana = 2
        cherry = 3
except Exception:
    pass

def test_pickle_dump_load(assertion, source, target=None, protocol=(0, HIGHEST_PROTOCOL)):
    start, stop = protocol
    failures = []
    for protocol in range(start, stop+1):
        try:
            if target is None:
                # if isinstance(source, Enum):
                #     print('tpdl 1')
                #     assertion(loads(dumps(source, protocol=protocol)) is source)
                # else:
                    # print('tpdl 2')
                    assertion(loads(dumps(source, protocol=protocol)), source)
            else:
                # print('tpdl 3')
                assertion(loads(dumps(source, protocol=protocol)), target)
        except Exception:
            exc, tb = sys.exc_info()[1:]
            failures.append('%2d: %s' %(protocol, exc))
    if failures:
        raise ValueError('Failed with protocols: %s' % ', '.join(failures))

def test_pickle_exception(assertion, exception, obj,
        protocol=(0, HIGHEST_PROTOCOL)):
    start, stop = protocol
    failures = []
    for protocol in range(start, stop+1):
        try:
            assertion(exception, dumps, obj, protocol=protocol)
        except Exception:
            exc = sys.exc_info()[1]
            failures.append('%d: %s %s' % (protocol, exc.__class__.__name__, exc))
    if failures:
        raise ValueError('Failed with protocols: %s' % ', '.join(failures))

if pyver >= 3.0:
    from aenum.test_v3 import TestEnumV3, TestOrderV3, TestNamedTupleV3
    from aenum import test_v3
    test_v3.pyver = pyver
    test_v3.IntStooges = IntStooges
    test_v3.test_pickle_exception = test_pickle_exception
    test_v3.test_pickle_dump_load = test_pickle_dump_load

# tests
class TestHelpers(TestCase):
    # _is_descriptor, _is_sunder, _is_dunder

    def test_is_descriptor(self):
        class foo:
            pass
        for attr in ('__get__','__set__','__delete__'):
            obj = foo()
            self.assertFalse(aenum._is_descriptor(obj))
            setattr(obj, attr, 1)
            self.assertTrue(aenum._is_descriptor(obj))

    def test_is_sunder(self):
        for s in ('_a_', '_aa_'):
            self.assertTrue(aenum._is_sunder(s))

        for s in ('a', 'a_', '_a', '__a', 'a__', '__a__', '_a__', '__a_', '_',
                '__', '___', '____', '_____',):
            self.assertFalse(aenum._is_sunder(s))

    def test_is_dunder(self):
        for s in ('__a__', '__aa__'):
            self.assertTrue(aenum._is_dunder(s))
        for s in ('a', 'a_', '_a', '__a', 'a__', '_a_', '_a__', '__a_', '_',
                '__', '___', '____', '_____',):
            self.assertFalse(aenum._is_dunder(s))

    def test_auto(self):
        def tester(first, op, final, second=None):
            if second is None:
                left = auto()
                value = op(left)
                left.value = first
                self.assertEqual(value.value, final,
                        "%s %r -> %r != %r" % (op.__name__, first, value, final))
            else:
                left = first
                right = auto()
                value = op(left, right)
                right.value = second
                self.assertEqual(value.value, final,
                        "forward: %r %s %r -> %r != %r" % (first, op.__name__, second, value.value, final))
                left = auto()
                right = second
                value = op(left, right)
                left.value = first
                self.assertEqual(value.value, final,
                        "reversed: %r %s %r -> %r != %r" % (second, op.__name__, first, value.value, final))
        for args in (
                (1, _abs_, abs(1)),
                (-3, _abs_, abs(-3)),
                (1, _add_, 1+2, 2),
                (25, _floordiv_, 25 // 5, 5),
                (49, _truediv_, 49 / 9, 9),
                (6, _mod_, 6 % 9, 9),
                (5, _lshift_, 5 << 2, 2),
                (5, _rshift_, 5 >> 2, 2),
                (3, _mul_, 3 * 6, 6),
                (5, _neg_, -5),
                (-4, _pos_, +(-4)),
                (2, _pow_, 2**5, 5),
                (7, _sub_, 7 - 10, 10),
                (1, _or_, 1 | 2, 2),
                (3, _xor_, 3 ^ 6, 6),
                (3, _and_, 3 & 6, 6),
                (7, _inv_, ~7),
                ('a', _add_, 'a'+'b', 'b'),
                ('a', _mul_, 'a' * 3, 3),
                ):
            tester(*args)
        # operator.div is gone in 3
        if pyver < 3:
            tester(12, _div_, 12 // 5, 5)
        # strigs are a pain
        left = auto()
        right = 'eggs'
        value = _mod_(left, right)
        left.value = 'I see 17 %s!'
        self.assertEqual(value.value, 'I see 17 %s!' % 'eggs')


class TestEnum(TestCase):

    def setUp(self):
        class Season(Enum):
            SPRING = 1
            SUMMER = 2
            AUTUMN = 3
            WINTER = 4
        self.Season = Season

        class Konstants(float, Enum):
            E = 2.7182818
            PI = 3.1415926
            TAU = 2 * PI
        self.Konstants = Konstants

        class Grades(IntEnum):
            A = 5
            B = 4
            C = 3
            D = 2
            F = 0
        self.Grades = Grades

        class Directional(str, Enum):
            EAST = 'east'
            WEST = 'west'
            NORTH = 'north'
            SOUTH = 'south'
        self.Directional = Directional

        from datetime import date
        class Holiday(date, Enum):
            NEW_YEAR = 2013, 1, 1
            IDES_OF_MARCH = 2013, 3, 15
        self.Holiday = Holiday

    def test_members_is_ordereddict_if_ordered(self):
        class Ordered(Enum):
            __order__ = 'first second third'
            first = 'bippity'
            second = 'boppity'
            third = 'boo'
        self.assertTrue(type(Ordered.__members__) is OrderedDict)

    def test_members_is_ordereddict_if_not_ordered(self):
        class Unordered(Enum):
            this = 'that'
            these = 'those'
        self.assertTrue(type(Unordered.__members__) is OrderedDict)

    def test_enum_in_enum_out(self):
        Season = self.Season
        self.assertTrue(Season(Season.WINTER) is Season.WINTER)

    def test_enum_value(self):
        Season = self.Season
        self.assertEqual(Season.SPRING.value, 1)

    def test_intenum_value(self):
        self.assertEqual(IntStooges.CURLY.value, 2)

    def test_enum(self):
        Season = self.Season
        lst = list(Season)
        self.assertEqual(len(lst), len(Season))
        self.assertEqual(len(Season), 4, Season)
        self.assertEqual(
            [Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER], lst)

        for i, season in enumerate('SPRING SUMMER AUTUMN WINTER'.split()):
            i += 1
            e = Season(i)
            self.assertEqual(e, getattr(Season, season))
            self.assertEqual(e.value, i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, season)
            self.assertTrue(e in Season)
            self.assertTrue(type(e) is Season)
            self.assertTrue(isinstance(e, Season))
            self.assertEqual(str(e), 'Season.' + season)
            self.assertEqual(
                    repr(e),
                    '<Season.%s: %s>' % (season, i),
                    )
    def test_enum_helper(self):
        e1 = enum(1, 2, three=9)
        e2 = enum(1, 2, three=9)
        e3 = enum(1, 2, 9)
        self.assertTrue(e1 is not e2)
        self.assertEqual(e1, e2)
        self.assertNotEqual(e1, e3)
        self.assertNotEqual(e2, e3)

    def test_value_name(self):
        Season = self.Season
        self.assertEqual(Season.SPRING.name, 'SPRING')
        self.assertEqual(Season.SPRING.value, 1)
        def set_name(obj, new_value):
            obj.name = new_value
        def set_value(obj, new_value):
            obj.value = new_value
        self.assertRaises(AttributeError, set_name, Season.SPRING, 'invierno', )
        self.assertRaises(AttributeError, set_value, Season.SPRING, 2)

    def test_attribute_deletion(self):
        class Season(Enum):
            SPRING = 1
            SUMMER = 2
            AUTUMN = 3
            WINTER = 4

            def spam(cls):
                pass

        self.assertTrue(hasattr(Season, 'spam'))
        del Season.spam
        self.assertFalse(hasattr(Season, 'spam'))

        self.assertRaises(AttributeError, delattr, Season, 'SPRING')
        self.assertRaises(AttributeError, delattr, Season, 'DRY')
        self.assertRaises(AttributeError, delattr, Season.SPRING, 'name')

    def test_bool_of_class(self):
        class Empty(Enum):
            pass
        self.assertTrue(bool(Empty))

    def test_bool_of_member(self):
        class Count(Enum):
            zero = 0
            one = 1
            two = 2
        for member in Count:
            self.assertTrue(bool(member))

    def test_invalid_names(self):
        def create_bad_class_1():
            class Wrong(Enum):
                mro = 9
        def create_bad_class_2():
            class Wrong(Enum):
                _reserved_ = 3
        self.assertRaises(ValueError, create_bad_class_1)
        self.assertRaises(ValueError, create_bad_class_2)

    def test_bool(self):
        class Logic(Enum):
            true = True
            false = False
            def __bool__(self):
                return bool(self.value)
            __nonzero__ = __bool__
        self.assertTrue(Logic.true)
        self.assertFalse(Logic.false)

    def test_contains(self):
        Season = self.Season
        self.assertTrue(Season.AUTUMN in Season)
        self.assertTrue(3 not in Season)

        val = Season(3)
        self.assertTrue(val in Season)

        class OtherEnum(Enum):
            one = 1; two = 2
        self.assertTrue(OtherEnum.two not in Season)

    if pyver >= 2.6:     # when `format` came into being

        def test_format_enum(self):
            Season = self.Season
            self.assertEqual('{0}'.format(Season.SPRING),
                             '{0}'.format(str(Season.SPRING)))
            self.assertEqual( '{0:}'.format(Season.SPRING),
                              '{0:}'.format(str(Season.SPRING)))
            self.assertEqual('{0:20}'.format(Season.SPRING),
                             '{0:20}'.format(str(Season.SPRING)))
            self.assertEqual('{0:^20}'.format(Season.SPRING),
                             '{0:^20}'.format(str(Season.SPRING)))
            self.assertEqual('{0:>20}'.format(Season.SPRING),
                             '{0:>20}'.format(str(Season.SPRING)))
            self.assertEqual('{0:<20}'.format(Season.SPRING),
                             '{0:<20}'.format(str(Season.SPRING)))

        def test_format_enum_custom(self):
            class TestFloat(float, Enum):
                one = 1.0
                two = 2.0
                def __format__(self, spec):
                    return 'TestFloat success!'
            self.assertEqual('{0}'.format(TestFloat.one), 'TestFloat success!')

        def assertFormatIsValue(self, spec, member):
            self.assertEqual(spec.format(member), spec.format(member.value))

        def test_format_enum_date(self):
            Holiday = self.Holiday
            self.assertFormatIsValue('{0}', Holiday.IDES_OF_MARCH)
            self.assertFormatIsValue('{0:}', Holiday.IDES_OF_MARCH)
            self.assertFormatIsValue('{0:20}', Holiday.IDES_OF_MARCH)
            self.assertFormatIsValue('{0:^20}', Holiday.IDES_OF_MARCH)
            self.assertFormatIsValue('{0:>20}', Holiday.IDES_OF_MARCH)
            self.assertFormatIsValue('{0:<20}', Holiday.IDES_OF_MARCH)
            self.assertFormatIsValue('{0:%Y %m}', Holiday.IDES_OF_MARCH)
            self.assertFormatIsValue('{0:%Y %m %M:00}', Holiday.IDES_OF_MARCH)

        def test_format_enum_float(self):
            Konstants = self.Konstants
            self.assertFormatIsValue('{0}', Konstants.TAU)
            self.assertFormatIsValue('{0:}', Konstants.TAU)
            self.assertFormatIsValue('{0:20}', Konstants.TAU)
            self.assertFormatIsValue('{0:^20}', Konstants.TAU)
            self.assertFormatIsValue('{0:>20}', Konstants.TAU)
            self.assertFormatIsValue('{0:<20}', Konstants.TAU)
            self.assertFormatIsValue('{0:n}', Konstants.TAU)
            self.assertFormatIsValue('{0:5.2}', Konstants.TAU)
            self.assertFormatIsValue('{0:f}', Konstants.TAU)

        def test_format_enum_int(self):
            Grades = self.Grades
            self.assertFormatIsValue('{0}', Grades.C)
            self.assertFormatIsValue('{0:}', Grades.C)
            self.assertFormatIsValue('{0:20}', Grades.C)
            self.assertFormatIsValue('{0:^20}', Grades.C)
            self.assertFormatIsValue('{0:>20}', Grades.C)
            self.assertFormatIsValue('{0:<20}', Grades.C)
            self.assertFormatIsValue('{0:+}', Grades.C)
            self.assertFormatIsValue('{0:08X}', Grades.C)
            self.assertFormatIsValue('{0:b}', Grades.C)

        def test_format_enum_str(self):
            Directional = self.Directional
            self.assertFormatIsValue('{0}', Directional.WEST)
            self.assertFormatIsValue('{0:}', Directional.WEST)
            self.assertFormatIsValue('{0:20}', Directional.WEST)
            self.assertFormatIsValue('{0:^20}', Directional.WEST)
            self.assertFormatIsValue('{0:>20}', Directional.WEST)
            self.assertFormatIsValue('{0:<20}', Directional.WEST)

    def test_hash(self):
        Season = self.Season
        dates = {}
        dates[Season.WINTER] = '1225'
        dates[Season.SPRING] = '0315'
        dates[Season.SUMMER] = '0704'
        dates[Season.AUTUMN] = '1031'
        self.assertEqual(dates[Season.AUTUMN], '1031')

    def test_enum_duplicates(self):
        class Season(Enum):
            __order__ = "SPRING SUMMER AUTUMN WINTER"
            SPRING = 1
            SUMMER = 2
            AUTUMN = FALL = 3
            WINTER = 4
            ANOTHER_SPRING = 1
        lst = list(Season)
        self.assertEqual(
            lst,
            [Season.SPRING, Season.SUMMER,
             Season.AUTUMN, Season.WINTER,
            ])
        self.assertTrue(Season.FALL is Season.AUTUMN)
        self.assertEqual(Season.FALL.value, 3)
        self.assertEqual(Season.AUTUMN.value, 3)
        self.assertTrue(Season(3) is Season.AUTUMN)
        self.assertTrue(Season(1) is Season.SPRING)
        self.assertEqual(Season.FALL.name, 'AUTUMN')
        self.assertEqual(
                set([k for k,v in Season.__members__.items() if v.name != k]),
                set(['FALL', 'ANOTHER_SPRING']),
                )

    def test_enum_with_value_name(self):
        class Huh(Enum):
            _order_ = 'name value'
            name = 1
            value = 2
        self.assertEqual(
            list(Huh),
            [Huh.name, Huh.value],
            )
        self.assertTrue(type(Huh.name) is Huh)
        self.assertEqual(Huh.name.name, 'name')
        self.assertEqual(Huh.name.value, 1)

    def test_intenum_from_scratch(self):
        class phy(int, Enum):
            pi = 3
            tau = 2 * pi
        self.assertTrue(phy.pi < phy.tau)

    def test_intenum_inherited(self):
        class IntEnum(int, Enum):
            pass
        class phy(IntEnum):
            pi = 3
            tau = 2 * pi
        self.assertTrue(phy.pi < phy.tau)

    def test_floatenum_from_scratch(self):
        class phy(float, Enum):
            pi = 3.1415926
            tau = 2 * pi
        self.assertTrue(phy.pi < phy.tau)

    def test_floatenum_inherited(self):
        class FloatEnum(float, Enum):
            pass
        class phy(FloatEnum):
            pi = 3.1415926
            tau = 2 * pi
        self.assertTrue(phy.pi < phy.tau)

    def test_strenum_from_scratch(self):
        class phy(str, Enum):
            pi = 'Pi'
            tau = 'Tau'
        self.assertTrue(phy.pi < phy.tau)

    def test_strenum_inherited(self):
        class StrEnum(str, Enum):
            pass
        class phy(StrEnum):
            pi = 'Pi'
            tau = 'Tau'
        self.assertTrue(phy.pi < phy.tau)

    def test_intenum(self):
        class WeekDay(IntEnum):
            SUNDAY = 1
            MONDAY = 2
            TUESDAY = 3
            WEDNESDAY = 4
            THURSDAY = 5
            FRIDAY = 6
            SATURDAY = 7

        self.assertEqual(['a', 'b', 'c'][WeekDay.MONDAY], 'c')
        self.assertEqual([i for i in range(WeekDay.TUESDAY)], [0, 1, 2])

        lst = list(WeekDay)
        self.assertEqual(len(lst), len(WeekDay))
        self.assertEqual(len(WeekDay), 7)
        target = 'SUNDAY MONDAY TUESDAY WEDNESDAY THURSDAY FRIDAY SATURDAY'
        target = target.split()
        for i, weekday in enumerate(target):
            i += 1
            e = WeekDay(i)
            self.assertEqual(e, i)
            self.assertEqual(int(e), i)
            self.assertEqual(e.name, weekday)
            self.assertTrue(e in WeekDay)
            self.assertEqual(lst.index(e)+1, i)
            self.assertTrue(0 < e < 8)
            self.assertTrue(type(e) is WeekDay)
            self.assertTrue(isinstance(e, int))
            self.assertTrue(isinstance(e, Enum))

    def test_intenum_duplicates(self):
        class WeekDay(IntEnum):
            __order__ = 'SUNDAY MONDAY TUESDAY WEDNESDAY THURSDAY FRIDAY SATURDAY'
            SUNDAY = 1
            MONDAY = 2
            TUESDAY = TEUSDAY = 3
            WEDNESDAY = 4
            THURSDAY = 5
            FRIDAY = 6
            SATURDAY = 7
        self.assertTrue(WeekDay.TEUSDAY is WeekDay.TUESDAY)
        self.assertEqual(WeekDay(3).name, 'TUESDAY')
        self.assertEqual([k for k,v in WeekDay.__members__.items()
                if v.name != k], ['TEUSDAY', ])

    def test_floatenum_fromhex(self):
        h = float.hex(FloatStooges.MOE.value)
        self.assertIs(FloatStooges.fromhex(h), FloatStooges.MOE)
        h = float.hex(FloatStooges.MOE.value + 0.01)
        with self.assertRaises(ValueError):
            FloatStooges.fromhex(h)

    def test_pickle_enum(self):
        if isinstance(Stooges, Exception):
            raise Stooges
        test_pickle_dump_load(self.assertTrue, Stooges.CURLY)
        test_pickle_dump_load(self.assertTrue, Stooges)

    def test_pickle_int(self):
        if isinstance(IntStooges, Exception):
            raise IntStooges
        test_pickle_dump_load(self.assertTrue, IntStooges.CURLY)
        test_pickle_dump_load(self.assertTrue, IntStooges)

    def test_pickle_float(self):
        if isinstance(FloatStooges, Exception):
            raise FloatStooges
        test_pickle_dump_load(self.assertTrue, FloatStooges.CURLY)
        test_pickle_dump_load(self.assertTrue, FloatStooges)

    def test_pickle_enum_function(self):
        if isinstance(Answer, Exception):
            raise Answer
        test_pickle_dump_load(self.assertTrue, Answer.him)
        test_pickle_dump_load(self.assertTrue, Answer)

    def test_pickle_enum_function_with_module(self):
        if isinstance(Question, Exception):
            raise Question
        test_pickle_dump_load(self.assertTrue, Question.who)
        test_pickle_dump_load(self.assertTrue, Question)

    def test_pickle_by_name(self):
        class ReplaceGlobalInt(IntEnum):
            ONE = 1
            TWO = 2
        ReplaceGlobalInt.__reduce_ex__ = _reduce_ex_by_name
        for proto in range(HIGHEST_PROTOCOL):
            self.assertEqual(ReplaceGlobalInt.TWO.__reduce_ex__(proto), 'TWO')

    def test_exploding_pickle(self):
        BadPickle = Enum('BadPickle', 'dill sweet bread-n-butter')
        aenum._make_class_unpicklable(BadPickle)
        globals()['BadPickle'] = BadPickle
        test_pickle_exception(self.assertRaises, TypeError, BadPickle.dill)
        test_pickle_exception(self.assertRaises, PicklingError, BadPickle)

    def test_string_enum(self):
        class SkillLevel(str, Enum):
            master = 'what is the sound of one hand clapping?'
            journeyman = 'why did the chicken cross the road?'
            apprentice = 'knock, knock!'
        self.assertEqual(SkillLevel.apprentice, 'knock, knock!')

    def test_getattr_getitem(self):
        class Period(Enum):
            morning = 1
            noon = 2
            evening = 3
            night = 4
        self.assertTrue(Period(2) is Period.noon)
        self.assertTrue(getattr(Period, 'night') is Period.night)
        self.assertTrue(Period['morning'] is Period.morning)

    def test_getattr_dunder(self):
        Season = self.Season
        self.assertTrue(getattr(Season, '__hash__'))

    def test_iteration_order(self):
        class Season(Enum):
            __order__ = 'SUMMER WINTER AUTUMN SPRING'
            SUMMER = 2
            WINTER = 4
            AUTUMN = 3
            SPRING = 1
        self.assertEqual(
                list(Season),
                [Season.SUMMER, Season.WINTER, Season.AUTUMN, Season.SPRING],
                )

    def test_iteration_order_reversed(self):
        self.assertEqual(
                list(reversed(self.Season)),
                [self.Season.WINTER, self.Season.AUTUMN, self.Season.SUMMER,
                 self.Season.SPRING]
                )

    def test_iteration_order_with_unorderable_values(self):
        class Complex(Enum):
            a = complex(7, 9)
            b = complex(3.14, 2)
            c = complex(1, -1)
            d = complex(-77, 32)
        self.assertEqual(
                list(Complex),
                [Complex.a, Complex.b, Complex.c, Complex.d],
                )

    def test_programatic_function_string(self):
        SummerMonth = Enum('SummerMonth', 'june july august')
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate('june july august'.split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_string_with_start(self):
        SummerMonth = Enum('SummerMonth', 'june july august', start=10)
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate('june july august'.split(), 10):
            e = SummerMonth(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_string_list(self):
        SummerMonth = Enum('SummerMonth', ['june', 'july', 'august'])
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate('june july august'.split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_string_list_with_start(self):
        SummerMonth = Enum('SummerMonth', ['june', 'july', 'august'], start=20)
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate('june july august'.split(), 20):
            e = SummerMonth(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_iterable(self):
        SummerMonth = Enum(
                'SummerMonth',
                (('june', 1), ('july', 2), ('august', 3))
                )
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate('june july august'.split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_from_dict(self):
        SummerMonth = Enum(
                'SummerMonth',
                dict((('june', 1), ('july', 2), ('august', 3)))
                )
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        if pyver < 3.0:
            self.assertEqual(
                    [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                    lst,
                    )
        for i, month in enumerate('june july august'.split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_type(self):
        SummerMonth = Enum('SummerMonth', 'june july august', type=int)
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate('june july august'.split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_type_with_start(self):
        SummerMonth = Enum('SummerMonth', 'june july august', type=int, start=30)
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate('june july august'.split(), 30):
            e = SummerMonth(i)
            self.assertEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_type_from_subclass(self):
        SummerMonth = IntEnum('SummerMonth', 'june july august')
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate('june july august'.split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_type_from_subclass_with_start(self):
        SummerMonth = IntEnum('SummerMonth', 'june july august', start=40)
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate('june july august'.split(), 40):
            e = SummerMonth(i)
            self.assertEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_unicode(self):
        SummerMonth = Enum('SummerMonth', unicode('june july august'))
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate(unicode('june july august').split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_unicode_list(self):
        SummerMonth = Enum('SummerMonth', [unicode('june'), unicode('july'), unicode('august')])
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate(unicode('june july august').split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_unicode_iterable(self):
        SummerMonth = Enum(
                'SummerMonth',
                ((unicode('june'), 1), (unicode('july'), 2), (unicode('august'), 3))
                )
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate(unicode('june july august').split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_from_unicode_dict(self):
        SummerMonth = Enum(
                'SummerMonth',
                dict(((unicode('june'), 1), (unicode('july'), 2), (unicode('august'), 3)))
                )
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        if pyver < 3.0:
            self.assertEqual(
                    [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                    lst,
                    )
        for i, month in enumerate(unicode('june july august').split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(int(e.value), i)
            self.assertNotEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_unicode_type(self):
        SummerMonth = Enum('SummerMonth', unicode('june july august'), type=int)
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate(unicode('june july august').split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programatic_function_unicode_type_from_subclass(self):
        SummerMonth = IntEnum('SummerMonth', unicode('june july august'))
        lst = list(SummerMonth)
        self.assertEqual(len(lst), len(SummerMonth))
        self.assertEqual(len(SummerMonth), 3, SummerMonth)
        self.assertEqual(
                [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                lst,
                )
        for i, month in enumerate(unicode('june july august').split()):
            i += 1
            e = SummerMonth(i)
            self.assertEqual(e, i)
            self.assertEqual(e.name, month)
            self.assertTrue(e in SummerMonth)
            self.assertTrue(type(e) is SummerMonth)

    def test_programmatic_function_unicode_class(self):
        if pyver < 3.0:
            class_names = unicode('SummerMonth'), 'S\xfcmm\xe9rM\xf6nth'.decode('latin1')
        else:
            class_names = 'SummerMonth', 'S\xfcmm\xe9rM\xf6nth'
        for i, class_name in enumerate(class_names):
            if pyver < 3.0 and i == 1:
                self.assertRaises(TypeError, Enum, class_name, unicode('june july august'))
            else:
                SummerMonth = Enum(class_name, unicode('june july august'))
                lst = list(SummerMonth)
                self.assertEqual(len(lst), len(SummerMonth))
                self.assertEqual(len(SummerMonth), 3, SummerMonth)
                self.assertEqual(
                        [SummerMonth.june, SummerMonth.july, SummerMonth.august],
                        lst,
                        )
                for i, month in enumerate(unicode('june july august').split()):
                    i += 1
                    e = SummerMonth(i)
                    self.assertEqual(e.value, i)
                    self.assertEqual(e.name, month)
                    self.assertTrue(e in SummerMonth)
                    self.assertTrue(type(e) is SummerMonth)

    def test_subclassing(self):
        if isinstance(Name, Exception):
            raise Name
        self.assertEqual(Name.BDFL, 'Guido van Rossum')
        self.assertTrue(Name.BDFL, Name('Guido van Rossum'))
        self.assertTrue(Name.BDFL is getattr(Name, 'BDFL'))
        test_pickle_dump_load(self.assertTrue, Name.BDFL)

    def test_extending(self):
        def bad_extension():
            class Color(Enum):
                red = 1
                green = 2
                blue = 3
            class MoreColor(Color):
                cyan = 4
                magenta = 5
                yellow = 6
        self.assertRaises(TypeError, bad_extension)

    def test_exclude_methods(self):
        class whatever(Enum):
            this = 'that'
            these = 'those'
            def really(self):
                return 'no, not %s' % self.value
        self.assertFalse(type(whatever.really) is whatever)
        self.assertEqual(whatever.this.really(), 'no, not that')

    def test_wrong_inheritance_order(self):
        def wrong_inherit():
            class Wrong(Enum, str):
                NotHere = 'error before this point'
        self.assertRaises(TypeError, wrong_inherit)

    def test_intenum_transitivity(self):
        class number(IntEnum):
            one = 1
            two = 2
            three = 3
        class numero(IntEnum):
            uno = 1
            dos = 2
            tres = 3
        self.assertEqual(number.one, numero.uno)
        self.assertEqual(number.two, numero.dos)
        self.assertEqual(number.three, numero.tres)

    def test_introspection(self):
        class Number(IntEnum):
            one = 100
            two = 200
        self.assertTrue(Number.one._member_type_ is int)
        self.assertTrue(Number._member_type_ is int)
        class String(str, Enum):
            yarn = 'soft'
            rope = 'rough'
            wire = 'hard'
        self.assertTrue(String.yarn._member_type_ is str)
        self.assertTrue(String._member_type_ is str)
        class Plain(Enum):
            vanilla = 'white'
            one = 1
        self.assertTrue(Plain.vanilla._member_type_ is object)
        self.assertTrue(Plain._member_type_ is object)

    def test_wrong_enum_in_call(self):
        class Monochrome(Enum):
            black = 0
            white = 1
        class Gender(Enum):
            male = 0
            female = 1
        self.assertRaises(ValueError, Monochrome, Gender.male)

    def test_wrong_enum_in_mixed_call(self):
        class Monochrome(IntEnum):
            black = 0
            white = 1
        class Gender(Enum):
            male = 0
            female = 1
        self.assertRaises(ValueError, Monochrome, Gender.male)

    def test_mixed_enum_in_call_1(self):
        class Monochrome(IntEnum):
            black = 0
            white = 1
        class Gender(IntEnum):
            male = 0
            female = 1
        self.assertTrue(Monochrome(Gender.female) is Monochrome.white)

    def test_mixed_enum_in_call_2(self):
        class Monochrome(Enum):
            black = 0
            white = 1
        class Gender(IntEnum):
            male = 0
            female = 1
        self.assertTrue(Monochrome(Gender.male) is Monochrome.black)

    def test_flufl_enum(self):
        class Fluflnum(Enum):
            def __int__(self):
                return int(self.value)
        class MailManOptions(Fluflnum):
            option1 = 1
            option2 = 2
            option3 = 3
        self.assertEqual(int(MailManOptions.option1), 1)

    def test_no_such_enum_member(self):
        class Color(Enum):
            red = 1
            green = 2
            blue = 3
        self.assertRaises(ValueError, Color, 4)
        self.assertRaises(KeyError, Color.__getitem__, 'chartreuse')

    def test_new_repr(self):
        class Color(Enum):
            red = 1
            green = 2
            blue = 3
            def __repr__(self):
                return "don't you just love shades of %s?" % self.name
        self.assertEqual(
                repr(Color.blue),
                "don't you just love shades of blue?",
                )

    def test_inherited_repr(self):
        class MyEnum(Enum):
            def __repr__(self):
                return "My name is %s." % self.name
        class MyIntEnum(int, MyEnum):
            this = 1
            that = 2
            theother = 3
        self.assertEqual(repr(MyIntEnum.that), "My name is that.")

    def test_multiple_mixin_mro(self):
        class auto_enum(EnumMeta):
            def __new__(metacls, cls, bases, classdict):
                original_dict = classdict
                temp_dict = metacls.__prepare__(cls, bases, {})
                if hasattr(original_dict, '_member_names'):
                    for k in original_dict._member_names:
                        temp_dict[k] = original_dict[k]
                    sunders = [k for k in original_dict.keys() if aenum._is_sunder(k)]
                else:
                    sunders = []
                    for k, v in original_dict.items():
                        if aenum._is_sunder(k):
                            sunders.append(k)
                        temp_dict[k] = v
                classdict = metacls.__prepare__(cls, bases, {})
                i = 0
                for k in sunders:
                    classdict[k] = original_dict[k]
                for k in temp_dict._member_names:
                    v = original_dict[k]
                    if v == ():
                        v = i
                    else:
                        i = v
                    i += 1
                    classdict[k] = v
                for k, v in original_dict.items():
                    if k not in temp_dict._member_names and k not in sunders:
                        classdict[k] = v
                return super(auto_enum, metacls).__new__(
                        metacls, cls, bases, classdict)

        AutoNumberedEnum = auto_enum('AutoNumberedEnum', (Enum,), {})

        AutoIntEnum = auto_enum('AutoIntEnum', (IntEnum,), {})

        class TestAutoNumber(AutoNumberedEnum):
            a = ()
            b = 3
            c = ()
        self.assertEqual(TestAutoNumber.b.value, 3)

        if pyver >= 3.0:
            self.assertEqual(
                [TestAutoNumber.a.value, TestAutoNumber.b.value, TestAutoNumber.c.value],
                [0, 3, 4],
                )

        class TestAutoInt(AutoIntEnum):
            a = ()
            b = 3
            c = ()
        self.assertEqual(TestAutoInt.b, 3)

        if pyver >= 3.0:
            self.assertEqual(
                [TestAutoInt.a.value, TestAutoInt.b.value, TestAutoInt.c.value],
                [0, 3, 4],
                )

    def test_subclasses_with_getnewargs(self):
        class NamedInt(int):
            __qualname__ = 'NamedInt'  # needed for pickle protocol 4
            def __new__(cls, *args):
                _args = args
                if len(args) < 1:
                    raise TypeError("name and value must be specified")
                name, args = args[0], args[1:]
                self = int.__new__(cls, *args)
                self._intname = name
                self._args = _args
                return self
            def __getnewargs__(self):
                return self._args
            @property
            def __name__(self):
                return self._intname
            def __repr__(self):
                # repr() is updated to include the name and type info
                return "%s(%r, %s)" % (type(self).__name__,
                                             self.__name__,
                                             int.__repr__(self))
            def __str__(self):
                # str() is unchanged, even if it relies on the repr() fallback
                base = int
                base_str = base.__str__
                if base_str.__objclass__ is object:
                    return base.__repr__(self)
                return base_str(self)
            # for simplicity, we only define one operator that
            # propagates expressions
            def __add__(self, other):
                temp = int(self) + int( other)
                if isinstance(self, NamedInt) and isinstance(other, NamedInt):
                    return NamedInt(
                        '(%s + %s)' % (self.__name__, other.__name__),
                        temp )
                else:
                    return temp

        class NEI(NamedInt, Enum):
            __qualname__ = 'NEI'  # needed for pickle protocol 4
            x = ('the-x', 1)
            y = ('the-y', 2)

        self.assertTrue(NEI.__new__ is Enum.__new__)
        self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
        globals()['NamedInt'] = NamedInt
        globals()['NEI'] = NEI
        NI5 = NamedInt('test', 5)
        self.assertEqual(NI5, 5)
        test_pickle_dump_load(self.assertTrue, NI5, 5)
        self.assertEqual(NEI.y.value, 2)
        test_pickle_dump_load(self.assertTrue, NEI.y)

    def test_subclasses_with_reduce(self):
        class NamedInt(int):
            __qualname__ = 'NamedInt'       # needed for pickle protocol 4
            def __new__(cls, *args):
                _args = args
                if len(args) < 1:
                    raise TypeError("name and value must be specified")
                name, args = args[0], args[1:]
                self = int.__new__(cls, *args)
                self._intname = name
                self._args = _args
                return self
            def __reduce__(self):
                return self.__class__, self._args
            @property
            def __name__(self):
                return self._intname
            def __repr__(self):
                # repr() is updated to include the name and type info
                return "%s(%r, %s)" % (type(self).__name__,
                                             self.__name__,
                                             int.__repr__(self))
            def __str__(self):
                # str() is unchanged, even if it relies on the repr() fallback
                base = int
                base_str = base.__str__
                if base_str.__objclass__ is object:
                    return base.__repr__(self)
                return base_str(self)
            # for simplicity, we only define one operator that
            # propagates expressions
            def __add__(self, other):
                temp = int(self) + int( other)
                if isinstance(self, NamedInt) and isinstance(other, NamedInt):
                    return NamedInt(
                        '(%s + %s)' % (self.__name__, other.__name__),
                        temp )
                else:
                    return temp

        class NEI(NamedInt, Enum):
            __qualname__ = 'NEI'      # needed for pickle protocol 4
            x = ('the-x', 1)
            y = ('the-y', 2)


        self.assertTrue(NEI.__new__ is Enum.__new__)
        self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
        globals()['NamedInt'] = NamedInt
        globals()['NEI'] = NEI
        NI5 = NamedInt('test', 5)
        self.assertEqual(NI5, 5)
        test_pickle_dump_load(self.assertEqual, NI5, 5)
        self.assertEqual(NEI.y.value, 2)
        test_pickle_dump_load(self.assertTrue, NEI.y)

    def test_subclasses_with_reduce_ex(self):
        class NamedInt(int):
            __qualname__ = 'NamedInt'       # needed for pickle protocol 4
            def __new__(cls, *args):
                _args = args
                if len(args) < 1:
                    raise TypeError("name and value must be specified")
                name, args = args[0], args[1:]
                self = int.__new__(cls, *args)
                self._intname = name
                self._args = _args
                return self
            def __reduce_ex__(self, proto):
                return self.__class__, self._args
            @property
            def __name__(self):
                return self._intname
            def __repr__(self):
                # repr() is updated to include the name and type info
                return "%s(%r, %s)" % (type(self).__name__,
                                             self.__name__,
                                             int.__repr__(self))
            def __str__(self):
                # str() is unchanged, even if it relies on the repr() fallback
                base = int
                base_str = base.__str__
                if base_str.__objclass__ is object:
                    return base.__repr__(self)
                return base_str(self)
            # for simplicity, we only define one operator that
            # propagates expressions
            def __add__(self, other):
                temp = int(self) + int( other)
                if isinstance(self, NamedInt) and isinstance(other, NamedInt):
                    return NamedInt(
                        '(%s + %s)' % (self.__name__, other.__name__),
                        temp )
                else:
                    return temp

        class NEI(NamedInt, Enum):
            __qualname__ = 'NEI'      # needed for pickle protocol 4
            x = ('the-x', 1)
            y = ('the-y', 2)


        self.assertTrue(NEI.__new__ is Enum.__new__)
        self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
        globals()['NamedInt'] = NamedInt
        globals()['NEI'] = NEI
        NI5 = NamedInt('test', 5)
        self.assertEqual(NI5, 5)
        test_pickle_dump_load(self.assertEqual, NI5, 5)
        self.assertEqual(NEI.y.value, 2)
        test_pickle_dump_load(self.assertTrue, NEI.y)

    def test_subclasses_without_direct_pickle_support(self):
        class NamedInt(int):
            __qualname__ = 'NamedInt'
            def __new__(cls, *args):
                _args = args
                name, args = args[0], args[1:]
                if len(args) == 0:
                    raise TypeError("name and value must be specified")
                self = int.__new__(cls, *args)
                self._intname = name
                self._args = _args
                return self
            @property
            def __name__(self):
                return self._intname
            def __repr__(self):
                # repr() is updated to include the name and type info
                return "%s(%r, %s)" % (type(self).__name__,
                                             self.__name__,
                                             int.__repr__(self))
            def __str__(self):
                # str() is unchanged, even if it relies on the repr() fallback
                base = int
                base_str = base.__str__
                if base_str.__objclass__ is object:
                    return base.__repr__(self)
                return base_str(self)
            # for simplicity, we only define one operator that
            # propagates expressions
            def __add__(self, other):
                temp = int(self) + int( other)
                if isinstance(self, NamedInt) and isinstance(other, NamedInt):
                    return NamedInt(
                        '(%s + %s)' % (self.__name__, other.__name__),
                        temp )
                else:
                    return temp

        class NEI(NamedInt, Enum):
            __qualname__ = 'NEI'
            x = ('the-x', 1)
            y = ('the-y', 2)

        self.assertTrue(NEI.__new__ is Enum.__new__)
        self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
        globals()['NamedInt'] = NamedInt
        globals()['NEI'] = NEI
        NI5 = NamedInt('test', 5)
        self.assertEqual(NI5, 5)
        self.assertEqual(NEI.y.value, 2)
        test_pickle_exception(self.assertRaises, TypeError, NEI.x)
        test_pickle_exception(self.assertRaises, PicklingError, NEI)

    def test_subclasses_without_direct_pickle_support_using_name(self):
        class NamedInt(int):
            __qualname__ = 'NamedInt'
            def __new__(cls, *args):
                _args = args
                name, args = args[0], args[1:]
                if len(args) == 0:
                    raise TypeError("name and value must be specified")
                self = int.__new__(cls, *args)
                self._intname = name
                self._args = _args
                return self
            @property
            def __name__(self):
                return self._intname
            def __repr__(self):
                # repr() is updated to include the name and type info
                return "%s(%r, %s)" % (type(self).__name__,
                                             self.__name__,
                                             int.__repr__(self))
            def __str__(self):
                # str() is unchanged, even if it relies on the repr() fallback
                base = int
                base_str = base.__str__
                if base_str.__objclass__ is object:
                    return base.__repr__(self)
                return base_str(self)
            # for simplicity, we only define one operator that
            # propagates expressions
            def __add__(self, other):
                temp = int(self) + int( other)
                if isinstance(self, NamedInt) and isinstance(other, NamedInt):
                    return NamedInt(
                        '(%s + %s)' % (self.__name__, other.__name__),
                        temp )
                else:
                    return temp

        class NEI(NamedInt, Enum):
            __qualname__ = 'NEI'
            x = ('the-x', 1)
            y = ('the-y', 2)
            def __reduce_ex__(self, proto):
                return getattr, (self.__class__, self._name_)

        self.assertTrue(NEI.__new__ is Enum.__new__)
        self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
        globals()['NamedInt'] = NamedInt
        globals()['NEI'] = NEI
        NI5 = NamedInt('test', 5)
        self.assertEqual(NI5, 5)
        self.assertEqual(NEI.y.value, 2)
        test_pickle_dump_load(self.assertTrue, NEI.y)
        test_pickle_dump_load(self.assertTrue, NEI)

    def test_tuple_subclass(self):
        class SomeTuple(tuple, Enum):
            __qualname__ = 'SomeTuple'
            first = (1, 'for the money')
            second = (2, 'for the show')
            third = (3, 'for the music')
        self.assertTrue(type(SomeTuple.first) is SomeTuple)
        self.assertTrue(isinstance(SomeTuple.second, tuple))
        self.assertEqual(SomeTuple.third, (3, 'for the music'))
        globals()['SomeTuple'] = SomeTuple
        test_pickle_dump_load(self.assertTrue, SomeTuple.first)

    def test_duplicate_values_give_unique_enum_items(self):
        class NumericEnum(AutoNumberEnum):
            __order__ = 'enum_m enum_d enum_y'
            enum_m = ()
            enum_d = ()
            enum_y = ()
            def __int__(self):
                return int(self._value_)
        self.assertEqual(int(NumericEnum.enum_d), 2)
        self.assertEqual(NumericEnum.enum_y.value, 3)
        self.assertTrue(NumericEnum(1) is NumericEnum.enum_m)
        self.assertEqual(
            list(NumericEnum),
            [NumericEnum.enum_m, NumericEnum.enum_d, NumericEnum.enum_y],
            )

    def test_inherited_new_from_enhanced_enum(self):
        class AutoNumber2(Enum):
            def __new__(cls):
                value = len(cls.__members__) + 1
                obj = object.__new__(cls)
                obj._value_ = value
                return obj
            def __int__(self):
                return int(self._value_)
        class Color(AutoNumber2):
            __order__ = 'red green blue'
            red = ()
            green = ()
            blue = ()
        self.assertEqual(len(Color), 3, "wrong number of elements: %d (should be %d)" % (len(Color), 3))
        self.assertEqual(list(Color), [Color.red, Color.green, Color.blue])
        if pyver >= 3.0:
            self.assertEqual(list(map(int, Color)), [1, 2, 3])

    def test_inherited_new_from_mixed_enum(self):
        class AutoNumber3(IntEnum):
            def __new__(cls):
                value = len(cls.__members__) + 1
                obj = int.__new__(cls, value)
                obj._value_ = value
                return obj
        class Color(AutoNumber3):
            red = ()
            green = ()
            blue = ()
        self.assertEqual(len(Color), 3, "wrong number of elements: %d (should be %d)" % (len(Color), 3))
        Color.red
        Color.green
        Color.blue

    def test_equality(self):
        class AlwaysEqual:
            def __eq__(self, other):
                return True
        class OrdinaryEnum(Enum):
            a = 1
        self.assertEqual(AlwaysEqual(), OrdinaryEnum.a)
        self.assertEqual(OrdinaryEnum.a, AlwaysEqual())

    def test_ordered_mixin(self):
        class Grade(OrderedEnum):
            __order__ = 'A B C D F'
            A = 5
            B = 4
            C = 3
            D = 2
            F = 1
        self.assertEqual(list(Grade), [Grade.A, Grade.B, Grade.C, Grade.D, Grade.F])
        self.assertTrue(Grade.A > Grade.B)
        self.assertTrue(Grade.F <= Grade.C)
        self.assertTrue(Grade.D < Grade.A)
        self.assertTrue(Grade.B >= Grade.B)

    def test_missing_deprecated(self):
        class Label(Enum):
            AnyApple = 0
            RedApple = 1
            GreenApple = 2
            @classmethod
            def _missing_(cls, name):
                return cls.AnyApple

        self.assertEqual(Label.AnyApple, Label(4))
        with self.assertRaises(AttributeError):
            Label.redapple
        with self.assertRaises(KeyError):
            Label['redapple']

    def test_missing(self):
        class Label(Enum):
            AnyApple = 0
            RedApple = 1
            GreenApple = 2
            @classmethod
            def _missing_value_(cls, name):
                return cls.AnyApple

        self.assertEqual(Label.AnyApple, Label(4))
        with self.assertRaises(AttributeError):
            Label.redapple
        with self.assertRaises(KeyError):
            Label['redapple']

    def test_missing_name(self):
        class Label(Enum):
            RedApple = 1
            GreenApple = 2
            @classmethod
            def _missing_name_(cls, name):
                for member in cls:
                    if member.name.lower() == name.lower():
                        return member

        Label['redapple']
        with self.assertRaises(AttributeError):
            Label.redapple
        with self.assertRaises(ValueError):
            Label('redapple')

    def test_missing_name_bad_return(self):
        class Label(Enum):
            RedApple = 1
            GreenApple = 2
            @classmethod
            def _missing_name_(cls, name):
                return None

        with self.assertRaises(AttributeError):
            Label.redapple
        with self.assertRaises(ValueError):
            Label('redapple')
        with self.assertRaises(KeyError):
            Label['redapple']

    def test_extending2(self):
        def bad_extension():
            class Shade(Enum):
                def shade(self):
                    print(self.name)
            class Color(Shade):
                red = 1
                green = 2
                blue = 3
            class MoreColor(Color):
                cyan = 4
                magenta = 5
                yellow = 6
        self.assertRaises(TypeError, bad_extension)

    def test_extending3(self):
        class Shade(Enum):
            def shade(self):
                return self.name
        class Color(Shade):
            def hex(self):
                return '%s hexlified!' % self.value
        class MoreColor(Color):
            cyan = 4
            magenta = 5
            yellow = 6
        self.assertEqual(MoreColor.magenta.hex(), '5 hexlified!')

    def test_extend_enum_plain(self):
        class Color(UniqueEnum):
            red = 1
            green = 2
            blue = 3
        extend_enum(Color, 'brown', 4)
        self.assertEqual(Color.brown.name, 'brown')
        self.assertEqual(Color.brown.value, 4)
        self.assertTrue(Color.brown in Color)
        self.assertEqual(len(Color), 4)

    def test_extend_enum_shadow(self):
        class Color(UniqueEnum):
            red = 1
            green = 2
            blue = 3
        extend_enum(Color, 'value', 4)
        self.assertEqual(Color.value.name, 'value')
        self.assertEqual(Color.value.value, 4)
        self.assertTrue(Color.value in Color)
        self.assertEqual(len(Color), 4)
        self.assertEqual(Color.red.value, 1)

    def test_extend_intenum(self):
        class Index(Enum):
            DeviceType    = 0x1000
            ErrorRegister = 0x1001

        for name, value in (
                ('ControlWord', 0x6040),
                ('StatusWord', 0x6041),
                ('OperationMode', 0x6060),
                ):
            extend_enum(Index, name, value)

        self.assertEqual(len(Index), 5)
        self.assertEqual(list(Index), [Index.DeviceType, Index.ErrorRegister, Index.ControlWord, Index.StatusWord, Index.OperationMode])
        self.assertEqual(Index.DeviceType.value, 0x1000)
        self.assertEqual(Index.StatusWord.value, 0x6041)

    def test_no_duplicates(self):
        def bad_duplicates():
            class Color1(UniqueEnum):
                red = 1
                green = 2
                blue = 3
            class Color2(UniqueEnum):
                red = 1
                green = 2
                blue = 3
                grene = 2
        self.assertRaises(ValueError, bad_duplicates)

    def test_no_duplicates_kinda(self):
        class Silly(UniqueEnum):
            one = 1
            two = 'dos'
            name = 3
        class Sillier(IntEnum, UniqueEnum):
            single = 1
            name = 2
            triple = 3
            value = 4

    def test_init(self):
        class Planet(Enum):
            MERCURY = (3.303e+23, 2.4397e6)
            VENUS   = (4.869e+24, 6.0518e6)
            EARTH   = (5.976e+24, 6.37814e6)
            MARS    = (6.421e+23, 3.3972e6)
            JUPITER = (1.9e+27,   7.1492e7)
            SATURN  = (5.688e+26, 6.0268e7)
            URANUS  = (8.686e+25, 2.5559e7)
            NEPTUNE = (1.024e+26, 2.4746e7)
            def __init__(self, mass, radius):
                self.mass = mass       # in kilograms
                self.radius = radius   # in meters
            @property
            def surface_gravity(self):
                # universal gravitational constant  (m3 kg-1 s-2)
                G = 6.67300E-11
                return G * self.mass / (self.radius * self.radius)
        self.assertEqual(round(Planet.EARTH.surface_gravity, 2), 9.80)
        self.assertEqual(Planet.EARTH.value, (5.976e+24, 6.37814e6))

        @skip
        def test_init_and_autonumber(self):
            pass

        @skip
        def test_init_and_autonumber_and_value(self):
            pass

    def test_no_init_and_autonumber(self):
        class DocEnum(str, Enum):
            """
            compares equal to all cased versions of its name
            accepts a docstring for each member
            """
            _settings_ = AutoNumber
            def __init__(self, value, doc=None):
                # first, fix _value_
                self._value_ = self._name_.lower()
                self.__doc__ = doc
            def __eq__(self, other):
                if isinstance(other, basestring):
                    return self._value_ == other.lower()
                elif isinstance(other, self.__class__):
                    return self is other
                else:
                    return False
            def __ne__(self, other):
                return not self == other
            REQUIRED = "required value"
            OPTION = "single value per name"
            MULTI = "multiple values per name (list form, no whitespace)"
            FLAG = "boolean/trivalent value per name"
            KEYWORD = 'unknown options'
        self.assertEqual(DocEnum.REQUIRED, 'required')
        self.assertEqual(DocEnum.REQUIRED, 'Required')
        self.assertEqual(DocEnum.REQUIRED, 'REQUIRED')

    def test_nonhash_value(self):
        class AutoNumberInAList(Enum):
            def __new__(cls):
                value = [len(cls.__members__) + 1]
                obj = object.__new__(cls)
                obj._value_ = value
                return obj
        class ColorInAList(AutoNumberInAList):
            __order__ = 'red green blue'
            red = ()
            green = ()
            blue = ()
        self.assertEqual(list(ColorInAList), [ColorInAList.red, ColorInAList.green, ColorInAList.blue])
        self.assertEqual(ColorInAList.red.value, [1])
        self.assertEqual(ColorInAList([1]), ColorInAList.red)

    def test_conflicting_types_resolved_in_new(self):
        class LabelledIntEnum(int, Enum):
            def __new__(cls, *args):
                value, label = args
                obj = int.__new__(cls, value)
                obj.label = label
                obj._value_ = value
                return obj

        class LabelledList(LabelledIntEnum):
            unprocessed = (1, "Unprocessed")
            payment_complete = (2, "Payment Complete")

        self.assertEqual(LabelledList.unprocessed, 1)
        self.assertEqual(LabelledList(1), LabelledList.unprocessed)
        self.assertEqual(list(LabelledList), [LabelledList.unprocessed, LabelledList.payment_complete])

    def test_auto_number(self):
        class Color(Enum):
            _order_ = 'red blue green'
            red = auto()
            blue = auto()
            green = auto()

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 1)
        self.assertEqual(Color.blue.value, 2)
        self.assertEqual(Color.green.value, 3)

    def test_auto_name(self):
        class Color(Enum):
            _order_ = 'red blue green'
            def _generate_next_value_(name, start, count, last):
                return name
            red = auto()
            blue = auto()
            green = auto()

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 'red')
        self.assertEqual(Color.blue.value, 'blue')
        self.assertEqual(Color.green.value, 'green')

    def test_auto_name_inherit(self):
        class AutoNameEnum(Enum):
            def _generate_next_value_(name, start, count, last):
                return name
        class Color(AutoNameEnum):
            _order_ = 'red blue green'
            red = auto()
            blue = auto()
            green = auto()

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 'red')
        self.assertEqual(Color.blue.value, 'blue')
        self.assertEqual(Color.green.value, 'green')

    def test_auto_garbage(self):
        class Color(Enum):
            _order_ = 'red blue'
            red = 'red'
            blue = auto()
        self.assertEqual(Color.blue.value, 1)

    def test_auto_garbage_corrected(self):
        class Color(Enum):
            _order_ = 'red blue green'
            red = 'red'
            blue = 2
            green = auto()

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 'red')
        self.assertEqual(Color.blue.value, 2)
        self.assertEqual(Color.green.value, 3)

    def test_duplicate_auto(self):
        class Dupes(Enum):
            _order_ = 'first second third'
            first = primero = auto()
            second = auto()
            third = auto()
        self.assertEqual([Dupes.first, Dupes.second, Dupes.third], list(Dupes))

    def test_empty_with_functional_api(self):
        empty = aenum.IntEnum('Foo', {})
        self.assertEqual(len(empty), 0)

    def test_auto_init(self):
        class Planet(Enum):
            _init_ = 'mass radius'
            MERCURY = (3.303e+23, 2.4397e6)
            VENUS   = (4.869e+24, 6.0518e6)
            EARTH   = (5.976e+24, 6.37814e6)
            MARS    = (6.421e+23, 3.3972e6)
            JUPITER = (1.9e+27,   7.1492e7)
            SATURN  = (5.688e+26, 6.0268e7)
            URANUS  = (8.686e+25, 2.5559e7)
            NEPTUNE = (1.024e+26, 2.4746e7)
            @property
            def surface_gravity(self):
                # universal gravitational constant  (m3 kg-1 s-2)
                G = 6.67300E-11
                return G * self.mass / (self.radius * self.radius)
        self.assertEqual(round(Planet.EARTH.surface_gravity, 2), 9.80)
        self.assertEqual(Planet.EARTH.value, (5.976e+24, 6.37814e6))

    def test_auto_init_with_value(self):
        class Color(Enum):
            _init_='value, rgb'
            RED = 1, (1, 0, 0)
            BLUE = 2, (0, 1, 0)
            GREEN = 3, (0, 0, 1)
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.BLUE.value, 2)
        self.assertEqual(Color.GREEN.value, 3)
        self.assertEqual(Color.RED.rgb, (1, 0, 0))
        self.assertEqual(Color.BLUE.rgb, (0, 1, 0))
        self.assertEqual(Color.GREEN.rgb, (0, 0, 1))

    def test_settings(self):
        class Settings(Enum):
            _settings_ = NoAlias
            red = 1
            rojo = 1
        self.assertFalse(Settings.red is Settings.rojo)

    def test_auto_and_init(self):
        class Field(IntEnum):
            _order_ = 'TYPE START'
            _init_ = '__doc__'
            _settings_ = AutoNumber
            TYPE = "Char, Date, Logical, etc."
            START = "Field offset in record"
        self.assertEqual(Field.TYPE, 1)
        self.assertEqual(Field.START, 2)
        self.assertEqual(Field.TYPE.__doc__, 'Char, Date, Logical, etc.')
        self.assertEqual(Field.START.__doc__, 'Field offset in record')

    def test_auto_and_start(self):
        class Field(IntEnum):
            _order_ = 'TYPE START'
            _start_ = 0
            _init_ = '__doc__'
            TYPE = "Char, Date, Logical, etc."
            START = "Field offset in record"
        self.assertEqual(Field.TYPE, 0)
        self.assertEqual(Field.START, 1)
        self.assertEqual(Field.TYPE.__doc__, 'Char, Date, Logical, etc.')
        self.assertEqual(Field.START.__doc__, 'Field offset in record')

    def test_auto_and_init_and_some_values(self):
        class Field(IntEnum):
            _order_ = 'TYPE START BLAH BELCH'
            _init_ = '__doc__'
            _settings_ = AutoNumber
            TYPE = "Char, Date, Logical, etc."
            START = "Field offset in record"
            BLAH = 5, "test blah"
            BELCH = 'test belch'
        self.assertEqual(Field.TYPE, 1)
        self.assertEqual(Field.START, 2)
        self.assertEqual(Field.BLAH, 5)
        self.assertEqual(Field.BELCH, 6)
        self.assertEqual(Field.TYPE.__doc__, 'Char, Date, Logical, etc.')
        self.assertEqual(Field.START.__doc__, 'Field offset in record')
        self.assertEqual(Field.BLAH.__doc__, 'test blah')
        self.assertEqual(Field.BELCH.__doc__, 'test belch')

    def test_auto_and_init_and_some_complex_values(self):
        class Field(IntEnum):
            _order_ = 'TYPE START BLAH BELCH'
            _init_ = '__doc__ help'
            _settings_ = AutoNumber
            TYPE = "Char, Date, Logical, etc.", "fields composed of character data"
            START = "Field offset in record", "where the data starts in the record"
            BLAH = 5, "test blah", "some help"
            BELCH = 'test belch', "some more help"
        self.assertEqual(Field.TYPE, 1)
        self.assertEqual(Field.START, 2)
        self.assertEqual(Field.BLAH, 5)
        self.assertEqual(Field.BELCH, 6)
        self.assertEqual(Field.TYPE.__doc__, 'Char, Date, Logical, etc.')
        self.assertEqual(Field.START.__doc__, 'Field offset in record')
        self.assertEqual(Field.BLAH.__doc__, 'test blah')
        self.assertEqual(Field.BELCH.__doc__, 'test belch')
        self.assertEqual(Field.TYPE.help, "fields composed of character data")
        self.assertEqual(Field.START.help, "where the data starts in the record")
        self.assertEqual(Field.BLAH.help, "some help")
        self.assertEqual(Field.BELCH.help, "some more help")

    def test_auto_and_init_inherited(self):
        class AutoEnum(IntEnum):
            _start_ = 0
            _init_ = '__doc__'
        class Field(AutoEnum):
            _order_ = 'TYPE START BLAH BELCH'
            TYPE = "Char, Date, Logical, etc."
            START = "Field offset in record"
            BLAH = 5, "test blah"
            BELCH = 'test belch'
        self.assertEqual(Field.TYPE, 0)
        self.assertEqual(Field.START, 1)
        self.assertEqual(Field.BLAH, 5)
        self.assertEqual(Field.BELCH, 6)
        self.assertEqual(Field.TYPE.__doc__, 'Char, Date, Logical, etc.')
        self.assertEqual(Field.START.__doc__, 'Field offset in record')
        self.assertEqual(Field.BLAH.__doc__, 'test blah')
        self.assertEqual(Field.BELCH.__doc__, 'test belch')

    def test_AutoNumberEnum_and_property(self):
        class Color(aenum.AutoNumberEnum):
            red = ()
            green = ()
            blue = ()
            @property
            def cap_name(self):
                return self.name.title()
        self.assertEqual(Color.blue.cap_name, 'Blue')

    def test_AutoNumberEnum(self):
        class Color(aenum.AutoNumberEnum):
            _order_ = 'red green blue'
            red = ()
            green = ()
            blue = ()
        self.assertEqual(list(Color), [Color.red, Color.green, Color.blue])
        self.assertEqual(Color.red.value, 1)
        self.assertEqual(Color.green.value, 2)
        self.assertEqual(Color.blue.value, 3)

    def test_combine_new_settings_with_old_settings(self):
        class Auto(Enum):
            _settings_ = Unique
        with self.assertRaises(ValueError):
            class AutoUnique(Auto):
                _settings_ = AutoNumber
                BLAH = ()
                BLUH = ()
                ICK = 1

    def test_timedelta(self):
        class Period(timedelta, Enum):
            '''
            different lengths of time
            '''
            _init_ = 'value period'
            _settings_ = NoAlias
            _ignore_ = 'Period i'
            Period = vars()
            for i in range(31):
                Period['day_%d' % i] = i, 'day'
            for i in range(15):
                Period['week_%d' % i] = i*7, 'week'
            for i in range(12):
                Period['month_%d' % i] = i*30, 'month'
            OneDay = day_1
            OneWeek = week_1
        self.assertFalse(hasattr(Period, '_ignore_'))
        self.assertFalse(hasattr(Period, 'Period'))
        self.assertFalse(hasattr(Period, 'i'))
        self.assertTrue(isinstance(Period.day_1, timedelta))

    def test_skip(self):
        class enumA(Enum):
            @skip
            class enumB(Enum):
                elementA = 'a'
                elementB = 'b'
            @skip
            class enumC(Enum):
                elementC = 'c'
                elementD = 'd'
        self.assertIs(enumA.enumB, enumA.__dict__['enumB'])

    if StdlibEnumMeta is not None:
        def test_stdlib_inheritence(self):
            self.assertTrue(isinstance(self.Season, StdlibEnumMeta))
            self.assertTrue(issubclass(self.Season, StdlibEnum))


class TestFlag(TestCase):
    """Tests of the Flags."""

    class Perm(Flag):
        R, W, X = 4, 2, 1

    class Open(Flag):
        RO = 0
        WO = 1
        RW = 2
        AC = 3
        CE = 1<<19

    def test_str(self):
        Perm = self.Perm
        self.assertEqual(str(Perm.R), 'Perm.R')
        self.assertEqual(str(Perm.W), 'Perm.W')
        self.assertEqual(str(Perm.X), 'Perm.X')
        self.assertEqual(str(Perm.R | Perm.W), 'Perm.R|W')
        self.assertEqual(str(Perm.R | Perm.W | Perm.X), 'Perm.R|W|X')
        self.assertEqual(str(Perm(0)), 'Perm.0')
        self.assertEqual(str(~Perm.R), 'Perm.W|X')
        self.assertEqual(str(~Perm.W), 'Perm.R|X')
        self.assertEqual(str(~Perm.X), 'Perm.R|W')
        self.assertEqual(str(~(Perm.R | Perm.W)), 'Perm.X')
        self.assertEqual(str(~(Perm.R | Perm.W | Perm.X)), 'Perm.0')
        self.assertEqual(str(Perm(~0)), 'Perm.R|W|X')

        Open = self.Open
        self.assertEqual(str(Open.RO), 'Open.RO')
        self.assertEqual(str(Open.WO), 'Open.WO')
        self.assertEqual(str(Open.AC), 'Open.AC')
        self.assertEqual(str(Open.RO | Open.CE), 'Open.CE')
        self.assertEqual(str(Open.WO | Open.CE), 'Open.CE|WO')
        self.assertEqual(str(~Open.RO), 'Open.CE|AC|RW|WO')
        self.assertEqual(str(~Open.WO), 'Open.CE|RW')
        self.assertEqual(str(~Open.AC), 'Open.CE')
        self.assertEqual(str(~(Open.RO | Open.CE)), 'Open.AC')
        self.assertEqual(str(~(Open.WO | Open.CE)), 'Open.RW')

    def test_repr(self):
        Perm = self.Perm
        self.assertEqual(repr(Perm.R), '<Perm.R: 4>')
        self.assertEqual(repr(Perm.W), '<Perm.W: 2>')
        self.assertEqual(repr(Perm.X), '<Perm.X: 1>')
        self.assertEqual(repr(Perm.R | Perm.W), '<Perm.R|W: 6>')
        self.assertEqual(repr(Perm.R | Perm.W | Perm.X), '<Perm.R|W|X: 7>')
        self.assertEqual(repr(Perm(0)), '<Perm.0: 0>')
        self.assertEqual(repr(~Perm.R), '<Perm.W|X: 3>')
        self.assertEqual(repr(~Perm.W), '<Perm.R|X: 5>')
        self.assertEqual(repr(~Perm.X), '<Perm.R|W: 6>')
        self.assertEqual(repr(~(Perm.R | Perm.W)), '<Perm.X: 1>')
        self.assertEqual(repr(~(Perm.R | Perm.W | Perm.X)), '<Perm.0: 0>')
        self.assertEqual(repr(Perm(~0)), '<Perm.R|W|X: 7>')

        Open = self.Open
        self.assertEqual(repr(Open.RO), '<Open.RO: 0>')
        self.assertEqual(repr(Open.WO), '<Open.WO: 1>')
        self.assertEqual(repr(Open.AC), '<Open.AC: 3>')
        self.assertEqual(repr(Open.RO | Open.CE), '<Open.CE: 524288>')
        self.assertEqual(repr(Open.WO | Open.CE), '<Open.CE|WO: 524289>')
        self.assertEqual(repr(~Open.RO), '<Open.CE|AC|RW|WO: 524291>')
        self.assertEqual(repr(~Open.WO), '<Open.CE|RW: 524290>')
        self.assertEqual(repr(~Open.AC), '<Open.CE: 524288>')
        self.assertEqual(repr(~(Open.RO | Open.CE)), '<Open.AC: 3>')
        self.assertEqual(repr(~(Open.WO | Open.CE)), '<Open.RW: 2>')

    def test_or(self):
        Perm = self.Perm
        for i in Perm:
            for j in Perm:
                self.assertEqual((i | j), Perm(i.value | j.value))
                self.assertEqual((i | j).value, i.value | j.value)
                self.assertIs(type(i | j), Perm)
        for i in Perm:
            self.assertIs(i | i, i)
        Open = self.Open
        self.assertIs(Open.RO | Open.CE, Open.CE)

    def test_and(self):
        Perm = self.Perm
        RW = Perm.R | Perm.W
        RX = Perm.R | Perm.X
        WX = Perm.W | Perm.X
        RWX = Perm.R | Perm.W | Perm.X
        values = list(Perm) + [RW, RX, WX, RWX, Perm(0)]
        for i in values:
            for j in values:
                self.assertEqual((i & j).value, i.value & j.value)
                self.assertIs(type(i & j), Perm)
        for i in Perm:
            self.assertIs(i & i, i)
            self.assertIs(i & RWX, i)
            self.assertIs(RWX & i, i)
        Open = self.Open
        self.assertIs(Open.RO & Open.CE, Open.RO)

    def test_xor(self):
        Perm = self.Perm
        for i in Perm:
            for j in Perm:
                self.assertEqual((i ^ j).value, i.value ^ j.value)
                self.assertIs(type(i ^ j), Perm)
        for i in Perm:
            self.assertIs(i ^ Perm(0), i)
            self.assertIs(Perm(0) ^ i, i)
        Open = self.Open
        self.assertIs(Open.RO ^ Open.CE, Open.CE)
        self.assertIs(Open.CE ^ Open.CE, Open.RO)

    def test_invert(self):
        Perm = self.Perm
        RW = Perm.R | Perm.W
        RX = Perm.R | Perm.X
        WX = Perm.W | Perm.X
        RWX = Perm.R | Perm.W | Perm.X
        values = list(Perm) + [RW, RX, WX, RWX, Perm(0)]
        for i in values:
            self.assertIs(type(~i), Perm)
            self.assertEqual(~~i, i)
        for i in Perm:
            self.assertIs(~~i, i)
        Open = self.Open
        self.assertIs(Open.WO & ~Open.WO, Open.RO)
        self.assertIs((Open.WO|Open.CE) & ~Open.WO, Open.CE)

    def test_bool(self):
        Perm = self.Perm
        for f in Perm:
            self.assertTrue(f)
        Open = self.Open
        for f in Open:
            self.assertEqual(bool(f.value), bool(f))

    def test_programatic_function_string(self):
        Perm = Flag('Perm', 'R W X')
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        for i, n in enumerate('R W X'.split()):
            v = 1<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_string_with_start(self):
        Perm = Flag('Perm', 'R W X', start=8)
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        for i, n in enumerate('R W X'.split()):
            v = 8<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_string_list(self):
        Perm = Flag('Perm', ['R', 'W', 'X'])
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        for i, n in enumerate('R W X'.split()):
            v = 1<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_iterable(self):
        Perm = Flag('Perm', (('R', 2), ('W', 8), ('X', 32)))
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        for i, n in enumerate('R W X'.split()):
            v = 1<<(2*i+1)
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_from_dict(self):
        Perm = Flag('Perm', OrderedDict((('R', 2), ('W', 8), ('X', 32))))
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        for i, n in enumerate('R W X'.split()):
            v = 1<<(2*i+1)
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_pickle(self):
        if isinstance(FlagStooges, Exception):
            raise FlagStooges
        test_pickle_dump_load(self.assertIs, FlagStooges.CURLY|FlagStooges.MOE)
        test_pickle_dump_load(self.assertIs, FlagStooges)

    def test_containment(self):
        Perm = self.Perm
        R, W, X = Perm
        RW = R | W
        RX = R | X
        WX = W | X
        RWX = R | W | X
        self.assertTrue(R in RW)
        self.assertTrue(R in RX)
        self.assertTrue(R in RWX)
        self.assertTrue(W in RW)
        self.assertTrue(W in WX)
        self.assertTrue(W in RWX)
        self.assertTrue(X in RX)
        self.assertTrue(X in WX)
        self.assertTrue(X in RWX)
        self.assertFalse(R in WX)
        self.assertFalse(W in RX)
        self.assertFalse(X in RW)

    def test_auto_number(self):
        class Color(Flag):
            _order_ = 'red blue green'
            red = auto()
            blue = auto()
            green = auto()

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 1)
        self.assertEqual(Color.blue.value, 2)
        self.assertEqual(Color.green.value, 4)

    def test_auto_number_garbage(self):
        with self.assertRaisesRegex(TypeError, 'Invalid Flag value: .not an int.'):
            class Color(Flag):
                _order_ = 'red blue'
                red = 'not an int'
                blue = auto()

    def test_cascading_failure(self):
        class Bizarre(Flag):
            c = 3
            d = 4
            f = 6
        # Bizarre.c | Bizarre.d
        self.assertRaisesRegex(ValueError, "5 is not a valid Bizarre", Bizarre, 5)
        self.assertRaisesRegex(ValueError, "5 is not a valid Bizarre", Bizarre, 5)
        self.assertRaisesRegex(ValueError, "2 is not a valid Bizarre", Bizarre, 2)
        self.assertRaisesRegex(ValueError, "2 is not a valid Bizarre", Bizarre, 2)
        self.assertRaisesRegex(ValueError, "1 is not a valid Bizarre", Bizarre, 1)
        self.assertRaisesRegex(ValueError, "1 is not a valid Bizarre", Bizarre, 1)

    def test_duplicate_auto(self):
        class Dupes(Enum):
            _order_ = 'first second third'
            first = primero = auto()
            second = auto()
            third = auto()
        self.assertEqual([Dupes.first, Dupes.second, Dupes.third], list(Dupes))

    def test_bizarre(self):
        class Bizarre(Flag):
            b = 3
            c = 4
            d = 6
        self.assertEqual(repr(Bizarre(7)), '<Bizarre.d|c|b: 7>')

    @unittest.skipUnless(threading, 'Threading required for this test.')
    def test_unique_composite(self):
        # override __eq__ to be identity only
        class TestFlag(Flag):
            _order_ = 'one two three four five six seven eight'
            one = auto()
            two = auto()
            three = auto()
            four = auto()
            five = auto()
            six = auto()
            seven = auto()
            eight = auto()
            def __eq__(self, other):
                return self is other
            def __hash__(self):
                return hash(self._value_)
        # have multiple threads competing to complete the composite members
        seen = set()
        failed = [False]
        def cycle_enum():
            # nonlocal failed
            try:
                for i in range(256):
                    seen.add(TestFlag(i))
            except Exception:
                failed[0] = True
        threads = [
                threading.Thread(target=cycle_enum)
                for _ in range(8)
                ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # check that only 248 members were created (8 were created originally)
        self.assertFalse(
                failed[0],
                'at least one thread failed while creating composite members')
        self.assertEqual(256, len(seen), 'too many composite members created')


class TestIntFlag(TestCase):
    """Tests of the IntFlags."""

    class Perm(IntFlag):
        X = 1 << 0
        W = 1 << 1
        R = 1 << 2

    class Open(IntFlag):
        RO = 0
        WO = 1
        RW = 2
        AC = 3
        CE = 1<<19

    def test_type(self):
        Perm = self.Perm
        Open = self.Open
        for f in Perm:
            self.assertTrue(isinstance(f, Perm))
            self.assertEqual(f, f.value)
        self.assertTrue(isinstance(Perm.W | Perm.X, Perm))
        self.assertEqual(Perm.W | Perm.X, 3)
        for f in Open:
            self.assertTrue(isinstance(f, Open))
            self.assertEqual(f, f.value)
        self.assertTrue(isinstance(Open.WO | Open.RW, Open))
        self.assertEqual(Open.WO | Open.RW, 3)


    def test_str(self):
        Perm = self.Perm
        self.assertEqual(str(Perm.R), 'Perm.R')
        self.assertEqual(str(Perm.W), 'Perm.W')
        self.assertEqual(str(Perm.X), 'Perm.X')
        self.assertEqual(str(Perm.R | Perm.W), 'Perm.R|W')
        self.assertEqual(str(Perm.R | Perm.W | Perm.X), 'Perm.R|W|X')
        self.assertEqual(str(Perm.R | 8), 'Perm.8|R')
        self.assertEqual(str(Perm(0)), 'Perm.0')
        self.assertEqual(str(Perm(8)), 'Perm.8')
        self.assertEqual(str(~Perm.R), 'Perm.W|X')
        self.assertEqual(str(~Perm.W), 'Perm.R|X')
        self.assertEqual(str(~Perm.X), 'Perm.R|W')
        self.assertEqual(str(~(Perm.R | Perm.W)), 'Perm.X')
        self.assertEqual(str(~(Perm.R | Perm.W | Perm.X)), 'Perm.-8')
        self.assertEqual(str(~(Perm.R | 8)), 'Perm.W|X')
        self.assertEqual(str(Perm(~0)), 'Perm.R|W|X')
        self.assertEqual(str(Perm(~8)), 'Perm.R|W|X')

        Open = self.Open
        self.assertEqual(str(Open.RO), 'Open.RO')
        self.assertEqual(str(Open.WO), 'Open.WO')
        self.assertEqual(str(Open.AC), 'Open.AC')
        self.assertEqual(str(Open.RO | Open.CE), 'Open.CE')
        self.assertEqual(str(Open.WO | Open.CE), 'Open.CE|WO')
        self.assertEqual(str(Open(4)), 'Open.4')
        self.assertEqual(str(~Open.RO), 'Open.CE|AC|RW|WO')
        self.assertEqual(str(~Open.WO), 'Open.CE|RW')
        self.assertEqual(str(~Open.AC), 'Open.CE')
        self.assertEqual(str(~(Open.RO | Open.CE)), 'Open.AC|RW|WO')
        self.assertEqual(str(~(Open.WO | Open.CE)), 'Open.RW')
        self.assertEqual(str(Open(~4)), 'Open.CE|AC|RW|WO')

    def test_repr(self):
        Perm = self.Perm
        self.assertEqual(repr(Perm.R), '<Perm.R: 4>')
        self.assertEqual(repr(Perm.W), '<Perm.W: 2>')
        self.assertEqual(repr(Perm.X), '<Perm.X: 1>')
        self.assertEqual(repr(Perm.R | Perm.W), '<Perm.R|W: 6>')
        self.assertEqual(repr(Perm.R | Perm.W | Perm.X), '<Perm.R|W|X: 7>')
        self.assertEqual(repr(Perm.R | 8), '<Perm.8|R: 12>')
        self.assertEqual(repr(Perm(0)), '<Perm.0: 0>')
        self.assertEqual(repr(Perm(8)), '<Perm.8: 8>')
        self.assertEqual(repr(~Perm.R), '<Perm.W|X: -5>')
        self.assertEqual(repr(~Perm.W), '<Perm.R|X: -3>')
        self.assertEqual(repr(~Perm.X), '<Perm.R|W: -2>')
        self.assertEqual(repr(~(Perm.R | Perm.W)), '<Perm.X: -7>')
        self.assertEqual(repr(~(Perm.R | Perm.W | Perm.X)), '<Perm.-8: -8>')
        self.assertEqual(repr(~(Perm.R | 8)), '<Perm.W|X: -13>')
        self.assertEqual(repr(Perm(~0)), '<Perm.R|W|X: -1>')
        self.assertEqual(repr(Perm(~8)), '<Perm.R|W|X: -9>')

        Open = self.Open
        self.assertEqual(repr(Open.RO), '<Open.RO: 0>')
        self.assertEqual(repr(Open.WO), '<Open.WO: 1>')
        self.assertEqual(repr(Open.AC), '<Open.AC: 3>')
        self.assertEqual(repr(Open.RO | Open.CE), '<Open.CE: 524288>')
        self.assertEqual(repr(Open.WO | Open.CE), '<Open.CE|WO: 524289>')
        self.assertEqual(repr(Open(4)), '<Open.4: 4>')
        self.assertEqual(repr(~Open.RO), '<Open.CE|AC|RW|WO: -1>')
        self.assertEqual(repr(~Open.WO), '<Open.CE|RW: -2>')
        self.assertEqual(repr(~Open.AC), '<Open.CE: -4>')
        self.assertEqual(repr(~(Open.RO | Open.CE)), '<Open.AC|RW|WO: -524289>')
        self.assertEqual(repr(~(Open.WO | Open.CE)), '<Open.RW: -524290>')
        self.assertEqual(repr(Open(~4)), '<Open.CE|AC|RW|WO: -5>')

    def test_or(self):
        Perm = self.Perm
        for i in Perm:
            for j in Perm:
                self.assertEqual(i | j, i.value | j.value)
                self.assertEqual((i | j).value, i.value | j.value)
                self.assertIs(type(i | j), Perm)
            for j in range(8):
                self.assertEqual(i | j, i.value | j)
                self.assertEqual((i | j).value, i.value | j)
                self.assertIs(type(i | j), Perm)
                self.assertEqual(j | i, j | i.value)
                self.assertEqual((j | i).value, j | i.value)
                self.assertIs(type(j | i), Perm)
        for i in Perm:
            self.assertIs(i | i, i)
            self.assertIs(i | 0, i)
            self.assertIs(0 | i, i)
        Open = self.Open
        self.assertIs(Open.RO | Open.CE, Open.CE)

    def test_and(self):
        Perm = self.Perm
        RW = Perm.R | Perm.W
        RX = Perm.R | Perm.X
        WX = Perm.W | Perm.X
        RWX = Perm.R | Perm.W | Perm.X
        values = list(Perm) + [RW, RX, WX, RWX, Perm(0)]
        for i in values:
            for j in values:
                self.assertEqual(i & j, i.value & j.value, 'i is %r, j is %r' % (i, j))
                self.assertEqual((i & j).value, i.value & j.value, 'i is %r, j is %r' % (i, j))
                self.assertIs(type(i & j), Perm, 'i is %r, j is %r' % (i, j))
            for j in range(8):
                self.assertEqual(i & j, i.value & j)
                self.assertEqual((i & j).value, i.value & j)
                self.assertIs(type(i & j), Perm)
                self.assertEqual(j & i, j & i.value)
                self.assertEqual((j & i).value, j & i.value)
                self.assertIs(type(j & i), Perm)
        for i in Perm:
            self.assertIs(i & i, i)
            self.assertIs(i & 7, i)
            self.assertIs(7 & i, i)
        Open = self.Open
        self.assertIs(Open.RO & Open.CE, Open.RO)

    def test_xor(self):
        Perm = self.Perm
        for i in Perm:
            for j in Perm:
                self.assertEqual(i ^ j, i.value ^ j.value)
                self.assertEqual((i ^ j).value, i.value ^ j.value)
                self.assertIs(type(i ^ j), Perm)
            for j in range(8):
                self.assertEqual(i ^ j, i.value ^ j)
                self.assertEqual((i ^ j).value, i.value ^ j)
                self.assertIs(type(i ^ j), Perm)
                self.assertEqual(j ^ i, j ^ i.value)
                self.assertEqual((j ^ i).value, j ^ i.value)
                self.assertIs(type(j ^ i), Perm)
        for i in Perm:
            self.assertIs(i ^ 0, i)
            self.assertIs(0 ^ i, i)
        Open = self.Open
        self.assertIs(Open.RO ^ Open.CE, Open.CE)
        self.assertIs(Open.CE ^ Open.CE, Open.RO)

    def test_invert(self):
        Perm = self.Perm
        RW = Perm.R | Perm.W
        RX = Perm.R | Perm.X
        WX = Perm.W | Perm.X
        RWX = Perm.R | Perm.W | Perm.X
        values = list(Perm) + [RW, RX, WX, RWX, Perm(0)]
        for i in values:
            self.assertEqual(~i, ~i.value)
            self.assertEqual((~i).value, ~i.value)
            self.assertIs(type(~i), Perm)
            self.assertEqual(~~i, i)
        for i in Perm:
            self.assertIs(~~i, i)
        Open = self.Open
        self.assertIs(Open.WO & ~Open.WO, Open.RO)
        self.assertIs((Open.WO|Open.CE) & ~Open.WO, Open.CE)

    def test_programatic_function_string(self):
        Perm = IntFlag('Perm', 'R W X')
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        for i, n in enumerate('R W X'.split()):
            v = 1<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e, v)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_string_with_start(self):
        Perm = IntFlag('Perm', 'R W X', start=8)
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        for i, n in enumerate('R W X'.split()):
            v = 8<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e, v)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_string_list(self):
        Perm = IntFlag('Perm', ['R', 'W', 'X'])
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        for i, n in enumerate('R W X'.split()):
            v = 1<<i
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e, v)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_iterable(self):
        Perm = IntFlag('Perm', (('R', 2), ('W', 8), ('X', 32)))
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        for i, n in enumerate('R W X'.split()):
            v = 1<<(2*i+1)
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e, v)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)

    def test_programatic_function_from_dict(self):
        Perm = IntFlag('Perm', OrderedDict((('R', 2), ('W', 8), ('X', 32))))
        lst = list(Perm)
        self.assertEqual(len(lst), len(Perm))
        self.assertEqual(len(Perm), 3, Perm)
        self.assertEqual(lst, [Perm.R, Perm.W, Perm.X])
        for i, n in enumerate('R W X'.split()):
            v = 1<<(2*i+1)
            e = Perm(v)
            self.assertEqual(e.value, v)
            self.assertEqual(type(e.value), int)
            self.assertEqual(e, v)
            self.assertEqual(e.name, n)
            self.assertIn(e, Perm)
            self.assertIs(type(e), Perm)


    def test_containment(self):
        Perm = self.Perm
        R, W, X = Perm
        RW = R | W
        RX = R | X
        WX = W | X
        RWX = R | W | X
        self.assertTrue(R in RW)
        self.assertTrue(R in RX)
        self.assertTrue(R in RWX)
        self.assertTrue(W in RW)
        self.assertTrue(W in WX)
        self.assertTrue(W in RWX)
        self.assertTrue(X in RX)
        self.assertTrue(X in WX)
        self.assertTrue(X in RWX)
        self.assertFalse(R in WX)
        self.assertFalse(W in RX)
        self.assertFalse(X in RW)

    def test_bool(self):
        Perm = self.Perm
        for f in Perm:
            self.assertTrue(f)
        Open = self.Open
        for f in Open:
            self.assertEqual(bool(f.value), bool(f))

    @unittest.skipUnless(threading, 'Threading required for this test.')
    def test_unique_composite(self):
        # override __eq__ to be identity only
        class TestFlag(IntFlag):
            _order_ = 'one two three four five six seven eight'
            one = auto()
            two = auto()
            three = auto()
            four = auto()
            five = auto()
            six = auto()
            seven = auto()
            eight = auto()
            def __eq__(self, other):
                return self is other
            def __hash__(self):
                return hash(self._value_)
        # have multiple threads competing to complete the composite members
        seen = set()
        failed = [False]
        def cycle_enum():
            # nonlocal failed
            try:
                for i in range(256):
                    seen.add(TestFlag(i))
            except Exception:
                failed[0] = True
        threads = [
                threading.Thread(target=cycle_enum)
                for _ in range(8)
                ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # check that only 248 members were created (8 were created originally)
        self.assertFalse(
                failed[0],
                'at least one thread failed while creating composite members')
        self.assertEqual(256, len(seen), 'too many composite members created')


class TestUnique(TestCase):
    """2.4 doesn't allow class decorators, use function syntax."""

    def test_unique_clean(self):
        class Clean(Enum):
            one = 1
            two = 'dos'
            tres = 4.0
        unique(Clean)
        class Cleaner(IntEnum):
            single = 1
            double = 2
            triple = 3
        unique(Cleaner)

    def test_unique_dirty(self):
        try:
            class Dirty(Enum):
                __order__ = 'one two'
                one = 1
                two = 'dos'
                tres = 1
            unique(Dirty)
        except ValueError:
            exc = sys.exc_info()[1]
            message = exc.args[0]
        self.assertTrue('tres -> one' in message)

        try:
            class Dirtier(IntEnum):
                __order__ = 'single triple'
                single = 1
                double = 1
                triple = 3
                turkey = 3
            unique(Dirtier)
        except ValueError:
            exc = sys.exc_info()[1]
            message = exc.args[0]
        self.assertTrue('double -> single' in message)
        self.assertTrue('turkey -> triple' in message)

    def test_unique_with_name(self):
        @unique
        class Silly(Enum):
            one = 1
            two = 'dos'
            name = 3
        @unique
        class Sillier(IntEnum):
            single = 1
            name = 2
            triple = 3
            value = 4


class TestNamedTuple(TestCase):

    def test_explicit_indexing(self):
        class Person(NamedTuple):
            age = 0
            first = 1
            last = 2
        p1 = Person(17, 'John', 'Doe')
        p2 = Person(21, 'Jane', 'Doe')
        self.assertEqual(p1[0], 17)
        self.assertEqual(p1[1], 'John')
        self.assertEqual(p1[2], 'Doe')
        self.assertEqual(p2[0], 21)
        self.assertEqual(p2[1], 'Jane')
        self.assertEqual(p2[2], 'Doe')
        self.assertEqual(p1.age, 17)
        self.assertEqual(p1.first, 'John')
        self.assertEqual(p1.last, 'Doe')
        self.assertEqual(p2.age, 21)
        self.assertEqual(p2.first, 'Jane')
        self.assertEqual(p2.last, 'Doe')

    def test_implicit_indexing(self):
        class Person(NamedTuple):
            __order__ = "age first last"
            age = "person's age"
            first = "person's first name"
            last = "person's last name"
        p1 = Person(17, 'John', 'Doe')
        p2 = Person(21, 'Jane', 'Doe')
        self.assertEqual(p1[0], 17)
        self.assertEqual(p1[1], 'John')
        self.assertEqual(p1[2], 'Doe')
        self.assertEqual(p2[0], 21)
        self.assertEqual(p2[1], 'Jane')
        self.assertEqual(p2[2], 'Doe')
        self.assertEqual(p1.age, 17)
        self.assertEqual(p1.first, 'John')
        self.assertEqual(p1.last, 'Doe')
        self.assertEqual(p2.age, 21)
        self.assertEqual(p2.first, 'Jane')
        self.assertEqual(p2.last, 'Doe')

    def test_mixed_indexing(self):
        class Person(NamedTuple):
            __order__ = "age last cars"
            age = "person's age"
            last = 2, "person's last name"
            cars = "person's cars"
        p1 = Person(17, 'John', 'Doe', 3)
        p2 = Person(21, 'Jane', 'Doe', 9)
        self.assertEqual(p1[0], 17)
        self.assertEqual(p1[1], 'John')
        self.assertEqual(p1[2], 'Doe')
        self.assertEqual(p1[3], 3)
        self.assertEqual(p2[0], 21)
        self.assertEqual(p2[1], 'Jane')
        self.assertEqual(p2[2], 'Doe')
        self.assertEqual(p2[3], 9)
        self.assertEqual(p1.age, 17)
        self.assertEqual(p1.last, 'Doe')
        self.assertEqual(p1.cars, 3)
        self.assertEqual(p2.age, 21)
        self.assertEqual(p2.last, 'Doe')
        self.assertEqual(p2.cars, 9)

    def test_issubclass(self):
        class Person(NamedTuple):
            age = 0
            first = 1
            last = 2
        self.assertTrue(issubclass(Person, NamedTuple))
        self.assertTrue(issubclass(Person, tuple))

    def test_isinstance(self):
        class Person(NamedTuple):
            age = 0
            first = 1
            last = 2
        p1 = Person(17, 'John', 'Doe')
        self.assertTrue(isinstance(p1, Person))
        self.assertTrue(isinstance(p1, NamedTuple))
        self.assertTrue(isinstance(p1, tuple))

    def test_explicit_indexing_after_functional_api(self):
        Person = NamedTuple('Person', (('age', 0), ('first', 1), ('last', 2)))
        p1 = Person(17, 'John', 'Doe')
        p2 = Person(21, 'Jane', 'Doe')
        self.assertEqual(p1[0], 17)
        self.assertEqual(p1[1], 'John')
        self.assertEqual(p1[2], 'Doe')
        self.assertEqual(p2[0], 21)
        self.assertEqual(p2[1], 'Jane')
        self.assertEqual(p2[2], 'Doe')
        self.assertEqual(p1.age, 17)
        self.assertEqual(p1.first, 'John')
        self.assertEqual(p1.last, 'Doe')
        self.assertEqual(p2.age, 21)
        self.assertEqual(p2.first, 'Jane')
        self.assertEqual(p2.last, 'Doe')

    def test_implicit_indexing_after_functional_api(self):
        Person = NamedTuple('Person', 'age first last')
        p1 = Person(17, 'John', 'Doe')
        p2 = Person(21, 'Jane', 'Doe')
        self.assertEqual(p1[0], 17)
        self.assertEqual(p1[1], 'John')
        self.assertEqual(p1[2], 'Doe')
        self.assertEqual(p2[0], 21)
        self.assertEqual(p2[1], 'Jane')
        self.assertEqual(p2[2], 'Doe')
        self.assertEqual(p1.age, 17)
        self.assertEqual(p1.first, 'John')
        self.assertEqual(p1.last, 'Doe')
        self.assertEqual(p2.age, 21)
        self.assertEqual(p2.first, 'Jane')
        self.assertEqual(p2.last, 'Doe')

    def test_mixed_indexing_after_functional_api(self):
        Person = NamedTuple('Person', (('age', 0), ('last', 2), ('cars', 3)))
        p1 = Person(17, 'John', 'Doe', 3)
        p2 = Person(21, 'Jane', 'Doe', 9)
        self.assertEqual(p1[0], 17)
        self.assertEqual(p1[1], 'John')
        self.assertEqual(p1[2], 'Doe')
        self.assertEqual(p1[3], 3)
        self.assertEqual(p2[0], 21)
        self.assertEqual(p2[1], 'Jane')
        self.assertEqual(p2[2], 'Doe')
        self.assertEqual(p2[3], 9)
        self.assertEqual(p1.age, 17)
        self.assertEqual(p1.last, 'Doe')
        self.assertEqual(p1.cars, 3)
        self.assertEqual(p2.age, 21)
        self.assertEqual(p2.last, 'Doe')
        self.assertEqual(p2.cars, 9)

    def test_issubclass_after_functional_api(self):
        Person = NamedTuple('Person', 'age first last')
        self.assertTrue(issubclass(Person, NamedTuple))
        self.assertTrue(issubclass(Person, tuple))

    def test_isinstance_after_functional_api(self):
        Person = NamedTuple('Person', 'age first last')
        p1 = Person(17, 'John', 'Doe')
        self.assertTrue(isinstance(p1, Person))
        self.assertTrue(isinstance(p1, NamedTuple))
        self.assertTrue(isinstance(p1, tuple))

    def test_creation_with_all_keywords(self):
        Person = NamedTuple('Person', 'age first last')
        p1 = Person(age=17, first='John', last='Doe')
        self.assertEqual(p1[0], 17)
        self.assertEqual(p1[1], 'John')
        self.assertEqual(p1[2], 'Doe')
        self.assertEqual(p1.age, 17)
        self.assertEqual(p1.first, 'John')
        self.assertEqual(p1.last, 'Doe')

    def test_creation_with_some_keywords(self):
        Person = NamedTuple('Person', 'age first last')
        p1 = Person(17, first='John', last='Doe')
        self.assertEqual(p1[0], 17)
        self.assertEqual(p1[1], 'John')
        self.assertEqual(p1[2], 'Doe')
        self.assertEqual(p1.age, 17)
        self.assertEqual(p1.first, 'John')
        self.assertEqual(p1.last, 'Doe')
        p1 = Person(17, last='Doe', first='John')
        self.assertEqual(p1[0], 17)
        self.assertEqual(p1[1], 'John')
        self.assertEqual(p1[2], 'Doe')
        self.assertEqual(p1.age, 17)
        self.assertEqual(p1.first, 'John')
        self.assertEqual(p1.last, 'Doe')

    def test_custom_new(self):
        class Book(NamedTuple):
            title = 0
            author = 1
            genre = 2
            def __new__(cls, string):
                args = [s.strip() for s in string.split(';')]
                return super(Book, cls).__new__(cls, *tuple(args))
        b1 = Book('The Last Mohican; John Doe; Historical')
        self.assertEqual(b1.title, 'The Last Mohican')
        self.assertEqual(b1.author, 'John Doe')
        self.assertEqual(b1.genre, 'Historical')

    def test_defaults_in_class(self):
        class Character(NamedTuple):
            name = 0
            gender = 1, None, 'male'
            klass = 2, None, 'fighter'
        for char in (
                {'name':'John Doe'},
                {'name':'William Pickney', 'klass':'scholar'},
                {'name':'Sarah Doughtery', 'gender':'female'},
                {'name':'Sissy Moonbeam', 'gender':'female', 'klass':'sorceress'},
                ):
            c = Character(**char)
            for name, value in (('name', None), ('gender','male'), ('klass','fighter')):
                if name in char:
                    value = char[name]
                self.assertEqual(getattr(c, name), value)

    def test_defaults_in_class_that_are_falsey(self):
        class Point(NamedTuple):
            x = 0, 'horizondal coordinate', 0
            y = 1, 'vertical coordinate', 0
        p = Point()
        self.assertEqual(p.x, 0)
        self.assertEqual(p.y, 0)

    def test_pickle_namedtuple_with_module(self):
        if isinstance(LifeForm, Exception):
            raise LifeForm
        lf = LifeForm('this', 'that', 'theother')
        test_pickle_dump_load(self.assertEqual, lf)

    def test_pickle_namedtuple_without_module(self):
        if isinstance(DeathForm, Exception):
            raise DeathForm
        df = DeathForm('sickly green', '2x4', 'foul')
        test_pickle_dump_load(self.assertEqual, df)

    def test_subclassing(self):
        if isinstance(ThatsIt, Exception):
            raise ThatsIt
        ti = ThatsIt('Henry', 'Weinhardt')
        self.assertEqual(ti.blah, 'Henry')
        self.assertTrue(ti.what(), 'Henry')
        test_pickle_dump_load(self.assertEqual, ti)

    def test_contains(self):
        Book = NamedTuple('Book', 'title author genre')
        b = Book('Teckla', 'Steven Brust', 'fantasy')
        self.assertTrue('Teckla' in b)
        self.assertTrue('Steven Brust' in b)
        self.assertTrue('fantasy' in b)

    def test_fixed_size(self):
        class Book(NamedTuple):
            _size_ = TupleSize.fixed
            title = 0
            author = 1
            genre = 2
        b = Book('Teckla', 'Steven Brust', 'fantasy')
        self.assertTrue('Teckla' in b)
        self.assertTrue('Steven Brust' in b)
        self.assertTrue('fantasy' in b)
        self.assertEqual(b.title, 'Teckla')
        self.assertEqual(b.author, 'Steven Brust')
        self.assertRaises(TypeError, Book, 'Teckla', 'Steven Brust')
        self.assertRaises(TypeError, Book, 'Teckla')

    def test_minimum_size(self):
        class Book(NamedTuple):
            _size_ = TupleSize.minimum
            title = 0
            author = 1
        b = Book('Teckla', 'Steven Brust', 'fantasy')
        self.assertTrue('Teckla' in b)
        self.assertTrue('Steven Brust' in b)
        self.assertTrue('fantasy' in b)
        self.assertEqual(b.title, 'Teckla')
        self.assertEqual(b.author, 'Steven Brust')
        b = Book('Teckla', 'Steven Brust')
        self.assertTrue('Teckla' in b)
        self.assertTrue('Steven Brust' in b)
        self.assertEqual(b.title, 'Teckla')
        self.assertEqual(b.author, 'Steven Brust')
        self.assertRaises(TypeError, Book, 'Teckla')

    def test_variable_size(self):
        class Book(NamedTuple):
            _size_ = TupleSize.variable
            title = 0
            author = 1
            genre = 2
        b = Book('Teckla', 'Steven Brust', 'fantasy')
        self.assertTrue('Teckla' in b)
        self.assertTrue('Steven Brust' in b)
        self.assertTrue('fantasy' in b)
        self.assertEqual(b.title, 'Teckla')
        self.assertEqual(b.author, 'Steven Brust')
        self.assertEqual(b.genre, 'fantasy')
        b = Book('Teckla', 'Steven Brust')
        self.assertTrue('Teckla' in b)
        self.assertTrue('Steven Brust' in b)
        self.assertEqual(b.title, 'Teckla')
        self.assertEqual(b.author, 'Steven Brust')
        self.assertRaises(AttributeError, getattr, b, 'genre')
        self.assertRaises(TypeError, Book, title='Teckla', genre='fantasy')
        self.assertRaises(TypeError, Book, author='Steven Brust')

    def test_combining_namedtuples(self):
        class Point(NamedTuple):
            x = 0, 'horizontal coordinate', 1
            y = 1, 'vertical coordinate', -1
        class Color(NamedTuple):
            r = 0, 'red component', 11
            g = 1, 'green component', 29
            b = 2, 'blue component', 37
        Pixel1 = NamedTuple('Pixel', Point+Color, module=__name__)
        class Pixel2(Point, Color):
            "a colored dot"
        class Pixel3(Point):
            r = 2, 'red component', 11
            g = 3, 'green component', 29
            b = 4, 'blue component', 37
        self.assertEqual(Pixel1._fields_, 'x y r g b'.split())
        self.assertEqual(Pixel1.x.__doc__, 'horizontal coordinate')
        self.assertEqual(Pixel1.x.default, 1)
        self.assertEqual(Pixel1.y.__doc__, 'vertical coordinate')
        self.assertEqual(Pixel1.y.default, -1)
        self.assertEqual(Pixel1.r.__doc__, 'red component')
        self.assertEqual(Pixel1.r.default, 11)
        self.assertEqual(Pixel1.g.__doc__, 'green component')
        self.assertEqual(Pixel1.g.default, 29)
        self.assertEqual(Pixel1.b.__doc__, 'blue component')
        self.assertEqual(Pixel1.b.default, 37)
        self.assertEqual(Pixel2._fields_, 'x y r g b'.split())
        self.assertEqual(Pixel2.x.__doc__, 'horizontal coordinate')
        self.assertEqual(Pixel2.x.default, 1)
        self.assertEqual(Pixel2.y.__doc__, 'vertical coordinate')
        self.assertEqual(Pixel2.y.default, -1)
        self.assertEqual(Pixel2.r.__doc__, 'red component')
        self.assertEqual(Pixel2.r.default, 11)
        self.assertEqual(Pixel2.g.__doc__, 'green component')
        self.assertEqual(Pixel2.g.default, 29)
        self.assertEqual(Pixel2.b.__doc__, 'blue component')
        self.assertEqual(Pixel2.b.default, 37)
        self.assertEqual(Pixel3._fields_, 'x y r g b'.split())
        self.assertEqual(Pixel3.x.__doc__, 'horizontal coordinate')
        self.assertEqual(Pixel3.x.default, 1)
        self.assertEqual(Pixel3.y.__doc__, 'vertical coordinate')
        self.assertEqual(Pixel3.y.default, -1)
        self.assertEqual(Pixel3.r.__doc__, 'red component')
        self.assertEqual(Pixel3.r.default, 11)
        self.assertEqual(Pixel3.g.__doc__, 'green component')
        self.assertEqual(Pixel3.g.default, 29)
        self.assertEqual(Pixel3.b.__doc__, 'blue component')
        self.assertEqual(Pixel3.b.default, 37)

    def test_function_api_type(self):
        class Tester(NamedTuple):
            def howdy(self):
                return 'backwards', list(reversed(self))
        Testee = NamedTuple('Testee', 'a c e', type=Tester)
        t = Testee(1, 2, 3)
        self.assertEqual(t.howdy(), ('backwards', [3, 2, 1]))

    def test_asdict(self):
        class Point(NamedTuple):
            x = 0, 'horizontal coordinate', 1
            y = 1, 'vertical coordinate', -1
        class Color(NamedTuple):
            r = 0, 'red component', 11
            g = 1, 'green component', 29
            b = 2, 'blue component', 37
        Pixel = NamedTuple('Pixel', Point+Color, module=__name__)
        pixel = Pixel(99, -101, 255, 128, 0)
        self.assertEqual(pixel._asdict(), {'x':99, 'y':-101, 'r':255, 'g':128, 'b':0})

    def test_make(self):
        class Point(NamedTuple):
            x = 0, 'horizontal coordinate', 1
            y = 1, 'vertical coordinate', -1
        self.assertEqual(Point(4, 5), (4, 5))
        self.assertEqual(Point._make((4, 5)), (4, 5))

    def test_replace(self):
        class Color(NamedTuple):
            r = 0, 'red component', 11
            g = 1, 'green component', 29
            b = 2, 'blue component', 37
        purple = Color(127, 0, 127)
        mid_gray = purple._replace(g=127)
        self.assertEqual(mid_gray, (127, 127, 127))


class TestNamedConstant(TestCase):

    def test_constantness(self):
        class K(NamedConstant):
            PI = 3.141596
            TAU = 2 * PI
        self.assertEqual(K.PI, 3.141596)
        self.assertEqual(K.TAU, 2 * K.PI)
        self.assertRaises(AttributeError, setattr, K, 'PI', 9)

    def test_duplicates(self):
        class CardNumber(NamedConstant):
            ACE      = 11
            TWO      = 2
            THREE    = 3
            FOUR     = 4
            FIVE     = 5
            SIX      = 6
            SEVEN    = 7
            EIGHT    = 8
            NINE     = 9
            TEN      = 10
            JACK     = 10
            QUEEN    = 10
            KING     = 10
        self.assertFalse(CardNumber.TEN is CardNumber.JACK)
        self.assertEqual(CardNumber.TEN, CardNumber.JACK)
        self.assertEqual(CardNumber.TEN, 10)

    def test_extend_constants(self):
        class CardSuit(NamedConstant):
            HEARTS = 1
            SPADES = 2
            DIAMONTS = 3
            CLUBS = 4
        self.assertEqual(CardSuit.HEARTS, 1)
        stars = CardSuit('STARS', 5)
        self.assertIs(stars, CardSuit.STARS)
        self.assertEqual(CardSuit.STARS, 5)

    def test_constant_with_docstring(self):
        class Stuff(NamedConstant):
            Artifact = constant(7, "lucky number!")
            Bowling = 11
            HillWomp = constant(29, 'blah blah')
        self.assertEqual(Stuff.Artifact, 7)
        self.assertEqual(Stuff.Artifact.__doc__, 'lucky number!')
        self.assertEqual(Stuff.Bowling, 11)
        self.assertEqual(Stuff.Bowling.__doc__, None)
        self.assertEqual(Stuff.HillWomp, 29)
        self.assertEqual(Stuff.HillWomp.__doc__, 'blah blah')


class TestMe(TestCase):

    pass


# These are unordered here on purpose to ensure that declaration order
# makes no difference.
CONVERT_TEST_NAME_D = 5
CONVERT_TEST_NAME_C = 5
CONVERT_TEST_NAME_B = 5
CONVERT_TEST_NAME_A = 5  # This one should sort first.
CONVERT_TEST_NAME_E = 5
CONVERT_TEST_NAME_F = 5
CONVERT_TEST_SIGABRT = 4 # and this one
CONVERT_TEST_SIGIOT = 4
CONVERT_TEST_EIO = 7
CONVERT_TEST_EBUS = 7    # and this one

class TestIntEnumConvert(TestCase):
    def test_convert_value_lookup_priority(self):
        test_type = IntEnum._convert(
                'UnittestConvert',
                '__main__',
                filter=lambda x: x.startswith('CONVERT_TEST_'))
        # We don't want the reverse lookup value to vary when there are
        # multiple possible names for a given value.  It should always
        # report the first lexigraphical name in that case.
        self.assertEqual(test_type(5).name, 'CONVERT_TEST_NAME_A')
        self.assertEqual(test_type(4).name, 'CONVERT_TEST_SIGABRT')
        self.assertEqual(test_type(7).name, 'CONVERT_TEST_EBUS')
        self.assertEqual(
                list(test_type),
                [
                    test_type.CONVERT_TEST_SIGABRT,
                    test_type.CONVERT_TEST_NAME_A,
                    test_type.CONVERT_TEST_EBUS,
                    ],
                )

    def test_convert(self):
        test_type = IntEnum._convert(
                'UnittestConvert',
                '__main__',
                filter=lambda x: x.startswith('CONVERT_TEST_'))
        # Ensure that test_type has all of the desired names and values.
        self.assertEqual(test_type.CONVERT_TEST_NAME_F,
                         test_type.CONVERT_TEST_NAME_A)
        self.assertEqual(test_type.CONVERT_TEST_NAME_B, 5)
        self.assertEqual(test_type.CONVERT_TEST_NAME_C, 5)
        self.assertEqual(test_type.CONVERT_TEST_NAME_D, 5)
        self.assertEqual(test_type.CONVERT_TEST_NAME_E, 5)
        # Ensure that test_type only picked up names matching the filter.
        self.assertEqual([name for name in dir(test_type)
                          if name[0:2] not in ('CO', '__')],
                         [], msg='Names other than CONVERT_TEST_* found.')


if __name__ == '__main__':
    unittest.main()
