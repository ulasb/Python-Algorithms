# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Created and published by Ulaş Bardak.

"""
Sudoku grid extraction module using Computer Vision and OCR.
"""

import asyncio
import os
import cv2
import numpy as np
import pytesseract
from playwright.async_api import async_playwright


async def capture_page_screenshot(url, screenshot_path="board.png"):
    """
    Navigates to the URL and captures a high-resolution screenshot.
    Also returns the bounding box of the detected Sudoku board if found.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use high resolution (4K) to help with fine details
        context = await browser.new_context(
            viewport={"width": 3840, "height": 2160},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        try:
            print(f"Navigating to {url}...")
            # Use 'load' instead of 'networkidle'
            await page.goto(url, wait_until="load", timeout=30000)

            # Wait for common board containers
            selectors = [
                "#sudokutable",
                ".game-wrapper",
                ".game-board",
                "#puzzle_grid",
                ".sudokugrid",
                "table.sudokutable",
                "canvas",
            ]
            
            board_bbox = None
            try:
                # Find the first visible selector
                for selector in selectors:
                    el = await page.wait_for_selector(selector, state="visible", timeout=2000)
                    if el:
                        board_bbox = await el.bounding_box()
                        if board_bbox:
                            print(f"Detected board using selector: {selector}")
                            break
            except Exception:
                pass

            # Dismiss overlays
            await page.evaluate("""
                () => {
                    const toClick = ['.qc-cmp2-close-icon', '.cookie-banner-close', '.cmp-close-button', '#onetrust-accept-btn-handler', '#promo-bubble', '[aria-label="Close"]'];
                    for (const s of toClick) {
                        try {
                            const el = document.querySelector(s);
                            if (el && typeof el.click === 'function') el.click();
                        } catch(e) {}
                    }
                }
            """)
            
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

            await page.screenshot(path=screenshot_path)
            await browser.close()
            return screenshot_path, board_bbox
        except Exception as e:
            await browser.close()
            raise RuntimeError(f"Failed to capture screenshot from {url}: {str(e)}") from e


def find_board_in_image(image_path, board_bbox=None):
    """
    Identifies and crops the Sudoku board.
    Uses bounding box from Playwright if available, otherwise falls back to CV.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None

    # If we have a bounding box from the browser, use it!
    if board_bbox:
        x, y, w, h = int(board_bbox['x']), int(board_bbox['y']), int(board_bbox['width']), int(board_bbox['height'])
        # Safety check for dimensions
        if w > 100 and h > 100:
            # Crop the board from the screenshot
            # Note: Playwright coordinates are in CSS pixels, screenshot is in viewport pixels.
            # At dpr=1 (default), they match 1:1.
            board = img[y:y+h, x:x+w]
            # Standardize size
            side = 1800
            return cv2.resize(board, (side, side), interpolation=cv2.INTER_CUBIC)

    # Fallback to CV-based detection (rest of logic...)
    """
    Identifies and crops the Sudoku board from a screenshot using OpenCV.
    Refined to prefer squares with internal grid structure.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Standardize image size for consistent parameter performance if huge
    h_orig, w_orig = gray.shape
    scale = 1.0
    if h_orig > 2000:
        scale = 2000.0 / h_orig
        gray_small = cv2.resize(gray, (0, 0), fx=scale, fy=scale)
    else:
        gray_small = gray

    # Multiple thresholding methods
    thresh_methods = [
        lambda g: cv2.adaptiveThreshold(
            cv2.GaussianBlur(g, (7, 7), 0), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        ),
        lambda g: cv2.threshold(
            cv2.GaussianBlur(g, (5, 5), 0), 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )[1],
    ]

    best_board_rect = None
    max_score = -1

    for method in thresh_methods:
        thresh = method(gray_small)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < (gray_small.size * 0.05): # Board should be at least 5% of page
                continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.8 <= aspect_ratio <= 1.2:
                    # Check for internal grid structure (score based on internal contours)
                    mask = np.zeros(thresh.shape, dtype="uint8")
                    cv2.drawContours(mask, [cnt], -1, 255, -1)
                    internal = cv2.bitwise_and(thresh, thresh, mask=mask)
                    # Count blobs inside: board should have ~20-81 blobs (numbers)
                    int_cnts, _ = cv2.findContours(internal, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                    score = len(int_cnts)
                    
                    if score > max_score:
                        max_score = score
                        best_board_rect = approx / scale # Scale back to original coordinates

    if best_board_rect is not None:
        pts1 = np.float32([best_board_rect[i][0] for i in range(4)])
        rect = np.zeros((4, 2), dtype="float32")
        s = pts1.sum(axis=1); rect[0] = pts1[np.argmin(s)]; rect[2] = pts1[np.argmax(s)]
        diff = np.diff(pts1, axis=1); rect[1] = pts1[np.argmin(diff)]; rect[3] = pts1[np.argmax(diff)]
        
        side = 1800 # Higher resolution for OCR
        pts2 = np.float32([[0, 0], [side, 0], [side, side], [0, side]])
        matrix = cv2.getPerspectiveTransform(rect, pts2)
        return cv2.warpPerspective(img, matrix, (side, side))

    return None


def extract_grid_ocr(board_img):
    """
    Extracts digits from a standardized board image using OCR.
    Refined to use a better thresholding for the whole board first, then process cells. Apply morphological opening to digits.
    """
    if board_img is None:
        return None

    side = board_img.shape[0]
    cell_size = side // 9
    grid = [[0 for _ in range(9)] for _ in range(9)]

    gray = cv2.cvtColor(board_img, cv2.COLOR_BGR2GRAY)
    
    # Try multiple global thresholds to handle different brightness backgrounds
    # Method 1: Adaptive
    thresh1 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10)
    # Method 2: Global Otsu after blurring
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh2 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    for thresh in [thresh2, thresh1]:
        # Clean up noise
        kernel = np.ones((3, 3), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        cnts, _ = cv2.findContours(processed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        found_count = 0
        for cnt in cnts:
            x, y, w, h = cv2.boundingRect(cnt)
            # Digit size constraints: height 30-80% of cell, width 10-70%
            if (h > cell_size * 0.3 and h < cell_size * 0.85 and 
                w > cell_size * 0.05 and w < cell_size * 0.7):
                
                # Center-ish check
                row = (y + h // 2) // cell_size
                col = (x + w // 2) // cell_size
                
                if 0 <= row < 9 and 0 <= col < 9 and grid[row][col] == 0:
                    # ROI with padding
                    roi = processed[y:y+h, x:x+w]
                    pad = 20
                    roi_padded = cv2.copyMakeBorder(roi, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
                    roi_padded = cv2.bitwise_not(roi_padded) # Black on white for Tesseract
                    
                    config = '--psm 10 --oem 3 -c tessedit_char_whitelist=123456789'
                    text = pytesseract.image_to_string(roi_padded, config=config).strip()
                    
                    if text and text.isdigit():
                        grid[row][col] = int(text[0])
                        found_count += 1
        
        if found_count >= 17: # Minimum clues for a unique Sudoku
            break
            
    return grid


async def extract_sudoku(url="https://sudoku.com/challenges/daily-sudoku"):
    """
    Main entry point for extracting a Sudoku grid from a URL.

    Parameters
    ----------
    url : str, optional
        The URL of the Sudoku page. Default is the Daily Challenge.

    Returns
    -------
    list of list of int or None
        The extracted grid, or None if extraction fails.
    """
    screenshot_path = "temp_board.png"
    try:
        screenshot_path, board_bbox = await capture_page_screenshot(url, screenshot_path)
        board_img = find_board_in_image(screenshot_path, board_bbox)

        if board_img is None:
            return None

        grid = extract_grid_ocr(board_img)
        return grid
    finally:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
