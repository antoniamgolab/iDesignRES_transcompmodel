"""
Explain intangible costs - what does VoT * travel_time * flow actually mean?
"""

# Parameters from model
VoT = 30  # EUR/hour - Value of Time for freight

# Example calculation for a single route
route_length_km = 1000  # km (e.g., Munich to Rome)
speed_kmh = 60          # km/h average truck speed
waiting_time_h = 2      # hours (loading/unloading)

travel_time_h = route_length_km / speed_kmh + waiting_time_h
print("=" * 70)
print("INTANGIBLE COST CALCULATION EXAMPLE")
print("=" * 70)

print(f"\nExample route: {route_length_km} km at {speed_kmh} km/h")
print(f"  Travel time: {route_length_km/speed_kmh:.1f} hours driving")
print(f"  Waiting time: {waiting_time_h} hours")
print(f"  Total time: {travel_time_h:.1f} hours")

intangible_per_tonne = VoT * travel_time_h
print(f"\nIntangible cost = VoT x time = {VoT} EUR/h x {travel_time_h:.1f} h")
print(f"                = {intangible_per_tonne:.0f} EUR per tonne transported")

# Now scale up to system level
print("\n" + "=" * 70)
print("SCALING TO SYSTEM LEVEL")
print("=" * 70)

# From the model results, total objective is ~362B EUR
# Intangible portion is ~305B EUR
intangible_total = 305e9  # EUR

# Back-calculate implied tonne-hours
implied_tonne_hours = intangible_total / VoT
print(f"\nTotal intangible costs: {intangible_total/1e9:.0f} billion EUR")
print(f"At VoT = {VoT} EUR/hour, this implies:")
print(f"  {implied_tonne_hours/1e9:.1f} billion tonne-hours of freight in transit")

# What does this mean in practical terms?
avg_travel_time = 20  # hours (rough average for long-haul)
implied_tonnes = implied_tonne_hours / avg_travel_time
time_step = 4  # years
years = 11  # modeled years

total_tonnes_over_horizon = implied_tonnes
annual_tonnes = total_tonnes_over_horizon / (years * time_step)

print(f"\nAssuming average {avg_travel_time} hours per shipment:")
print(f"  Total freight: {implied_tonnes/1e6:.0f} million tonnes over model horizon")
print(f"  Annual freight: {annual_tonnes/1e6:.1f} million tonnes/year")

print("\n" + "=" * 70)
print("IS 30 EUR/HOUR REASONABLE?")
print("=" * 70)

print("""
VoT = 30 EUR/hour means the MODEL VALUES freight time at 30 EUR per tonne-hour.

This represents:
  - Inventory carrying cost (capital tied up in goods)
  - Supply chain delays (production waiting for inputs)
  - Customer service levels (delivery time commitments)

Typical values in literature:
  - Low-value bulk goods: 0.5-2 EUR/tonne-hour
  - General freight: 5-15 EUR/tonne-hour
  - High-value/time-sensitive: 20-50+ EUR/tonne-hour

30 EUR/hour is on the HIGH end - appropriate for time-sensitive freight,
but may overvalue the cost of transit time for bulk commodities.
""")

print("=" * 70)
print("IMPACT ON MODEL BEHAVIOR")
print("=" * 70)

print("""
With VoT = 30 EUR/hour dominating the objective (84% of costs):

1. The model STRONGLY prioritizes FASTER routes
2. Mode choice is heavily influenced by speed (road > rail for time)
3. Vehicle costs (capital, fuel) are relatively minor considerations
4. BEV adoption is NOT penalized much by higher capital cost

This explains why BEV adoption happens even with high capital costs -
the intangible costs dwarf the vehicle costs!

If you want vehicle costs to matter more, consider:
  - Reducing VoT (e.g., 5-10 EUR/hour for general freight)
  - Or running scenarios with VoT = 0 to see pure TCO optimization
""")
