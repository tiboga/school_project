import requests
from bs4 import BeautifulSoup

from db_models import db_session
from db_models.cities import Cities
# res = requests.get("https://ru.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D0%B3%D0%BE%D1%80%D0%BE%D0%B4%D0%BE%D0%B2_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B8#%D0%93%D0%BE%D1%80%D0%BE%D0%B4%D0%B0_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B9%D1%81%D0%BA%D0%BE%D0%B9_%D0%A4%D0%B5%D0%B4%D0%B5%D1%80%D0%B0%D1%86%D0%B8%D0%B8_(%D0%BA%D1%80%D0%BE%D0%BC%D0%B5_%D0%B3%D0%BE%D1%80%D0%BE%D0%B4%D0%BE%D0%B2,_%D0%B2%D1%85%D0%BE%D0%B4%D1%8F%D1%89%D0%B8%D1%85_%D0%B2_%D0%B3%D0%BE%D1%80%D0%BE%D0%B4%D0%B0_%D1%84%D0%B5%D0%B4%D0%B5%D1%80%D0%B0%D0%BB%D1%8C%D0%BD%D0%BE%D0%B3%D0%BE_%D0%B7%D0%BD%D0%B0%D1%87%D0%B5%D0%BD%D0%B8%D1%8F)").text
# soup = BeautifulSoup(res, 'html.parser')
# table = soup.find("table")
# tbody = table.find("tbody")
# trs = tbody.findChildren("tr")
# db_session.global_init()
# db_sess = db_session.create_session()

# for elem in (trs[1:]):
#     cildren = elem.findChildren("td")
#     city = Cities()
#     city.name = cildren[2].text + ", " + cildren[3].text
#     city.population = int(cildren[5].text.replace(" ", '') if "[" not in cildren[5].text else cildren[5].text.replace(" ", '')[:-3])
#     db_sess.add(city)
# table = soup.find_all("table")[1]
# tbody = table.find("tbody")
# trs = tbody.findChildren("tr")
# for elem in (trs[1:]):
#     cildren = elem.findChildren("td")
#     city = Cities()
#     city.name = cildren[2].text + ", " + cildren[3].text
#     city.population = int(cildren[5].text.replace(" ", '').remove("") if "[" not in cildren[5].text else cildren[5].text.replace(" ", '')[:-3])
#     db_sess.add(city)
# db_sess.commit()
import pandas as pd
df = pd.read_csv("https://raw.githubusercontent.com/hflabs/city/refs/heads/master/city.csv",na_values=["?"]) #
np = df[["address", "population"]].to_numpy()
db_session.global_init()
db_sess = db_session.create_session()    
for i in range(np.shape[0]):
    city = Cities()
    name = ", ".join(reversed(np[i][0].split(", ")))
    city.name = name
    city.population = np[i][1]
    db_sess.add(city)
db_sess.commit()