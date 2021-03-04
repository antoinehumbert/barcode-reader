/* This class is a rewrite of the GenericMultipleBarcodeReader from zxing allowing finding *all* barcodes in an image
even if several barcodes have the same value.
*/
// package com.google.zxing.multi;

import com.google.zxing.multi.MultipleBarcodeReader;
import com.google.zxing.BinaryBitmap;
import com.google.zxing.DecodeHintType;
import com.google.zxing.NotFoundException;
import com.google.zxing.Reader;
import com.google.zxing.ReaderException;
import com.google.zxing.Result;
import com.google.zxing.ResultPoint;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * <p>Attempts to locate multiple barcodes in an image by repeatedly decoding portion of the image.
 * After one barcode is found, the areas left, above, right and below the barcode's
 * {@link ResultPoint}s are scanned, recursively.</p>
 *
 * <p>A caller may want to also employ {@link ByQuadrantReader} when attempting to find multiple
 * 2D barcodes, like QR Codes, in an image, where the presence of multiple barcodes might prevent
 * detecting any one of them.</p>
 *
 * <p>That is, instead of passing a {@link Reader} a caller might pass
 * {@code new ByQuadrantReader(reader)}.</p>
 *
 * @author Sean Owen
 */
public final class GenericMultipleBarcodeReaderEx implements MultipleBarcodeReader {

  private static final int MIN_DIMENSION_TO_RECUR = 100;
  private static final int MAX_DEPTH = 4;

  static final Result[] EMPTY_RESULT_ARRAY = new Result[0];

  private final Reader delegate;

  public GenericMultipleBarcodeReaderEx(Reader delegate) {
    this.delegate = delegate;
  }

  @Override
  public Result[] decodeMultiple(BinaryBitmap image) throws NotFoundException {
    return decodeMultiple(image, null);
  }

  @Override
  public Result[] decodeMultiple(BinaryBitmap image, Map<DecodeHintType,?> hints)
      throws NotFoundException {
    List<Result> results = new ArrayList<>();
    doDecodeMultiple(image, hints, results, 0, 0, 0);
    if (results.isEmpty()) {
      throw NotFoundException.getNotFoundInstance();
    }
    return results.toArray(EMPTY_RESULT_ARRAY);
  }

  private void doDecodeMultiple(BinaryBitmap image,
                                Map<DecodeHintType,?> hints,
                                List<Result> results,
                                int xOffset,
                                int yOffset,
                                int currentDepth) {
    if (currentDepth > MAX_DEPTH) {
      return;
    }

    Result result;
    try {
      result = delegate.decode(image, hints);
    } catch (ReaderException ignored) {
      return;
    }
    result = translateResultPoints(result, xOffset, yOffset);
    ResultPoint[] resultPoints = result.getResultPoints();
    if (resultPoints == null || resultPoints.length == 0) {
      boolean alreadyFound = false;
      for (Result existingResult : results) {
        if (existingResult.getText().equals(result.getText())) {
          alreadyFound = true;
          break;
        }
      }
      if (!alreadyFound) {
        results.add(result);
      }
      return;
    }

    boolean alreadyFound = false;
    for (Result existingResult : results) {
      if (existingResult.getText().equals(result.getText())) {
        // Also check that resultPoints are the same
        boolean samePoints = true;
        ResultPoint[] existingPoints = existingResult.getResultPoints();
        if (existingPoints != null && existingPoints.length == resultPoints.length) {
          for (int i = 0; i < resultPoints.length; i++) {
            if (!resultPoints[i].equals(existingPoints[i])) {
              samePoints = false;
              break;
            }
          }
        }
        if (samePoints) {
          alreadyFound = true;
          break;
        }
      }
    }
    if (!alreadyFound) {
      results.add(result);
    }
    int width = image.getWidth();
    int height = image.getHeight();
    float minX = width;
    float minY = height;
    float maxX = 0.0f;
    float maxY = 0.0f;
    for (ResultPoint point : resultPoints) {
      if (point == null) {
        continue;
      }
      float x = point.getX();
      float y = point.getY();
      if (x < minX) {
        minX = x;
      }
      if (y < minY) {
        minY = y;
      }
      if (x > maxX) {
        maxX = x;
      }
      if (y > maxY) {
        maxY = y;
      }
    }

    // Decode left of barcode
    if (minX > MIN_DIMENSION_TO_RECUR) {
      doDecodeMultiple(image.crop(0, 0, (int) minX, height),
                       hints, results,
                       xOffset, yOffset,
                       currentDepth + 1);
    }
    // Decode above barcode
    if (minY > MIN_DIMENSION_TO_RECUR) {
      doDecodeMultiple(image.crop(0, 0, width, (int) minY),
                       hints, results,
                       xOffset, yOffset,
                       currentDepth + 1);
    }
    // Decode right of barcode
    if (maxX < width - MIN_DIMENSION_TO_RECUR) {
      doDecodeMultiple(image.crop((int) maxX, 0, width - (int) maxX, height),
                       hints, results,
                       xOffset + (int) maxX, yOffset,
                       currentDepth + 1);
    }
    // Decode below barcode
    if (maxY < height - MIN_DIMENSION_TO_RECUR) {
      doDecodeMultiple(image.crop(0, (int) maxY, width, height - (int) maxY),
                       hints, results,
                       xOffset, yOffset + (int) maxY,
                       currentDepth + 1);
    }
  }

  private static Result translateResultPoints(Result result, int xOffset, int yOffset) {
    ResultPoint[] oldResultPoints = result.getResultPoints();
    if (oldResultPoints == null) {
      return result;
    }
    ResultPoint[] newResultPoints = new ResultPoint[oldResultPoints.length];
    for (int i = 0; i < oldResultPoints.length; i++) {
      ResultPoint oldPoint = oldResultPoints[i];
      if (oldPoint != null) {
        newResultPoints[i] = new ResultPoint(oldPoint.getX() + xOffset, oldPoint.getY() + yOffset);
      }
    }
    Result newResult = new Result(result.getText(),
                                  result.getRawBytes(),
                                  result.getNumBits(),
                                  newResultPoints,
                                  result.getBarcodeFormat(),
                                  result.getTimestamp());
    newResult.putAllMetadata(result.getResultMetadata());
    return newResult;
  }

}
