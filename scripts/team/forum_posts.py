import re, html, sys
def posts(path):
    h = open(path, encoding='utf-8', errors='ignore').read()
    out = []
    chunks = re.split(r"<article\b", h)[1:]
    for ch in chunks:
        a = re.search(r"class=['\"]ipsType_break[^'\"]*['\"][^>]*>\s*(?:<a[^>]*>)?\s*([^<]+?)\s*<", ch)
        a2 = re.search(r"data-memberhovercard[^>]*>([^<]+)</a>", ch)
        date = re.search(r"<time datetime=['\"]([^'\"]+)['\"]", ch)
        c = re.search(r"data-role=['\"]commentContent['\"][^>]*>(.*)", ch, re.S)
        if not c:
            continue
        txt = c.group(1)
        txt = txt.split("data-role='commentControls'")[0].split('ipsItemControls')[0]
        txt = re.sub(r'<blockquote.*?</blockquote>', ' [quote] ', txt, flags=re.S)
        txt = re.sub(r'<(script|style).*?</\1>', ' ', txt, flags=re.S)
        txt = html.unescape(re.sub(r'<[^>]+>', ' ', txt))
        txt = re.sub(r'\s+', ' ', txt).strip()
        au = (a2 or a)
        out.append(dict(author=au.group(1).strip() if au else '?', date=date.group(1)[:10] if date else '', text=txt))
    return out
if __name__ == '__main__':
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    for p in posts(sys.argv[1]):
        print(f"[{p['date']}] {p['author']}: {p['text'][:n]}\n")
