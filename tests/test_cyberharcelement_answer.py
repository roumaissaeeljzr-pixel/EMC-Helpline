from rag.generator import generate_answer

question = (
    "Je reçois constamment des messages insultants "
    "et humiliants sur les réseaux sociaux."
)

print("=" * 80)
print("QUESTION")
print("=" * 80)
print(question)

print("\n" + "=" * 80)
print("RÉPONSE")
print("=" * 80)

result = generate_answer(question)

print(result)