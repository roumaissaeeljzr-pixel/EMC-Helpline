from rag.generator import generate_answer

question = (
    "أتلقى باستمرار رسائل مهينة ومذلة عبر مواقع التواصل الاجتماعي."
)

result = generate_answer(question)

print("=" * 80)
print("QUESTION")
print("=" * 80)
print(question)

print("\n" + "=" * 80)
print("RÉPONSE")
print("=" * 80)
print(result.get("answer"))

print("\n" + "=" * 80)
print("INTENTION")
print("=" * 80)
print(result.get("predicted_intent"))

print("\n" + "=" * 80)
print("SOURCES")
print("=" * 80)

for source in result.get("sources", []):
    print(source)