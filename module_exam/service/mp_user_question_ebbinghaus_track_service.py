from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from module_exam.dao.mp_user_question_ebbinghaus_track_dao import MpUserQuestionEbbinghausTrackDao
from module_exam.model.mp_user_question_ebbinghaus_track import MpUserQuestionEbbinghausTrackModel
from module_exam.service.base_service import BaseService

# 继承Service类，专注于业务操作, 可添加自定义方法
class MpUserQuestionEbbinghausTrackService(BaseService[MpUserQuestionEbbinghausTrackModel]):
    def __init__(self):
        """
        初始化服务实例
        创建DAO实例并传递给基类
        """
        self.dao_instance = MpUserQuestionEbbinghausTrackDao()
        super().__init__(dao=self.dao_instance)

    # 可以根据业务需求添加自定义方法


    """
    模拟考试的抽题逻辑(100道题) 
    :param user_id: 用户ID
    :param exam_id: 模拟考试ID
    :param choose_question_count: 要抽取的题目数
    :return: 题目ID列表
    
    按照优先级从高到低抽题。不足则从下一级补充，直到满足指定数量的题目。
    1. 当天复习题。 即下次复习时间为当天的待复习题目。
    2. 已过期待复习题。 即下次复习时间小于当天的待复习题目
    3. 未答题过的题目。 即没有在轨迹表中记录的题目
    4. 未到期待复习题。 即下次复习时间大于当天的待复习题目
    5. 已巩固题目（status=1,cycle_idx=-1）。 即已巩固的题目
    """

    def monikaoshi_choose_question_ids(self, db_session: Session, user_id: int, exam_id: int,choose_question_count: int):
        # 初始化题目ID集合，用于去重
        question_ids = set()

        # 定义抽题优先级和对应的DAO方法
        priority_methods = [
            self.dao_instance.get_today_review_question,  # 当天复习题
            self.dao_instance.get_expired_review_question,  # 已过期待复习题
            self.dao_instance.get_unanswered_review_question,  # 未答题过的题目
            self.dao_instance.get_no_expired_review_question,  # 未到期待复习题
            self.dao_instance.get_stable_review_question  # 已巩固题目
        ]

        # 按优先级顺序抽取题目
        for method in priority_methods:
            # 如果已经收集到足够的题目，就停止
            if len(question_ids) >= choose_question_count:
                break

            # 计算还需要的题目数量
            need_count = choose_question_count - len(question_ids)

            # 获取题目
            fetched_ids = method(db_session, user_id, exam_id, need_count)

            # 添加新题目到题目ID集合(自动去重)
            question_ids.update(fetched_ids)

        # 确保返回的题目数量正确
        if len(question_ids) > choose_question_count:
            question_ids = question_ids[:choose_question_count]

        # 如果最终还是没有收集到足够的题目，抛出异常
        if len(question_ids) < choose_question_count:
            raise Exception(f"抽题失败，无法收集到足够的题目。要求{choose_question_count}道，实际收集到{len(question_ids)}道")

        return question_ids


    def update_question_track(self,db_session: Session,user_id: int,question_id: int,question_type: int,is_correct: int) -> bool:
        """
        更新题目答题轨迹记录
        :param db_session: 数据库会话
        :param user_id: 用户ID
        :param question_id: 题目ID
        :param question_type: 题目类型
        :param is_correct: 是否答对 0:答错 1:答对
        :return: 是否更新成功
        """

        review_cycle_list = [0,1,3,7,14,30]

        # 先根据user_id,question_id查询该题目是否存在轨迹记录
        track_one = self.dao_instance.get_one_by_filters(
            db_session,
            filters={
                "user_id": user_id,
                "question_id": question_id,
            },
        )

        if not track_one:
            # 如果不存在轨迹记录，创建新记录
            self.dao_instance.add(db_session, dict_data=MpUserQuestionEbbinghausTrackModel(
                user_id=user_id,
                question_id=question_id,
                question_type=question_type,
                correct_count=1 if is_correct else 0,    # 答对次数
                error_count=1 if not is_correct else 0,  # 答错次数
                total_count=1,                       # 总答题次数
                last_answer_time=datetime.now(), # 最后一次答题时间
                status=0,       # 0:待复习 1:已巩固
                cycle_index=0,  # 复习周期索引初始化为0，-1表示已巩固，其他值表示待复习的复习周期索引
                next_review_time= datetime.now() + timedelta(days=review_cycle_list[0]),  # 下一次复习时间初始化为当前时间+复习周期对应的天数
            ).to_dict())

        else:
            # 根据答对/答错判断是否需要更新复习周期索引
            if is_correct:
                # 如果答对，复习周期索引+1
                new_cycle_index = track_one.cycle_index+1
            else:
                # 如果答错，复习周期索引重置为0
                new_cycle_index = 0

            # 如果复习周期索引超过了最大索引，说明已巩固，设置status为1，cycle_index为-1
            if new_cycle_index >= len(review_cycle_list):
                new_status = 1
                new_cycle_index = -1
            else:
                new_status = 0

            # 更新下一次复习时间
            if new_status == 0:
                new_next_review_time = datetime.now() + timedelta(days=review_cycle_list[new_cycle_index])
            else:
                new_next_review_time = None

            # 更新记录
            self.dao_instance.update_by_id(
                db_session,
                id=track_one.id,
                update_data=MpUserQuestionEbbinghausTrackModel(
                    correct_count=track_one.correct_count+1 if is_correct else track_one.correct_count, # 答对次数
                    error_count=track_one.error_count+1 if not is_correct else track_one.error_count, # 答错次数
                    total_count=track_one.total_count+1,                       # 总答题次数
                    last_answer_time=datetime.now(), # 最后一次答题时间
                    status=new_status,       # 0:待复习 1:已巩固
                    cycle_index=new_cycle_index,  # 复习周期索引初始化为0，-1表示已巩固，其他值表示待复习的复习周期索引
                    next_review_time= new_next_review_time,  # 下一次复习时间初始化为当前时间+复习周期对应的天数
                ).to_dict(),
            )
            return True








