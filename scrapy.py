import requests
from bs4 import BeautifulSoup
import os
import re
import pandas as pd 
import argparse


def save_to_file(url, title, content_text, path_out):
    # Create the path_out folder if it doesn't exist
    if not os.path.exists(path_out):
        os.makedirs(path_out)
    
    title = re.sub(r'\W+', '_', title.replace(" ", "_"))
    filename = title + '.txt'
    with open(os.path.join(path_out, filename), 'w', encoding='utf-8') as file:
        file.write(url + '\n')
        file.write(title + '\n')
        file.write(content_text)

def scrape_page(url, path_out):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.find('h1', class_='eckb-article-title').text.strip()
    content = soup.find('div', id='eckb-article-content-body')

    # Remove unnecessary elements
    for script in content(['script', 'style']):
        script.decompose()
            
    # Add 'Title' before each h2 title
    h2_tags = content.find_all('h2')
    for h2 in h2_tags:
        # h2.string = ' '.join(['Title:', title, h2.get_text()])
        h2.string = 'Title: ' + h2.get_text() 

    content_text = content.get_text(separator='\n').strip()
    save_to_file(url, title, content_text, path_out)


base_url = 'https://classfit.com'
help_center_url = 'https://classfit.com/help-centre/?cache=no'

response = requests.get(help_center_url)
soup = BeautifulSoup(response.text, 'html.parser')

article_links = soup.find_all('a', class_='epkb-mp-article')
article_links = [e['href'] for e in article_links]



# Main scraping function
def main(links, repeat, processed_links, path_out):
    if repeat : 
        processed_links = []
    if not os.path.exists('scraped_data'):
        os.mkdir('scraped_data')
    for link in links:
        if link not in processed_links : 
            print('-----Scraping----- : ' , link)
            scrape_page(link, path_out)
            processed_links.append(link)
    
        

if __name__ == '__main__':


    
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeat' , type = bool, default = False, 
                        help = 'choose weither repeat scraping of already scraped pages')
    parser.add_argument('--path_out', type= str, default = "scraped_data_store/",
                        help = 'path of scraped websites data' )
    args = parser.parse_args()
    try : 
        processed_links_file = pd.read_csv('processed_links.csv')
        processed_links = processed_links_file.links.tolist()
    except : 
        processed_links_file = pd.DataFrame(columns=['links'])
        processed_links = processed_links_file.links.tolist()

    main(article_links, args.repeat, processed_links, args.path_out)
    processed_links_file['links'] = processed_links
    processed_links_file.to_csv('processed_links.csv' ,index = False )

    
