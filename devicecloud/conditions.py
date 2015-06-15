# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.

"""Module with functionality for building queries against cloud resources

This functionality is somewhat poorly documented in the device cloud documentation
in the `Compound Queries <http://ftp1.digi.com/support/documentation/html/90002008/90002008_P/Default.htm#ProgrammingTopics/ResourceConventions.htm#CompQueries%3FTocPath%3DDevice%20Cloud%20Programming%20Guide%7CResource%20Conventions%7C_____3>`_
section.

"""
import datetime

from devicecloud.util import isoformat, to_none_or_dt


def _quoted(value):
    """Return a single-quoted and escaped (percent-encoded) version of value

    This function will also perform transforms of known data types to a representation
    that will be handled by the device cloud.  For instance, datetime objects will be
    converted to ISO8601.

    """
    if isinstance(value, datetime.datetime):
        value = isoformat(to_none_or_dt(value))
    else:
        value = str(value)

    return "'{}'".format(value)



class Expression(object):
    r"""A condition is an evaluable filter

    Examples of conditions would include the following:
    * fdType='file'
    * fdName like 'sample%gas'

    Conditions may also be compound.  E.g.
    * (fdType='file' and fdName like 'sample%gas')

    """

    def __init__(self):
        pass

    def __and__(self, rhs):
        return Combination(self, " and ", rhs)

    def __or__(self, rhs):
        return Combination(self, " or ", rhs)

    and_ = __and__  # alternate syntax
    or_ = __or__  # alternate syntax

    def compile(self):
        raise NotImplementedError("Should be implemented in subclass")


class Combination(Expression):
    """A combination combines two expressions"""

    def __init__(self, lhs, sep, rhs):
        Expression.__init__(self)
        self.lhs = lhs
        self.sep = sep
        self.rhs = rhs

    def __str__(self):
        return self.compile()

    def compile(self):
        """Compile this expression into a query string"""
        return "{lhs}{sep}{rhs}".format(
            lhs=self.lhs.compile(),
            sep=self.sep,
            rhs=self.rhs.compile(),
        )


class Comparison(Expression):
    """A comparison is an expression comparing an attribute with a value using some operator"""

    def __init__(self, attribute, sep, value):
        Expression.__init__(self)
        self.attribute = attribute
        self.sep = sep
        self.value = value

    def __str__(self):
        return self.compile()

    def compile(self):
        """Compile this expression into a query string"""
        return "{attribute}{sep}{value}".format(
            attribute=self.attribute,
            sep=self.sep,
            value=_quoted(self.value)
        )


class Attribute(object):
    """An attribute is a piece of data on which we may perform comparisons

    Comparisons performed to attributes will in turn generate new
    :class:`.Comparison` instances.
    """

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __gt__(self, value):
        return Comparison(self, '>', value)

    def __lt__(self, value):
        return Comparison(self, '<', value)

    def __eq__(self, value):
        return Comparison(self, '=', value)

    def like(self, value):
        return Comparison(self, ' like ', value)
