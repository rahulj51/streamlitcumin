import base64
import datetime
import io
import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import pandas as pd
import justjira
import styler
import dash_bootstrap_components as dbc



epics_df = None
tickets_df = None

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)


app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            dbc.Button('Select Files')
        ]),
        style= styler.upload_box_style,
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-data-upload'),
])


@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    """
    Callback to parse the uploaded file
    :param list_of_contents:
    :param list_of_names:
    :param list_of_dates:
    :return:
    """
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


def parse_contents(contents, filename, date):
    global epics_df, tickets_df
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            full_df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            full_df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    # take the raw df and process it
    epics_df, tickets_df = justjira.summarize(full_df)
    epics_df['pct_completed'] = epics_df['pct_completed'].apply(lambda pct: styler.progress_bar(pct))
    epics_df['epic_url'] = epics_df.apply(lambda x: f"[{x.epic_id}]({x.epic_url})", axis=1)

    epics_table_df = epics_data(epics_df)

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            id='table',
            data=epics_table_df.to_dict('records'),
            style_cell={
                'textAlign': 'left',
                'font-size': '15px',
                'font-family': 'Helvetica, Arial, sans-serif'

            },
            style_header={
                'backgroundColor': 'light-grey',
                'fontWeight': 'bold',
                'font-size': '15px',
                'font-family': 'Helvetica, Arial, sans-serif'

            },
            columns=[
                {"name": col, "id": col, "presentation": "markdown"}
                if col in ["pct_completed", 'epic_url']
                else
                {'name': col, 'id': col}
                for col in epics_table_df.columns
            ],
            sort_action="native",
            filter_action='native',
            markdown_options= {"html": True}
        ),
        dbc.Modal(
            [
                dbc.ModalHeader("Tickets in Epic", id="modal-header"),

                # dbc.ModalBody("This is the content of the modal"),
                dbc.ModalBody(dash_table.DataTable(
                    id='table2',
                    data=dict(),
                    style_cell={
                        'textAlign': 'left',
                        'font-size': '15px',
                        'font-family': 'Helvetica, Arial, sans-serif'

                    },
                    style_header={
                        'backgroundColor': 'light-grey',
                        'fontWeight': 'bold',
                        'font-size': '15px',
                        'font-family': 'Helvetica, Arial, sans-serif'

                    },
                    columns=[
                        {'name': col, 'id': col}
                        for col in tickets_df.columns
                    ],
                    markdown_options={"html": True}
                )),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ml-auto")
                ),
            ],
            id="modal",
            scrollable=True,
            size="xl",
        )

    ])


def epics_data(epics_df):
    return epics_df.drop("epic_id", axis=1)



@app.callback([Output('modal', 'is_open'),
               Output('table2', 'data'), Output('modal-header', 'children')],
              [Input('table', 'active_cell'),
               Input('close', 'n_clicks')],
              [State("modal", "is_open")])
def toggle_modal(active_cell, close, is_open):
    data = None
    epic_id = None
    title = "Stories in epic {}"

    if active_cell:
        row_id = active_cell['row']
        epic_id = epics_df.iloc[row_id]['epic_id']
        tickets_in_this_epic = tickets_df.query(f'`Custom field (Epic Link)` == "{epic_id}"')
        data = tickets_in_this_epic.to_dict("records")

    if active_cell or close:
        return (not is_open), data, title.format(epic_id)

    return is_open, data, title.format(epic_id)


if __name__ == '__main__':
    app.run_server(debug=True)
