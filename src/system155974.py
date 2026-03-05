from RatingSystem import RatingSystem
import csv

class MySystem(RatingSystem):
    def __init__(self):
        super().__init__()
        self.movie_genres = {}

        try:
            with open('../data/movie.csv', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                next(csv_reader)
                for line in csv_reader:
                    movie_id = int(line[0])
                    if len(line) > 2:
                        genres = line[2].split('|')
                    else:
                        genres = []
                    self.movie_genres[movie_id] = genres
        except FileNotFoundError:
            print("Uwaga: Nie znaleziono pliku 'data/movie.csv'.")

    def rate(self, user, movie):
        """
        Zwraca średnią ważoną ocen użytkownika.
        Wagą jest liczba gatunków wspólnych między ocenionym filmem a filmem docelowym.
        """
        target_genres = set(self.movie_genres.get(movie, []))

        if not target_genres:
            if user.ratings:
                return sum(user.ratings.values()) / len(user.ratings)
            return 2.5

        weighted_rating_sum = 0
        total_weight = 0

        for rated_movie_id, rating in user.ratings.items():
            rated_movie_genres = set(self.movie_genres.get(rated_movie_id, []))

            common_genres = target_genres.intersection(rated_movie_genres)

            weight = len(common_genres)

            if weight > 0:
                weighted_rating_sum += rating * weight
                total_weight += weight

        if total_weight > 0:
            return weighted_rating_sum / total_weight

        user_ratings_count = len(user.ratings)
        user_avg = sum(user.ratings.values()) / user_ratings_count if user_ratings_count > 0 else 2.5

        movie_ratings_list = self.movie_ratings.get(movie, [])
        movie_ratings_count = len(movie_ratings_list)
        movie_avg = sum(movie_ratings_list) / movie_ratings_count if movie_ratings_count > 0 else 2.5

        # Hybryda działa lepiej niż sama średnia użytkownika
        return (user_avg + movie_avg) / 2.0

    def __str__(self):
        """
        Ta metoda zwraca numery indeksów wszystkich twórców rozwiązania. Poniżej przykład.
        """
        return 'System created by 155974, 155874 and 155879'
