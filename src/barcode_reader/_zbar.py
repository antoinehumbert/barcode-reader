"""
This module is a fork of pyzbar.pyzbar with a modification in _decode_symbols function so that the returned polygon for
a barcode always starts with the point being the top-left corner of the barcode and coordinates are in clockwise order.

It also adds an additional functions for correct decoding of barcode data.
"""
import operator
from collections import deque
from ctypes import cast, c_void_p, string_at, c_uint, c_char_p

# noinspection PyPackageRequirements
from pyzbar.locations import bounding_box, convex_hull
# noinspection PyProtectedMember,PyPackageRequirements
from pyzbar.pyzbar import _image_scanner, _pixel_data, _FOURCC, _symbols_for_image, _RANGEFN, _image, Decoded
# noinspection PyPackageRequirements
from pyzbar.pyzbar_error import PyZbarError
# noinspection PyProtectedMember,PyPackageRequirements
from pyzbar.wrapper import (
    zbar_image_scanner_set_config, zbar_symbol_get_quality, zbar_image_set_format, zbar_image_set_size,
    zbar_image_set_data, zbar_scan_image, zbar_symbol_get_data, zbar_symbol_get_orientation, zbar_symbol_get_loc_size,
    zbar_symbol_get_loc_x, zbar_symbol_get_loc_y, zbar_symbol_xml, ZBarConfig, ZBarSymbol, ZBarOrientation
)


def _decode_zbar_data(data):
    """
    Zbar returns data in utf-8 encoding. But, when reading the barcode, it decoded it with the sjis encoding whereas
    the default should be iso-8859-1 for barcode producers that do not use utf-8 encoding.

    For this reason, we try to decode the zbar returned data by replacing sjis encoding by iso-8859-1. But if this
    does not work, we assume that original encoding was utf-8 and do not re-encode/decode zbar data

    :param bytes data: the zbar read data (utf-8 encoded)
    :return: the decoded data
    :rtype: str
    """
    data_str = data.decode("utf-8")
    print("foo", data, data_str)
    # For unknown reason, when a QR-Code is encoded in iso-8859-1 with 2 and only 2 non-ascii characters, zbar decode it
    # using sjis encoding instead of iso-8859-1. So we try here to correct this.
    try:
        data = data_str.encode("sjis")
    except UnicodeEncodeError:
        pass  # It was not decoded using sjis encoding, so this is ok
    else:
        iso_8859_1 = data.decode("iso-8859-1")
        print("bar", data, iso_8859_1)
        # If string contains 2 and only 2 non-ascii characters, it was probably iso-8859-1 encoded and not sjis
        if len(iso_8859_1.encode("ascii", errors="ignore")) == len(data) - 2:
            data_str = iso_8859_1
    return data_str


def _decode_symbols(symbols, xml=False):
    """Generator of decoded symbol information.

    Args:
        symbols: iterable of instances of `POINTER(zbar_symbol)`

    Yields:
        Decoded: decoded symbol
    """
    for symbol in symbols:
        data = _decode_zbar_data(string_at(zbar_symbol_get_data(symbol)))
        # The 'type' int in a value in the ZBarSymbol enumeration
        symbol_type = ZBarSymbol(symbol.contents.type).name
        polygon = [
            (zbar_symbol_get_loc_x(symbol, index), zbar_symbol_get_loc_y(symbol, index))
            for index in _RANGEFN(zbar_symbol_get_loc_size(symbol))
        ]
        x, y = polygon[0]
        polygon = deque(convex_hull(polygon))
        # change polygon points from counterclockwise order to clockwise order
        polygon.reverse()
        # Reorder convex polygon points so that first point is the closest to first point of original polygon (i.e. the
        # top left point of the barcode)
        x_y_dists = [(idx, (px - x) ** 2 + (py - y) ** 2) for idx, (px, py) in enumerate(polygon)]
        min_dist_idx = min(x_y_dists, key=operator.itemgetter(1))[0]
        polygon.rotate(-min_dist_idx)
        polygon = list(polygon)
        orientation = ZBarOrientation(zbar_symbol_get_orientation(symbol))
        quality = zbar_symbol_get_quality(symbol)

        if xml:
            xml_len_p = c_uint()
            xml_buf = c_char_p()
            item = zbar_symbol_xml(symbol, xml_buf, xml_len_p)
        else:
            item = Decoded(
                data=data,
                type=symbol_type,
                rect=bounding_box(polygon),
                polygon=polygon,
                orientation=orientation,
                quality=quality,
            )
        yield item


# noinspection PyIncorrectDocstring
def decode(image, symbols=None, xml=False):
    """Decodes datamatrix barcodes in `image`.

    Args:
        image: `numpy.ndarray`, `PIL.Image` or tuple (pixels, width, height)
        symbols: iter(ZBarSymbol) the symbol types to decode; if `None`, uses
            `zbar`'s default behaviour, which is to decode all symbol types.

    Returns:
        :obj:`list` of :obj:`Decoded`: The values decoded from barcodes.
    """
    pixels, width, height = _pixel_data(image)

    results = []
    with _image_scanner() as scanner:
        if symbols:
            # Disable all but the symbols of interest
            disable = set(ZBarSymbol).difference(symbols)
            for symbol in disable:
                zbar_image_scanner_set_config(
                    scanner, symbol, ZBarConfig.CFG_ENABLE, 0
                )
            # I think it likely that zbar will detect all symbol types by
            # default, in which case enabling the types of interest is
            # redundant but it seems sensible to be over-cautious and enable
            # them.
            for symbol in symbols:
                zbar_image_scanner_set_config(
                    scanner, symbol, ZBarConfig.CFG_ENABLE, 1
                )
        with _image() as img:
            zbar_image_set_format(img, _FOURCC['L800'])
            zbar_image_set_size(img, width, height)
            zbar_image_set_data(img, cast(pixels, c_void_p), len(pixels), None)
            decoded = zbar_scan_image(scanner, img)
            if decoded < 0:
                raise PyZbarError('Unsupported image format')
            else:
                results.extend(_decode_symbols(_symbols_for_image(img), xml))

    return results
