import scrapy
from scrapy.selector import Selector
from scrapy.crawler import CrawlerProcess
from pathlib import Path
import re

class PapersSpider(scrapy.Spider):
    name = "papers"
    allowed_domains = ["papers.nips.cc"]
    start_urls = ["https://papers.nips.cc/"]
    DOWNLOAD_FAIL_ON_DATALOSS = False

    def parse(self, response):
        """
        Parses the main homepage of the website and extracts all links.
        If a link contains "paper_files", it follows the link to fetch paper details.
        """
        allLinksOnHomePage = response.css("a::attr(href)").getall()
        p = Path(f"papers/")
        p.mkdir(parents=True, exist_ok=True)
        
        for link in allLinksOnHomePage:
            if link is not None and "paper_files" in link:
                next_page = response.urljoin(link)
                yield scrapy.Request(next_page, callback=self.parseYearPaper)

    def parseYearPaper(self, response):
        """
        Parses the year-specific paper page and extracts paper details.
        Creates a directory for storing papers and follows relevant links.
        """
        paperDiv = response.css("div.col")
        paperName = paperDiv.css("h4::text")[-1]
        allLinksOnSecondPage = response.css("li a::attr(href)").getall()
        
        # Create a directory for storing papers
        p = Path(f"papers/{paperName}/")
        p.mkdir(parents=True, exist_ok=True)

        for link in allLinksOnSecondPage:
            if link is not None and "paper_files" in link:
                next_page = response.urljoin(link)
                yield scrapy.Request(next_page, callback=self.parseYearPaperPage)

    def parseYearPaperPage(self, response):
        """
        Extracts paper details, including name and year, and saves the PDF link.
        """
        paperDiv = response.css("div.col")
        paperName = paperDiv.css("h4")[0].css("h4::text").get()
        p = paperDiv.css("p")
        paperYear = p.css("a::text").get()
        
        # Clean up the extracted year
        paperYear = paperYear.rstrip(paperYear[-1])
        paperYear = paperYear.rstrip(paperYear[-1])
        
        # Sanitize paper name for file naming
        paperName = re.sub(r'[^a-zA-Z0-9]', '', paperName)
        
        # Define file paths
        filename = f"papers/{paperYear}/{paperName}.txt"
        filenamePDF = f"papers/{paperYear}/{paperName}.pdf"
        
        allLinksOnThirdPage = response.css("div.col a::attr(href)").getall()
        
        for link in allLinksOnThirdPage:
            if "pdf" in link:
                Path(filename).write_text("https://papers.nips.cc" + link)
                url = "https://papers.nips.cc" + link
                self.filenamePDF = filenamePDF
                next_page = response.urljoin(url)
                yield scrapy.Request(next_page, callback=self.parseSavePDF)

    def parseSavePDF(self, response):
        """
        Saves the fetched PDF file to the corresponding directory.
        """
        with open(self.filenamePDF, 'wb') as file:
            file.write(response.body)
            
if __name__ =="__main__":
    process = CrawlerProcess()
    process.crawl(PapersSpider)
    process.start()
