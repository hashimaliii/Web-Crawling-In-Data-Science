import scrapy
from scrapy.selector import Selector
from scrapy.crawler import CrawlerProcess
from pathlib import Path
import re
import requests
import threading

class PapersSpider(scrapy.Spider):
    name = "papers"
    allowed_domains = ["papers.nips.cc"]
    start_urls = ["https://papers.nips.cc/"]
    DOWNLOAD_FAIL_ON_DATALOSS = False

    def parse(self, response):
        allLinksOnHomePage = response.css("a::attr(href)").getall()
        p = Path(f"papers/")
        p.mkdir(parents=True, exist_ok=True)
        for link in allLinksOnHomePage:
            if (link is not None and "paper_files" in link):
                next_page = response.urljoin(link)
                yield scrapy.Request(next_page, callback=self.parseYearPaper)

    def parseYearPaper(self, response):
        paperDiv = response.css("div.col")
        paperName = paperDiv.css("h4::text")[-1]
        allLinksOnSecondPage = response.css("li a::attr(href)").getall()
        p = Path(f"papers/{paperName}/")
        p.mkdir(parents=True, exist_ok=True)

        for link in allLinksOnSecondPage:
            if (link is not None and "paper_files" in link):
                next_page = response.urljoin(link)
                yield scrapy.Request(next_page, callback=self.parseYearPaperPage)

    def parseYearPaperPage(self, response):
        paperDiv = response.css("div.col")
        paperName = (paperDiv.css("h4")[0]).css("h4::text").get()
        p = paperDiv.css("p")
        paperYear = p.css("a::text").get()
        paperYear = paperYear.rstrip(paperYear[-1])
        paperYear = paperYear.rstrip(paperYear[-1])
        paperName = re.sub(r'[^a-zA-Z0-9]', '', paperName)
        allLinksOnThirdPage = response.css("div.col a::attr(href)").getall()
        filename = f"papers/{paperYear}/{paperName}.txt"
        filenamePDF = f"papers/{paperYear}/{paperName}.pdf"
        for link in allLinksOnThirdPage:
            if "pdf" in link:
                Path(filename).write_text("https://papers.nips.cc"+link)
                url = "https://papers.nips.cc"+link
                self.filenamePDF = filenamePDF
                next_page = response.urljoin(url)
                yield scrapy.Request(next_page, callback=self.parseSavePDF)

    def parseSavePDF(self, response):
        with open(self.filenamePDF, 'wb') as file:
            file.write(response.body)
            

# Using Requests
def downloadPDFUsingRequests(url, filenamePDF):
    response = requests.get(url)

    if response.status_code == 200:
        with open(filenamePDF, 'wb') as file:
            file.write(response.content)
        # print('File downloaded successfully')
    else:
        pass
        # print('Failed to download file')

if __name__ =="__main__":
    process = CrawlerProcess()
    process.crawl(PapersSpider)
    process.start()
