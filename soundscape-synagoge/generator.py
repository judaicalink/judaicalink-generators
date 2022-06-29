import requests
import urllib3
import bs4 as beautifulsoup
from selenium import webdriver
import os
import sys

driver = webdriver.Chrome(executable_path="~/chromedriver")


def get_urls():
    """
    Get the URL and return the response
    """
    url = "https://www.soundscape-synagoge.de/search?tab=persondict&key="

    # iterate over a-z and get the urls
    for letter in range(ord('a'), ord('z') + 1):
        letter = chr(letter)
        http = urllib3.PoolManager()

        driver.get(url + letter)
        html = driver.page_source
        soup = beautifulsoup.BeautifulSoup(html, 'html.parser')
        # response = http.request('GET', url + letter, preload_content=False)
        # response = requests.get(url + letter)
        # print(url + letter)
        print(html)
        break

        if response.status == 200:
            soup = beautifulsoup.BeautifulSoup(response.data, 'html.parser')
            print(soup)

            # get url, principal name and UID for each person in personBaseList
            for persons in soup.find_all('div', id_='personBaseList'):
                print(persons)
                # find all a tags in persons and get the href as url
                for persons in persons.find_all('li'):
                    # find a tag and get the href as url
                    for a in persons.find_all('a'):
                        url = a.get('href')
                    # find all span tags in persons
                    for span in persons.find_all('span'):
                        # get the text from the second span as principal name
                        principal_name = span[1].text
                        # get the UID from the last span
                        uid = span[3].text

                # print the url, principal name and UID
                print(url, principal_name, uid)

    driver.quit()


get_urls()
