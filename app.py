from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Additive safety database for fallback/extra analysis
ADDITIVE_DB = {
    "palm oil": ("High in saturated fats; linked to inflammation.", "YELLOW"),
    "palmolein": ("Refined palm oil; heavily processed.", "YELLOW"),
    "high fructose corn syrup": ("Refined liquid sugar linked to insulin spikes.", "RED"),
    "maltodextrin": ("Ultra-processed starch that spikes blood sugar.", "YELLOW"),
    "sodium benzoate": ("Preservative (INS 211) that can irritate sensitive stomachs.", "RED"),
    "monosodium glutamate": ("Flavor enhancer (INS 621 / MSG).", "YELLOW"),
    "ins 621": ("Monosodium glutamate (MSG) flavor enhancer.", "YELLOW"),
    "ins 322": ("Emulsifier (soy lecithin); ultra-processed binder.", "YELLOW"),
    "artificial flavor": ("Synthetic flavoring chemicals.", "RED"),
    "hydrogenated": ("Contains or risks hidden trans fats.", "RED")
}

def analyze_ingredients_text(text):
    clean_text = text.lower()
    flagged = []
    has_red = False
    
    for ingredient, (reason, severity) in ADDITIVE_DB.items():
        if ingredient in clean_text:
            flagged.append({"name": ingredient.title(), "reason": reason, "severity": severity})
            if severity == "RED":
                has_red = True
            
    if len(flagged) == 0:
        status = "GREEN"
        summary = "Clean profile! No major red-flag additives detected."
    elif has_red:
        status = "RED"
        summary = f"High alert — {len(flagged)} processed additive(s) found."
    else:
        status = "YELLOW"
        summary = f"Moderate caution — {len(flagged)} additive(s) found."
        
    return {"status": status, "summary": summary, "flagged": flagged}

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    search_query = ""
    product_name = ""
    
    if request.method == "POST":
        search_query = request.form.get("search_query", "").strip()
        manual_text = request.form.get("manual_ingredients", "").strip()
        
        if search_query:
            # Query Open Food Facts API
            api_url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={search_query}&search_simple=1&action=process&json=1"
            try:
                response = requests.get(api_url, timeout=5)
                data = response.json()
                products = data.get("products", [])
                
                if products:
                    first_product = products[0]
                    product_name = first_product.get("product_name", search_query)
                    ingredients_text = first_product.get("ingredients_text_en", first_product.get("ingredients_text", ""))
                    
                    if not ingredients_text:
                        ingredients_text = "Ingredient list not provided in database for this item. Try manual paste."
                        
                    result = analyze_ingredients_text(ingredients_text)
                    result["product_name"] = product_name
                else:
                    result = {
                        "status": "YELLOW",
                        "summary": f"No products found for '{search_query}'. Try pasting ingredients manually below.",
                        "flagged": []
                    }
            except Exception as e:
                result = {
                    "status": "RED",
                    "summary": "Error connecting to food database. Check your internet connection.",
                    "flagged": []
                }
        elif manual_text:
            result = analyze_ingredients_text(manual_text)
            result["product_name"] = "Custom Paste"
            
    return render_template("index.html", result=result, search_query=search_query)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)