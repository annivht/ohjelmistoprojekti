import json

class Leaderboard:
    def __init__(self):
        self.scores = {}

    def add_score(self, player_id: int, score: int) -> None:
        if player_id in self.scores:
            if score > self.scores[player_id]:
                self.scores[player_id] = score
        else:
            self.scores[player_id] = score

    def top(self, K: int) -> int:
        return sum(sorted(self.scores.values(), reverse=True)[:K])

    def reset(self, player_id: int) -> None:
        if player_id in self.scores:
            del self.scores[player_id]
    
    def reset_all(self) -> None:
        self.scores.clear()

    def get_score(self, player_id: int) -> int:
        return self.scores.get(player_id, 0)
    
    def get_all_scores(self) -> dict:
        return self.scores.copy()
    
    def __str__(self) -> str:
        return str(self.scores)
    
    def __repr__(self) -> str:
        return f"Leaderboard(scores={self.scores})"
    
    def get_top_players(self, K: int) -> list:
        return sorted(self.scores.items(), key=lambda item: item[1], reverse=True)[:K]
    
    def get_player_rank(self, player_id: int) -> int:
        sorted_scores = sorted(self.scores.items(), key=lambda item: item[1], reverse=True)
        for rank, (pid, score) in enumerate(sorted_scores, start=1):
            if pid == player_id:
                return rank
        return -1  # Player not found
    
    def get_player_score(self, player_id: int) -> int:
        return self.scores.get(player_id, 0)
    
    def get_average_score(self) -> float:
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)
    
    def get_median_score(self) -> float:
        if not self.scores:
            return 0.0
        sorted_scores = sorted(self.scores.values())
        n = len(sorted_scores)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_scores[mid - 1] + sorted_scores[mid]) / 2
        else:
            return sorted_scores[mid]
        
    def get_highest_score(self) -> int:
        if not self.scores:
            return 0
        return max(self.scores.values())
    
    def get_lowest_score(self) -> int:
        if not self.scores:
            return 0
        return min(self.scores.values())
    
    def get_score_distribution(self) -> dict:
        distribution = {}
        for score in self.scores.values():
            distribution[score] = distribution.get(score, 0) + 1
        return distribution
    
    def get_player_scores(self) -> dict:
        return self.scores.copy()
    
    def clear_leaderboard(self) -> None:
        self.scores.clear()

    def save_to_file(self, filename: str) -> None:
        try:
            with open(filename, 'w') as file:
                json.dump(self.scores, file)
        except Exception as e:
            print(f"Virhe tallennettaessa tiedostoon: {e}")

    def load_from_file(self, filename: str) -> None:
        self.scores.clear()
        try:
            with open(filename, 'r') as file:
                self.scores = json.load(file)
        except Exception as e:
            print(f"Virhe ladattaessa tiedostosta: {e}")
            with open(filename, 'w') as file:
                json.dump({}, file)
                self.scores = {}

    def merge_leaderboard(self, other_leaderboard) -> None:
        for player_id, score in other_leaderboard.get_player_scores().items():
            self.add_score(player_id, score)
    
    def get_top_n_players(self, n: int) -> list:
        return sorted(self.scores.items(), key=lambda item: item[1], reverse=True)[:n]
    
    def get_bottom_n_players(self, n: int) -> list:
        return sorted(self.scores.items(), key=lambda item: item[1])[:n]
    
    def get_player_count(self) -> int:
        return len(self.scores)
    
    def get_total_score(self) -> int:
        return sum(self.scores.values())
    
    def get_average_score_per_player(self) -> float:
        if not self.scores:
            return 0.0
        return self.get_total_score() / self.get_player_count()
    
    def get_score_percentile(self, player_id: int) -> float:
        if player_id not in self.scores:
            return 0.0
        player_score = self.scores[player_id]
        count_below = sum(1 for score in self.scores.values() if score < player_score)
        return (count_below / self.get_player_count()) * 100
    
    def get_score_rank(self, player_id: int) -> int:
        if player_id not in self.scores:
            return -1
        sorted_scores = sorted(self.scores.values(), reverse=True)
        player_score = self.scores[player_id]
        return sorted_scores.index(player_score) + 1
    
    def get_score_histogram(self) -> dict:
        histogram = {}
        for score in self.scores.values():
            histogram[score] = histogram.get(score, 0) + 1
        return histogram
    
    def get_score_summary(self) -> dict:
        return {
            'total_players': self.get_player_count(),
            'total_score': self.get_total_score(),
            'average_score': self.get_average_score(),
            'median_score': self.get_median_score(),
            'highest_score': self.get_highest_score(),
            'lowest_score': self.get_lowest_score()
        }
    
    def get_top_player(self) -> tuple:
        if not self.scores:
            return None
        top_player_id = max(self.scores, key=self.scores.get)
        return (top_player_id, self.scores[top_player_id])
    
    def get_bottom_player(self) -> tuple:
        if not self.scores:
            return None
        bottom_player_id = min(self.scores, key=self.scores.get)
        return (bottom_player_id, self.scores[bottom_player_id])
    
    def get_player_rankings(self) -> list:
        return sorted(self.scores.items(), key=lambda item: item[1], reverse=True)
    
    def get_score_percentiles(self) -> dict:
        percentiles = {}
        for player_id in self.scores:
            percentiles[player_id] = self.get_score_percentile(player_id)
        return percentiles
    
    def get_score_ranks(self) -> dict:
        ranks = {}
        for player_id in self.scores:
            ranks[player_id] = self.get_score_rank(player_id)
        return ranks
    
    def get_score_histogram_bins(self, bin_size: int) -> dict:
        histogram = {}
        for score in self.scores.values():
            bin_key = (score // bin_size) * bin_size
            histogram[bin_key] = histogram.get(bin_key, 0) + 1
        return histogram
    
    def get_score_summary_statistics(self) -> dict:
        return {
            'total_players': self.get_player_count(),
            'total_score': self.get_total_score(),
            'average_score': self.get_average_score(),
            'median_score': self.get_median_score(),
            'highest_score': self.get_highest_score(),
            'lowest_score': self.get_lowest_score(),
            'score_distribution': self.get_score_distribution()
        }
    
    def get_top_n_scores(self, n: int) -> list:
        return sorted(self.scores.values(), reverse=True)[:n]
    
    def get_bottom_n_scores(self, n: int) -> list:
        return sorted(self.scores.values())[:n]
    
    def get_score_percentile_rank(self, player_id: int) -> float:
        if player_id not in self.scores:
            return 0.0
        player_score = self.scores[player_id]
        count_below = sum(1 for score in self.scores.values() if score < player_score)
        count_equal = sum(1 for score in self.scores.values() if score == player_score)
        return ((count_below + 0.5 * count_equal) / self.get_player_count()) * 100
    
    def get_score_z_score(self, player_id: int) -> float:
        if player_id not in self.scores:
            return 0.0
        player_score = self.scores[player_id]
        average_score = self.get_average_score()
        std_dev = (sum((score - average_score) ** 2 for score in self.scores.values()) / self.get_player_count()) ** 0.5
        if std_dev == 0:
            return 0.0
        return (player_score - average_score) / std_dev
