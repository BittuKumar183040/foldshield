## Running locally
```
streamlit run app.py --server.runOnSave true
```

The Analyze page hides **Load a saved run** by default. To enable it, set
`FOLDSHIELD_SHOW_SAVED_RUN=true` in the environment before starting Streamlit.

## In Docker/Podman
```
podman build -t foldshield:v1 .
```
```
podman run -d -p 8080:8501 foldshield:v1
```
