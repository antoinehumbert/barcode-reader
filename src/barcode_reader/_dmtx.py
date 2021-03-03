import ctypes
from collections import namedtuple
from ctypes import cast, string_at
from functools import partial

# noinspection PyProtectedMember
from pylibdmtx.pylibdmtx import (
    ENCODING_SIZE_PREFIX, ENCODING_SIZE_NAMES, ENCODING_SCHEME_PREFIX, ENCODING_SCHEME_NAMES, _encoder, Encoded,
    _decoded_matrix_region, Rect, _pixel_data, _decoder, _image, _PACK_ORDER, _region
)
from pylibdmtx.pylibdmtx_error import PyLibDMTXError
# noinspection PyProtectedMember
from pylibdmtx.wrapper import (
    c_ubyte_p, dmtxTimeAdd, dmtxTimeNow, dmtxMatrix3VMultiplyBy, dmtxDecodeSetProp, DmtxProperty, DmtxUndefined,
    DmtxVector2, DmtxSymbolSize, DmtxScheme, dmtxEncodeSetProp, dmtxEncodeDataMatrix, dmtxImageGetProp
)

Point = namedtuple('Point', 'x y')
Decoded = namedtuple('Decoded', 'data rect polygon')


def _decode_region(decoder, region, corrections, shrink, height):
    """Decodes and returns the value in a region.

    Args:
        region (DmtxRegion):

    Yields:
        Decoded or None: The decoded value.
    """
    with _decoded_matrix_region(decoder, region, corrections) as msg:
        if msg:
            # Coordinates
            p00 = DmtxVector2()
            p10 = DmtxVector2(1.0, 0)
            p11 = DmtxVector2(1.0, 1.0)
            p01 = DmtxVector2(0.0, 1.0)
            dmtxMatrix3VMultiplyBy(p00, region.contents.fit2raw)
            dmtxMatrix3VMultiplyBy(p10, region.contents.fit2raw)
            dmtxMatrix3VMultiplyBy(p11, region.contents.fit2raw)
            dmtxMatrix3VMultiplyBy(p01, region.contents.fit2raw)
            top_left = Point(int((shrink * p01.X) + 0.5), int(height - (shrink * p01.Y) - 0.5))
            top_right = Point(int((shrink * p11.X) + 0.5), int(height - (shrink * p11.Y) - 0.5))
            bottom_right = Point(int((shrink * p10.X) + 0.5), int(height - (shrink * p10.Y) - 0.5))
            bottom_left = Point(int((shrink * p00.X) + 0.5), int(height - (shrink * p00.Y) - 0.5))
            polygon = [top_left, top_right, bottom_right, bottom_left]
            x_min = min(p.x for p in polygon)
            x_max = max(p.x for p in polygon)
            y_min = min(p.y for p in polygon)
            y_max = max(p.y for p in polygon)
            return Decoded(
                string_at(msg.contents.output),
                Rect(x_min, y_min, x_max - x_min, y_max - y_min),
                polygon
            )
        else:
            return None


def decode(image, timeout=None, gap_size=None, shrink=1, shape=None,
           deviation=None, threshold=None, min_edge=None, max_edge=None,
           corrections=None, max_count=None):
    """Decodes datamatrix barcodes in `image`.

    Args:
        image: `numpy.ndarray`, `PIL.Image` or tuple (pixels, width, height)
        timeout (int): milliseconds
        gap_size (int):
        shrink (int):
        shape (int):
        deviation (int):
        threshold (int):
        min_edge (int):
        max_edge (int):
        corrections (int):
        max_count (int): stop after reading this many barcodes. `None` to read
            as many as possible.

    Returns:
        :obj:`list` of :obj:`Decoded`: The values decoded from barcodes.
    """
    dmtx_timeout = None
    if timeout:
        now = dmtxTimeNow()
        dmtx_timeout = dmtxTimeAdd(now, timeout)

    if max_count is not None and max_count < 1:
        raise ValueError('Invalid max_count [{0}]'.format(max_count))

    pixels, width, height, bpp = _pixel_data(image)

    results = []
    with _image(
        cast(pixels, c_ubyte_p), width, height, _PACK_ORDER[bpp]
    ) as img:
        with _decoder(img, shrink) as decoder:
            properties = [
                (DmtxProperty.DmtxPropScanGap, gap_size),
                (DmtxProperty.DmtxPropSymbolSize, shape),
                (DmtxProperty.DmtxPropSquareDevn, deviation),
                (DmtxProperty.DmtxPropEdgeThresh, threshold),
                (DmtxProperty.DmtxPropEdgeMin, min_edge),
                (DmtxProperty.DmtxPropEdgeMax, max_edge)
            ]

            # Set only those properties with a non-None value
            for prop, value in ((p, v) for p, v in properties if v is not None):
                dmtxDecodeSetProp(decoder, prop, value)

            if not corrections:
                corrections = DmtxUndefined

            while True:
                with _region(decoder, dmtx_timeout) as region:
                    # Finished file or ran out of time before finding another
                    # region
                    if not region:
                        break
                    else:
                        # Decoded
                        res = _decode_region(
                            decoder, region, corrections, shrink, height
                        )
                        if res:
                            results.append(res)

                            # Stop if we've reached maximum count
                            if max_count and len(results) == max_count:
                                break

    return results


def encode(data, scheme=None, size=None):
    """
    Encodes `data` in a DataMatrix image.

    For now bpp is the libdmtx default which is 24

    Args:
        data: bytes instance
        scheme: encoding scheme - one of `ENCODING_SCHEME_NAMES`, or `None`.
            If `None`, defaults to 'Ascii'.
        size: image dimensions - one of `ENCODING_SIZE_NAMES`, or `None`.
            If `None`, defaults to 'ShapeAuto'.

    Returns:
        Encoded: with properties `(width, height, bpp, pixels)`.
        You can use that result to build a PIL image:

            Image.frombytes('RGB', (width, height), pixels)

    """

    size = size if size else 'ShapeAuto'
    size_name = '{0}{1}'.format(ENCODING_SIZE_PREFIX, size)
    if not hasattr(DmtxSymbolSize, size_name):
        raise PyLibDMTXError(
            'Invalid size [{0}]: should be one of {1}'.format(
                size, ENCODING_SIZE_NAMES
            )
        )
    size = getattr(DmtxSymbolSize, size_name)

    scheme = scheme if scheme else 'Ascii'
    scheme_name = '{0}{1}'.format(
        ENCODING_SCHEME_PREFIX, scheme
    )
    if not hasattr(DmtxScheme, scheme_name):
        scheme_name = '{0}{1}'.format(
            ENCODING_SCHEME_PREFIX, scheme.capitalize()
        )
    if not hasattr(DmtxScheme, scheme_name):
        raise PyLibDMTXError(
            'Invalid scheme [{0}]: should be one of {1}'.format(
                scheme, ENCODING_SCHEME_NAMES
            )
        )
    scheme = getattr(DmtxScheme, scheme_name)

    with _encoder() as encoder:
        dmtxEncodeSetProp(encoder, DmtxProperty.DmtxPropScheme, scheme)
        dmtxEncodeSetProp(encoder, DmtxProperty.DmtxPropSizeRequest, size)

        if dmtxEncodeDataMatrix(encoder, len(data), cast(data, c_ubyte_p)) == 0:
            raise PyLibDMTXError(
                'Could not encode data, possibly because the image is not '
                'large enough to contain the data'
            )

        w, h, bpp = map(
            partial(dmtxImageGetProp, encoder[0].image),
            (
                DmtxProperty.DmtxPropWidth, DmtxProperty.DmtxPropHeight,
                DmtxProperty.DmtxPropBitsPerPixel
            )
        )
        size = w * h * bpp // 8
        pixels = cast(
            encoder[0].image[0].pxl, ctypes.POINTER(ctypes.c_ubyte * size)
        )
        return Encoded(
            width=w, height=h, bpp=bpp, pixels=ctypes.string_at(pixels, size)
        )
