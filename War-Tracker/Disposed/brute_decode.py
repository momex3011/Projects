
import base64
import re
import sys

url = "https://news.google.com/rss/articles/CBMiiwFBVV95cUxOWVVNOW9oUUNXNWJyLVg4MXhLRGwtRW1jMzVMSkFQdEEwS2hmZU04aE5raGN2Z0RnY18zNzh3SlFXeU5EcHFHcXduUlNBMmFlc0dsUjh1QUVWY1lqYnU3V1NMMFhmZVNJN0ozWE1tSXkyekptemZhRVdEdFdWWHdNSVJudWNCb3pBS2ZB0gGQAUFVX3lxTE05clp2aVgxZXRoNjdtZ0lxRkp5M3lsa2NsZjhRSjRBQUlORVhhMzMzZTBiV2RwbnhKTWVHT0NJTGNNZ3RkdW9WWlNBSlA3MVp4TDFXNWZUT3IyY3M4eElPckFyMHFiUjRETmNFMXNCbTlJbV93N1Z2bDhaenoyZmE0OHowdkx5NEh0bDh4NVVhQw?oc=5"
match = re.search(r'articles/([^?]+)', url)
if not match:
    print("No B64 found")
    sys.exit()

b64 = match.group(1)
print(f"B64 Length: {len(b64)}")

def try_decode(s):
    # Try all paddings
    for i in range(4):
        padded = s + '=' * i
        try:
            d = base64.urlsafe_b64decode(padded)
            return d
        except:
            pass
    return None

decoded = try_decode(b64)
if decoded:
    print("Success decoding!")
    # Look for http
    import string
    printable = set(string.printable.encode('ascii'))
    
    # Hex dump
    print("--- HEX DUMP ---")
    # print in chunks of 16
    for i in range(0, len(decoded), 16):
        chunk = decoded[i:i+16]
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        ascii_str = ''.join(chr(b) if chr(b) in string.printable and b >= 32 else '.' for b in chunk)
        print(f"{i:04x}: {hex_str:<48} | {ascii_str}")
        
    print("\n--- STRING SEARCH ---")
    # Search for anything that looks like a domain or path
    # Look for .com, .org, or /
    text = decoded.decode('latin1')
    match = re.search(r'[a-zA-Z0-9-]+\.(com|org|net|io|co|uk|us|sy)[^\x00-\x1f\s]*', text)
    if match:
        print(f"Possible Domain match: {match.group(0)}")
else:
    print("Failed to decode")
