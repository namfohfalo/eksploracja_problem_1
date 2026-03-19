from RatingSystem import RatingSystem
import csv
import math


class MySystem(RatingSystem):
    def __init__(self):
        super().__init__()
        self.movie_genres = {}
        self.movie_to_user_ratings = {}
        self.item_sim_cache = {}

        try:
            with open('../data/movie.csv', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                next(csv_reader)
                for line in csv_reader:
                    if not line: continue
                    m_id = int(line[0])
                    self.movie_genres[m_id] = line[2].split('|') if len(line) > 2 else []
        except FileNotFoundError:
            print("Błąd: Brak pliku movie.csv")

        for u_id, user_obj in self.users.items():
            for m_id, rating in user_obj.ratings.items():
                if m_id not in self.movie_to_user_ratings:
                    self.movie_to_user_ratings[m_id] = {}
                self.movie_to_user_ratings[m_id][u_id] = rating

    def _get_item_similarity(self, movie_a, movie_b):
        """Oblicza podobieństwo cosinusowe między filmami."""
        pair = tuple(sorted((movie_a, movie_b)))
        if pair in self.item_sim_cache:
            return self.item_sim_cache[pair]

        ratings_a = self.movie_to_user_ratings.get(movie_a, {})
        ratings_b = self.movie_to_user_ratings.get(movie_b, {})

        common_users = set(ratings_a.keys()) & set(ratings_b.keys())

        if len(common_users) < 2:
            return 0.0

        dot_product = 0.0
        norm_a = 0.0
        norm_b = 0.0

        for u_id in common_users:
            r_a = ratings_a[u_id]
            r_b = ratings_b[u_id]
            dot_product += r_a * r_b
            norm_a += r_a ** 2
            norm_b += r_b ** 2

        sim = dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b)) if norm_a * norm_b > 0 else 0.0
        self.item_sim_cache[pair] = sim
        return sim

    def _item_based_score(self, user, target_movie, k=15):
        """Predykcja na podstawie podobieństwa przedmiotów."""
        similarities = []

        for rated_movie_id, rating in user.ratings.items():
            if rated_movie_id == target_movie:
                continue

            sim = self._get_item_similarity(target_movie, rated_movie_id)
            if sim > 0:
                similarities.append((sim, rating))

        if not similarities:
            return None, 0

        similarities.sort(key=lambda x: x[0], reverse=True)
        top_k = similarities[:k]

        weighted_sum = 0.0
        sum_of_sims = 0.0

        for sim, rating in top_k:
            weighted_sum += sim * rating
            sum_of_sims += sim

        if sum_of_sims == 0:
            return None, 0

        prediction = weighted_sum / sum_of_sims
        confidence = len(top_k) / k
        return prediction, confidence

    def _genre_score(self, user, movie):
        """Content-based filtering (gatunki)."""
        target_genres = set(self.movie_genres.get(movie, []))
        if not target_genres: return None, 0

        weighted_sum, total_w = 0.0, 0.0
        for m_id, rating in user.ratings.items():
            common = len(target_genres.intersection(set(self.movie_genres.get(m_id, []))))
            if common > 0:
                weighted_sum += rating * common
                total_w += common

        return (weighted_sum / total_w, min(total_w / 10, 1.0)) if total_w > 0 else (None, 0)

    def rate(self, user, movie):
        it_val, it_conf = self._item_based_score(user, movie)
        gn_val, gn_conf = self._genre_score(user, movie)

        if it_val is not None and gn_val is not None:
            w_it = it_conf * 2.5
            w_gn = gn_conf * 1.0
            res = (it_val * w_it + gn_val * w_gn) / (w_it + w_gn)
            return max(0.5, min(5.0, res))

        if it_val is not None: return max(0.5, min(5.0, it_val))
        if gn_val is not None: return max(0.5, min(5.0, gn_val))

        u_avg = sum(user.ratings.values()) / len(user.ratings) if user.ratings else 2.5
        m_ratings = self.movie_ratings.get(movie, [])
        m_avg = sum(m_ratings) / len(m_ratings) if m_ratings else 2.5

        return (u_avg + m_avg) / 2.0

    def __str__(self):
        """
        Ta metoda zwraca numery indeksów wszystkich twórców rozwiązania. Poniżej przykład.
        """
        return 'System created by 155974, 155874 and 155879'