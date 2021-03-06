
import random
import unittest

from decimal import Decimal
from fractions import Fraction

import quickselect as statistics


class NumericTestCase(unittest.TestCase):
    """Unit test class for numeric work.
    This subclasses TestCase. In addition to the standard method
    ``TestCase.assertAlmostEqual``,  ``assertApproxEqual`` is provided.
    """
    # By default, we expect exact equality, unless overridden.
    tol = rel = 0

    def assertApproxEqual(
            self, first, second, tol=None, rel=None, msg=None
            ):
        """Test passes if ``first`` and ``second`` are approximately equal.
        This test passes if ``first`` and ``second`` are equal to
        within ``tol``, an absolute error, or ``rel``, a relative error.
        If either ``tol`` or ``rel`` are None or not given, they default to
        test attributes of the same name (by default, 0).
        The objects may be either numbers, or sequences of numbers. Sequences
        are tested element-by-element.
        >>> class MyTest(NumericTestCase):
        ...     def test_number(self):
        ...         x = 1.0/6
        ...         y = sum([x]*6)
        ...         self.assertApproxEqual(y, 1.0, tol=1e-15)
        ...     def test_sequence(self):
        ...         a = [1.001, 1.001e-10, 1.001e10]
        ...         b = [1.0, 1e-10, 1e10]
        ...         self.assertApproxEqual(a, b, rel=1e-3)
        ...
        >>> import unittest
        >>> from io import StringIO  # Suppress test runner output.
        >>> suite = unittest.TestLoader().loadTestsFromTestCase(MyTest)
        >>> unittest.TextTestRunner(stream=StringIO()).run(suite)
        <unittest.runner.TextTestResult run=2 errors=0 failures=0>
        """
        if tol is None:
            tol = self.tol
        if rel is None:
            rel = self.rel
        if (
                isinstance(first, collections.abc.Sequence) and
                isinstance(second, collections.abc.Sequence)
            ):
            check = self._check_approx_seq
        else:
            check = self._check_approx_num
        check(first, second, tol, rel, msg)

    def _check_approx_seq(self, first, second, tol, rel, msg):
        if len(first) != len(second):
            standardMsg = (
                "sequences differ in length: %d items != %d items"
                % (len(first), len(second))
                )
            msg = self._formatMessage(msg, standardMsg)
            raise self.failureException(msg)
        for i, (a,e) in enumerate(zip(first, second)):
            self._check_approx_num(a, e, tol, rel, msg, i)

    def _check_approx_num(self, first, second, tol, rel, msg, idx=None):
        if approx_equal(first, second, tol, rel):
            # Test passes. Return early, we are done.
            return None
        # Otherwise we failed.
        standardMsg = self._make_std_err_msg(first, second, tol, rel, idx)
        msg = self._formatMessage(msg, standardMsg)
        raise self.failureException(msg)

    @staticmethod
    def _make_std_err_msg(first, second, tol, rel, idx):
        # Create the standard error message for approx_equal failures.
        assert first != second
        template = (
            '  %r != %r\n'
            '  values differ by more than tol=%r and rel=%r\n'
            '  -> absolute error = %r\n'
            '  -> relative error = %r'
            )
        if idx is not None:
            header = 'numeric sequences first differ at index %d.\n' % idx
            template = header + template
        # Calculate actual errors:
        abs_err, rel_err = _calc_errors(first, second)
        return template % (first, second, tol, rel, abs_err, rel_err)


class UnivariateTypeMixin:
    """Mixin class for type-conserving functions.
    This mixin class holds test(s) for functions which conserve the type of
    individual data points. E.g. the mean of a list of Fractions should itself
    be a Fraction.
    Not all tests to do with types need go in this class. Only those that
    rely on the function returning the same type as its input data.
    """
    def prepare_types_for_conservation_test(self):
        """Return the types which are expected to be conserved."""
        class MyFloat(float):
            def __truediv__(self, other):
                return type(self)(super().__truediv__(other))
            def __rtruediv__(self, other):
                return type(self)(super().__rtruediv__(other))
            def __sub__(self, other):
                return type(self)(super().__sub__(other))
            def __rsub__(self, other):
                return type(self)(super().__rsub__(other))
            def __pow__(self, other):
                return type(self)(super().__pow__(other))
            def __add__(self, other):
                return type(self)(super().__add__(other))
            __radd__ = __add__
            def __mul__(self, other):
                return type(self)(super().__mul__(other))
            __rmul__ = __mul__
        return (float, Decimal, Fraction, MyFloat)

    def test_types_conserved(self):
        # Test that functions keeps the same type as their data points.
        # (Excludes mixed data types.) This only tests the type of the return
        # result, not the value.
        data = self.prepare_data()
        for kind in self.prepare_types_for_conservation_test():
            d = [kind(x) for x in data]
            result = self.func(d)
            self.assertIs(type(result), kind)


class UnivariateCommonMixin:
    # Common tests for most univariate functions that take a data argument.

    def test_no_args(self):
        # Fail if given no arguments.
        self.assertRaises(TypeError, self.func)

    def test_empty_data(self):
        # Fail when the data argument (first argument) is empty.
        for empty in ([], (), iter([])):
            self.assertRaises(statistics.StatisticsError, self.func, empty)

    def prepare_data(self):
        """Return int data for various tests."""
        data = list(range(10))
        while data == sorted(data):
            random.shuffle(data)
        return data

    def test_no_inplace_modifications(self):
        # Test that the function does not modify its input data.
        data = self.prepare_data()
        assert len(data) != 1  # Necessary to avoid infinite loop.
        assert data != sorted(data)
        saved = data[:]
        assert data is not saved
        _ = self.func(data)
        self.assertListEqual(data, saved, "data has been modified")

    def test_order_doesnt_matter(self):
        # Test that the order of data points doesn't change the result.

        # CAUTION: due to floating point rounding errors, the result actually
        # may depend on the order. Consider this test representing an ideal.
        # To avoid this test failing, only test with exact values such as ints
        # or Fractions.
        data = [1, 2, 3, 3, 3, 4, 5, 6]*100
        expected = self.func(data)
        random.shuffle(data)
        actual = self.func(data)
        self.assertEqual(expected, actual)

    def test_type_of_data_collection(self):
        # Test that the type of iterable data doesn't effect the result.
        class MyList(list):
            pass
        class MyTuple(tuple):
            pass
        def generator(data):
            return (obj for obj in data)
        data = self.prepare_data()
        expected = self.func(data)
        for kind in (list, tuple, iter, MyList, MyTuple, generator):
            result = self.func(kind(data))
            self.assertEqual(result, expected)

    def test_range_data(self):
        # Test that functions work with range objects.
        data = range(20, 50, 3)
        expected = self.func(list(data))
        self.assertEqual(self.func(data), expected)

    def test_bad_arg_types(self):
        # Test that function raises when given data of the wrong type.

        # Don't roll the following into a loop like this:
        #   for bad in list_of_bad:
        #       self.check_for_type_error(bad)
        #
        # Since assertRaises doesn't show the arguments that caused the test
        # failure, it is very difficult to debug these test failures when the
        # following are in a loop.
        self.check_for_type_error(None)
        self.check_for_type_error(23)
        self.check_for_type_error(42.0)
        self.check_for_type_error(object())

    def check_for_type_error(self, *args):
        self.assertRaises(TypeError, self.func, *args)

    def test_type_of_data_element(self):
        # Check the type of data elements doesn't affect the numeric result.
        # This is a weaker test than UnivariateTypeMixin.testTypesConserved,
        # because it checks the numeric result by equality, but not by type.
        class MyFloat(float):
            def __truediv__(self, other):
                return type(self)(super().__truediv__(other))
            def __add__(self, other):
                return type(self)(super().__add__(other))
            __radd__ = __add__

        raw = self.prepare_data()
        expected = self.func(raw)
        for kind in (float, MyFloat, Decimal, Fraction):
            data = [kind(x) for x in raw]
            result = type(expected)(self.func(data))
            self.assertEqual(result, expected)


class AverageMixin(UnivariateCommonMixin):
    # Mixin class holding common tests for averages.

    def test_single_value(self):
        # Average of a single value is the value itself.
        for x in (23, 42.5, 1.3e15, Fraction(15, 19), Decimal('0.28')):
            self.assertEqual(self.func([x]), x)

    def prepare_values_for_repeated_single_test(self):
        return (3.5, 17, 2.5e15, Fraction(61, 67), Decimal('4.9712'))

    def test_repeated_single_value(self):
        # The average of a single repeated value is the value itself.
        for x in self.prepare_values_for_repeated_single_test():
            for count in (2, 5, 10, 20):
                with self.subTest(x=x, count=count):
                    data = [x]*count
                    self.assertEqual(self.func(data), x)


class TestMedian(NumericTestCase, AverageMixin):
    # Common tests for median and all median.* functions.
    def setUp(self):
        self.func = statistics.median

    def prepare_data(self):
        """Overload method from UnivariateCommonMixin."""
        data = super().prepare_data()
        if len(data)%2 != 1:
            data.append(2)
        return data

    def test_even_ints(self):
        # Test median with an even number of int data points.
        data = [1, 2, 3, 4, 5, 6]
        assert len(data)%2 == 0
        self.assertEqual(self.func(data), 3.5)

    def test_odd_ints(self):
        # Test median with an odd number of int data points.
        data = [1, 2, 3, 4, 5, 6, 9]
        assert len(data)%2 == 1
        self.assertEqual(self.func(data), 4)

    def test_odd_fractions(self):
        # Test median works with an odd number of Fractions.
        F = Fraction
        data = [F(1, 7), F(2, 7), F(3, 7), F(4, 7), F(5, 7)]
        assert len(data)%2 == 1
        random.shuffle(data)
        self.assertEqual(self.func(data), F(3, 7))

    def test_even_fractions(self):
        # Test median works with an even number of Fractions.
        F = Fraction
        data = [F(1, 7), F(2, 7), F(3, 7), F(4, 7), F(5, 7), F(6, 7)]
        assert len(data)%2 == 0
        random.shuffle(data)
        self.assertEqual(self.func(data), F(1, 2))

    def test_odd_decimals(self):
        # Test median works with an odd number of Decimals.
        D = Decimal
        data = [D('2.5'), D('3.1'), D('4.2'), D('5.7'), D('5.8')]
        assert len(data)%2 == 1
        random.shuffle(data)
        self.assertEqual(self.func(data), D('4.2'))

    def test_even_decimals(self):
        # Test median works with an even number of Decimals.
        D = Decimal
        data = [D('1.2'), D('2.5'), D('3.1'), D('4.2'), D('5.7'), D('5.8')]
        assert len(data)%2 == 0
        random.shuffle(data)
        self.assertEqual(self.func(data), D('3.65'))


class TestMedianDataType(NumericTestCase, UnivariateTypeMixin):
    # Test conservation of data element type for median.
    def setUp(self):
        self.func = statistics.median

    def prepare_data(self):
        data = list(range(15))
        assert len(data)%2 == 1
        while data == sorted(data):
            random.shuffle(data)
        return data


# class TestMedianLow(TestMedian, UnivariateTypeMixin):
#     def setUp(self):
#         self.func = statistics.median_low

#     def test_even_ints(self):
#         # Test median_low with an even number of ints.
#         data = [1, 2, 3, 4, 5, 6]
#         assert len(data)%2 == 0
#         self.assertEqual(self.func(data), 3)

#     def test_even_fractions(self):
#         # Test median_low works with an even number of Fractions.
#         F = Fraction
#         data = [F(1, 7), F(2, 7), F(3, 7), F(4, 7), F(5, 7), F(6, 7)]
#         assert len(data)%2 == 0
#         random.shuffle(data)
#         self.assertEqual(self.func(data), F(3, 7))

#     def test_even_decimals(self):
#         # Test median_low works with an even number of Decimals.
#         D = Decimal
#         data = [D('1.1'), D('2.2'), D('3.3'), D('4.4'), D('5.5'), D('6.6')]
#         assert len(data)%2 == 0
#         random.shuffle(data)
#         self.assertEqual(self.func(data), D('3.3'))


# class TestMedianHigh(TestMedian, UnivariateTypeMixin):
#     def setUp(self):
#         self.func = statistics.median_high

#     def test_even_ints(self):
#         # Test median_high with an even number of ints.
#         data = [1, 2, 3, 4, 5, 6]
#         assert len(data)%2 == 0
#         self.assertEqual(self.func(data), 4)

#     def test_even_fractions(self):
#         # Test median_high works with an even number of Fractions.
#         F = Fraction
#         data = [F(1, 7), F(2, 7), F(3, 7), F(4, 7), F(5, 7), F(6, 7)]
#         assert len(data)%2 == 0
#         random.shuffle(data)
#         self.assertEqual(self.func(data), F(4, 7))

#     def test_even_decimals(self):
#         # Test median_high works with an even number of Decimals.
#         D = Decimal
#         data = [D('1.1'), D('2.2'), D('3.3'), D('4.4'), D('5.5'), D('6.6')]
#         assert len(data)%2 == 0
#         random.shuffle(data)
#         self.assertEqual(self.func(data), D('4.4'))


# class TestMedianGrouped(TestMedian):
#     # Test median_grouped.
#     # Doesn't conserve data element types, so don't use TestMedianType.
#     def setUp(self):
#         self.func = statistics.median_grouped

#     def test_odd_number_repeated(self):
#         # Test median.grouped with repeated median values.
#         data = [12, 13, 14, 14, 14, 15, 15]
#         assert len(data)%2 == 1
#         self.assertEqual(self.func(data), 14)
#         #---
#         data = [12, 13, 14, 14, 14, 14, 15]
#         assert len(data)%2 == 1
#         self.assertEqual(self.func(data), 13.875)
#         #---
#         data = [5, 10, 10, 15, 20, 20, 20, 20, 25, 25, 30]
#         assert len(data)%2 == 1
#         self.assertEqual(self.func(data, 5), 19.375)
#         #---
#         data = [16, 18, 18, 18, 18, 20, 20, 20, 22, 22, 22, 24, 24, 26, 28]
#         assert len(data)%2 == 1
#         self.assertApproxEqual(self.func(data, 2), 20.66666667, tol=1e-8)

#     def test_even_number_repeated(self):
#         # Test median.grouped with repeated median values.
#         data = [5, 10, 10, 15, 20, 20, 20, 25, 25, 30]
#         assert len(data)%2 == 0
#         self.assertApproxEqual(self.func(data, 5), 19.16666667, tol=1e-8)
#         #---
#         data = [2, 3, 4, 4, 4, 5]
#         assert len(data)%2 == 0
#         self.assertApproxEqual(self.func(data), 3.83333333, tol=1e-8)
#         #---
#         data = [2, 3, 3, 4, 4, 4, 5, 5, 5, 5, 6, 6]
#         assert len(data)%2 == 0
#         self.assertEqual(self.func(data), 4.5)
#         #---
#         data = [3, 4, 4, 4, 5, 5, 5, 5, 6, 6]
#         assert len(data)%2 == 0
#         self.assertEqual(self.func(data), 4.75)

#     def test_repeated_single_value(self):
#         # Override method from AverageMixin.
#         # Yet again, failure of median_grouped to conserve the data type
#         # causes me headaches :-(
#         for x in (5.3, 68, 4.3e17, Fraction(29, 101), Decimal('32.9714')):
#             for count in (2, 5, 10, 20):
#                 data = [x]*count
#                 self.assertEqual(self.func(data), float(x))

#     def test_odd_fractions(self):
#         # Test median_grouped works with an odd number of Fractions.
#         F = Fraction
#         data = [F(5, 4), F(9, 4), F(13, 4), F(13, 4), F(17, 4)]
#         assert len(data)%2 == 1
#         random.shuffle(data)
#         self.assertEqual(self.func(data), 3.0)

#     def test_even_fractions(self):
#         # Test median_grouped works with an even number of Fractions.
#         F = Fraction
#         data = [F(5, 4), F(9, 4), F(13, 4), F(13, 4), F(17, 4), F(17, 4)]
#         assert len(data)%2 == 0
#         random.shuffle(data)
#         self.assertEqual(self.func(data), 3.25)

#     def test_odd_decimals(self):
#         # Test median_grouped works with an odd number of Decimals.
#         D = Decimal
#         data = [D('5.5'), D('6.5'), D('6.5'), D('7.5'), D('8.5')]
#         assert len(data)%2 == 1
#         random.shuffle(data)
#         self.assertEqual(self.func(data), 6.75)

#     def test_even_decimals(self):
#         # Test median_grouped works with an even number of Decimals.
#         D = Decimal
#         data = [D('5.5'), D('5.5'), D('6.5'), D('6.5'), D('7.5'), D('8.5')]
#         assert len(data)%2 == 0
#         random.shuffle(data)
#         self.assertEqual(self.func(data), 6.5)
#         #---
#         data = [D('5.5'), D('5.5'), D('6.5'), D('7.5'), D('7.5'), D('8.5')]
#         assert len(data)%2 == 0
#         random.shuffle(data)
#         self.assertEqual(self.func(data), 7.0)

#     def test_interval(self):
#         # Test median_grouped with interval argument.
#         data = [2.25, 2.5, 2.5, 2.75, 2.75, 3.0, 3.0, 3.25, 3.5, 3.75]
#         self.assertEqual(self.func(data, 0.25), 2.875)
#         data = [2.25, 2.5, 2.5, 2.75, 2.75, 2.75, 3.0, 3.0, 3.25, 3.5, 3.75]
#         self.assertApproxEqual(self.func(data, 0.25), 2.83333333, tol=1e-8)
#         data = [220, 220, 240, 260, 260, 260, 260, 280, 280, 300, 320, 340]
#         self.assertEqual(self.func(data, 20), 265.0)

#     def test_data_type_error(self):
#         # Test median_grouped with str, bytes data types for data and interval
#         data = ["", "", ""]
#         self.assertRaises(TypeError, self.func, data)
#         #---
#         data = [b"", b"", b""]
#         self.assertRaises(TypeError, self.func, data)
#         #---
#         data = [1, 2, 3]
#         interval = ""
#         self.assertRaises(TypeError, self.func, data, interval)
#         #---
#         data = [1, 2, 3]
#         interval = b""
#         self.assertRaises(TypeError, self.func, data, interval)


if __name__ == '__main__':
    unittest.main()
