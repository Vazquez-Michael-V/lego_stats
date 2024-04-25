# -*- coding: utf-8 -*-
"""
Created on Sun Apr 14 18:23:00 2024

@author: Michael Vazquez
"""


#Selenium imports for website navigation.
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains

import pandas as pd
import numpy as np

import time
import datetime
import pytz

import json



# Setup Chrome driver stuffs.
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--incognito')

PATH = "C:\Program Files (x86)\chromedriver.exe" # Directory of the Chromedriver
serv = Service(PATH)
driver = webdriver.Chrome(service=serv, options=chrome_options)

# Navigate to Lego Star Wars website.
WEBSITE = "https://www.lego.com/en-us/themes/star-wars"
driver.get(WEBSITE)
driver.maximize_window()
web_title = driver.title
print(WEBSITE)
print(web_title)

time.sleep(2)

### Close the two popups that always appear on first visiting the website. ###
popup_website_continue_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, 'age-gate-grown-up-cta'))
    )
popup_website_continue_button.click()

popup_privacy_dismiss_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/aside/div/div/div[3]/div[1]/button[1]'))
    )
popup_privacy_dismiss_button.click()
###


### Find all the pages. ###
pages_links_a = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="blt4e128e4a78935e4b"]/section/div/div[2]/div/div/nav/div')))\
    .find_elements(By.TAG_NAME, 'a')

num_pages = len(pages_links_a)
# for page_link in pages_links_a:
#     print(page_link.get_attribute('href'))
#     print(page_link.text)

page_links_href = [page_link.get_attribute('href') for page_link in pages_links_a]
###

time.sleep(5)
product_links_dfs_list = []
for page_link in page_links_href:
    driver.get(page_link)
    
    # Find the page number. This will be a column for data validation.
    # On the first page, there is no page number.
    # After the first page, the url has query '?page=2', '?page=3', ... etc.
    if 'page' in page_link:
        page_num = page_link[-1:]
    else:
        page_num = 1
    
    ### Once on the products page, this will obtain a series of the unique product links.
    # product_listing_grid_ul = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.ID, 'product-listing-grid')))
    
    # products_href = product_listing_grid_ul.find_elements(By.TAG_NAME, 'a')
    
    products_href = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, 'product-listing-grid')))\
        .find_elements(By.TAG_NAME, 'a')    
    
    # for num, product in enumerate(products_href, 1):
    #     print(f"{num}. {product.get_attribute('href')}")
    #     print(product.text)
    
    # Somehow each link appears twice. Remove the duplicates.
    df_product_links_temp = pd.Series(
        [product.get_attribute('href') for product in products_href]
        ).drop_duplicates().reset_index(drop=True).to_frame(name='product_link')
    
    df_product_links_temp['page_num'] = page_num
    
    product_links_dfs_list.append(df_product_links_temp)
    ###

time.sleep(5)

df_product_links = pd.concat(product_links_dfs_list).reset_index(drop=True)

# Split on the seperator '-' and obtain the last split string.
# Example: lego-star-wars-123 --> 123
df_product_links['item_num'] = df_product_links['product_link']\
    .apply(lambda x: x.split(sep='-')[-1:][0])

# More complicated but avoids using .apply(). Would probably be faster than .apply() if the DataFrame was large.
# df_product_links['item_num_2'] = \
#     df_product_links['product_link'].str.split(pat='-')\
#     .explode()\
#     .reset_index()\
#     .drop_duplicates(subset=['index'], keep='last')\
#     .loc[:, 'product_link']\
#     .reset_index(drop=True)

# Can check that the .apply() and the more complicated way produce the same results.
# if df_product_links['item_num'].eq(df_product_links['item_num_2']).any():
#     print("'item_num' is equal to 'item_num_2'.")
# else:
#     print("'item_num' is not equal to 'item_num_2'.")
# Just use the .apply() because there's not even 100 rows.

print(f'df_product_links shape: {df_product_links.shape}')
print(f"{df_product_links['product_link'].nunique()} unique links obtained.")
print(f"'page_num' value counts:\n{df_product_links['page_num'].value_counts()}")
print(df_product_links.info())

# TODO: Obtain info on each product. Price, number of pieces, etc.
# Loop over all the links.
for product_link in df_product_links['product_link']:
    driver.get(product_link)
    print(driver.title)
    time.sleep(5)

    # df_product_links_temp['page_title'] = driver.title
    # # Found a url on the products page that is different from the displayed url once the product is selected.
    # # The current url should be more reliable for obtaining the item number.
    # df_product_links_temp['current_url'] = driver.current_url

