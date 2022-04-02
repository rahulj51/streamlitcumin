import streamlit as st
import pandas as pd
from annotated_text import annotated_text
from st_aggrid import AgGrid



st.title('Project Progress Report')

keys = ["Summary", "Issue key", "Issue Type", "Status", "Custom field (Epic Link)","Assignee","Created"]

in_progress_statuses = ['Requested', 'Backlog', 'Implementing', 'Analyze']
done_statuses = ['Done - In production']

uploaded_file = st.file_uploader("Choose a file")


def split_into_epics_and_tickets(df):
    df1, df2 = df[(mask := df['Issue Type'] == 'Epic')], df[~mask]
    return df1, df2


def summary_status(tickets, epic_status):
    # we shouldn't trust the epic status since no one changes it usually
    # but let's use it as the default
    summary_status = 'Unknown' if epic_status.empty  else epic_status.iloc[0]

    if tickets.size > 0:
        statuses = tickets['Status'].to_list()
        if any(status in statuses for status in in_progress_statuses):
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


def pct_completed(tickets):
    pct_completed = 0
    total_count = tickets.size
    completed_count = tickets[tickets['Status'].isin(done_statuses)].size
    if total_count > 0:
        pct_completed = (completed_count / total_count) * 100

    return round(pct_completed)





if uploaded_file is not None:
    full_df = pd.read_csv(uploaded_file)
    # st.write(full_df)
    # st.subheader("filtered")
    df = full_df[keys]
    # st.write(df)

    # split into epics and tickets
    epics, tickets = split_into_epics_and_tickets(df)
    # st.subheader("Epics")
    # st.write(epics)
    # st.subheader("Tickets")
    # st.write(tickets)

    # now group tickets by epic link
    tickets_by_epic = tickets.groupby('Custom field (Epic Link)')
    epic_keys = tickets_by_epic.groups.keys()

    # for each group, use some logic for completion status
    for epic in epic_keys:
        epic_details = epics.loc[epics['Issue key'] == epic].head(1)
        epic_status = epic_details['Status']
        epic_summary = epic_details['Summary'].iloc[0] if not epic_details.empty else 'Unknown'
        tickets_in_this_epic = tickets_by_epic.get_group(epic)
        status = summary_status(tickets_in_this_epic, epic_status)
        pct = pct_completed(tickets_in_this_epic)
        with st.container():
            annotated_text((f"{status}", "", f"{get_color(status)}"))
            st.markdown(f"Epic - [{epic}](https://jira.taxibeat.com/browse/{epic}) : {epic_summary}")
            st.progress(pct)
            with st.expander("See all tickets"):
                AgGrid(tickets_in_this_epic)

        # use agggrid for better visualization




