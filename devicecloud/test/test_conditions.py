import unittest
import datetime

from devicecloud.conditions import Attribute


class TestConditions(unittest.TestCase):

    def test_gt(self):
        a = Attribute("a")
        self.assertEqual((a > 21).compile(), "a>'21'")

    def test_lt(self):
        a = Attribute("a")
        self.assertEqual((a < 25).compile(), "a<'25'")

    def test_eq(self):
        a = Attribute("a")
        self.assertEqual((a == "a string").compile(), "a='a string'")

    def test_like(self):
        a = Attribute("a")
        self.assertEqual(a.like(r"%.txt").compile(), "a like '%.txt'")

    def test_and(self):
        a = Attribute("a")
        b = Attribute("b")
        expr = (a > 21) & (b == "Amsterdam")
        self.assertEqual(expr.compile(), "a>'21' and b='Amsterdam'")

    def test_or(self):
        a = Attribute("a")
        b = Attribute("b")
        expr = (a.like("%.csv")) | (b < 1024)
        self.assertEqual(expr.compile(), "a like '%.csv' or b<'1024'")

    def test_datacmp(self):
        a = Attribute("a")
        self.assertEqual((a < datetime.datetime(2014, 7, 7)).compile(),
                         "a<'2014-07-07T00:00:00Z'")

    def test_multi_combination(self):
        a = Attribute("a")
        self.assertEqual(((a > 1) & (a > 2) & (a > 3)).compile(),
                         "a>'1' and a>'2' and a>'3'")

if __name__ == '__main__':
    unittest.main()
