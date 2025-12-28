#!/usr/bin/env python3
"""测试URL编码解码"""

from urllib.parse import quote, unquote

author_id = "monge <mongezheng@gmail.com>"

# URL编码
encoded = quote(author_id, safe='')
print(f"原始: {author_id}")
print(f"编码: {encoded}")

# URL解码
decoded = unquote(encoded)
print(f"解码: {decoded}")

# 测试浏览器中的编码
browser_encoded = author_id.replace(' ', '%20').replace('<', '%3C').replace('>', '%3E')
print(f"\n浏览器编码: {browser_encoded}")
print(f"解码后: {unquote(browser_encoded)}")
