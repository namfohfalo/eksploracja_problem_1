from RatingSystem import RatingSystem
import csv
import math


class MySystem(RatingSystem):
    def __init__(self):
        super().__init__()
        self.movie_genres = {}
        # Słownik pomocniczy: movie_id -> lista user_id, którzy go ocenili
        self.movie_to_users = {}

        # Wczytywanie gatunków filmowych
        try:
            with open('../data/movie.csv', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                next(csv_reader)
                for line in csv_reader:
                    if not line:
                        continue
                    movie_id = int(line[0])
                    genres = line[2].split('|') if len(line) > 2 else []
                    self.movie_genres[movie_id] = genres
        except FileNotFoundError:
            print("Uwaga: Nie znaleziono pliku '../data/movie.csv'.")

        # Budowanie indeksu movie -> users dla optymalizacji Collaborative Filtering
        # Zakładamy, że self.users jest wypełnione przez klasę bazową przed lub w trakcie działania
        for user_id, user_obj in self.users.items():
            for movie_id in user_obj.ratings.keys():
                if movie_id not in self.movie_to_users:
                    self.movie_to_users[movie_id] = []
                self.movie_to_users[movie_id].append(user_id)

    def _get_user_mean(self, ratings_dict):
        """Oblicza średnią ocen użytkownika."""
        if not ratings_dict:
            return 2.5
        return sum(ratings_dict.values()) / len(ratings_dict)

    def _cosine_similarity(self, ratings_a, ratings_b):
        """Adjusted Cosine Similarity (wyśrodkowany cosinus)."""
        common_movies = set(ratings_a.keys()) & set(ratings_b.keys())
        if not common_movies:
            return 0.0

        mean_a = self._get_user_mean(ratings_a)
        mean_b = self._get_user_mean(ratings_b)

        dot_product = 0.0
        norm_a = 0.0
        norm_b = 0.0

        for movie in common_movies:
            diff_a = ratings_a[movie] - mean_a
            diff_b = ratings_b[movie] - mean_b
            dot_product += diff_a * diff_b
            norm_a += diff_a ** 2
            norm_b += diff_b ** 2

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))

    def _collaborative_score(self, user, movie, k=20, min_common=2):
        """User-based collaborative filtering z ograniczeniem do K sąsiadów."""
        neighbors = []
        user_mean = self._get_user_mean(user.ratings)

        # Optymalizacja: sprawdzamy tylko użytkowników, którzy ocenili ten film
        potential_neighbor_ids = self.movie_to_users.get(movie, [])

        for other_id in potential_neighbor_ids:
            if other_id == user.id:
                continue

            other_user = self.users[other_id]
            common_movies = set(user.ratings.keys()) & set(other_user.ratings.keys())

            if len(common_movies) < min_common:
                continue

            sim = self._cosine_similarity(user.ratings, other_user.ratings)
            if sim > 0:  # Interesują nas tylko pozytywne korelacje
                neighbors.append((other_user, sim))

        if not neighbors:
            return None, 0

        # Wybór najlepszych sąsiadów
        neighbors.sort(key=lambda x: x[1], reverse=True)
        top_k = neighbors[:k]

        numerator = 0.0
        denominator = 0.0

        for neighbor, sim in top_k:
            neighbor_mean = self._get_user_mean(neighbor.ratings)
            numerator += sim * (neighbor.ratings[movie] - neighbor_mean)
            denominator += sim

        if denominator == 0:
            return None, 0

        prediction = user_mean + (numerator / denominator)
        confidence = len(top_k) / k
        return prediction, confidence

    def _genre_score(self, user, movie):
        """Content-based filtering oparty na gatunkach."""
        target_genres = set(self.movie_genres.get(movie, []))
        if not target_genres:
            return None, 0

        weighted_sum = 0.0
        total_weight = 0.0

        for rated_id, rating in user.ratings.items():
            rated_genres = set(self.movie_genres.get(rated_id, []))
            weight = len(target_genres.intersection(rated_genres))

            if weight > 0:
                weighted_sum += rating * weight
                total_weight += weight

        if total_weight > 0:
            # Confidence rośnie wraz z liczbą dopasowań (max przy 15 punktach wagi)
            confidence = min(total_weight / 15.0, 1.0)
            return weighted_sum / total_weight, confidence

        return None, 0

    def rate(self, user, movie):
        """Hybrydowa metoda predykcji ocen."""
        collab_val, collab_conf = self._collaborative_score(user, movie)
        genre_val, genre_conf = self._genre_score(user, movie)

        # Scenariusz 1: Mamy oba wyniki - ważymy je
        if collab_val is not None and genre_val is not None:
            # Dajemy większą wagę CF, bo zazwyczaj jest dokładniejszy
            w_collab = collab_conf * 2.0
            w_genre = genre_conf * 1.0
            final = (collab_val * w_collab + genre_val * w_genre) / (w_collab + w_genre)
            return max(0.5, min(5.0, final))

        # Scenariusz 2: Mamy tylko jeden z systemów
        if collab_val is not None:
            return max(0.5, min(5.0, collab_val))
        if genre_val is not None:
            return max(0.5, min(5.0, genre_val))

        # Scenariusz 3: Cold Start - brak danych o gatunkach i sąsiadach
        u_avg = self._get_user_mean(user.ratings)

        movie_ratings = self.movie_ratings.get(movie, [])
        m_avg = sum(movie_ratings) / len(movie_ratings) if movie_ratings else 2.5

        return (u_avg + m_avg) / 2.0

    def __str__(self):
        return 'System created by 155974, 155874 and 155879'