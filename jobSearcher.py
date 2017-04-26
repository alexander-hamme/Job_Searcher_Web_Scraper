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

        """Keep the spaces between the search terms, remove them from the relevancy phrases and keywords!"""

        """Can't zip() because lengths of lists probably wont be the same"""
        for phrase in self.search_phrases:
            # prevent repetitions
            try:
                self.search_terms.remove(phrase)
            except Exception as e:
                raise e

        for phrase in self.relevancy_phrases:

            try:
                self.relevancy_keywords.remove(phrase)
            except Exception as e:
                raise e

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
        self.driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH)
        self.driver.get(url)
        print "Time elapsed in opening session:", time.time() - self.timeSinceBeginning
        #self.session_url = self.driver.command_executor._url
        #self.session_id = self.driver.session_id
        #print(self.sessionUrl, self.sessionID)

    def enter_values(self, values=None, element_id=None):  # add class name / xpath options
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
        # check if values is not an iterable?
        else:
            for val in values:
                entry_box.send_keys(str(val))
                entry_box.send_keys(',')
        
    #@param :elementIDs: list of tuples
    def chooseDropDowns(self, *selection_pairs):  # = 'radius'):  # you can just rewrite this definition in a child class for a different website?
        """" @param a tuple of ('id', 'value', 'visible text') triples """
        # **args probably better than * args
        # or just unpack from a tuple paramater using *(tuple)
        # radius id = 'radius'
        # results per page id = 'limit'
        
        self.driver.implicitly_wait(self.DRIVER_IMPLICIT_WAIT_TIME//2)  # <-- necessary / useful?
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
                    # If neither works, stop program


    def search_button(self, element_id=None, element_class_name=None):
        # on indeed home page website: 
        # //*[@id="hp_welcome_message"]/a
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
        # put collect method within each website's class e.g. class IndeedSearcher --> collectJobs()
        list_of_jobs = []
        if not(element_id is None and element_class_name is None):
            soup = BeautifulSoup(html_doc, 'html.parser')
            if element_class_name is not None:
                jobs = soup.find_all("div", class_=element_class_name)

            # unnecessary to even have element_id for search method specific to indeed?
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
                            except AttributeError:
                                # 'NoneType' object has no attribute 'text'
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

                            # title, company, location, summary = tuple(job_parts)

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
            # for job in self.list_of_jobs:
            #     job.print_info()
            #     job.

    def sort_by_relevancy(self, jobs, keywords, keyphrases=None):

        """ Sorts jobs by relevancy count - relevancy count is determined by number of occurrences
        of relevant_keywords in job description

        Is TimSort the best sort for this? Does it copy all the text?
        https://docs.python.org/3.4/library/stdtypes.html#string-methods
        :type jobs: list of Job objects


        is it working right now?


        """

        timeZero = time.time()

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

        jobs.sort(key=lambda jb: jb.relevancyScore, reverse=True)
        # jobs = sorted(jobs, key=lambda jb: jb.relevancyScore, reverse=True)


        print "Elapsed sorting time: {}s".format(time.time() - timeZero)
        # for j in jobs:
        #     print j.relevancyScore

        # return jobs

    def save_search_results(self, mainSearchTerm, kwds, location, ):
        pass


    def write_to_file(self, jobs_list, listLink = True, listAll = False):
        # type: (list, bool, bool) -> None

        """

        TODO: construct a (hash map(?) with all jobs' information to check if job already entered
        """

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

        print 'Elapsed time of {} before writing to file: {}s'.format(self.__class__, time.time() - self.timeSinceBeginning)

    def complete_report(self):
        # print sys.getwindowsversion()
        print '\nTotal elapsed time of this jobSearcher session: {}m {}s'.format(
                (time.time()-self.timeSinceBeginning)//60, (time.time()-self.timeSinceBeginning+0.5) % 60)
        pass

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
            
    @property
    def main(self, url=None):
        
        
        """ get rid of all of this
            
        -main method should only be written within each child class
        
        """
        #sys.argv[1]
        
        jobs = []
        self.open_new_session(url)
        
        print "Estimated time of this job searcher session:     --blurp--"
        
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
        self.enterLocation(self.areas[0], 'where')   
        self.enterKeyWords(self.mainSearchTerms, 'as_any')

        # add jobType parameter
        self.chooseDropDowns(('radius','15'), ('limit','50'), ) #('jt','internship'))

        time.sleep(1)
        self.search_button('fj', 'input_submit')
        time.sleep(1)
        htmlPage = self.driver.page_source

        # jobs = self.collectIndeedJobs()

        jobs = self.collect_indeed_jobs2(htmlPage)


        self.write_to_file(self.sort_by_relevancy(jobs))
        #print '\nExamples of jobs found:\n'
        
        #self.listJobsInfo(jobs[:2],listLink = True)
        
        # self.write_to_file(jobs)#[:10] at a time, different filename for each
        
        print '\nTotal elapsed time of {} session: {}m, {}s'.format(
              self.__class__.__name__, int((time.time()-self.timeSinceBeginning)//60),
              (time.time()-self.timeSinceBeginning+0.5) % 60
        )
        self.closeSession()
        ''' if giveReport: self.fullReport()'''
        # return jobs

        

def main():
    import sys
    try:
        siteURL = sys.argv[1]
    except:
        siteURL = None

    print(__doc__)
    JobSearcher().main(siteURL)


#js = JobSearcher()
#js.main(INDEED_URL)

'''
if __name__ == '__main__':
    main()
'''       
        


''' do one kind of search, e.g. all keywords combined with location, 
then go back and do another, e.g. one search for each company, 
then by job Type*** ... 

also, note you need to enter date each time. probably safest to enter all information
each time. call searchBox.clear() first'''



'''##### recursively do each search? '''


"""    def collectIndeedJobs(self, elementID = None, elementClassName = 'row'):#'result'):

        ''' split bs4's returned text by <p>?'''

        '''
        Use Scrapy because it can travel to next pages while previous information still being parsed.

        Much faster(?)
        '''



        timeZero = time.time()

        try:
            jobParentElements = self.driver.find_elements_by_class_name(elementClassName)
        except:
            try:
                jobParentElements = self.driver.find_elements_by_id(elementID)
            except Exception as e:
                print('\nCollecting Indeed jobs failed- neither WebElement identifier worked\n')
                raise e

        jobsList = {}
        notUseful = ['','Sponsored',  ]
        companiesFound = []  # or by title?

        print '\nCollecting jobs. Elapsed time up to now:',time.time()-self.timeSinceBeginning

        '''
        exclude by job type
        list of (some of the) expected qualifications, link to apply / more info
        '''

        for jb in jobParentElements:

            startTime = time.time()

            link,title,location,summary,pay = 'Not found','Not found','Not found','Not found','Unspecified or not found'

            try:
                link = (jb.find_element_by_class_name('turnstileLink').get_attribute("href")).encode('ascii', 'ignore')
            except:
                pass
            try:
                title = ((jb.find_element_by_class_name('jobtitle')).text).encode('ascii', 'ignore')
            except:
                pass
            try:
                location = (jb.find_element_by_class_name('location').text).encode('ascii', 'ignore')  #must be location, not by ('sjcl') first, because this is not consistent.
            except:
                pass
            try:
                summary = (jb.find_element_by_class_name('summary').text).encode('ascii', 'ignore')  #...('snip').find_element_by_class_name('summary')
            except:
                pass
            try:
                company = (jb.find_element_by_class_name('company').text).encode('ascii', 'ignore')
            except:
                pass

            companiesFound.append(company)

            currentJobText= []

            childNodes = jb.find_elements_by_xpath('./*')

            for child in childNodes:
                if not(child.text in notUseful ): # need to split it first? --> #or 'reviews' in child.text):
                    currentJobText.append(child.text)
                    if '$' in child.text:
                        try:
                            splt = child.text.split('hour')
                        except:
                            i = 0
                            wrds = child.text.split(' ')
                            for wrd in wrds:
                                i += 1
                                if wrd in 'hour':
                                    pay = (child.text.encode('ascii', 'ignore'))[:i]
                                    print pay
                            if pay == 'Unspecified or not found':
                                pay = (child.text.encode('ascii', 'ignore'))[:15]  # Worst Case
                                print "Found pay the wrong way:", pay
                        else:
                            pay = splt[0] + 'hour'


            # \/ \/ just add SOME parts?  (e.g. don't need to add all of them again?)
            try:
                currentJobText = (u' '.join(currentJobText)).encode('utf-8')
            except UnicodeEncodeError:
                txtSum = ""
                for txt in currentJobText:
                    txtSum += txt.encode('utf-8', 'ignore') + " "
                currentJobText = txtSum

            '''jobParts = {"Title":title, "Company":company, "Location":location, "Link":link, "Summary":summary,"FullText":currentJobText, "Pay":pay}'''

            jobParts = (("Title: "+str(title)), ("Company: "+str(company)), ("Location: "+str(location)), ("Pay: "+str(pay)), ("Summary: "+str(summary)),
                        ("Link: "+str(link)), ("FullText: "+str(currentJobText)) )

            # for dict in jobPartsDict: return any(d['Company'] == 'Ekso Bionics' for d in label)

             # \/ or by title? (e.g. by title[:10] or first five words or something)

            if companiesFound.count(company) == 1:
                jobsList[company] = jobParts
            else:
                # print "Multiple job entries for company '", company, "'"
                jobsList[str(company)+str(companiesFound.count(company))] = jobParts  # to maintain unique keys in the dictionary

            print "Found job. Retrieval time:", time.time()-startTime,'s'
            ##### maybe just do another list instead of a dictionary????(you'll have to change sortByRelevancy() )
        print len(jobsList), 'jobs found.\n', "Job collection total elapsed time:", time.time()-timeZero,'s'
        return self.sortByRelevancy(jobsList)

    def sortByRelevancy(self, dictOfJobs):
        timeZero = time.time()
        sortedJobsList = []
        tmp = []
        print '\nSorting jobs by relevancy now...'
        for jobKey in (dictOfJobs.iterkeys()):#iteritems()):
            #print jobKey
            jobTxt = str((dictOfJobs.get(jobKey))[6])
            relevancyCount = 1 # 0
            #print relevancyCount
            for phrase in self.relevantJobPhrases:
                # re.compile
                if phrase in jobTxt:
                    print phrase, 'in', jobTxt[:50]
                    relevancyCount += 10 #Very relevant
                    #isRelevant = True
            for word in self.relevantJobKeyWords:
                if word in jobTxt:
                    relevancyCount += 1
            tmp.append((relevancyCount,jobKey))

        for relevancyTuple in sorted(tmp, reverse = True): # Python automatically sorts by the first value in the tuple
            jobKey = relevancyTuple[1]
            sortedJobsList.append((str(jobKey),dictOfJobs.get(jobKey)))

        print "Elapsed sorting time:", time.time() - timeZero,"s"

        return sortedJobsList


    def listJobsInfo(self, listOfJobs, listLink = False, listAll = False):
        # jobLines = []
        # f.write(jobsLines
        for job in listOfJobs:
            print '\n'
            if listLink:
                for jobPart in job[1][:6]:
                    print jobPart

            elif listAll:
                for jobPart in job[1]:
                    print jobPart
            else:
                for jobPart in job[1][:5]: #everything but the link and fulltext
                    print jobPart
            print '\n'"""

