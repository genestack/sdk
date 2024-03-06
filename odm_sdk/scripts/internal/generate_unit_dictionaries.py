# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2023 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import itertools
import os
from odm_sdk import make_connection_parser

PLACEHOLDER_VAR = 'x'

# Metric prefixes
DIV_PREFIXES = [
    ('femto', 'f', -15),
    ('pico', 'p', -12),
    ('nano', 'n', -9),
    ('micro', 'μ', -6),
    ('milli', 'm', -3),
]
MUL_PREFIXES = [
    ('kilo', 'k', 3),
    ('mega', 'M', 6),
    # ('giga', 'G', 9),
    # ('tera', 'T', 12),
    # ('peta', 'P', 15),
]
NON_C_PREFIXES = [
    ('centi', 'c', -2),
]


class Unit(object):
    """
    Base class for the unit hierarchy. Represents a generic unit.
    """

    def __init__(self, label, name, parent=None, factor=1, conversion_to=None,
                 conversion_from=None):
        """
        :param label: unit label. Used to build relations between units.
        :type label: str
        :param name: unit abbreviation.
        :type name: str
        :param parent: parent unit. Used to convert units between each other.
        :type parent: Unit
        :param factor: a number that can be used to convert current unit to parent unit by multiplying
        :type factor: int | long | float
        :param conversion_to: formula to convert this unit to it's parent unit
        :type conversion_to: str
        :param conversion_from: formula to convert from parent unit to this unit
        :type conversion_from: str
        """

        self.label = label
        self.name = name
        self.parent = parent
        self.factor = factor
        self._conversion_to = conversion_to
        self._conversion_from = conversion_from

    def to_csv(self):
        return (
            self.label,
            self.name,
            '' if self.parent is None else self.parent.label,
            self.conversion_to,
            self.conversion_from
        )

    @property
    def str_factor(self):
        return str(self.factor)

    @property
    def conversion_to(self):
        if self.parent is None:
            return ''
        if self._conversion_to is None:
            f = self.str_factor
            return '%s * %s' % (PLACEHOLDER_VAR, f) if f else ''
        else:
            return self._conversion_to

    @property
    def conversion_from(self):
        if self.parent is None:
            return ''
        if self._conversion_from is None:
            f = self.str_factor
            return '%s / %s' % (PLACEHOLDER_VAR, f) if f else ''
        else:
            return self._conversion_from


class SimpleUnit(Unit):
    """
    Represents units that can be converted between each other by simply multiplying with a power of 10.
    """

    def __init__(self, label, name, parent=None, power_of_10=0):
        super(SimpleUnit, self).__init__(label, name, parent)
        self.power_of_10 = power_of_10

    def apply_prefix(self, prefix, name, power_of_10):
        return SimpleUnit(
            label=prefix + self.label,
            name=name + self.name,
            parent=self if self.parent is None else self.parent,
            power_of_10=self.power_of_10 + power_of_10
        )

    @property
    def str_factor(self):
        return '1' if self.power_of_10 == 0 else '10 ^ %d' % self.power_of_10


class PowerUnit(Unit):
    """
    Represents units that are actually a power of another unit (like square metres).
    """

    def __init__(self, base, power, parent=None):
        def power_to_str():
            if power == 2:
                return 'square'
            elif power == 3:
                return 'cubic'

        super(PowerUnit, self).__init__(
            label='%s %s' % (power_to_str(), base.label),
            name='%s^%d' % (base.name, power),
            parent=parent,
        )
        self.base = base
        self.power = power

    def apply_prefix(self, *args):
        return PowerUnit(
            self.base.apply_prefix(*args),
            self.power,
            self if self.parent is None else self.parent
        )

    @property
    def str_factor(self):
        if self.parent is None:
            return '1'
        if isinstance(self.base, SimpleUnit):
            return '10 ^ %d' % (self.base.power_of_10 * self.power)
        return '(%s) ^ %d' % (super(PowerUnit, self).str_factor, self.power)


class CombinationUnit(Unit):
    """
    Represents units that are expressed as a relation between several units (like metres per second).
    Only division relation is supported now.
    """

    def __init__(self, *args):
        def compute_parent():
            if all([arg.parent is None for arg in args]):
                return None
            return CombinationUnit(*[arg if arg.parent is None else arg.parent for arg in args])

        super(CombinationUnit, self).__init__(
            label=' per '.join(a.label for a in args),
            name='/'.join(a.name if a.name else '1' for a in args),
            parent=compute_parent()
        )
        self.units = args

    @property
    def str_factor(self):
        def get_format_operands():
            return ' / '.join(unit.str_factor for unit in self.units)

        return '' if self.parent is None else '(%s)' % get_format_operands()


class DictionaryGenerator(object):
    HEADERS = ['Label', 'Name', 'Parent', 'To_parent', 'From_parent']

    def __init__(self, dict_name):
        super(DictionaryGenerator, self).__init__()
        self._dict_name = dict_name

    def __enter__(self):
        self._dict_file = open(self._dict_name, 'w')
        self._dict_file.write(','.join(self.HEADERS) + '\n')
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, *args):
        self._dict_file.close()

    def save_unit_array(self, arr):
        self._dict_file.writelines(map(lambda u: ','.join(u.to_csv()) + '\n', arr))

    def save_unit(self, unit):
        self.save_unit_array([unit])


def generate_unit_array(unit, prefixes):
    result = [unit]
    for prefix in prefixes:
        result.append(unit.apply_prefix(*prefix))
    return result


# Predefined units
METRE = SimpleUnit('metre', 'm')
SQ_METRE = PowerUnit(METRE, 2)
CUBIC_METRE = PowerUnit(METRE, 3)
LITRE = SimpleUnit('litre', 'l', parent=CUBIC_METRE, power_of_10=-3)
SECOND = Unit('second', 'sec')
METRES = generate_unit_array(METRE, DIV_PREFIXES + MUL_PREFIXES[:-1] + NON_C_PREFIXES)
SQUARE_METRES = generate_unit_array(SQ_METRE, DIV_PREFIXES + NON_C_PREFIXES)
VOLUMES = generate_unit_array(CUBIC_METRE, DIV_PREFIXES + NON_C_PREFIXES) + generate_unit_array(
    LITRE, DIV_PREFIXES + NON_C_PREFIXES)
TIME_UNITS = [
    SECOND,
    Unit('week', 'w', SECOND, 7 * 24 * 60 * 60),
    Unit('day', 'd', SECOND, 24 * 60 * 60),
    Unit('hour', 'h', SECOND, 60 * 60),
    Unit('minute', 'min', SECOND, 60)
]


def get_combinations(*args):
    return (CombinationUnit(*combination) for combination in itertools.product(*args))


def generate_dose_dict(dict_name):
    gram = SimpleUnit('gram', 'g')
    mole = SimpleUnit('mole', 'mol')
    molar = SimpleUnit('molar', 'M')

    weights = generate_unit_array(gram, DIV_PREFIXES + MUL_PREFIXES[:-1])
    moles = generate_unit_array(mole, DIV_PREFIXES)
    molars = generate_unit_array(molar, DIV_PREFIXES)
    with DictionaryGenerator(dict_name) as dictionary:
        dictionary.save_unit_array(weights)
        dictionary.save_unit_array(METRES)
        dictionary.save_unit_array(SQUARE_METRES)
        dictionary.save_unit_array(VOLUMES)
        dictionary.save_unit_array(TIME_UNITS)
        dictionary.save_unit_array(moles)
        dictionary.save_unit_array(molars)

        dictionary.save_unit_array(get_combinations(weights, weights))
        dictionary.save_unit_array(get_combinations(weights, VOLUMES))
        dictionary.save_unit_array(get_combinations(VOLUMES, weights))
        dictionary.save_unit_array(get_combinations(VOLUMES, VOLUMES))
        dictionary.save_unit_array(get_combinations(weights, TIME_UNITS))
        dictionary.save_unit_array(get_combinations(weights, SQUARE_METRES))
        dictionary.save_unit_array(get_combinations(weights, weights, TIME_UNITS))
        dictionary.save_unit_array(get_combinations(moles, weights))


def generate_energy_dict(dict_name):
    sievert = SimpleUnit('sievert', 'Sv')
    watt = SimpleUnit('watt', 'W')
    gray = SimpleUnit('gray', 'Gy')
    kelvin = Unit('kelvin', 'K')
    joule = SimpleUnit('joule', 'J')
    becquerel = SimpleUnit('becquerel', 'Bq')
    rad = SimpleUnit('rad', 'rad')
    einstein = SimpleUnit('einstein', 'E')
    lux = SimpleUnit('lux', 'lx')
    pascal = SimpleUnit('pascal', 'Pa')

    watts = generate_unit_array(watt, DIV_PREFIXES + MUL_PREFIXES)
    grays = generate_unit_array(gray, DIV_PREFIXES)
    temperatures = (
        kelvin,
        Unit(
            'degree Celsius', '°C', kelvin,
            conversion_to='%s + 273.15' % PLACEHOLDER_VAR,
            conversion_from='%s - 273.15' % PLACEHOLDER_VAR
        ),
        Unit(
            'degree Fahrenheit', '°F', kelvin,
            conversion_to='(%s + 459.67) * 5 / 9' % PLACEHOLDER_VAR,
            conversion_from='%s * 9 / 5 - 459.67' % PLACEHOLDER_VAR
        )
    )
    joules = generate_unit_array(joule, DIV_PREFIXES)
    becquerels = generate_unit_array(becquerel, MUL_PREFIXES)
    einsteins = generate_unit_array(einstein, MUL_PREFIXES)
    with DictionaryGenerator(dict_name) as dictionary:
        dictionary.save_unit_array(watts)
        dictionary.save_unit_array(grays)
        dictionary.save_unit_array(temperatures)
        dictionary.save_unit_array(joules)
        dictionary.save_unit_array(becquerels)

        dictionary.save_unit_array(generate_unit_array(sievert, DIV_PREFIXES))
        dictionary.save_unit_array(generate_unit_array(rad, DIV_PREFIXES))
        dictionary.save_unit_array(generate_unit_array(lux, DIV_PREFIXES + MUL_PREFIXES))
        dictionary.save_unit_array(generate_unit_array(pascal, DIV_PREFIXES + MUL_PREFIXES))

        dictionary.save_unit_array(get_combinations(watts, SQUARE_METRES))
        dictionary.save_unit_array(get_combinations(grays, TIME_UNITS))
        dictionary.save_unit_array(get_combinations(joules, SQUARE_METRES))
        dictionary.save_unit_array(get_combinations(becquerels, VOLUMES))
        dictionary.save_unit_array(get_combinations(einsteins, TIME_UNITS, SQUARE_METRES))


def generate_length_dict(dict_name):
    with DictionaryGenerator(dict_name) as dictionary:
        dictionary.save_unit_array(METRES)
        dictionary.save_unit(Unit('inch', 'in', METRE, 0.0254))


def generate_time_dict(dict_name):
    month = Unit('month', 'm', SECOND, 24 * 60 * 60 * 365 / 12)
    year = Unit('year', 'y', SECOND, 24 * 60 * 60 * 365)
    with DictionaryGenerator(dict_name) as dictionary:
        dictionary.save_unit_array(TIME_UNITS)
        dictionary.save_unit(month)
        dictionary.save_unit(year)
        dictionary.save_unit(Unit('hertz', 'Hz'))

        dictionary.save_unit(CombinationUnit(TIME_UNITS[0], TIME_UNITS[0]))
        dictionary.save_unit(CombinationUnit(TIME_UNITS[3], TIME_UNITS[2]))


def generate_bio_counts_dict(dict_name):
    colony_forming_unit = Unit('colony_forming_unit', '')
    cells = Unit('cells', '')

    with DictionaryGenerator(dict_name) as dictionary:
        dictionary.save_unit(colony_forming_unit)

        dictionary.save_unit_array(get_combinations([colony_forming_unit], TIME_UNITS))
        dictionary.save_unit_array(get_combinations([colony_forming_unit], VOLUMES))
        dictionary.save_unit_array(get_combinations([cells], VOLUMES))


def main():

    args = get_args()

    if args.destination_path:
        destination_path = args.destination_path
    else:
        destination_path = os.path.join(os.getcwd(), 'generated')

    if not os.path.exists(destination_path):
        os.mkdir(destination_path)

    def make(generator, basename):
        """Make dictionary and return path of created file."""
        path = os.path.join(destination_path, basename)
        generator(path)
        return path

    make(generate_dose_dict, 'units_dose.csv')
    make(generate_energy_dict, 'units_energy.csv')
    make(generate_length_dict, 'units_length.csv')
    make(generate_time_dict, 'units_time.csv')
    make(generate_bio_counts_dict, 'units_bio_counts.csv')


def get_args():
    parser = make_connection_parser()
    parser.add_argument('--destination-path',
                        help="[Optional] Path to put generated dictionaries, "
                        "The path will be generated automatically when the parameter is not specified. ")

    return parser.parse_args()


if __name__ == '__main__':
    main()
