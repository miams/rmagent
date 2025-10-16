"""
Image Registration for Census Forms

Uses feature-based alignment to warp target images to match the template.
This enables precise grid application regardless of rotation, skew, or distortion.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ImageRegistration:
    """
    Aligns census images to a reference template using homography transformation.

    This solves the problem of naive linear scaling which fails when images have:
    - Different crops or aspect ratios
    - Rotation or skew
    - Lens distortion
    - Different scanner/camera perspectives
    """

    def __init__(self, template_path: Path):
        """
        Initialize with reference template.

        Args:
            template_path: Path to blank census form template image
        """
        self.template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
        if self.template is None:
            raise ValueError(f"Could not load template: {template_path}")

        self.template_height, self.template_width = self.template.shape
        logger.info(f"Loaded template: {self.template_width}x{self.template_height}px")

        # Pre-compute template keypoints (do once, reuse for all images)
        self.template_keypoints, self.template_descriptors = self._detect_features(
            self.template
        )
        logger.info(
            f"Detected {len(self.template_keypoints)} keypoints in template"
        )

    def _detect_features(
        self, image: np.ndarray
    ) -> Tuple[list, np.ndarray]:
        """
        Detect keypoints and compute descriptors using AKAZE.

        AKAZE is chosen because:
        - Free and open-source (no patent issues like SIFT)
        - Rotation and scale invariant
        - Robust to noise
        - Fast enough for real-time use

        Args:
            image: Grayscale image

        Returns:
            Tuple of (keypoints, descriptors)
        """
        detector = cv2.AKAZE_create()
        keypoints, descriptors = detector.detectAndCompute(image, None)

        if descriptors is None:
            logger.warning("No features detected in image")
            return [], np.array([])

        return keypoints, descriptors

    def _match_features(
        self,
        descriptors1: np.ndarray,
        descriptors2: np.ndarray,
        ratio_threshold: float = 0.75,
    ) -> list:
        """
        Match features between two images using Lowe's ratio test.

        Args:
            descriptors1: Descriptors from first image
            descriptors2: Descriptors from second image
            ratio_threshold: Lowe's ratio test threshold (lower = more strict)

        Returns:
            List of good matches
        """
        if len(descriptors1) == 0 or len(descriptors2) == 0:
            return []

        # Use BFMatcher with Hamming distance (for binary descriptors like AKAZE)
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = matcher.knnMatch(descriptors1, descriptors2, k=2)

        # Apply Lowe's ratio test to filter good matches
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < ratio_threshold * n.distance:
                    good_matches.append(m)

        logger.debug(
            f"Found {len(good_matches)} good matches out of {len(matches)} total"
        )
        return good_matches

    def _compute_homography(
        self,
        keypoints1: list,
        keypoints2: list,
        matches: list,
        min_matches: int = 10,
    ) -> Optional[np.ndarray]:
        """
        Compute homography matrix from matched keypoints.

        Args:
            keypoints1: Keypoints from target image
            keypoints2: Keypoints from template image
            matches: List of good matches
            min_matches: Minimum number of matches required

        Returns:
            Homography matrix (3x3) or None if insufficient matches
        """
        if len(matches) < min_matches:
            logger.warning(
                f"Insufficient matches: {len(matches)} < {min_matches}"
            )
            return None

        # Extract matched keypoint locations
        src_pts = np.float32(
            [keypoints1[m.queryIdx].pt for m in matches]
        ).reshape(-1, 1, 2)
        dst_pts = np.float32(
            [keypoints2[m.trainIdx].pt for m in matches]
        ).reshape(-1, 1, 2)

        # Find homography using RANSAC
        # RANSAC filters outliers and finds best-fit transformation
        homography, mask = cv2.findHomography(
            src_pts, dst_pts, cv2.RANSAC, ransacReprojThreshold=5.0
        )

        if homography is None:
            logger.warning("Failed to compute homography")
            return None

        # Count inliers (matches that fit the homography)
        inliers = np.sum(mask)
        logger.info(
            f"Homography computed: {inliers}/{len(matches)} inliers"
        )

        return homography

    def align(
        self, target_image: np.ndarray, debug: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray], dict]:
        """
        Align target image to template using homography transformation.

        Args:
            target_image: Image to align (grayscale or color)
            debug: If True, return visualization of matches

        Returns:
            Tuple of:
            - Aligned image (same size as template)
            - Homography matrix (or None if alignment failed)
            - Metadata dict with alignment stats
        """
        # Convert to grayscale if needed
        if len(target_image.shape) == 3:
            target_gray = cv2.cvtColor(target_image, cv2.COLOR_BGR2GRAY)
        else:
            target_gray = target_image.copy()

        # Detect features in target image
        target_keypoints, target_descriptors = self._detect_features(
            target_gray
        )

        if len(target_keypoints) == 0:
            logger.error("No keypoints detected in target image")
            return target_gray, None, {"status": "failed", "reason": "no_keypoints"}

        # Match features
        good_matches = self._match_features(
            target_descriptors, self.template_descriptors
        )

        if len(good_matches) < 10:
            logger.warning(
                f"Too few matches: {len(good_matches)}, falling back to simple resize"
            )
            # Fallback: just resize to template dimensions
            aligned = cv2.resize(
                target_gray, (self.template_width, self.template_height)
            )
            return aligned, None, {
                "status": "fallback_resize",
                "matches": len(good_matches),
            }

        # Compute homography
        homography = self._compute_homography(
            target_keypoints, self.template_keypoints, good_matches
        )

        if homography is None:
            logger.warning("Homography computation failed, falling back to resize")
            aligned = cv2.resize(
                target_gray, (self.template_width, self.template_height)
            )
            return aligned, None, {
                "status": "fallback_resize",
                "matches": len(good_matches),
                "reason": "homography_failed",
            }

        # Warp target image to align with template
        aligned = cv2.warpPerspective(
            target_gray,
            homography,
            (self.template_width, self.template_height),
            flags=cv2.INTER_LINEAR,
        )

        logger.info("Image successfully aligned to template")

        metadata = {
            "status": "success",
            "target_keypoints": len(target_keypoints),
            "template_keypoints": len(self.template_keypoints),
            "matches": len(good_matches),
            "homography_computed": True,
        }

        # Create debug visualization if requested
        debug_image = None
        if debug:
            debug_image = cv2.drawMatches(
                target_gray,
                target_keypoints,
                self.template,
                self.template_keypoints,
                good_matches[:50],  # Show top 50 matches
                None,
                flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
            )

        return aligned, homography, metadata


def align_to_template(
    target_image_path: Path,
    template_path: Path,
    output_path: Optional[Path] = None,
) -> Tuple[np.ndarray, dict]:
    """
    Convenience function to align a census image to template.

    Args:
        target_image_path: Path to census image to align
        template_path: Path to template image
        output_path: Optional path to save aligned image

    Returns:
        Tuple of (aligned_image, metadata)
    """
    # Load target image
    target = cv2.imread(str(target_image_path), cv2.IMREAD_GRAYSCALE)
    if target is None:
        raise ValueError(f"Could not load target image: {target_image_path}")

    # Initialize registration
    registration = ImageRegistration(template_path)

    # Align
    aligned, homography, metadata = registration.align(target, debug=False)

    # Save if requested
    if output_path is not None:
        cv2.imwrite(str(output_path), aligned)
        logger.info(f"Saved aligned image: {output_path}")

    return aligned, metadata
