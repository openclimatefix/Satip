"""Thin wrapper around imagecodecs.JpegXl.
"""
from typing import Optional

import numpy as np
from imagecodecs.numcodecs import JpegXl
from numcodecs.registry import register_codec

# See the docs in `encode_nans` for an explanation of what these consts do.
# Also, please be aware that for sensical results, the values should follow the ordering:
# LOWER_BOUND_FOR_REAL_PIXELS > NAN_THRESHOLD > NAN_VALUE.
# Otherwise encoding and decoding back will lead to valid pixels being marked NaN.
LOWER_BOUND_FOR_REAL_PIXELS = 0.075
NAN_THRESHOLD = 0.05
NAN_VALUE = 0.025


class JpegXlFloatWithNaNs(JpegXl):
    """Thin wrapper around imagecodecs.JpegXl for floats with NaNs."""

    codec_id = "imagecodecs_jpegxl_float_with_nans"

    def __init__(
        self,
        lossless: Optional[bool] = None,
        distance: Optional[int] = None,
        level: Optional[int] = None,
        decodingspeed: Optional[float] = None,
        *args,
        **kwargs,
    ):
        """Initialise.

        This __init__ function is a simple hack to make the JpegXl compressor in the currently
        released version of imagecodecs (version 2021.11.20) look like the version in development.
        (We can't simply use the version in development because the imagecodecs author does not
        develop on GitHub. The imagecodecs authors just uses GitHub as one of several mechanisms
        to release imagecodecs.)

        See https://github.com/cgohlke/imagecodecs/issues/31#issuecomment-1026179413

        Args:
            lossless: Set to True to enable lossless compression.
            distance: Lowest settings are 0.00 or 0.01.  If 0.0 then also set lossless to True.
                To quote the cjxl man page:
                The preferred way to specify quality. It is specified in multiples of a
                just-noticeable difference. That is, -d 0 is mathematically lossless,
                -d 1 should be visually lossless, and higher distances yield denser and
                denser files with lower and lower fidelity.
            effort: To quote the cjxl man page:
                Controls the amount of effort that goes into producing an “optimal” file in
                terms of quality/size. That is to say, all other parameters being equal,
                a higher effort should yield a file that is at least as dense and possibly
                denser, and with at least as high and possibly higher quality.
                1 is fastest. 9 is slowest.
            level: DON'T SET THIS WITH THIS JpegXlFuture wrapper!
                In imagecodecs version 2021.11.20, level is mapped (incorrectly) to the decoding
                speed tier. Minimum is 0 (highest quality), and maximum is 4 (lowest quality).
                Default is 0.
            decodingspeed: DON'T SET THIS WITH THIS JpegXlFuture wrapper!
        """
        assert decodingspeed is None
        if lossless is not None:
            if lossless:
                assert (
                    level is None
                )  # level must be None to enable lossless in imagecodecs 2021.11.20.
                assert distance is None or distance == 0
            else:
                # Enable lossy compression.
                # level must be set to 0, 1, 2, 3, or 4 to enable lossy
                # compression in imagecodecs 2021.11.20.
                level = 0
        super().__init__(level=level, distance=distance, *args, **kwargs)

    def encode(self, buf: np.ndarray) -> None:
        """Encode `buf` with JPEG-XL.

        Under the hood, NaNs will be encoded as NAN_VALUE, and all "real"
        values will be in the range [LOWER_BOUND_FOR_REAL_PIXELS, 1]. But
        this is all taken care of by encode and decode.

        Args:
            buf: The input array to compress as JPEG-XL.
                Expects buf to be of shape (n_timesteps, y, x, n_channels).
                n_timesteps and n_channels must == 1.
                buf can be float16 or float32.
                All values must be in the range [0, 1].
                Use as much of the range [0, 1] as possible. 0 is black and 1 is white.
                If all the information is squished into, say, the range [0, 0.1] then
                JPEG-XL will interpret the image as very dark, and will agressively
                compress the data because JPEG-XL assumes that human viewers do not
                notice if detail is lost in the shadows.
        """
        assert buf.dtype in (
            np.float16,
            np.float32,
        ), f"dtype must be float16 or float32, not {buf.dtype}"

        # Even if the original DataArray doesn't have NaNs,
        # when Zarr saves chunks at the edges of the image, the image data for that chunk
        # might be smaller than the chunk. In that case, `buf` will be the same shape
        # as the nominal chunk size, but will include NaNs. Those NaNs must be encoded
        # with a floating point value in the range [0, 1] because JPEG-XL cannot
        # handle NaN values.
        buf = encode_nans(buf)

        # Sanity checks.
        assert np.all(np.isfinite(buf))
        assert np.amin(buf) >= 0
        assert np.amax(buf) <= 1

        # In the future, JPEG-XL will be able to encode multiple images per file.
        # But, for now, it can only compress one image at a time. See:
        # https://github.com/cgohlke/imagecodecs/issues/32
        n_timesteps = buf.shape[0]
        n_channels = buf.shape[-1]
        assert n_timesteps == 1
        assert n_channels == 1

        return super().encode(buf)

    def decode(self, buf, out=None) -> np.ndarray:
        """Decode JPEG-XL `buf`.

        Reconstruct the NaNs encoded by encode_nans.
        """
        out = super().decode(buf, out)
        out = decode_nans(out)
        return out


def encode_nans(data: np.ndarray) -> np.ndarray:
    """Encode NaNs as the value NAN_VALUE.

    Encode all other values in the range [LOWER_BOUND_FOR_REAL_PIXELS, 1].

    JPEG-XL does not understand "NaN" values. JPEG-XL only understands floating
    point values in the range [0, 1]. So we must encode NaN values
    as real values in the range [0, 1].

    After lossy JPEG-XL compression, there is slight "ringing" around the edges
    of regions with filled with a constant number. In experiments, when NAN_VALUE = 0.025,
    it appears that the values at the inner edges of a "NaN region" vary in the range
    [0.0227, 0.0280]. But, to be safe, we use a nice wide margin: We don't set
    the value of "NaNs" to be 0.00 because the ringing would cause the values
    to drop below zero, which is illegal for JPEG-XL images.

    After decompression, reconstruct regions of NaNs using "image < NAN_THRESHOLD"
    to find NaNs.

    See this comment for more info:
    https://github.com/openclimatefix/Satip/issues/67#issuecomment-1036456502

    Args:
        data: The input data. All values must already
            be in the range [0, 1]. The original data is modified in place.

    Returns:
        The returned array. "Real" values will be shifted to
            the range [LOWER_BOUND_FOR_REAL_PIXELS, 1].
            NaNs will be encoded as NAN_VALUE.
    """
    assert issubclass(
        data.dtype.type, np.floating
    ), f"dataarray.dtype must be floating point not {data.dtype}!"

    # Shift all the "real" values up to the range [0.075, 1]
    data *= 1 - LOWER_BOUND_FOR_REAL_PIXELS
    # Now [0, 1-0.075]
    data += LOWER_BOUND_FOR_REAL_PIXELS
    # Now [0.075, 1.]
    data = np.nan_to_num(data, nan=NAN_VALUE).clip(min=0, max=1)
    return data


def decode_nans(data: np.ndarray) -> np.ndarray:
    """Reconstruct the NaNs encoded by encode_nans."""
    assert np.all(np.isfinite(data))
    assert issubclass(data.dtype.type, np.floating)
    data[data <= NAN_THRESHOLD] = np.NaN
    # [0.075, 1]
    data -= LOWER_BOUND_FOR_REAL_PIXELS
    # [0, 1-0.075]
    data /= 1 - LOWER_BOUND_FOR_REAL_PIXELS
    # [0, 1]
    return data.clip(min=0, max=1)


register_codec(JpegXlFloatWithNaNs)
