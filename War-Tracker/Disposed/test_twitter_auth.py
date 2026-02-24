import requests
import json
import time

# Load accounts
try:
    with open("twitter_accounts.json", "r") as f:
        ACCOUNTS = json.load(f)
except FileNotFoundError:
    print("Error: twitter_accounts.json not found.")
    exit(1)

# GraphQL Endpoint for SearchTimeline
# Note: The queryId 'nK1dw4oV3k4w5TdtcAdSww' might rotate. 
# If this fails with specific error, we might need to update it.
SEARCH_URL = "https://twitter.com/i/api/graphql/nK1dw4oV3k4w5TdtcAdSww/SearchTimeline"

def get_headers(account):
    return {
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "x-csrf-token": account["ct0"], # CRITICAL: Must match ct0 cookie
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
        "x-twitter-active-user": "yes",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": f"auth_token={account['auth_token']}; ct0={account['ct0']}"
    }

def test_account(account):
    print(f"Testing account: {account['username']}...")
    headers = get_headers(account)
    
    params = {
        "variables": json.dumps({
            "rawQuery": "Syria",
            "count": 1,
            "querySource": "typed_query",
            "product": "Top"
        }),
        "features": json.dumps({
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_media_download_video_enabled": False,
            "responsive_web_enhance_cards_enabled": False
        })
    }

    try:
        response = requests.get(SEARCH_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            print(f"  [SUCCESS] Auth valid. Status 200.")
            try:
                data = response.json()
                # Check for standard errors Twitter wraps in 200
                errors = data.get("errors", [])
                if errors:
                    print(f"  [WARNING] 200 OK but API returned errors: {errors[0].get('message')}")
                    return False
                print(f"  [SUCCESS] JSON parsed. Connection viable.")
                return True
            except:
                print("  [WARNING] 200 OK but failed to parse JSON.")
        elif response.status_code == 401:
            print(f"  [FAILED] 401 Unauthorized. Session likely expired.")
        elif response.status_code == 403:
             print(f"  [FAILED] 403 Forbidden. CSRF mismatch or WAF block.")
        elif response.status_code == 429:
             print(f"  [FAILED] 429 Rate Limit.")
        else:
            print(f"  [FAILED] Status: {response.status_code} - {response.text[:100]}")
            
    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}")

    return False

# Run tests
working_count = 0
for acc in ACCOUNTS:
    if test_account(acc):
        working_count += 1
    time.sleep(1)

print(f"\nSummary: {working_count}/{len(ACCOUNTS)} accounts working.")
