from os import write
import requests
from bs4 import BeautifulSoup
import re
import datetime
import pandas as pd
import streamlit as st
import locale
from tkinter import Tk
from tkinter.filedialog import asksaveasfile

LIMIT_DATE = datetime.date(2004, 2, 13)
TWICE_DATE = datetime.date(2011, 5, 10)
YEAR_RANGE = reversed(range(2004, 2022))
locale.setlocale(locale.LC_TIME, 'de_CH')


def get_lotto_dates(year):
    dates = []
    begin_dt = LIMIT_DATE if year == 2004 else datetime.date(year, 1, 1)
    end_dt = datetime.date(year+1, 1, 1)
    if year == datetime.date.today().year:
        end_dt = datetime.date.today()
    while begin_dt < end_dt:
        if begin_dt.strftime('%a') in ['Fr']:
            dates.append(begin_dt.strftime('%d.%m.%Y'))
        if begin_dt >= TWICE_DATE and begin_dt.strftime('%a') in ['Di']:
            dates.append(begin_dt.strftime('%d.%m.%Y'))
        begin_dt += datetime.timedelta(1)
    return dates


@st.cache
def get_lotto_numbers_of_year(year):
    df = pd.DataFrame(columns=['Zahl-1', 'Zahl-2', 'Zahl-3',
                               'Zahl-4', 'Zahl-5', 'Stern-1', 'Stern-2', 'Datum'])
    lotto_dt = get_lotto_dates(year)
    for dt in lotto_dt:
        request_data = {'formattedFilterDate': dt,
                        'filterDate': dt, 'currentDate': dt}
        response = requests.post(
            'https://www.swisslos.ch/de/euromillions/information/gewinnzahlen/gewinnzahlen-quoten.html', request_data)
        soup = BeautifulSoup(response.content, 'html.parser')
        lotto_nrs = re.findall('[0-9]+', ''.join(str(x)
                                                 for x in soup.find_all('span', class_='transform__center')[:7]))
        lotto_nrs.append(datetime.datetime.strptime(
            dt, '%d.%m.%Y').date().strftime('%a') + '. ' + dt)
        df.loc[len(df)] = lotto_nrs
    return df


st.sidebar.title('Benutze die Eingabetools')
selected_year = st.sidebar.selectbox('Jahr:', YEAR_RANGE)

d1 = st.sidebar.slider('Wähle ein Datum aus: ', min_value=LIMIT_DATE, max_value=datetime.date.today(
), value=datetime.date.today(), format='DD.MM.YYYY')
st.sidebar.metric('Ausgewähltes Datum: ', d1.strftime('%d.%m.%Y'))

d2 = st.sidebar.date_input('Gib ein Datum ein:', min_value=LIMIT_DATE,
                           max_value=datetime.date.today(), value=datetime.date.today())
st.sidebar.metric('Ausgewähltes Datum: ', d2.strftime('%d.%m.%Y'))


st.title('Euromillion Gewinnzahlen')
st.markdown("""
Diese Applikation zeigt alle Euromillionzishungen des ausgewählten Jahres.
* Die Daten werden von [swisslos.ch](www.swisslos.ch) abgerufen.
* Die Daten kann man als CSV Datei herunterladen.
""")
st.header('Die Ziehungen von ' + str(selected_year))
df = get_lotto_numbers_of_year(selected_year)
st.dataframe(df)


def download_data(df):
    header = ','.join(col for col in df.columns)
    csv = df.to_csv(index=False, header=False)
    Tk().withdraw()
    file_name = asksaveasfile(mode='a', defaultextension='.csv').name
    with open(file_name, 'a+') as f:
        f.seek(0)
        first_line = f.readline()
        header += '\n'
        if first_line != header:
            f.write(header)
        f.writelines(csv)


st.download_button(
    label='Als CSV herunterladen',
    data=df.to_csv(index=False),
    file_name='euromillion_' + str(selected_year) + '.csv'
)
#if st.button('Als CSV Datei Herunterladen'): download_data(df)

df2 = df.iloc[:, :7].astype('int64')
st.write(df2.describe())
st.write(df2.duplicated().sum())
