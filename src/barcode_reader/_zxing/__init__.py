from collections import namedtuple, deque
from concurrent.futures import ProcessPoolExecutor

# noinspection PyPackageRequirements
import jpype
import numpy as np
from PIL import Image
from pkg_resources import resource_filename

Point = namedtuple("Point", ["x", "y"])
Rect = namedtuple('Rect', ['left', 'top', 'width', 'height'])
Decoded = namedtuple('Decoded', ["data", "type", "rect", "polygon"])


# zxing functions requiring the JVM are launch in other processes to avoid interaction with possible other libraries
# using jpype and needing a JVM with different configuration
_CLASS_PATHS = (
    resource_filename(__name__, "core-3.4.1.jar"),
    resource_filename(__name__, "javase-3.4.1.jar"),
    resource_filename(*__name__.rsplit(".", 1))
)


def _start_zxing_jvm():
    # noinspection PyUnresolvedReferences
    jpype.startJVM(classpath=_CLASS_PATHS)


_executors = ProcessPoolExecutor(initializer=_start_zxing_jvm)


# noinspection PyPep8Naming
def _decode(image_path):
    """
    Decode barcodes of image at given path. This function is intended for execution in child process. The Zxing JVM must
    have been started with the _start_zxing_jvm function before calling this function.

    :param pathlib.Path image_path: path to the image to decode
    :return: the list of decoding results
    :rtype: list[barcode_reader._zxing.Decoded]
    """
    DataBufferByte = jpype.JClass("java.awt.image.DataBufferByte")
    Raster = jpype.JClass("java.awt.image.Raster")
    BufferedImage = jpype.JClass("java.awt.image.BufferedImage")
    URI = jpype.JClass("java.net.URI")
    ArrayList = jpype.JClass("java.util.ArrayList")
    BarcodeFormat = jpype.JClass("com.google.zxing.BarcodeFormat")
    BinaryBitmap = jpype.JClass("com.google.zxing.BinaryBitmap")
    DecodeHintType = jpype.JClass("com.google.zxing.DecodeHintType")
    MultiFormatReader = jpype.JClass("com.google.zxing.MultiFormatReader")
    HybridBinarizer = jpype.JClass("com.google.zxing.common.HybridBinarizer")
    BufferedImageLuminanceSource = jpype.JClass("com.google.zxing.client.j2se.BufferedImageLuminanceSource")
    ImageReader = jpype.JClass("com.google.zxing.client.j2se.ImageReader")
    # ResultParser = jpype.JClass("com.google.zxing.client.result.ResultParser")
    # GenericMultipleBarcodeReader = jpype.JClass("com.google.zxing.multi.GenericMultipleBarcodeReader")
    GenericMultipleBarcodeReader = jpype.JClass("GenericMultipleBarcodeReaderEx")
    QRCodeMultiReader = jpype.JClass("com.google.zxing.multi.qrcode.QRCodeMultiReader")
    PDF417Reader = jpype.JClass("com.google.zxing.pdf417.PDF417Reader")
    NotFoundException = jpype.JClass("com.google.zxing.NotFoundException")

    im = np.array(Image.open(image_path).convert("L"))
    height, width = im.shape
    image = BufferedImage(width, height, BufferedImage.TYPE_BYTE_GRAY)
    image.setData(
        Raster.createBandedRaster(
            DataBufferByte(jpype.JArray.of(im.flatten(), dtype=jpype.JByte), width * height),
            width, height, width, [0], [0], None
        )
    )

    # image = ImageReader.readImage(URI(image_path.as_uri()))
    source = BufferedImageLuminanceSource(image)
    bitmap = BinaryBitmap(HybridBinarizer(source))
    hints = {
        DecodeHintType.TRY_HARDER: False,
        # DecodeHintType.CHARACTER_SET: "UTF-8",  # Do not set. Let it detect !
        DecodeHintType.POSSIBLE_FORMATS: ArrayList([
            BarcodeFormat.AZTEC, BarcodeFormat.CODABAR, BarcodeFormat.CODE_39, BarcodeFormat.CODE_93,
            BarcodeFormat.CODE_128, BarcodeFormat.DATA_MATRIX, BarcodeFormat.EAN_8, BarcodeFormat.EAN_13,
            BarcodeFormat.ITF, BarcodeFormat.MAXICODE,
            BarcodeFormat.RSS_14, BarcodeFormat.RSS_EXPANDED, BarcodeFormat.UPC_A, BarcodeFormat.UPC_E,
            # BarcodeFormat.PDF_417, BarcodeFormat.QR_CODE,  # use specific readers for QR_CODE and PDF_417
        ])
    }
    results = []
    # Detect QR-Codes first
    reader = QRCodeMultiReader()
    try:
        results.extend(reader.decodeMultiple(bitmap, hints))
    except NotFoundException:
        pass
    # Then detect PDF-417
    reader = PDF417Reader()
    try:
        results.extend(reader.decodeMultiple(bitmap, hints))
    except NotFoundException:
        pass
    # Finally, search for others with the inefficient GenericMultipleBarcodeReader
    multi_format_reader = MultiFormatReader()
    reader = GenericMultipleBarcodeReader(multi_format_reader)
    try:
        results.extend(reader.decodeMultiple(bitmap, hints))
    except NotFoundException:
        pass
    decoded_results = []
    for result in results:
        polygon = deque(Point(x=round(p.getX()), y=round(p.getY())) for p in result.getResultPoints())
        polygon.rotate(-1)
        polygon = list(polygon)
        x_min = min(p.x for p in polygon)
        x_max = max(p.x for p in polygon)
        y_min = min(p.y for p in polygon)
        y_max = max(p.y for p in polygon)
        data = str(result.getText())
        barcode_format = str(result.getBarcodeFormat())
        if barcode_format == "DATA_MATRIX":
            # Zxing usually decode datamatrix using iso-8859-1 charset. However, it may be encoded in utf-8. SO, we try
            # to re-decode data using utf-8 encoding. If it works, we consider this was the correct encoding. If not, we
            # keep the originally decoded data from Zxing
            try:
                data = data.encode("iso-8859-1").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        decoded_results.append(
            Decoded(
                data=data,
                type=barcode_format,
                rect=Rect(left=x_min, top=y_min, width=x_max - x_min, height=y_max - y_min),
                polygon=polygon,
            )
        )
    return decoded_results


def decode(image_path):
    """
    Decode barcodes of image at given path

    :param pathlib.Path image_path: path to the image to decode
    :return: list of found barcodes
    :rtype: list[barcode_reader._zxing.Decoded]
    """
    return _executors.submit(_decode, image_path).result()
