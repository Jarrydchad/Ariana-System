import requests
import json

def clean_data():
  r = requests.get('https://coderbyte.com/api/challenges/json/json-cleaning')
  return r.json()


def clean(obj):
  if isinstance(obj, dict):
      return {key: clean(value) for key, value in obj.items() if value not in ("N/A", "-", "")}
  elif isinstance(obj, list):
      return [clean(item) for item in obj if item not in ("N/A", "-", "")]
  else:
      return obj

cleaned_data = clean(clean_data())
# return json.dumps(cleaned_data)

print(clean_data())