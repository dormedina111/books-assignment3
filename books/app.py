from flask import Flask, request, jsonify
import requests, datetime
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb://mongo:27017/')  
db = client['library']  
books_collection = db['books']
ratings_collection = db['ratings']

GOOGLE_BOOKS_API_BASE_URL = 'https://www.googleapis.com/books/v1/volumes?q=isbn:'

def get_authors_publisher_publishedDate(isbn_num):
    # Fetch book information from Google Books API
    response = requests.get(GOOGLE_BOOKS_API_BASE_URL + isbn_num)
    if response.status_code == 200:
        book_info = response.json().get('items')[0].get('volumeInfo')
        
        authors_list = book_info.get('authors', ["missing"])
        if len(authors_list) == 1:
            authors = authors_list[0]
        elif len(authors_list) > 1:
            authors = ' and '.join(authors_list)
        
        publisher = book_info.get('publisher', 'missing')
        
        published_date = book_info.get('publishedDate')

        if published_date:
            try:
                datetime.datetime.strptime(published_date, '%Y-%m-%d')
            except ValueError:
                try:
                    datetime.datetime.strptime(published_date, '%Y')
                except ValueError:
                    published_date = "missing"
        else:
            published_date = "missing"
        return authors, publisher, published_date
    else:
        # If Google Books API request fails, send 500
        return jsonify({"error": "Unable to connect to Google"}), 500

def create_ratings_entry(book_id, title):
    # Create a new ratings entry with default values
    ratings_entry = {
        'id': book_id,
        'values': [],
        'average': 0.0,
        'title': title
    }
    # Add the ratings entry to the ratings collection
    ratings_collection.insert_one(ratings_entry)

# POST /books request
@app.route('/books', methods=['POST'])
def create_book():
    # Get book data from request
    data = request.json
    if not data:
        return jsonify({"error": "Unsupported media type"}), 415

    # Check if all required fields are provided
    required_fields = ['title', 'ISBN', 'genre']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 422
    
    title = data.get('title')
    isbn = data.get('ISBN')
    genre = data.get('genre')
    
    # Check if the genre value is valid
    valid_genres = ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other']
    if genre not in valid_genres:
        return jsonify({"error": f"{genre} is not a valid genre"}), 422

    # Check if a book with the same ISBN already exists
    if books_collection.find_one({'ISBN': isbn}):
        return jsonify({"error": "A book with this ISBN number already exists"}), 422

    authors, publisher, published_date = get_authors_publisher_publishedDate(isbn)

    # Create the book 
    book = {
        'title': title,
        'authors': authors,
        'ISBN': isbn,
        'publisher': publisher,
        'publishedDate': published_date,
        'genre': genre
    }

    # Add book to books collection
    result = books_collection.insert_one(book)
    book_id = str(result.inserted_id)

    # Set the id field to the book document
    books_collection.update_one({'_id': result.inserted_id}, {'$set': {'id': book_id}})

    # Create ratings entry for the new book
    create_ratings_entry(book_id, title)

    # Return created book resource
    return jsonify({"id": book_id}), 201

# GET /books request
@app.route('/books', methods=['GET'])
def get_books():
    # Get query parameters from the request
    query_params = request.args.to_dict()

    # If there are no query parameters, return all books
    if not query_params:
        books = list(books_collection.find({}, {'_id': 0, 'id': 1, 'title': 1, 'ISBN': 1, 'genre': 1, 'authors': 1, 'publisher': 1, 'publishedDate': 1}))
        return jsonify(books), 200

    # Filter books based on query parameters
    filtered_books = list(books_collection.find(query_params, {'_id': 0, 'id': 1, 'title': 1, 'ISBN': 1, 'genre': 1, 'authors': 1, 'publisher': 1, 'publishedDate': 1}))
    return jsonify(filtered_books), 200

# GET /books/id request
@app.route('/books/<id>', methods=['GET'])
def get_book_by_id(id):
    # Check if the book with the given ID exists
    book = books_collection.find_one({'_id': ObjectId(id)}, {'_id': 0, 'id': 1, 'title': 1, 'ISBN': 1, 'genre': 1, 'authors': 1, 'publisher': 1, 'publishedDate': 1})
    if not book:
        return jsonify({"error": "Book not found"}), 404

    # Return the book with the given ID
    return jsonify(book), 200

# DELETE /books/<id> request
@app.route('/books/<id>', methods=['DELETE'])
def delete_book(id):
    # Check if the book exists
    result = books_collection.delete_one({'_id': ObjectId(id)})

    if result.deleted_count == 0:
        return jsonify({"error": "Not Found"}), 404

    # Delete the corresponding rating entry
    ratings_collection.delete_one({'id': id})

    return jsonify({"id": id, "message": "Book and its ratings deleted successfully"}), 200

# UPDATE /books/<id> request
@app.route('/books/<id>', methods=['PUT'])
def update_book(id):
    # Check if the book exists
    if not books_collection.find_one({'_id': ObjectId(id)}):
        return jsonify({"error": "Not Found"}), 404

    # Get the updated data from the request
    updated_data = request.json
    if not updated_data:
        return jsonify({"error": "Unsupported media type"}), 415
    
    # Check if all required fields are provided
    required_fields = ['title', 'ISBN', 'genre', 'authors', 'publisher', 'publishedDate']
    if not all(field in updated_data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 422

    # Check if the genre value is valid
    valid_genres = ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other']
    if updated_data['genre'] not in valid_genres:
        return jsonify({"error": "Invalid genre"}), 422

    # Update the book's information
    books_collection.update_one({'_id': ObjectId(id)}, {'$set': updated_data})

    # Return the ID of the updated resource
    return jsonify({"id": id, "message": "Book updated successfully"}), 200

# GET /ratings request
@app.route('/ratings', methods=['GET'])
def get_ratings():
    # Get the query parameters from the request
    query_params = request.args.to_dict()

    # If the query parameter 'id' is provided, return the rating information for that specific book
    if 'id' in query_params:
        book_id = query_params.get('id')
        rating = ratings_collection.find_one({'id': book_id}, {'_id': 0})
        if not rating:
            return jsonify({"error": "Rating not found"}), 404
        return jsonify(rating), 200

    # If no query parameter is provided, return a JSON array containing all rating information
    ratings = list(ratings_collection.find({}, {'_id': 0}))
    return jsonify(ratings), 200

# GET /ratings/{id} request
@app.route('/ratings/<id>', methods=['GET'])
def get_rating_by_id(id):
    # Check if the book with the given ID exists in the ratings
    rating = ratings_collection.find_one({'id': id}, {'_id': 0})
    if not rating:
        return jsonify({"error": "Rating not found"}), 404
    
    # Return the rating with the given ID
    return jsonify(rating), 200

# POST /ratings/{id}/values request
@app.route('/ratings/<id>/values', methods=['POST'])
def add_rating_value(id):
    # Check if the book with the given ID exists in the ratings
    rating = ratings_collection.find_one({'id': id})
    if not rating:
        return jsonify({"error": "Rating not found"}), 404
    
    # Get the data from the request
    data = request.json
    if not data or 'value' not in data:
        return jsonify({"error": "Invalid request format"}), 422
    
    # Extract the rating value from the data
    new_value = data['value']

    # Check if the new value is valid (between 1 and 5)
    if new_value < 1 or new_value > 5:
        return jsonify({"error": "Rating value must be between 1 and 5"}), 422

    # Add the new value to the existing values
    current_values = rating.get('values', [])
    current_values.append(new_value)

    # Calculate the new average rating
    new_average = sum(current_values) / len(current_values)

    # Update the values and average rating in the ratings collection
    ratings_collection.update_one({'id': id}, {'$set': {'values': current_values, 'average': round(new_average, 2)}})


    # Return the new average rating
    return jsonify({"average": round(new_average, 2)}), 200

# GET /top request
@app.route('/top', methods=['GET'])
def get_top_books():
    try:
        # Calculate the average rating for each book
        ratings = list(ratings_collection.find())
        print(f"Ratings found: {ratings}")  # Debugging: Print all ratings found
        
        top_books = [r for r in ratings if len(r.get('values', [])) >= 3]
        print(f"Top books before sorting: {top_books}")  # Debugging: Print top books before sorting
        
        top_books.sort(key=lambda x: x['average'], reverse=True)
        print(f"Top books after sorting: {top_books}")  # Debugging: Print top books after sorting

        if len(top_books) > 3:
            # Get the average rating of the third highest rated book
            third_highest_average = top_books[2]['average']
            print(f"Third highest average: {third_highest_average}")  # Debugging: Print third highest average

            # Select all books with one of the top 3 average ratings
            top_books = [book for book in top_books if book['average'] >= third_highest_average]
            print(f"Top books after filtering: {top_books}")  # Debugging: Print top books after filtering
        
        top_books_response = [
            {
                'id': str(book['_id']),  # Convert ObjectId to string
                'title': book['title'],
                'average': book['average']
            }
            for book in top_books
        ]

        # Return list of top books
        return jsonify(top_books_response), 200
    except Exception as e:
        print(f"Error: {e}")  # Debugging: Print the error
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

