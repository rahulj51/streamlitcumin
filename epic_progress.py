import streamlit as st
import pandas as pd
import duckdb
from annotated_text import annotated_text
from st_aggrid import AgGrid



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

        with st.container():
            annotated_text((f"{status}", "", f"{get_color(status)}"))
            st.markdown(f"Epic - [{epic}](https://jira.taxibeat.com/browse/{epic}) : {epic_summary}")
            st.progress(pct)
            with st.expander("See all tickets"):
                AgGrid(tickets_in_this_epic.to_df(), key=epic)





