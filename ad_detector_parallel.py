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
import os
import time
import re
import csv

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

PATIENCE = 5

ad_domains = []
with open('Adblocklist.txt', 'r') as file:
    while True:
        # read the second line of each two line for redundency
        ad_domain = file.readline()
        if not ad_domain:
            break
        ad_domain = file.readline()
        ad_domains.append(ad_domain.strip())

# Create Chromeoptions instance 
options = webdriver.ChromeOptions() 

# set header and headless mode
options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
options.add_argument('--headless')  

# Adding argument to disable the AutomationControlled flag 
options.add_argument("--disable-blink-features=AutomationControlled") 

# Exclude the collection of enable-automation switches 
options.add_experimental_option("excludeSwitches", ["enable-automation"]) 

# Turn-off userAutomationExtension 
options.add_experimental_option("useAutomationExtension", False) 

# store iframe information to dynamc_conntent
def extract_iframes(driver, dynamic_content, verbose=False):
    # try:
    #     # Wait for iframes to be present
    #     WebDriverWait(driver, 2).until(
    #         EC.presence_of_all_elements_located((By.TAG_NAME, 'iframe'))
    #     )
    # except TimeoutException:
    #     if verbose:
    #         print("Timeout waiting for iframes to load")

    # Find all iframes at the current level
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')

    for index, iframe in enumerate(iframes):
        try:
            src = iframe.get_attribute('src')
            dynamic_content.append(src)
        except Exception as e:
            if verbose:
                print(f'Error processing {index}-th iframe: {e}')
                
            # Ensure the driver is switched back to the parent frame in case of an error

# return the dynamic content of a url
def dynamic_content_extractor(url):
    # Setting the driver path and requesting a page 
    driver = webdriver.Chrome(options=options) 
    
    # Changing the property of the navigator value for webdriver to undefined 
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
    
    driver.get('http://'+url)
    time.sleep(5)
    dynamic_content = []
    extract_iframes(driver, dynamic_content=dynamic_content)
    driver.quit()
    return dynamic_content

def ad_url_check(dynamic_url):
    for ad_domain in ad_domains:
        regex_pattern = '.*' + ad_domain.replace('*', '.*').replace('.', r'\.') + '.*'
        if re.match(regex_pattern, dynamic_url):
            return True, ad_domain
    return False, None

# return counter of ad servers
def ad_url_counter(url):
    dynamic_content = dynamic_content_extractor(url)
    counter = Counter()
    for src in dynamic_content:
        is_ad, ad_admin = ad_url_check(src)
        if is_ad:
            counter[ad_admin] += 1
    return counter

# helper function for ad_server_analysis
def ad_server_analysis(counter):
    uniq_ad_servers = len(counter)
    ad_servers = sum([v for k, v in counter.items()])
    return uniq_ad_servers, ad_servers
    
def ad_detect(domain):
    num_tries = 0
    time_record = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    duration = 0
    while num_tries < PATIENCE:
        num_tries += 1
        try:
            print(domain)
            start = time.time()
            nested_counter = ad_url_counter(domain)
            uniq_ad_servers, ad_servers = ad_server_analysis(nested_counter)
            duration = time.time() - start
            break
        except Exception as e:
            print(f'Try {num_tries} for {domain}: error {e} found when browsing')
            uniq_ad_servers, ad_servers = 0, 0

    # if a domain is not loaded, store in list for further notice
    if num_tries == PATIENCE:
        print(f'failed in ad detection for {domain}')
    
    return (domain, uniq_ad_servers, ad_servers, time_record, duration)

def process_batch(domains, batch_number):
    with Pool(processes=10) as mp_pool:
        results = mp_pool.imap(ad_detect, domains)
        results = list(results)

    batch_file = f'ad_batch/ad_info_batch_{batch_number}.csv'
    with open(batch_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Domain', 'Unique Ad Servers', 'Ad Servers', 'Time Record', 'Duration'])
        for result in results:
            writer.writerow(result)
    
    return batch_file

def combine_and_delete_batches(batch_files, final_file):
    with open(final_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Domain', 'Unique Ad Servers', 'Ad Servers', 'Time Record', 'Duration'])

        for batch_file in batch_files:
            with open(batch_file, 'r') as read_file:
                reader = csv.reader(read_file)
                next(reader)  # Skip the header row
                for row in reader:
                    writer.writerow(row)
            os.remove(batch_file)  # Delete the batch file

if __name__ == '__main__':
    domains = list(pd.read_csv('ideo_domain_mbfc081123_with_weights.tsv', sep='\t')['domain'])
    domains = domains[:10]
    batch_size = 2
    batch_files = []
    for i in range(0, len(domains), batch_size):
        batch_number = i // batch_size + 1
        print(f'Processing batch {batch_number}')
        batch_file = process_batch(domains[i:i + batch_size], batch_number)
        batch_files.append(batch_file)

    print('Combining batch files into the final CSV file...')
    combine_and_delete_batches(batch_files, 'ad_info_final.csv')

    print('Analysis complete. The final CSV file is saved.')