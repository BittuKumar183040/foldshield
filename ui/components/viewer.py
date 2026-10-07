"""3D structure viewer (3Dmol.js in an iframe)."""
import json
import streamlit as st
import streamlit.components.v1 as components


def structure_viewer(*, pdb_id: str | None = None, pdb_text: str | None = None, height: int = 440,
                     fill: bool = False) -> None:
    """Show a structure from an RCSB id or from raw PDB text.

    fill=True makes the viewer fill its iframe (100% of the iframe's height), so the page can size
    the iframe with CSS; `height` is then only the iframe's initial height.
    """
    if pdb_text:
        load = f'v.addModel({json.dumps(pdb_text)}, "pdb"); done();'
    elif pdb_id:
        load = f'$3Dmol.download("pdb:" + {json.dumps(str(pdb_id))}, v, {{}}, done);'
    else:
        st.info("No structure available for this entry.")
        return
    box = "height:100vh;box-sizing:border-box" if fill else f"height:{height - 10}px"
    page_css = "<style>html,body{margin:0;overflow:hidden}</style>" if fill else ""
    components.html(f"""
        {page_css}
        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
        <div id="v" style="{box};width:100%;position:relative;
            border:1px solid #ccc;border-radius:8px;overflow:hidden"></div>
        <script>
        const v = $3Dmol.createViewer("v", {{backgroundColor: "white"}});
        function done() {{ v.setStyle({{}}, {{cartoon: {{color: "spectrum"}}}}); v.zoomTo(); v.render(); }}
        window.addEventListener("resize", () => {{ v.resize(); v.render(); }});
        {load}
        </script>""", height=height)