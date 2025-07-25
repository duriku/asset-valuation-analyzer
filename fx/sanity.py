# fx/sanity.py
def fx_sanity_check(data, fx_expected_ranges):
    print("\n=== FX Rate Sanity Check (last close) ===")
    for fx, rng in fx_expected_ranges.items():
        try:
            val = data[fx]['Close'].dropna()[-1]
            print(f"{fx}: {val}")
            if not (rng[0] < val < rng[1]):
                print(f"⚠️  Warning: {fx} out of expected range {rng}")
        except Exception as e:
            print(f"Could not check {fx}: {e}")
