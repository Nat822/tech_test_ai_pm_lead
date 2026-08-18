#  AI Project Navigator

> AI-помощник для PM по внедрению ИИ — анализирует документы проекта, выявляет блокеры, готовит к встречам и создаёт задачи.

---

##  Описание

**AI Project Navigator** — это полноценный AI-агент, разработанный для Product Manager'ов, ведущих проекты по внедрению искусственного интеллекта. Система работает на базе **NeuralDeep GPT-OSS-120B** с RAG-пайплайном на **ChromaDB**, предоставляя контекстные ответы на основе реальных документов проекта.

### Ключевые возможности

-  **RAG (Retrieval-Augmented Generation)** — работа с документами проекта (требования, встречи, переписки)
-  **Подготовка к встречам** — контекст, открытые вопросы, невыполненные обещания
-  **Анализ требований** — дифф между версиями, противоречия, актуальная гипотеза
-  **Выявление блокеров** — технические и организационные, с ответственными
-  **Создание задач** — генерация и сохранение через локальный API

---

##  Технологический стек

| Компонент        | Технология                          |
|------------------|-------------------------------------|
| Backend          | FastAPI (async)                     |
| UI               | Streamlit                           |
| LLM              | NeuralDeep GPT-OSS-120B             |
| Embeddings       | NeuralDeep bge-m3                   |
| Векторное хранилище | ChromaDB                         |
| HTTP-клиент      | httpx (async)                       |
| Валидация        | Pydantic v2                         |
| Хранилище задач  | tasks.json                          |
| Окружение        | python-dotenv                       |

---

##  Структура проекта

```
tech_test_ai_pm_lead/
│
├── agent/
│   ├── main.py              # FastAPI entrypoint
│   ├── llm.py               # NeuralDeep client (chat + embeddings)
│   ├── rag.py               # RAG-пайплайн (индексация + поиск)
│   ├── tasks.py             # Tool/API для создания задач
│   ├── utils.py             # Вспомогательные функции
│   ├── __init__.py
│   │
│   ├── routes/
│   │   ├── meeting.py       # POST /prepare_meeting
│   │   ├── requirements.py  # POST /requirements_diff
│   │   ├── blockers.py      # POST /find_blockers
│   │   └── next_step.py     # POST /next_step_task
│   │
│   ├── models/
│   │   ├── meeting.py       # Pydantic: MeetingPrep
│   │   ├── requirements.py  # Pydantic: RequirementsDiff
│   │   ├── blockers.py      # Pydantic: Blockers
│   │   └── task.py          # Pydantic: TaskModel
│   │
│   ├── data/                # Документы проекта (.md, .txt и др.)
│   │   └── sample_project.md
│   │
│   ├── embeddings/          # ChromaDB storage (создаётся автоматически)
│   └── streamlit_app.py     # Streamlit UI
│
├── requirements.txt
├── .env                     # Секреты (не коммитить!)
├── .env.example             # Шаблон переменных окружения
├── .gitignore
└── task                     # Техническое задание
```

---

##  Установка и запуск

### 1. Клонирование и создание окружения

```bash
git clone <repo-url>
cd tech_test_ai_pm_lead

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните своими данными:

```bash
cp .env.example .env
```

```env
NEURALDEEP_API_KEY=your_key_here
NEURALDEEP_MODEL=GPT-OSS-120B
NEURALDEEP_EMBED_MODEL=bge-m3
NEURALDEEP_BASE_URL=https://api.neuraldeep.ru/v1
```

### 4. Добавление документов проекта

Поместите документы проекта (`.md`, `.txt`) в папку `agent/data/`.  
Файл `agent/data/sample_project.md` содержит пример с демо-данными.

### 5. Запуск FastAPI backend

```bash
uvicorn agent.main:app --reload --port 8000
```

API будет доступен по адресу: [http://localhost:8000](http://localhost:8000)  
Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Запуск Streamlit UI

В отдельном терминале:

```bash
streamlit run agent/streamlit_app.py
```

UI будет доступен по адресу: [http://localhost:8501](http://localhost:8501)

---

##  API Endpoints

### `GET /`
Health-check.

```json
{ "status": "ok", "service": "AI Project Navigator" }
```

---

### `POST /prepare_meeting`
Подготовка к встрече на основе документов проекта.

**Request body:**
```json
{
  "query": "Подготовь меня к встрече по статусу проекта"
}
```

**Response (`MeetingPrep`):**
```json
{
  "context": "Краткий контекст проекта...",
  "decisions": ["ChromaDB одобрен как векторное хранилище"],
  "open_questions": ["Бюджет на GPU ещё не утверждён"],
  "must_ask": ["Когда CTO подпишет бюджет?"],
  "unfulfilled_promises": ["Denis: прототип RAG до 22 августа"]
}
```

---

### `POST /requirements_diff`
Анализ изменений требований.

**Request body:**
```json
{
  "query": "Какие требования изменились за последний месяц?"
}
```

**Response (`RequirementsDiff`):**
```json
{
  "added": ["Требование on-premise развёртывания"],
  "changed": ["SLA с 5с → 3с (P95)"],
  "removed": ["Анализ тональности чатов"],
  "conflicts": [{"issue": "On-premise vs 3s SLA", "parties": ["Denis", "Olga"]}],
  "current_hypothesis": "Актуальное требование v1.3..."
}
```

---

### `POST /find_blockers`
Выявление блокеров проекта.

**Request body:**
```json
{
  "query": "Какие блокеры есть сейчас?"
}
```

**Response (`Blockers`):**
```json
{
  "technical": ["GPU серверы задержаны до 15 сентября"],
  "organizational": ["CFO в отпуске, бюджет завис"],
  "responsibles": [{"blocker": "GPU budget", "owner": "Maria Ivanova"}],
  "next_steps": ["Запросить облачный GPU как временное решение"]
}
```

---

### `POST /next_step_task`
Генерация следующей задачи и её сохранение.

**Request body:**
```json
{
  "query": "Что нужно сделать прямо сейчас?"
}
```

**Response (`TaskModel`):**
```json
{
  "title": "Оценить облачный GPU для RAG-тестирования",
  "description": "Из-за задержки on-premise серверов...",
  "priority": "high",
  "assignee": "Denis Volkov"
}
```

---

### `POST /tasks`
Прямое создание задачи (запись в `tasks.json`).

**Request body (`TaskModel`):**
```json
{
  "title": "Название задачи",
  "description": "Описание",
  "priority": "high",
  "assignee": "Имя"
}
```

---

### `POST /index`
Принудительная переиндексация всех документов из `data/`.

```json
{ "status": "ok", "chunks_indexed": 42 }
```

---

##  Архитектура RAG-пайплайна

```
agent/data/*.md,*.txt
        │
        ▼
  [Chunker] 500–1000 символов
        │
        ▼
  [NeuralDeep bge-m3] → embeddings
        │
        ▼
  [ChromaDB] — векторное хранилище
        │
        ▼
  [Query] → top-k релевантных чанков
        │
        ▼
  [NeuralDeep GPT-OSS-120B] + контекст → ответ
```

---

##  Pydantic-модели

| Модель            | Поля                                                                        |
|-------------------|-----------------------------------------------------------------------------|
| `MeetingPrep`     | `context`, `decisions`, `open_questions`, `must_ask`, `unfulfilled_promises`|
| `RequirementsDiff`| `added`, `changed`, `removed`, `conflicts`, `current_hypothesis`            |
| `Blockers`        | `technical`, `organizational`, `responsibles`, `next_steps`                 |
| `TaskModel`       | `title`, `description`, `priority`, `assignee`                              |

---

##  Зависимости

```
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
openai>=1.35.0
chromadb>=0.5.0
httpx>=0.27.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
python-dotenv>=1.0.0
streamlit>=1.35.0
tqdm>=4.66.0
```

---

##  Безопасность

- **Никогда не коммитьте `.env`** — он уже добавлен в `.gitignore`
- Используйте `.env.example` как шаблон для других разработчиков
- API-ключ NeuralDeep хранится только в переменных окружения

---

##  Демо-данные

В `agent/data/sample_project.md` содержится полный пример проекта:

- **Проект**: AI Integration for E-Commerce Platform (RetailTech Corp)
- **PM**: Alexey Sorokin
- Требования v1.0 → v1.3, встречи, блокеры, вехи, риски

Используйте его для тестирования всех эндпоинтов без реальных данных.

---

##  Вклад в проект

1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/your-feature`
3. Закоммитьте изменения: `git commit -m 'Add some feature'`
4. Отправьте в ветку: `git push origin feature/your-feature`
5. Откройте Pull Request

---

##  Лицензия

MIT License — используйте свободно.
