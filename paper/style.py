import matplotlib as mpl
mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 9.5,
    "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#8a8a85",
    "axes.grid": True, "grid.color": "#e6e5e0", "grid.linewidth": 0.6, "axes.axisbelow": True,
    "lines.linewidth": 2, "savefig.dpi": 300, "savefig.bbox": "tight", "figure.dpi": 110,
    "text.color": "#1f1f1d", "axes.labelcolor": "#1f1f1d", "xtick.color": "#4a4a46", "ytick.color": "#4a4a46"})
COL = {"A": "#2a78d6", "A*": "#eb6834", "B": "#1baf7a", "C": "#eda100", "random": "#8a8a85",
       "adaptive": "#2a78d6", "cover": "#b9b8b2"}
MRK = {"A": "o", "A*": "s", "B": "^", "C": "D", "adaptive": "o", "random": "s"}
NAME = {"A": "A: base (α=0.05)", "A*": "A*: base (α=0.06)", "B": "B: adaptive α", "C": "C: A + hidden layer"}
def save(fig, stem):
    from pipeline import FIG
    fig.savefig(FIG / f"{stem}.png"); fig.savefig(FIG / f"{stem}.pdf")
