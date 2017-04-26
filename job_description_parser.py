from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from bs4 import Tag, NavigableString


class JobDescriptionParser:

    DEBUG_MODE = True

    MINIMUM_TEXT_LENGTH = 10

    # set to check membership
    TAGS_TO_INCLUDE = {"p", "span", "body", "table", "th", "tr", "td", "tbody", "b", "i", "em", "small", "br", "strong",
                       "font", "div", "ul", "ol", "dl", "dd", "dt", "li", "b", "em", "h1", "h2", "h3", "h4", "h5", "h6"}
    # set to check membership
    TAGS_TO_EXCLUDE = {"script", "style", "label", "input", "a", "img", "iframe"}  # set to check membership

    # list for iteration
    TEXT_TO_EXCLUDE = ["discrimination", "veteran", "disability", "disabled", "disabilities", "All rights reserved",
                       "click", ]

    MINIMUM_TEXT_LENGTH = 50

    ATTRIBUTES_TO_INCLUDE = ["style", "size", "face", "color"]

    """
    ||||||||||

                TODO:   decide on a font (and other characteristics(?)) to be used throughout,

                        change the font of incoming elements in the tag.attrs section
    ||||||||||
    """

    def __init__(self, text):
        """
        :param text: unicode string
        """
        if not isinstance(text, BeautifulSoup):
            self.page = BeautifulSoup(text, "html.parser", parse_only=SoupStrainer(self.TAGS_TO_INCLUDE))
        else:
            self.page = text

    def strain_page(self, page):

        """
        :param page:
        :return: unicode string

        :type(soup_page) -> BeautifulSoup

        TODO: Finding the PAY is not working!
        """

        assert isinstance(page, BeautifulSoup)

        # some pages don't have a body?

        if page.body is not None:
            # print "body tag found"
            for key in list(page.body.attrs):
                # if key not in self.ATTRIBUTES_TO_INCLUDE:
                del page.body.attrs[key]
            soup_page = BeautifulSoup(str(page.body), "html.parser")
        else:
            if not isinstance(page, BeautifulSoup):
                soup_page = BeautifulSoup(str(page), "html.parser")
            else:
                soup_page = page

        # for key in list(soup_page.body.attrs):

        # for child in list(soup_page.body.descendants):
        for child in list(soup_page.descendants):

            if child.name in ("None", None):
                continue

            elif isinstance(child, NavigableString):
                child.strip()
                if not len(child) > self.MINIMUM_TEXT_LENGTH:
                    child.replace_with('')
                else:
                    if any(txt in child for txt in self.TEXT_TO_EXCLUDE):
                        child.replace_with('')
                continue

            assert isinstance(child, Tag)

            if child.name in self.TAGS_TO_EXCLUDE:
                child.decompose()

            elif child.name not in self.TAGS_TO_INCLUDE:
                if child.get_text(strip=True) > self.MINIMUM_TEXT_LENGTH:
                    # If potentially important text is wrapped with an unknown html tag
                    child.unwrap()
                else:
                    child.decompose()

            elif not len(list(child.stripped_strings)):
                # This comes third because tags like <script> and <input> contain text
                # What's the difference between this and get_text()?
                child.decompose()

            else:
                # remove irrelevant attributes
                for key in list(child.attrs):
                    if key not in self.ATTRIBUTES_TO_INCLUDE:
                        del child[key]

                if len(child.get_text(strip=True)) < self.MINIMUM_TEXT_LENGTH:
                    child.decompose()

        # return "".join(line.strip() for line in str(soup_page.body.unwrap()).split("\n"))
        '''
        body_text = soup_page.body
        assert isinstance(body_text, Tag)
        body_text.unwrap()
        '''
        # strip whitespace and extra lines
        return "".join(line.strip() for line in unicode(soup_page).split("\n"))