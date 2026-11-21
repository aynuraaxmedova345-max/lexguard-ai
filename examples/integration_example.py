from retriever import search_law

query = 'Ijaraga beruvchi ijara shartnomasini bir tomonlama bekor qilishi mumkinmi?'
results = search_law(query, top_k=5, include_full_article=True)
for r in results:
    print(f"{r['document_name']} {r['article_number']}-modda: {r['article_title']}")
    print(r['text'][:250])
    print('Rasmiy manba:', r['source_url'])
    print('Hujjat holati:', r['verification_status'])
    print('---')

# For an LLM: send only the retrieved, cited article text as legal evidence.
# Do not equate retrieval rank/score with evidence validity or legal correctness.
