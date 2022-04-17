"""Tests script.generate_test_plots and by extension satip.utils.

The reason why we are doing it like this instead of separately testing
utils is that
a) there are very weird installation issues yet unclear how to solve
b) script.generate_test_plot is our user-facing try-it-out-script,
   so we would like to make sure that one runs correctly. As that also
   calls pretty much all of utils, we can kill two birds with one stone
   here and also link generate_test_plot-tests to the utils-tests.
   No need to test satip.utils twice.

In case you want to check the separate utils-tests, you can do so in
disabled_utils.py.
"""
import unittest

from scripts.generate_test_plots import generate_test_plots


class TestPlotGeneration(unittest.TestCase):  # noqa
    def test_plot_generation(self):  # noqa
        # Run the function and assert that it does not raise any errors.
        self.assertIsNone(generate_test_plots())
