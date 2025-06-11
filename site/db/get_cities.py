from db_models import db_session
from db_models.cities import Cities
import pandas as pd

df = pd.read_csv(
    'https://raw.githubusercontent.com/hflabs/city/refs/heads/master/city.csv',
    na_values=['?'],
)  #
np = df[['address', 'population']].to_numpy()
db_session.global_init()
db_sess = db_session.create_session()
for i in range(np.shape[0]):
    city = Cities()
    name = ', '.join(reversed(np[i][0].split(', ')))
    city.name = name
    city.population = np[i][1]
    db_sess.add(city)
db_sess.commit()
