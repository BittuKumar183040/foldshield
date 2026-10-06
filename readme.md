## Running locally
```
streamlit run app.py --server.runOnSave true
```

## In Docker/Podman
```
podman build -t foldshield:v1 .
```
```
podman run -d -p 8080:8501 foldshield:v1
```
