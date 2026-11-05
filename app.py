import warnings
import altair as alt, joblib, pandas as pd, streamlit as st

st.set_page_config(page_title="Alerta temprana", layout="wide")

NOMBRES = {"Creditos_Acumulados": "Créditos acumulados",
    "Cursos_Desaprobados": "Cursos desaprobados",
    "Promedio_Ponderado": "Promedio ponderado",
    "Asistencia": "Asistencia",
    "Semestre_Actual": "Semestre actual",
    "Edad": "Edad", "Sexo": "Sexo",
    "Distancia_Uni_Km": "Distancia a la universidad",
    "Estado_Laboral": "Estado laboral",
    "Procedencia_Escolar": "Procedencia escolar",
    "Conectividad": "Conectividad",
    "Soporte_Familiar": "Soporte familiar",
    "Horas_Estudio_Sem": "Horas de estudio",
    "Nivel_Estres": "Nivel de estrés"}
SN = {"No": 0, "Sí": 1}

@st.cache_resource
def cargar():
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        modelo = joblib.load("modelo_riesgo_academico.joblib")
        ref = joblib.load("referencia_riesgo.joblib")
    version = any("version" in str(a.message).lower() for a in avisos)
    return modelo, ref, version

try:
    modelo, ref, distinta_version = cargar()
except FileNotFoundError:
    st.error("Faltan los archivos modelo_riesgo_academico.joblib y "
             "referencia_riesgo.joblib (generados por el Código 4).")
    st.stop()

st.title("Alerta temprana de riesgo académico")
st.warning("Prototipo entrenado con datos SIMULADOS: los resultados "
           "no corresponden a estudiantes reales.")
if distinta_version:
    st.info("El modelo se entrenó con otra versión de scikit-learn; "
            "fije la misma versión en requirements.txt.")

izq, der = st.columns(2, gap="large")
x = {}
with izq:
    st.subheader("Datos del estudiante")
    st.markdown("**Académica**")
    x["Creditos_Acumulados"] = st.slider(
        "Créditos acumulados", 0, 200, 77)
    x["Cursos_Desaprobados"] = st.slider(
        "Cursos desaprobados", 0, 8, 1)
    x["Promedio_Ponderado"] = st.slider(
        "Promedio ponderado (0-20)", 0.0, 20.0, 13.3, 0.1)
    x["Asistencia"] = st.slider("Asistencia (%)", 0, 100, 85)
    x["Semestre_Actual"] = st.slider("Semestre actual", 1, 10, 5)
    st.markdown("**Demográfica**")
    x["Edad"] = st.slider("Edad", 16, 30, 20)
    x["Sexo"] = {"Femenino": 0, "Masculino": 1}[
        st.radio("Sexo", ["Femenino", "Masculino"], horizontal=True)]
    x["Distancia_Uni_Km"] = st.slider(
        "Distancia a la universidad (km)", 0.0, 30.0, 5.0, 0.5)
    st.markdown("**Socioeconómica**")
    x["Estado_Laboral"] = SN[st.radio(
        "¿Trabaja?", list(SN), horizontal=True)]
    x["Procedencia_Escolar"] = {"Privado": 0, "Público": 1}[st.radio(
        "Colegio de procedencia", ["Privado", "Público"], index=1,
        horizontal=True)]
    x["Conectividad"] = SN[st.radio(
        "¿Tiene internet y equipo propio?", list(SN), index=1,
        horizontal=True)]
    x["Soporte_Familiar"] = st.slider(
        "Soporte familiar (1 = bajo, 4 = alto)", 1, 4, 3)
    st.markdown("**Comportamiento y bienestar**")
    x["Horas_Estudio_Sem"] = st.slider(
        "Horas de estudio por semana", 0, 40, 14)
    x["Nivel_Estres"] = st.slider(
        "Nivel de estrés (1 = bajo, 4 = alto)", 1, 4, 2)

with der:
    st.subheader("Resultado")
    if st.button("Evaluar riesgo", type="primary"):
        fila = pd.DataFrame([x])[list(ref.index)]
        clase = int(modelo.predict(fila)[0])
        prob = modelo.predict_proba(fila)[0, 1]
        efectos = {}
        for c in fila.columns:       # sensibilidad local
            f2 = fila.copy()
            f2[c] = ref[c]
            efectos[c] = prob - modelo.predict_proba(f2)[0, 1]
        top = pd.Series(efectos).sort_values(
            key=abs, ascending=False).head(5)
        if clase == 1:
            st.error("Estudiante EN RIESGO")
        else:
            st.success("Estudiante SIN RIESGO")
        st.metric("Probabilidad estimada de riesgo", f"{prob:.1%}")
        st.caption("Valor orientativo (escalamiento de Platt); "
                   "la clase la determina el modelo.")
        st.markdown("**Factores que más influyen** "
                    "(respecto a un perfil típico)")
        graf = pd.DataFrame({
            "Variable": [NOMBRES.get(c, c) for c in top.index],
            "Efecto": top.values,
            "Sentido": ["Aumenta el riesgo" if v > 0
                        else "Reduce el riesgo" for v in top.values]})
        st.altair_chart(alt.Chart(graf).mark_bar().encode(
            x=alt.X("Efecto:Q", title="Cambio en la probabilidad",
                    axis=alt.Axis(format="+.0%")),
            y=alt.Y("Variable:N", sort=None, title=None,
                    axis=alt.Axis(labelLimit=220)),
            color=alt.Color("Sentido:N", legend=alt.Legend(
                orient="bottom", title=None), scale=alt.Scale(
                domain=["Aumenta el riesgo", "Reduce el riesgo"],
                range=["#d62728", "#2ca02c"]))), width="stretch")
    else:
        st.info("Ingrese los datos y pulse «Evaluar riesgo».")
