from pymongo import MongoClient

def check_faculty():
    client = MongoClient('mongodb+srv://admin:Uj42BhTYo0D3Q2HE@nepcluster.e5ujuoo.mongodb.net/?retryWrites=true&w=majority')
    db = client['NEP-Timetable']
    
    # Check faculty collection
    faculty_docs = list(db['faculty'].find(limit=10))
    print(f'Total faculty: {len(faculty_docs)}')
    for doc in faculty_docs:
        print(f"ID: {doc.get('_id')}, Name: {doc.get('name')}, Specialization: {doc.get('specialization')}")
    
    client.close()

check_faculty()
