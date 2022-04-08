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
        # two nan-values to be close or equal, we have to jump through some hoops.
        # Hence, for the comparison between the original and the treated array,
        # we replace nan-values in both arrays with the same but random number.
        # If there would not be the exact same nan-values at the exact same places, any comparison
        # would thus fail:
        nan_replacement = np.random.rand()
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
        nan_replacement = np.random.rand()
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
