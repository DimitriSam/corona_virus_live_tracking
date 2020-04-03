from flask import Flask, render_template, session, redirect, url_for, session
# from infoclass import InfoFormDB, InfoFormRadius, InfoFormComparables
# from utils import load_data,load_data_from_db, distance, retrieve_prop_form_db, filtering, ranking, map_transactions


import folium
from folium import plugins



import requests
import json
import pandas as pd
import numpy as np

import requests
from bs4 import BeautifulSoup
import re
import time

app = Flask(__name__)


def map_corona(df_corona_m):

    global m

    m = folium.Map(location=[34.88835, 33.40835], zoom_start=2,\
                tiles="cartodbdark_matter")

    # folium.TileLayer('cartodbdark_matter').add_to(m)

    # I can add marker one by one on the map
    df_corona_m = df_corona_m[(~df_corona_m['lat'].isnull()) &(df_corona_m['Country'] != 'Diamond Princess')]



    for i in range(0,len(df_corona_m)):


        string = "<strong>Country:</strong> {}<br>\
                  <strong>Total cases:</strong> {}<br>\
                  <strong>Total deaths:</strong> {}<br>\
                  <strong>Total Recovered:</strong> {}<br>\
                  <strong>Serious critical:</strong> {}".format(df_corona_m.iloc[i]['Country'],\
                                                                df_corona_m.iloc[i]['Total cases'],\
                                                                df_corona_m.iloc[i]['Total deaths'],\
                                                                df_corona_m.iloc[i]['Total Recovered'],\
                                                                df_corona_m.iloc[i]['Serious critical']
                                                                                  )


        #     if df_corona_m.iloc[i]['Country'] == 'China':

        #         folium.Circle(
        #           location=[df_corona_m.iloc[i]['lat'], df_corona_m.iloc[i]['long']],
        #           popup=folium.Popup(string,max_width=50,min_width=150),
        #           radius=int(df_corona_m.iloc[i]['Total cases'])*30,
        #           color='crimson',
        #           fill=True,
        #           fill_color='crimson').add_to(m)


        #     else:
        folium.Circle(
              location=[df_corona_m.iloc[i]['lat'], df_corona_m.iloc[i]['long']],
              popup=folium.Popup(string,max_width=50,min_width=150),
              radius=(int(df_corona_m.iloc[i]['Total cases'])**0.3)*30000,
              color='crimson',
              fill=True,
              fill_color='crimson'

        ).add_to(m)


    #m.save('templates/corona_virus.html')



def retrieve_info():

    url = 'https://www.worldometers.info/coronavirus/'

    custom_headers = {'Referer':'https://www.worldometers.info/coronavirus/'}
    page = requests.get(url, headers = custom_headers)

    soup = BeautifulSoup(page.content, 'html.parser')

    table = soup.find('table',{'class':re.compile(r'table table-bordered table-hover')})
    countries = table.find_all('td',style="font-weight: bold; font-size:15px; text-align:left;")
    total_cases = table.findAll('td',style="font-weight: bold; text-align:right")
    new_cases = table.findAll('td',style="font-weight: normal; text-align:right;background-color:#FFEEAA;")

    #total_deaths = table.findAll('td', style = "font-weight: bold; text-align:right;")

    total_deaths = table.findAll('td', style=re.compile(r'font-weight: bold; text-align:right;'))
    total_deaths = total_deaths[1::3]

    df = []

    total_cases_chunks = list(zip(*[iter(total_cases)]*5))

    for i in range(len(countries)):

        df.append((countries[i].text.strip(),total_cases_chunks[i][0].text.strip(),total_deaths[i].text.strip(),
                   total_cases_chunks[i][1].text.strip()
                 , total_cases_chunks[i][2].text.strip()))

    with open("geo_data.json") as datafile:
        data = json.load(datafile)


    di={'S. Korea':'South Korea',
    'USA' : 'United States of America',
    'U.A.E.':'United Arab Emirates',
   'North Macedonia' : 'Macedonia',
    'UK':'United Kingdom',
   'Macao': 'Macao S.A.R',
    'Hong Kong':'Hong Kong S.A.R.'


    }


    df_corona = pd.DataFrame(data=df, columns=['Country', 'Total cases', 'Total deaths', 'Total Recovered', 'Serious critical'])
    df_corona.replace('',float('nan'),inplace=True)
    df_corona=df_corona.apply(lambda x: x.str.replace(',',''))

    df_corona['Country'] = df_corona['Country'].map(di).fillna(df_corona['Country'])


    df_corona.apply(lambda x: x.str.replace(',',''))

    centroids = pd.read_excel('country_centroids_az8.xlsx')

    df_corona_m = pd.merge(df_corona, centroids[['admin','lat','long']], how='left', left_on = 'Country', right_on='admin')

    df_corona_m = df_corona_m.fillna(0)

    df_corona_m['Total cases'] = df_corona_m['Total cases'].astype(int)
    df_corona_m.sort_values(by=['Total cases'], ascending=False, inplace = True)
    df_corona_m.reset_index(drop=True, inplace=True)


    map_corona(df_corona_m)

    return df_corona_m



@app.route('/')
def index():

    df_corona_m = retrieve_info()


    df_corona_m_r = df_corona_m.iloc[:, 0:5]
    # Connecting to a template (html file)
    return render_template('index.html',  tables=[df_corona_m_r.to_html()], titles = ['na','General info'])


@app.route('/get_map')
def get_map():

    return m._repr_html_()
    #return render_template('corona_virus.html')


if __name__ == '__main__':
    app.run()
