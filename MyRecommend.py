import numpy as np
from collections import defaultdict
import heapq


class MyRecommend:
    def __init__(self):
        pass

    def get_recommend_music_title_list(target_user_id, top_k):
        # 加载数据
        user_dict_list = list()
        with open(r"data\users.txt", "r", encoding="utf-8") as f:
            line_list = f.readlines()
            # 舍去标题行
            line_list.pop(0)
            for line in line_list:
                user_dict = {"user_id": line.split()[0], "user_name": line.split()[1]}
                user_dict_list.append(user_dict)

        song_dict_list = list()
        with open(r"data\songs.txt", "r", encoding="utf-8") as f:
            line_list = f.readlines()
            # 舍去标题行
            line_list.pop(0)
            for line in line_list:
                song_dict = {"song_id": line.split()[0], "song_name": line.split()[1]}
                song_dict_list.append(song_dict)

        count_dict_list = list()
        with open(r"data\count.txt", "r", encoding="utf-8") as f:
            line_list = f.readlines()
            # 舍去标题行
            line_list.pop(0)
            for line in line_list:
                count_dict = {
                    "user_id": line.split()[0],
                    "song_id": line.split()[1],
                    "count": line.split()[2],
                }
                count_dict_list.append(count_dict)

        # 构建用户-歌曲矩阵
        user_song_matrix = defaultdict(dict)
        for count_dict in count_dict_list:
            user_id = count_dict["user_id"]
            song_id = count_dict["song_id"]
            count = int(count_dict["count"])
            user_song_matrix[user_id][song_id] = count

        # 获取用户ID列表
        user_ids = [user["user_id"] for user in user_dict_list]
        num_users = len(user_ids)
        # 获取歌曲ID列表
        song_ids = [song["song_id"] for song in song_dict_list]
        num_songs = len(song_ids)

        # 构建用户ID到索引的映射
        user_id_to_idx = {user_id: idx for idx, user_id in enumerate(user_ids)}
        # 构建歌曲ID到索引的映射
        song_id_to_idx = {song_id: idx for idx, song_id in enumerate(song_ids)}

        # 将用户-歌曲矩阵转换为NumPy数组
        user_song_array = np.zeros((num_users, num_songs))
        for user_id, song_counts in user_song_matrix.items():
            user_idx = user_id_to_idx[user_id]
            for song_id, count in song_counts.items():
                song_idx = song_id_to_idx.get(song_id)
                if song_idx is not None:
                    user_song_array[user_idx, song_idx] = count

        # 计算用户相似度矩阵（余弦相似度）
        # 归一化矩阵
        norms = np.linalg.norm(user_song_array, axis=1, keepdims=True)
        # 考虑零向量
        norms[norms == 0] = 1
        # 计算矩阵点积
        user_similarity = np.matmul(user_song_array, user_song_array.T) / (
            norms * norms.T
        )

        # 找到最相似的10个用户
        target_user_idx = user_id_to_idx[target_user_id]
        # 获取相似用户及其相似度
        similar_users = []
        for idx in range(num_users):
            if idx != target_user_idx:
                similarity = user_similarity[target_user_idx, idx]
                similar_users.append((idx, similarity))
        # 相似度排序
        similar_users.sort(key=lambda x: x[1], reverse=True)
        similar_user_indices = [idx for idx, _ in similar_users[:10]]

        # 获取已听歌曲
        target_user_songs = set()
        target_user_idx = user_id_to_idx[target_user_id]
        for song_idx in range(num_songs):
            if user_song_array[target_user_idx, song_idx] > 0:
                target_user_songs.add(song_idx)

        # 计算未听歌曲的推荐分数
        song_recommendation_scores = {}
        for user_idx in similar_user_indices:
            similarity = user_similarity[target_user_idx, user_idx]
            for song_idx in range(num_songs):
                if (
                    song_idx not in target_user_songs
                    and user_song_array[user_idx, song_idx] > 0
                ):
                    # 累加相似用户对该歌曲的听歌次数乘以相似度的加权值
                    similarity_weight = similarity  # 直接使用相似度作为权重
                    song_recommendation_scores[song_idx] = (
                        song_recommendation_scores.get(song_idx, 0)
                        + (user_song_array[user_idx, song_idx] * similarity_weight)
                    )

        # 按推荐分数排序
        recommended_song_indices = heapq.nlargest(
            top_k,
            song_recommendation_scores.keys(),
            key=lambda x: song_recommendation_scores[x],
        )

        # 将歌曲索引转换为歌曲ID和名称
        recommended_songs = []
        for song_idx in recommended_song_indices:
            song_id = song_ids[song_idx]
            song_name = next(
                (
                    song["song_name"]
                    for song in song_dict_list
                    if song["song_id"] == song_id
                ),
                "未知歌曲",
            )
            recommended_songs.append(
                (song_id, song_name, song_recommendation_scores[song_idx])
            )

        return recommended_songs


if __name__ == "__main__":
    target_user_id = "66"
    recommended_songs = MyRecommend.get_recommend_music_title_list(
        target_user_id, top_k=30
    )

    recommended_music_name_list = list()
    for song_id, song_name, score in recommended_songs:
        recommended_music_name_list.append(song_name)

    print(recommended_music_name_list)
