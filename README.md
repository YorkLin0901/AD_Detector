# Ad Server Analysis in News Websites

## Description
This project analyzes the number of unique ad servers and total ads in various news websites. It involves data loading, WebDriver initialization for web scraping with Selenium, iframe detection, and histogram analysis for visualizing the distribution of ad servers.

## Requirements
They are listed in the file requirements.txt.

## Usage
1. Load the list of domains to inspect from 'domainsToInspect.csv' and ad block list from 'Adblocklist.txt'.
2. Initialize the WebDriver with ChromeOptions for headless browsing.
3. Detect iframes in each website and extract the URLs of nested iframes.
4. Check if the iframe URLs are in the ad block list and count the number of unique ad servers and total ads.
5. Analyze the data and visualize the distribution of unique ad servers per domain using histograms.

## Authors
Yukai Lin (yorklin.math@outlook.com)

## License
MIT License
