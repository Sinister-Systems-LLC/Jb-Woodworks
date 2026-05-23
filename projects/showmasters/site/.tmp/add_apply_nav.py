import os, re, glob

# Add "Apply" link to .nav-links across all pages (between Blog and Contact)
# Skip blog/* files since they already have it (most do; let's audit)

root_pages = [p for p in glob.glob('*.html') if os.path.basename(p) not in ('blog.html',)]
blog_pages = glob.glob('blog/*.html')

count_root = 0
for f in root_pages:
    with open(f, 'r', encoding='utf-8') as fp:
        s = fp.read()
    orig = s
    # Skip if already present
    if 'href="careers.html">Apply</a>' in s:
        continue
    # Insert Apply after Blog in nav-links (root-context paths)
    pat = re.compile(r'(<li><a href="blog\.html"[^>]*>Blog</a></li>)(\s*)(<li><a href="contact\.html")')
    s2 = pat.sub(r'\1\2<li><a href="careers.html">Apply</a></li>\2\3', s)
    if s2 != s:
        s = s2
    if s != orig:
        with open(f, 'w', encoding='utf-8') as fp:
            fp.write(s)
        count_root += 1
        print(f'root: {f} updated')

# Now blog posts (../-prefixed paths)
count_blog = 0
for f in blog_pages:
    with open(f, 'r', encoding='utf-8') as fp:
        s = fp.read()
    orig = s
    if 'href="../careers.html">Apply</a>' in s:
        # Already has it as a button in some blog posts; check nav-links
        if '<li><a href="../careers.html">Apply</a></li>' in s:
            continue
    # Insert Apply after Blog in nav-links
    pat = re.compile(r'(<li><a href="\.\./blog\.html">Blog</a></li>)(\s*)(<li><a href="\.\./contact\.html")')
    s2 = pat.sub(r'\1\2<li><a href="../careers.html">Apply</a></li>\2\3', s)
    if s2 != s:
        s = s2
    if s != orig:
        with open(f, 'w', encoding='utf-8') as fp:
            fp.write(s)
        count_blog += 1
        print(f'blog: {f} updated')

print(f'Total: root {count_root}, blog {count_blog}')
