import pandas as pd
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import re
from multiprocessing import Pool
from functools import partial
import os

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

donation_keywords = [
    "donate", "donation", 'supporter', 'support us'
]
import re

def clean_string(input_string):
    # Replace newlines with spaces
    no_newlines = input_string.replace("\n", " ")
    
    # Strip leading and trailing whitespace
    stripped = no_newlines.strip()
    
    # Replace multiple consecutive spaces with a single space
    single_spaced = re.sub(r'\s+', ' ', stripped)
    
    return single_spaced

def check_elements(elements):
    for element in elements:
        # Check if the element is visible and clickable
        if element.is_displayed() and element.is_enabled():
            # Check the element's text and attributes for donation-related keywords
            text = clean_string(element.text.lower())
            href = element.get_attribute("href") or ""
            for keyword in donation_keywords:
                if len(text.split(' ')) <= 8:
                    if keyword in text or keyword in href:
                        print(f"Donation option found: {text}; {href}")
                        return True
    return False

def find_donation_option(url):
    print(url)
    driver = webdriver.Chrome(options=options) 
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
    desired_width = 1200
    desired_height = 800
    driver.set_window_size(desired_width, desired_height)
    try:
        driver.get('https://' + url)
        for keyword in donation_keywords:
            links = driver.find_elements(By.PARTIAL_LINK_TEXT, keyword)
            buttons = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
            if check_elements(links + buttons):
                return 1

            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(iframes)):
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                if i >= len(iframes):
                    break

                iframe = iframes[i]
                title = iframe.get_attribute("title") or ""
                if keyword in title.lower():
                    print(f"Donation option found in iframe title: {title}")
                    return 1

                driver.switch_to.frame(iframe)
                clickable_elements = driver.find_elements(By.XPATH, f"//*[contains(@href, '{keyword}') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                if check_elements(clickable_elements):
                    return 1
                driver.switch_to.default_content()

        print("Donation option not found")
        return 0

    except TimeoutException as e:
        print(f"TimeoutException encountered while processing {url}, skipping...")
        return 'failed'
    
    except Exception as e:
        print(f"Encountered an error of type {type(e).__name__} while processing {url}, skipping...")
        return 'failed'
    
    finally:
        driver.quit()

def find_donation_option_wrapper(url):
    return (url, find_donation_option(url))

if __name__ == '__main__':
    start = 0
    end = 5
    df_domain = pd.read_csv('ideo_domain_mbfc081123_with_weights.tsv', sep='\t')
    df_domain = df_domain[start: end]
    print(df_domain)

    with Pool(processes=int(os.cpu_count()/2)) as mp_pool:
        results = mp_pool.imap(find_donation_option, list(df_domain['domain']))
    
        df_domain['donation'] = list(results)
    df_domain.to_csv(f'donation_info_{start}_{end}.csv')
