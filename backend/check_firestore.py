"""Prove the Firestore connection works: write one document, read it, delete it."""
from app.db import connect_firestore

db = connect_firestore()
print(f"Connected to project: {db.project}")

doc = db.collection("connection_check").document("hello")

doc.set({"message": "Flask can reach Firestore"})
print("Wrote a document")

print("Read it back:", doc.get().to_dict())

doc.delete()
print("Deleted it. Still exists?", doc.get().exists)
