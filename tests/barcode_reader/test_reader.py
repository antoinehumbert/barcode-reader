import sys
from PIL import Image, ImageDraw

from barcode_reader.reader import Reader, Barcode
from imforge.crop import crop
# noinspection PyProtectedMember
from barcode_reader import _dmtx


class TestReader:

    DEBUG = False
    # Some results depend on the running platform. May some some rounding difference !
    WIN = sys.platform == "win32"
    DARWIN = sys.platform == "darwin"

    def test_zbar_read_utf8(self, resources):
        with Reader(resources / "qrcode.png") as reader:
            barcodes = reader.zbar_read()
        assert len(barcodes) == 1
        barcode = barcodes[0]
        assert barcode.type == Barcode.Type.QRCODE
        assert barcode.data == str(barcode) == "Sample € QR-Code"
        assert barcode.coordinates == [(39, 39), (259, 38), (261, 261), (38, 259)]
        assert repr(barcode) == "<Barcode: Sample € QR-Code - QRCODE@[(39, 39), (259, 38), (261, 261), (38, 259)]>"
        if self.DEBUG:
            with Image.open(resources / "qrcode.png") as image:
                crop(image, barcode.coordinates, fillcolor=(255, 0, 255), cut_out=True).show()

    def test_zbar_read_iso_8859_1(self, resources):
        with Reader(resources / "iso-8859-1_qrcode.png") as reader:
            barcodes = reader.zbar_read()
        assert len(barcodes) == 1
        barcode = barcodes[0]
        assert barcode.type == Barcode.Type.QRCODE
        assert barcode.data == str(barcode) == "QR-Code encodé en iso-8859-1"
        assert barcode.coordinates == [(38, 38), (210, 38), (211, 211), (38, 210)]
        if self.DEBUG:
            with Image.open(resources / "iso-8859-1_qrcode.png") as image:
                crop(image, barcode.coordinates, fillcolor=(255, 0, 255), cut_out=True).show()

    def test_zbar_read_sjis(self, resources):
        with Reader(resources / "sjis_qrcode.png") as reader:
            barcodes = reader.zbar_read()
        assert len(barcodes) == 1
        barcode = barcodes[0]
        assert barcode.type == Barcode.Type.QRCODE
        assert barcode.data == str(barcode) == "日本語"
        assert barcode.coordinates == [(41, 41), (209, 41), (209, 209), (41, 209)]
        if self.DEBUG:
            with Image.open(resources / "sjis_qrcode.png") as image:
                crop(image, barcode.coordinates, fillcolor=(255, 0, 255), cut_out=True).show()

    def test_zbar_read_bad_decoding(self, resources):
        # This is QR-Code encoded in iso-8859-1, but zbar decoded it as sjis
        with Reader(resources / "bad_decoding_qrcode.png") as reader:
            barcodes = reader.zbar_read()
        assert len(barcodes) == 1
        barcode = barcodes[0]
        assert barcode.type == Barcode.Type.QRCODE
        assert barcode.data == str(barcode) == "___é___à____"
        assert barcode.coordinates == [(41, 41), (209, 41), (209, 209), (41, 209)]
        if self.DEBUG:
            with Image.open(resources / "bad_decoding_qrcode.png") as image:
                crop(image, barcode.coordinates, fillcolor=(255, 0, 255), cut_out=True).show()

    def test_zbar_read_multi_rotated(self, resources):
        multi_qr_image = resources / "qrcode_multi.png"
        if not multi_qr_image.exists():
            with Image.open(resources / "qrcode.png") as qrcode_image:
                w, h = qrcode_image.rotate(45, expand=True).size
                with Image.new(mode=qrcode_image.mode, size=(w * 6, h * 4), color=(255, 255, 255)) as image:
                    for idx, angle in enumerate(range(0, 360, 15)):
                        rotated_qr = qrcode_image.rotate(
                            angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255)
                        )
                        rw, rh = rotated_qr.size
                        image.paste(
                            rotated_qr,
                            ((idx % 6) * w + ((w - rw) // 2), (idx // 6) * h + ((h - rh) // 2))
                        )
                    image.save(multi_qr_image)
        with Reader(multi_qr_image) as reader:
            barcodes = reader.zbar_read()
        expected_barcodes_coordinates = [
            [(1648, 1065), (1492, 1221),
             (1334, 1064) if self.WIN else (1334, 1065) if self.DARWIN else (1333, 1064), (1492, 909)],
            [(1333, 213), (1490, 56), (1647, 213), (1490, 369)],
            [(1491, 1333), (1647, 1490),
             (1490, 1647) if self.WIN else (1491, 1647), (1335, 1490) if self.WIN else (1334, 1490)],
            [(1491, 796), (1335, 640) if self.DARWIN else (1334, 640), (1491, 482), (1647, 640)],
            [(1875, 1339), (2067, 1449), (1958, 1642), (1765, 1530)],
            [(1106, 1339), (1216, 1530), (1024, 1643), (915, 1449)],
            [(2068, 1024), (1958, 1216), (1765, 1105), (1877, 914)],
            [(1217, 1105), (1026, 1216), (913, 1024), (1106, 914)],
            [(1957, 791), (1766, 680), (1877, 487) if self.WIN else (1876, 486), (2067, 600)],
            [(1024, 790), (914, 599), (1105, 488), (1216, 680)],
            [(913, 172), (1105, 61), (1216, 254), (1023, 362)],
            [(1764, 254), (1875, 63), (2068, 172), (1956, 365)],
            [(717, 1354), (775, 1568), (561, 1625), (504, 1412)],
            [(2478, 986), (2422, 1199), (2207, 1143), (2265, 929)],
            [(560, 775), (503, 561), (717, 503), (773, 717)],
            [(2207, 291), (2263, 78), (2479, 134), (2420, 348)],
            [(2264, 1355), (2477, 1412), (2421, 1627), (2206, 1568)],
            [(775, 1143), (561, 1201), (504, 986), (718, 930)],
            [(2421, 774), (2207, 718), (2264, 503), (2478, 562)],
            [(503, 134), (716, 77), (775, 291), (560, 347)],
            [(324, 1380), (324, 1600), (102, 1602), (103, 1379)],
            [(324, 1176), (103, 1176), (102, 954), (324, 955)],
            [(102, 750), (101, 529), (324, 528), (322, 750)],
            [(102, 102), (322, 101), (324, 324), (101, 322)],
        ]
        assert len(barcodes) == len(expected_barcodes_coordinates) == 24
        if self.DEBUG:
            with Image.open(multi_qr_image) as image:
                draw = ImageDraw.ImageDraw(image)
                for barcode in barcodes:
                    draw.line(barcode.coordinates, fill=(255, 0, 0), width=8, joint="curve")
                image.show()
        for barcode, expected_coordinates in zip(barcodes, expected_barcodes_coordinates):
            assert barcode.type == Barcode.Type.QRCODE
            assert barcode.data == str(barcode) == "Sample € QR-Code"
            assert barcode.coordinates == expected_coordinates
            if self.DEBUG:
                with Image.open(multi_qr_image) as image:
                    w, h = image.size
                    cropped_image = crop(image, barcode.coordinates, fillcolor=(255, 0, 255), cut_out=True)
                    cw, ch = cropped_image.size
                    debug_image = Image.new(mode=image.mode, size=(w, h + ch), color=(255, 255, 255))
                    ImageDraw.ImageDraw(image).line(barcode.coordinates, fill=(255, 0, 0), width=8, joint="curve")
                    debug_image.paste(image)
                    debug_image.paste(cropped_image, ((w - cw) // 2, h))
                    debug_image.show()

    def test_dmtx_read(self, resources):
        sample_datamatrix = resources / "datamatrix.png"
        if not sample_datamatrix.exists():
            encoded = _dmtx.encode(
                "This is a datamatrix containing € sign and 日本語 characters".encode("utf-8"), "AutoBest", "52x52"
            )
            Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels).save(sample_datamatrix)
        with Reader(sample_datamatrix) as reader:
            barcodes = reader.dmtx_read()
        assert len(barcodes) == 1
        barcode = barcodes[0]
        assert barcode.type == Barcode.Type.DATAMATRIX
        assert barcode.data == str(barcode) == "This is a datamatrix containing € sign and 日本語 characters"
        assert barcode.coordinates == [(9, 10), (269, 10), (269, 269), (9, 269)]
        assert repr(barcode) == (
            "<Barcode: This is a datamatrix containing € sign and 日本語 characters - "
            "DATAMATRIX@[(9, 10), (269, 10), (269, 269), (9, 269)]>"
        )
        if self.DEBUG:
            with Image.open(sample_datamatrix) as image:
                crop(image, barcode.coordinates, fillcolor=(255, 0, 255), cut_out=True).show()

    def test_dmtx_read_multi_rotated(self, resources):
        multi_dm_image = resources / "datamatrix_multi.png"
        if not multi_dm_image.exists():
            with Image.open(resources / "datamatrix.png") as datamatrix_image:
                w, h = datamatrix_image.rotate(45, expand=True).size
                # Add more blank around datamatrix, otherwise, one of the 225° rotated one is not read
                w += 10
                h += 10
                with Image.new(mode=datamatrix_image.mode, size=(w * 6, h * 4), color=(255, 255, 255)) as image:
                    for idx, angle in enumerate(range(0, 360, 15)):
                        rotated_dm = datamatrix_image.rotate(
                            angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255)
                        )
                        rw, rh = rotated_dm.size
                        image.paste(
                            rotated_dm,
                            ((idx % 6) * w + ((w - rw) // 2), (idx // 6) * h + ((h - rh) // 2))
                        )
                    image.save(multi_dm_image)
        with Reader(multi_dm_image) as reader:
            barcodes = reader.dmtx_read()
        expected_barcodes_coordinates = [
            [(332, 1144), (73, 1144), (73, 884), (332, 884)],
            [(332, 1290), (332, 1550), (73, 1550), (73, 1290)],
            [(2392, 922), (2324, 1174), (2073, 1107), (2141, 855)],
            [(2140, 1261), (2392, 1329), (2325, 1579), (2073, 1512)],
            [(73, 739), (73, 479), (332, 479), (332, 739)],
            [(73, 73), (332, 73), (332, 333), (73, 333)],
            [(2325, 768), (2073, 700), (2141, 449), (2392, 516)],
            [(2073, 294), (2141, 43), (2392, 110), (2324, 361)],
            [(700, 1261), (768, 1512), (516, 1580), (449, 1328)],
            [(1062, 1243), (1192, 1468), (967, 1598), (837, 1373)],
            [(768, 1106), (517, 1174), (449, 922), (701, 855)],
            [(1421, 1237), (1605, 1421), (1421, 1605), (1237, 1421)],
            [(1779, 1243), (2004, 1373), (1874, 1599), (1649, 1468)],
            [(2004, 967), (1874, 1192), (1649, 1062), (1779, 837)],
            [(449, 110), (700, 43), (768, 295), (517, 362)],
            [(836, 155), (1062, 25), (1192, 250), (967, 380)],
            [(516, 768), (449, 517), (701, 449), (768, 700)],
            [(1237, 203), (1421, 18) if self.WIN else (1421, 19), (1605, 203), (1421, 387)],
            [(1649, 250), (1779, 25), (2004, 155), (1874, 380)],
            [(1193, 1062), (967, 1192), (837, 967), (1062, 837)],
            [(1605, 1015), (1420, 1199), (1237, 1015), (1421, 831)],
            [(967, 787), (837, 561), (1062, 431), (1192, 657)],
            [(1421, 793), (1237, 609), (1421, 425), (1605, 609)],
            [(1874, 786), (1649, 656), (1779, 431), (2004, 561)],
        ]
        assert len(barcodes) == len(expected_barcodes_coordinates) == 24
        if self.DEBUG:
            with Image.open(multi_dm_image) as image:
                draw = ImageDraw.ImageDraw(image)
                for barcode in barcodes:
                    draw.line(barcode.coordinates, fill=(255, 0, 0), width=8, joint="curve")
                image.show()
        for barcode, expected_coordinates in zip(barcodes, expected_barcodes_coordinates):
            assert barcode.type == Barcode.Type.DATAMATRIX
            assert barcode.data == str(barcode) == "This is a datamatrix containing € sign and 日本語 characters"
            assert barcode.coordinates == expected_coordinates
            if self.DEBUG:
                with Image.open(multi_dm_image) as image:
                    w, h = image.size
                    cropped_image = crop(image, barcode.coordinates, fillcolor=(255, 0, 255), cut_out=True)
                    cw, ch = cropped_image.size
                    debug_image = Image.new(mode=image.mode, size=(w, h + ch), color=(255, 255, 255))
                    ImageDraw.ImageDraw(image).line(barcode.coordinates, fill=(255, 0, 0), width=8, joint="curve")
                    debug_image.paste(image)
                    debug_image.paste(cropped_image, ((w - cw) // 2, h))
                    debug_image.show()
