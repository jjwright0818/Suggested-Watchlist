import requests
import os
import json
from collections import Counter

# get api key from the environment
KEY = os.environ.get("TMDB_API_KEY", "")
if not KEY:
    print("Error: TMDB API key not found. Please set it as an environment variable.")
    exit(1)
    
URL = "https://api.themoviedb.org/3"

# clears the terminal, working for both mac and windows
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# prompt user for input, and checks that movie is correct before returning
def get_movie():
    clear()
    while True:    
        user_input = input("Movie: ")

        endpoint = f"{URL}/search/movie"
        params = {
            "api_key": KEY,
            "query": user_input,
            "language": "en-US",
            "page": 1,
            "include_adult": False
        }
        
        response = requests.get(endpoint, params=params)

        data = response.json()

        if not data.get('results'):
            input('No movies found, press enter to continue\n')
            continue
            
        while True:
            print(f"{data['results'][0]['original_title']} released {data['results'][0]['release_date']}")

            user_input = input("Select a command\n1. Correct movie\n2. Select a different movie\n3. Exit\n")

            if user_input == '1':
                return data['results'][0]
            elif user_input == '2':
                break
            elif user_input == '3':
                return None

# given a movie, ask for rating and add it to the watched list
# movie - movie being added to the watched list
# movies - contains the watched and planned lists
def add_watched(movie, movies):
    movies['watched'][movie[0]] = movie

    clear()
    # ensure rating is between 1 and 10 (inclusive)
    while True:
        try:
            rating = float(input('Rate the movie fromm 1 to 10: '))
        except ValueError:
            pass

        if rating >= 1 and rating <= 10:
            break

    # add it to the watched list
    movies['watched'][movie[0]].append(rating)

# given a list, display options to user and get input
# my_list - list with input to be chosen from
def select_from_list(my_list):
    clear()
    if not my_list:
        return None
    
    print('Select a movie: ')

    i = 1
    for movie in my_list:
        print(f"{i}. {movie}")
        i += 1

    user_input = input()

    if user_input.isdigit() and int(user_input) <= len(my_list) and int(user_input) > 0:
        return my_list[int(user_input) - 1]
    
    return None

# handler of user input of watchlist functionality
# movies - contains the watched and planned lists
def watchlist(movies):
    while True:
        clear()
        user_input = (input("Select a command\n1. View lists\n2. Add planned movie\n3. Move to watched\n4. Remove planned movie\n5. Add watched movie\n6. Remove watched movie\n7. Exit\n"))

        # iterate thorugh both watched and planned and display them to the user
        if user_input == '1':
            clear()
            print("Watched movies: ")
            i = 1
            for movie in movies['watched']:
                print(f"{i}. {movies['watched'][movie][0]} {movies['watched'][movie][2]}/10")
                i += 1
            
            print("\nPlanned movies: ")
            i = 1
            for movie in movies['planned']:
                print(f"{i}. {movies['planned'][movie][0]}")
                i += 1
            
            input("\nEnter to continue")
        # get movie and add the movie to planned
        elif user_input == '2':
            movie = get_movie()

            if movie and not movies['planned'].get(movie['original_title']):
                movies['planned'][movie['original_title']] = [movie['original_title'], movie['genre_ids']]
        # select from the planned list and move it to the watched list
        elif user_input == '3':
            movie = select_from_list(list(movies['planned'].keys()))

            if movie:
                add_watched(movies['planned'][movie], movies)
                del movies['planned'][movie]
        # select from planned and remove it
        elif user_input == '4':
            movie = select_from_list(list(movies['planned'].keys()))
            if movie:
                del movies['planned'][movie]
        # get movie and immediately add it to watched
        elif user_input == '5':
            movie = get_movie()
            add_watched([movie['original_title'], movie['genre_ids']], movies)
        # select from watched and remove it from the list
        elif user_input == '6':
            movie = select_from_list(list(movies['watched'].keys()))
            if movie:
                del movies['watched'][movie]
        elif user_input == '7':
            break

# generate suggestions based upon TMDB genre ids
# genre_id - id representing certain genres
# page - page number we want to get movies from
def generate_movies(genre_id=None, page=1):
    url = f"{URL}/discover/movie"
    params = {
        "api_key": KEY,
        "language": "en-US",
        "sort_by": "vote_count.desc",
        "page": page
    }
    
    if genre_id:
            params["with_genres"] = genre_id

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("results", [])
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

# print the suggested movies, not printing the user selected movie, if applicable, or already watched movies
# movies - contains the watched and planned lists
# suggestions - list of suggested movies
# genres - name of genres used in getting suggestions
# user_movie - default to None, used in suggest from specific movie
def print_movies(movies, suggestions, genres, user_movie=None):
    clear()
    # handler if suggestions are just from popular movies
    if genres is not None:    
        print(f"Popular movies in {", ".join(genres[:-1]) + (" and " + genres[-1] if len(genres) > 1 else genres[0])}")
    else:
        print("Popular movies")

    if user_movie:
        user_movie = user_movie['original_title']
            
    i = 0
    for movie in suggestions:
        # ensure the user has not watched the movie or inputted as a suggestion
        if movie['original_title'] not in movies['watched'] and movie['original_title'] != user_movie:
            i += 1
            print(movie['original_title'])
        
        # only print 5 movies
        if i == 5:
            break
    
    input()

# handler of all suggestion functionality
# movies - contains the watched and planned lists
def suggest(movies):
    # get a list of genre ids from TMDB
    endpoint = f"{URL}/genre/movie/list"
    params = {
        "api_key": KEY,
        "language": "en-US"
    }

    response = requests.get(endpoint, params=params)
    data = response.json()
    
    genres = {genre['id']: genre['name'] for genre in data.get('genres', [])}
    
    while True:
        # clear the comman line
        clear()

        user_input = (input("Select a command\n1. Suggestion from watchlist\n2. Suggestion from specific movie\n3. Suggestion by genre\n4. Popular suggestions\n5. Exit\n"))

        # suggestions from watched movies
        if user_input == '1':
            if not movies['watched']:
                print("You haven't watched any movies yet. No suggestions available.")
                input("\nPress Enter to continue...")
                continue

            # counts the occurences of each genre in watched movies to determine preferred movies
            genre_counts = Counter()
            for movie in movies['watched'].values():
                genre_ids = movie[1]
                genre_counts.update(genre_ids)

            top_genres = [genre for genre, _ in genre_counts.most_common(3)]

            # displays combined top 3 suggestions
            combined_suggestions = generate_movies(top_genres)
            genre_names = [genres.get(genre, "Unknown") for genre in top_genres]


            print_movies(movies, combined_suggestions, genre_names)

            # displays the individual genre suggestions to the user
            if len(top_genres) > 1:   
                for genre in top_genres:
                    individual_suggestion = generate_movies(genre)
                    genre_name = [genres.get(genre, "Unknown")]

                    print_movies(movies, individual_suggestion, genre_name)
        # get specific movie from the user and generate suggestions based on its genre ids
        elif user_input == '2':
            user_movie = get_movie()
            user_genres = user_movie['genre_ids']

            suggestions = generate_movies(user_genres)

            genre_names = [genres.get(genre, "Unknown") for genre in user_genres]

            print_movies(movies, suggestions, genre_names, user_movie)
        # prompt user with all genre ids, and generate suggestions from selected genre
        elif user_input == '3':
            user_genre = select_from_list(list(genres.values()))

            # take word of selected genre and convert it back to id number
            if user_genre:
                for id in genres:
                    if genres[id] == user_genre:
                        user_id = [id]
                        break

                suggestions = generate_movies(user_id)

                print_movies(movies, suggestions, [user_genre])
        # genereate a list of popular movies
        elif user_input == '4':
            suggestions = generate_movies()

            print_movies(movies, suggestions, None)
        elif user_input == '5':
            clear()
            break


# save to json file movies.json
def save_movies(movies):
    try:
        with open("movies.json", "w") as file:
            json.dump(movies, file, indent=4)
    except Exception:
        print("error saving files")
        input()

# load json file movies.json
def load_movies():
    if not os.path.exists("movies.json"):
        return {'watched': {}, 'planned': {}}

    try:
        with open("movies.json", "r") as file:
            movies = json.load(file)
        return movies
    except Exception as e:
        return {'watched': {}, 'planned': {}}

def main():
    # load from json file
    movies = load_movies()

    # get input form user on what functionality they want
    while True:
        # clear the comman line
        clear()

        user_input = (input("Select a command\n1. Review watchlist\n2. Generate suggestions\n3. Exit\n"))

        if user_input == '1':
            watchlist(movies)
        elif user_input == '2':
            suggest(movies)
        elif user_input == '3':
            clear()
            break
    
    # save to json file
    save_movies(movies)

if __name__ == "__main__":
    main()
