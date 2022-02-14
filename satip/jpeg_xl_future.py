"""Thin wrapper around imagecodecs.JpegXl.

This this wrapper is only required while the most recent version of imagecodecs is version
2021.11.20.
"""
from typing import Optional

import numpy as np
from imagecodecs import JpegXl
from numcodecs import register_codec


class JpegXlFuture(JpegXl):
    """Thin wrapper around imagecodecs.JpegXl.

    Simple hack to make the JpegXl compressor in the currently released
    version of imagecodecs (version 2021.11.20) look like the version in development.
    (We can't simply use the version in development because the imagecodecs author
    does not develop on GitHub. The imagecodecs authors just uses GitHub as one of
    several mechanisms to release imagecodecs.)

    See https://github.com/cgohlke/imagecodecs/issues/31#issuecomment-1026179413
    """

    codec_id = "imagecodecs_jpegxl"

    def __init__(
        self,
        lossless: Optional[bool] = None,
        distance: Optional[int] = None,
        level: Optional[int] = None,
        decodingspeed: Optional[float] = None,
        *args,
        **kwargs
    ):
        """Initialise JpegXlFuture.

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
                )  # level must be None to enable lossless in imagecodecs 2011.11.20.
                assert distance is None or distance == 0
            else:
                # Enable lossy compression.
                # level must be set to 0, 1, 2, 3, or 4 to enable lossy
                # compression in imagecodecs 2021.11.20.
                level = 0

        super().__init__(level=level, distance=distance, *args, **kwargs)

    def encode(self, buf):
        """Encode buf at JPEG-XL."""
        n_examples = buf.shape[0]
        n_timesteps = buf.shape[1]
        n_channels = buf.shape[-1]
        assert n_examples == 1
        assert n_timesteps == 1
        assert n_channels == 1
        buf = buf[0]
        return super().encode(buf)

    def decode(self, buf, out=None):
        """Decode JPEG-XL data."""
        assert out is None
        out = super().decode(buf, out)
        out = out[np.newaxis, ...]
        return out


register_codec(JpegXlFuture)
