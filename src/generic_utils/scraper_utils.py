"""Module for common web-scraping helper functions / class
"""
from bs4 import UnicodeDammit
from lxml import html
from lxml.html.clean import Cleaner
import requests
from generic_utils import loggingtools
from .requests_utils import SSLAdapter


log = loggingtools.getLogger()


class ScraperHelper(object):
    """Helper class for web scrapers"""

    @staticmethod
    def decode_html(html_string):
        """Method to take in a string of HTML and return a unicode string
        :param html_string:
        :type html_string: str
        :returns:
        :rtype: unicode
        """
        converted = UnicodeDammit(html_string, is_html=True)
        if not converted.unicode_markup:
            raise UnicodeDecodeError(
                "Failed to detect encoding, tried [%s]",
                ', '.join(converted.tried_encodings))
        return converted.unicode_markup

    @classmethod
    def get_url_response(cls, url, ssl_protocol=None, mount_point='https://'):
        """Method to use a custom SSL adapter since we have had problems with certain OpenSSL versions & HTTPS

        :param url:
        :type url: str
        :param ssl_protocol:
        :type ssl_protocol:
        :param mount_point: attach this adapter to any URLs beginning with mount_point
        :type mount_point: str

        :return: the URL response
        :rtype: requests.Response
        """
        tls_session = requests.Session()
        if ssl_protocol is not None:
            tls_adapter = SSLAdapter(ssl_protocol)
            tls_session.mount(mount_point, tls_adapter)
        return tls_session.get(url)

    @classmethod
    def sanitize_html_text(cls, raw_html, safe_attrs=None):
        """
        Clean script tags, etc.
        :param raw_html:
        :type raw_html: str
        :param safe_attrs:
        :type safe_attrs: set
        :return: cleaned html
        :rtype: str
        """
        if safe_attrs is None:
            safe_attrs = set(html.defs.safe_attrs)
            safe_attrs.add('content')
        cleaner = Cleaner(scripts=True,
                          javascript=True,
                          page_structure=False,
                          meta=False,
                          safe_attrs=safe_attrs)
        cleaned_html = cleaner.clean_html(raw_html)
        return cleaned_html

    @classmethod
    def parse_raw_html(cls, raw_html, source_url=None, make_urls_absolute=True, sanitize=True):
        """

        :param raw_html:
        :type raw_html: str
        :param source_url:
        :type source_url: str
        :param make_urls_absolute: Whether to transform links / src urls in the document to absolute based on source_url
        :type make_urls_absolute: bool
        :param sanitize: whether to clean this content before creating tree structure.
        :type sanitize: bool
        :return: parsed html document, optionally sanitized and relative URLs transformed
        :rtype: lxml.html.HtmlElement
        """
        if sanitize:
            raw_html = cls.sanitize_html_text(raw_html)

        html_document = html.document_fromstring(raw_html)
        if source_url and make_urls_absolute:
            html_document.make_links_absolute(source_url)
        return html_document

    @classmethod
    def get_string_for_xpath(cls, xpath_expression, tree):
        """

        :param xpath_expression: an xpath expression to evaluate against tree.
        :type xpath_expression: str
        :param tree:
        :type tree: lxml.html.HtmlElement
        :returns: The string value of the xpath expression.
        :rtype: str

        """
        result = tree.xpath(xpath_expression)
        if result:
            if not isinstance(result, basestring):
                if isinstance(result, list):
                    log.debug('result of xpath (%s) is a list, joining to form a string', result)
                    result = ' '.join(result)
                else:
                    log.warn("received unexpected type (%s), could not get value for xpath %s",
                             type(result), xpath_expression)
        else:
            log.debug("empty result for xpath expression (%s)", xpath_expression)
        return result
