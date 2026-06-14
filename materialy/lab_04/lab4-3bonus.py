import numpy as np

filmy = {
    "Incepcja":          np.array([0.8, 0.3, 0.9]),
    "Matrix":            np.array([0.75, 0.35, 0.85]),
    "Toy Story":         np.array([0.2, 0.9, 0.1]),
    "Shrek":             np.array([0.25, 0.85, 0.15]),
    "Szeregowiec Ryan":  np.array([0.6, 0.1, 0.7]),
}


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def semantic_search(query_vec, database, top_k=3):
    scored = [
        (title, cosine_similarity(query_vec, vec))
        for title, vec in database.items()
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]


query = np.array([0.7, 0.3, 0.8])  # "coś jak sci-fi"
results = semantic_search(query, filmy, top_k=3)
for title, sim in results:
    print(f"  {title}: {sim:.3f}")