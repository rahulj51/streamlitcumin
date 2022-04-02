import streamlit as st
import pandas as pd
import duckdb
from annotated_text import annotated_text
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

st.set_page_config(layout='wide')
st.title('Project Progress Report')

keys = ["Summary", "Issue key", "Issue Type", "Status", "Custom field (Epic Link)","Assignee","Created"]

in_progress_statuses = ['Requested', 'Backlog', 'Implementing', 'Analyze']
done_statuses = ['Done - In production']

uploaded_file = st.file_uploader("Choose a file")


def split_into_epics_and_tickets(alldata):
    epics = alldata.filter('"Issue Type" = \'Epic\'')
    tickets = alldata.filter('"Issue Type" != \'Epic\'')
    return epics, tickets


def summary_status(ticket_statuses, epic_status):
    # we shouldn't trust the epic status since no one changes it usually
    # but let's use it as the default
    summary_status = epic_status or 'Unknown'

    if len(ticket_statuses) > 0:
        if any(x in ticket_statuses for x in in_progress_statuses):
            summary_status = 'In Progress'
        else:
            summary_status = 'Completed'

    return summary_status

def get_color(status):
    color = "#afa"
    if status == 'In Progress':
        color = "#fea"
    elif status == "Unknown":
        color = "#faa"
    return color


def pct_completed(ticket_statuses):
    pct_completed = 0
    total_count = len(ticket_statuses)
    completed_count = len([x for x in ticket_statuses if x in done_statuses])
    if total_count > 0:
        pct_completed = (completed_count / total_count) * 100

    return round(pct_completed)


if uploaded_file is not None:
    full_df = pd.read_csv(uploaded_file)
    df = full_df[keys]
    conn = duckdb.connect()
    conn.execute("CREATE TABLE epic_statuses (epic_id String, epic_url String, status String, pct_completed Integer)")
    epic_statuses = conn.table("epic_statuses")

    alldata = conn.from_df(df)

    # split into epics and tickets
    epics, tickets = split_into_epics_and_tickets(alldata)
    # st.subheader("Epics")
    # st.write(epics.df())
    # st.subheader("Tickets")
    # st.write(tickets.df())

    # iterate over each epic
    epic_links = [ x[0] for x in epics.project('"Issue key"').order('"Issue key"').fetchall()]
    for epic in epic_links:
        epic_details = epics.filter('"Issue key" = \'{}\''.format(epic)).fetchall()[0]
        epic_summary = epic_details[0]
        epic_status = epic_details[3]

        tickets_in_this_epic = tickets.filter('"Custom field (Epic Link)" = \'{}\''.format(epic))
        ticket_statuses = [x[0] for x in tickets_in_this_epic.project('Status').fetchall()]
        status = summary_status(ticket_statuses, epic_status)
        pct = pct_completed(ticket_statuses)

        # add this into into the statuses table
        epic_url = f"https://jira.taxibeat.com/browse/{epic}"
        conn.execute("Insert into epic_statuses values (?,?,?,?)", [epic, epic_url, status, pct] )

    # now build a new table that joins the epics and tickets and adds the other stuff
    epics = epics.set_alias('a').join(epic_statuses.set_alias('b'), 'a."Issue key" = b.epic_id')
    epics_df = epics.project('epic_id, epic_url, Summary, b.status as status, pct_completed').to_df()

    builder = GridOptionsBuilder.from_dataframe(epics_df)
    http_renderer = '''
    function(params) {return '<a href="' + params.value + '">' + params.value + '</a>'}
    '''
    builder.configure_column("epic_url", header_name="Epic URL", initialWidth=200, cellRenderer=JsCode(http_renderer))
    go = builder.build()

    grid_return = AgGrid(epics_df, go, allow_unsafe_jscode=True)
    # new_df = grid_return["data"]
    #
    # # st.write(new_df)

    # with st.container():
    #
    #     annotated_text((f"{status}", "", f"{get_color(status)}"))
    #     st.markdown(f"Epic - [{epic}](https://jira.taxibeat.com/browse/{epic}) : {epic_summary}")
    #     st.progress(pct)
    #     with st.expander("See all tickets"):
    #         AgGrid(tickets_in_this_epic.to_df(), key=epic)





