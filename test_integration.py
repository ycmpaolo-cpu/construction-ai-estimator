import pandas as pd
from pricing_engine import MaterialIntelligence
from blueprint_engine import BlueprintEngine

def test_integration():
    tasks = pd.read_csv("tasks.csv")
    assemblies = pd.read_csv("assemblies.csv")
    pricing_engine = MaterialIntelligence()
    blueprint_engine = BlueprintEngine()

    # Simulate extracted blueprint components
    components = [{"component": "roof", "width": 40, "length": 50}]
    
    # Calculate materials
    materials = blueprint_engine.calculate_materials(components, assemblies)
    print("Materials:", materials)

    # Test pricing logic (where the bug was)
    total_cost = 0
    for item in materials:
        price, supplier = pricing_engine.get_best_price(item["material"])[:2]
        
        if price != float('inf'):
            cost = price * item["quantity"]
            total_cost += cost
            print(f"Cost for {item['material']}: ${cost}")
        else:
            print(f"Missing price for {item['material']}")
            
    print(f"Total calculated cost: ${total_cost}")

if __name__ == "__main__":
    test_integration()
