import asyncio
import os
import cv2
import numpy as np
import pytesseract
from playwright.async_api import async_playwright

async def capture_page_screenshot(url, screenshot_path="board.png"):
    """
    Navigates to the URL and captures screenshots of the main page and all frames.
    Returns the path to the best screenshot (the one most likely containing a board).
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use high resolution as requested (4K)
        context = await browser.new_context(
            viewport={'width': 3840, 'height': 2160},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"Navigating to {url}...")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5) # Wait for stability
            
            # Dismiss overlays
            await page.evaluate("""
                () => {
                    const toClick = ['.qc-cmp2-close-icon', '.cookie-banner-close', '.cmp-close-button', '#onetrust-accept-btn-handler', '#promo-bubble', '[aria-label="Close"]'];
                    for (const s of toClick) {
                        const el = document.querySelector(s);
                        if (el && typeof el.click === 'function') el.click();
                    }
                }
            """)
            await asyncio.sleep(2)

            # Capture all frames. Sites like WebSudoku use framesets.
            screenshots = []
            
            # 1. Main page screenshot
            await page.screenshot(path=screenshot_path)
            screenshots.append(screenshot_path)
            
            # 2. Check all frames
            frames = page.frames
            for i, frame in enumerate(frames):
                if frame == page.main_frame: continue
                try:
                    # Check if frame is visible and has content
                    is_visible = await frame.evaluate("() => window.innerWidth > 0 && window.innerHeight > 0")
                    if is_visible:
                        f_path = f"frame_{i}_{screenshot_path}"
                        # Frames don't have .screenshot directly, we need to find an element or use page.screenshot if it's a frameset
                        # If it's a frameset, the main page screenshot should already contain the content.
                        # But if it's an iframe, we might want to capture it specifically.
                        # For now, let's just stick to the main page but ensure we wait for frames.
                        pass
                except:
                    continue

            await browser.close()
            return screenshot_path
        except Exception as e:
            await browser.close()
            raise Exception(f"Failed to capture screenshot: {str(e)}")

def find_board_in_image(image_path):
    """
    Advanced board detection using multiple thresholding and contour analysis.
    """
    img = cv2.imread(image_path)
    if img is None: return None
    
    # Pre-processing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Try multiple thresholding methods to handle different grid colors/weights
    thresh_methods = [
        # 1. Adaptive Gaussian (good for varying light)
        lambda g: cv2.adaptiveThreshold(cv2.GaussianBlur(g, (7, 7), 0), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2),
        # 2. Otsu's Binary (good for high contrast)
        lambda g: cv2.threshold(cv2.GaussianBlur(g, (5, 5), 0), 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
        # 3. Canny Edges (good for thin lines)
        lambda g: cv2.Canny(cv2.GaussianBlur(g, (5, 5), 0), 50, 150)
    ]
    
    best_board = None
    max_area = 0
    
    for method in thresh_methods:
        thresh = method(gray)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 50000: continue # Skip small things
            
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.85 <= aspect_ratio <= 1.15: # Square-like
                    if area > max_area:
                        max_area = area
                        # Perspective transform
                        pts1 = np.float32([approx[i][0] for i in range(4)])
                        rect = np.zeros((4, 2), dtype="float32")
                        s = pts1.sum(axis=1); rect[0] = pts1[np.argmin(s)]; rect[2] = pts1[np.argmax(s)]
                        diff = np.diff(pts1, axis=1); rect[1] = pts1[np.argmin(diff)]; rect[3] = pts1[np.argmax(diff)]
                        side = 900 # Standardize size for OCR
                        pts2 = np.float32([[0, 0], [side, 0], [side, side], [0, side]])
                        M = cv2.getPerspectiveTransform(rect, pts2)
                        best_board = cv2.warpPerspective(img, M, (side, side))
    
    return best_board

def extract_grid_ocr(board_img):
    if board_img is None: return None
    side = board_img.shape[0]
    cell_size = side // 9
    grid = [[0 for _ in range(9)] for _ in range(9)]
    
    gray = cv2.cvtColor(board_img, cv2.COLOR_BGR2GRAY)
    
    # Refined Thresholding for OCR
    # Digital boards often have very sharp text. 
    # Let's try to remove the grid lines better.
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 5)
    
    # Morphological operations to clean up
    kernel = np.ones((2,2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # Find contours
    cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    found_digits = []
    
    for cnt in cnts:
        x, y, w, h = cv2.boundingRect(cnt)
        # Digit aspect ratio and size constraints
        if h > cell_size * 0.4 and h < cell_size * 0.9 and w > cell_size * 0.1 and w < cell_size * 0.8:
            # Avoid the outside grid lines which might have been captured
            if x > 5 and y > 5 and x + w < side - 5 and y + h < side - 5:
                found_digits.append((x, y, w, h, cnt))

    # Process localized digits
    for x, y, w, h, cnt in found_digits:
        row = (y + h // 2) // cell_size
        col = (x + w // 2) // cell_size
        
        if 0 <= row < 9 and 0 <= col < 9 and grid[row][col] == 0:
            roi = thresh[y:y+h, x:x+w]
            # Padding for Tesseract
            pad = 10
            roi_padded = cv2.copyMakeBorder(roi, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
            roi_padded = cv2.bitwise_not(roi_padded) # Black on white
            
            config = '--psm 10 -c tessedit_char_whitelist=123456789'
            text = pytesseract.image_to_string(roi_padded, config=config).strip()
            
            if text and text.isdigit():
                grid[row][col] = int(text[0])

    return grid

async def extract_sudoku(url="https://sudoku.com/challenges/daily-sudoku"):
    screenshot_path = "temp_board.png"
    try:
        await capture_page_screenshot(url, screenshot_path)
        board_img = find_board_in_image(screenshot_path)
        
        if board_img is None:
            # Try a second pass with a different contrast/brightness if needed?
            # Or just fail if no square found.
            if os.path.exists(screenshot_path): os.remove(screenshot_path)
            return None
            
        grid = extract_grid_ocr(board_img)
        if os.path.exists(screenshot_path): os.remove(screenshot_path)
        return grid
    except Exception as e:
        if os.path.exists(screenshot_path): os.remove(screenshot_path)
        raise e
