import csv
from datetime import datetime
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup

client = httpx.Client()


def main():
    r = client.get(url="https://www.bnm.gov.my/senior-officers-of-the-bank")
    souped = BeautifulSoup(r.content, "html.parser")
    tables = souped.select(selector="table.standard-table.table-hover.table.table-sm")
    rows = tables[0].select_one("tbody").select("tr")
    table_results = list()
    keys = ("designation", "name", "phone_or_ext")
    for row in rows:
        if row:
            cols = row.select("td")
            result = [col.get_text(strip=True, separator=" ") if col else [] for col in cols]
            if result and all(result):
                table_results.append({k: v for k, v in zip(keys, result)})

    r2 = client.get("https://www.bnm.gov.my/governance/bod")
    r2.encoding = "utf-8"
    souped2 = BeautifulSoup(r2.content, "html.parser")
    cards = souped2.select("div.card")
    
    board_members = list()
    for card in cards:
        name_tag = card.select_one(".card> div:nth-child(2) > a")
        photo_tag = card.select_one(".card > a:nth-child(1) > img")
        designation_tag = card.select_one(".card .card-footer")
        
        board_members.append({
                "designation": designation_tag.get_text(strip=True, separator=" "),
                "name": name_tag.get_text(strip=True, separator=" ").replace("\xa0", " "),
                "phone_or_ext": "",
                "photo_url": urljoin("https://www.bnm.gov.my", photo_tag.get("src", ""))
        })
    
    for dict1 in table_results:
        for dict2 in board_members:
            if dict2["name"][:16] in dict1["name"]:
                dict1["photo_url"] = dict2["photo_url"]
                break
                
            dict1["photo_url"] = ""

    name_list = [dic1["name"] for dic1 in table_results]
    for dict2 in board_members:
        if all(dict2["name"][:16] not in name for name in name_list):
            table_results.append(dict2)
            
    return table_results
    
    
if __name__ == "__main__":
    file_name = "result_table_{0}.csv".format(datetime.now().strftime("%d%m%Y%H%M%S"))
    with open(file_name, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("designation", "name", "phone_or_ext", "photo_url"), delimiter=";")
        writer.writeheader()
        print("Scraping web...")
        results = main()
        print(f"Save to {file_name}...")
        for r in results:
            writer.writerow(r)
        f.close()
        print("Done...")
