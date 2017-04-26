# -*- coding: utf-8 -*-
"""
Created on Tue Nov 08 15:52:34 2016

@author: Alexander Hamme
"""

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as ec
import job_class
import codecs
import time
import os
import re


class JobSearcher:  
    
    """Documentation goes here. a Job collecting program to blah blah"""
    CHROMEDRIVER_PATH = "C:\Chromedriver\chromedriver.exe"
    INDEED_URL = 'http://www.indeed.com/advanced_search'
    DEFAULT_SEARCH_TERMS = ['python', 'computer programming', 'java', 'software']  # to be searched in the OR box.
    DEFAULT_SEARCH_LOCATION = "new york, ny"
    SEARCH_RADIUS = 50
    DEFAULT_RELEVANCY_KEYWORDS = [
                                'python', 'java', 'music', 'javascript', 'programming', 'computer',
                                'software', 'videogame', 'biotechnology', 'oculus', 'intern', 'undergrad',
                                'bionics', 'software', 'Marvel', 'comics', 'DC', 'bioinspire'
                             ]
    DEFAULT_RELEVANCY_PHRASES = [
                             'computer vision', 'deep learning', 'machine learning',
                             'video game', 'software development', 'cyber security'
                            ]
    DEBUG_MODE = True
    SELECTION_WAIT_TIME = 0.1
    DRIVER_IMPLICIT_WAIT_TIME = 6
    
    def __init__(self):

        self.driver = None
        self.search_terms = []
        self.search_phrases = []
        self.search_location = ''
        self.search_jobtype = ''
        self.relevancy_phrases = []
        self.relevancy_keywords = []

        self.list_of_jobs = []

        self.username = None
        self.password = None

        self.timeSinceBeginning = 0

    def get_information(self, search_terms=None, search_phrases=None, location=None, key_words=None, user=None, pswd=None, jobtype=None):

        """
        TODO: add jobType parameter,

        Also: search for spaces within each entered search term, if there are --> enter as search exact Phrase

        """

        if not search_terms:
            self.search_terms = list(str(raw_input("Enter search terms or phrases separated by commas >>>")).split(','))
            if self.search_terms is None or len(self.search_terms) == 0:  # The only mandatory parameter
                raise SystemExit("No search terms given")
        else:
            self.search_terms = search_terms

        if search_phrases:
            self.search_phrases = []
        else:
            self.search_phrases = search_phrases

        if not location:
            self.search_location = raw_input("Enter location to search within {} miles of >>>".format(SEARCH_RADIUS))
        else:
            self.search_location = location

        if not(jobtype):
            jobtype_indx = raw_input(
                "Select job type from this list:\n{} >>>".format(
                "1. 'Full-time' 2. 'Part-time' 3. 'Contract' 4. 'Internship' 5. 'Temporary'"
                )
            )
        else:
            self.search_jobtype = jobtype

        if not(isinstance(key_words, list)):
            self.relevancy_keywords = list(raw_input("Finally, enter keywords or phrases separated by commas,"
                                                     "\nto be searched for within each job's description >>>").split(','))
        else:
            self.relevancy_keywords = key_words

        self.search_phrases = list(term for term in self.search_terms if len(term) > 1 and ' ' in term[1:])
        # if a space in search term, not at the beginning, add it to search phrases
        self.relevancy_phrases = list(term for term in self.relevancy_keywords if len(term) > 1 and ' ' in term[1:])

        for phrase in self.search_phrases:
            # prevent repetitions
            try:
                self.search_terms.remove(phrase)
            except ValueError:
                pass
        for phrase in self.relevancy_phrases:
            try:
                self.relevancy_keywords.remove(phrase)
            except ValueError:
                pass
            phrase.strip()

        for kwd in self.relevancy_keywords:
            kwd.strip()

        if not(user is None or pswd is None or user == '' or pswd == ''):
            self.username = str(user)
            self.password = str(pswd)

        print "Search Phrases:", self.search_phrases
        print "Relevancy Phrases:", self.relevancy_phrases

    def open_new_session(self, url):
        self.timeSinceBeginning = time.time()
        self.driver = webdriver.Chrome(executable_path=self.CHROMEDRIVER_PATH)
        self.driver.get(url)
        print "Time elapsed in opening session:", time.time() - self.timeSinceBeginning

    def enter_values(self, values=None, element_id=None):
        # @param values must be passed within an iterable
        if element_id is None or element_id == '':
            raise ValueError("No elementID given")

        if values is None or len(values) == 0:
            raise ValueError("No values given")
            
        self.driver.implicitly_wait(self.DRIVER_IMPLICIT_WAIT_TIME)
        
        try:
            # wait until the search box is loaded
            WebDriverWait(self.driver, self.DRIVER_IMPLICIT_WAIT_TIME).until(
               ec.presence_of_element_located((By.ID, element_id))
            )
        except TimeoutException as e:
            print "Could not find '{}' as element id".format(element_id)
            raise e

        entry_box = self.driver.find_element_by_id(str(element_id))
        
        if not isinstance(values, list):
            entry_box.send_keys(str(values))
        elif len(values) == 1:
            entry_box.send_keys(values[0])
        else:
            for val in values:
                entry_box.send_keys(str(val))
                entry_box.send_keys(',')

    def chooseDropDowns(self, *selection_pairs): 
        '''
        :param: selection_pairs - a tuple of ('id', 'value', 'visible text') selection values
        '''        
        self.driver.implicitly_wait(self.DRIVER_IMPLICIT_WAIT_TIME//2)  
        for pair in selection_pairs:
            time.sleep(self.SELECTION_WAIT_TIME)
            select = Select(self.driver.find_element_by_id(pair[0]))
            time.sleep(self.SELECTION_WAIT_TIME)
            try:
                select.select_by_value(pair[1])
            except NoSuchElementException:
                try:
                    select.select_by_visible_text(pair[2])
                except NoSuchElementException as e:
                    raise e


    def search_button(self, element_id=None, element_class_name=None):
        if not(element_id is None and element_class_name is None):
            try:
                search_button = self.driver.find_element_by_id(element_id)
            except WebDriverException:
                try:
                    search_button = self.driver.find_element_by_class_name(element_class_name)
                except WebDriverException as w:
                    raise w
            finally:
                if search_button:
                    search_button.click()
                else:
                    raise ValueError("Could not find search button by identifiers")
        else:
            raise ValueError("No element identifiers given for search_button method")

    def collect_indeed_jobs2(self, html_doc, element_id=None, element_class_name=None):  # 'row' for indeed
        list_of_jobs = []
        if not(element_id is None and element_class_name is None):
            soup = BeautifulSoup(html_doc, 'html.parser')
            if element_class_name is not None:
                jobs = soup.find_all("div", class_=element_class_name)

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
                            except AttributeError:    # 'NoneType' object has no attribute 'text'
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

                    print "Job found, collection time: {}".format(start_time)
                    job = job_class.Job()
                    job.assignvalues(tuple(job_parts))
                    try:
                        self.driver.get(job.link)
                    except WebDriverException:
                        print "Job instance may have invalid url : {}".format(job.link)
                    else:
                        job.collect_job_description(self.driver.page_source)

                    list_of_jobs.append(job)
                    
        return list_of_jobs

    def sort_by_relevancy(self, jobs, keywords, keyphrases=None):
        '''
        Sorts jobs by relevancy count - relevancy count is determined by number of occurrences
        of relevant_keywords in job description
        :param: jobs - list of job object instances
        :param: keywords - list of strings
        :param: keyphrases - list of strings
        '''
        assert isinstance(jobs, list)
        assert isinstance(keywords, list)

        kwd_pattern = re.compile((r"\b" + r"\b|\b".join(keywords) + r"\b"), re.IGNORECASE)
        phrase_pattern = None

        if isinstance(keyphrases, list) and (len(keyphrases) != 0):   #  use more complicated regex patterns for phrases?
            phrase_pattern = re.compile((r"\b" + r"\b|\b".join(keyphrases) + r"\b"))

        for job in jobs:
            assert isinstance(job, job_class.Job)
            job.relevancyScore += len(set(kwd_pattern.findall(job.full_text)))   # don't count repetitions of words
            if phrase_pattern is not None:
                job.relevancyScore += 5 * len(set(phrase_pattern.findall(job.full_text)))
                
        t = time.time()
        
        jobs.sort(key=lambda jb: jb.relevancyScore, reverse=True)
        print "Elapsed sorting time: {}s".format(time.time() - t)

    def write_to_file(self, jobs_list, listLink = True, listAll = False):
        path_numb = 0
        while os.path.exists('jobsList'+str(path_numb)+'.html'):
            path_numb += 1
        with codecs.open('jobsList'+str(path_numb)+'.html', 'w', encoding='utf8') as f:
            f.write(u'''<!DOCTYPE html>
<html>
    <head>
        <title>jobSearcher_JobResults</title>
        <meta charset="UTF-8">
    </head>
    <style>

        body { padding: 1em; }

    </style>
    <body>'''
                    )
            for job in jobs_list:
                assert isinstance(job, job_class.Job)
                f.write(u"""
                        <h3>Title: {0}</h3>
                        <p>Company: {1}</p>
                        <p>Location: {2}</p>
                        <p>Summary: {3}</p>
                        <p>Pay: {4}</p>""".format(*job.basic_info)
                        )
                if len(job.full_text):
                    f.write(job.full_text)
                else:
                    f.write(u"<p><i>Could not retrieve full job description, please visit the job link below.</i></p>")
                f.write(u"<p><a href={}>Job Link</a></p>".format(job.link))
                f.write(u"<br></br><hr><br></br>")
            f.write(u'''
    </body>
</html>'''
                    )
            
    def close_session(self):
        try:
            self.driver.close()
            self.driver.quit()
        except:
            pass
        else:
            print("\nChromedriver closed successfully.\n")
        finally:
            self.driver.quit()
                   
# Potential Usage if multiple job board classes were developed
def main():
    import sys
    try:
        siteURL = sys.argv[1]
    except:
        siteURL = None

    print(__doc__)
    JobSearcher().main(siteURL)
