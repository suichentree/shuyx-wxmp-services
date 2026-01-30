from typing import List

from base.base_dao import BaseDao
from module_exam.model.mp_user_question_ebbinghaus_track import MpUserQuestionEbbinghausTrackModel


# 继承BaseDao类，专注于数据访问操作, 可添加自定义方法
class MpUserQuestionEbbinghausTrackDao(BaseDao[MpUserQuestionEbbinghausTrackModel]):
    def __init__(self):
        """初始化DAO实例"""
        super().__init__(model = MpUserQuestionEbbinghausTrackModel)

    # 可以根据业务需求添加自定义方法

    # 查询今日需要复习的题目ID列表，最多返回question_count个题目
    def get_today_review_question(self,db_session,user_id,exam_id,question_count):
        # 该sql主要是查询，轨迹表中，某个用户在某个试题中，今日需要复习的题目ID列表。
        # 根据最后答题时间升序，先复习最近答题的题目
        sql =   """
                SELECT qtrack.question_id FROM mp_user_question_ebbinghaus_track qtrack 
                LEFT JOIN mp_question q ON qtrack.question_id = q.id 
                WHERE qtrack.user_id = :user_id AND q.exam_id = :exam_id
                AND qtrack.next_review_time = CURDATE() 
                AND qtrack.status = 0
                ORDER BY qtrack.last_answer_time
                """
        params = {"user_id": user_id, "exam_id": exam_id}
        # 执行SQL查询，返回结果列表
        results: List[dict] = self.get_list_by_execute_sql(db_session, sql, params)
        # 提取question_id字段，转换为整数列表
        question_ids = [result["question_id"] for result in results]

        # 只取前question_count个题目
        if len(question_ids) > question_count:
            question_ids = question_ids[:question_count]

        return question_ids


    # 查询已过期的复习题目ID列表，最多返回question_count个题目
    def get_expired_review_question(self,db_session,user_id,exam_id,question_count):
        # 该sql主要是查询，轨迹表中，某个用户在某个试题中，已过期的复习题目ID列表
        # 根据最后答题时间升序，先复习最近答题的题目
        sql =   """
                SELECT qtrack.question_id FROM mp_user_question_ebbinghaus_track qtrack 
                LEFT JOIN mp_question q ON qtrack.question_id = q.id 
                WHERE qtrack.user_id = :user_id AND q.exam_id = :exam_id
                AND qtrack.next_review_time < CURDATE() 
                AND qtrack.status = 0
                ORDER BY qtrack.last_answer_time
                """
        params = {"user_id": user_id, "exam_id": exam_id}
        # 执行SQL查询，返回结果列表
        results: List[dict] = self.get_list_by_execute_sql(db_session, sql, params)
        # 提取question_id字段，转换为整数列表
        question_ids = [result["question_id"] for result in results]

        # 只取前question_count个题目
        if len(question_ids) > question_count:
            question_ids = question_ids[:question_count]

        return question_ids

    # 查询未在轨迹表中记录的题目ID列表，最多返回question_count个题目
    def get_unanswered_review_question(self,db_session,user_id,exam_id,question_count):
        # 该sql主要是查询，轨迹表中，某个用户在考试中，未在轨迹表中记录的题目ID列表
        # 根据题目ID升序，先复习题目ID较小的题目
        sql =   """
                    SELECT q.id as question_id
                    FROM mp_question q 
                    WHERE q.exam_id = :exam_id 
                    AND q.id NOT IN (
                        SELECT qtrack.question_id 
                        FROM mp_user_question_ebbinghaus_track qtrack 
                        WHERE qtrack.user_id = :user_id
                    )
                    ORDER BY q.id
                """
        params = {"user_id": user_id, "exam_id": exam_id}
        # 执行SQL查询，返回结果列表
        results: List[dict] = self.get_list_by_execute_sql(db_session, sql, params)
        # 提取question_id字段，转换为整数列表
        question_ids = [result["question_id"] for result in results]

        # 只取前question_count个题目
        if len(question_ids) > question_count:
            question_ids = question_ids[:question_count]

        return question_ids

    # 查询未到期待复习的题目ID列表，最多返回question_count个题目
    def get_no_expired_review_question(self,db_session,user_id,exam_id,question_count):
        # 该sql主要是查询，轨迹表中，某个用户在某个试题中，未到期待复习的题目ID列表
        # 根据最后答题时间升序，先复习最近答题的题目
        sql = """
                SELECT qtrack.question_id FROM mp_user_question_ebbinghaus_track qtrack 
                LEFT JOIN mp_question q ON qtrack.question_id = q.id 
                WHERE qtrack.user_id = :user_id AND q.exam_id = :exam_id
                AND qtrack.next_review_time > CURDATE() 
                AND qtrack.status = 0
                ORDER BY qtrack.last_answer_time
                """
        params = {"user_id": user_id, "exam_id": exam_id}
        # 执行SQL查询，返回结果列表
        results: List[dict] = self.get_list_by_execute_sql(db_session, sql, params)
        # 提取question_id字段，转换为整数列表
        question_ids = [result["question_id"] for result in results]

        # 只取前question_count个题目
        if len(question_ids) > question_count:
            question_ids = question_ids[:question_count]

        return question_ids

    # 查询已巩固的题目ID列表，最多返回question_count个题目
    def get_stable_review_question(self,db_session,user_id,exam_id,question_count):
        # 该sql主要是查询，轨迹表中，某个用户在某个试题中，已巩固的题目ID列表(status=1,cycle_idx=-1)
        # 根据最后答题时间升序，先复习最近答题的巩固题目
        sql = """
                SELECT qtrack.question_id FROM mp_user_question_ebbinghaus_track qtrack 
                LEFT JOIN mp_question q ON qtrack.question_id = q.id 
                WHERE qtrack.user_id = :user_id AND q.exam_id = :exam_id
                AND qtrack.status = 1
                AND qtrack.cycle_index = -1
                ORDER BY qtrack.last_answer_time
                """
        params = {"user_id": user_id, "exam_id": exam_id}
        # 执行SQL查询，返回结果列表
        results: List[dict] = self.get_list_by_execute_sql(db_session, sql, params)
        # 提取question_id字段，转换为整数列表
        question_ids = [result["question_id"] for result in results]

        # 只取前question_count个题目
        if len(question_ids) > question_count:
            question_ids = question_ids[:question_count]

        return question_ids
