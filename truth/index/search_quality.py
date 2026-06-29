"""5-note search regression gate — isolated temp notes + DB."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# ponytail: global env + singleton reset — acceptable for one regression module; Phase 9 may move to pytest

_CASES: list[tuple[str, str, str]] = [
    (
        "topics/quantum.md",
        "Quantum Entanglement",
        """Quantum entanglement links two or more particles so that measuring one instantly "
        "constrains the state of the other, regardless of distance. This non-local correlation "
        "was famously described by Einstein as spooky action at a distance, yet experiments "
        "confirm entangled particles violate Bell inequalities.\n\n"
        "Entangled photon pairs are produced in parametric down-conversion crystals. Each particle "
        "carries complementary polarization or spin. When one photon's polarization collapses "
        "upon measurement, its partner's outcome is determined. Quantum information protocols "
        "such as teleportation and quantum key distribution rely on entanglement fidelity.""",
    ),
    (
        "topics/baking.md",
        "Sourdough Bread",
        """Sourdough bread fermentation begins with a wild yeast and lactobacillus culture "
        "maintained as a starter. The starter feeds on flour and water, producing lactic and "
        "acetic acids that give sourdough its tang and extend shelf life without commercial yeast.\n\n"
        "Bulk fermentation develops gluten structure and flavor precursors. Shaping creates surface "
        "tension for oven spring. A long cold proof in the refrigerator slows fermentation for "
        "deeper flavor. Scoring the loaf before baking controls expansion. The crumb should show "
        "open holes from proper fermentation and strong gluten development.""",
    ),
    (
        "topics/gardening.md",
        "Tomato Companion Planting",
        """Tomato companion planting pairs tomatoes with herbs and flowers that deter pests or "
        "improve growth. Basil planted near tomatoes is said to repel aphids and whiteflies while "
        "possibly enhancing tomato flavor through shared root-zone chemistry.\n\n"
        "Marigolds release compounds that suppress nematodes in the soil around tomato roots. "
        "Avoid planting tomatoes near brassicas or fennel, which compete for nutrients. Carrots "
        "and tomatoes share space well when tomatoes provide shade for carrot roots. Rotate tomato "
        "beds annually to break disease cycles and maintain healthy companion planting benefits.""",
    ),
    (
        "topics/music.md",
        "Jazz Chord Progressions",
        """Jazz chord progressions extend functional harmony with ii-V-I turnarounds, tritone "
        "substitutions, and modal interchange. The ii-V-I in major keys (Dm7-G7-Cmaj7) is the "
        "backbone of countless jazz standards and bebop heads.\n\n"
        "Minor ii-V-i progressions use half-diminished and altered dominant chords. Coltrane "
        "changes cycle through descending major thirds. Rhythm changes borrow from I Got Rhythm "
        "for fast-moving chord sequences. Voice leading smooths transitions between chord "
        "progressions so each note moves by step or common tone.""",
    ),
    (
        "topics/hiking.md",
        "Mountain Trail Elevation",
        """Mountain trail elevation gain measures total vertical ascent along a hiking route, "
        "often exceeding the net difference between start and summit due to ups and downs. "
        "A trail with two thousand feet of elevation gain on a ten-mile loop demands pacing "
        "and hydration planning.\n\n"
        "Steep switchbacks reduce grade but add distance. Above treeline, elevation gain "
        "combines with thinner air to increase exertion. Trekking poles help on sustained "
        "descents after long elevation gain days. Track cumulative elevation gain in a GPS "
        "watch or topo map profile before committing to a mountain trail.""",
    ),
]


def run_search_quality_check() -> None:
    import truth.index.db as db_module
    from truth.index.indexer import index_all
    from truth.index.search import memory_search
    from truth.tools.write import memory_write

    queries = {
        "topics/quantum.md": "quantum entanglement particles",
        "topics/baking.md": "sourdough bread fermentation",
        "topics/gardening.md": "tomato companion planting",
        "topics/music.md": "jazz chord progressions",
        "topics/hiking.md": "mountain trail elevation gain",
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        os.environ["TRUTH_NOTES_ROOT"] = str(tmp_path)
        os.environ["TRUTH_DB_PATH"] = str(tmp_path / "memory.db")
        db_module._CONN = None

        for path, title, body in _CASES:
            memory_write(path, body, title=title)

        indexed = index_all(tmp_path)
        assert indexed >= len(_CASES), f"expected >={len(_CASES)} indexed, got {indexed}"

        for expected_path, query in queries.items():
            hits = memory_search(query, k=5)
            assert hits, f"no hits for query {query!r}"
            top = hits[0]["path"]
            assert top == expected_path or top.endswith(expected_path), (
                f"query {query!r}: expected {expected_path!r} at rank 1, got {top!r} (hits={hits!r})"
            )


if __name__ == "__main__":
    run_search_quality_check()
    print("search_quality=ok")
