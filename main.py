import time
import csv
from io import StringIO

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
ua=UserAgent()
headers = {
    'User-Agent': ua.random
}
def scrape_link(url="https://swfis.pwr.edu.pl/oferta/dyscypliny"):
    soup=BeautifulSoup(requests.get(url,headers=headers).content,'html.parser')
    href_tags=soup.find_all('a', href=True)
    links=[link.get('href') for link in href_tags if link.get('href')!='']
    doc=""
    for link in links:
        if "https://docs.google.com/" in link:
            doc=link
            break
    # print(doc)
    if not doc or doc != "https://docs.google.com/spreadsheets/d/1loQPwhuwM6MAZBWGntm0acNm_yDqehPSJk0wuorC3h4/edit?usp=sharing":
        return True, doc
    return False, None

def run():
    while True:
        res, doc = scrape_link()
        if res and doc!="":
            notify(notif="Jest nowa rozpiska!")
            split=doc.split('/')
            if "edit" in split[-1]:
                split.pop(-1)
                doc="/".join(split)
            doc+="/export?format=csv"
            scrape_groups(doc)
            break
        elif res:
            notify(notif="Ze strony zniknął link!")
        time.sleep(30)


            
def scrape_groups(doc):
    resp = requests.get(doc)
    resp.encoding="utf-8"
    KW_SKIP=["SWF000",
             "PONIEDZIAŁEK",
             "WTOREK",
             "ŚRODA",
             "CZWARTEK",
             "PIĄTEK",
             "mgr Robert Jarosz",
             "mgr Grzegorz Banaszczyk",
             "015",
             "15",
             "P-22"]
    groups=[]
    if resp.status_code == 200:
        csv_data=StringIO(resp.text)
        reader=csv.reader(csv_data)
        for row in reader:
            if any("Badminton" in col for col in row):
                groups_row=[]
                for col in row:
                    if any(kw in col for kw in KW_SKIP) or col=="":
                        continue
                    groups_row.append(col)
                if len(groups_row)!=5:
                    notify(notif="Błąd podczas parsowania csvki z miejscami - sprawdź ręcznie")
                    return
                groups.append(groups_row)
        
        slots=""
        for group in groups:
            if group[2] != "0":
               slots=slots+", "+group[1]
        if slots!="":
            notify(notif=f"Wolne miejsca w grupach {slots}!")
        else:
            notify(notif="Nie ma wolnych miejsc, lub błąd parsowania - sprawdź ręcznie")
    return
def notify(notif):
    time.sleep(5)
    requests.post(
        "https://ntfy.sh/PWR-zapisywacz-wf",
        data=notif.encode("utf-8"),
        headers={
            "Title": "Zapisy WF",
            "Priority": "urgent",
            "Tags": "warning"
        }
    )
    return
if __name__ == '__main__':
    run()


