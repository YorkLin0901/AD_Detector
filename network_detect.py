import requests
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium import webdriver 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from collections import Counter
from multiprocessing import Pool
from functools import partial
from urllib.parse import urlparse
import random
import os
import time
import re
import csv
from fake_useragent import UserAgent
from selenium.webdriver.common.proxy import Proxy, ProxyType
import string
import zipfile

ua = UserAgent()

user_agents = [
    ua.chrome,
    ua.firefox,
    ua.safari,
    ua.edge,
    # ua.opera,
    # ua.ie
]

proxy_list = [
'cbxaaynd:9gck0pt7939y@38.154.227.167:5868',
'cbxaaynd:9gck0pt7939y@185.199.229.156:7492',
'cbxaaynd:9gck0pt7939y@185.199.228.220:7300',
'cbxaaynd:9gck0pt7939y@185.199.231.45:8382',
'cbxaaynd:9gck0pt7939y@188.74.210.207:6286',
'cbxaaynd:9gck0pt7939y@188.74.183.10:8279',
'cbxaaynd:9gck0pt7939y@188.74.210.21:6100',
'cbxaaynd:9gck0pt7939y@45.155.68.129:8133',
'cbxaaynd:9gck0pt7939y@154.95.36.199:6893',
'cbxaaynd:9gck0pt7939y@45.94.47.66:8110',
''
]
def create_proxy_auth_extension(proxy_host, proxy_port, proxy_username, proxy_password, scheme='http',
                                plugin_path=None):
    if plugin_path is None:
        plugin_path = r'{}_{}@http-dyn.dobel.com_9020.zip'.format(proxy_username, proxy_password)

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Dobel Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = string.Template(
        """
        var config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "${scheme}",
                    host: "${host}",
                    port: parseInt(${port})
                },
                bypassList: ["foobar.com"]
            }
          };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "${username}",
                    password: "${password}"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
        );
        """
    ).substitute(
        host=proxy_host,
        port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        scheme=scheme,
    )

    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_path


def from_proxy_get_daili(proxy):
    # proxy是这种格式 user:pass@ip:port
    user_pass_str, ip_port_str = proxy.split('@')
    proxyHost, proxyPort = ip_port_str.split(':')
    proxyUser, proxyPass = user_pass_str.split(':')
    return proxyHost, proxyPort, proxyUser, proxyPass


def init_driver():
    options = webdriver.ChromeOptions()

    proxy = random.choice(proxy_list)
    if '@' in proxy:
        proxyHost, proxyPort, proxyUser, proxyPass = from_proxy_get_daili(proxy)
        proxy_auth_plugin_path = create_proxy_auth_extension(
            proxy_host=proxyHost,
            proxy_port=proxyPort,
            proxy_username=proxyUser,
            proxy_password=proxyPass)
        options.add_extension(proxy_auth_plugin_path)
    else:
        options.add_argument(f'--proxy-server={proxy}')
        
    random_user_agent = random.choice(user_agents)
    options.add_argument(f'user-agent={random_user_agent}')
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_argument("--use_subprocess")
    # options.add_argument('--headless')  
    options.add_argument("--incognito")
    driver = webdriver.Chrome(options=options)
    return driver, proxy

# Open the webpage
def get_pair(domain, result, spec_set):
    # spec_set is used to record those with results more than one page   
    driver, proxy_ip = init_driver()
    if not driver:
        return 'fail', proxy_ip
    driver.get(f"https://projects.propublica.org/nonprofits/full_text_search?sort=best&year%5B%5D=2022&year%5B%5D=2021&year%5B%5D=2020&q={domain}&submit=Apply")
    print(domain, end=' ')
    ran_time = random.randint(0,5)
    time.sleep(ran_time)
    name_set = set()
    try:
        i = 1 
        page = 1
        overlay_closed = False
        while True: 
            i+=1
            num = driver.find_element(By.XPATH, '//*[@id="search-tabs"]/div[3]/span/span[2]').text
            # print(num)
            try: 
                if (not num[1:-1].isnumeric() or int(num[1:-1]) > 25) and not overlay_closed:
                    spec_set.append((domain, 'more than one page'))

                    # close a hidden overlay that present us to click button
                    iframe = driver.find_element(By.CLASS_NAME, 'syndicated-modal')
                    driver.switch_to.frame(iframe)
                    close_btn = driver.find_element(By.XPATH, "//div[@class='collapsible-content content']/button")
                    close_btn.click()
                    driver.switch_to.default_content()

                    # get page limit
                    parent_element = driver.find_element(By.XPATH, '//*[@id="search-bottom"]/nav')
                    span_elements = parent_element.find_elements(By.TAG_NAME, 'span')
                    last_element_idx = len(span_elements)
                    last_element = driver.find_element(By.XPATH,f'//*[@id="search-bottom"]/nav/span[{last_element_idx-2}]/a')
                    page_limit = int(last_element.text)

                    # only do this once
                    overlay_closed = True

                title = driver.find_element(By.XPATH, f'//*[@id="search-results"]/div[1]/div[{i}]/div[1]/div[1]/div/a')
                try:
                    content = driver.find_element(By.XPATH, f'//*[@id="search-results"]/div[1]/div[{i}]/div[2]')
                except:
                    content = ''
            except Exception as e:
                try:
                    page += 1
                    if page <= page_limit:
                        driver.get(f"https://projects.propublica.org/nonprofits/full_text_search?page={page}&q={domain}&sort=best&submit=Apply&year%5B%5D=2020&year%5B%5D=2021&year%5B%5D=2022")
                        i = 1
                        continue
                    else:
                        print(f'no more pages for {domain} where page limit is {page_limit}')
                        break
                except:
                    pass
                print(f'mission complete for {domain}')
                break

            name = title.text.split(' — ')[0].strip()
            if name not in name_set:
                name_set.add(name)
                result.append({'domain':domain, 'org_name':name, 'relevant_content':content.text})
            
        return 'success', proxy_ip
    

    except Exception as e:
        spec_set.append((domain, 'failed visit'))
        print(f'error found: {e}')
        return 'failed', proxy_ip
    

if __name__ == '__main__':
    df = pd.read_csv('donation_info_adj.csv')
    num_pause = 150
    domain_type = 'conspiracy'
    domains = df[(df['category']==domain_type)&(df['donation_adj']=='1')].sort_values(by=['ave_m'], ascending=True)['domain']
    result = []
    spec_set = []
    for i, domain in enumerate(domains):
        while proxy_list:
            status, proxy_ip = get_pair(domain, result, spec_set)
            if status == 'failed':
                proxy_list.remove(proxy_ip)
            else:
                break

        if not i % num_pause:
            time.sleep()

        if not proxy_list:
            print(f'proxy down at website {i}: {domain}')
            break

    pd.DataFrame(result).to_csv(f'{domain_type}_domain_name_pair_unfinished.csv')
    print(f'file saved with {len(result)} records.')
    print('special events: ', spec_set)