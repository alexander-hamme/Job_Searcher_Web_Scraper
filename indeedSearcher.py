# -*- coding: utf-8 -*-
"""
Created on Sat Dec 17 18:54:19 2016

@author: Alexander Hamme
"""
from bs4 import BeautifulSoup
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import jobSearcher
import job_class
import urllib2
import time
import sys


class IndeedSearcher(jobSearcher.JobSearcher):

    TIMING_SIGFIGS = 5

    ACCESS_URL = u"https://www.indeed.com/advanced_search"

    VISIBLE_ELEMENT_ID_CHECK = "what"

    VISIBLE_ELEMENT_CLASS_CHECK = "input_text"

    RESULTS_COUNT_ID = "searchCount"

    JOBTYPE_SELECT_ID = "jt"

    RESULTS_PER_PAGE = 15

    DEBUG_MODE = False

    def __init__(self):
        jobSearcher.JobSearcher.__init__(self)
        self.results_count = 0

    def collect_jobs(self, html_doc, element_id=None, element_class_name=None):  

        list_of_jobs = []

        job_collection_times = []

        if not(element_id is None and element_class_name is None):
            soup = BeautifulSoup(html_doc, 'html.parser')
            if element_class_name is not None:
                jobs = soup.find_all("div", class_=element_class_name)

            # if first attempt unsuccessful
            if jobs is None and element_id is not None:
                jobs = soup.find_all("div", id=element_id)

            if jobs is not None:
                for job in jobs:
                    start_time = time.time()
                    element = BeautifulSoup(job.encode("utf-8").strip(), "html.parser")
                    job_parts = []
                    if element not in (None, "None"):
                        for className in ("jobtitle", "company", "location", "summary"):
                            try:
                                txt = element.find(class_=className).text
                            except AttributeError:   # 'NoneType' object has no attribute 'text'
                                job_parts.append(u"{} Not found")
                            else:
                                job_parts.append(txt.strip())

                        if job_parts[0] == u"Not found":  # alternative identifier
                            try:
                                job_parts[0] = element.find(class_="turnstileLink").text.strip()
                            except AttributeError:
                                pass

                        link = element.find('a').get('href')
                        if link is None or len(link) == 0:
                            job_parts.append(u"Not found")
                        elif not ("http" in link or "www" in link):
                            link = u"https://www.indeed.com" + link
                            job_parts.append(link)

                    print "Job found, collection time: {}".format(int((time.time()-start_time) * (10**self.TIMING_SIGFIGS))
                                                                  / (10.0**self.TIMING_SIGFIGS))

                    job = job_class.Job()
                    job.assign_values(tuple(job_parts))


                    list_of_jobs.append(job)
        return list_of_jobs

    def get_results_count(self):
        try:
            self.results_count = int(self.driver.find_element_by_id(self.RESULTS_COUNT_ID).text.split(' ')[-1])
        except (WebDriverException, NoSuchElementException) as wn:
            raise wn("Unable to find number of search results")
        except ValueError as v:
            raise v("Unable to convert search count to integer")
        else:
            print "Found results count:{}".format(self.results_count)

    def wait_for_results_loaded(self):
        try:
            # wait until page is loaded using specific class name of text boxes on Indeed page
            WebDriverWait(self.driver, self.DRIVER_IMPLICIT_WAIT_TIME).until(
               ec.presence_of_element_located((By.CLASS_NAME, self.VISIBLE_ELEMENT_CLASS_CHECK))
            )
        except TimeoutException as te:
            raise te("Could not find '{}' as element class name".format(self.VISIBLE_ELEMENT_CLASS_CHECK))

    def collect_descriptions_alt(self, j_list):
        """
        Backup method to collect all job descriptions using Selenium WebDriver. 
        This method is far more time-costly, so it is a backup.
        :param j_list: list of Job class instances
        :return: None
        """
        for job in j_list:
            assert isinstance(job, job_class.Job)
            try:
                self.driver.get(job.link)
            except WebDriverException:
                print "Job instance may have invalid url : {}".format(job.link)
                continue
            else:
                self.driver.implicitly_wait(self.DRIVER_IMPLICIT_WAIT_TIME)
                job.collect_job_description(self.driver.page_source)

            if job.pay == "Unspecified or not found" or not len(job.pay):
                job.get_pay()
                if job.pay != "Unspecified or not found":
                    print "Found pay:", job.pay

    def collect_description_backup(self, jb):
        """
        Backup method to collect job descriptions using Selenium WebDriver, in case link is a redirect.
        The time cost of this method is much greater, but it is very reliable.
        :param jb: Job class instance
        :return: None
        """
        assert isinstance(jb, job_class.Job)
        try:
            self.driver.get(jb.link)
        except WebDriverException:
            print "Job instance may have invalid url : {}".format(jb.link)
        else:
            self.driver.implicitly_wait(self.DRIVER_IMPLICIT_WAIT_TIME)
            jb.collect_job_description(self.driver.page_source)

        if jb.pay == "Unspecified or not found" or not jb.pay:
            jb.get_pay()

    def collect_descriptions(self, j_list):
        """
        Retrieve full page source code for each job application to parse out full job description
        :param j_list: list of Job instances
        :return:
        """

        for job in j_list:
            assert isinstance(job, job_class.Job)
            try:
                page = urllib2.urlopen(job.link)
            except (ValueError, urllib2.URLError, urllib2.HTTPError):
                # Link may be a redirect, instead of being broken, so visit the page using Selenium
                self.collect_description_backup(job)
            else:
                job.collect_job_description(page.read())

            if job.pay == "Unspecified or not found" or not len(job.pay):
                job.get_pay()
                if job.pay != "Unspecified or not found":
                    print "Found pay:", job.pay

    def visit_next_page(self, lnk_txt):
        """
        Method to visit next page of search results by clicking Next button
        :param lnk_txt: string --> element id of next button to pass to self.driver
        :return: None
        """
        try:
            self.driver.implicitly_wait(self.DRIVER_IMPLICIT_WAIT_TIME)
            self.driver.find_element_by_link_text(lnk_txt).click()
        except NoSuchElementException:
            # May have reached end of search results
            pass


    def main(self):

        job_results = []
        self.get_information()
        """

        TODO: make get_information use a dialog window!

        """

        self.open_new_session(str(self.ACCESS_URL))

        '''
        for term in self.mainSearchTerms:   # then another one, and change jt to 'part time'
            self.enterKeyWords(term, 'as_and')
            self.enterKeyWords(self.mainSearchTerms, 'as_any')
            self.enterLocation(self.areas[0], 'where')
            self.chooseDropDowns(('radius','15'), ('limit','50'), ('jt','internship'))
            time.sleep(1)
            self.searchButton('fj', 'input_submit')
            time.sleep(1)
            jobs += self.collectIndeedJobs()
        '''
        #self.enterKeyWords([self.mainSearchTerms], 'as_and')
        self.enter_values(self.search_location, element_id='where')
        self.enter_values(self.search_terms, element_id='as_any')
        if len(self.search_phrases):
            self.enter_values(self.search_phrases, element_id='as_phr')

        """
        TODO: add jobType parameter
        """
        
        self.chooseDropDowns(('radius', '25', 'within 25 miles of'), ('limit', '50', '50'), ('jt', 'all', 'All job types'))

        time.sleep(0.5)  # purely for user viewing

        self.search_button(element_id='fj', element_class_name='input_submit')
        self.wait_for_results_loaded()
        self.get_results_count()
        # Check if there are zero search results
        if self.results_count == 0:
            raise SystemExit("No search results for these specific parameters")

        html_page = self.driver.page_source
        job_results += self.collect_jobs(html_page, element_class_name='row')
        # If there are more results on the next page
        time.sleep(2)
        """ copy the link to go to the next page instead?"""

        if self.RESULTS_PER_PAGE < self.results_count:
            # time.sleep(1)
            for i in range(self.results_count//self.RESULTS_PER_PAGE):  # + 1
                self.visit_next_page("Next »")
                self.wait_for_results_loaded()
                html_page = self.driver.page_source
                job_results += self.collect_jobs(html_page, element_class_name='row')
                time.sleep(1)
        # self.collect_descriptions_alt(job_results)
        self.collect_descriptions(job_results)

        self.sort_by_relevancy(job_results, self.relevancy_keywords, self.relevancy_phrases)
        # previous: job_results = self.sort_by_relevancy(jobs_list, self.relevancy_keywords, self.relevancy_phrases)

        self.write_to_file(job_results)

        print '\nTotal elapsed time of {} session: {}m, {}s'.format(
            self.__class__.__name__, int((time.time()-self.timeSinceBeginning)//60),
            (time.time()-self.timeSinceBeginning+0.5) % 60
        )
        self.close_session()
        ''' if giveReport: self.fullReport()'''
        return job_results


def main():
    searcher = IndeedSearcher()
    return searcher.main()

if __name__ == "__main__":
    main()

