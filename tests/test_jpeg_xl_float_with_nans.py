"""Unit tests for satip.jpeg_xl_float_with_nans."""

import unittest

import numpy as np

from satip.jpeg_xl_float_with_nans import (
    LOWER_BOUND_FOR_REAL_PIXELS,
    NAN_VALUE,
    JpegXlFloatWithNaNs,
    decode_nans,
    encode_nans,
)


class TestJpegXlFloatWithNaNs(unittest.TestCase):
    """Test class for unittest for the class methods and the functions.

    We only test our home-written functions.
    The two similarly named class functions encode and decode are mostly wrappers
    around our home-written function output piped into an external library.
    Testing the functionality of the external functions is out of scope.
    """

    def setUp(self) -> None:  # noqa D102
        # Define synthetic input array and the expected target array:
        self.buf = np.asarray([np.nan, 0.0, 0.5, 1.0], dtype=np.float32)
        self.encoded = np.asarray(
            [NAN_VALUE, LOWER_BOUND_FOR_REAL_PIXELS, 0.5 * (1 + LOWER_BOUND_FOR_REAL_PIXELS), 1.0],
            dtype=np.float32,
        )

        self.jpegxl = JpegXlFloatWithNaNs()

        return super().setUp()

    def test_encode(self):
        """Tests the encoding function.

        After encoding the raw array, the nan-values should be gone and the
        real values should be transformed to the range specified by the
        constants imported from the source code. See there for more details.
        """
        # Check that the enconded buffer matches the expected target
        # (attention: use a copy of the originals!):
        self.assertTrue(np.isclose(encode_nans(self.buf.copy()), self.encoded).all())

    def test_decode(self):
        """Tests the decoding function.

        When taking what was previously the encoded array and decode it,
        we expect to get the original buf-array back again.
        """
        # As np.nan != np.nan (!) and thus np.isclose or array comparison do not consider
        # two nan-values to be close or equal, we have to replace all nan-values with
        # a numeric value before comparison. This numeric value should be one that
        # can not be created via decoding (e.g. a negative number).
        nan_replacement = -3.14
        self.assertTrue(
            np.isclose(
                np.nan_to_num(self.buf, nan_replacement),
                np.nan_to_num(decode_nans(self.encoded.copy()), nan_replacement),
            ).all()
        )

    def test_class_roundtrip(self):
        """Tests the class-defined wrappers around our home-written functions.

        We test whether a back-and-forth transformation (nested encode-decode)
        will give us back our original input value.
        """
        reshaped_buf = self.buf.copy().reshape((1, -1, 1))

        roundtrip_result = self.jpegxl.decode(self.jpegxl.encode(reshaped_buf.copy()))

        # For reasons explained in the decoding test, we have to manually replace
        # the nan-values to make them comparable:
        nan_replacement = -3.14
        reshaped_buf = np.nan_to_num(reshaped_buf, nan_replacement)
        roundtrip_result = np.nan_to_num(roundtrip_result, nan_replacement)

        # When we do the comparison, we have to be very lenient, as the external library
        # will have worked its compression magic, so values will not completely align.
        # Also, going back and forth removes the information about the channel number
        # in our test case (presumably b/c we here only have one channel for simplicity's sake).
        # So we have to reshape both:
        self.assertTrue(
            np.isclose(reshaped_buf.reshape((-1)), roundtrip_result.reshape((-1)), atol=0.1).all()
        )

    def test_consistent_init_params(self):
        """The JpegXLFloat-class has to be initialised with specific parameter combinations.

        Stuff that is allowed:
        1. If lossless = None, then everything is allowed.
        2. If lossless = True, then level has to be None and distance has to be None or 0
        3. If lossless = False, then everything is allowed.

        To test this, we will try various parameters and see that the class gets
        initialised properly, w/o throwing any errors.
        """

        # Sub-case 1:
        self.assertTrue(JpegXlFloatWithNaNs(lossless=None, level="very_high", distance=-10))

        # Sub-case 2:
        with self.assertRaises(AssertionError):
            JpegXlFloatWithNaNs(lossless=True, level=1, distance=1)

        with self.assertRaises(AssertionError):
            JpegXlFloatWithNaNs(lossless=True, level=None, distance=1)

        with self.assertRaises(AssertionError):
            JpegXlFloatWithNaNs(lossless=True, level=2, distance=0)

        # Sub-case 3:
        self.assertTrue(JpegXlFloatWithNaNs(lossless=False))
