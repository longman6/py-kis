# 프로젝트 규칙

## 가상환경 (Virtual Environment)

- **항상 가상환경을 사용할 것**
- 가상환경 경로: `.venv/`
- 활성화 명령어: `source venv/bin/activate`
- 패키지 설치 시 반드시 가상환경 활성화 후 진행
- pip 명령어 사용 시: `venv/bin/pip` 또는 활성화 후 `pip` 사용

## Python 버전

- Python 3.12.3 사용

## 명령어 실행 규칙

- 모든 Python 스크립트 실행 시 가상환경 Python 사용: `venv/bin/python`
- 패키지 설치: `venv/bin/pip install <package>`

## Git & Versioning

- **Push 시 버전 업데이트 필수**
  - 코드 변경 후 `git push` 할 때마다 버전을 업데이트할 것
  - 버전 위치:
    - `pyproject.toml` → `version = "X.Y.Z"`
    - `src/pykis/__init__.py` → `__version__ = "X.Y.Z"`
  - 버그 수정: Patch 버전 (Z) 증가 (예: 0.1.0 → 0.1.1)
  - 기능 추가: Minor 버전 (Y) 증가 (예: 0.1.0 → 0.2.0)
