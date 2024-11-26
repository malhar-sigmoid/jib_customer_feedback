

import streamlit as st
import openai
import pandas as pd
from datetime import datetime

# Load data
openai.api_key = st.secrets["openai_api_key"]

# Sidebar for choosing between options
st.sidebar.title("Customer Feedback Insights")
option = st.sidebar.radio("Choose an option", ["Overall summary", "Choose data slice"])

# Load the data
try:
    file_path = 'Review_Feed_Jack_in_the_Box_Oct.xlsx'
    df = pd.read_excel(file_path)
    df['Review'] = df['Review'].astype('str')
    df['Date'] = pd.to_datetime(df['Date'])
    df_working = df[['St/Prov/Region', 'Date', 'Review']].copy()
except Exception as e:
    st.write(f"Error loading data: {e}")

# Rubrics
rubrics = ["Taste", "Service", "Accuracy of order", "Adherence to restaurant timings"]

def get_user_prompt(combined_feedback):
    user_prompt = f"""
    Customer feedback:
    {combined_feedback}

    Provide the summary in the following format:

    Taste:
    Feedback Summary:
    Percent Comments:
    Actionable Insights:

    Service:
    Feedback Summary:
    Percent Comments:
    Actionable Insights:

    Accuracy of order:
    Feedback Summary:
    Percent Comments:
    Actionable Insights:

    Adherence to restaurant timings:
    Feedback Summary:
    Percent Comments:
    Actionable Insights:

    Specific Food Items:
    Follow-Up Questions:
    """
    return user_prompt


system_prompt = (
f"""
You are a customer experience and operations analyst specializing in quick service restaurants. You are tasked with analyzing customer feedback for Jack in the Box, identifying key pain points, and quantifying the extent to which larger themes are present. You will provide actionable insights that a restaurant manager can implement to improve the customer experience.

You will receive multiple customer comments, each separated by the character: '__end__'.

Based on the comments:
Identify Key Themes: Break down the comments into different rubrics.\n
Quantify: Provide an approximate percentage for how many comments are attributable to each theme.\n
Root Cause Classification: Employee Errors, Technology Issues, Product Quality. Classify feedback based on the root cause of the problem. For example, categorize issues as stemming from human error (e.g., staff training), technical issues (e.g., online ordering problems), or product issues (e.g., food temperature).\n
Actionable Insights: Provide two categories of insights: Minimal Effort Feedback: Quick fixes that can be implemented immediately (e.g., double-checking for missing items, ensuring ingredients are consistent, informing customers about shortages).\n
Specific Food Items: Highlight any specific food items mentioned repeatedly in complaints or prone to errors (e.g., tacos, Ultimate Cheeseburger).\n
Follow-Up Questions: Supply three thought-provoking follow-up questions at the end of your response to clarify ambiguous aspects or explore additional areas.\n

All of the above points must be answered.
Be concise but precise, focusing on actionable insights for restaurant managers. Avoid disclaimers and do not disclose AI identity.

Avoid words like 'numerous', 'many', 'several'. Instead always quantify in terms of percentage. For example, 'x% customers reported order inaccuracies'

For example, a bad response would be:
Customer service experiences varied widely; while some staff members were praised for friendliness and attentiveness, many reviews highlighted rude interactions, long waits for service, and poor communication skills.

The same example can be corrected by quantifying observations:
Customer service experiences varied widely; while 15% comments praised staff members for friendliness and attentiveness, 45% reviews highlighted rude interactions, long waits for service, and poor communication skills.

Avoid accusatory feedback like 'lack of training' or 'poor customer service skills'. Assume that a lot of resources are spent on training; instead point out exact areas of improvements in a non-confrontational way.

Analyze the following customer feedback and provide a summary across the 4 rubrics:
{', '.join(rubrics)}.
"""
)

def get_custom_system_prompt(combined_feedback):
    custom_system_prompt = (
    f"""
    You are a customer experience and operations analyst specializing in quick service restaurants. You are tasked with analyzing customer feedback for Jack in the Box, identifying key pain points, and quantifying the extent to which larger themes are present. You will provide actionable insights that a restaurant manager can implement to improve the customer experience.

    You will receive multiple customer comments, each separated by the character: '__end__'. Here is that data: {combined_feedback}

    You will receive a question from the user. Use the customer data to answer the question.
    """
    )
    return custom_system_prompt



# Main content
st.title("Customer Feedback Insights")

# Initialize session state to store responses
if 'overall_summary' not in st.session_state:
    st.session_state['overall_summary'] = None
if 'custom_response' not in st.session_state:
    st.session_state['custom_response'] = None

if option == "Overall summary":
    st.header("Overall Summary")

    # Display the date range based on service_date
    min_date = df_working['Date'].min().strftime('%Y-%m-%d')
    max_date = df_working['Date'].max().strftime('%Y-%m-%d')
    st.write(f"Time period considered: {min_date} to {max_date}")

    if st.button("Generate"):
        with st.spinner("Generating overall summary..."):
            df_working_truncated = df_working[:2000].copy()
            combined_feedback = "__end__".join(
                (df_working_truncated['Review']).tolist()
            )

            user_prompt = get_user_prompt(combined_feedback)

            reply = openai.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            # Store the response in session state
            st.session_state['overall_summary'] = reply.choices[0].message.content

    # Display the stored summary if available
    if st.session_state['overall_summary']:
        st.markdown(st.session_state['overall_summary'])

        # Display a text box for follow-up questions
        custom_question = st.text_input("Ask a follow-up question:")
        if custom_question:
          df_working_truncated = df_working[:2000].copy()
          combined_feedback = "__end__".join(
                  (df_working_truncated['Review']).tolist()
              )

          custom_prompt = f"Customer feedback question: {custom_question}"
          custom_system_prompt = get_custom_system_prompt(combined_feedback)
          custom_reply = openai.chat.completions.create(
              model='gpt-4o-mini',
              messages=[
                  {"role": "system", "content": custom_system_prompt},
                  {"role": "user", "content": custom_prompt}
              ]
          )
          # Store the custom response in session state
          st.session_state['custom_response'] = custom_reply.choices[0].message.content

        # Display the custom response if available
        if st.session_state['custom_response']:
            st.markdown(st.session_state['custom_response'])

elif option == "Choose data slice":
    st.header("Choose Data Slice")

    # Add "All" option to the months list
    months = ['All'] + df_working['Date'].dt.to_period('M').unique().astype(str).tolist()

    # Select a month
    selected_month = st.selectbox("Choose a month", months)

    # Filter by month if a specific month is selected (not "All")
    if selected_month != 'All':
        df_filtered = df_working[df_working['Date'].dt.to_period('M') == selected_month]
    else:
        df_filtered = df_working.copy()

    # Choose market
    unique_markets = df_filtered['St/Prov/Region'].unique()
    selected_market = st.selectbox("Choose a market", unique_markets)

    # Filter by market
    df_filtered_market = df_filtered[df_filtered['St/Prov/Region'] == selected_market]

    if st.button("Generate"):
        with st.spinner("Generating insights..."):
            combined_feedback_market = "__end__".join(
                (df_filtered_market['Review']).tolist()
            )

            user_prompt = get_user_prompt(combined_feedback_market)

            reply = openai.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Store the response in session state
            st.session_state['overall_summary'] = reply.choices[0].message.content

    # Display the stored summary if available
    if st.session_state['overall_summary']:
        st.markdown(st.session_state['overall_summary'])


        # Display a text box for follow-up questions
        custom_question = st.text_input("Ask a follow-up question:")
        if custom_question:
            combined_feedback_market = "__end__".join(
                (df_filtered_market['Review']).tolist()
            )
            custom_prompt = f"Customer feedback question: {custom_question}"
            custom_system_prompt = get_custom_system_prompt(combined_feedback_market)
            custom_reply = openai.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {"role": "system", "content": custom_system_prompt},
                    {"role": "user", "content": custom_prompt}
                ]
            )
            # Store the custom response in session state
            st.session_state['custom_response'] = custom_reply.choices[0].message.content

        # Display the custom response if available
        if st.session_state['custom_response']:
            st.markdown(st.session_state['custom_response'])





