import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from html2text import HTML2Text
import multiprocessing as mp

def remove_html_tags(html):
    h = HTML2Text()
    h.ignore_links = True
    return h.handle(html)

def cfDecodeEmail(encodedString):
    if encodedString:
        k = int(encodedString[:2], 16)
        email = ''.join([chr(int(encodedString[i:i+2], 16) ^ k) for i in range(2, len(encodedString), 2)])
        return email
    else:
        return "Not Available"

def scrape_page(url, results_list):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        s = soup.find('ul', class_='list-group')
        college = []
        r = s.find_all('a')
        college.append(r)

        phones = []
        locations = []
        emails = []

        for link in r:
            link_u = link.get('href')
            base = 'https://www.indcareer.com'
            link_url = f'{base}{link_u}'

            link_response = requests.get(link_url)

            if link_response.status_code == 200:
                link_soup = BeautifulSoup(link_response.content, 'html.parser')
                p = link_soup.find('th', string=' Phone ')

                if p:
                    phone = str(p.find_next('td').text)
                    phones.append(phone)
                else:
                    phone = "Not Available"
                    phones.append(phone)

                l = link_soup.find('th', string=' City ')

                if l:
                    location = str(l.find_next('td').text)
                    locations.append(location)
                else:
                    location = "Not Available"
                    locations.append(location)

                e = link_soup.find('th', string=' Email ')

                if e:
                    encoded_email = e.find_next('a').get("data-cfemail")
                    email = cfDecodeEmail(encoded_email)
                    emails.append(email)
                else:
                    email = "Not Available"
                    emails.append(email)
        k = [[remove_html_tags(str(element))] + [location, phone, email] for element, location, phone, email in zip(r, locations, phones, emails)]

        results_list.extend(k)
    else:
        print(f'Error: Failed to retrieve the webpage. Status code: {response.status_code}')

if __name__ == "__main__":
    base_url = 'https://www.indcareer.com/find/all-colleges-in-chhattisgarh?page='
    num_pages = 32

    manager = mp.Manager()
    all_paragraphs = manager.list()
    urls = [f'{base_url}{page_number}' for page_number in range(num_pages + 1)]

    processes = []
    for url in urls:
        p = mp.Process(target=scrape_page, args=(url, all_paragraphs))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    # Convert the Manager list to a regular list before creating the DataFrame
    df = pd.DataFrame(list(all_paragraphs), columns=['College', 'Location', 'Phone No.', 'Email ID'])

    print(df)
    excel_filename = '1.xlsx'
    df.to_excel(excel_filename, index=False, engine='openpyxl')
    print(f'Data saved to {excel_filename}')
    os.system(excel_filename)
