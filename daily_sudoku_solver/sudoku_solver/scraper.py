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

    Parameters
    ----------
    url : str
        The URL of the page containing the Sudoku board.
    screenshot_path : str, optional
        The path where the screenshot will be saved. Default is "board.png".

    Returns
    -------
    str
        The path to the captured screenshot.

    Raises
    ------
    Exception
        If the navigation or screenshot capture fails.
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
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5)  # Wait for stability and animations

            # Dismiss common overlays (cookies, promos)
            await page.evaluate(
                """
                () => {
                    const toClick = [
                        '.qc-cmp2-close-icon', 
                        '.cookie-banner-close', 
                        '.cmp-close-button', 
                        '#onetrust-accept-btn-handler', 
                        '#promo-bubble', 
                        '[aria-label="Close"]'
                    ];
                    for (const s of toClick) {
                        const el = document.querySelector(s);
                        if (el && typeof el.click === 'function') el.click();
                    }
                }
            """
            )
            await asyncio.sleep(2)

            await page.screenshot(path=screenshot_path)
            await browser.close()
            return screenshot_path
        except Exception as e:
            await browser.close()
            raise Exception(f"Failed to capture screenshot: {str(e)}")


def find_board_in_image(image_path):
    """
    Identifies and crops the Sudoku board from a screenshot using OpenCV.

    Parameters
    ----------
    image_path : str
        The path to the image file.

    Returns
    -------
    numpy.ndarray or None
        A warped and standardized image of the Sudoku board, or None if not found.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Try multiple thresholding methods to handle different grid styles
    thresh_methods = [
        lambda g: cv2.adaptiveThreshold(
            cv2.GaussianBlur(g, (7, 7), 0),
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2,
        ),
        lambda g: cv2.threshold(
            cv2.GaussianBlur(g, (5, 5), 0),
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
        )[1],
        lambda g: cv2.Canny(cv2.GaussianBlur(g, (5, 5), 0), 50, 150),
    ]

    best_board = None
    max_area = 0

    for method in thresh_methods:
        thresh = method(gray)
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 50000:
                continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.85 <= aspect_ratio <= 1.15:  # Board should be square-like
                    if area > max_area:
                        max_area = area
                        # Perspective transform to flatten the board
                        pts1 = np.float32([approx[i][0] for i in range(4)])
                        rect = np.zeros((4, 2), dtype="float32")
                        s = pts1.sum(axis=1)
                        rect[0] = pts1[np.argmin(s)]
                        rect[2] = pts1[np.argmax(s)]
                        diff = np.diff(pts1, axis=1)
                        rect[1] = pts1[np.argmin(diff)]
                        rect[3] = pts1[np.argmax(diff)]

                        side = 900  # Standardize size for OCR
                        pts2 = np.float32([[0, 0], [side, 0], [side, side], [0, side]])
                        matrix = cv2.getPerspectiveTransform(rect, pts2)
                        best_board = cv2.warpPerspective(img, matrix, (side, side))

    return best_board


def extract_grid_ocr(board_img):
    """
    Extracts digits from a standardized board image using OCR.

    Parameters
    ----------
    board_img : numpy.ndarray
        A 900x900 image of the Sudoku board.

    Returns
    -------
    list of list of int
        A 9x9 matrix representing the extracted grid.
    """
    if board_img is None:
        return None

    side = board_img.shape[0]
    cell_size = side // 9
    grid = [[0 for _ in range(9)] for _ in range(9)]

    gray = cv2.cvtColor(board_img, cv2.COLOR_BGR2GRAY)

    # Thresholding to isolate digits
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 5
    )

    # Clean up noise
    kernel = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Find contours (potential digits)
    cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    found_digits = []
    for cnt in cnts:
        x, y, w, h = cv2.boundingRect(cnt)
        # Filter by size: a digit should be around 40-90% of a cell's height
        if (
            h > cell_size * 0.4
            and h < cell_size * 0.9
            and w > cell_size * 0.1
            and w < cell_size * 0.8
        ):
            # Avoid the outside grid lines
            if x > 5 and y > 5 and x + w < side - 5 and y + h < side - 5:
                found_digits.append((x, y, w, h, cnt))

    # OCR each localized digit
    for x, y, w, h, cnt in found_digits:
        row = (y + h // 2) // cell_size
        col = (x + w // 2) // cell_size

        if 0 <= row < 9 and 0 <= col < 9 and grid[row][col] == 0:
            roi = thresh[y : y + h, x : x + w]
            # Padding for Tesseract
            pad = 10
            roi_padded = cv2.copyMakeBorder(
                roi, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0
            )
            roi_padded = cv2.bitwise_not(roi_padded)  # Convert to black on white

            config = "--psm 10 -c tessedit_char_whitelist=123456789"
            text = pytesseract.image_to_string(roi_padded, config=config).strip()

            if text and text.isdigit():
                grid[row][col] = int(text[0])

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
        await capture_page_screenshot(url, screenshot_path)
        board_img = find_board_in_image(screenshot_path)

        if board_img is None:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            return None

        grid = extract_grid_ocr(board_img)

        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        return grid
    except Exception as e:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        raise e
