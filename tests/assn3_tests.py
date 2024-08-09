# import pytest
# import requests

# base_url = "http://localhost:5001"

# book1 = { "title":"Adventures of Huckleberry Finn", "ISBN":"9780520343641", "genre":"Fiction" }
# book2 = { "title":"The Best of Isaac Asimov", "ISBN":"9780385050784", "genre":"Science Fiction" }
# book3 = { "title":"Fear No Evil", "ISBN":"9780394558783", "genre":"Biography" }
# book4 = { "title": "No such book", "ISBN":"0000001111111", "genre":"Biography" }
# book5 = { "title":"The Greatest Joke Book Ever", "authors":"Mel Greene", "ISBN":"9780380798490", "genre":"Jokes" }
# Book6 = { "title":"The Adventures of Tom Sawyer", "ISBN":"9780195810400", "genre":"Fiction" }
# book7 = { "title": "I, Robot", "ISBN":"9780553294385", "genre":"Science Fiction"}
# book8 = { "title": "Second Foundation", "ISBN":"9780553293364", "genre":"Science Fiction"}

# def delete_all_books():
#     response = requests.get(f"{base_url}/books")
#     books = response.json()
#     for book in books:
#         delete_response = requests.delete(f"{base_url}/books/{book['id']}")
#         if delete_response.status_code != 200:
#             print(f"Failed to delete book: {delete_response.json()}")


# @pytest.fixture(scope="module")
# def create_books():
#     delete_all_books()
#     books = [book1, book2, book3]
#     responses = []
#     for book in books:
#         response = requests.post(f"{base_url}/books", json=book)
#         if response.status_code != 201:
#             print(f"Failed to create book: {response.json()}")
#         responses.append(response)
#     return responses

# @pytest.fixture(scope="module")
# def books_ids(create_books):
#     return [response.json()['id'] for response in create_books]
# ----- NIR TEST ------ 

import requests

BASE_URL = "http://localhost:5001/books"

book6 = {
    "title": "The Adventures of Tom Sawyer",
    "ISBN": "9780195810400",
    "genre": "Fiction"
}

book7 = {
    "title": "I, Robot",
    "ISBN": "9780553294385",
    "genre": "Science Fiction"
}

book8 = {
    "title": "Second Foundation",
    "ISBN": "9780553293364",
    "genre": "Science Fiction"
}

books_data = []


def test_post_books():
    books = [book6, book7, book8]
    for book in books:
        res = requests.post(BASE_URL, json=book)
        assert res.status_code == 201
        res_data = res.json()
        assert "id" in res_data
        books_data.append(res_data)
        books_data_tuples = [frozenset(book.items()) for book in books_data]
    assert len(set(books_data_tuples)) == 3


def test_get_query():
    res = requests.get(f"{BASE_URL}?authors=Isaac Asimov")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_delete_book():
    res = requests.delete(f"{BASE_URL}/{books_data[0]['id']}")
    assert res.status_code == 200


def test_post_book():
    book = {
        "title": "The Art of Loving",
        "ISBN": "9780062138927",
        "genre": "Science"
    }
    res = requests.post(BASE_URL, json=book)
    assert res.status_code == 201



def test_get_new_book_query():
    res = requests.get(f"{BASE_URL}?genre=Science")
    assert res.status_code == 200
    res_data = res.json()
    assert res_data[0]["title"] == "The Art of Loving"
