import itertools
from collections import defaultdict

# noinspection PyPackageRequirements
import cv2
import numpy as np
from PIL import Image


def get_groups_of_contours(image, fast=True):
    """
    Return contours of black regions grouped by level (in case of nested contours)

    :param numpy.ndarray image: the (opencv) gray image in which to look for contours
    :param bool fast: if ``True``, make the detection faster by blurring image before detection. This will make the
      contours coordinates less accurate (a little larger than real contours). If ``False``, contours coordinates
      are more accurate.
    :return: the different groups of contours
    :rtype: list[list[numpy.ndarray]]
    """
    if fast:
        # We apply gaussian blur to reduce details and get less contours to compute
        image = cv2.GaussianBlur(image, (15, 15), cv2.BORDER_DEFAULT)
    _, bin_image = cv2.threshold(image, 191, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(bin_image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    # group contours by parents
    groups = defaultdict(list)
    for contour, (_, _, _, parent) in zip(contours, hierarchy[0]):
        if parent >= 0:
            groups[parent].append(contour)
    return list(groups.values())


def merge_contours(contours, dist):
    """
    For given list of contours, merge contours that are closer than given distance, and return the convex contour
    each grouped contours

    :param list[numpy.ndarray] contours: the list of contours to group together
    :param int dist: the distance under which contours should be merged
    :return: the list of new contours after grouping close contours
    :rtype: list[numpy.ndarray]
    """

    def can_merge(cnt1, cnt2):
        """
        Return whether or not the 2 given contours can be merged if there are close to each other

        :param list[numpy.ndarray] cnt1: first contour to compare
        :param list[numpy.ndarray] cnt2: second contour to compare
        :return: whether or not the two contours can be merged
        :rtype: bool
        """
        return any(
            cv2.pointPolygonTest(cnt2, tuple(pt1[0]), True) >= -dist for pt1 in cnt1
        ) or any(
            cv2.pointPolygonTest(cnt1, tuple(pt2[0]), True) >= -dist for pt2 in cnt2
        )

    contours = [cv2.convexHull(contour) for contour in contours]
    merged_contours = []
    for contour in contours:
        new_contours = []
        for merged_contour in merged_contours:
            if can_merge(contour, merged_contour):
                contour = cv2.convexHull(np.concatenate((contour, merged_contour)))
            else:
                new_contours.append(merged_contour)
        merged_contours = new_contours
        merged_contours.append(contour)
    return merged_contours


def detect_barcodes_pil(image, quiet_dist=10, min_area=12000, fast=True):
    """
    Detect areas on given image which may contain a barcode.

    :param PIL.Image.Image image: the image to analyze
    :param int quiet_dist: the quiet distance in pixels (i.e. blank zone around barcodes)
    :param int min_area: the min area in pixels x pixels a barcode must have
    :param bool fast: if ``True``, make the detection faster. This will make the contours coordinates less accurate
      (a little larger than real contours). If ``False``, contours coordinates are more accurate.
    :return: a list of (opencv) rectangles for each area detected. Each rectangle is defined by a tuple containing:
      * a tuple with the coordinates of the rectangle's center
      * a tuple with the width anf height of the rectangle
      * the angle of the rectangle
    :rtype: list[tuple[tuple[int, int], tuple[int, int], float]]
    """
    if image.mode != "L":
        image = image.convert("L")
    return detect_barcodes_cv2_gray(np.array(image), quiet_dist=quiet_dist, min_area=min_area, fast=fast)


def detect_barcodes_cv2(image, quiet_dist=10, min_area=12000, fast=True):
    """
    Detect areas on given image which may contain a barcode.

    :param numpy.ndarray image: the (opencv) gray or BGR image to analyze
    :param int quiet_dist: the quiet distance in pixels (i.e. blank zone around barcodes)
    :param int min_area: the min area in pixels x pixels a barcode must have
    :param bool fast: if ``True``, make the detection faster. This will make the contours coordinates less accurate
      (a little larger than real contours). If ``False``, contours coordinates are more accurate.
    :return: a list of (opencv) rectangles for each area detected. Each rectangle is defined by a tuple containing:
      * a tuple with the coordinates of the rectangle's center
      * a tuple with the width anf height of the rectangle
      * the angle of the rectangle
    :rtype: list[tuple[tuple[int, int], tuple[int, int], float]]
    """
    if len(image.shape) > 2:
        # Assume BGR image
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return detect_barcodes_cv2_gray(image, quiet_dist=quiet_dist, min_area=min_area, fast=fast)


def detect_barcodes_cv2_gray(image, quiet_dist=10, min_area=12000, fast=True):
    """
    Detect areas on given image which may contain a barcode.

    :param numpy.ndarray image: the (opencv) gray image to analyze
    :param int quiet_dist: the quiet distance in pixels (i.e. blank zone around barcodes)
    :param int min_area: the min area in pixels x pixels a barcode must have
    :param bool fast: if ``True``, make the detection faster. This will make the contours coordinates less accurate
      (a little larger than real contours). If ``False``, contours coordinates are more accurate.
    :return: a list of (opencv) rectangles for each area detected. Each rectangle is defined by a tuple containing:
      * a tuple with the coordinates of the rectangle's center
      * a tuple with the width anf height of the rectangle
      * the angle of the rectangle
    :rtype: list[tuple[tuple[int, int], tuple[int, int], float]]
    """
    return [
        cv2.minAreaRect(contour) for contour in itertools.chain.from_iterable(
            merge_contours(contours, quiet_dist) for contours in get_groups_of_contours(image, fast=fast)
        ) if cv2.contourArea(contour) > min_area
    ]


def detect_barcodes(image, quiet_dist=10, min_area=12000, fast=True):
    """
    Detect areas on given image which may contain a barcode.

    :param image: the (pillow or opencv) image to crop
    :type image: Union[PIL.Image.Image,numpy.ndarray]
    :param int quiet_dist: the quiet distance in pixels (i.e. blank zone around barcodes)
    :param int min_area: the min area in pixels x pixels a barcode must have
    :param bool fast: if ``True``, make the detection faster. This will make the contours coordinates less accurate
      (a little larger than real contours). If ``False``, contours coordinates are more accurate.
    :return: a list of (opencv) rectangles for each area detected. Each rectangle is defined by a tuple containing:
      * a tuple with the coordinates of the rectangle's center
      * a tuple with the width anf height of the rectangle
      * the angle of the rectangle
    :rtype: list[tuple[tuple[int, int], tuple[int, int], float]]
    """
    if isinstance(image, Image.Image):
        return detect_barcodes_pil(image, quiet_dist=quiet_dist, min_area=min_area, fast=fast)
    else:
        return detect_barcodes_cv2(image, quiet_dist=quiet_dist, min_area=min_area, fast=fast)
