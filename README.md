# selenitron

## Start webserver
```
uvicorn main:app --host 0.0.0.0 --no-use-colors --log-level debug
```

## Start worker
```
python task_worker.py --looped
```

