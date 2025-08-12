# import csv
# import random
# import datetime
# import hashlib

# csv_path = '.\\apps\\fraud-detector\\fraud_detection_dataset.csv'
# num_new_records = 500000  # Change this to your desired number

# def random_ip_hash():
#     return 'IPH' + str(random.randint(100, 999))

# def random_device_fp():
#     return 'DFP' + str(random.randint(100, 999))

# def random_provider():
#     return random.choice(['MTN','Telecel','ArtelTigo','GCB','Standbic Bank','MTN','MTN','CBG','ADB Bank','Access Bank'])

# def random_country():
#     return random.choice(['GH', 'US','GB','CA','NG','IN','BR','DE','RU','FR','UA','ZA'])

# def random_network():
#     return random.choice(['WiFi','4G','5G', '3G'])

# def random_transaction_type():
#     return random.choice(['payment','transfer','withdrawal'])

# def generate_row(idx):
#     amount = round(random.expovariate(1/75.8), 2)
#     normalized_amount = min(amount/130664.62, 1.0)
#     transaction_type = random_transaction_type()
#     cross_provider_flag = random.randint(0,1)
#     freq_1m = random.randint(0, 20)
#     freq_10m = random.randint(0, 40)
#     freq_1h = random.randint(0, 80)
#     freq_24h = random.randint(0, 160)
#     total_7d = random.randint(0, 320)
#     time_since_last_tx_hours = round(random.uniform(0.5, 5.0), 1)
#     hour_of_day = random.randint(0, 23)
#     day_of_week = random.randint(0, 6)
#     account_age_days = random.randint(1, 1000)
#     num_linked_wallets = random.randint(1, 5)
#     days_since_pwd_change = random.randint(1, 40)
#     days_since_provider_added = random.randint(1, 200)
#     num_devices = random.randint(1, 5)
#     past_fraud_flag = random.randint(0,1)
#     dispute_ratio = round(random.uniform(0.0, 0.05), 2)
#     avg_success_rate = round(random.uniform(0.80, 0.99), 2)
#     device_fingerprint = random_device_fp()
#     is_new_device = random.randint(0,1)
#     session_duration_seconds = random.randint(60, 2000)
#     failed_login_attempts = random.randint(0, 10)
#     biometric_used = random.randint(0,1)
#     ip_address_hash = random_ip_hash()
#     country = random_country()
#     distance_from_last_loc_km = round(random.uniform(0.1, 500.0), 1)
#     high_risk_region = 1 if country in ['NG','RU','UA'] else 0
#     vpn_flag = random.randint(0,1)
#     network_type = random_network()
#     provider = random_provider()
#     provider_latency_ms = random.randint(50, 2000)
#     provider_downtime_rate = round(random.uniform(0.01, 0.30), 2)
#     fee = round(amount * random.uniform(0.01, 0.05), 2)
#     retries = random.randint(0, 20)
#     amount_to_balance_ratio = round(random.uniform(0.1, 1.0), 2)
#     frequency_change_ratio = round(random.uniform(0.01, 0.30), 2)
#     amount_jump_ratio = round(random.uniform(0.1, 20.0), 2)
#     geo_change_speed_kmph = round(random.uniform(0.1, 200.0), 2)
#     device_change_rate = round(random.uniform(0.01, 0.30), 2)
#     unusual_hour_flag = 1 if hour_of_day in [0,1,2,3,4] else 0
#     unusual_provider_flag = random.randint(0,1)
#     # Heuristic fraud label
#     fraud_score = (
#         int(amount_to_balance_ratio > 0.8) +
#         int(amount > 5000) +
#         int(is_new_device) +
#         int(vpn_flag) +
#         int(high_risk_region) +
#         int(failed_login_attempts > 3) +
#         int(freq_1m > 10) +
#         int(provider_latency_ms > 1500) +
#         int(retries > 10) +
#         int(past_fraud_flag)
#     )
#     label_is_fraud = 1 if fraud_score >= 4 else 0

#     timestamp = (datetime.datetime.now() - datetime.timedelta(days=random.randint(0,30), hours=random.randint(0,23), minutes=random.randint(0,59))).strftime('%Y-%m-%dT%H:%M:%S')
#     transaction_id = f'TX{str(50000+idx).zfill(8)}'
#     user_id = f'U{str(random.randint(1,18302)).zfill(6)}'

#     return [
#         transaction_id, user_id, timestamp, amount, normalized_amount, transaction_type, cross_provider_flag,
#         freq_1m, freq_10m, freq_1h, freq_24h, total_7d, time_since_last_tx_hours, hour_of_day, day_of_week,
#         account_age_days, num_linked_wallets, days_since_pwd_change, days_since_provider_added, num_devices,
#         past_fraud_flag, dispute_ratio, avg_success_rate, device_fingerprint, is_new_device, session_duration_seconds,
#         failed_login_attempts, biometric_used, ip_address_hash, country, distance_from_last_loc_km, high_risk_region,
#         vpn_flag, network_type, provider, provider_latency_ms, provider_downtime_rate, fee, retries,
#         amount_to_balance_ratio, frequency_change_ratio, amount_jump_ratio, geo_change_speed_kmph, device_change_rate,
#         unusual_hour_flag, unusual_provider_flag, label_is_fraud
#     ]
# fraud = 0
# non_fraud = 0

# with open(csv_path, 'a+', newline='') as csvfile:
#     writer = csv.writer(csvfile)

#     for i in range(num_new_records):
#         row_data = generate_row(i)

#         if fraud < 200:
#             if row_data[-1] == 1:
#                 fraud += 1
#             else:
#                 non_fraud += 1

#         writer.writerow(row_data)

# print("Data generation completed")

# print(f'Non-fraud count per 50 fraud counts: {non_fraud}')


"""
Synthetic fraud dataset generator with automatic tuning so fraud <= target_rate
Saves CSV to csv_path. No label-flipping — instead the generator reduces the
probabilities of rare/fraud-triggering signals until the empirical fraud rate
in a small calibration sample falls below the target.

Author: ChatGPT (adapted for SYNCASH)
"""

import csv
import random
import datetime
import os
import math

# === CONFIG ===
csv_path = r'.\apps\fraud-detector\fraud_detection_dataset.csv'  # output file
num_new_records = 500000              # desired total records
TARGET_FRAUD_RATE = 0.02              # desired maximum fraud prevalence (2%)
CALIBRATE_BATCH = 5000                # sample size used to estimate fraud rate during tuning
MAX_TUNE_ITERS = 20                   # maximum tuning iterations
RANDOM_SEED = 42

random.seed(RANDOM_SEED)

# === Adjustable generation parameters (will be tuned) ===
params = {
    "p_new_device": 0.02,         # probability of new device
    "p_vpn": 0.02,                # VPN usage probability
    "p_past_fraud": 0.005,        # fraction of users with past fraud
    "lam_failed_logins": 0.03,    # Poisson lambda for failed logins (mostly zero)
    "lam_freq_1m": 0.02,          # base poisson lam for freq_1m
    "chance_amount_spike": 0.002, # chance of a very large amount spike (>5000)
    "chance_latency_spike": 0.01, # chance of provider latency > 1500 ms
    "chance_retries_high": 0.005  # chance retries > 10
}

# === Helper functions ===
def random_ip_hash():
    return 'IPH' + str(random.randint(100, 999))

def random_device_fp():
    return 'DFP' + str(random.randint(1000, 9999))

def random_provider():
    return random.choice(['MTN','Telecel','AirtelTigo','GCB','Stanbic','CBG','ADB','Access'])

def random_country_weighted():
    # Make high-risk countries rare in selection to reduce high_risk_region frequency
    countries = ['GH']*40 + ['US']*10 + ['GB']*6 + ['CA']*4 + ['NG']*3 + ['IN']*3 + ['BR']*2 + ['DE']*2 + ['FR']*1 + ['RU']*1 + ['UA']*1 + ['ZA']*1
    return random.choice(countries)

def random_network():
    return random.choice(['WiFi','4G','5G','3G'])

def random_transaction_type():
    return random.choice(['payment','transfer','withdrawal'])

# Use an exponential distribution for amounts with a controllable scale
AMOUNT_MEAN = 75.8

def sample_amount():
    # base amount
    val = random.expovariate(1.0 / AMOUNT_MEAN)
    # occasional very large spike (rare); probability controlled by params
    if random.random() < params["chance_amount_spike"]:
        val *= random.uniform(80, 500)   # produces values typically >> 5k
    return round(val, 2)

# Heuristic (same structure as yours)
def compute_fraud_score(features):
    score = 0
    score += 1 if features["amount_to_balance_ratio"] > 0.8 else 0
    score += 1 if features["amount"] > 5000 else 0
    score += 1 if features["is_new_device"] else 0
    score += 1 if features["vpn_flag"] else 0
    score += 1 if features["high_risk_region"] else 0
    score += 1 if features["failed_login_attempts"] > 3 else 0
    score += 1 if features["freq_1m"] > 10 else 0
    score += 1 if features["provider_latency_ms"] > 1500 else 0
    score += 1 if features["retries"] > 10 else 0
    score += 1 if features["past_fraud_flag"] else 0
    return score

# Single-row generator using current params
def generate_row(idx):
    amount = sample_amount()
    normalized_amount = min(amount / 130664.62, 1.0)
    transaction_type = random_transaction_type()
    cross_provider_flag = random.randint(0,1)
    freq_1m = max(0, int(random.poissonvariate(params["lam_freq_1m"]) if hasattr(random, "poissonvariate") else random.randint(0, 3)))
    # fallback simple small integer alternatives if poisson not available:
    if freq_1m == 0:
        freq_1m = random.choices([0,1,2,3], weights=[0.92,0.05,0.02,0.01])[0]
    freq_10m = min(40, random.randint(0, int(freq_1m*5 + 1)))
    freq_1h = min(80, random.randint(0, int(freq_10m*3 + 1)))
    freq_24h = min(160, random.randint(0, int(freq_1h*4 + 1)))
    total_7d = min(320, random.randint(0, int(freq_24h*7 + 1)))
    time_since_last_tx_hours = round(random.uniform(0.2, 72.0), 2)
    hour_of_day = random.randint(0, 23)
    day_of_week = random.randint(0, 6)
    account_age_days = random.randint(1, 3000)
    num_linked_wallets = random.choices([1,2,3,4,5], weights=[0.5,0.25,0.12,0.08,0.05])[0]
    days_since_pwd_change = random.randint(1, 400)
    days_since_provider_added = random.randint(1, 1000)
    num_devices = random.choices([1,2,3,4,5], weights=[0.7,0.18,0.07,0.03,0.02])[0]
    past_fraud_flag = 1 if random.random() < params["p_past_fraud"] else 0
    dispute_ratio = round(random.uniform(0.0, 0.05), 2)
    avg_success_rate = round(random.uniform(0.85, 0.995), 3)
    device_fingerprint = random_device_fp()
    is_new_device = 1 if random.random() < params["p_new_device"] else 0
    session_duration_seconds = random.randint(10, 3600)
    # failed login attempts follow a mostly-zero heavy-tailed distribution
    failed_login_attempts = 0
    if random.random() < params["lam_failed_logins"]:
        failed_login_attempts = random.randint(1, 8)
    biometric_used = 1 if random.random() < 0.15 else 0
    ip_address_hash = random_ip_hash()
    country = random_country_weighted()
    distance_from_last_loc_km = round(random.uniform(0.0, 500.0), 1)
    high_risk_region = 1 if country in ['RU', 'CN', 'BR', 'UA'] else 0
    vpn_flag = 1 if random.random() < params["p_vpn"] else 0
    network_type = random_network()
    provider = random_provider()
    # provider_latency heavy-tailed: low baseline, small chance of big spike
    provider_latency_ms = int(random.uniform(50, 250))
    if random.random() < params["chance_latency_spike"]:
        provider_latency_ms = int(random.uniform(1500, 4000))
    provider_downtime_rate = round(random.uniform(0.0, 0.12), 3)
    fee = round(amount * random.uniform(0.005, 0.04), 2)
    # retries mostly 0, small chance high
    retries = 0
    if random.random() < 0.02:
        retries = random.randint(1, 6)
    if random.random() < params["chance_retries_high"]:
        retries = random.randint(11, 25)
    amount_to_balance_ratio = round(min(1.2, random.lognormvariate(math.log(0.2+1e-6), 1.2)), 3)
    frequency_change_ratio = round(random.uniform(0.001, 1.0), 3)
    amount_jump_ratio = round(max(0.01, amount / max(1.0, random.expovariate(1/50.0))), 3)
    geo_change_speed_kmph = round(random.uniform(0.0, 600.0), 2)
    device_change_rate = round(random.uniform(0.0, 0.5), 3)
    unusual_hour_flag = 1 if hour_of_day in [0,1,2,3,4] else 0
    unusual_provider_flag = 1 if random.random() < 0.01 else 0

    features = {
        "amount": amount,
        "amount_to_balance_ratio": amount_to_balance_ratio,
        "is_new_device": is_new_device,
        "vpn_flag": vpn_flag,
        "high_risk_region": high_risk_region,
        "failed_login_attempts": failed_login_attempts,
        "freq_1m": freq_1m,
        "provider_latency_ms": provider_latency_ms,
        "retries": retries,
        "past_fraud_flag": past_fraud_flag
    }

    fraud_score = compute_fraud_score(features)
    # Keep threshold conservative; tuning loop may increase if necessary
    label_is_fraud = 1 if fraud_score >= 4 else 0

    timestamp = (datetime.datetime.now() - datetime.timedelta(days=random.randint(0,30),
                                                              hours=random.randint(0,23),
                                                              minutes=random.randint(0,59))).strftime('%Y-%m-%dT%H:%M:%S')
    transaction_id = f'TX{str(50000+idx).zfill(8)}'
    user_id = f'U{str(random.randint(1,18302)).zfill(6)}'

    row = [
        transaction_id, user_id, timestamp, amount, normalized_amount, transaction_type, cross_provider_flag,
        freq_1m, freq_10m, freq_1h, freq_24h, total_7d, time_since_last_tx_hours, hour_of_day, day_of_week,
        account_age_days, num_linked_wallets, days_since_pwd_change, days_since_provider_added, num_devices,
        past_fraud_flag, dispute_ratio, avg_success_rate, device_fingerprint, is_new_device, session_duration_seconds,
        failed_login_attempts, biometric_used, ip_address_hash, country, distance_from_last_loc_km, high_risk_region,
        vpn_flag, network_type, provider, provider_latency_ms, provider_downtime_rate, fee, retries,
        amount_to_balance_ratio, frequency_change_ratio, amount_jump_ratio, geo_change_speed_kmph, device_change_rate,
        unusual_hour_flag, unusual_provider_flag, label_is_fraud
    ]
    return row, label_is_fraud

# === TUNING LOOP ===
def estimate_fraud_rate_sample(sample_size):
    frauds = 0
    for i in range(sample_size):
        _, label = generate_row(i)
        if label == 1:
            frauds += 1
    return frauds / sample_size, frauds

# iterative attenuation parameters
attenuation_factor = 0.6   # multiply probabilities by this factor when reducing
min_probs = {
    "p_new_device": 0.001,
    "p_vpn": 0.001,
    "p_past_fraud": 0.0005,
    "lam_failed_logins": 0.001,
    "chance_amount_spike": 1e-5,
    "chance_latency_spike": 1e-4,
    "chance_retries_high": 1e-4
}

print("Starting tuning to meet target fraud rate:", TARGET_FRAUD_RATE)
# calibrate
for it in range(MAX_TUNE_ITERS):
    rate, n_f = estimate_fraud_rate_sample(CALIBRATE_BATCH)
    print(f"Iteration {it+1}: sample fraud rate = {rate:.4%} ({n_f}/{CALIBRATE_BATCH})")
    if rate <= TARGET_FRAUD_RATE:
        print("Target achieved. Proceeding to full dataset generation.")
        break
    # Attenuate the parameters that produce fraud signals
    # We reduce probabilities multiplicatively, respecting minimum floors
    for key in ["p_new_device", "p_vpn", "p_past_fraud", "lam_failed_logins",
                "chance_amount_spike", "chance_latency_spike", "chance_retries_high"]:
        new_val = max(min_probs[key], params[key] * attenuation_factor)
        params[key] = new_val
    # Also as a fallback, we could raise the fraud threshold to make fraud rarer:
    # but prefer reducing rare-signal probabilities first (preserves heuristic semantics)
else:
    print("Warning: reached max tuning iterations; final sample rate:", rate)

# === WRITE CSV ===
os.makedirs(os.path.dirname(csv_path), exist_ok=True)
header = [
    'transaction_id','user_id','timestamp','amount','normalized_amount','transaction_type','cross_provider_flag',
    'freq_1m','freq_10m','freq_1h','freq_24h','total_7d','time_since_last_tx_hours','hour_of_day','day_of_week',
    'account_age_days','num_linked_wallets','days_since_pwd_change','days_since_provider_added','num_devices',
    'past_fraud_flag','dispute_ratio','avg_success_rate','device_fingerprint','is_new_device','session_duration_seconds',
    'failed_login_attempts','biometric_used','ip_address_hash','country','distance_from_last_loc_km','high_risk_region',
    'vpn_flag','network_type','provider','provider_latency_ms','provider_downtime_rate','fee','retries',
    'amount_to_balance_ratio','frequency_change_ratio','amount_jump_ratio','geo_change_speed_kmph','device_change_rate',
    'unusual_hour_flag','unusual_provider_flag','label_is_fraud'
]

write_header = not os.path.exists(csv_path)

fraud_count = 0
non_fraud_count = 0

with open(csv_path, 'a+', newline='') as csvfile:
    writer = csv.writer(csvfile)
    if write_header:
        writer.writerow(header)
    for i in range(num_new_records):
        row, label = generate_row(i)
        writer.writerow(row)
        if label == 1:
            fraud_count += 1
        else:
            non_fraud_count += 1
        if (i+1) % 50000 == 0:
            print(f"Wrote {i+1} rows... (so far) fraud_count={fraud_count}")

total_written = fraud_count + non_fraud_count
achieved_rate = fraud_count / total_written if total_written > 0 else 0.0

print("Generation complete.")
print(f"Total rows written: {total_written}")
print(f"Fraud count: {fraud_count}, Non-fraud count: {non_fraud_count}")
print(f"Achieved fraud rate: {achieved_rate:.4%} (target: {TARGET_FRAUD_RATE*100:.2f}%)")
print("Final generation parameters:", params)
