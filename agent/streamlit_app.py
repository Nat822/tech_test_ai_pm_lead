"""
AI Project Navigator — Streamlit UI
"""
from __future__ import annotations

import json

import httpx
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Project Navigator",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — dark premium theme
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Global background ── */
.stApp {
    background: linear-gradient(135deg, #0d1117 0%, #161b27 100%);
    color: #e6edf3;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #161b27 0%, #0d1117 100%);
    border-right: 1px solid #30363d;
}
section[data-testid="stSidebar"] * {
    color: #e6edf3 !important;
}

/* ── Headers ── */
h1 { 
    background: linear-gradient(90deg, #7c3aed, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 2rem !important;
}
h2, h3 { color: #c9d1d9 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #161b27;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    color: #8b949e;
    font-weight: 500;
    padding: 8px 18px;
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #7c3aed22, #3b82f622);
    color: #7c3aed !important;
    border-bottom: 2px solid #7c3aed;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(90deg, #7c3aed, #3b82f6);
    color: white !important;
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1.6rem;
    font-weight: 600;
    font-size: 0.95rem;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(124, 58, 237, 0.45);
}
.stButton > button:active {
    transform: translateY(0px);
}

/* ── Input fields ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #161b27 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
}

/* ── Result cards ── */
.result-card {
    background: #161b27;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 10px 0;
    transition: border-color 0.2s ease;
}
.result-card:hover {
    border-color: #7c3aed44;
}
.result-card h4 {
    color: #7c3aed;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 12px;
}
.tag {
    display: inline-block;
    background: #7c3aed22;
    color: #a78bfa;
    border: 1px solid #7c3aed44;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.8rem;
    margin: 3px 4px 3px 0;
    font-weight: 500;
}
.tag.green {
    background: #10b98122;
    color: #34d399;
    border-color: #10b98144;
}
.tag.red {
    background: #ef444422;
    color: #f87171;
    border-color: #ef444444;
}
.tag.yellow {
    background: #f59e0b22;
    color: #fbbf24;
    border-color: #f59e0b44;
}
.tag.blue {
    background: #3b82f622;
    color: #60a5fa;
    border-color: #3b82f644;
}
.conflict-item {
    background: #ef444411;
    border: 1px solid #ef444433;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.88rem;
}
.responsible-item {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.88rem;
}
.task-card {
    background: linear-gradient(135deg, #7c3aed11, #3b82f611);
    border: 1px solid #7c3aed44;
    border-radius: 12px;
    padding: 20px 24px;
}
.priority-high  { color: #f87171; font-weight: 600; }
.priority-medium { color: #fbbf24; font-weight: 600; }
.priority-low   { color: #34d399; font-weight: 600; }
.status-ok {
    background: #10b98122;
    color: #34d399;
    border: 1px solid #10b98144;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 0.9rem;
}
.status-error {
    background: #ef444422;
    color: #f87171;
    border: 1px solid #ef444444;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 0.9rem;
}

/* ── Divider ── */
hr { border-color: #30363d; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# HTTP client — trust_env=False prevents httpx from picking up system/registry
# proxy settings (e.g. socks4://127.0.0.1:10808 from Windows registry).
# All requests go directly to localhost FastAPI, no proxy needed.
# ---------------------------------------------------------------------------
API_BASE = "http://localhost:8000"
# LLM calls can take 60-90 s with max_tokens=2000 on NeuralDeep
TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)

_http = httpx.Client(
    trust_env=False,  # ignore HTTP_PROXY, HTTPS_PROXY, Windows registry proxy
    timeout=TIMEOUT,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def api_post(path: str, payload: dict) -> tuple[dict | None, str | None]:
    """POST to FastAPI. Returns (data, error_msg)."""
    try:
        r = _http.post(f"{API_BASE}{path}", json=payload)
        r.raise_for_status()
        return r.json(), None
    except httpx.TimeoutException:
        return None, "Запрос к FastAPI превысил таймаут. LLM-модель отвечает слишком долго — попробуйте ещё раз."
    except httpx.ConnectError:
        return None, "Невозможно подключиться к FastAPI. Проверьте, что сервер запущен на порту 8000."
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", e.response.text)
        except Exception:
            detail = e.response.text or f"HTTP {e.response.status_code} (empty body)"
        return None, f"API error {e.response.status_code}: {detail}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


@st.cache_data(ttl=600, show_spinner=False)
def api_post_cached(path: str, payload_key: str, payload: dict) -> tuple[dict | None, str | None]:
    """
    Cached version of api_post for LLM-heavy endpoints (TTL=10 min).
    payload_key is a string representation of payload used as cache key.
    Repeated identical requests return instantly from cache.
    """
    return api_post(path, payload)


def api_get(path: str) -> tuple[dict | None, str | None]:
    """GET from FastAPI. Returns (data, error_msg)."""
    try:
        r = _http.get(f"{API_BASE}{path}")
        r.raise_for_status()
        return r.json(), None
    except httpx.TimeoutException:
        return None, "Запрос к FastAPI превысил таймаут."
    except httpx.ConnectError:
        return None, "Невозможно подключиться к FastAPI."
    except Exception as e:
        return None, f"{e}"


def render_list(items: list[str], tag_class: str = "") -> None:
    tags = "".join(
        f'<span class="tag {tag_class}">{item}</span>' for item in items
    )
    st.markdown(tags, unsafe_allow_html=True)


def render_status(msg: str, is_error: bool = False) -> None:
    css = "status-error" if is_error else "status-ok"
    st.markdown(f'<div class="{css}">{msg}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## AI Project Navigator")
    st.markdown("---")

    project = st.text_input(
        "Название проекта",
        value="RetailTech AI Integration",
        help="Используется как контекст во всех запросах к ИИ",
    )

    st.markdown("---")
    st.markdown("### Быстрые действия")

    if st.button("Переиндексировать документы", use_container_width=True):
        with st.spinner("Indexing documents…"):
            data, err = api_get("/index")  # POST /index
            if err:
                # Retry as POST
                data, err = api_post("/index", {})
        if err:
            render_status(err, is_error=True)
        else:
            chunks = data.get("chunks_indexed", "?")
            render_status(f"Проиндексировано {chunks} чанков успешно!")

    st.markdown("---")
    st.markdown("### Сохранённые задачи")

    if st.button("Загрузить задачи", use_container_width=True):
        data, err = api_get("/tasks/")
        if err:
            render_status(err, is_error=True)
        else:
            tasks = data.get("tasks", [])
            if not tasks:
                st.info("Задачи ещё не сохранены.")
            else:
                for t in tasks:
                    pri_cls = f"priority-{t.get('priority', 'medium')}"
                    st.markdown(
                        f"**{t.get('title','—')}**  "
                        f"<span class='{pri_cls}'>[{t.get('priority','?')}]</span>  "
                        f"{t.get('assignee','—')}",
                        unsafe_allow_html=True,
                    )
                    st.caption(t.get("description", ""))
                    st.markdown("---")

    st.markdown("")
    st.caption("Работает на NeuralDeep · ChromaDB · FastAPI")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.markdown("# AI Project Navigator")
st.markdown(
    "ИИ-помощник для PM — RAG по документам проекта · NeuralDeep GPT-OSS-120B"
)
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Подготовка к встрече", "Анализ требований", "Блокеры", "Следующий шаг"]
)

# ── Tab 1: Meeting Preparation ──────────────────────────────────────────────
with tab1:
    st.markdown("### Подготовка к встрече")
    st.markdown(
        "Формирует структурированный брифинг: контекст проекта, принятые решения, открытые вопросы, "
        "что нужно спросить и невыполненные обещания."
    )
    extra1 = st.text_area(
        "Дополнительный контекст (необязательно)",
        placeholder="например: Ревью спринта с CTO, акцент на решении по бюджету оборудования",
        key="meeting_extra",
        height=80,
    )

    if st.button("Сформировать брифинг к встрече", key="btn_meeting"):
        with st.spinner("Запрос к RAG + LLM... Это может занять 30–60 секунд."):
            payload = {"project": project, "extra_context": extra1}
            data, err = api_post_cached(
                "/prepare_meeting",
                str(payload),
                payload,
            )

        if err:
            render_status(err, is_error=True)
        else:
            st.success("Брифинг к встрече сформирован!")

            st.markdown(
                f'<div class="result-card"><h4>Контекст</h4>'
                f'<p>{data.get("context","—")}</p></div>',
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    '<div class="result-card"><h4>Принятые решения</h4>',
                    unsafe_allow_html=True,
                )
                render_list(data.get("decisions", []), "green")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown(
                    '<div class="result-card"><h4>Что нужно спросить</h4>',
                    unsafe_allow_html=True,
                )
                render_list(data.get("must_ask", []), "blue")
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown(
                    '<div class="result-card"><h4>Открытые вопросы</h4>',
                    unsafe_allow_html=True,
                )
                render_list(data.get("open_questions", []), "yellow")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown(
                    '<div class="result-card"><h4>Невыполненные обещания</h4>',
                    unsafe_allow_html=True,
                )
                render_list(data.get("unfulfilled_promises", []), "red")
                st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("Исходный JSON"):
                st.json(data)

# ── Tab 2: Requirements Diff ─────────────────────────────────────────────────
with tab2:
    st.markdown("### Анализ изменений требований")
    st.markdown(
        "Выявляет добавленные, изменённые и удалённые требования, обнаруживает противоречия "
        "и формирует гипотезу об актуальном состоянии требований."
    )
    extra2 = st.text_area(
        "Дополнительный контекст (необязательно)",
        placeholder="например: Сосредоточиться на изменениях v1.2 → v1.3",
        key="req_extra",
        height=80,
    )

    if st.button("Проанализировать требования", key="btn_req"):
        with st.spinner("Запрос к RAG + LLM... Это может занять 30–60 секунд."):
            payload = {"project": project, "extra_context": extra2}
            data, err = api_post_cached(
                "/requirements_diff",
                str(payload),
                payload,
            )

        if err:
            render_status(err, is_error=True)
        else:
            st.success("Анализ требований завершён!")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="result-card"><h4>Добавлены</h4>', unsafe_allow_html=True)
                render_list(data.get("added", []), "green")
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="result-card"><h4>Изменены</h4>', unsafe_allow_html=True)
                render_list(data.get("changed", []), "yellow")
                st.markdown("</div>", unsafe_allow_html=True)

            with col3:
                st.markdown('<div class="result-card"><h4>Удалены</h4>', unsafe_allow_html=True)
                render_list(data.get("removed", []), "red")
                st.markdown("</div>", unsafe_allow_html=True)

            if data.get("conflicts"):
                st.markdown("#### Противоречия")
                for c in data["conflicts"]:
                    parties = ", ".join(c.get("parties", []))
                    status = c.get("status", "pending")
                    st.markdown(
                        f'<div class="conflict-item">'
                        f'<b>{c.get("description", "—")}</b><br/>'
                        f'<small>Стороны: {parties} · Статус: <b>{status}</b></small>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )

            st.markdown(
                f'<div class="result-card"><h4>Актуальная гипотеза</h4>'
                f'<p>{data.get("current_hypothesis","—")}</p></div>',
                unsafe_allow_html=True,
            )

            with st.expander("Исходный JSON"):
                st.json(data)

# ── Tab 3: Blockers ──────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Блокеры проекта")
    st.markdown(
        "Выявляет технические и организационные блокеры, определяет ответственных "
        "и предлагает конкретные следующие шаги."
    )
    extra3 = st.text_area(
        "Дополнительный контекст (необязательно)",
        placeholder="например: Сосредоточиться на блокерах по оборудованию и бюджету",
        key="blocker_extra",
        height=80,
    )

    if st.button("Найти блокеры", key="btn_blockers"):
        with st.spinner("Запрос к RAG + LLM... Это может занять 30–60 секунд."):
            payload = {"project": project, "extra_context": extra3}
            data, err = api_post_cached(
                "/find_blockers",
                str(payload),
                payload,
            )

        if err:
            render_status(err, is_error=True)
        else:
            st.success("Анализ блокеров завершён!")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    '<div class="result-card"><h4>Технические блокеры</h4>',
                    unsafe_allow_html=True,
                )
                for b in data.get("technical", []):
                    st.markdown(f"- {b}")
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown(
                    '<div class="result-card"><h4>Организационные блокеры</h4>',
                    unsafe_allow_html=True,
                )
                for b in data.get("organizational", []):
                    st.markdown(f"- {b}")
                st.markdown("</div>", unsafe_allow_html=True)

            if data.get("responsibles"):
                st.markdown("#### Ответственные")
                for r in data["responsibles"]:
                    # r is now a plain string: "Имя: действие"
                    st.markdown(
                        f'<div class="responsible-item">{r}</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown('<div class="result-card"><h4>Следующие шаги</h4>', unsafe_allow_html=True)
            render_list(data.get("next_steps", []), "blue")
            st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("Исходный JSON"):
                st.json(data)

# ── Tab 4: Next Step / Create Task ───────────────────────────────────────────
with tab4:
    st.markdown("### Сформировать и создать следующую задачу")
    st.markdown(
        "Использует RAG для определения наиболее критичного следующего действия, "
        "автоматически создаёт задачу и сохраняет её в `tasks.json`."
    )
    situation = st.text_area(
        "Текущая ситуация (необязательно)",
        placeholder="например: Оборудование ещё не одобрено, до прототипа RAG 6 дней",
        key="task_situation",
        height=100,
    )

    if st.button("Сформировать и сохранить задачу", key="btn_task"):
        with st.spinner("Запрос к RAG + LLM... Это может занять 30–60 секунд."):
            payload = {"project": project, "situation": situation}
            data, err = api_post(
                "/next_step_task",
                payload,
            )

        if err:
            render_status(err, is_error=True)
        else:
            st.success("Задача создана и сохранена в tasks.json!")

            pri = data.get("priority", "medium")
            pri_cls = f"priority-{pri}"
            st.markdown(
                f'<div class="task-card">'
                f'<h3 style="color:#a78bfa;margin-bottom:8px">{data.get("title","—")}</h3>'
                f'<p style="color:#c9d1d9;margin-bottom:14px">{data.get("description","—")}</p>'
                f'<div>'
                f'<span class="tag">Priority: <span class="{pri_cls}">{pri.upper()}</span></span>'
                f'<span class="tag blue">{data.get("assignee","—")}</span>'
                f"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

            with st.expander("Исходный JSON"):
                st.json(data)
