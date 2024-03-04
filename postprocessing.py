from xml.dom import minidom
from bs4 import BeautifulSoup, NavigableString
from shutil import copyfile, copytree
import re
import os
import datetime
import subprocess

# mkdir processed
os.makedirs("processed", exist_ok=True)
copyfile("style.css", "processed/style.css")
copyfile("lwarp.css", "processed/lwarp.css")
copyfile("script.js", "processed/script.js")
copytree("main-images", "processed/main-images", dirs_exist_ok=True)

## table of contents and anchor links
def rearrange_heading_anchors(soup):
    heading_tags = ["h4", "h5", "h6"]
    for tag in soup.find_all(heading_tags):
        entry = tag.find()
        assert "class" in entry.attrs and "sectionnumber" in entry["class"]
        entry.string = entry.string.replace("\u2003", "").strip()
        anchor = "sec-" + entry.string
        entry["id"] = anchor
        # add space between sectionnumber and section title
        for index, content in enumerate(tag.contents):
            if isinstance(content, str):
                space = NavigableString(' ')
                tag.insert(index, space)
                break
        # add paragraph links
        if tag.name in ["h4", "h5", "h6"]:
            # wrap the headline tag's contents in a span (for flexbox purposes)
            headline = soup.new_tag("span")
            for child in reversed(tag.contents):
                headline.insert(0, child.extract())
            tag.append(headline)
            link = soup.new_tag('a', href=f"#{anchor}")
            link['class'] = 'anchor-link'
            if tag.name != "h4":
                # h4 should only get PDF link
                link['data-html-link'] = anchor
            link.append("¶")
            tag.append(link)
        # find human-readable link target and re-arrange anchor
        for sibling in tag.next_siblings:
            if sibling.name is None:
                continue
            if sibling.name == 'a' and 'id' in sibling.attrs:
                # potential link target
                if 'pgfmanual-auto' in sibling['id']:
                    continue
                # print(f"Human ID: {tag['id']} -> {sibling['id']}")
                # found a human-readable link target
                a_tag = sibling.extract()
                tag.insert(0, a_tag)
                break
            else:
                break

def make_page_toc(soup):
    container = soup.find(class_="bodyandsidetoc")
    toc_container = soup.new_tag('div')
    # toc_container['class'] = 'page-toc-container'
    toc_container['class'] = 'sidetoccontainer'
    toc_container['id'] = 'local-toc-container'
    toc_nav = soup.new_tag('nav')
    toc_nav['class'] = 'sidetoc'
    toc_container.append(toc_nav)
    toctitle = soup.new_tag('div')
    toctitle['class'] = 'sidetoctitle'
    toctitle_text = soup.new_tag('p')
    toctitle_text.append("On this page")
    toctitle.append(toctitle_text)
    toc_nav.append(toctitle)
    toc = soup.new_tag('div')
    toc['class'] = 'sidetoccontents'
    toc_nav.append(toc)
    heading_tags = ["h5", "h6"]
    for tag in soup.find_all(heading_tags):
        anchor = tag.find(class_="sectionnumber").get('id')
        item = soup.new_tag('p')
        a = soup.new_tag('a', href=f"#{anchor}")
        toc_string = tag.text.strip().replace("¶", "")
        sectionnumber = tag.find(class_="sectionnumber").text.strip()
        toc_string = toc_string.replace(sectionnumber, "")
        a.string = toc_string.strip()
        if tag.name == "h5":
            a['class'] = 'tocsubsection'
        elif tag.name == "h6":
            a['class'] = 'tocsubsubsection'
        item.append(a)
        toc.append(item)
    container.insert(0,toc_container)

def add_class(tag, c):
    if 'class' in tag.attrs:
        tag['class'].append(c)
    else:
        tag['class'] = [c]

def _add_mobile_toc(soup):
    "on part overview pages, add a list of sections for mobile users"
    mobile_toc = soup.new_tag('div')
    mobile_toc['class'] = 'mobile-toc'
    mobile_toc_title = soup.new_tag('strong')
    mobile_toc_title.string = "Sections"
    mobile_toc.append(mobile_toc_title)
    mobile_toc_list = soup.new_tag('ul')
    mobile_toc.append(mobile_toc_list)
    # get toc contents
    toc_container = soup.find(class_="sidetoccontainer")
    toc_items = toc_container.find_all('a', class_="tocsection")
    for item in toc_items:
        li = soup.new_tag('li')
        a = soup.new_tag('a', href=item.get('href'))
        a.string = item.text
        li.append(a)
        mobile_toc_list.append(li)
    # add toc to section class="textbody", after the h2
    textbody = soup.find(class_="textbody")
    h2_index = textbody.contents.index(soup.h2)
    textbody.insert(h2_index+1, mobile_toc)


## shorten sidetoc
def shorten_sidetoc_and_add_part_header(soup, is_home=False):
    container = soup.find(class_="sidetoccontainer")
    container['id'] = "chapter-toc-container"
    sidetoc = soup.find(class_="sidetoccontents")
    if soup.h4 is None:
        my_file_id = soup.h2['id']    
        is_a_section = False
    else:
        my_file_id = soup.h4['id']
        is_a_section = True
    toc = []
    last_part = None
    my_part = None
    for entry in sidetoc.children:
        if entry.name != 'p':
            continue
        # Skip home link
        # if entry.a['href'] == "index.html":
        #     continue
        if "linkhome" in entry.a['class']:
            entry.a.decompose()
            continue
        if len(entry.a['href'].split('#')) < 2:
            print(f"WARNING: {entry.a['href']}")
        filename = entry.a['href'].split('#')[0]
        file_id = entry.a['href'].split('#')[1]
        # get rid of autosec in toc, not needed
        entry.a['href'] = filename # .replace(".html", "") # remove .html if using server to serve .html files without .html
        # get rid of sectionnumber
        new_a = soup.new_tag('a', href=entry.a['href'])
        new_a['class'] = entry.a['class']
        contents = entry.a.contents[2:]
        contents[0] = contents[0][1:] # delete tab
        new_a.extend(contents)
        entry.a.replace_with(new_a)
        # Skip introduction link because it doesn't have a part
        if "index-0" in entry.a['href']:
            entry.a['class'] = ['linkintro']
            entry.a['href'] = "index.html"
            if is_home:
                entry['class'] = ['current']
            continue
        if "tocpart" in entry.a['class']:
            element = {
                "tag": entry,
                "file_id": file_id,
                "children": []
            }
            last_part = element
            toc.append(element)
            if file_id == my_file_id:
                assert 'class' not in entry
                entry['class'] = ["current"]
                soup.title.string = entry.a.get_text()
                my_part = element
        elif "tocsection" in entry.a['class']:
            element = {
                "tag": entry,
                "file_id": file_id,
            }
            if last_part:
                last_part['children'].append(element)
            if file_id == my_file_id:
                assert 'class' not in entry
                entry['class'] = ["current"]
                my_part = last_part
                my_title = entry.a.get_text()
                my_href = entry.a.get('href')
                soup.title.string = my_title
        else:
            print(f"unknown class: {entry.a['class']}")
    for part in toc:
        if part != my_part:
            for section in part['children']:
                section['tag'].decompose()
        else:
            add_class(part['tag'], "current-part")
            for section in part['children']:
                add_class(section['tag'], "current-part")
            if is_a_section:
                h2 = soup.new_tag('h2')
                h2['class'] = ['inserted']
                part_name = part['tag'].a.get_text()
                assert part_name is not None
                h2.append(part_name)
                soup.h1.insert_after(h2)
    if not is_a_section and not is_home:
        # this is a part overview page
        # let's insert an additional local table of contents for mobile users
        _add_mobile_toc(soup)


## write to file
def write_to_file(soup, filename):
    with open(filename, "w") as file:
        html = soup.encode(formatter="html5").decode("utf-8")
        html = html.replace("index-0","/")
        lines = html.splitlines()
        new_lines = []
        for line in lines:
            # count number of spaces at the start of line
            spaces_at_start = len(re.match(r"^\s*", line).group(0))
            line = line.strip()
            # replace multiple spaces by a single space
            line = re.sub(' +', ' ', line)
            # restore indentation
            line = " " * spaces_at_start + line
            new_lines.append(line)
        html = "\n".join(new_lines)
        file.write(html)

def remove_html_from_links(filename, soup):
    for tag in soup.find_all("a"):
        if 'href' in tag.attrs:
            if tag['href'] == "index.html" or tag['href'] == "index":
                tag['href'] = "/"
            tag['href'] = tag['href'].replace('.html', '')
            if filename == "index.html":
                if "#" in tag['href']:
                    tag['href'] = tag['href'].split('#')[0]

def remove_useless_elements(soup):
    # soup.find("h1").decompose()
    soup.find(class_="topnavigation").decompose()
    soup.find(class_="botnavigation").decompose()

def add_header(soup):
    header = soup.new_tag('header')

    hamburger = soup.new_tag('div')
    hamburger['id'] = "hamburger-button"
    hamburger.string = "☰"
    header.append(hamburger)

    h1 = soup.new_tag('strong')
    link = soup.new_tag('a', href="/")
    h1.append(link)
    link.append("Website Title")
    header.append(h1)
    soup.find(class_="bodyandsidetoc").insert(0, header)

def favicon(soup):
    link = soup.new_tag('link', rel="icon", type="image/png", sizes="16x16", href="/favicon-16x16.png")
    soup.head.append(link)
    link = soup.new_tag('link', rel="icon", type="image/png", sizes="32x32", href="/favicon-32x32.png")
    soup.head.append(link)
    link = soup.new_tag('link', rel="apple-touch-icon", type="image/png", sizes="180x180", href="/apple-touch-icon.png")
    soup.head.append(link)
    link = soup.new_tag('link', rel="manifest", href="/site.webmanifest")
    soup.head.append(link)

def add_footer(soup):
    footer = soup.new_tag('footer')
    footer_left = soup.new_tag('div')
    footer_left['class'] = "footer-left"
    # Link 1
    link = soup.new_tag('a', href="#")
    link.string = "Link 1"
    footer_left.append(link)
    footer_left.append(" · ")
    # Link 2
    link = soup.new_tag('a', href="#")
    link.string = "Link 2"
    footer_left.append(link)
    footer.append(footer_left)
    footer_right = soup.new_tag('div')
    footer_right['class'] = "footer-right"
    today = datetime.date.today().isoformat()
    em = soup.new_tag('em')
    em.append("Last updated: " + today)
    footer_right.append(em)
    footer.append(footer_right)
    soup.find(class_="bodyandsidetoc").append(footer)

def _add_dimensions(tag, svgfilename):
    with open(svgfilename, "r") as svgfile:
        svg = minidom.parse(svgfile)
        width_pt = svg.documentElement.getAttribute("width").replace("pt", "")
        height_pt = svg.documentElement.getAttribute("height").replace("pt", "")
    width_px = float(width_pt) * 1.33333
    height_px = float(height_pt) * 1.33333
    tag['width'] = "{:.3f}".format(width_px)
    tag['height'] = "{:.3f}".format(height_px)
    return (width_px, height_px)

def process_images(filename, soup):
    "replace SVGs by PNGs if this saves filesize"
    # Step 1: label all images explicitly tagged that they should remain an SVG
    # (tagging works by adding the option "svg" to the \begin{codeexample})
    for tag in soup.find_all("img"):
        if "svg" in tag['src']: 
            width_px, height_px = _add_dimensions(tag, tag['src'])
            # very large SVGs are pathological and empty, delete them
            if height_px > 10000:
                tag.decompose()
                continue
            tag["loading"] = "lazy"
    for tag in soup.find_all("object"):
        if "svg" in tag['data']: 
            _add_dimensions(tag, tag['data'])

def rewrite_svg_links(soup):
    for tag in soup.find_all("a"):
        if tag.has_attr('href') and "svg" in tag['href']:
            img = tag.img
            if img and "inlineimage" in img['class']:
                object = soup.new_tag('object')
                object['data'] = img['src']
                object['type'] = "image/svg+xml"
                tag.replace_with(object)

def add_version_to_css_js(soup):
    "to avoid caching, add a version number to the URL"
    today = datetime.date.today().isoformat().replace("-", "")
    for tag in soup.find_all("link"):
        if tag.has_attr('href') and tag['href'] == "style.css":
            tag['href'] += "?v=" + today
    for tag in soup.find_all("script"):
        if tag.has_attr('src') and tag['src'] == "pgfmanual.js":
            tag['src'] += "?v=" + today

def semantic_tags(soup):
    for example in soup.find_all(class_="example"):
        example.name = "figure"
    for examplecode in soup.find_all(class_="example-code"):
        p = examplecode.find("p")
        p.name = "code"

def add_meta_tags(filename, soup):
    stem = os.path.splitext(filename)[0]
    # title
    if filename == "index-0.html":
        soup.title.string = "Example HTML Title"
    # descriptions
    if filename == "index-0.html":
        meta = soup.new_tag('meta', content="Meta tag description.")
        meta['name'] = "description"
        soup.head.append(meta)
        og_meta = soup.new_tag('meta', property="og:description", content="Meta tag description")
        soup.head.append(og_meta)
    # canonical
    if filename == "index-0.html":
        link = soup.new_tag('link', rel="canonical", href="https://example.com/")
        soup.head.append(link)
        meta = soup.new_tag('meta', property="og:url", content="https://example.com/")
        soup.head.append(meta)
    else:
        link = soup.new_tag('link', rel="canonical", href="https://example.com/" + stem)
        soup.head.append(link)
        meta = soup.new_tag('meta', property="og:url", content="https://example.com/" + stem)
        soup.head.append(meta)
    # thumbnail
    img_filename = "social-media-banners/" + stem + ".png"
    if filename == "index-0.html":
        img_filename = "social-media-banners/introduction.png"
    if os.path.isfile("banners/"+img_filename):
        meta = soup.new_tag('meta', property="og:image", content="https://example.com/" + img_filename)
        soup.head.append(meta)
        # allow Google Discover
        meta = soup.new_tag('meta', content="max-image-preview:large")
        meta['name'] = "robots"
        soup.head.append(meta)
    # og.type = article
    meta = soup.new_tag('meta', property="og:type", content="article")
    soup.head.append(meta)
    # get og.title from soup.title
    meta = soup.new_tag('meta', property="og:title", content=soup.title.string)
    soup.head.append(meta)
    # twitter format
    meta = soup.new_tag('meta', content="summary")
    meta['name'] = "twitter:card"
    soup.head.append(meta)


for filename in sorted(os.listdir()):
    if filename.endswith(".html"):
        if filename in ["main_html.html", "home.html"] or "spotlight" in filename:
            continue
        else:
            print(f"Processing {filename}")
            with open(filename, "r") as fp:
                soup = BeautifulSoup(fp, 'html5lib')
                add_footer(soup)
                shorten_sidetoc_and_add_part_header(soup, is_home=(filename == "index-0.html"))
                rearrange_heading_anchors(soup)
                make_page_toc(soup)
                # remove_html_from_links(filename, soup) # use if server is configured to serve .html files without .html
                remove_useless_elements(soup)
                rewrite_svg_links(soup)
                add_version_to_css_js(soup)
                process_images(filename, soup)
                add_header(soup)
                favicon(soup)
                semantic_tags(soup)
                add_meta_tags(filename, soup)
                soup.find(class_="bodyandsidetoc")['class'].append("grid-container")
                if filename == "index-0.html":
                    soup.h4.decompose() # don't need header on start page
                    soup.body['class'] = "index-page"
                    write_to_file(soup, "processed/index.html")
                else:
                    write_to_file(soup, "processed/"+filename)

# prettify
# run command with subprocess
print("Prettifying")
subprocess.run(["prettier", "--write", "processed/*.html"])

print("Finished")