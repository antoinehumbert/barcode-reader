import operator
from collections import namedtuple, deque
from concurrent.futures import ProcessPoolExecutor

# noinspection PyPackageRequirements
import cv2
# noinspection PyPackageRequirements
import jpype
import numpy as np
from imforge.crop import crop
from pkg_resources import resource_filename

from barcode_reader.utils import detect_barcodes

Point = namedtuple("Point", ["x", "y"])
Rect = namedtuple('Rect', ['left', 'top', 'width', 'height'])
Decoded = namedtuple('Decoded', ["data", "type", "rect", "polygon"])
_ZxingResult = namedtuple("ZxingResult", ["data", "format", "result_points"])

# zxing functions requiring the JVM are launch in other processes to avoid interaction with possible other libraries
# using jpype and needing a JVM with different configuration
_CLASS_PATHS = (
    resource_filename(__name__, "core-3.4.1.jar"),
    resource_filename(__name__, "javase-3.4.1.jar"),
)


def _start_zxing_jvm():
    # noinspection PyUnresolvedReferences
    jpype.startJVM(classpath=_CLASS_PATHS)


class ZxingDecoder:

    def __init__(self):
        # Binary image generation
        self.DataBufferByte = jpype.JClass("java.awt.image.DataBufferByte")
        self.Raster = jpype.JClass("java.awt.image.Raster")
        self.BufferedImage = jpype.JClass("java.awt.image.BufferedImage")
        self.BinaryBitmap = jpype.JClass("com.google.zxing.BinaryBitmap")
        self.HybridBinarizer = jpype.JClass("com.google.zxing.common.HybridBinarizer")
        self.BufferedImageLuminanceSource = jpype.JClass("com.google.zxing.client.j2se.BufferedImageLuminanceSource")
        # exceptions
        self.NotFoundException = jpype.JClass("com.google.zxing.NotFoundException")
        # readers
        self.multi_reader = jpype.JClass("com.google.zxing.MultiFormatReader")()
        self.qr_reader = jpype.JClass("com.google.zxing.multi.qrcode.QRCodeMultiReader")()
        self.pdf417_reader = jpype.JClass("com.google.zxing.pdf417.PDF417Reader")()
        # hints
        # noinspection PyPep8Naming
        ArrayList = jpype.JClass("java.util.ArrayList")
        # noinspection PyPep8Naming
        BarcodeFormat = jpype.JClass("com.google.zxing.BarcodeFormat")
        # noinspection PyPep8Naming
        DecodeHintType = jpype.JClass("com.google.zxing.DecodeHintType")
        self.qr_hints = {DecodeHintType.TRY_HARDER: True}
        self.pdf417_hints = {DecodeHintType.TRY_HARDER: True}
        self.other_hints = {
            DecodeHintType.POSSIBLE_FORMATS: ArrayList([
                BarcodeFormat.AZTEC, BarcodeFormat.CODABAR, BarcodeFormat.CODE_39, BarcodeFormat.CODE_93,
                BarcodeFormat.CODE_128, BarcodeFormat.DATA_MATRIX, BarcodeFormat.EAN_8, BarcodeFormat.EAN_13,
                BarcodeFormat.ITF, BarcodeFormat.MAXICODE, BarcodeFormat.RSS_14, BarcodeFormat.RSS_EXPANDED,
                BarcodeFormat.UPC_E,
                # BarcodeFormat.PDF_417, BarcodeFormat.QR_CODE,  # use specific readers for QR_CODE and PDF_417
            ])
        }

    def decode(self, image, quiet_dist=10, min_area=12000):
        """
        Decode barcodes of given image (must be in L mode). This function is intended for execution in child process.
        The Zxing JVM must have been started with the _start_zxing_jvm function before calling this function.

        :param PIL.Image.Image image: the image (in L mode) to decode
        :param int quiet_dist: the quiet distance in pixels (i.e. blank zone around barcodes)
        :param int min_area: the min area in pixels x pixels a barcode must have
        :return: the list of decoding results
        :rtype: list[barcode_reader._zxing.Decoded]
        """
        image = image.convert("L")
        im = np.array(image)
        bitmap = self.get_binary_bitmap(im)
        results = self.decode_qr(bitmap)
        results.extend(self.decode_pdf417(bitmap))
        for result in results:
            cv2.fillConvexPoly(im, np.int0(result.result_points), color=255)
        image.frombytes(im)
        all_points = [pt for result in results for pt in result.result_points]
        for center, (width, height), angle in detect_barcodes(image, quiet_dist, min_area):
            rectangle = deque(
                (round(p[0]), round(p[1]))
                for p in cv2.boxPoints((center, (width + 2 * quiet_dist, height + 2 * quiet_dist), angle))
            )
            # Check if rectangle contains an already identified barcode. If so, we skip it
            if any(cv2.pointPolygonTest(np.array(rectangle), pt, False) >= 0 for pt in all_points):
                continue
            # change rectangle and angle to have the top-left corner first
            top_left_idx = min(
                ((idx, x * x + y * y) for idx, (x, y) in enumerate(rectangle)), key=operator.itemgetter(1)
            )[0]
            rectangle.rotate(-top_left_idx)
            rectangle = list(rectangle)
            if top_left_idx == 0:
                angle -= 90
            # elif min_dist_idx == 1:
            #    the rectangle is correctly oriented. No change
            elif top_left_idx == 2:
                angle += 90
            elif top_left_idx == 3:
                angle += 180
            mat = cv2.getRotationMatrix2D((width / 2 + quiet_dist, height / 2 + quiet_dist), -angle, 1)
            top_left = rectangle[0]
            mat[0][2] = top_left[0]
            mat[1][2] = top_left[1]
            im = np.array(crop(image, rectangle, fillcolor=255))
            for zxing_result in self.decode_other(self.get_binary_bitmap(im)):
                results.append(
                    _ZxingResult(
                        data=zxing_result.data,
                        format=zxing_result.format,
                        result_points=cv2.transform(
                            np.array([zxing_result.result_points], dtype=np.float32), mat
                        ).tolist()[0]
                    )
                )
        decoded_results = []
        for result in results:
            polygon = deque(Point(x=round(x), y=round(y)) for x, y in result.result_points)
            polygon.rotate(-1)
            polygon = list(polygon)
            x_min = min(p.x for p in polygon)
            x_max = max(p.x for p in polygon)
            y_min = min(p.y for p in polygon)
            y_max = max(p.y for p in polygon)
            decoded_results.append(
                Decoded(
                    data=result.data,
                    type=result.format,
                    rect=Rect(left=x_min, top=y_min, width=x_max - x_min, height=y_max - y_min),
                    polygon=polygon,
                )
            )
        return decoded_results

    def get_binary_bitmap(self, image):
        """
        Return binary bitmap for given grayscale (numpy array) image

        :param numpy.array image: the grayscale image to convert
        :return: the binary bitmap (a ``com.google.zxing.BinaryBitmap`` instance)
        """
        height, width = image.shape
        buf_image = self.BufferedImage(width, height, self.BufferedImage.TYPE_BYTE_GRAY)
        buf_image.setData(
            self.Raster.createBandedRaster(
                self.DataBufferByte(jpype.JArray.of(image.flatten(), dtype=jpype.JByte), width * height),
                width, height, width, [0], [0], None
            )
        )
        return self.BinaryBitmap(self.HybridBinarizer(self.BufferedImageLuminanceSource(buf_image)))

    def decode_qr(self, bitmap):
        """
        Decode QR-Codes in given binary bitmap

        :param bitmap: the bitmap to decode (a ``com.google.zxing.BinaryBitmap`` instance)
        :return: the list of read QR-Codes
        :rtype: list[barcode_reader._zxing._ZxingResult]
        """
        results = []
        # Detect multiple QR-Codes
        reader = self.qr_reader
        reader.reset()
        try:
            qr_results = reader.decodeMultiple(bitmap, self.qr_hints)
        except self.NotFoundException:
            pass
        else:
            for result in qr_results:
                result_points = [(float(p.getX()), float(p.getY())) for p in result.getResultPoints()]
                data = str(result.getText())
                barcode_format = str(result.getBarcodeFormat())
                results.append(_ZxingResult(data=data, format=barcode_format, result_points=result_points))
        return results

    def decode_pdf417(self, bitmap):
        """
        Decode PDF417 Codes in given binary bitmap

        :param bitmap: the bitmap to decode (a ``com.google.zxing.BinaryBitmap`` instance)
        :return: the list of read PDF417 Codes
        :rtype: list[barcode_reader._zxing._ZxingResult]
        """
        results = []
        # Detect multiple PDF-417
        reader = self.pdf417_reader
        reader.reset()
        try:
            pdf417_results = reader.decodeMultiple(bitmap, self.pdf417_hints)
        except self.NotFoundException:
            pass
        else:
            for result in pdf417_results:
                result_points = [(float(p.getX()), float(p.getY())) for p in result.getResultPoints()]
                data = str(result.getText())
                barcode_format = str(result.getBarcodeFormat())
                results.append(_ZxingResult(data=data, format=barcode_format, result_points=result_points))
        return results

    def decode_other(self, bitmap):
        """
        Decode **one** barcode (not QR-Code or PDF417) in given binary bitmap

        :param bitmap: the bitmap to decode (a ``com.google.zxing.BinaryBitmap`` instance)
        :return: the list of read PDF417 Codes
        :rtype: list[barcode_reader._zxing._ZxingResult]
        """
        results = []
        # Finally, search for one code with the MultiFormatReader
        reader = self.multi_reader
        reader.reset()
        try:
            any_result = reader.decode(bitmap, self.other_hints)
        except self.NotFoundException:
            pass
        else:
            result_points = [(float(p.getX()), float(p.getY())) for p in any_result.getResultPoints()]
            data = str(any_result.getText())
            barcode_format = str(any_result.getBarcodeFormat())
            if barcode_format == "DATA_MATRIX":
                # Zxing usually decode datamatrix using iso-8859-1 charset. However, it may be encoded in utf-8.
                # So, we try to re-decode data using utf-8 encoding. If it works, we consider this was the correct
                # encoding. If not, we keep the originally decoded data from Zxing
                try:
                    data = data.encode("iso-8859-1").decode("utf-8")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass
            results.append(_ZxingResult(data=data, format=barcode_format, result_points=result_points))
        return results


def _init_process():
    global _zxing_decoder
    _start_zxing_jvm()
    _zxing_decoder = ZxingDecoder()


_zxing_decoder = None
_executors = ProcessPoolExecutor(initializer=_init_process)


def _decode(image):
    # noinspection PyUnresolvedReferences
    return _zxing_decoder.decode(image)


def decode(image):
    """
    Decode barcodes of given image

    :param PIL.Image.Image image: the image to decode
    :return: list of found barcodes
    :rtype: list[barcode_reader._zxing.Decoded]
    """
    return _executors.submit(_decode, image).result()
