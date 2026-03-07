import streamlit as st
import os
import io
from crewai import Agent, Task, Crew, Process, LLM


os.environ["OPENAI_API_KEY"] = ""


st.set_page_config(page_title="Анализ отзывов выпускников", layout="wide")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Ошибка: Ключ GOOGLE_API_KEY не найден в .streamlit/secrets.toml")
    st.stop()


llm = LLM(
    model="gemini/gemini-3-flash-preview",
    api_key=st.secrets["GOOGLE_API_KEY"],
    temperature=0.3
)

st.title("🎓 Система анализа обратной связи выпускников")
st.info("СРС №2: Проект №15 — Мультиагентный анализ данных")
st.markdown("---")


st.header("1. Настройка агентов и задач")
col1, col2 = st.columns(2)

with col1:
    st.subheader("👥 Агенты")
    with st.expander("Агент: Исследователь (Researcher)", expanded=True):
        r_role = st.text_input("Role", "Аналитик текстов", key="r_role")
        r_goal = st.text_area("Goal", "Проанализировать отзывы и составить таблицу в формате Markdown.", key="r_goal")
        r_backstory = st.text_area("Backstory", "Эксперт по структурированию данных из CSV.", key="r_bs")

    with st.expander("Агент: Стратег (Reporting Analyst)", expanded=True):
        a_role = st.text_input("Role", "Образовательный стратег", key="a_role")
        a_goal = st.text_area("Goal", "Подготовить финальный отчет на основе таблицы исследователя.", key="a_goal")
        a_backstory = st.text_area("Backstory", "Консультант по развитию программ.", key="a_bs")

with col2:
    st.subheader("📝 Задачи")
    with st.expander("Задача: Исследование данных", expanded=True):
        t1_desc = st.text_area("Описание задачи 1", "Создай таблицу Markdown с колонками: Категория, Отзыв, Инсайт.")

    with st.expander("Задача: Итоговый отчет", expanded=True):
        t2_desc = st.text_area("Описание задачи 2", "Напиши краткий отчет для ректората, используя таблицу выше.")

st.markdown("---")


st.header("2. Ввод данных для анализа")
uploaded_file = st.file_uploader("Загрузите CSV-файл", type=["csv"])

if uploaded_file is not None:
    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    st.session_state['csv_data'] = stringio.read()

raw_feedback = st.text_area(
    "Данные для анализа (CSV):",
    value=st.session_state.get('csv_data', ""),
    height=200
)

st.markdown("---")

st.header("3. Выполнение")
if st.button("🚀 Запустить анализ", type="primary"):
    if not raw_feedback.strip():
        st.error("Данные не введены!")
    else:

        researcher = Agent(role=r_role, goal=r_goal, backstory=r_backstory, llm=llm)
        analyst = Agent(role=a_role, goal=a_goal, backstory=a_backstory, llm=llm)

        task_research = Task(
            description=f"{t1_desc}\n\nДАННЫЕ:\n{raw_feedback}",
            agent=researcher,
            expected_output="Таблица Markdown."
        )

        task_report = Task(
            description=t2_desc,
            agent=analyst,
            expected_output="Итоговый отчет с таблицей."
        )

        crew = Crew(
            agents=[researcher, analyst],
            tasks=[task_research, task_report],
            process=Process.sequential,
            verbose=True
        )

        with st.status("🤖 Агенты работают...", expanded=True) as status:
            result = crew.kickoff()
            status.update(label="✅ Анализ завершен!", state="complete", expanded=False)

        st.subheader("📊 Результат:")
        st.markdown(result)
        st.download_button("📂 Скачать отчет", data=str(result), file_name="report.md")