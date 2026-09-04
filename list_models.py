import google.generativeai as genai

# bu yerga API keyingni joylashtir
genai.configure(api_key="AIzaSyATHN1AoaE_zEL3KHEsXT0oZJ_3p23yIrQ")

models = genai.list_models()
for model in models:
    print(model.name)
