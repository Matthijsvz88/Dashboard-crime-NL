import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import dash
from dash import html
from dash import dcc
from dash import callback
from dash.dependencies import Input, Output
from dash.dash_table import DataTable

dash.register_page(__name__, path='/inzichten', name='Inzichten Misdaad Nederland') # register the page so it can be used by the main app



NL_misdaad = pd.read_csv('data/Crimefull.csv') #importing data

#read in text for dataframe
f =  open('data/text.txt')
datatext = f.read()

def create_scatter():
    df = NL_misdaad.loc[NL_misdaad.RegioS.str.contains("GM")]
    df = df.loc[(df.Misdaad == "Misdrijven, totaal")]
    df = df.loc[df.Perioden == 2022]
    fig = px.scatter(df, x='BevolkingOp1Januari_1', y='Misdrijven Per 1000 Inw',
                         hover_name="Regio",labels = {'BevolkingOp1Januari_1':"Populatie"})
    return fig

def crimes_per_year(parameter):
    mask = NL_misdaad.Regio == "Nederland"
    df = NL_misdaad.loc[mask].copy()
    df = df.drop_duplicates(subset=["CategoryGroupID", "Perioden"]).sort_values(
        ['Perioden', "CategoryGroupID"]).set_index(["Perioden", "Misdaad"]).copy()
    df = df.loc[:, parameter].unstack(1).copy()
    return df

def bars_crime_change(year1,year2,parameter):
    df = crimes_per_year(parameter)
    df = round(df.loc[year2] / df.loc[year1] * 100, 1)
    if parameter == "Opgehelderde Misdrijven Relatief":
        df = crimes_per_year(parameter)
        df = round(df.loc[year2] - df.loc[year1],2)
    fig = px.bar(df, orientation='h', text = [f'{i}%' for i in df])
    fig.update_layout(showlegend=False, margin_r = 0)
    fig.update_xaxes(visible=False)
    fig.update_traces(hovertemplate='%{y} : %{x}%<extra></extra>')
    return fig



def line_yearly_crime(year1,year2,parameter):
    df = crimes_per_year(parameter)
    df = df.loc[year1:year2]
    if parameter == 'Geregistreerde Misdrijven':
        df = round(df.div(df.loc[year1])*100,1)
    fig = px.line(df)
    fig.update_layout(hovermode = 'x unified')
    fig.update_traces(hovertemplate=' %{y}%')
    #change the line names with line break to better fit the graph
    fig['data'][1]['name'] = '2 Vernielingen,<br>misdropenborde/gezag'
    fig['data'][2]['name'] = '3 Gewelds- en <br>seksuele misdrijven'
    fig['data'][3]['name'] = '4 Misdrijven WvSr<br> (overig)'
    fig['data'][7]['name'] = '8 Misdrijven overige<br> wetten'
    return fig

# create df for DataTable
def datatable_crime_df():
    maskcrime = NL_misdaad.Misdaad == "Misdrijven, totaal"
    maskregion = NL_misdaad.RegioS.str.contains('GM')
    df = NL_misdaad[maskcrime & maskregion].set_index(['Perioden', 'Regio'])['Misdrijven Per 1000 Inw'].unstack(0).copy()
    df = df[df[2022].notna()]
    df['Verschil'] = round(df[2022] - df.fillna(method='bfill', axis=1).iloc[:, 0], 2)
    df.sort_values('Verschil', ascending=True)
    df = df.reset_index()
    df.columns = ['Regio', '2010', '2011', '2012', '2013', '2014',
                      '2015', '2016', '2017', '2018', '2019', '2020',
                      '2021', '2022', 'Verschil']
    return df

def create_crime_table():
    df = datatable_crime_df()
    used_columns = ['Regio', '2010', '2011', '2012', '2013', '2014',
                    '2015', '2016', '2017', '2018', '2019', '2020',
                    '2021', '2022', 'Verschil']

    #Regio column is text type, the other ones are numeric

    columns = [
        {"name": "Regio", "id": "Regio", "type": "text"},
    ]
    # for other columns we use loop
    for name in df.columns[1:]:
        col_info = {
            "name": name,
            "id": name,
            "type": "numeric",
            "format": {'specifier': ','}
        }
        columns.append(col_info)
    data = df.sort_values('Regio').to_dict("records")
    crime_table = DataTable(
        id="crime-table",
        columns=columns,
        data=data,
        fixed_rows={"headers": True},
        style_table={
            # "minHeight": "50vh",
            # "height": "50vh",
            "overflowX":"auto",
            "width": '70vw',
            "overflowY": "scroll",
            'border': '1px black',
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

        style_cell_conditional=[
            {
                "if": {'column_id': 'Regio'},
                'width': '150px',
                "textAlign": "left",
            },
        ],
        sort_action='native',
        filter_action='native',
        filter_options={'case': 'insensitive'},
        page_size=150,
        virtualization=True,
        style_data_conditional=[  # conditional styling for the data within the cells
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#fafbfb",
            }
        ]
    )
    return crime_table


scatter_graph = dcc.Graph(figure=create_scatter(), id="scatter-graph", style={"width": "90vw", 'max-width': '1500px', 'margin-left': 'auto',
	                        'margin-right': 'auto' })

bars_dev_crime = dcc.Graph(figure=bars_crime_change(2010,2022,'Geregistreerde Misdrijven'), id="bars-change-graph", style={"width": "50vw", 'max-width': '900px'})
line_dev_crime = dcc.Graph(figure=line_yearly_crime(2010,2022,'Geregistreerde Misdrijven'), id="line-graph", style={"width": "50vw", 'max-width': '900px'})
slider_crime = html.Div([dcc.RangeSlider(2010, 2022, 2, marks={i: '{}'.format(i) for i in range(2010, 2023)},
                                   value=[2010, 2022], id='range-slider-crime')],
                  style={"width": '70%', 'padding-left': '25%', 'margin-bottom': '50px'})

bars_dev_solved_crime = dcc.Graph(figure=bars_crime_change(2010,2022,'Opgehelderde Misdrijven Relatief'), id="bars-solved-crime", style={"width": "50vw", 'max-width': '900px'})
line_dev_solved_crime = dcc.Graph(figure=line_yearly_crime(2010,2022,'Opgehelderde Misdrijven Relatief'), id="line-solved-crime", style={"width": "50vw", 'max-width': '900px'})
slider_solved_crime = html.Div([dcc.RangeSlider(2010, 2022, 2, marks={i: '{}'.format(i) for i in range(2010, 2023)},
                                   value=[2010, 2021], id='range-slider-solved-crime')],
                  style={"width": '70%', 'padding-left': '25%', 'margin-bottom': '50px'})

layout = html.Div([dcc.Markdown('# Ontwikkeling misdaad per gemeente', style={'text-align': 'center'}),
                   dcc.Markdown(datatext.split('$')[0], className='textbox'),
                   html.Div([dbc.Row([create_crime_table()])],id = 'table_div'),
                   dcc.Markdown(datatext.split('$')[1], className='textbox'),
                   html.Div([scatter_graph]),
                   html.Hr(),
                   dcc.Markdown('# Ontwikkeling misdaad per categorie', style={'text-align': 'center'}),
                   dcc.Markdown(datatext.split('$')[2], className='textbox'),
                   #dropdown,
                   dbc.Row([bars_dev_crime, line_dev_crime]),
                   slider_crime,
                   dcc.Markdown(datatext.split('$')[3], className='textbox'),
                   dbc.Row([bars_dev_solved_crime, line_dev_solved_crime]),
                   slider_solved_crime
                   ],
                  style={'max-width': '2000px', 'margin': 'auto'})


#callbacks to update graphs

@callback(
    Output('line-graph', 'figure'),
    [Input('range-slider-crime', 'value')])

def update_line_yearly_crime(year):
    return line_yearly_crime(year[0],year[1], 'Geregistreerde Misdrijven')


@callback(
    Output("bars-change-graph", 'figure'),
    [Input('range-slider-crime', 'value')])

def update_change_bars(year):
    return bars_crime_change(year[0],year[1],'Geregistreerde Misdrijven')

@callback(
    Output('line-solved-crime', 'figure'),
    [Input('range-slider-solved-crime', 'value')])

def update_line_yearly_crime(year):
    return line_yearly_crime(year[0],year[1], 'Opgehelderde Misdrijven Relatief')


@callback(
    Output("bars-solved-crime", 'figure'),
    [Input('range-slider-solved-crime', 'value')])

def update_change_bars(year):
    return bars_crime_change(year[0],year[1],'Opgehelderde Misdrijven Relatief')