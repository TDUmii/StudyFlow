from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from app.i18n import tr


class StudyCharts(FigureCanvasQTAgg):
    def __init__(self):
        self.figure = Figure(figsize=(8, 3), facecolor="#FFFFFF", tight_layout=True)
        super().__init__(self.figure)
        self.setMinimumHeight(280)

    def update_data(self, by_subject: dict[str, int], by_day: dict[str, int]):
        self.figure.clear()
        left, right = self.figure.subplots(1, 2)
        if by_subject:
            names = list(by_subject)
            values = [by_subject[name] for name in names]
            left.bar(names, values, color="#6366F1")
            left.tick_params(axis="x", rotation=25, labelsize=8)
            left.set_title(tr("chart.study_subject"))
            left.set_ylabel(tr("chart.minutes"))
        else:
            left.text(0.5, 0.5, tr("chart.no_subject"), ha="center", va="center")
            left.set_axis_off()
        if by_day:
            days = sorted(by_day)[-7:]
            right.plot(
                [day[5:] for day in days],
                [by_day[day] for day in days],
                marker="o",
                color="#22C55E",
                linewidth=2,
            )
            right.set_title(tr("chart.study_activity"))
            right.set_ylabel(tr("chart.minutes"))
            right.tick_params(axis="x", rotation=25, labelsize=8)
        else:
            right.text(0.5, 0.5, tr("chart.no_history"), ha="center", va="center")
            right.set_axis_off()
        for axis in (left, right):
            axis.spines[["top", "right"]].set_visible(False)
            axis.grid(axis="y", alpha=0.15)
        self.figure.tight_layout()
        self.draw_idle()
