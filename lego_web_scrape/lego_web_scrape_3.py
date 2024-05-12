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
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains

import pandas as pd
import numpy as np

import time
import datetime
import pytz

import json

import os


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

# There seem to be 2 XPATHS for this, ...div[4]/... and ...div[5]/...
try:
    print('Trying to close the popup with XPATH ...div[4]...')
    popup_privacy_dismiss_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/aside/div/div/div[3]/div[1]/button[1]'))
        )
except TimeoutException:
    print('Re-trying to close the popup with XPATH ...div[5]...')
    popup_privacy_dismiss_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/aside/div/div/div[3]/div[1]/button[1]'))
        )
finally:
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
    
    time.sleep(2) # Short explicit wait to avoid StaleElementReferenceException.
    products_href = WebDriverWait(driver, 15).until(
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

# Still duplicates after concat.
# df_dup_links = df_product_links['product_link'].value_counts().sort_values(ascending=False).reset_index()
# df_dup_links = df_dup_links.loc[(df_dup_links['count'] > 1), :]
# df_dup_links['product_link'].str[15:]

df_product_links = df_product_links.drop_duplicates(subset=['product_link'])

# If a link is for a product, then the link should contain 'product'. Otherwise the link is for an ad.
df_product_links = df_product_links.loc[
    (df_product_links['product_link'].str.lower().str.contains('product')), :]\
    .reset_index(drop=True)

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
product_dfs_list = []
for product_link in df_product_links['product_link']:
    driver.get(product_link)
    print(driver.title)

    #################################################################################################################
    ######## This try block finds the product info in the product details wrapper on the product page. ##############
    # The ads mixed in with the products won't have any product detail wrapper.
    page_tries = 2
    # Occassionally the browser fails to load the page, and items are missed.
    # Use this while loop to address page failing to load.
    while page_tries != 0:
        try:
            product_details_wrapper = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="main-content"]/div/div[1]/div/div[1]/section[2]/div'))
                )
        except (TimeoutException, StaleElementReferenceException):
            print('This should be an ad, not a product. Will try again to be sure.')
            driver.get(product_link)
            time.sleep(5)
            page_tries=-1
        else:
            break
    ####################################################################################################
    
    ####################################################################################################
    ### This code takes place on a product page. Obtains age, pieces if applicable, and item number. ###
    # Somehow get random StaleElementReferenceException here.
    # Just try again and hope it works lol
    try:
        wrapper_text_list = ','.join((product_details_wrapper.text.lower()).split()).split(sep=',')
    except StaleElementReferenceException:
        print('Handling StaleElementReferenceException.')
        product_details_wrapper = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="main-content"]/div/div[1]/div/div[1]/section[2]/div'))
            )
        wrapper_text_list = ','.join((product_details_wrapper.text.lower()).split()).split(sep=',')
    else:
        # Every product should have age info.
        # Age, piece, and item info is located at index-1, index. --> [index-1: index+1] since endpoint of a slice is not included.
        # Example: ['18+', 'ages', ....] --> age info has indexes 0 and 1, so the slice would be [0:2].
        print('Finding age info.')
        age_index = wrapper_text_list.index('ages')
        age_info = wrapper_text_list[age_index-1: age_index+1]
        
        # There are also plush and keychain products, so not every product will have pieces.
        try:
            pieces_index = wrapper_text_list.index('pieces')
        except ValueError as e:
            print(e)
            print("This product should be plush or keychain.")
            pieces_info = [np.nan, 'pieces']
        else:
            print('Finding pieces info.')
            pieces_info = wrapper_text_list[pieces_index-1: pieces_index+1]
        
        # Every product has an item number.
        print('Finding item number info.')
        item_index = wrapper_text_list.index('item')
        item_info = wrapper_text_list[item_index-1: item_index+1]
        
        # # Found a url on the products page that is different from the displayed url once the product is selected.
        # # The current url should be more reliable for obtaining the item number.
        current_url = driver.current_url
    #################################################################################################################
    
    #################################################################################################################
    ######### This try block obtains the price info from the product overview on the product page. ##################
    ### This code also takes place on the product page, but uses a different section of the webpage. ### 
    print('Finding price info.')
    try:
        product_overview = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="main-content"]/div/div[1]/div/div[2]/div[2]')))
    # No price info should only happen on ads.
    except TimeoutException:
        print('Could not find price info.')
    else:
        product_overview_inner_text = product_overview.get_property('innerText').split(sep='\n')
        # print(product_overview_inner_text)
        
        item_name = product_overview_inner_text[0]
        
        # In the pricing info, 'Price' is directly before the amount.
        price_index = product_overview_inner_text.index('Price')
        price_info = product_overview_inner_text[price_index: price_index+2]
    #################################################################################################################

    # All the info obtained from the current product page, into a DataFrame place.
    df_product_temp = pd.DataFrame(
        data={
            item_info[1]: [item_info[0]],
            'item_name': [item_name],
            age_info[1]: [age_info[0]],
            pieces_info[1]: [pieces_info[0]],
            price_info[0]: [price_info[1]],
            'url': [current_url]
            }
        )
    
    print(df_product_temp.info())
    product_dfs_list.append(df_product_temp)


df_product_details = pd.concat(product_dfs_list).reset_index(drop=True)
# Time the webscrape completed.
df_product_details['scrape_ts'] = pd.Timestamp.now().floor('min')

# Get rid of the 'TM' in the 'itme_name' column.
df_product_details['item_name'] = df_product_details['item_name'].str.replace('\u2122', '')

# Lowercase column name for consistency.
df_product_details = df_product_details.rename(columns={'Price': 'price'})

# Mainly interested in products with pieces.
# If pieces not null then 'set' else 'other'.
df_product_details['item_type'] = 'other'
df_product_details.loc[(~df_product_details['pieces'].isna()), 'item_type'] = 'set'


print('\ndf_product_details info:')
print(df_product_details.info())
print(f'df_product_details shape: {df_product_details.shape}\n')


print('df_product_links info:')
print(df_product_links.info())
print(f'df_product_links shape: {df_product_links.shape}')

# Save web scrapes to csv.
webscrape_output_dir = r'some_dir\\'
webscrape_output_dir_2 = r'some_dir_2\\'
df_product_details.to_csv(rf'{webscrape_output_dir_2}df_product_details.csv', index=False)
df_product_links.to_csv(rf'{webscrape_output_dir_2}df_product_links.csv', index=False)

df_products = pd.merge(df_product_details, df_product_links,
                       how='outer',
                       left_on=['item'],
                       right_on=['item_num'],
                       indicator=True)
print(df_products['_merge'].value_counts(dropna=False))


print('\ndf_products info:')
print(df_products.info())
print(f'df_products shape: {df_products.shape}\n')

df_products.to_csv(
    rf"{webscrape_output_dir}df_products_{datetime.datetime.now().strftime('%Y%m%dT%H%M')}.csv",
    index=False)

# Ran the webscrape code several times to ensure no products were missed due to page not loading properly.
# Concat the csvs from all the runs and drop duplicates by 'item'.

# 'item' comes from webscraping the page, and 'item_num' comes from splitting the 'product_link' column.
print('Concatting results of several webscrapes.\n')
df_products_finalized = pd.concat(
    [pd.read_csv(rf'{webscrape_output_dir}{csv}')
     for csv in os.listdir(webscrape_output_dir[:-2])]
    ).drop_duplicates(subset=['item_num'])\
    .dropna(subset=['item'])\
    .drop(columns=['_merge'])\
    .reset_index(drop=True)

print('df_products_finalized info:')
print(df_products_finalized.info())
print(f"{df_products_finalized['item_num'].nunique()} unique products found.")
if df_products_finalized['item'].equals(df_products_finalized['item_num'].astype('float64')):
    print('Item numbers are as expected.')
else:
    print('Item numbers are not as expected.')
print(f'df_products_finalized shape: {df_products_finalized.shape}')
df_products_finalized.to_csv(rf'{webscrape_output_dir}df_products_finalized.csv', index=False)

### A few checks that everything worked as expected.
# Before dropping duplicates, checked and found that 'item' is only not equal to 'item_num' when 'item' is null.
# df_products_finalized['item_num'].nunique(dropna=False)
# df_products_finalized['item'].nunique(dropna=False)
# df_products_finalized.shape
# df_products_finalized.info()
# df_products_finalized['item'].equals(df_products_finalized['item_num'].astype('float64')) >> True
# df_products_finalized.loc[(df_products_finalized['item'] != df_products_finalized['item_num']), ['item', 'item_num']]
# df_products_finalized['item_type'].value_counts(dropna=False)
# df_products_finalized['scrape_ts'].value_counts(dropna=False)


