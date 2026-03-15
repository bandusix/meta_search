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
    url_path = '-'.join(params)
    
    return f"{base_url}/vodshow/{url_path}.html"
