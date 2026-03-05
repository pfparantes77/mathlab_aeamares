import json
import time
from datetime import datetime
from pathlib import Path
import streamlit as st
    

# ✅ Caminho robusto: procura o JSON na mesma pasta do jogo.py
DB_PATH = Path(__file__).parent / "questions.json"


def load_questions(path: Path) -> dict:
    """Carrega e valida o ficheiro JSON. Devolve mapa: id -> questão."""
    if not path.exists():
        st.error(f"Não foi encontrado o ficheiro: {path.resolve()}")
        st.stop()

    raw = path.read_text(encoding="utf-8").strip()

    if not raw:
        st.error("O ficheiro questions.json está vazio.")
        st.stop()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        st.error("O ficheiro questions.json não tem JSON válido.")
        st.code(f"Erro: {e}\n\nPrimeiros 200 caracteres do ficheiro:\n{raw[:200]}")
        st.stop()

    if not isinstance(data, list) or len(data) == 0:
        st.error("O questions.json deve ser uma lista de questões (array).")
        st.stop()

    ids = set()
    for q in data:
        obrig = {"id", "enunciado", "opcoes", "correta", "numero_associado"}
        if not isinstance(q, dict) or not obrig.issubset(q.keys()):
            st.error("Estrutura inválida no JSON: cada questão tem de ter id, enunciado, opcoes, correta e numero_associado.")
            st.stop()

        if not isinstance(q["id"], int):
            st.error("Cada questão tem de ter 'id' inteiro.")
            st.stop()

        if q["id"] in ids:
            st.error(f"ID repetido no JSON: {q['id']}.")
            st.stop()
        ids.add(q["id"])

        if not isinstance(q["opcoes"], list) or len(q["opcoes"]) != 4:
            st.error(f"A questão {q['id']} tem de ter exatamente 4 opções.")
            st.stop()

        if not isinstance(q["correta"], int) or not (0 <= q["correta"] <= 3):
            st.error(f"A questão {q['id']} tem 'correta' inválida (deve ser 0..3).")
            st.stop()

        if not isinstance(q["numero_associado"], int):
            st.error(f"A questão {q['id']} tem 'numero_associado' inválido (deve ser inteiro).")
            st.stop()

    return {q["id"]: q for q in data}


def init_state():
    if "quiz" not in st.session_state:
        st.session_state.quiz = {
            "nome": None,                     # ✅ nome obrigatório
            "start_ts": None,                 # ✅ início (epoch)
            "tentativas_por_id": {},          # id -> tentativas usadas
            "concluida": set(),               # ids concluídas
            "acertou": set(),                 # ids acertadas
            "pontos": 0,
            "log": [],
            "terminado": False,
            "ultimo_numero_devolvido": None,
            "ultima_questao": None,
            "feedback_msg": None,             # ✅ mensagem "Boa! ..."
            "feedback_qid": None,             # ✅ a que questão pertence
        }


def pontos_por_tentativa(tentativa_num: int) -> int:
    return {1: 3, 2: 2, 3: 1}.get(tentativa_num, 0)


def calcular_resultados(quiz: dict):
    # Número de questões realizadas (concluídas)
    questoes_realizadas = len(quiz["concluida"])

    # Número total de tentativas (somatório das tentativas por questão)
    total_tentativas = sum(quiz["tentativas_por_id"].values())

    if total_tentativas > 0:
        taxa_sucesso = (questoes_realizadas / total_tentativas) * 100
    else:
        taxa_sucesso = 0.0

    return questoes_realizadas, total_tentativas, taxa_sucesso


# -------- UI --------
from pathlib import Path

LOGO_PATH = Path(__file__).parent / "logo.png"

st.set_page_config(
    page_title="AEAmares + Matemática + Crédito Agrícola Calcular o futuro",
    page_icon=str(LOGO_PATH),  # substitui o emoji pelo logo
    layout="centered"
)

st.image(str(LOGO_PATH), width=300)  # mostra o logo no topo
st.markdown(
    "<h2>AEAmares + Matemática + Crédito Agrícola: calcular o futuro</h2>\n",
    unsafe_allow_html=True
)







questions = load_questions(DB_PATH)
init_state()
quiz = st.session_state.quiz

# Barra superior
col_a, col_b, col_c = st.columns([1, 1, 1])
with col_a:
    if st.button("🔄 Reiniciar"):
        st.session_state.clear()
        st.rerun()

with col_b:
    if st.button("⛔ Terminar", type="primary"):
        quiz["terminado"] = True

with col_c:
    st.metric("Pontos", quiz["pontos"])

# ✅ Nome obrigatório no início (bloqueia tudo)
if not quiz.get("nome"):
    st.subheader("Identificação")
    nome = st.text_input("Nome do aluno", value="", placeholder="Escreve o teu nome!")
    if not nome or not nome.strip():
        st.info("Para iniciar, escreve o teu nome.")
        st.stop()
    quiz["nome"] = nome.strip()
    quiz["start_ts"] = time.time()
    st.success(f"Bem-vindo(a), {quiz['nome']}!")
    st.rerun()

# Se terminou, relatório
if quiz["terminado"]:
    st.subheader("📄 Relatório final")

    questoes_realizadas, total_tentativas, taxa_sucesso = calcular_resultados(quiz)

    # Tempo total
    end_ts = time.time()
    elapsed_sec = int(round(end_ts - (quiz.get("start_ts") or end_ts)))
    mins = elapsed_sec // 60
    secs = elapsed_sec % 60
    tempo_str = f"{mins:02d}:{secs:02d}"  # mm:ss

    st.write(f"**Aluno:** {quiz['nome']}")
    st.write(f"**Questões realizadas:** {questoes_realizadas}")
    st.write(f"**Total de tentativas:** {total_tentativas}")
    st.write(f"**Taxa de sucesso (eficiência):** {taxa_sucesso:.2f}%")
    st.write(f"**Pontuação total:** {quiz['pontos']}")
    st.write(f"**Tempo total até terminar:** {tempo_str} (mm:ss)")

    # Medalhas (conforme pedido)
    if taxa_sucesso > 90:
        st.success("🥇 Medalha de Ouro — desempenho de excelência.")
        medalha = "Ouro"
        mensagem = "Desempenho de excelência."
    elif 70 <= taxa_sucesso <= 89:
        st.info("🥈 Medalha de Prata — muito bom desempenho.")
        medalha = "Prata"
        mensagem = "Muito bom desempenho."
    elif 50 <= taxa_sucesso <= 69:
        st.warning("🥉 Medalha de Bronze — bom esforço, continua.")
        medalha = "Bronze"
        mensagem = "Bom esforço; continua."
    else:
        st.error("👏 Menos de 50%: revê a matéria e tenta novamente. A consistência constrói resultados.")
        medalha = "Sem medalha"
        mensagem = "Menos de 50%: rever matéria e tentar novamente."


        st.write("Sem questões respondidas.")

    # ✅ Relatório JSON para guardar na subpasta Resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    relatorio = {
        "aluno": quiz["nome"],
        "data_hora": datetime.now().isoformat(),
        "tempo_total_segundos": elapsed_sec,
        "tempo_total_mmss": tempo_str,
        "resumo": {
            "questoes_realizadas": questoes_realizadas,
            "respostas_certas": total_tentativas,
            "taxa_sucesso_percent": round(taxa_sucesso, 1),
            "pontuacao_total": quiz["pontos"],
            "medalha": medalha,
            "mensagem": mensagem,
        },
        "registo_por_questao": quiz["log"],
    }

    resultados_path = Path(__file__).parent / "Resultados"
    resultados_path.mkdir(exist_ok=True)

    nome_ficheiro = f"relatorio_{quiz['nome'].replace(' ', '_')}_{timestamp}.json"
    caminho_ficheiro = resultados_path / nome_ficheiro

    with open(caminho_ficheiro, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)



    st.stop()

# ---------------- JOGO ----------------
st.write("Insere o número da questão para a visualizares!")

q_txt = st.text_input(
    "Número da questão",
    value="",
    placeholder=f"Entre {min(questions.keys())} e {max(questions.keys())}",
    key="q_txt",
)

# Sem número -> não mostra nada
if not q_txt.strip():
    st.stop()

# Validação do inteiro
try:
    q_id = int(q_txt.strip())
except ValueError:
    st.error("O número da questão tem de ser um inteiro (ex.: 3).")
    st.stop()

# Existe?
if q_id not in questions:
    st.error("Esse número não corresponde a nenhuma questão existente.")
    st.stop()

# Já concluída?
if q_id in quiz["concluida"]:
    numero_assoc = questions[q_id]["numero_associado"]
    st.warning(
        f"Questão concluída!\n\n "
        f"O número associado à questão {q_id} é {numero_assoc}.\n\n "
        f"Próxima!."
    )
    st.stop()

# ✅ Se mudou de questão, limpar feedback da anterior
if quiz.get("feedback_qid") is not None and quiz["feedback_qid"] != q_id:
    quiz["feedback_msg"] = None
    quiz["feedback_qid"] = None

# ✅ Mostrar feedback apenas se for desta questão
if quiz.get("feedback_msg") and quiz.get("feedback_qid") == q_id:
    st.success(quiz["feedback_msg"])

# Mostrar questão
q = questions[q_id]
st.subheader(f"Questão {q['id']} — {q.get('tema', '')}".strip(" — "))
st.write(q["enunciado"])

tentativas_usadas = quiz["tentativas_por_id"].get(q_id, 0)
st.caption(f"Tentativas restantes: {3 - tentativas_usadas}")

opcao = st.radio("Escolhe uma opção:", q["opcoes"], index=None, key=f"opcao_{q_id}")

if st.button("✅ Submeter"):
    if opcao is None:
        st.error("Tens de escolher uma opção antes de submeter.")
        st.stop()

    # Atualiza tentativas
    tentativas_usadas += 1
    quiz["tentativas_por_id"][q_id] = tentativas_usadas

    idx_escolhida = q["opcoes"].index(opcao)
    correta_idx = q["correta"]

    if idx_escolhida == correta_idx:
        pts = pontos_por_tentativa(tentativas_usadas)
        quiz["pontos"] += pts
        quiz["concluida"].add(q_id)
        quiz["acertou"].add(q_id)

        quiz["ultimo_numero_devolvido"] = q["numero_associado"]
        quiz["ultima_questao"] = q_id

        quiz["log"].append({
            "id": q_id,
            "resultado": "Certa",
            "tentativas": tentativas_usadas,
            "pontos": pts,
            "numero_associado": q["numero_associado"]
        })

        # ✅ mensagem pedida (persistente até mudar de questão)
        quiz["feedback_msg"] = f"Boa! \n\nO número associado à questão {q_id} é {q['numero_associado']}."
        quiz["feedback_qid"] = q_id

        st.rerun()

    else:
        if tentativas_usadas >= 3:
            quiz["concluida"].add(q_id)

            quiz["ultimo_numero_devolvido"] = q["numero_associado"]
            quiz["ultima_questao"] = q_id

            quiz["log"].append({
                "id": q_id,
                "resultado": "Errada (3 tentativas)",
                "tentativas": tentativas_usadas,
                "pontos": 0,
                "numero_associado": q["numero_associado"]
            })

            st.error("Errado ❌ | Esgotaste as 3 tentativas.")
            st.rerun()
        else:
            st.warning(f"Errado ❌ | Tenta novamente. (Tentativa {tentativas_usadas}/3)")
            st.stop()