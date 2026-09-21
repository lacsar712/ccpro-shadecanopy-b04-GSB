"""气候日志双签（记录人/复核人）同源口径。

四处共用本模块，保证判定一致：
1. 气候新建/更新的双签校验（validate_dual_sign，失败返回 400）；
2. 气候列表缺签过滤（unsigned_climate_logs）；
3. 新建轮灌的缺签拦截（is_zone_irrigation_blocked）；
4. 看板缺签条数与禁灌分区数（unsigned_climate_logs / unsigned_climate_zone_ids）。
"""

from django.db.models import Q
from rest_framework import serializers

from .models import ClimateLog

SIGN_MIN_LEN = 2

# 仅空白字符（与 Python str.strip() 口径对齐）；PostgreSQL 与 SQLite 均支持 \s。
_WS_ONLY_RE = r"^\s*$"


def normalize_sign(value):
    """签名去空白；None 视为空串。"""
    return (value or "").strip()


def is_unsigned(recorder, reviewer):
    """Python 侧缺签判定：记录人或复核人去空白后为空。"""
    return not normalize_sign(recorder) or not normalize_sign(reviewer)


def validate_dual_sign(recorder, reviewer):
    """双签校验：去空白后均至少 2 字且不得相同。

    新建与更新气候日志共用本函数；校验失败抛 serializers.ValidationError（DRF 返回 400）。
    通过时返回去空白后的 (recorder, reviewer)。
    """
    recorder = normalize_sign(recorder)
    reviewer = normalize_sign(reviewer)
    errors = {}
    if len(recorder) < SIGN_MIN_LEN:
        errors["recorder"] = f"记录人去空白后至少 {SIGN_MIN_LEN} 字"
    if len(reviewer) < SIGN_MIN_LEN:
        errors["reviewer"] = f"复核人去空白后至少 {SIGN_MIN_LEN} 字"
    if not errors and recorder == reviewer:
        errors["reviewer"] = "记录人与复核人不得相同"
    if errors:
        raise serializers.ValidationError(errors)
    return recorder, reviewer


def unsigned_climate_logs(queryset=None):
    """缺签气候日志口径（DB 侧）：记录人或复核人去空白后为空。"""
    qs = queryset if queryset is not None else ClimateLog.objects.all()
    return qs.filter(Q(recorder__regex=_WS_ONLY_RE) | Q(reviewer__regex=_WS_ONLY_RE))


def unsigned_climate_zone_ids():
    """存在缺签气候日志的分区 id 子查询（禁灌/看板共用）。"""
    return unsigned_climate_logs().order_by().values("zone_id").distinct()


def is_zone_irrigation_blocked(zone_id):
    """该分区存在缺签气候 → 禁止新建轮灌；无缺签行时不拦。"""
    return unsigned_climate_logs().filter(zone_id=zone_id).exists()
