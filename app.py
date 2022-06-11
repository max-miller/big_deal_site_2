from dash import Dash, dcc, html, Input, Output, callback
from pages import city_dash, modeling_dash, homepage

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

header_style = {'float':'left','color':'#f2f2f2','text-align':'center','padding':'14px 16px','font-size':'17px'}
# app = dash.Dash()

app.layout = html.Div([
    # represents the browser address bar and doesn't render anything
    dcc.Location(id='url', refresh=False),
    html.Div([html.A('Home',href='/',style=header_style),
    html.A('Cities',href='/cities',style=header_style),
    html.A('Modeling',href='/modeling',style=header_style),

    ],style={'overflow': 'hidden','background-color': '#333'}),



    # content will be rendered in this element
    html.Div(id='page-content')
])

@callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/modeling':
        return modeling_dash.layout
    elif pathname == '/cities':
        return city_dash.layout
    elif pathname == '/':
        return homepage.layout



if __name__ == '__main__':
    app.run_server(port=8051,debug=True)
