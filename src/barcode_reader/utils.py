import itertools
from collections import defaultdict

# noinspection PyPackageRequirements
import cv2
import numpy as np


def get_groups_of_contours(image):
    """
    Return contours of black regions grouped by level (in case of nested contours)

    :param PIL.Image.Image image: the image in which looking for contours
    :return: the different groups of contours
    :rtype: list[list[numpy.ndarray]]
    """
    # We apply gaussian blur to reduce details and get less contours to compute
    # cv_im = cv2.GaussianBlur(np.array(image.convert("L")), (15, 15), cv2.BORDER_DEFAULT)
    # im = image.convert("L")
    # im.frombytes(cv_im)
    # im.show()
    _, bin_image = cv2.threshold(
        cv2.GaussianBlur(np.array(image.convert("L")), (15, 15), cv2.BORDER_DEFAULT), 191, 255, cv2.THRESH_BINARY
    )
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


def detect_barcodes(image, quiet_dist=10, min_area=12000):
    """
    Detect areas on given image which may contain a barcode.

    :param PIL.Image.Image image: the image to analyze
    :param int quiet_dist: the quiet distance in pixels (i.e. blank zone around barcodes)
    :param int min_area: the min area in pixels x pixels a barcode must have
    :return: a list of (opencv) rectangles for each area detected. Each rectangle is defined by a tuple containing:
      * a tuple with the coordinates of the rectangle's center
      * a tuple with the width anf height of the rectangle
      * the angle of the rectangle
    :rtype: list[tuple[tuple[int, int], tuple[int, int], float]]
    """
    return [
        cv2.minAreaRect(contour) for contour in itertools.chain.from_iterable(
            merge_contours(contours, quiet_dist) for contours in get_groups_of_contours(image)
        ) if cv2.contourArea(contour) > min_area
    ]
