import job_description_parser as jdp
from bs4 import BeautifulSoup, NavigableString


class Job:
    # Job class to store information for jobs
    TEXT_TO_EXCLUDE = {
    "discrimination", "veteran", "disability", "disabled", "disabilities", "All rights reserved",
    "click",
    }

    def __init__(self):
        self.title = u"Not found"
        self.company = u"Not found"
        self.location = u"Not found"
        self.summary = u"Not found"
        self.pay = u"Unspecified or not found"
        self.link = u"Not found"
        self.full_text = u""
        self.relevancyScore = 0

    def assign_values(self, tup):
        if isinstance(tup, tuple) and len(tup) == 5:
            self.title, self.company, self.location, self.summary, self.link = tup
        else:
            raise ValueError("Job info tuple must contain 5 values")

    def collect_job_description(self, page_source):
        parser = jdp.JobDescriptionParser(page_source)
        self.full_text = parser.strain_page(parser.page)

    def get_pay(self):
        if len(self.full_text):
            tmp_soup = BeautifulSoup(unicode(self.full_text), "html.parser")
            pay_keywords = {'$', 'pay:', 'a year', '/year', 'an hour', 'wage', 'a month', '/hr', 'compensation'}
            for strng in tmp_soup.stripped_strings:
                if any(kwd in strng for kwd in pay_keywords):
                    self.pay = unicode(strng)

    def basic_info_to_string(self):
        return u"\nJob title: {}\nCompany: {}\nLocation: {}\nSummary: {}\nPay: {}\nLink: {}".format(
               self.title, self.company, self.location, self.summary, self.pay, self.link
        )

    @property
    def basic_info(self):
        return self.title, self.company, self.location, self.summary, self.pay
