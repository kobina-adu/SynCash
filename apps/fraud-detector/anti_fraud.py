import streamlit as st
import pandas as pd
import joblib

model = joblib.load('anti_fraud_model_pipeline.pkl')

st.title("Fraud Detection")

st.markdown('Please enter the transaction details and use the prediction button')

st.divider()

transaction_type = st.selectbox("Transaction Type:", ['PAYMENT', "TRANSFER", 'CASH_OUT', 'DEBIT'])
amount = st.number_input("Amount:", min_value=0.0, value=1000.0)
oldbalanceOrig = st.number_input("Sender's old balance:", min_value=0.0, value=10000.0)
newbalanceOrig = st.number_input("Sender's new balance :", min_value=0.0, value=9000.0)
oldbalanceDest = st.number_input("Reciever's old balance:", min_value=0.0, value=0.0)
newbalanceDest = st.number_input("Reciever's new balance:", min_value=0.0, value=1000.0)


if st.button("Predict"):
    input_data = pd.DataFrame([{
        'type': transaction_type,
        'amount': amount,
        'oldbalanceOrg': oldbalanceOrig,
        'newbalanceOrig': newbalanceOrig,
        'oldbalanceDest': oldbalanceDest,
        'newbalanceDest': newbalanceDest
    }])


prediction = model.predict(input_data)
print(prediction)
st.subheader(f'Fraud Detected: {bool(prediction[0])}')

if prediction == 1:
    st.error("Fraud Alert! Proceed with caution or terminate transaction.")
else:
    st.success("No fraudulent activity detected!")
