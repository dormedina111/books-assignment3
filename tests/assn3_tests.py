import pytest
import requests

base_url = "http://localhost:5001"

book1 = { "title":"Adventures of Huckleberry Finn", "ISBN":"9780520343641", "genre":"Fiction" }
book2 = { "title":"The Best of Isaac Asimov", "ISBN":"9780385050784", "genre":"Science Fiction" }
book3 = { "title":"Fear No Evil", "ISBN":"9780394558783", "genre":"Biography" }
book4 = { "title": "No such book", "ISBN":"0000001111111", "genre":"Biography" }
book5 = { "title":"The Greatest Joke Book Ever", "authors":"Mel Greene", "ISBN":"9780380798490", "genre":"Jokes" }
Book6 = { "title":"The Adventures of Tom Sawyer", "ISBN":"9780195810400", "genre":"Fiction" }
book7 = { "title": "I, Robot", "ISBN":"9780553294385", "genre":"Science Fiction"}
book8 = { "title": "Second Foundation", "ISBN":"9780553293364", "genre":"Science Fiction"}

def delete_all_books():
    response = requests.get(f"{base_url}/books")
    books = response.json()
    for book in books:
        delete_response = requests.delete(f"{base_url}/books/{book['id']}")
        if delete_response.status_code != 200:
            print(f"Failed to delete book: {delete_response.json()}")


@pytest.fixture(scope="module")
def create_books():
    delete_all_books()
    books = [book1, book2, book3]
    responses = []
    for book in books:
        response = requests.post(f"{base_url}/books", json=book)
        if response.status_code != 201:
            print(f"Failed to create book: {response.json()}")
        responses.append(response)
    return responses

@pytest.fixture(scope="module")
def books_ids(create_books):
    return [response.json()['id'] for response in create_books]

def test_create_books(create_books):
    responses = create_books
    for response in responses:
        assert response.status_code == 201
    ids = [response.json()['id'] for response in responses]
    assert len(ids) == 3  
    assert len(ids) == len(set(ids)) 

def test_get_book_by_id(books_ids):
    book1_id = books_ids[0]
    response = requests.get(f"{base_url}/books/{book1_id}")
    assert response.status_code == 200
    book = response.json()
    assert book['authors'] == "Mark Twain"

def test_get_all_books():
    response = requests.get(f"{base_url}/books")
    assert response.status_code == 200
    books_list = response.json()
    assert isinstance(books_list, list)
    assert len(books_list) == 3

def test_create_book_with_invalid_isbn():
    response = requests.post(f"{base_url}/books", json=book4)
    assert response.status_code in [400, 500]

def test_delete_book(books_ids):
    book2_id = books_ids[1]
    response = requests.delete(f"{base_url}/books/{book2_id}")
    assert response.status_code == 200

def test_get_deleted_book(books_ids):
    book2_id = books_ids[1]
    response = requests.get(f"{base_url}/books/{book2_id}")
    assert response.status_code == 404

def test_create_book_with_invalid_genre():
    response = requests.post(f"{base_url}/books", json=book5)
    assert response.status_code == 422
