import requests
import random
import time
from statistics import mean

BASE_URL = "https://mealbot-85zc.onrender.com/meal-plan"

TOTAL_TESTS = 100
VALID_RATIO = 0.8
TIMEOUT_SECONDS = 10

results = {
    "success_200": 0,
    "validation_422": 0,
    "server_500": 0,
    "other_http_errors": 0,
    "connection_errors": 0,
    "response_times": []
}


def generate_valid_payload():
    return {
        "name": f"User_{random.randint(1, 100000)}",
        "age": random.randint(18, 60),
        "weight": random.randint(50, 100),
        "height": random.randint(150, 190),
        "diet_type": random.choice(["veg", "non_veg"]),
        "goal": random.choice(["weight_loss", "muscle_gain", "maintenance"]),
        "allergies": random.choice([[], ["nuts"], ["milk"]]),
        "phone_number": f"9{random.randint(100000000, 999999999)}",
        "preferences": random.choice(["south_indian", "high_protein", "balanced"])
    }


def generate_invalid_payload():
    return {
        "name": "",
        "age": -5,
        "weight": 0,
        "height": 0,
        "diet_type": "alien_food",
        "goal": "become_superhuman",
        "allergies": "not_a_list",
        "phone_number": "abc123",
        "preferences": None
    }


def run_test(payload):
    try:
        start = time.time()
        response = requests.post(
            BASE_URL,
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        duration = time.time() - start

        results["response_times"].append(duration)

        status = response.status_code

        if status == 200:
            results["success_200"] += 1
        elif status == 422:
            results["validation_422"] += 1
        elif status >= 500:
            results["server_500"] += 1
        else:
            results["other_http_errors"] += 1

    except requests.exceptions.RequestException as e:
        results["connection_errors"] += 1
        print("Connection error:", e)


print("Running tests...\n")

for i in range(TOTAL_TESTS):
    if random.random() < VALID_RATIO:
        payload = generate_valid_payload()
    else:
        payload = generate_invalid_payload()

    run_test(payload)
    time.sleep(0.05)


print("\n===== TEST SUMMARY =====")
print(f"Total tests: {TOTAL_TESTS}")
print(f"200 Success: {results['success_200']}")
print(f"422 Validation: {results['validation_422']}")
print(f"500 Server Errors: {results['server_500']}")
print(f"Other HTTP Errors: {results['other_http_errors']}")
print(f"Connection Errors: {results['connection_errors']}")

if results["response_times"]:
    print(f"Average response time: {mean(results['response_times']):.4f} sec")
    print(f"Max response time: {max(results['response_times']):.4f} sec")
