"""
Image processing utility module for the AutoZ framework.
Provides functions for image manipulation and recognition.
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List
from src.utils.logging import log_error

def load_image(image_path: str) -> Optional[np.ndarray]:
    """Load an image from file."""
    try:
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            log_error(f"Could not load image: {image_path}")
            return None
        return image.astype(np.uint8)
    except Exception as e:
        log_error(f"Error loading image {image_path}: {e}")
        return None

def match_template(screen: np.ndarray, template: np.ndarray, threshold: float = 0.8) -> Optional[Tuple[int, int, float]]:
    """Match template in screen image."""
    try:
        # Ensure both images are in BGR format
        if screen.shape[-1] == 4:  # If BGRA
            screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
        if template.shape[-1] == 4:  # If BGRA
            template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
        
        # Make sure both images have the same data type
        screen = screen.astype(np.uint8)
        template = template.astype(np.uint8)
        
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            return (max_loc[0], max_loc[1], max_val)
        return None
        
    except Exception as e:
        log_error(f"Error in template matching: {e}")
        return None

def match_template_enhanced(screen: np.ndarray, template: np.ndarray, threshold: float = 0.8) -> Optional[Tuple[int, int, float]]:
    """Enhanced template matching with multiple scales and preprocessing."""
    try:
        # Convert to grayscale
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        scales = [0.8, 0.9, 1.0, 1.1, 1.2]
        best_result = None
        best_confidence = -1
        
        for scale in scales:
            # Resize template
            if scale != 1.0:
                width = int(template.shape[1] * scale)
                height = int(template.shape[0] * scale)
                scaled_template = cv2.resize(template_gray, (width, height))
            else:
                scaled_template = template_gray
            
            # Try different preprocessing
            screen_variants = [
                screen_gray,  # Original
                cv2.equalizeHist(screen_gray),  # Histogram equalization
                cv2.GaussianBlur(screen_gray, (3,3), 0)  # Slight blur
            ]
            template_variants = [
                scaled_template,
                cv2.equalizeHist(scaled_template),
                cv2.GaussianBlur(scaled_template, (3,3), 0)
            ]
            
            # Try each combination
            for s_img in screen_variants:
                for t_img in template_variants:
                    result = cv2.matchTemplate(s_img, t_img, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val > best_confidence and max_val >= threshold:
                        h, w = scaled_template.shape
                        x = max_loc[0] + w//2
                        y = max_loc[1] + h//2
                        best_result = (x, y, max_val)
                        best_confidence = max_val
                    
        return best_result

    except Exception as e:
        log_error(f"Error in enhanced template matching: {e}")
        return None

def find_multiple_templates(screen: np.ndarray, template: np.ndarray, threshold: float = 0.8, max_results: int = 10) -> List[Tuple[int, int, float]]:
    """Find multiple occurrences of a template in the screen."""
    try:
        # Ensure both images are in BGR format
        if screen.shape[-1] == 4:
            screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
        if template.shape[-1] == 4:
            template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
        
        screen = screen.astype(np.uint8)
        template = template.astype(np.uint8)
        
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        matches = []
        for pt in zip(*locations[::-1]):  # Switch columns and rows
            matches.append((pt[0], pt[1], result[pt[1], pt[0]]))
            
        # Sort by confidence and limit results
        matches.sort(key=lambda x: x[2], reverse=True)
        return matches[:max_results]
        
    except Exception as e:
        log_error(f"Error finding multiple templates: {e}")
        return []

def preprocess_image(image: np.ndarray, preprocessing: str = None) -> Optional[np.ndarray]:
    """Apply preprocessing to an image."""
    try:
        if preprocessing is None:
            return image
            
        if preprocessing == "grayscale":
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif preprocessing == "blur":
            return cv2.GaussianBlur(image, (3,3), 0)
        elif preprocessing == "equalize":
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return cv2.equalizeHist(gray)
        else:
            log_error(f"Unknown preprocessing method: {preprocessing}")
            return None
            
    except Exception as e:
        log_error(f"Error preprocessing image: {e}")
        return None

def load_template(template_path: str) -> np.ndarray:
    """
    Load a template image for matching.
    
    Args:
        template_path: Path to the template image
        
    Returns:
        np.ndarray: Loaded template image
    """
    return cv2.imread(template_path)

def find_template(
    screenshot: np.ndarray,
    template: np.ndarray,
    threshold: float = 0.8,
    return_score: bool = False
) -> Optional[Tuple[int, int]] | Tuple[Optional[Tuple[int, int]], float]:
    """
    Find a template image within a screenshot.
    
    Args:
        screenshot: Screenshot to search in
        template: Template to search for
        threshold: Matching threshold (0-1)
        return_score: Whether to return the matching score
        
    Returns:
        Tuple of (x, y) coordinates if found, None if not found
        If return_score is True, also returns the matching score
    """
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= threshold:
        if return_score:
            return max_loc, max_val
        return max_loc
    
    if return_score:
        return None, max_val
    return None

def find_all_templates(
    screenshot: np.ndarray,
    template: np.ndarray,
    threshold: float = 0.8
) -> List[Tuple[int, int]]:
    """
    Find all occurrences of a template in a screenshot.
    
    Args:
        screenshot: Screenshot to search in
        template: Template to search for
        threshold: Matching threshold (0-1)
        
    Returns:
        List of (x, y) coordinates for all matches
    """
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    matches = list(zip(*locations[::-1]))
    
    # Remove overlapping matches
    if matches:
        matches = non_max_suppression(matches, template.shape)
    
    return matches

def non_max_suppression(
    matches: List[Tuple[int, int]],
    template_shape: Tuple[int, int],
    overlap_threshold: float = 0.3
) -> List[Tuple[int, int]]:
    """
    Remove overlapping matches using non-maximum suppression.
    
    Args:
        matches: List of match coordinates
        template_shape: Shape of the template (height, width)
        overlap_threshold: Maximum allowed overlap ratio
        
    Returns:
        List of filtered match coordinates
    """
    if not matches:
        return []
    
    # Convert matches to boxes format [x1, y1, x2, y2]
    boxes = np.array([[x, y, x + template_shape[1], y + template_shape[0]] 
                     for x, y in matches])
    
    # Calculate areas
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    
    # Sort by bottom-right y-coordinate
    indices = np.argsort(boxes[:, 3])
    
    keep = []
    while len(indices) > 0:
        # Keep the last box
        current = indices[-1]
        keep.append(current)
        
        if len(indices) == 1:
            break
            
        # Calculate IoU with remaining boxes
        xx1 = np.maximum(boxes[current, 0], boxes[indices[:-1], 0])
        yy1 = np.maximum(boxes[current, 1], boxes[indices[:-1], 1])
        xx2 = np.minimum(boxes[current, 2], boxes[indices[:-1], 2])
        yy2 = np.minimum(boxes[current, 3], boxes[indices[:-1], 3])
        
        w = np.maximum(0, xx2 - xx1)
        h = np.maximum(0, yy2 - yy1)
        
        overlap = (w * h) / areas[indices[:-1]]
        
        # Remove overlapping boxes
        indices = indices[:-1][overlap < overlap_threshold]
    
    return [(boxes[i, 0], boxes[i, 1]) for i in keep]

def get_center_point(
    coords: Tuple[int, int],
    template_shape: Tuple[int, int]
) -> Tuple[int, int]:
    """
    Get the center point of a template match.
    
    Args:
        coords: Top-left coordinates of the match
        template_shape: Shape of the template (height, width)
        
    Returns:
        (x, y) coordinates of the center point
    """
    x, y = coords
    h, w = template_shape
    return (x + w // 2, y + h // 2) 