import dash
from dash import Dash, dcc, html, Input, Output, callback

import plotly.offline as pyo
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import datetime

from dash.dependencies import Input, Output

electric_df = pd.read_excel('pages/data/energy_modeling_inputs.xlsx',sheet_name='electric_df',index_col=0)
#electric_df.index = pd.to_datetime(electric_df.index)
resi_energy = pd.read_excel('pages/data/energy_modeling_inputs.xlsx',sheet_name='resi_energy')
com_energy = pd.read_excel('pages/data/energy_modeling_inputs.xlsx',sheet_name='com_energy')
gas_energy = pd.read_excel('pages/data/energy_modeling_inputs.xlsx',sheet_name='gas_energy').set_index('Month')
BTU_to_kwh = 0.000293071*1000000000000/1000000

resi_pivot = resi_energy.pivot(index='date',columns='Description',values='Value')
resi_pivot.rename({'Natural Gas Consumed by the Residential Sector (Excluding Supplemental Gaseous Fuels)':'Natural Gas'},
                  axis=1,inplace=True)
resi_pivot['Natural Gas'] = pd.to_numeric(resi_pivot['Natural Gas'])*BTU_to_kwh
resi_pivot = resi_pivot['2010':]['Natural Gas'].groupby(by=[resi_pivot['2010':].index.month]).mean()

com_pivot = com_energy.pivot(index='date',columns='Description',values='Value')
com_pivot.rename({'Natural Gas Consumed by the Commercial Sector (Excluding Supplemental Gaseous Fuels)':'Natural Gas'},
                  axis=1,inplace=True)
com_pivot['Natural Gas'] = pd.to_numeric(com_pivot['Natural Gas'])*BTU_to_kwh
com_pivot = com_pivot['2010':]['Natural Gas'].groupby(by=[com_pivot['2010':].index.month]).mean()

gas_energy['gasoline'] = pd.to_numeric(gas_energy['gasoline'])
gas_pivot = gas_energy['2010':]['gasoline'].groupby(by=[gas_energy['2010':].index.month]).mean()

def future_generation(electric_df,growth_rates,years_of_growth):
    date_index = pd.date_range(electric_df.index[-1]+pd.offsets.DateOffset(months=1),
                               electric_df.index[-1]+pd.offsets.DateOffset(years=10),freq='MS')
    append_df = pd.DataFrame(index=date_index)
    for fuel in electric_df.columns:
        rate = 1+growth_rates[fuel]
        values = list(electric_df[fuel][-12:]*rate)
        for n in range(2,years_of_growth+1):
            values += list(electric_df[fuel][-12:]*(rate**n))
        for n in range(years_of_growth+1,11):
            values += values[-12:]
        append_df[fuel] = values
    return pd.concat([electric_df,append_df])

def additional_demand(start_date,electric_df,parameters):
    date_index = pd.date_range(start_date+pd.offsets.DateOffset(months=1),
                               start_date+pd.offsets.DateOffset(years=10),freq='MS')
    demand_growth_df = pd.DataFrame(index=date_index)
    demand_growth_df['Resi heating'] = np.nan
    demand_growth_df['Com heating'] = np.nan
    demand_growth_df['autos'] = np.nan
    for date in date_index:
        if parameters['inc_res']==1:
            demand_growth_df.loc[date,'Resi heating'] = (resi_pivot*parameters['heat_efficiency']*
                                                         np.min(((parameters['resi_grow']**
                                                                  (date.year-start_date.year))-1,1)))[date.month]
        if parameters['inc_com']==1:
            demand_growth_df.loc[date,'Com heating'] = (com_pivot*parameters['heat_efficiency']*
                                                         np.min(((parameters['com_grow']**
                                                                  (date.year-start_date.year))-1,1)))[date.month]
        if parameters['inc_cars']==1:
            demand_growth_df.loc[date,'autos'] = (gas_pivot*parameters['car_efficiency']*
                                                         np.min(((parameters['car_grow']*.1*
                                                                  (date.year-start_date.year)),1)))[date.month]


    electric_df = electric_df.merge(demand_growth_df,how='left',left_index=True,right_index=True)
    electric_df.fillna(0,inplace=True)
    return electric_df

def model_energy(electric_df,parameters):
    df = electric_df[['wind','Total Solar','all fuels (utility-scale)','Other non-FF sources']].copy()
    df.rename({'all fuels (utility-scale)':'Total Demand'},axis=1,inplace=True)

    df = future_generation(df,parameters['growth rates'],parameters['years_of_growth'])
    df = additional_demand(electric_df.index[-1],df,parameters)

    df['Total Demand'] = df[['Total Demand','Resi heating','Com heating','autos']].sum(axis=1)
    df['Total Renewables'] = df[['wind','Total Solar','Other non-FF sources']].sum(axis=1)

    df['Excess renewables'] = np.maximum((df['Total Renewables'] - df['Total Demand']),0)
    df['Renewable plus Storage'] = df['Total Renewables']
    running_total = 0
    for index in df.index:
        if df.loc[index]['Excess renewables'] > 0:
            running_total += df.loc[index]['Excess renewables']
        elif running_total > 0:
            capacity_used = np.min((running_total,
                                   (1/parameters['storage efficiency'])*(df.loc[index]['Total Demand']-df.loc[index]['Total Renewables'])))
            df.loc[index,
                     'Renewable plus Storage'] = df.loc[index]['Total Renewables']+(parameters['storage efficiency']*capacity_used)
            running_total -= capacity_used

    return df[str(electric_df.index[-1].year-5):]

parameters = {'inc_res':0,'inc_com':0,'heat_efficiency':.5,'resi_grow':1.1,'com_grow':1.1,'storage efficiency':.25,
              'inc_cars':0,'car_efficiency':.5,'car_grow':.04,'years_of_growth':5,
             'growth rates':{'wind':.1,'Total Solar':.2,'Total Demand':0,'Other non-FF sources':0}}
slider_tooltip = {"placement": "bottom", "always_visible": True}


layout = html.Div([

    dcc.Graph(id='graph_modeling'),

    html.Div([
        html.Div([
            dcc.Checklist(['Include Residential Heating'],[],inline=True,id='res_selection'),
            html.Div('Growth rate of residential heating electrification'),
            dcc.Slider(0, .5, .01, value=.05, marks=None,tooltip=slider_tooltip,id='res_grow')
        ],style={'width': '30%','display': 'inline-block'}),
        html.Div([
            dcc.Checklist(['Include Commercial Heating'],[],inline=True,id='com_selection'),
            html.Div('Growth rate of commercial heating electrification'),
            dcc.Slider(0, .5, .01, value=.05, marks=None,tooltip=slider_tooltip,id='com_grow')
        ],style={'width': '30%','display': 'inline-block'}),
        html.Div([
            dcc.Checklist(['Include Automotive Electrification'],[],inline=True,id='car_selection'),
            html.Div('Fraction of new cars sold that are electric'),
            dcc.Slider(0, 1, .01, value=.04, marks=None,tooltip=slider_tooltip,id='car_grow')
        ],style={'width': '30%','display': 'inline-block'})
        ],style={'padding':'25px',}),

    html.Div([
        html.Div([html.Div('Energy savings from heat pumps',style={'width': '45%','display': 'inline-block','vertical-align': 'middle'}),
                 html.Div(dcc.Slider(0, 1, .01, value=.5, marks=None,tooltip=slider_tooltip,id='heat_eff'),
                 style={'width': '45%','display': 'inline-block','vertical-align': 'middle'})],
                 style={'width': '45%','display': 'inline-block'}),
        html.Div([html.Div('Energy savings from electric vehicles',style={'width': '45%','display': 'inline-block','vertical-align': 'middle'}),
                 html.Div(dcc.Slider(0, 1, .01, value=.5, marks=None,tooltip=slider_tooltip,id='car_eff'),
                 style={'width': '45%','display': 'inline-block','vertical-align': 'middle'})],
                 style={'width': '45%','display': 'inline-block'})
    ],style={'padding':'25px',}),

    html.Div([
        html.Div([html.Div('Growth of solar power',style={'width': '45%','display': 'inline-block','vertical-align': 'middle'}),
                 html.Div(dcc.Slider(0, .5, .01, value=.2, marks=None,tooltip=slider_tooltip,id='solar_grow'),
                 style={'width': '45%','display': 'inline-block','vertical-align': 'middle'})],
                 style={'width': '45%','display': 'inline-block'}),
        html.Div([html.Div('Growth rate of wind',style={'width': '45%','display': 'inline-block','vertical-align': 'middle'}),
                 html.Div(dcc.Slider(0, .5, .01, value=.1, marks=None,tooltip=slider_tooltip,id='wind_grow'),
                 style={'width': '45%','display': 'inline-block','vertical-align': 'middle'})],
                 style={'width': '45%','display': 'inline-block'})
    ],style={'padding':'25px',}),

    html.Div(
        html.Div([html.Div('Renewable build up through year:',style={'width': '45%','display': 'inline-block','vertical-align': 'middle'}),
                 html.Div(dcc.Slider(2025, 2032, 1, value=2027, marks=None,tooltip=slider_tooltip,id='ren_grow_through'),
                 style={'width': '45%','display': 'inline-block','vertical-align': 'middle'})],
                 style={'width': '45%','display': 'inline-block'}),style={'padding':'25px',}),

    html.Div(['Efficiency of long term storage(%): ',
              dcc.Input(id='storage_eff', value=25)],style={'padding':'25px',}),

    html.Div(id='electric_growth',style={'padding':'25px',}),
    html.Div(id='wind_growth',style={'padding':'25px',})
])
@callback(Output('graph_modeling','figure'),
            Output('electric_growth','children'),
            Output('wind_growth','children'),
             [Input('res_selection','value'),
              Input('com_selection','value'),
              Input('car_selection','value'),
             Input('res_grow','value'),
             Input('com_grow','value'),
             Input('car_grow','value'),
             Input('heat_eff','value'),
             Input('car_eff','value'),
             Input('solar_grow','value'),
             Input('wind_grow','value'),
             Input('ren_grow_through','value'),
             Input('storage_eff','value')])

def update_figure(res_selection,com_selection,car_selection,r_grow,c_grow,car_grow,heat_eff,car_eff,solar_grow,
                 wind_grow,ren_grow_through,storage_eff):
    if 'Include Residential Heating' in res_selection:
        parameters['inc_res'] = 1
    else:
        parameters['inc_res'] = 0
    if 'Include Commercial Heating' in com_selection:
        parameters['inc_com'] = 1
    else:
        parameters['inc_com'] = 0
    if 'Include Automotive Electrification' in car_selection:
        parameters['inc_cars'] = 1
    else:
        parameters['inc_cars'] = 0

    parameters['resi_grow'] = r_grow+1
    parameters['com_grow'] = c_grow+1
    parameters['car_grow'] = car_grow
    parameters['heat_efficiency'] = 1-heat_eff
    parameters['car_efficiency'] = 1-car_eff
    parameters['growth rates']['Total Solar'] = solar_grow
    parameters['growth rates']['wind'] = wind_grow
    parameters['years_of_growth'] = ren_grow_through - 2022
    parameters['storage efficiency'] = int(storage_eff)/100
    df = model_energy(electric_df,parameters)
    data = [go.Scatter(x=df.index, y=df[column], mode='lines', name=column) for column in ['Total Demand','Renewable plus Storage','Total Renewables']]
    layout = go.Layout(title = f'Renewable growth vs. total demand',yaxis={'range':(0,(df.max().max())*1.1)})

    start_date = electric_df.index[-1] - pd.offsets.DateOffset(months=11)
    base_solar = df[f'{start_date.year}-{start_date.month}':
    f'{electric_df.index[-1].year}-{electric_df.index[-1].month}']['Total Solar'].sum()

    new_solar = df[df.index[-12]:]['Total Solar'].sum()
    solar_text = f'''Total solar power output will be {round(new_solar/base_solar,2)}X current output.'''

    base_wind = df[f'{start_date.year}-{start_date.month}':
    f'{electric_df.index[-1].year}-{electric_df.index[-1].month}']['wind'].sum()
    new_wind = df[df.index[-12]:]['wind'].sum()
    wind_text = f'''Total wind power output will be {round(new_wind/base_wind,2)}X current output.'''
    return {'data':data,'layout':layout}, solar_text, wind_text
