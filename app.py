import streamlit as st
import pandas as pd
from datetime import date
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.express as px

st.set_page_config(page_title="PRogress", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f5f7fa;
        color: #333333;
    }

    html, body, [class*="css"] {
        font-family: Arial, sans-serif;
    }

    .css-10trblm {
        color: #2c3e50;
    }

    .css-1d391kg {
        background-color: #ecf0f1;
    }
    </style>
    """,
    unsafe_allow_html=True
)

#App title
st.title("PRogress")
st.sidebar.header("Event Selection")

event_map = {
    "100m Dash": "100m",
    "200m Dash": "200m",
    "Long Jump": "LongJump"
}

selected_label = st.sidebar.selectbox(
    "Select the event you want to track",
    options=list(event_map.keys()),
    help="Choose an event to enter results for and view your progress."
)

selected_event = event_map[selected_label]

st.sidebar.subheader("Set your Goal PR")

goal_placeholder = {
     "100m": "e.g., 10.50",
     "200m": "e.g., 21.00",
     "LongJump": "e.g., 7.90"
}

goal_pr = st.sidebar.text_input(
    f"Goal for {selected_label}",
    placeholder=goal_placeholder[selected_event],
    key="goal_pr_input"
)
st.subheader(f"Enter up to 6 results for: {selected_label}")

if "results" not in st.session_state:
    st.session_state["results"] = []

with st.form("input_form"):
    for i in range(6):
        st.markdown(f"### Result #{i+1}")
        col1, col2, col3, col4 = st.columns(4)

        result_date = col1.date_input(
            f"Date #{i+1}",
            value=date.today(),
            key=f"date_{i}"
        )

        mark = col2.text_input(
            f"Mark #{i+1}",
            placeholder="e.g., 10.80 or 7.50",
            key=f"mark_{i}"
        )

        wind = col3.text_input(
            f"Wind #{i+1}",
            placeholder="optional",
            key=f"wind_{i}"
        )

        notes = col4.text_input(
            f"Notes #{i+1}",
            placeholder="optional",
            key=f"notes_{i}"
        )

          
    submitted = st.form_submit_button("Submit Results")
    
    if submitted:

        st.session_state["results"] = [
        {
            "Date": st.session_state[f"date_{i}"],
            "Event": selected_event, 
            "Mark": st.session_state[f"mark_{i}"],
            "Wind": st.session_state[f"wind_{i}"],
            "Notes": st.session_state[f"notes_{i}"]
        }
        for i in range(6)
    ]

        df = pd.DataFrame(st.session_state["results"])
        
        df = df[df["Event"] == selected_event]

        df["Date"] = pd.to_datetime(df["Date"])

        df = df.sort_values("Date")

        st.success(f" Results for: {selected_label}")
        st.dataframe(df, use_container_width=True)

        try:
            goal_value = float(goal_pr)
            show_goal_line = True
        except: 
            goal_value = None
            show_goal_line = False

        st.subheader(f"Progression Chart for {selected_label}")

        if df["Mark"].replace('', np.nan).dropna().shape[0] > 0:

            df_clean = df.copy()
            df_clean = df_clean[df_clean["Mark"] != '']
            df_clean["Mark"] = df_clean["Mark"].astype(float)
            df_clean["Date"] = pd.to_datetime(df_clean["Date"])
            df_clean = df_clean.sort_values("Date")

            fig = px.scatter(df_clean, x="Date", y="Mark",
                             title=f"{selected_label} Performance Over Time",
                             labels={"Mark": "Mark (s or m)"})
            
            if show_goal_line:
                fig.add_hline(
                    y=goal_value,
                    line_dash="dot",
                    line_color="green",
                    annotation_text=f"Goal: {goal_value}",
                    annotation_position="top left"
                )
            
            if selected_event == "LongJump":
                fig.update_yaxes(range=[4.0,9.0])
            elif selected_event == "100m":
                fig.update_yaxes(range=[15.00, 9.50], autorange=False)
            elif selected_event =="200m":
                fig.update_yaxes(range=[30.00, 19.00], autorange=False)

            fig.update_layout(dragmode=False)

            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


            x = np.array(df_clean["Date"].map(pd.Timestamp.toordinal)).reshape(-1,1)
            y = df_clean["Mark"].values
            if len(x) > 1:
                model = LinearRegression().fit(x,y)
                y_pred = model.predict(x)
                df_clean["Trend"] = y_pred

                fig.add_traces(px.line(df_clean, x="Date", y="Trend").data)

            st.plotly_chart(fig, use_container_width=True)

            if show_goal_line:
                if selected_event == "LongJump":
                    best_mark = df_clean["Mark"].max()
                    diff = goal_value - best_mark
                    units = "m"
                    if best_mark >= goal_value:
                        st.success(f"You've already hit your PR. ({abs(diff):.2f}{units} better)")
                    else:
                        st.info(f"You are {diff:.2f}{units} away from your goal.")
                else:
                    best_mark = df_clean["Mark"].min()
                    diff = best_mark - goal_value
                    units = "s"
                    if best_mark <= goal_value:
                        st.success(f"You've already hit your goal. ({abs(diff):.2f}{units} better)")
                    else: st.info(f"You are {diff:.2f}{units} away from your goal.")
