"""Constants extracted from mautrix-gvoice for Google Voice API integration"""

# User agents and client details
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
CH_USER_AGENT = '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"'
CH_PLATFORM = '"Linux"'
CLIENT_VERSION = "665865172"
JAVASCRIPT_USER_AGENT = "google-api-javascript-client/1.1.0"
WAA_X_USER_AGENT = "grpc-web-javascript/0.1"

# API Keys
API_KEY = "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg"
UPLOAD_OPI = "111538494"
WAA_API_KEY = "AIzaSyBGb5fGAyC-pRcRU6MUHb__b_vKha71HRE"
WAA_REQUEST_KEY = "/JR8jsAkqotcKsEKhXic"

# Domains
ORIGIN = "https://voice.google.com"
API_DOMAIN = "clients6.google.com"
REALTIME_DOMAIN = f"signaler-pa.{API_DOMAIN}"
CONTACTS_DOMAIN = f"peoplestack-pa.{API_DOMAIN}"
UPLOAD_DOMAIN = "docs.google.com"
WAA_DOMAIN = f"waa-pa.{API_DOMAIN}"

# API Endpoints
API_BASE_URL = f"https://{API_DOMAIN}/voice/v1/voiceclient"
ENDPOINTS = {
    "get_account": f"{API_BASE_URL}/account/get",
    "get_thread": f"{API_BASE_URL}/api2thread/get",
    "list_threads": f"{API_BASE_URL}/api2thread/list",
    "send_sms": f"{API_BASE_URL}/api2thread/sendsms",
    "update_attributes": f"{API_BASE_URL}/thread/updateattributes",
    "delete_thread": f"{API_BASE_URL}/thread/delete",
    "mark_all_read": f"{API_BASE_URL}/thread/markallread",
}

# Realtime endpoints
REALTIME_BASE_URL = f"https://{REALTIME_DOMAIN}"
REALTIME_ENDPOINTS = {
    "channel": f"{REALTIME_BASE_URL}/punctual/multi-watch/channel",
    "choose_server": f"{REALTIME_BASE_URL}/punctual/v1/chooseServer",
}

# Contacts endpoints
CONTACTS_BASE_URL = f"https://{CONTACTS_DOMAIN}/$rpc/peoplestack.PeopleStackAutocompleteService"
CONTACTS_ENDPOINTS = {
    "autocomplete": f"{CONTACTS_BASE_URL}/Autocomplete",
    "lookup": f"{CONTACTS_BASE_URL}/Lookup",
}

# WAA endpoints
WAA_BASE_URL = f"https://{WAA_DOMAIN}/$rpc/google.internal.waa.v1.Waa"
WAA_ENDPOINTS = {
    "create": f"{WAA_BASE_URL}/Create",
    "ping": f"{WAA_BASE_URL}/Ping",
}

# Upload/Download
UPLOAD_URL = f"https://{UPLOAD_DOMAIN}/upload/photos/resumable"
DOWNLOAD_URL_TEMPLATE = "https://voice.google.com/u/{auth_user}/a/i/{media_id}"

# Content types
CONTENT_TYPE_PROTOBUF = "application/x-protobuf"
CONTENT_TYPE_PBLITE = "application/json+protobuf"
CONTENT_TYPE_FORM_DATA = "application/x-www-form-urlencoded"
CONTENT_TYPE_PLAIN_TEXT = "text/plain"

# Client details for API requests
CLIENT_DETAILS = {
    "appVersion": "5.0 (X11)",
    "platform": "Linux x86_64",
    "userAgent": USER_AGENT,
}