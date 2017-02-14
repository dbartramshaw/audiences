#coding=utf-8

from bs4 import BeautifulSoup
from time import sleep as wait
import re
import requests

# Newsgroups to use for topics
# http://qwone.com/~jason/20Newsgroups/


try:
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser

##################################################
# Copied code
##################################################

class MLStripper(HTMLParser):
    # Code copied from StackOverflow http://stackoverflow.com/a/925630/3664835
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    # Code copied from StackOverflow http://stackoverflow.com/a/925630/3664835
    s = MLStripper()
    s.feed(html)
    return ' '.join(s.get_data().split())

##################################################
# Helpers
##################################################

# Best: http://www.bing.com/search?q=hello+world&first=9
# Recent: http://www.bing.com/search?q=hello+world&filters=ex1%3a%22ez1%22
def generate_url(query, first, recent, country_code):
    """(str, str) -> str
    A url in the required format is generated.
    """
    query = '+'.join(query.split())
    url = 'http://www.bing.com/search?q=' + query + '&first=' + first
    if recent in ['h', 'd', 'w', 'm', 'y']: # A True/False would be enough. This is just to maintain consistancy with google.
        url = url + '&filters=ex1%3a%22ez1%22'
    if country_code is not None:
        url += '&cc=' + country_code
    return url

# Best: http://www.bing.com/news/search?q=hello+world&first=11
# Recent: http://www.bing.com/news/search?q=hello+world&qft=sortbydate%3d%221%22
def generate_news_url(query, first, recent, country_code):
    """(str, str) -> str
    A url in the required format is generated.
    """
    query = '+'.join(query.split())
    url = 'http://www.bing.com/news/search?q=' + query + '&first' + first
    if recent in ['h', 'd', 'w', 'm', 'y']: # A True/False would be enough. This is just to maintain consistancy with google.
        url = url + '&qft=sortbydate%3d%221%22'
    if country_code is not None:
        url += '&cc=' + country_code
    return url

def try_cast_int(s):
    """(str) -> int
    All the digits in a given string are concatenated and converted into a single number.
    """
    try:
        temp = re.findall('\d', str(s))
        temp = ''.join(temp)
        return int(temp)
    except:
        return s

##################################################
# Class
##################################################

class Bing:
    @staticmethod
    def search(query, num=10, start=0, sleep=True, recent=None, country_code=None):
        results = []
        _start = start # Remembers the initial value of start for later use
        _url = None
        related_queries = []
        total_results = None

        while len(results) < num:
            if sleep: # Prevents loading too many pages too soon
                wait(1)
            url = generate_url(query, str(start), recent, country_code)
            if _url is None:
                _url = url # Remembers the first url that is generated
            soup = BeautifulSoup(requests.get(url).text, "html.parser")
            new_results = Bing.scrape_search_result(soup)
            results += new_results
            start += len(new_results)
            if total_results is None:
                raw_total_results = soup.find('span', attrs = {'class' : 'sb_count'})
                total_results = 0
                if raw_total_results is not None:
                    for i in raw_total_results.string:
                        try:
                            temp = int(i)
                            total_results = total_results * 10 + temp
                        except:
                            continue
            if len(new_results) == 0:
                break
            if related_queries == []:
                related_queries = Bing.scrape_related(soup)

        results = results[:num]

        temp = {'results' : results,
                'url' : _url,
                'expected_num' : num,
                'received_num' : start,
                'start' : _start,
                'search_engine' : 'bing',
                'related_queries' : related_queries,
                'total_results' : total_results,
                'country_code': country_code,
        }
        return temp

    @staticmethod
    def scrape_related(soup):
        related_queries = []
        raw_related = soup.find('ul', attrs = {'class' : 'b_vList'})
        raw_related = raw_related.find_all('a')

        for related in raw_related:
            related_queries.append(strip_tags(str(related)))
        return related_queries

    @staticmethod
    def scrape_search_result(soup):
        raw_results = soup.find_all('li', attrs = {'class' : 'b_algo'})
        results = []

        for result in raw_results:
            link = result.find('a').get('href')

            raw_link_text = result.find('a')
            link_text = strip_tags(str(raw_link_text))

            additional_links = dict()

            raw_link_info = result.find('div', attrs = {'class' : 'b_caption'})
            description = raw_link_info.find('div', attrs = {'class' : 'b_snippet'})
            if description is None: # If there aren't any additional links
                link_info = strip_tags(str(raw_link_info.find('p')))
            else: # If there are any additional links
                link_info = strip_tags(str(description))
                for a_link in raw_link_info.find_all('a'):
                    additional_links[strip_tags(str(a_link))] = a_link.get('href')

            temp = { 'link' : link,
                     'link_text' : link_text,
                     'link_info' : link_info,
                     'additional_links' : additional_links,
            }
            results.append(temp)
        return results

    @staticmethod
    def search_news(query, num=10, start=0, sleep=True, recent=None, country_code=None):
        results = []
        _start = start # Remembers the initial value of start for later use
        _url = None
        while len(results) < num:
            if sleep: # Prevents loading too many pages too soon
                wait(1)
            url = generate_news_url(query, str(start), recent, country_code)
            if _url is None:
                _url = url # Remembers the first url that is generated
            soup = BeautifulSoup(requests.get(url).text, "html.parser")
            new_results = Bing.scrape_news_result(soup)
            results += new_results
            start += len(new_results)
        results = results[:num]

        temp = {'results' : results,
                'url' : _url,
                'num' : num,
                'start' : _start,
                'search_engine' : 'bing',
                'country_code': country_code,
        }
        return temp

    @staticmethod
    def scrape_news_result(soup):
        raw_results = soup.find_all('div', attrs = {'class' : 'sn_r'})
        results = []

        for result in raw_results:
            link = result.find('a').get('href')

            raw_link_text = result.find('a')
            link_text = strip_tags(str(raw_link_text))

            additional_links = dict() # For consistancy

            raw_link_info = result.find('span', attrs = {'class' : 'sn_snip'})
            link_info = strip_tags(str(raw_link_info))

            raw_source = result.find('cite', attrs = {'class' : 'sn_src'})
            source = strip_tags(str(raw_source))

            raw_time = result.find('span', attrs = {'class' : 'sn_tm'})
            time = strip_tags(str(raw_time))

            temp = { 'link' : link,
                     'link_text' : link_text,
                     'link_info' : link_info,
                     'additional_links' : additional_links,
                     'source' : source,
                     'time' : time,
            }
            results.append(temp)
        return results




################################################################################################################
# RUN ON CATEGORIES -
################################################################################################################


import random
import time
import pandas as pd

'''
title_name = 'category'
title_name = 'wiki_category'
title_name = 'category_forum'
title_name = 'what_is_category'
title_name = 'partner'
'''

title_name = 'partner'
input_file_location = '/Users/davidbartram-shaw/3D/Sponsor Feature Project/data/'


#Load the lookup file in
cats = pd.read_table('/Users/davidbartram-shaw/3D/Sponsor Feature Project/category_lookup.csv',header = 0, sep=',')
cats.columns


#partners = ['Argos','Sky']
cats = pd.read_table('/Users/davidbartram-shaw/3D/datasets/partners_for_extraction.csv',header = 0, sep='|')
cats['category']='partner'




#######################################################################################################################################
# Run search
#######################################################################################################################################

# Empty list for search urls
columns_url = ['link','search_num','category',title_name,'i','link_info','link_text']
urls_test_full = pd.DataFrame(columns=columns_url)

# Empty list for search urls
columns_search = ['related queries','rank','category',title_name,'i']
related_searches = pd.DataFrame(columns=columns_search)

# Empty list for errors
columns_error = ['category']
errors_saved = pd.DataFrame(columns=columns_error)

urls_test_full


# Run loop to save results
for i in range(0,len(cats)):
    try:
        word = cats[title_name][i]
        wt = random.uniform(10, 12)
        #print word
        #output_test = pd.DataFrame(Google_rerun.search(query='bp', num=5, start=0, country_code="gb"))
        output_test = Bing.search(query=word, num=5, start=0, country_code='gb')
        # save output to frame
        output_df = pd.DataFrame(output_test['results'])
        output_df['search_num'] = output_df.index
        pn = output_df[['link','search_num','link_text','link_text','search_num','link_info','link_text']]
        pn.columns=['link','search_num','category',title_name,'i','link_info','link_text']
        pn.loc[:,2:3]=cats['category'][i]
        pn.loc[:,3:4]=word
        pn.loc[:,4:5]=i
        urls_test_full = urls_test_full.append(pn, ignore_index=True)
        print '%s  This is the %dth iteration and waited %f seconds' % (word,i, wt)


        # save related queries
        if output_test['related_queries'] == []:
            print 'no related queries'
            time.sleep(wt)
        else:
            rq = pd.DataFrame(output_test['related_queries'])
            rq.columns=['related queries']

            rq['rank'] = rq.index
            rqf = rq[['related queries','rank','rank','rank','rank']]
            rqf.columns=['related queries','rank','category',title_name,'i']
            rqf.loc[:,2:3]=cats['category'][i]
            rqf.loc[:,3:4]=word
            rqf.loc[:,4:5]=i
            related_searches = related_searches.append(rqf, ignore_index=True)

            time.sleep(wt)
    except (AttributeError,UnicodeEncodeError,UnicodeDecodeError) as e:  ## Multiple exceptions
        errors_iter = pn[['category']]
        errors_saved = errors_saved.append(errors_iter, ignore_index=True)
        print '!!!FAILED!!! %s  This is the %dth iteration and waited %f seconds' % (word,i, wt)



# wiki fail = 0,1,4,5,15,17,18,20,24,28

urls_test_full
related_searches

output_file_loc = '/Users/davidbartram-shaw/3D/Sponsor Feature Project/data/X1_search_and_textgrab/'
urls_test_full_output_loc = str(output_file_loc)+str(title_name)+'_search_results2'
related_searches_output_loc = str(output_file_loc)+str(title_name)+'_related_searches2'

# Save to file
urls_test_full.to_csv('%s.csv' % urls_test_full_output_loc, encoding='utf-8')
related_searches.to_csv('%s.csv' % related_searches_output_loc, encoding='utf-8')


#test1 = pd.read_table('%s.csv' % urls_test_full_output_loc,header = 0, sep=',')
#test2 = pd.read_table('%s.csv' % related_searches_output_loc,header = 0, sep=',')


#######################################################################################################################################
# Pull Text
#######################################################################################################################################



from bs4 import BeautifulSoup
from time import sleep as wait
import re
import requests
import pandas as pd
import string
import urllib2
import string


try:
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser


# Set up
urlAccesser = urllib2.build_opener()
urlAccesser.addheaders = [('User-Agent', 'Mozilla/5.0')] #v. imp. to not get blocked by cloudflare
urls_test_full['text']=''


#for i in range(0, 1):
for i in range(0, len(urls_test_full)):
    try:
        url = urls_test_full['link'][i]

        print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        print i
        print url
        html = urlAccesser.open(url)
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()
        new_text = text.replace("\n"," ")
        new_text = ' '.join(new_text.split())
        print new_text
        urls_test_full.iloc[i:i+1:,7:8] = new_text
    except:
        print 'error!'
        pass


len(urls_test_full)

urls_test_full.columns = ['link', 'search_num','category', str(title_name) ,'i','link_info','link_text','text']
urls_test_full['text'].fillna(' ', inplace=True)

## Save to file
output_file_loc = '/Users/davidbartram-shaw/3D/Sponsor Feature Project/data/X1_search_and_textgrab/'
urls_test_full_text_output_loc = str(output_file_loc)+str(title_name)+'_search_results_added_text'

urls_test_full.to_csv('%s' % urls_test_full_text_output_loc, header=1, index=False, sep='\t', encoding='utf-8')














###
