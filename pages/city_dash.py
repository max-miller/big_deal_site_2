import dash
from dash import Dash, dcc, html, Input, Output, callback

import plotly.offline as pyo
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import datetime

from dash.dependencies import Input, Output
from scipy import stats

df = pd.read_excel('pages/data/city_climate_data.xlsx',index_col=0)

city_names = ['Albuquerque, NM', 'Anchorage, AK', 'Atlanta, GA', 'Austin, TX', 'Bakersfield, CA',
             'Baltimore, MD', 'Baton Rouge, LA', 'Boise, ID', 'Boston, MA', 'Buffalo, NY', 'Charlotte, NC',
             'Chesapeake, VA', 'Chicago, IL', 'Cincinnati, OH', 'Cleveland, OH', 'Columbus, OH', 'Dallas, TX',
             'Denver, CO', 'Detroit, MI', 'Durham, NC', 'El Paso, TX', 'Fort Wayne, IN', 'Fort Worth, TX',
             'Fresno, CA', 'Greensboro, NC', 'Honolulu, HI', 'Houston, TX', 'Indianapolis, IN', 'Jacksonville, FL',
             'Jersey City, NJ', 'Kansas City, MO', 'Las Vegas, NV', 'Lexington, KY', 'Lincoln, NE',
             'Long Beach, CA', 'Los Angeles, CA', 'Louisville, KY', 'Lubbock, TX', 'Madison, WI', 'Memphis, TN',
             'Mesa, AZ', 'Miami, FL', 'Milwaukee, WI', 'Minneapolis, MN', 'Nashville, TN', 'New Orleans, LA',
             'New York, NY', 'Newark, NJ', 'Norfolk, VA', 'Oakland, CA', 'Oklahoma City, OK', 'Orlando, FL',
             'Philadelphia, PA', 'Phoenix, AZ', 'Pittsburgh, PA', 'Plano, TX', 'Portland, OR', 'Raleigh, NC',
             'Richmond, VA', 'Riverside, CA', 'Sacramento, CA', 'Saint Paul, MN', 'San Antonio, TX', 'San Diego, CA',
             'San Francisco, CA', 'San Jose, CA', 'Santa Ana, CA', 'Seattle, WA', 'Spokane, WA', 'St. Louis, MO',
             'St. Petersburg, FL', 'Stockton, CA', 'Tacoma, WA', 'Tampa, FL', 'Toledo, OH', 'Tucson, AZ',
             'Tulsa, OK', 'Virginia Beach, VA', 'Washington D.C.']

def rounder(number):
    if number < 1000:
        return number
    if number <2000:
        clean =  str((number // 250)*250)
        return clean[0]+','+clean[1:]
    digits =len(str(number))
    power = (10**(digits-1))
    clean = str((number//power)*power)
    n_commas = (digits-1)//3
    for position in range(n_commas,0,-1):
        clean = clean[:-(position*3)]+','+clean[-(position*3):]
    return clean

label_dict = {'TMAX':'Average Daily Maximum Temperature','TMIN':'Average Daily Minimum Temperature',
             't90':'Number of Days Above 90 Degrees','TMAX_rolling':'Rolling average',
              'TMIN_rolling':'Rolling average','t90_rolling':'Rolling average'}

def ttest(df, metric, city):
    diff = round(df['2010':'2019'][f'{metric}{city}'].mean()-df['1950':'2000'][f'{metric}{city}'].mean(),2)
    pvalue = stats.ttest_ind(df['2010':'2019'][f'{metric}{city}'],
                             df['1950':'2000'][f'{metric}{city}'],equal_var=False)[1]
    if pvalue == 0:
        if diff >0:
            return f'''The {label_dict[metric].lower()} was {diff} higher in the last ten years compared to the last half of the 20th century. The odds of this happening by chance are vanishingly small'''
        return f'''The {label_dict[metric].lower()} was {-diff} lower in the last ten years compared to the last half of the 20th century. The odds of this happening by chance are vanishingly small'''
    elif pvalue < .2:
        odds = rounder(int(round(1/pvalue)))
        if diff >0:
            return f'''The {label_dict[metric].lower()} was {diff} higher in the last ten years compared to the last half of the 20th century. The odds of this happening by chance are about 1 in {odds}'''

        return f'''The {label_dict[metric].lower()} was {-diff} lower in the last ten years compared to the last half of the 20th century. The odds of this happening by chance are about 1 in {odds}'''
    elif diff >0:
        return f'''The {label_dict[metric].lower()} was {diff} higher in the last ten years compared to the last half of the 20th century. This difference may well be due to chance'''
    return f'''The {label_dict[metric].lower()} was {-diff} lower in the last ten years compared to the last half of the 20th century. This difference may well be due to chance'''

background_color = 'rgba(227,227,246,.5)'
header_text = '''How much have temperatures changed in cities across the US? Select a city and a metric to see historical numbers since 1950.
Average Maximum and Average Minimum temperatures are year by year averages of all daily maximums and minimums.
You may notice that warming trends are generally more noticeable in the daily minimums - nights have gotten warmer at a faster rate than days.
'''
# app= dash.Dash()

layout = html.Div(html.Div([html.Div([html.Div(id='header',children=header_text,
                                                  style={'fontSize':24,'marginBottom':20}),

                                          dcc.Dropdown(id='city-dropdown',
                                            options=[{'label':city,'value':city} for city in city_names],
                                            value='New York, NY',style={'width':'50%','display':'inline-block'}),

                                 dcc.Dropdown(id='metric-dropdown',
                            options=[{'label':'Average Maximum Temp','value':'TMAX'},
                                    {'label':'Average Minimum Temp','value':'TMIN'},
                                    {'label':'Number of days above 90','value':'t90'}],
                            value='TMAX',style={'width':'50%','display':'inline-block'})
                                ]),

                       html.Div([html.Div(dcc.Graph(id='city_graph'),style={'width':'75%','display':'inline-block',
                                                                      'vertical-align': 'middle'}),
                                html.Div(id='ttest',style={'width':'25%','display':'inline-block',
                                                          'vertical-align': 'middle',
                                                          'fontSize':24
                                                          })])],
                                style={'backgroundColor':background_color},
                     ),id='picture',
                      )


@callback(Output('city_graph','figure'),
             [Input('metric-dropdown','value'),
             Input('city-dropdown','value')])

def update_figure(metric,city):
    temp_dict = {f'{metric}{city}':label_dict[metric],f'{metric}_rolling{city}':'Rolling average'}
    data = [go.Scatter(x=df.index, y=df[column], mode='lines', name=temp_dict[column],line={'width':3})
            for column in [f'{metric}{city}',f'{metric}_rolling{city}']]
    layout = go.Layout(title = go.layout.Title(text=f'{label_dict[metric]} and 10 year rolling average',font={'size':24}),
                       legend=go.layout.Legend(xanchor='center', x=0.5, orientation='h',font={'size':20}),
                        paper_bgcolor='rgba(227,227,246,0)',
                      plot_bgcolor='rgba(227,227,246,0)',
                        height=600,
                       yaxis=go.layout.YAxis(gridwidth=3,tickfont={'size':18}),
                       xaxis=go.layout.XAxis(tickfont={'size':18})
                      )
    return {'data':data,'layout':layout}

@callback(Output('ttest','children'),
             [Input('metric-dropdown','value'),
             Input('city-dropdown','value')])
def perform_ttest(metric,city):
    return(ttest(df,metric,city))
