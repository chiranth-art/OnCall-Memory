import streamlit as st
from agent import respond_to_incident

# Page configuration
st.set_page_config(
    page_title="Incident Response Agent",
    page_icon="🚨",
    layout="wide"
)

# Page heading
st.title("🚨 Incident Response Agent")

st.write(
    "An AI-powered assistant that helps engineers investigate "
    "production incidents using historical incident records."
)

st.divider()

# Incident input
st.subheader("Describe the Incident")

error_text = st.text_area(
    "Enter the error or incident details:",
    placeholder="Example: Database connection timeout in payment-service. Customer orders are failing.",
    height=150
)

# Analyse button
if st.button("🔍 Analyse Incident", type="primary"):

    if not error_text.strip():
        st.warning("Please enter an incident description.")

    else:
        with st.spinner("Investigating incident... Please wait."):

            try:
                result = respond_to_incident(error_text)

                st.success("Incident analysis completed!")

                st.subheader("📋 Investigation Report")
                st.markdown(result)

            except Exception as e:
                st.error("Something went wrong while analysing the incident.")
                st.exception(e)

st.divider()

st.caption("Incident Response Agent | Hack With Bangalore 4.0")