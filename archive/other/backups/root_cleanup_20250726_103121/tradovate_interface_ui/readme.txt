https://chatgpt.com/c/67215d27-5a0c-8007-a0bd-6ff4ddcee6d5

pip freeze > requirements.txt

cd /Users/Mike/trading/tradingview_webhook
git add .
git commit -m "Updated confirmation logic"
git push heroku main



# Step 1: Get the Access Token
ACCESS_TOKEN=$(curl -s -X POST "https://demo.tradovateapi.com/v1/auth/accesstokenrequest" \
-H "Content-Type: application/json" \
-d '{
    "name": "stonkz92224",
    "password": "24$tonkZ24!",
    "appId": "Test 1",
    "appVersion": "0.0.1",
    "deviceId": "96c41e70-74e5-6bb7-2057-3cd280ece582",
    "cid": "4398",
    "sec": "aadd1caa-ff30-4712-bc4e-1fca4c2ecad9"
}' | jq -r '.accessToken')

# Step 2: Fetch Account List using the Access Token
curl -X GET "https://demo.tradovateapi.com/v1/account/list" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json"
