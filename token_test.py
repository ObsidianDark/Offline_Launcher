# This is not the method that is used
# Use it while testing only

"""
import time
import minecraft_launcher_lib
import msal

CLIENT_ID = "00000000402b5328"
TENANT = "consumers"
SCOPES = ["XboxLive.signin"]

app = msal.PublicClientApplication(CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT}")

flow = app.initiate_device_flow(scopes=SCOPES)
print(flow)

def device_code_login():
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT}"
    )

    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise Exception("Failed to create device flow")

    print(flow["message"])  # Instructions for the user to authenticate

    result = None
    while not result:
        time.sleep(5)
        result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise Exception(f"Authentication failed: {result.get('error_description', 'Unknown error')}")

    return result["access_token"]

def main():
    print("Starting Microsoft device code login for Minecraft...")
    ms_access_token = device_code_login()

    print("\nMicrosoft login successful!")
    print("Fetching Minecraft tokens...")

    mc_tokens = minecraft_launcher_lib.microsoft_account.get_minecraft_tokens(ms_access_token)

    print("\nMinecraft username:", mc_tokens["name"])
    print("UUID:", mc_tokens["uuid"])
    print("Minecraft Access Token:", mc_tokens["access_token"])

if __name__ == "__main__":
    main()
"""