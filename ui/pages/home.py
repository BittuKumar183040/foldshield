import streamlit as st
from services import state
import html
from ui.components import card_row, page_header, section, stat_card
from ui.html import fmt
from ui.route import go
from ui.theme import score_color

def render() -> None:
    page_header("Protein Similarity Platform", "FoldShield++ detects mutation impact, fold switching, and conformational shifts using symbolic topology – catching what TM-score, RMSD, and LDDT systematically miss.")

    left, right = st.columns(2)
    with left, st.container(border=False):
        st.subheader("Analyze")
        st.write("Upload two PDB files and run the similarity pipeline.")
        if st.button("Open analyzer", type="primary", key="home_analyze"):
            go("analyze")
    with right, st.container(border=True):
        st.subheader("Proteins")
        st.write("Browse stored structures and open them in 3D.")
        if st.button("Browse proteins", key="home_proteins"):
            go("proteins")

    result = state.get_result()
    fusion = ((result.summary or {}).get("fusion") or {}) if result else {}
    if fusion:
        st.divider()
        section("Latest run")
        score = fusion.get("combined_score")
        card_row(stat_card("Combined score", fmt(score, ".4f"), score_color(score), center=False, size="xl", sub=str(fusion.get("overall", ""))))
        if st.button("View full results", key="home_results"):
            go("analyze")

    st.text("Sample Compressions Proteins")

    comparisons = [
        ("ca_1A3N vs ca_1A3O",
        "These two proteins are highly similar, with a TM-score of 0.95 and an RMSD of 1.2 Å. "
        "The main difference is a small loop region that adopts different conformations in the two structures."),
        ("ca_1AKE vs ca_1A3P",
        "These two proteins are moderately similar, with a TM-score of 0.85 and an RMSD of 2.0 Å. "
        "The main difference is a significant conformational change in the active site."),
        ("ca_CRM vs ca_1CSH",
        "These two proteins are distantly related, with a TM-score of 0.65 and an RMSD of 3.5 Å. "
        "The main difference is a large structural rearrangement in the C-terminal domain."),
        ("ca_1HHO vs ca_2HHO",
        "These two proteins are unrelated, with a TM-score of 0.45 and an RMSD of 5.0 Å. "
        "The main difference is that they belong to different protein families and have different folds."),
    ]

    def card(title: str, desc: str) -> str:
        e = html.escape
        return f"""
        <div class="flex h-48 flex-col gap-2 overflow-hidden rounded-lg border border-foreground/15 bg-secondary p-4 text-foreground">
          <div class="truncate text-base font-semibold">{e(title)}</div>
          <p class="line-clamp-4 text-sm leading-snug text-foreground/70" title="{e(desc)}">{e(desc)}</p>
        </div>
        """

    st.html(
        '<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">'
        + "".join(card(t, d) for t, d in comparisons)
        + "</div>"
    )