import urllib.request, json

# Test /datasets
r = urllib.request.urlopen('http://localhost:8000/datasets')
d = json.loads(r.read())
print("=== /datasets ===")
for ds in d['datasets']:
    print(f"  {ds['name']}: {ds['full_name']} | {ds['years_covered']} | {ds['frequency']}")
print(f"\nTotal datasets: {len(d['datasets'])}")
print(f"Disclaimer present: {'yes' if d.get('disclaimer') else 'no'}")

# Test a single dataset
r2 = urllib.request.urlopen('http://localhost:8000/datasets/plfs')
plfs = json.loads(r2.read())
print(f"\n=== /datasets/plfs ===")
print(f"  Records: {len(plfs['data'])}")
print(f"  Sample: {plfs['data'][0]}")

print("\nAll endpoint tests passed!")
