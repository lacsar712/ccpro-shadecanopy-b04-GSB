"""
双签与缺签的唯一口径来源（single source of truth）。

- 双签校验：记录人与复核人去空白后都至少 2 字，且不得相同。
  新建与更新气候日志必须共用 validate_dual_signature。
- 缺签判定：missing_signature_logs / blocked_zone_ids 同时服务于
  气候列表缺签过滤、轮灌新建拦截、仪表盘两项指标，保证四处口径同源。
"""
from django.db.models import Q

# 去空白后的最小字符数
MIN_SIGNATURE_LENGTH = 2


def _clean(value):
    """签名统一口径：None 安全，去首尾空白。"""
    return (value or "").strip()


def validate_dual_signature(recorder_name, reviewer_name):
    """
    校验双签。返回清洗后的 (recorder, reviewer)；不合规抛 ValueError。

    规则（记录人 recorder_name / 复核人 reviewer_name 完全对称）：
    1. 去空白后都至少 2 字；
    2. 两人去空白后不得相同。
    """
    recorder = _clean(recorder_name)
    reviewer = _clean(reviewer_name)
    errors = {}

    if len(recorder) < MIN_SIGNATURE_LENGTH:
        errors["recorderName"] = "记录人去空白后至少 2 个字"
    if len(reviewer) < MIN_SIGNATURE_LENGTH:
        errors["reviewerName"] = "复核人去空白后至少 2 个字"
    if recorder and reviewer and recorder == reviewer:
        errors["non_field_errors"] = "记录人与复核人不得相同"

    if errors:
        raise ValueError(errors)
    return recorder, reviewer


def missing_signature_logs(queryset=None):
    """
    缺签气候记录：记录人或复核人去空白后为空。
    接受可选 queryset 以复用列表的 zoneId 等过滤条件，但缺签判定只由此处定义。
    """
    from .models import ClimateLog

    qs = queryset if queryset is not None else ClimateLog.objects.all()
    return qs.filter(
        Q(recorder_name__isnull=True)
        | Q(recorder_name__exact="")
        | Q(reviewer_name__isnull=True)
        | Q(reviewer_name__exact="")
    )


def blocked_zone_ids(queryset=None):
    """
    因缺签被禁灌的分区 id：至少存在一条缺签气候记录的分区（去重）。
    轮灌新建拦截与仪表盘「被禁灌区数」共用本函数。
    """
    return (
        missing_signature_logs(queryset)
        .values_list("zone_id", flat=True)
        .distinct()
    )
