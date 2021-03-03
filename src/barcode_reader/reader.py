from enum import Enum
from pathlib import Path

from PIL import Image

from barcode_reader import _zbar, _dmtx


class Reader:
    
    def __init__(self, image_path):
        """
        Initialize barcode reader for given image
        
        :param pathlib.Path|str image_path: path to the image to read
        """
        self._image_path = Path(image_path)
        self._image = None

    def _close(self):
        if self._image is not None:
            self._image.close()
            self._image = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()
            
    def __del__(self):
        self._close()

    @property
    def image(self):
        """
        :return: the pillow image to process
        :rtype: PIL.Image.Image
        """
        if self._image is None:
            self._image = Image.open(self._image_path)
        return self._image

    def zbar_read(self):
        zbar_result = _zbar.decode(self.image)
        barcodes = [
            Barcode(Barcode.Type(barcode.type), [(p.x, p.y) for p in barcode.polygon], barcode.data)
            for barcode in zbar_result
        ]
        return barcodes

    def dmtx_read(self):
        dmtx_result = _dmtx.decode(self.image)
        barcodes = [
            Barcode(Barcode.Type.DATAMATRIX, [(p.x, p.y) for p in barcode.polygon], barcode.data.decode("utf-8"))
            for barcode in dmtx_result
        ]
        return barcodes


class Barcode:

    class Type(Enum):
        EAN2 = "EAN2"  # /**< GS1 2-digit add-on */
        EAN5 = "EAN5"  # /**< GS1 5-digit add-on */
        EAN8 = "EAN8"  # /**< EAN-8 */
        UPCE = "UPCE"  # /**< UPC-E */
        ISBN10 = "ISBN10"  # /**< ISBN-10 (from EAN-13). @since 0.4 */
        UPCA = "UPCA"  # /**< UPC-A */
        EAN13 = "EAN13"  # /**< EAN-13 */
        ISBN13 = "ISBN13"  # /**< ISBN-13 (from EAN-13). @since 0.4 */
        COMPOSITE = "COMPOSITE"  # /**< EAN/UPC composite */
        I25 = "I25"  # /**< Interleaved 2 of 5. @since 0.4 */
        DATABAR = "DATABAR"  # /**< GS1 DataBar (RSS). @since 0.11 */
        DATABAR_EXP = "DATABAR_EXP"  # /**< GS1 DataBar Expanded. @since 0.11 */
        CODABAR = "CODABAR"  # /**< Codabar. @since 0.11 */
        CODE39 = "CODE39"  # /**< Code 39. @since 0.4 */
        PDF417 = "PDF417"  # /**< PDF417. @since 0.6 */
        QRCODE = "QRCODE"  # /**< QR Code. @since 0.10 */
        CODE93 = "CODE93"  # /**< Code 93. @since 0.11 */
        CODE128 = "CODE128"  # /**< Code 128 */
        DATAMATRIX = "DATAMATRIX"

    def __init__(self, type_, coordinates, data):
        """
        Initialize barcode

        :param barcode_reader.reader.Barcode.Type type_: the barcode type
        :param list[tuple[int, int]] coordinates: list of barcode corners coordinates starting from the top-left of the
          barcode (in barcode reading order), in clockwise order
        :param str data: the barcode data
        """
        self._type = type_
        self._coordinates = coordinates
        self._data = data

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self._data} - {self._type.name}@{self._coordinates}>"

    def __str__(self):
        return self._data

    @property
    def type(self):
        """
        :return: the barcode type
        :rtype: str
        """
        return self._type

    @property
    def data(self):
        """
        :return: the barcode data
        :rtype: str
        """
        return self._data

    @property
    def coordinates(self):
        """
        :return: the barcode coordinates
        :rtype: list[tuple[int, int]]
        """
        return self._coordinates
