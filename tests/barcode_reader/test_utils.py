import sys

import cv2
import numpy as np
from PIL import Image

# noinspection PyProtectedMember
from barcode_reader.utils import detect_barcodes


class TestUtilsPil:

    DEBUG = False
    # Some results depend on the running platform. May some some rounding difference !
    WIN = sys.platform == "win32"
    DARWIN = sys.platform == "darwin"

    def test_detect_qrcode(self, resources):
        quiet_dist = 10
        min_area = 12000
        multi_dm_image = resources / "qrcode.png"
        with Image.open(multi_dm_image).convert("RGB") as image:
            rectangles = [
                np.int0(cv2.boxPoints(((center_x, center_y), (width + 2 * quiet_dist, height + 2 * quiet_dist), angle)))
                for (center_x, center_y), (width, height), angle in detect_barcodes(image, quiet_dist, min_area)
            ]
            assert [[tuple(p) for p in rect] for rect in rectangles] == [
                [(24, 274), (24, 23), (274, 23), (274, 274)],
            ]
            if self.DEBUG:
                cv_im = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                cv2.drawContours(cv_im, rectangles, -1, (0, 255, 0), 3)
                image.frombytes(cv2.cvtColor(cv_im, cv2.COLOR_BGR2RGB))
                image.show()

    def test_detect_qrcode_multi(self, resources):
        quiet_dist = 10
        min_area = 12000
        multi_dm_image = resources / "qrcode_multi.png"
        with Image.open(multi_dm_image).convert("RGB") as image:
            rectangles = [
                np.int0(cv2.boxPoints(((center_x, center_y), (width + 2 * quiet_dist, height + 2 * quiet_dist), angle)))
                for (center_x, center_y), (width, height), angle in detect_barcodes(image, quiet_dist, min_area)
            ]
            assert [[tuple(p) for p in rect] for rect in rectangles] == [
                [(87, 1615), (87, 1364), (338, 1364), (338, 1615)],
                [(2187, 1578), (2253, 1335), (2496, 1400), (2431, 1644)],
                [(484, 1400), (727, 1335), (793, 1578), (549, 1644)],
                [(1744, 1535), (1870, 1317), (2088, 1443), (1962, 1661)],
                [(892, 1443), (1110, 1318), (1236, 1535), (1018, 1661)],
                [(1313, 1489), (1490, 1312), (1667, 1489), (1490, 1666)],
                [(87, 1191), (87, 939), (337, 939), (337, 1191)],
                [(484, 975), (728, 910), (793, 1153), (550, 1219)],
                [(2188, 1153), (2254, 909), (2497, 975), (2432, 1218)],
                [(1745, 1110), (1871, 892), (2089, 1018), (1963, 1236)],
                [(893, 1018), (1111, 892), (1237, 1110), (1019, 1236)],
                [(1314, 1064), (1491, 887), (1668, 1064), (1491, 1241)],
                [(85, 763), (85, 512), (337, 512), (337, 763)],
                [(2188, 728), (2253, 484), (2497, 550), (2431, 793)],
                [(483, 550), (727, 484), (792, 728), (549, 793)],
                [(1744, 685), (1870, 467), (2088, 593), (1962, 811)],
                [(892, 593), (1110, 467), (1236, 685), (1018, 810)],
                [(1313, 639), (1490, 462), (1667, 639), (1490, 816)],
                [(87, 337), (87, 85), (337, 86), (337, 337)],
                [(2187, 301), (2252, 58), (2496, 123), (2430, 367)],
                [(483, 123), (726, 57), (792, 301), (548, 366)],
                [(1743, 258), (1869, 40), (2087, 166), (1961, 384)],
                [(892, 166), (1109, 40), (1235, 258), (1017, 384)],
                [(1312, 212), (1489, 35), (1666, 212), (1489, 389)],
            ]
            if self.DEBUG:
                cv_im = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                cv2.drawContours(cv_im, rectangles, -1, (0, 255, 0), 3)
                image.frombytes(cv2.cvtColor(cv_im, cv2.COLOR_BGR2RGB))
                image.show()

    def test_detect_datamatrix(self, resources):
        quiet_dist = 10
        min_area = 12000
        multi_dm_image = resources / "datamatrix.png"
        with Image.open(multi_dm_image).convert("RGB") as image:
            rectangles = [
                np.int0(cv2.boxPoints(((center_x, center_y), (width + 2 * quiet_dist, height + 2 * quiet_dist), angle)))
                for (center_x, center_y), (width, height), angle in detect_barcodes(image, quiet_dist, min_area)
            ]
            assert [[tuple(p) for p in rect] for rect in rectangles] == [
                [(-4, 282), (-4, -2), (280, -2), (280, 282)],
            ]
            if self.DEBUG:
                cv_im = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                cv2.drawContours(cv_im, rectangles, -1, (0, 255, 0), 3)
                image.frombytes(cv2.cvtColor(cv_im, cv2.COLOR_BGR2RGB))
                image.show()

    def test_detect_datamatrix_multi(self, resources):
        quiet_dist = 10
        min_area = 12000
        multi_dm_image = resources / "datamatrix_multi.png"
        with Image.open(multi_dm_image).convert("RGB") as image:
            rectangles = [
                np.int0(cv2.boxPoints(((center_x, center_y), (width + 2 * quiet_dist, height + 2 * quiet_dist), angle)))
                for (center_x, center_y), (width, height), angle in detect_barcodes(image, quiet_dist, min_area)
            ]
            assert [[tuple(p) for p in rect] for rect in rectangles] == [
                [(59, 1561), (59, 1276), (343, 1276), (343, 1561)],
                [(2056, 1521), (2130, 1246), (2405, 1320), (2332, 1595)],
                [(432, 1319), (707, 1245), (781, 1520), (506, 1594)],
                [(1630, 1472), (1773, 1226), (2019, 1368), (1877, 1615)],
                [(818, 1368), (1065, 1225), (1207, 1472), (961, 1614)],
                [(1218, 1420), (1419, 1219), (1619, 1420), (1419, 1621)],
                [(61, 1156), (61, 871), (345, 871), (345, 1156)],
                [(2057, 1114), (2131, 838), (2406, 912), (2332, 1187)],
                [(434, 912), (709, 838), (783, 1114), (508, 1187)],
                [(1631, 1065), (1774, 818), (2020, 961), (1878, 1207)],
                [(820, 961), (1066, 818), (1209, 1065), (962, 1207)],
                [(1219, 1013), (1420, 812), (1621, 1013), (1420, 1213)],
                [(61, 752), (61, 467), (345, 467), (345, 752)],
                [(435, 508), (710, 434), (784, 709), (508, 783)],
                [(2059, 708), (2132, 433), (2408, 507), (2334, 782)],
                [(821, 556), (1067, 414), (1210, 660), (963, 803)],
                [(1633, 660), (1775, 413), (2022, 556), (1879, 802)],
                [(1221, 608), (1422, 407), (1622, 608), (1422, 809)],
                [(59, 345), (59, 61), (343, 61), (343, 345)],
                [(2058, 304), (2132, 29), (2407, 102), (2333, 378)],
                [(433, 102), (708, 29), (782, 304), (507, 378)],
                [(1632, 255), (1774, 9), (2021, 151), (1878, 398)],
                [(819, 151), (1066, 9), (1208, 255), (962, 398)],
                [(1219, 204), (1420, 3), (1621, 204), (1420, 404)],
            ]
            if self.DEBUG:
                cv_im = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                cv2.drawContours(cv_im, rectangles, -1, (0, 255, 0), 3)
                image.frombytes(cv2.cvtColor(cv_im, cv2.COLOR_BGR2RGB))
                image.show()


class TestUtilsCv2:

    DEBUG = False
    # Some results depend on the running platform. May some some rounding difference !
    WIN = sys.platform == "win32"
    DARWIN = sys.platform == "darwin"

    def test_detect_qrcode(self, resources):
        quiet_dist = 10
        min_area = 12000
        multi_dm_image = resources / "qrcode.png"
        image = cv2.imread(str(multi_dm_image), cv2.IMREAD_UNCHANGED)
        rectangles = [
            np.int0(cv2.boxPoints(((center_x, center_y), (width + 2 * quiet_dist, height + 2 * quiet_dist), angle)))
            for (center_x, center_y), (width, height), angle in detect_barcodes(image, quiet_dist, min_area)
        ]
        assert [[tuple(p) for p in rect] for rect in rectangles] == [
            [(24, 274), (24, 23), (274, 23), (274, 274)],
        ]
        if self.DEBUG:
            cv2.drawContours(image, rectangles, -1, (0, 255, 0), 3)
            Image.frombytes("RGB", image.shape[1::-1], cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).show()

    def test_detect_qrcode_multi(self, resources):
        quiet_dist = 10
        min_area = 12000
        multi_dm_image = resources / "qrcode_multi.png"
        image = cv2.imread(str(multi_dm_image), cv2.IMREAD_UNCHANGED)
        rectangles = [
            np.int0(cv2.boxPoints(((center_x, center_y), (width + 2 * quiet_dist, height + 2 * quiet_dist), angle)))
            for (center_x, center_y), (width, height), angle in detect_barcodes(image, quiet_dist, min_area)
        ]
        assert [[tuple(p) for p in rect] for rect in rectangles] == [
            [(87, 1615), (87, 1364), (338, 1364), (338, 1615)],
            [(2187, 1578), (2253, 1335), (2496, 1400), (2431, 1644)],
            [(484, 1400), (727, 1335), (793, 1578), (549, 1644)],
            [(1744, 1535), (1870, 1317), (2088, 1443), (1962, 1661)],
            [(892, 1443), (1110, 1318), (1236, 1535), (1018, 1661)],
            [(1313, 1489), (1490, 1312), (1667, 1489), (1490, 1666)],
            [(87, 1191), (87, 939), (337, 939), (337, 1191)],
            [(484, 975), (728, 910), (793, 1153), (550, 1219)],
            [(2188, 1153), (2254, 909), (2497, 975), (2432, 1218)],
            [(1745, 1110), (1871, 892), (2089, 1018), (1963, 1236)],
            [(893, 1018), (1111, 892), (1237, 1110), (1019, 1236)],
            [(1314, 1064), (1491, 887), (1668, 1064), (1491, 1241)],
            [(85, 763), (85, 512), (337, 512), (337, 763)],
            [(2188, 728), (2253, 484), (2497, 550), (2431, 793)],
            [(483, 550), (727, 484), (792, 728), (549, 793)],
            [(1744, 685), (1870, 467), (2088, 593), (1962, 811)],
            [(892, 593), (1110, 467), (1236, 685), (1018, 810)],
            [(1313, 639), (1490, 462), (1667, 639), (1490, 816)],
            [(87, 337), (87, 85), (337, 86), (337, 337)],
            [(2187, 301), (2252, 58), (2496, 123), (2430, 367)],
            [(483, 123), (726, 57), (792, 301), (548, 366)],
            [(1743, 258), (1869, 40), (2087, 166), (1961, 384)],
            [(892, 166), (1109, 40), (1235, 258), (1017, 384)],
            [(1312, 212), (1489, 35), (1666, 212), (1489, 389)],
        ]
        if self.DEBUG:
            cv2.drawContours(image, rectangles, -1, (0, 255, 0), 3)
            Image.frombytes("RGB", image.shape[1::-1], cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).show()

    def test_detect_datamatrix(self, resources):
        quiet_dist = 10
        min_area = 12000
        multi_dm_image = resources / "datamatrix.png"
        image = cv2.imread(str(multi_dm_image), cv2.IMREAD_UNCHANGED)
        rectangles = [
            np.int0(cv2.boxPoints(((center_x, center_y), (width + 2 * quiet_dist, height + 2 * quiet_dist), angle)))
            for (center_x, center_y), (width, height), angle in detect_barcodes(image, quiet_dist, min_area)
        ]
        assert [[tuple(p) for p in rect] for rect in rectangles] == [
            [(-4, 282), (-4, -2), (280, -2), (280, 282)],
        ]
        if self.DEBUG:
            cv2.drawContours(image, rectangles, -1, (0, 255, 0), 3)
            Image.frombytes("RGB", image.shape[1::-1], cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).show()

    def test_detect_datamatrix_multi(self, resources):
        quiet_dist = 10
        min_area = 12000
        multi_dm_image = resources / "datamatrix_multi.png"
        image = cv2.imread(str(multi_dm_image), cv2.IMREAD_UNCHANGED)
        rectangles = [
            np.int0(cv2.boxPoints(((center_x, center_y), (width + 2 * quiet_dist, height + 2 * quiet_dist), angle)))
            for (center_x, center_y), (width, height), angle in detect_barcodes(image, quiet_dist, min_area)
        ]
        assert [[tuple(p) for p in rect] for rect in rectangles] == [
            [(59, 1561), (59, 1276), (343, 1276), (343, 1561)],
            [(2056, 1521), (2130, 1246), (2405, 1320), (2332, 1595)],
            [(432, 1319), (707, 1245), (781, 1520), (506, 1594)],
            [(1630, 1472), (1773, 1226), (2019, 1368), (1877, 1615)],
            [(818, 1368), (1065, 1225), (1207, 1472), (961, 1614)],
            [(1218, 1420), (1419, 1219), (1619, 1420), (1419, 1621)],
            [(61, 1156), (61, 871), (345, 871), (345, 1156)],
            [(2057, 1114), (2131, 838), (2406, 912), (2332, 1187)],
            [(434, 912), (709, 838), (783, 1114), (508, 1187)],
            [(1631, 1065), (1774, 818), (2020, 961), (1878, 1207)],
            [(820, 961), (1066, 818), (1209, 1065), (962, 1207)],
            [(1219, 1013), (1420, 812), (1621, 1013), (1420, 1213)],
            [(61, 752), (61, 467), (345, 467), (345, 752)],
            [(435, 508), (710, 434), (784, 709), (508, 783)],
            [(2059, 708), (2132, 433), (2408, 507), (2334, 782)],
            [(821, 556), (1067, 414), (1210, 660), (963, 803)],
            [(1633, 660), (1775, 413), (2022, 556), (1879, 802)],
            [(1221, 608), (1422, 407), (1622, 608), (1422, 809)],
            [(59, 345), (59, 61), (343, 61), (343, 345)],
            [(2058, 304), (2132, 29), (2407, 102), (2333, 378)],
            [(433, 102), (708, 29), (782, 304), (507, 378)],
            [(1632, 255), (1774, 9), (2021, 151), (1878, 398)],
            [(819, 151), (1066, 9), (1208, 255), (962, 398)],
            [(1219, 204), (1420, 3), (1621, 204), (1420, 404)],
        ]
        if self.DEBUG:
            cv2.drawContours(image, rectangles, -1, (0, 255, 0), 3)
            Image.frombytes("RGB", image.shape[1::-1], cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).show()
