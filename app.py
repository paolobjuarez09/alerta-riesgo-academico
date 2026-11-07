import math, warnings
import altair as alt, joblib, pandas as pd, streamlit as st

st.set_page_config(page_title="Alerta temprana de riesgo académico",
                   page_icon=":material/school:", layout="wide")

PETROLEO, TEAL, AMBAR = "#0F3B4C", "#0F6E7E", "#E8A33D"
ROJO, VERDE, TINTA = "#C8453B", "#2E8B57", "#1B2A33"

NOMBRES = {"Creditos_Acumulados": "Créditos acumulados",
    "Cursos_Desaprobados": "Cursos desaprobados",
    "Promedio_Ponderado": "Promedio ponderado",
    "Asistencia": "Asistencia", "Semestre_Actual": "Semestre actual",
    "Edad": "Edad", "Sexo": "Sexo",
    "Distancia_Uni_Km": "Distancia a la universidad",
    "Estado_Laboral": "Estado laboral",
    "Procedencia_Escolar": "Procedencia escolar",
    "Conectividad": "Conectividad",
    "Soporte_Familiar": "Soporte familiar",
    "Horas_Estudio_Sem": "Horas de estudio",
    "Nivel_Estres": "Nivel de estrés"}

ACCIONES = {  # solo factores sobre los que se puede actuar
    "Cursos_Desaprobados": "planificar la recuperación de los cursos desaprobados",
    "Promedio_Ponderado": "reforzar los cursos con menor nota",
    "Asistencia": "mejorar la asistencia a clases",
    "Estado_Laboral": "organizar un horario compatible con el trabajo",
    "Horas_Estudio_Sem": "aumentar las horas de estudio semanales",
    "Nivel_Estres": "buscar apoyo en bienestar universitario para manejar el estrés",
    "Soporte_Familiar": "acercarlo a los servicios de bienestar estudiantil",
    "Conectividad": "gestionar acceso a internet o préstamo de equipos",
    "Distancia_Uni_Km": "considerar el tiempo de traslado al organizar su horario",
    "Creditos_Acumulados": "revisar su avance en el plan de estudios",
    "Semestre_Actual": "revisar su avance en el plan de estudios"}

def recomendacion(clase, prob, top):
    acc = []
    for c in top.index:
        if top[c] > 0.01 and c in ACCIONES and ACCIONES[c] not in acc:
            acc.append(ACCIONES[c])
    if clase == 1:
        texto = "El perfil presenta señales claras de riesgo. Se recomienda "
        texto += (acc[0] + (f" y {acc[1]}" if len(acc) > 1 else "") + "."
                  if acc else "revisar su situación académica cuanto antes.")
        return "Seguimiento prioritario", texto, ROJO, "#FBEDEB"
    if prob >= 0.35:
        texto = ("No se clasifica en riesgo, pero está cerca del límite. Se recomienda "
                 + (acc[0] if acc else "revisar su avance antes de fin de ciclo") + ".")
        return "Seguimiento preventivo", texto, AMBAR, "#FBF4E6"
    texto = "El perfil no muestra señales importantes de riesgo. "
    texto += (f"Para mantenerlo así, se recomienda {acc[0]}." if acc
              else "Se recomienda mantener su ritmo de estudio actual.")
    return "Seguimiento regular", texto, VERDE, "#EAF4EE"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,500;7..72,700&family=Public+Sans:wght@400;500;600&display=swap');
html, body, .stApp, .stMarkdown, label, button, input, textarea {{
  font-family: 'Public Sans', sans-serif; }}
h1, h2, h3, .serif {{ font-family: 'Literata', Georgia, serif !important; }}
.block-container {{ padding-top: 1.2rem; max-width: 1240px; }}
#MainMenu, footer {{ visibility: hidden; }}

.hero {{ background: {PETROLEO}; color: #fff; border-radius: 20px;
  padding: 2.2rem 2.4rem; display: flex; align-items: center;
  justify-content: space-between; gap: 2rem; margin-bottom: 1.6rem; }}
.hero h1 {{ color: #fff; font-size: 2.35rem; line-height: 1.15;
  margin: 0 0 .7rem 0; padding: 0; font-weight: 700; }}
.hero p {{ color: #CFE3E7; font-size: 1.05rem; max-width: 34rem;
  line-height: 1.55; margin: 0; }}
.hero .escuela {{ color: {AMBAR}; font-weight: 600; font-size: .95rem;
  margin-bottom: .6rem; }}
.hero svg {{ flex-shrink: 0; }}
@media (max-width: 760px) {{ .hero svg {{ display: none; }}
  .hero h1 {{ font-size: 1.8rem; }} }}

.st-key-perfil {{ background: #fff; border-radius: 18px;
  padding: 1.6rem 1.8rem .8rem 1.8rem; border: 1px solid #DCE6EA; }}
.grupo {{ display: flex; align-items: center; gap: .6rem;
  margin: .4rem 0 .2rem 0; }}
.grupo .ic {{ width: 34px; height: 34px; border-radius: 50%;
  background: #E3EEF0; display: grid; place-items: center; }}
.grupo h3 {{ font-size: 1.15rem; margin: 0; padding: 0; color: {PETROLEO}; }}
.st-key-perfil hr {{ margin: .9rem 0 .6rem 0; border-color: #E6EDF0; }}

.st-key-resultado {{ position: sticky; top: 1rem; background: #fff;
  border-radius: 18px; padding: 1.5rem 1.6rem; border: 1px solid #DCE6EA; }}
.estado {{ font-family: 'Literata', serif; font-size: 1.55rem;
  font-weight: 700; text-align: center; margin: -.4rem 0 .2rem 0; }}
.sub {{ text-align: center; color: #5B6B73; font-size: .9rem; }}
.reco {{ border-radius: 14px; padding: 1rem 1.15rem; margin-top: 1rem;
  display: flex; gap: .85rem; align-items: flex-start; }}
.reco .ic {{ flex-shrink: 0; width: 38px; height: 38px; border-radius: 50%;
  display: grid; place-items: center; }}
.reco h4 {{ font-family: 'Literata', serif; font-size: 1.08rem; margin: 0 0 .25rem 0;
  padding: 0; }}
.reco p {{ margin: 0; font-size: .95rem; line-height: 1.5; color: #24343C; }}
.nota {{ color: #6B7B83; font-size: .82rem; line-height: 1.45;
  margin-top: .8rem; }}
.stButton button[kind="primary"] {{ background: {AMBAR}; color: {PETROLEO};
  border: none; font-weight: 600; font-size: 1.02rem; padding: .65rem 0; }}
.stButton button[kind="primary"]:hover {{ background: #F0B456;
  color: {PETROLEO}; }}
</style>"""

HERO_SVG = f"""
<svg width="300" height="170" viewBox="0 0 300 170" role="img"
 aria-label="Semestre con rendimiento descendente y alerta">
 <rect x="0" y="0" width="300" height="170" rx="16" fill="#154B5E"/>
 <line x1="24" y1="140" x2="276" y2="140" stroke="#2E6577" stroke-width="2"/>
 {''.join(f'<rect x="{28+i*30}" y="{140-h}" width="18" height="{h}" rx="4" fill="{c}"/>'
   for i, (h, c) in enumerate([(92,'#4E9AA8'),(100,'#4E9AA8'),(88,'#4E9AA8'),
   (80,'#4E9AA8'),(66,'#4E9AA8'),(52,'#E8A33D'),(40,'#E8A33D'),(28,'#C8453B')]))}
 <polyline points="37,40 67,32 97,44 127,52 157,66 187,80 217,92 247,104"
  fill="none" stroke="#CFE3E7" stroke-width="2.5" stroke-dasharray="5 5"/>
 <circle cx="247" cy="104" r="15" fill="{AMBAR}"/>
 <text x="247" y="110" text-anchor="middle" font-size="18" font-weight="700"
  fill="{PETROLEO}" font-family="Public Sans, sans-serif">!</text>
 <text x="24" y="160" font-size="11" fill="#8FB6BF"
  font-family="Public Sans, sans-serif">Semana 1</text>
 <text x="276" y="160" text-anchor="end" font-size="11" fill="#8FB6BF"
  font-family="Public Sans, sans-serif">Semana 16</text>
</svg>"""

ICONOS = {  # trazos simples, 18 px
 "academica": '<path d="M3 5h6a3 3 0 0 1 3 3v11a2 2 0 0 0-2-2H3zM21 5h-6a3 3 0 0 0-3 3v11a2 2 0 0 1 2-2h7z"/>',
 "demografica": '<circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>',
 "socio": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>',
 "bienestar": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'}

def grupo(clave, titulo):
    st.markdown(f"""<div class="grupo"><div class="ic"><svg width="18" height="18"
      viewBox="0 0 24 24" fill="none" stroke="{TEAL}" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round">{ICONOS[clave]}</svg></div>
      <h3>{titulo}</h3></div>""", unsafe_allow_html=True)

def gauge(prob, color):
    """Semicírculo de 0 a 100 % con aguja en la probabilidad."""
    cx, cy, r = 150, 140, 110
    def punto(f, rr=r):
        a = math.pi * (1 - f)
        return cx + rr * math.cos(a), cy - rr * math.sin(a)
    tramos = ""
    for f0, f1, c in [(0, .35, VERDE), (.35, .6, AMBAR), (.6, 1, ROJO)]:
        (x0, y0), (x1, y1) = punto(f0), punto(f1)
        tramos += (f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f}" '
                   f'stroke="{c}" stroke-width="22" fill="none" '
                   f'opacity="{.95 if prob is not None else .25}"/>')
    aguja = ""
    if prob is not None:
        x, y = punto(prob, r - 30)
        aguja = (f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{TINTA}" '
                 f'stroke-width="5" stroke-linecap="round"/>'
                 f'<circle cx="{cx}" cy="{cy}" r="10" fill="{TINTA}"/>')
    valor = "—" if prob is None else f"{prob:.0%}"
    return f"""<svg viewBox="0 0 300 200" width="100%" style="max-width:340px;
      display:block;margin:0 auto" role="img" aria-label="Probabilidad {valor}">
      {tramos}{aguja}
      <text x="{cx}" y="190" text-anchor="middle" font-size="34" font-weight="700"
       fill="{color}" font-family="Literata, serif">{valor}</text>
      <text x="40" y="160" text-anchor="middle" font-size="12" fill="#6B7B83">0 %</text>
      <text x="260" y="160" text-anchor="middle" font-size="12" fill="#6B7B83">100 %</text>
    </svg>"""

FALTAN = []
def opcion(etiqueta, opciones, clave):
    v = st.segmented_control(etiqueta, list(opciones), default=None, key=clave)
    if v is None:
        FALTAN.append(etiqueta.strip("¿?"))
        return None
    return opciones[v]

@st.cache_resource
def cargar():
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        modelo = joblib.load("modelo_riesgo_academico.joblib")
        ref = joblib.load("referencia_riesgo.joblib")
    version = any("version" in str(a.message).lower() for a in avisos)
    return modelo, ref, version

st.markdown(CSS, unsafe_allow_html=True)
try:
    modelo, ref, distinta_version = cargar()
except FileNotFoundError:
    st.error("Faltan los archivos modelo_riesgo_academico.joblib y "
             "referencia_riesgo.joblib en la carpeta de la aplicación.")
    st.stop()

st.markdown(f"""<div class="hero"><div>
  <div class="escuela">Escuela de Informática, Universidad Nacional de Trujillo</div>
  <h1>Alerta temprana de riesgo académico</h1>
  <p>Ingrese el perfil de un estudiante para estimar su riesgo de bajo
  rendimiento y ver qué factores influyen en el resultado.</p>
  </div>{HERO_SVG}</div>""", unsafe_allow_html=True)
if distinta_version:
    st.info("El modelo se entrenó con otra versión de scikit-learn; "
            "fije la misma versión en requirements.txt.")

izq, der = st.columns([1.35, 1], gap="large")
x = {}
with izq:
    with st.container(key="perfil"):
        grupo("academica", "Rendimiento académico")
        a, b = st.columns(2)
        x["Promedio_Ponderado"] = a.slider("Promedio ponderado (0-20)", 0.0, 20.0, 0.0, 0.1)
        x["Cursos_Desaprobados"] = b.slider("Cursos desaprobados", 0, 8, 0)
        x["Asistencia"] = a.slider("Asistencia (%)", 0, 100, 0)
        x["Creditos_Acumulados"] = b.slider("Créditos acumulados", 0, 200, 0)
        x["Semestre_Actual"] = a.slider("Semestre actual", 1, 10, 1)
        st.divider()
        grupo("demografica", "Datos personales")
        a, b = st.columns(2)
        x["Edad"] = a.slider("Edad", 16, 30, 16)
        x["Distancia_Uni_Km"] = b.slider("Distancia a la universidad (km)", 0.0, 30.0, 0.0, 0.5)
        with a:
            x["Sexo"] = opcion("Sexo", {"Femenino": 0, "Masculino": 1}, "sexo")
        st.divider()
        grupo("socio", "Situación socioeconómica")
        a, b = st.columns(2)
        with a:
            x["Estado_Laboral"] = opcion("¿Trabaja?", {"No": 0, "Sí": 1}, "trabaja")
            x["Conectividad"] = opcion("¿Tiene internet y equipo propio?",
                                       {"No": 0, "Sí": 1}, "conect")
        with b:
            x["Procedencia_Escolar"] = opcion("Colegio de procedencia",
                                              {"Privado": 0, "Público": 1}, "colegio")
            x["Soporte_Familiar"] = st.slider("Soporte familiar (1 = bajo, 4 = alto)", 1, 4, 1)
        st.divider()
        grupo("bienestar", "Hábitos y bienestar")
        a, b = st.columns(2)
        x["Horas_Estudio_Sem"] = a.slider("Horas de estudio por semana", 0, 40, 0)
        x["Nivel_Estres"] = b.slider("Nivel de estrés (1 = bajo, 4 = alto)", 1, 4, 1)

with der:
    with st.container(key="resultado"):
        evaluar = st.button("Evaluar riesgo", type="primary", width="stretch")
        if evaluar and not FALTAN:
            fila = pd.DataFrame([x])[list(ref.index)]
            clase = int(modelo.predict(fila)[0])
            prob = float(modelo.predict_proba(fila)[0, 1])
            efectos = {}
            for c in fila.columns:          # sensibilidad local
                f2 = fila.copy(); f2[c] = ref[c]
                efectos[c] = prob - modelo.predict_proba(f2)[0, 1]
            top = pd.Series(efectos).sort_values(key=abs, ascending=False).head(5)
            color = ROJO if clase == 1 else VERDE
            st.markdown(gauge(prob, color), unsafe_allow_html=True)
            texto = "En riesgo académico" if clase == 1 else "Sin riesgo académico"
            st.markdown(f'<div class="estado" style="color:{color}">{texto}</div>'
                        '<div class="sub">Probabilidad estimada por el modelo '
                        '(valor orientativo)</div>', unsafe_allow_html=True)
            titulo, texto_r, col_r, fondo_r = recomendacion(clase, prob, top)
            st.markdown(f"""<div class="reco" style="background:{fondo_r}">
              <div class="ic" style="background:{col_r}"><svg width="20" height="20"
               viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2"
               stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V4"/>
               <path d="M5 4h11l-2 4 2 4H5"/></svg></div>
              <div><h4 style="color:{col_r}">{titulo}</h4><p>{texto_r}</p></div>
              </div>""", unsafe_allow_html=True)
            graf = pd.DataFrame({
                "Variable": [NOMBRES.get(c, c) for c in top.index],
                "Efecto": top.values,
                "Sentido": ["Aumenta el riesgo" if v > 0 else "Reduce el riesgo"
                            for v in top.values]})
            st.markdown('<div class="serif" style="font-weight:700;color:#0F3B4C;'
                        'margin-top:1.3rem;font-size:1.05rem">Factores que más influyen</div>',
                        unsafe_allow_html=True)
            st.altair_chart(alt.Chart(graf).mark_bar(cornerRadiusEnd=3).encode(
                x=alt.X("Efecto:Q", title=None,
                        axis=alt.Axis(format="+.0%", grid=False, tickCount=5)),
                y=alt.Y("Variable:N", sort=None, title=None,
                        axis=alt.Axis(labelLimit=200, labelFontSize=12, ticks=False,
                                      labelOverlap=False, labelPadding=8)),
                color=alt.Color("Sentido:N", legend=None,
                    scale=alt.Scale(domain=["Aumenta el riesgo", "Reduce el riesgo"],
                                    range=[ROJO, VERDE])))
                .properties(height=190, background="#FFFFFF")
                .configure_view(strokeWidth=0), width="stretch")
            st.markdown('<div class="nota" style="margin-top:0">Cambio en la probabilidad respecto a '
                        'un estudiante típico. En rojo, lo que aumenta el riesgo; en verde, '
                        'lo que lo reduce.</div>', unsafe_allow_html=True)
        else:
            if evaluar:
                st.warning("Falta seleccionar: " + ", ".join(FALTAN) + ".")
            st.markdown(gauge(None, "#9AA9B0"), unsafe_allow_html=True)
            st.markdown('<div class="estado" style="color:#5B6B73;font-size:1.2rem">'
                        'Complete el perfil y pulse «Evaluar riesgo»</div>',
                        unsafe_allow_html=True)
