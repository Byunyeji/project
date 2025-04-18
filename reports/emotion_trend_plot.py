import pandas as pd
import matplotlib.pyplot as plt
from .generate_report import get_emotion_report
import os
import matplotlib.font_manager as fm

# 폰트 다운로드 및 설정
font_dir = "./fonts"
font_path = os.path.join(font_dir, "malgun.ttf")
os.makedirs(font_dir, exist_ok=True)

if os.path.exists(font_path):
    fontprop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = fontprop.get_name()
    plt.rcParams["axes.unicode_minus"] = False
else:
    fontprop = None 


def plot_emotion_trend(login_id: str, start_date, end_date) -> plt.Figure | None:
    df = get_emotion_report(login_id)
    df["분석 날짜"] = pd.to_datetime(df["분석 날짜"]).dt.date
    df = df[(df["분석 날짜"] >= start_date) & (df["분석 날짜"] <= end_date)]

    if df.empty:
        return None

    # 날짜별 감정 비율 계산
    total_per_day = df.groupby("분석 날짜").size().reset_index(name="총합")
    emotion_per_day = df.groupby(["분석 날짜", "감정 카테고리"]).size().reset_index(name="건수")

    merged = pd.merge(emotion_per_day, total_per_day, on="분석 날짜")
    merged["비율"] = (merged["건수"] / merged["총합"]) * 100

    pivot = merged.pivot(index="분석 날짜", columns="감정 카테고리", values="비율").fillna(0)

    if pivot.empty:
        return None

    fig, ax = plt.subplots(figsize=(6, 5))
    pivot.plot(ax=ax)

    # 제목 및 라벨 (한글 폰트 적용)
    if fontprop:
        ax.set_xlabel("", fontproperties=fontprop)
        ax.set_ylabel("", fontproperties=fontprop)
        ax.legend(title="", prop=fontprop)
    else:
        ax.set_xlabel("날짜")
        ax.set_ylabel("")

    # x축 포맷 MM/DD로
    ax.set_xticks(pivot.index)
    ax.set_xticklabels(
        [d.strftime("%m/%d") for d in pivot.index],
        rotation=0,
        fontproperties=fontprop if fontprop else None
    )

    # y축 0~100, 20단위로
    ax.set_yticks(range(0, 105, 20))
    ax.set_ylim(0, 100)
    ax.annotate(
        "(%)",
        xy=(0.01, 1.02),
        xycoords="axes fraction",
        ha="left",
        va="bottom",
        fontsize=12,
        fontproperties=fontprop
        )
    
    ax.legend(
    loc='upper center',
    bbox_to_anchor=(0.5, -0.15),  # x=가운데, y=아래로 약간 내리기
    ncol=len(pivot.columns),      # 감정 카테고리 수만큼 가로 정렬
    frameon=False,                # 테두리 제거 (선택)
    prop=fontprop if fontprop else None
)
    plt.tight_layout(pad=2.0)   
    return fig

