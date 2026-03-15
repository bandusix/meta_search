# -*- coding: utf-8 -*-
"""
utils/url_builder.py

Utility functions for constructing URLs for the jzftdz.com website.
"""

def build_list_url(base_url, cid, page=1, year=None):
    """
    Constructs a list page URL with proper parameter positioning.
    
    The URL format is: /vodshow/{cid}-{area}-{by}-{class}-{id}-{lang}-{letter}-{level}-{page}-{state}-{tag}-{year}.html
    
    Args:
        base_url (str): The base URL of the website.
        cid (int): Category ID.
        page (int): Page number (default: 1).
        year (int, optional): Year filter (default: None).
    
    Returns:
        str: The constructed URL.
    
    Example:
        >>> build_list_url("https://jzftdz.com", 1, 2, 2025)
        'https://jzftdz.com/vodshow/1--------2---2025.html'
    """
    # Initialize 12 parameter positions (0-indexed in list, but 12 total)
    params = [''] * 12
    params[0] = str(cid)  # Category ID
    
    if page > 1:
        params[8] = str(page)  # Page number (9th position)
    
    if year:
        params[11] = str(year)  # Year (12th position)
    
    # Join with hyphens
    # If no year is provided, the URL will end with e.g. "---.html"
    # The format requires a fixed number of parameters, usually separated by '-'.
    # We ensure 12 slots are filled (some empty string)
    # However, list positions are:
    # 0: id
    # 1: area
    # 2: by
    # 3: class
    # 4: id (duplicate?) or lang
    # ...
    # Wait, the example "1--------2---2025" implies:
    # 1 (id) - (area) - (by) - (class) - (lang) - (letter) - (level) - (order) - 2 (page) - (state) - (tag) - 2025 (year)
    # Total 12 slots: 0..11
    # Slot 8 is page (index 8, 9th element).
    # Slot 11 is year (index 11, 12th element).
    
    # Correct logic based on observed URLs:
    # /vodshow/1--------1---2025.html
    # 1 (0) - (1) - (2) - (3) - (4) - (5) - (6) - (7) - 1 (8) - (9) - (10) - 2025 (11)
    
    # If page is 1, it seems the site accepts '1' in slot 8.
    # So we always set page.
    params[8] = str(page)

    if year:
        params[11] = str(year)

    url_path = '-'.join(params)
    
    return f"{base_url}/vodshow/{url_path}.html"
