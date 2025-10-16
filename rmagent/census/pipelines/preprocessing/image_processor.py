"""
Image preprocessing for census extraction.

Handles deskewing, denoising, contrast enhancement, and binarization
to prepare census images for optimal OCR performance.

Key techniques:
- Deskewing via Hough line detection
- Gaussian blur for denoising
- CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Adaptive thresholding for binarization
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class CensusImageProcessor:
    """Preprocesses census images for OCR extraction."""

    def __init__(
        self,
        deskew: bool = False,  # Disabled by default - needs improvement
        denoise: bool = False,  # Disabled by default - degrades lines
        enhance_contrast: bool = True,
        binarize: bool = False,  # Disabled temporarily to test grayscale
    ):
        """
        Initialize image processor with preprocessing options.

        Args:
            deskew: Apply rotation correction
            denoise: Apply noise reduction
            enhance_contrast: Apply CLAHE contrast enhancement
            binarize: Apply adaptive thresholding
        """
        self.deskew = deskew
        self.denoise = denoise
        self.enhance_contrast = enhance_contrast
        self.binarize = binarize

        # Metrics (always calculated, whether or not we apply corrections)
        self.last_skew_score = 0.0
        self.last_noise_score = 0.0

    def process_image(
        self, image_path: str | Path, output_path: Optional[str | Path] = None
    ) -> np.ndarray:
        """
        Process a census image through the full pipeline.

        Args:
            image_path: Path to input image
            output_path: Optional path to save processed image

        Returns:
            Processed image as numpy array (grayscale)

        Raises:
            FileNotFoundError: If image_path does not exist
            ValueError: If image cannot be loaded
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        logger.info(f"Processing image: {image_path.name}")

        # Load image
        image = self._load_image(image_path)

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # ALWAYS measure quality metrics (whether or not we apply corrections)
        self.last_skew_score = self._measure_skew(image)
        self.last_noise_score = self._measure_noise(image)

        logger.info(f"Image quality: skew={self.last_skew_score:.1f}/100, noise={self.last_noise_score:.1f}/100")

        # Apply preprocessing steps (if enabled)
        if self.deskew:
            image = self._deskew_image(image)
            logger.info(f"Applied deskewing")

        if self.denoise:
            image = self._denoise_image(image)
            logger.info(f"Applied denoising")

        if self.enhance_contrast:
            image = self._enhance_contrast(image)

        if self.binarize:
            image = self._binarize_image(image)

        # Save if output path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), image)
            logger.info(f"Saved processed image: {output_path}")

        return image

    def _load_image(self, image_path: Path) -> np.ndarray:
        """
        Load image from disk.

        Args:
            image_path: Path to image file

        Returns:
            Image as numpy array

        Raises:
            ValueError: If image cannot be loaded
        """
        image = cv2.imread(str(image_path))
        if image is None:
            # Try with PIL as fallback
            try:
                pil_image = Image.open(image_path)
                image = np.array(pil_image)
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            except Exception as e:
                raise ValueError(f"Failed to load image: {e}") from e

        logger.debug(f"Loaded image: shape={image.shape}, dtype={image.dtype}")
        return image

    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Correct image rotation using Hough line detection.

        Detects dominant lines in the image and rotates to align them
        horizontally. Useful for correcting scanner skew.

        Args:
            image: Grayscale input image

        Returns:
            Deskewed image
        """
        # Apply edge detection
        edges = cv2.Canny(image, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is None or len(lines) == 0:
            logger.debug("No lines detected for deskewing")
            return image

        # Calculate angles of detected lines
        angles = []
        for line in lines:
            rho, theta = line[0]
            # Convert to degrees, normalize to [-45, 45]
            angle = (theta * 180 / np.pi) - 90
            if -45 <= angle <= 45:
                angles.append(angle)

        if not angles:
            logger.debug("No valid angles for deskewing")
            return image

        # Use median angle for robustness
        median_angle = np.median(angles)

        # Only rotate if angle is significant (> 0.5 degrees)
        if abs(median_angle) < 0.5:
            logger.debug(f"Skew angle too small: {median_angle:.2f}°")
            return image

        logger.debug(f"Deskewing by {median_angle:.2f}°")

        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image,
            M,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        return rotated

    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """
        Reduce noise using Gaussian blur.

        Args:
            image: Input image

        Returns:
            Denoised image
        """
        # Use small kernel to preserve text sharpness
        denoised = cv2.GaussianBlur(image, (3, 3), 0)
        logger.debug("Applied Gaussian denoising")
        return denoised

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).

        CLAHE improves local contrast without over-amplifying noise,
        making faded or uneven text more readable.

        Args:
            image: Grayscale input image

        Returns:
            Contrast-enhanced image
        """
        # Create CLAHE object with subtle settings
        # clipLimit=1.0 provides minimal enhancement without darkening backgrounds
        clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        logger.debug("Applied CLAHE contrast enhancement (subtle: clipLimit=1.0)")
        return enhanced

    def _binarize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Convert to binary (black/white) using adaptive thresholding.

        Adaptive thresholding handles varying lighting conditions better
        than global thresholding, crucial for historical documents.

        Args:
            image: Grayscale input image

        Returns:
            Binarized image (0=black, 255=white)
        """
        # Use Gaussian adaptive thresholding
        binary = cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Block size
            2,  # Constant subtracted from mean
        )
        logger.debug("Applied adaptive thresholding")
        return binary

    def _measure_skew(self, image: np.ndarray) -> float:
        """
        Measure image skew without applying correction.

        Returns a score from 0-100 where:
        - 0 = perfectly straight (no skew detected)
        - 100 = severely skewed (>10 degrees)

        Args:
            image: Grayscale input image

        Returns:
            Skew score (0-100)
        """
        # Detect edges
        edges = cv2.Canny(image, 50, 150, apertureSize=3)

        # Detect lines
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is None or len(lines) == 0:
            return 0.0  # Can't measure skew if no lines detected

        # Calculate angles
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            if -45 <= angle <= 45:
                angles.append(angle)

        if not angles:
            return 0.0

        # Get median angle
        median_angle = abs(np.median(angles))

        # Convert to 0-100 scale (10 degrees = 100)
        skew_score = min(100.0, (median_angle / 10.0) * 100.0)

        return skew_score

    def _measure_noise(self, image: np.ndarray) -> float:
        """
        Measure image noise level without applying denoising.

        Uses Laplacian variance method - higher variance indicates more noise/detail.
        We score it such that:
        - 0 = very clean/sharp (low variance = low noise)
        - 100 = very noisy (high variance)

        Args:
            image: Grayscale input image

        Returns:
            Noise score (0-100)
        """
        # Calculate Laplacian variance
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        variance = laplacian.var()

        # Normalize to 0-100 scale
        # Typical values: clean scans ~100-500, noisy scans ~1000+
        # Using logarithmic scale for better distribution
        if variance < 10:
            noise_score = 0.0
        else:
            # log scale: 100->20, 500->45, 1000->60, 2000->76
            noise_score = min(100.0, (np.log10(variance) - 1) * 33.0)

        return max(0.0, noise_score)

    def process_batch(
        self,
        image_paths: list[str | Path],
        output_dir: str | Path,
        max_workers: int = 4,
    ) -> list[Path]:
        """
        Process multiple images in parallel.

        Args:
            image_paths: List of input image paths
            output_dir: Directory for processed images
            max_workers: Number of parallel workers

        Returns:
            List of output paths for processed images
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_paths = []

        def process_one(img_path: Path) -> Path:
            output_path = output_dir / f"processed_{img_path.name}"
            self.process_image(img_path, output_path)
            return output_path

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_one, Path(p)): p for p in image_paths
            }

            for future in as_completed(futures):
                try:
                    output_path = future.result()
                    output_paths.append(output_path)
                    logger.info(f"Processed: {output_path.name}")
                except Exception as e:
                    img_path = futures[future]
                    logger.error(f"Failed to process {img_path}: {e}")

        logger.info(f"Batch processing complete: {len(output_paths)}/{len(image_paths)} succeeded")
        return output_paths


def preprocess_census_image(
    image_path: str | Path,
    output_path: Optional[str | Path] = None,
    **options,
) -> np.ndarray:
    """
    Convenience function to preprocess a single census image.

    Args:
        image_path: Path to input image
        output_path: Optional path to save processed image
        **options: Processing options (deskew, denoise, enhance_contrast, binarize)

    Returns:
        Processed image as numpy array

    Example:
        >>> img = preprocess_census_image("census_1900.jpg", "processed.jpg")
        >>> img.shape
        (2000, 1500)
    """
    processor = CensusImageProcessor(**options)
    return processor.process_image(image_path, output_path)
