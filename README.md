# Job Searching Web Scraper
<h4> Web scraping program to collect jobs from job boards such as Indeed.com. </h4>
<p>User inputs search terms, search location, and relevancy keywords. Travels through search result pages until ALL jobs for specific search criteria have been collected. Script then collects jobs' full descriptions from each job application page, straining the entire page using BeautifulSoup to only retain text related tags such as p, h1-6, ul, ol, li, formatting tags, etc. 
<br>Program finally sorts jobs by relevancy score, using relevancy keywords, and writes final results to HTML file. </p>


<h6>Technologies used: </h6>
- Urllib2<br>
- BeautifulSoup<br>
- Selenium WebDriver<br>
- ChromeDriver<br><br>

<p><i>Note: The JobSearcher Parent Class can easily be extended to scrape from other job boards such as Monster, Glassdoor, etc.</i><p>
