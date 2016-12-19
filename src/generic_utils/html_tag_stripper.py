"""Strips HTML tags and retain the content."""
import bs4


def strip_tags(html):
    """
    This is a utility function that takes ``html``, strips off:
    1. All HTML tags
    2. Script tags and their contents
    3. CData and their contents
    4. Newline characters.
    , Converts &nbsp; to a ASCII space character.
    and then return the text.
    :param html: HTML content.
    :type html: str or unicode
    :return: Content without HTML tags.
    """
    soup = bs4.BeautifulSoup(html, "lxml")

    # Remove script tag and its content
    if soup.script:
        soup.script.decompose()

    # Remove CDATA and its content
    # CData is a special subclass of "navigable strings" and it does not have decompose().
    for element in soup.find_all(text=True):
        if isinstance(element, bs4.CData):
            element.replace_with('')

    # According to http://www.crummy.com/software/BeautifulSoup/bs4/doc/#entities
    # BeautifulSoup4 produces proper Unicode for all entities, meaning '&nbsp;' is converted to u'\xa0'.
    return soup.get_text().replace(u"\xa0", " ").replace("\n", "")
