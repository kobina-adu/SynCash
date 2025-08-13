import joblib
import pandas as pd

# Loading the trained model here
model = joblib.load(".\\apps\\fraud-detector\\anti_fraud_model_pipeline.pkl")

# Data from the database
transaction_type = 'PAYMENT'
amount = 2000
sender_old_balance = 2500
sender_new_balance = 500
reciever_old_balance = 5000
reciever_new_balance = 9000

# Constructing the dataframe
data = pd.DataFrame([{
    'type': transaction_type,
    'amount': amount,
    'oldbalanceOrg': sender_old_balance,
    'newbalanceOrig': sender_new_balance,
    'oldbalanceDest': reciever_old_balance,
    'newbalanceDest': reciever_new_balance
}])

# Making prediction
prediction = model.predict(data)

# Displaying results
print(prediction)