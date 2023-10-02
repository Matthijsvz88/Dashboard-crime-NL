import dash
from dash import html
import dash_bootstrap_components as dbc
from dash import dcc

# use pages = True allows to use multiple pages

app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.SPACELAB])
server = app.server



link = 'https://opendata.cbs.nl/portal.html?_la=nl&_catalog=CBS&tableId=83648NED&_theme=406'
linkgithub = 'https://github.com/Matthijsvz88/Dashboard-crime-NL'

# Creating the Navigation bar at the top of dashboard.

nav = dbc.Nav(
    [html.Img(src="assets/logopic.png", id = 'logo-image'),
        dbc.NavLink(["Dashboard Misdaad",html.Br(), "Nederland 2022"], class_name = 'link', href="/"),
        dbc.NavLink(["Inzichten Misdaad",html.Br(), "Nederland"], class_name = 'link', href="/inzichten"),
        dbc.NavLink(["Check Project",html.Br(),"on GitHub"],target = "_blank",class_name = 'link', href=linkgithub)
    ], id = 'navbar'
)

source = html.Div(["bron: ", dcc.Link('CBS Open Data Statline',href = link, target = "_blank")],id = 'source-link')
date_header = html.Div(["Gebaseerd op data tot 31-12-2022",html.Br()], id = 'date-header')

layout = html.Div(
    [nav, date_header,source, dash.page_container # dash.page_container contains the page data you find in pages file
     ])

app.layout = layout

if __name__ == "__main__":
    app.run(debug=False, port=8010)
