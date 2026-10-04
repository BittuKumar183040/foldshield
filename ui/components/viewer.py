"""3D structure viewer (3Dmol.js in an iframe)."""
import json
import streamlit as st
import streamlit.components.v1 as components


def structure_viewer(*, pdb_id: str | None = None, pdb_text: str | None = None, height: int = 440) -> None:
    """Show a structure from an RCSB id or from raw PDB text."""
    if pdb_text:
        load = f'v.addModel({json.dumps(pdb_text)}, "pdb"); done();'
    elif pdb_id:
        load = f'$3Dmol.download("pdb:" + {json.dumps(str(pdb_id))}, v, {{}}, done);'
    else:
        st.info("No structure available for this entry.")
        return
    components.html(f"""
    <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
    <div id="v" style="height:{height - 10}px;width:100%;position:relative;
         border:1px solid #ccc;border-radius:8px;overflow:hidden"></div>
    <script>
      const v = $3Dmol.createViewer("v", {{backgroundColor: "white"}});
      function done() {{ v.setStyle({{}}, {{cartoon: {{color: "spectrum"}}}}); v.zoomTo(); v.render(); }}
      {load}
    </script>""", height=height)
