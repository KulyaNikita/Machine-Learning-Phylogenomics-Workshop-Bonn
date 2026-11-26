#!/usr/bin/env python3
"""Save a PDF cladogram of a vertebrate Newick tree rooted on the dataset's shark.

Usage: python3 visualise_tree.py TREE [--output PREFIX] [--show]
Requires Biopython and Matplotlib.
"""

import argparse
from pathlib import Path

from Bio import Phylo


GROUPS = {
    "Monotremes": ("#a14a17", {"platypus"}),
    "Other mammals": ("#8b4c9b", {"kangaroo", "opossum", "elephant", "armadillo", "dog", "human", "mouse"}),
    "Birds and reptiles": ("#287e64", {"lizard", "turtle", "zebrafinch", "chicken", "turkey"}),
    "Amphibians": ("#8a761e", {"frog"}),
    "Lungfishes and coelacanth": ("#287f9e", {"Australian-lungfish", "African-lungfish", "American-lungfish", "coelacanth"}),
    "Ray-finned fishes": ("#3e64a0", {"gar", "zebrafish", "pufferfish", "tilapia"}),
    "Cartilaginous fishes": ("#626a75", {"shark"}),
}
OUTGROUP = "shark_Callorhinchus_milii"


def taxon_style(name):
    common, _, scientific = name.partition("_")
    for group, (color, taxa) in GROUPS.items():
        if common in taxa:
            break
    else:
        group, color = "Other taxa", "#626a75"
    label = common.replace("-", " ").capitalize()
    if scientific:
        label += "  ·  " + scientific.replace("_", " ")
    return label, group, color


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path, help="Newick tree with the workshop taxon identifiers")
    parser.add_argument("--output", type=Path, help="PDF output prefix (default: TREE_shark_rooted)")
    parser.add_argument("--show", action="store_true", help="Also open an interactive Matplotlib window")
    args = parser.parse_args()

    try:
        tree = Phylo.read(args.tree, "newick")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    tips = tree.get_terminals()
    names = [tip.name for tip in tips]
    if any(not name for name in names) or len(set(names)) != len(names):
        parser.error("Every tip must have a unique, nonempty taxon name.")
    if OUTGROUP not in names:
        parser.error(f"Shark outgroup missing: {OUTGROUP}")
    tree.root_with_outgroup(next(tip for tip in tips if tip.name == OUTGROUP))
    tree.ladderize(reverse=True)

    import matplotlib
    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    tips = tree.get_terminals()
    # A cladogram keeps topology legible even when branch lengths are absent or uneven.
    x = tree.depths(unit_branch_lengths=True)
    y = {tip: i for i, tip in enumerate(tips)}
    for clade in tree.get_nonterminals(order="postorder"):
        y[clade] = (y[clade.clades[0]] + y[clade.clades[-1]]) / 2
    styles = {tip: taxon_style(tip.name) for tip in tips}
    present_groups = {style[1] for style in styles.values()}
    max_depth = max(x.values())
    label_x = max_depth + 0.5

    fig, ax = plt.subplots(figsize=(15, max(7, len(tips) * 0.38 + 2.4)))
    fig.patch.set_facecolor("#fafbf9")
    ax.set_facecolor("#fafbf9")
    for tip in tips:
        label, _, color = styles[tip]
        if tip.name == OUTGROUP:
            ax.axhspan(y[tip] - 0.45, y[tip] + 0.45, color="#fae8d7", zorder=0)
        ax.plot([x[tip], label_x - 0.12], [y[tip], y[tip]], color="#d3d9dc", lw=0.8, ls=(0, (2, 3)))
        ax.scatter(x[tip], y[tip], s=25, color=color, zorder=4)
        ax.text(label_x, y[tip], label, va="center", fontsize=10.5, color=color,
                weight="bold" if tip.name == OUTGROUP else "normal")

    for clade in tree.find_clades():
        if clade.clades:
            ax.plot([x[clade], x[clade]], [y[clade.clades[0]], y[clade.clades[-1]]],
                    color="#465563", lw=1.5)
        for child in clade.clades:
            ax.plot([x[clade], x[child]], [y[child], y[child]], color="#465563", lw=1.5)
            if child.confidence is not None and not child.is_terminal():
                ax.annotate(f"{child.confidence:g}", (x[child], y[child]), xytext=(-4, 5),
                            textcoords="offset points", ha="right", fontsize=8, color="#66717c")

    ax.set_xlim(-0.3, label_x + 10)
    ax.set_ylim(len(tips) - 0.4, -1)
    ax.axis("off")
    fig.suptitle("Vertebrate phylogeny", x=0.055, y=0.97, ha="left", fontsize=24,
                 weight="bold", color="#233744")
    fig.text(0.055, 0.927, "Rooted on shark · Callorhinchus milii", fontsize=12, color="#6d502d")
    handles = [Line2D([], [], marker="o", ls="", color=color, label=group)
               for group, (color, _) in GROUPS.items() if group in present_groups]
    if "Other taxa" in present_groups:
        handles.append(Line2D([], [], marker="o", ls="", color="#626a75", label="Other taxa"))
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.05, 0.045),
               ncol=4, frameon=False, fontsize=9, handletextpad=0.4, columnspacing=1.8)
    fig.text(0.055, 0.025, "Cladogram: branch lengths are not shown.  |  Source: " + args.tree.name,
             fontsize=9, color="#6b7880")
    fig.subplots_adjust(left=0.055, right=0.99, top=0.89, bottom=0.15)

    prefix = args.output or args.tree.with_name(args.tree.stem + "_shark_rooted")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    output = Path(str(prefix) + ".pdf")
    fig.savefig(output, facecolor=fig.get_facecolor())
    print(f"Saved {output}")
    if args.show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
