# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 22:12:08 2022

@author: c_ver
"""
#IMPORTING LIBRARIES
import pandas as pd
import numpy as np
import time
import re

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from chromedriver_py import binary_path

#FUNCTIONS
def select_language():
    '''returns selected language'''
    
    while True:
        try:
            language = int(input('\nPlease select language (English = 0, Espanol = 1): '))
            print('')
            
        except ValueError:
            continue
        
        if language in {0,1}:
            break
        else:
            continue
        
    return language

def query_google_maps(language_selection):
    '''input: query to be made
        return: url to get'''
    
    query1 = input(f'{language_selection[0]}: ')
    assert query1 != '','ERROR!: query cannot be blank'
    
    query2 = input(f'{language_selection[1]}: ')
    assert query2 != '','ERROR!: query cannot be blank'
    
    print('')
    query = query1+' '+query2
    query = query.replace(' ', '+')
    
    if int(language_selection[9]) == 0:
        url = "https://www.google.com/maps/search/"+query
    
    
    elif int(language_selection[9]) == 1:
        url = "https://www.google.cl/maps/search/"+query 
    
    return query,url
    
    
def load_all_results(driver):
    '''loads the complete list of the query results'''
    
    load_list_element= driver.find_element(By.XPATH,"//div[@class='qjESne veYFef']")    
    while True:
        try:
            time.sleep(2)
            scroll_down = ActionChains(driver).move_to_element(load_list_element).perform()
            
        except: #Last result
            break

def get_data(driver, sleep_time=3):
    '''returns a dictionary with the information of each result'''
    
    time.sleep(sleep_time) 
    dict_data = {}
    
    #name, rating, category
    name = driver.find_element(By.XPATH,"//h1[@class='DUwDvf fontHeadlineLarge']").text
    name = ''.join(re.findall('[\w\s\d]',name))    
    dict_data['name'] = name
    
    try:
        rating = driver.find_element(By.XPATH,"//div[@class='LBgpqf']//div[@role='button']").text
        dict_data['rating'] = rating

    except:
        dict_data['rating'] = np.nan
           
    try:  
        category = driver.find_element(By.XPATH,"//div[@class='fontBodyMedium']// \
                                   button[@jsaction='pane.rating.category']").text
        dict_data['category'] = category
    
    except:
        dict_data['category'] = np.nan
       
    #address, phone, website
    data = driver.find_elements(By.XPATH,"//div[@class='RcCsl fVHpi w4vB1d NOE9ve M0S7ae AG25L']")        
    for i in data:

        attribute = i.find_element(By.XPATH,"./button[1]").get_attribute("data-item-id")
        text = i.find_element(By.XPATH,"./button[1]").text

        if attribute == None:
            attribute = i.find_element(By.XPATH,"./a").get_attribute("data-item-id") #for website
            text = i.find_element(By.XPATH,"./a").get_attribute("href")
        
        attribute = attribute.replace(':',' ').split()[0] #for formatting the phone
        dict_data[attribute] = text
               
    #coordenates
    current_url = driver.current_url
    latitude    = current_url.split('!8m2!3d')[1]
    latitude    = float(latitude.split('!4d')[0])
    longitude   = current_url.split('!4d')[1]
    longitude   = float(longitude.split('!')[0])
    
    dict_data['latitude']  = latitude
    dict_data['longitude'] = longitude
    
    return dict_data

def generate_df(scrape_data):
    df = pd.DataFrame(scrape_data)
    
    df.rename(columns={'authority':'website', 'oloc':'location'}, inplace=True)
    df['name'] = df['name'].apply(lambda row: row.lower().capitalize())
    df['location'] = df['location'].apply(lambda row: ' '.join(str(row).split()[1:]))
    df['rating'] = pd.to_numeric(df['rating'])
    df.replace('',np.nan, inplace=True)
    df = df[['name', 'category', 'rating', 'phone', 'address', 'location', 'latitude', 'longitude', 'website']]
    
    return df


def language_dict(language):
    dictionary = np.array([('What are you looking for?, ex:supermarket', 'Que andas buscando? ej: supermercado'),
                 ('Where? ex: santiago chile', 'En qué lugar? ej: santiago chile'),
                  ('Loading list with the results...', 'Cargando lista con los resultados...'),
                  ('Done! \n', 'Listo! \n'),
                  ('Scraping the data...', 'Extrayendo los datos...'),
                  ('Results found', 'Resultados encontrados'),
                  ('Getting data from the result', 'Extrayendo data del resultado'),
                  ('Saving file...', 'Guardando archivo'),
                  ('Do you want to save all the results? (all = 0, otherwise select the amount: ex: Top 10 results = 10)',
                   'Quieres guardar todos los resultados? (todos = 0, o seleccione la cantidad: ej: Top 10 resultados = 10)'),
                    (0,1)])
    
    return dictionary[:,language]


def main():
    
    #language selection
    language = select_language()
    language_selection = language_dict(language)
    
    #querying google maps
    query, url = query_google_maps(language_selection)
    
    # to supress the error messages/logs
    options = webdriver.ChromeOptions() 
    options.add_argument("start-maximized")   
    options.add_experimental_option('excludeSwitches', ['enable-logging'])  
    driver = webdriver.Chrome(options=options,executable_path=binary_path)
    
    driver.get(url)
    time.sleep(1)
    
    #Loading the list with the results
    print(language_selection[2])
    load_all_results(driver) 
    print(language_selection[3]) 
    
    results_list = driver.find_elements(By.CLASS_NAME, "hfpxzc") 
    len_list = len(results_list)
    
    #Scraping the data for each result
    scrape_data = []
    print(language_selection[4])
    print(f'{language_selection[5]}: {len_list} ')
    
    try:
        filter_results = int(input(f'{language_selection[8]} :'))
        assert filter_results >= 0
        print('')
   
    except Exception as exception:        
        print(f'ERROR, must be a number >= 0 : {exception}')
        raise
          
    if filter_results != 0:
        results_list = results_list[:filter_results]
      
    for index,result in enumerate(results_list,start=1):
        print(f'{language_selection[6]}: {index}')             
        try:
            result.click()
             
            element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH,"//h1[@class='DUwDvf fontHeadlineLarge']")))
                       
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", result)
        
        finally:      
                data = get_data(driver)
                scrape_data.append(data)
    
    #Dataframe and saving the file as csv
    df = generate_df(scrape_data)
    
    query_file_name = query.replace('+', '_')    
    print(f'\n{language_selection[7]}: {query_file_name}.csv')
    df.to_csv(f'{query_file_name}.csv', header=True, index=False, encoding="latin1")

    
if __name__ == '__main__':
    main()
    
     
        