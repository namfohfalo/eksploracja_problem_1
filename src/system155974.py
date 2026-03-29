from RatingSystem import RatingSystem
import csv
import math


class MySystem(RatingSystem):
    def __init__(self):
        super().__init__()
        self.movie_genres = {}

        self.movie_to_user_ratings = {}
        self.movie_to_users_list = {}
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

                if m_id not in self.movie_to_users_list:
                    self.movie_to_users_list[m_id] = []
                self.movie_to_users_list[m_id].append(u_id)

    def _get_user_mean(self, ratings_dict):
        if not ratings_dict: return 2.5
        return sum(ratings_dict.values()) / len(ratings_dict)

    def _user_cosine_similarity(self, ratings_a, ratings_b):
        common = set(ratings_a.keys()) & set(ratings_b.keys())
        if not common: return 0.0
        mean_a, mean_b = self._get_user_mean(ratings_a), self._get_user_mean(ratings_b)
        dot, n_a, n_b = 0.0, 0.0, 0.0
        for m_id in common:
            da, db = ratings_a[m_id] - mean_a, ratings_b[m_id] - mean_b
            dot += da * db
            n_a += da ** 2
            n_b += db ** 2
        return dot / (math.sqrt(n_a) * math.sqrt(n_b)) if n_a * n_b > 0 else 0.0

    def _user_based_score(self, user, movie, k=20):
        neighbors = []
        u_mean = self._get_user_mean(user.ratings)
        potential_ids = self.movie_to_users_list.get(movie, [])
        for o_id in potential_ids:
            if o_id == user.id: continue
            other = self.users[o_id]
            sim = self._user_cosine_similarity(user.ratings, other.ratings)
            if sim > 0: neighbors.append((other, sim))

        if not neighbors: return None, 0
        neighbors.sort(key=lambda x: x[1], reverse=True)
        top_k = neighbors[:k]
        num, den = 0.0, 0.0
        for n, sim in top_k:
            num += sim * (n.ratings[movie] - self._get_user_mean(n.ratings))
            den += sim
        return (u_mean + num / den, len(top_k) / k) if den > 0 else (None, 0)

    def _item_cosine_similarity(self, m_a, m_b):
        pair = tuple(sorted((m_a, m_b)))
        if pair in self.item_sim_cache: return self.item_sim_cache[pair]
        r_a, r_b = self.movie_to_user_ratings.get(m_a, {}), self.movie_to_user_ratings.get(m_b, {})
        common = set(r_a.keys()) & set(r_b.keys())
        if len(common) < 2: return 0.0
        dot, n_a, n_b = 0.0, 0.0, 0.0
        for u_id in common:
            dot += r_a[u_id] * r_b[u_id]
            n_a += r_a[u_id] ** 2
            n_b += r_b[u_id] ** 2
        sim = dot / (math.sqrt(n_a) * math.sqrt(n_b)) if n_a * n_b > 0 else 0.0
        self.item_sim_cache[pair] = sim
        return sim

    def _item_based_score(self, user, target, k=15):
        sims = []
        for r_m_id, rating in user.ratings.items():
            if r_m_id == target: continue
            sim = self._item_cosine_similarity(target, r_m_id)
            if sim > 0: sims.append((sim, rating))
        if not sims: return None, 0
        sims.sort(key=lambda x: x[0], reverse=True)
        top_k = sims[:k]
        num, den = sum(s * r for s, r in top_k), sum(s for s, r in top_k)
        return (num / den, len(top_k) / k) if den > 0 else (None, 0)

    def _genre_score(self, user, movie):
        t_gen = set(self.movie_genres.get(movie, []))
        if not t_gen: return None, 0
        w_sum, t_w = 0.0, 0.0
        for m_id, rat in user.ratings.items():
            common = len(t_gen.intersection(set(self.movie_genres.get(m_id, []))))
            w_sum += rat * common
            t_w += common
        return (w_sum / t_w, min(t_w / 15, 1.0)) if t_w > 0 else (None, 0)

    def rate(self, user, movie):
        ub_val, ub_conf = self._user_based_score(user, movie)
        ib_val, ib_conf = self._item_based_score(user, movie)
        gn_val, gn_conf = self._genre_score(user, movie)

        scores = []
        if ub_val is not None: scores.append((ub_val, ub_conf * 2.5))
        if ib_val is not None: scores.append((ib_val, ib_conf * 2.5))
        if gn_val is not None: scores.append((gn_val, gn_conf * 1.0))

        if scores:
            final_num = sum(v * w for v, w in scores)
            final_den = sum(w for v, w in scores)
            return max(0.5, min(5.0, final_num / final_den))

        u_avg = self._get_user_mean(user.ratings)
        m_list = self.movie_ratings.get(movie, [])
        m_avg = sum(m_list) / len(m_list) if m_list else 2.5
        return (u_avg + m_avg) / 2.0

    def __str__(self):
        return 'System created by 155974, 155874 and 155879'