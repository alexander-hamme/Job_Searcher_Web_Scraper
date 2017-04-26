# -*- coding: utf-8 -*-
"""
Created on Tue Nov 08 15:52:34 2016

@author: Alexander Hamme
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as ec
from selenium import webdriver
from bs4 import BeautifulSoup
import job_class
import codecs
import time
import os
import re


class JobSearcher:  
    '''
    JobSearcher Parent Class, to be extended in child classes for specific website web scrapers.
    '''
    CHROMEDRIVER_PATH = "C:\Chromedriver\chromedriver.exe"          # Change to the location on your system
    INDEED_URL = 'http://www.indeed.com/advanced_search'
    SEARCH_RADIUS = 50
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
        self.timeSinceBeginning = 0

    def get_information(self, search_terms=None, search_phrases=None, location=None, key_words=None, user=None, pswd=None, jobtype=None):
        '''
        Get search criteria from user. Currently reads input from command line or terminal, or wherever the program is run from, 
        however future versions will include a custom Tkinter GUI for easier usage.
        '''
        if not search_terms:
            self.search_terms = list(str(raw_input("Enter search terms or phrases separated by commas >>>")).split(','))
            if self.search_terms is None or len(self.search_terms) == 0:  # The only mandatory parameter
                raise SystemExit("No search terms given")
        else:
            self.search_terms = search_terms

        if not search_phrases:
            self.search_phrases = []
        else:
            self.search_phrases = search_phrases

        if not location:
            self.search_location = raw_input("Enter location to search within {} miles of >>>".format(self.SEARCH_RADIUS))
        else:
            self.search_location = location

        if not jobtype:
            jobtype_indx = raw_input(
                "Select job type from this list:\n{} >>>".format(
                "1. Full-time 2. Part-time 3. Contract 4. Internship 5. Temporary"
                )
            )
        else:
            self.search_jobtype = jobtype

        if not key_words:
            self.relevancy_keywords = list(raw_input("Enter keywords or phrases separated by commas"
                                                     "\nto be searched for within each job's description >>>").split(','))
        else:
            self.relevancy_keywords = key_words
 
        # if a space in search term, not at the beginning, add it to search phrases
        self.search_phrases = list(term.strip() for term in self.search_terms if len(term) > 1 and ' ' in term[1:])
        self.relevancy_phrases = list(term.strip() for term in self.relevancy_keywords if len(term) > 1 and ' ' in term[1:])

        # Try to remove repetitions
        
        for phrase in self.search_phrases:
            try:
                self.search_terms.remove(phrase)
            except ValueError:
                pass
            phrase.strip()
            
        for phrase in self.relevancy_phrases:
            try:
                self.relevancy_keywords.remove(phrase)
            except ValueError:
                pass
            phrase.strip()

        for kwd in self.relevancy_keywords:
            kwd.strip()

        print ("Search Phrases are," self.search_phrases)
        print ("Relevancy Phrases are", self.relevancy_phrases)

    def open_new_session(self, url):
        self.timeSinceBeginning = time.time()
        self.driver = webdriver.Chrome(executable_path=self.CHROMEDRIVER_PATH)
        self.driver.get(url)
        print "Time elapsed in opening session:", time.time() - self.timeSinceBeginning

    def enter_values(self, values=None, element_id=None):
        '''
        :param: values must be passed within an iterable
        '''
        if element_id is None or element_id == '':
            raise ValueError("No elementID given")

        if values is None or len(values) == 0:
            raise ValueError("No values given")
        
        try:
            # wait until the search box is loaded            
            WebDriverWait(self.driver, self.DRIVER_IMPLICIT_WAIT_TIME).until(
               ec.presence_of_element_located((By.ID, element_id))
            )
        except TimeoutException as te:
            raise te("Could not find '{}' as element id".format(element_id))

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
                    self.driver.implicitly_wait(self.DRIVER_IMPLICIT_WAIT_TIME)
                else:
                    raise ValueError("Could not find search button by identifiers")
        else:
            raise ValueError("No element identifiers given for search_button method")

    def sort_by_relevancy(self, jobs, keywords, keyphrases=None):
        '''
        Sorts jobs by relevancy count - relevancy count is determined by number of occurrences
        of relevant keywords and relevant keyphrases in the job description text
        :param: jobs - list of job object instances
        :param: keywords - list of strings
        :param: keyphrases - list of strings
        '''
        assert isinstance(jobs, list)
        assert isinstance(keywords, list)

        kwd_pattern = re.compile((r"\b" + r"\b|\b".join(keywords) + r"\b"), re.IGNORECASE)
        
        if isinstance(keyphrases, list) and (len(keyphrases) != 0):   #  TODO: better regex pattern for phrases
            phrase_pattern = re.compile((r"\b" + r"\b|\b".join(keyphrases) + r"\b"))
        else:
            phrase_pattern = None
            
        for job in jobs:
            assert isinstance(job, job_class.Job)
            job.relevancyScore += len(set(kwd_pattern.findall(job.full_text)))   # Don't count repetitions of words
            if phrase_pattern is not None:      # Increase relevancy score more upon finding an exact phrase
                job.relevancyScore += 5 * len(set(phrase_pattern.findall(job.full_text)))
                
        t = time.time()
        
        jobs.sort(key=lambda jb: jb.relevancyScore, reverse=True)
        
        print "Elapsed sorting time: {}s".format(time.time() - t)

    def write_to_file(self, jobs_list, listLink = True, listAll = False, filename=None):
        '''
        Method to write all Job instances to HTML file.
        TODO: add JavaScript option and navigation buttons
        :param: jobs_list - list of Job object instances
        '''
        if not filename:
            path_numb = 0                                               # Avoid overwriting previous file(s)
            while os.path.exists('jobsList'+str(path_numb)+'.html'):    # Default file name
                path_numb += 1
            filename = 'jobsList'+str(path_numb)+'.html'
            
        with codecs.open(filename, 'w', encoding='utf8') as f:
            f.write(u'''<!DOCTYPE html>
<html lang="en-us">
    <head>
        <title>JobSearcher_Job_Results</title>
        <meta charset="UTF-8" content="width=device-width, initial-scale=1.0">
    </head>
    <style>
        body {
                    padding: 6em;
                    font-family: "Lucida Sans Unicode", "Lucida Grande", sans-serif;
                    background-image: url('groovepaper.png');
                    background-color: gray;
                    background-repeat: repeat;
              }

        div.container {
                    width: 100%;
                    border: 1px solid Lavender;
                    border-width:10px;
                    border-style:ridge;
                    
                    padding: 8px;
                    background-image: none;
                    background-color: white;
              }
    </style>
    <body>'''
                    )
            for job in jobs_list:
                assert isinstance(job, job_class.Job)
                f.write(u"""<div class="container">
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
                f.write(u"</div><br></br><hr><br></br>")
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
            print("Chromedriver closed successfully.")
        finally:
            self.driver.quit()
                   
# Potential usage if multiple job board website child classes were to be developed
def main():
    
    import sys
    
    try:
        siteURL = sys.argv[1]
    except:
        siteURL = None
        
    JobSearcher().main(siteURL)
