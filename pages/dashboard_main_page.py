
import geopandas as gpd
import dash_bootstrap_components as dbc
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from dash.dash_table import DataTable
import dash
from dash import html
from dash import dcc
from dash import callback
from dash.dependencies import Input, Output
from dash import ctx

dash.register_page(__name__, path = '/', name = 'Dashboard Misdaad Nederland')

# importing data

NL_misdaad = pd.read_csv('data/Crimefull.csv')
gdftot = gpd.read_file('data/dataframe.geojson')
description = pd.read_csv("data/misdrijf_meta.csv")["Description"]
populatie = pd.read_csv('data/pop.csv')

# Creating functions to create graphs in the dashboard

def create_table(region):
    used_columns = [
        "Misdaad",
        "Geregistreerde Misdrijven",
        'Misdrijven Per 1000 Inw',
        'Opgehelderde Misdrijven',
        'Opgehelderde Misdrijven Relatief'
    ]
    df = NL_misdaad.loc[(NL_misdaad.Regio == region) & (NL_misdaad.Perioden == 2022), used_columns]
    indent = [] # loop to count numeric characters in "Misdaad" column. Helps to create indentation in table
    for val in df.Misdaad:
        count = 0
        for char in val:
            if char.isnumeric():
                count += 1
        indent.append(count)
    df["Indent"] = indent
    df = df[['Indent', 'Misdaad', 'Geregistreerde Misdrijven', 'Misdrijven Per 1000 Inw',
             'Opgehelderde Misdrijven', 'Opgehelderde Misdrijven Relatief']]
    # first two columns are text columns, we declare these separately
    columns = [
        {"name": "Indent", "id": "Indent", "type": "text"},
        {"name": "Misdaad", "id": "Misdaad", "type": "text"}]

    # for other columns we use loop
    for name in df.columns[2:]:
        col_info = {
            "name": name,
            "id": name,
            "type": "numeric",
            "format": {'specifier': ','}
        }
        columns.append(col_info)
    data = df.to_dict("records")
    crime_table = DataTable(
        id="crime-table",
        columns=columns,
        data=data,
        fixed_rows={"headers": True},
        derived_virtual_data=data, # Necessary to read the correct data after sorting
        tooltip_header={ # create tooltip for headers for small screens. Keeps header content readable
        'Misdaad': {'value':'Misdaad','type':'markdown'} ,
        'Geregistreerde Misdrijven': 'Geregistreerde Misdrijven',
        'Misdrijven Per 1000 Inw':'Misdrijven Per 1000 Inw',
        'Opgehelderde Misdrijven':'Opgehelderde Misdrijven',
        'Opgehelderde Misdrijven Relatief':'Opgehelderde Misdrijven Relatief'
        },
        tooltip_data=[{ # tooltip for more detailed description of crime
        'Misdaad': {'value': row, 'type': 'markdown'}} for row in description],
        tooltip_delay=0,
        tooltip_duration=None,
        style_table={ #setting table height, need to provide height and minheight
            "minHeight": "80vh",
            "height": "80vh",
            #"overflowY": "scroll",
            "borderRadius": "0px 0px 10px 10px"
        },
        style_cell={
            # "whiteSpace": "normal",
            "height": "auto",
            "fontFamily": "verdana"
        },
        style_header={  # Styling headers for datatable through CSS
            "textAlign": "center",
            "fontSize": 12,
            "height": "50px",
            "whiteSpace": "normal",
        },
        style_data={  # styling the data within the cell
            "fontSize": 12},

        style_cell_conditional=[  # conditional styling for the cells
            {
                "if": {"column_id": "Indent"},
                'display': 'None'
            },
            {
                "if": {'column_id': 'Misdaad'},
                'width': '200px',
                "textAlign": "left",
            },
        ],
        style_data_conditional=[  # conditional styling for the data within the cells. Used to create alternating row colors and indent
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#fafbfb",
            },
            {
                'if': {
                    'filter_query': '{Indent} eq "2"',
                    'column_id': 'Misdaad'
                },
                "textIndent": "20px"
            },
            {
                'if': {
                    'filter_query': '{Indent} eq "3"',
                    'column_id': 'Misdaad'
                },
                "textIndent": "40px"
            },
            {
                'if': {
                    'filter_query': '{Indent} eq "4"',
                    'column_id': 'Misdaad'
                },
                "textIndent": "60px"
            },
        ],
    )
    return crime_table


def create_bar(region):
    data = NL_misdaad[NL_misdaad.Regio.str.contains(region, case=False, regex=False)].drop_duplicates(
        subset=['CategoryGroupID']).iloc[1:]
    naam = data.iloc[0, 1]
    fig = go.Figure() #two bars, one for total crimes and one for solved crimes. offsetgroup = 0 to have them overlap
    fig.add_bar(x=data["Misdaad"], y=data["Geregistreerde Misdrijven"], name="Misdrijven", offsetgroup=0)
    fig.add_bar(x=data["Misdaad"], y=data["Opgehelderde Misdrijven"], name="Opgelost", offsetgroup=0)
    fig.update_layout(hovermode="x unified", title={"text": f'<b>Selecteer staaf</b>', "x": 0.5, 'font_size':14},
                      margin={"t": 25, "l": 50, "r": 10, "b": 0}
                      , legend={"x": 0.75, "y": 0.95, }
                      )
    fig.update_xaxes(tickangle=15,
                     tickmode='array',
                     tickvals=data["Misdaad"],
                     ticktext=['Vermogensmisdrijven',
                               'Vernielingen,misdropenborde/gezag',
                               'Gewelds- en seksuele misdrijven',
                               'WvSr (overig)',
                               'Verkeersmisdrijven',
                               'Drugsmisdrijven',
                               'Vuurwapenmisdrijven',
                               'Overig'])
    return fig


def create_line(regio, misdaad):
    data = NL_misdaad.drop_duplicates(subset=["Perioden", "Regio", "CategoryGroupID"]).sort_values(
        ["CategoryGroupID", "Perioden"])
    misdaad_title = misdaad[2:]
    if misdaad == 'Misdrijven, totaal':
        misdaad_title = misdaad
    data = data[(data.Regio.str.contains(regio, case=False, regex=False)) & (data.Misdaad == misdaad)]
    fig = px.line(data_frame=data, x="Perioden", y="Geregistreerde Misdrijven", color=data["Misdaad"])
    fig.update_layout(hovermode="x unified", title={"text": f'{misdaad_title} in {regio}', "x": 0.5}, showlegend=False,
                      margin={"t": 40, "l": 50, "r": 10, "b": 0}, xaxis_title=None, yaxis_title=None)
    fig.update_traces(hovertemplate=' %{y}')
    return fig

# Function to create custom text. Will be used to create hover data for map figure
def hover_text(x):

    name = x["statnaam"]
    crimes = x["Geregistreerde Misdrijven"]
    crimest = x["Misdrijven Per 1000 Inw"]
    solvedr = x['Opgehelderde Misdrijven Relatief']
    return (
        f"<b>{name}</b><br>"
        f"Geregistreerde Misdrijven - {crimes:,.0f}<br>"
        f"Misdrijven Per 1000 Inw - {crimest}<br>"
        f"Opgehelderde Misdrijven Relatief - {solvedr}%<br>"
    )

def create_map(param, reverse=False):
    color = 'ylorrd' # color scale from yellow to red, low is better high is worse
    if reverse:
        color = 'rdylgn' #reverse color scale when user indicates reverse = True
    text = gdftot.apply(hover_text, axis=1) #create hover text with custom function
    fig = px.choropleth_mapbox(gdftot,
                               geojson=gdftot.geometry,
                               locations=gdftot.index,
                               color=gdftot[param],
                               mapbox_style="carto-positron",
                               title="Misdaad",
                               center={"lat": 52.132633, "lon": 5.291266},
                               zoom=5.9,
                               color_continuous_scale=color)
    fig.update_layout(margin={"t": 0, "l": 10, "r": 10, "b": 0},
                      coloraxis_colorbar=dict(title=""))
    fig.update_traces(hovertemplate=text),
    return fig


# preparing data for dropdown menu containing all regions
steden = NL_misdaad.loc[(NL_misdaad.Perioden == 2022)].dropna(thresh=7, axis=0)
stedendict = dict(zip(steden.Regio, steden.Regio))
stedenlabels = [{'label': k, 'value': v} for k, v in stedendict.items()]


def create_tab(content, label, value):
    return dcc.Tab(
        content,
        label=label,
        value=value,
        id=f"{value}-tab",
        className="single-tab",
        selected_className="single-tab--selected",
    )

# functions to create cards 

def create_card_crime(regio, misdaad):
    mask1 = NL_misdaad.Perioden == 2022
    mask2 = NL_misdaad.Regio == regio
    mask3 = NL_misdaad.Misdaad == misdaad
    param22 = NL_misdaad.loc[mask1&mask2&mask3,'Geregistreerde Misdrijven'].item()
    param21 = NL_misdaad.loc[(NL_misdaad.Perioden == 2021)&mask2&mask3,'Geregistreerde Misdrijven'].item()
    try:
        change = round((-1 + param22/param21)*100,2)
    except ZeroDivisionError:
        change = 0
    color = 'red'
    symbol = "+"
    if change < 0.1 : #if the change is lower than 0.1 use green
        color = '#00FA9A'
    if change < 0: #if change is lower than 0 dont use + symbol
        symbol = ""
    card = dbc.Card([
                dbc.CardHeader([html.H6('Geregistreerde Misdrijven'),html.P("vs 2021",style = {'font-size':'12px', 'marginBottom':'2px'})],
                              style = {'background-color': '#2F4F4F','color':'white','border-radius': '15px 15px 0px 0px'}),
                dbc.CardBody([html.H6(f"{param22:,.0f}"),html.P(f'{symbol}{change}%',style =  {'color':color, 'font-size':'12px'})])
    ],color="primary",className="mb-4",outline=True,style = {'text-align':"center",'border-radius': '15px 15px 20px 20px'})
    return card

def create_card_crime_t(Regio, misdaad):
    mask1 = NL_misdaad.Perioden == 2022
    mask2 = NL_misdaad.Regio == Regio
    mask3 = NL_misdaad.Misdaad == misdaad
    param22 = NL_misdaad.loc[mask1&mask2&mask3,"Misdrijven Per 1000 Inw"].item()
    param21 = NL_misdaad.loc[(NL_misdaad.Perioden == 2021)&mask2&mask3,"Misdrijven Per 1000 Inw"].item()
    change = round(param22-param21,1)
    color = 'red'
    symbol = "+"
    if change < 0.1 : #if the change is lower than 0.1 use green
        color = '#00FA9A'
    if change < 0: #if change is lower than dont use + symbol
        symbol = ""
    card = dbc.Card([
                dbc.CardHeader([html.H6("Misdrijven Per 1000 Inw"),html.P("vs 2021",style = {'font-size':'12px', 'marginBottom':'2px'})],
                              style = {'background-color': '#2F4F4F','color':'white','border-radius': '15px 15px 0px 0px'}),
                dbc.CardBody([html.H6(f"{param22}"),html.P(f'{symbol}{change}',style =  {'color':color, 'font-size':'12px'})])
    ],color="primary",className="mb-4",outline=True)
    return card

def create_card_pop(Regio):
    try:
        mask1 = populatie.Regio == Regio
        pop = populatie.loc[mask1,"Populatie"].item()
        card = dbc.Card([
                dbc.CardHeader([html.H6("Populatie"),html.P("1 Januari 2022",style = {'font-size':'12px', 'marginBottom':'2px'})],
                              style = {'background-color': '#2F4F4F','color':'white','border-radius': '15px 15px 0px 0px'}),
                dbc.CardBody([html.H6(f"{pop:,.0f}")])
        ],color="primary",className="mb-4",outline=True)
    except ValueError: #there's a few regions with no definable population, in that case display NA for population
        card = dbc.Card([
                dbc.CardHeader([html.H6("Populatie")],
                              style = {'background-color': '#2F4F4F','color':'white','border-radius': '15px 15px 0px 0px'}),
                dbc.CardBody([html.H6("NA")])],color="primary",className="mb-4",outline=True)
    return card

#creating the graphs and tabs using previously defined functions

misdrijven_relatief = dcc.Graph(figure=create_map("Misdrijven Per 1000 Inw"))
misdrijven_totaal = dcc.Graph(figure=create_map("Geregistreerde Misdrijven"))
Opgehelderde_Misdrijven = dcc.Graph(figure=create_map("Opgehelderde Misdrijven Relatief", reverse=True))

tab_misdrijven_relatief = create_tab(misdrijven_relatief, 'Misdrijven per 1000 Inw', 'Misdrijven per 1000 Inw')
tab_misdrijven_totaal = create_tab(misdrijven_totaal, "Geregistreerde Misdrijven", "Geregistreerde Misdrijven")
tab_misdrijven_opgehelderd = create_tab(Opgehelderde_Misdrijven, "Opgehelderde Misdrijven Relatief",
                                        "Opgehelderde Misdrijven Relatief")

map_tabs = dcc.Tabs(
    [tab_misdrijven_totaal, tab_misdrijven_relatief, tab_misdrijven_opgehelderd],
    className="tabs-container",
    id="table-tabs",
    value='Misdrijven per 1000 Inw')

card_div = html.Div([create_card_pop('Nederland'), create_card_crime("Nederland", "Misdrijven, totaal"),
                     create_card_crime_t("Nederland","Misdrijven, totaal")],
                    style = {'gridArea':'cards','margin-top':'50px'}, id = 'cards-div')

fig_map = create_map("Misdrijven Per 1000 Inw")
map_graph = dcc.Graph(figure=fig_map, id="map-graph")
map_div = html.Div([map_tabs], style={'gridArea': 'maps', 'margin-top': '10px'})

regio = "Nederland"
misdaad = "Misdrijven, totaal"

dropdown = dcc.Dropdown(id='city-picker', options=stedenlabels,
                        value='Nederland', clearable = False)

# dropdowndiv = html.Div([html.H6('Regio:', id = 'dropdowntitle'), dropdown], id = 'dropdown-div')
# dropdowndiv.style = {'gridArea': "dropdown"}
table = create_table(regio)
tablediv = html.Div([ table])
tablediv.style = {'gridArea': "tables"}
line = dcc.Graph(figure=create_line(regio, misdaad), id='line',
                 style={'height': "calc(25vh - 30px)", "margin-bottom": "30px"})
lineheader = html.H1("Jaarlijkse Ontwikkeling", className='graph-header')
linediv = html.Div([lineheader, line],style ={'gridArea': 'line'} )

bars = dcc.Graph(figure=create_bar(regio), id='bars', style={'height': "calc(35vh - 30px)"})
barheader = html.H1("Verdeling Misdaad per Categorie (Totaal vs Opgelost)", className='graph-header')
#
bardiv = html.Div([barheader, bars])
bardiv.style = {'gridArea': "bar", 'margin-bottom': '0px'}

container = html.Div([card_div, dropdown, tablediv, bardiv, linediv, map_div], id = 'container')

layout = html.Div([container], style = {'max-width': '2000px','margin': 'auto'})

#callbacks to update figures interactively



@callback(Output('line', 'figure'), 
              [Input('bars', 'clickData')], Input('city-picker', 'value'))
def changeline(clickData, regio):
    crime = 'Misdrijven, totaal'
    button_clicked = ctx.triggered_id
    if button_clicked == 'bars':
        crime = json.dumps(clickData['points'][0]['label']).replace('"', '')
    return create_line(regio, crime)


@callback(Output('bars', 'figure'),
              [Input('city-picker', 'value')])
def changebars(regio):
    return create_bar(regio)

@callback(Output('cards-div','children'),
             [Input('city-picker','value'),
              Input('bars', 'clickData')])

def changecards(regio, clickData):
    crime = 'Misdrijven, totaal'
    button_clicked = ctx.triggered_id
    if button_clicked == 'bars':
        crime = json.dumps(clickData['points'][0]['label']).replace('"', '')
    return create_card_pop(regio),create_card_crime(regio, crime),create_card_crime_t(regio, crime)

@callback(Output('crime-table', 'data'),
              [Input('city-picker', 'value')])
def changetable(regio): #output to change table is data, we recreate data to fill the table
    used_columns = [
        "Misdaad",
        "Geregistreerde Misdrijven",
        'Misdrijven Per 1000 Inw',
        'Opgehelderde Misdrijven',
        'Opgehelderde Misdrijven Relatief'
    ]
    df = NL_misdaad.loc[(NL_misdaad.Regio == regio) & (NL_misdaad.Perioden == 2022), used_columns]
    indent = []
    for val in df.Misdaad:
        count = 0
        for char in val:
            if char.isnumeric():
                count += 1
        indent.append(count)
    df["Indent"] = indent
    df = df[['Indent', 'Misdaad', 'Geregistreerde Misdrijven', 'Misdrijven Per 1000 Inw',
             'Opgehelderde Misdrijven', 'Opgehelderde Misdrijven Relatief']]
    # first two columns are text columns, we declare these separately
    # columns = [
    #     {"name": "Indent", "id": "Indent", "type": "text"},
    #     {"name": "Misdaad", "id": "Misdaad", "type": "text"}]

    # for other columns we use loop
    # for name in df.columns[2:]:
    #     col_info = {
    #         "name": name,
    #         "id": name,
    #         "type": "numeric",
    #         "format": {'specifier': ','}
    #     }
    #     columns.append(col_info)
    data = df.to_dict("records")
    return data


