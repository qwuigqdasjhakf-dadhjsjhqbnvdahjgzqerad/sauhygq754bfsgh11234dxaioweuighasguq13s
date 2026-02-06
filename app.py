import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import ast
import locale
import io
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO REGIONAL (PT-BR) ---
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except:
        pass 

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="Barbosa Contabilidade | Treinamentos", layout="wide")

# Inicializa conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    df = conn.read(worksheet="Treinamentos", ttl=0)
    if df.empty or len(df.columns) < 2:
        return pd.DataFrame(columns=["Data", "Funcionário", "Setor", "Líder", "Tema", "Horas", "Avaliação", "Nota_Lider"])
    
    df["Nota_Lider"] = df["Nota_Lider"].astype(str).replace(['nan', 'None', '', 'nan.0'], '-')
    df["Avaliação"] = df["Avaliação"].astype(str).replace(['nan', 'None', ''], '-')
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors='coerce')
    df["Horas"] = pd.to_numeric(df["Horas"], errors='coerce').fillna(0)
    return df

def carregar_usuarios():
    return conn.read(worksheet="Usuarios", ttl=0)

def salvar_dados(df_atualizado):
    conn.update(worksheet="Treinamentos", data=df_atualizado)

def salvar_usuarios(df_usuarios):
    conn.update(worksheet="Usuarios", data=df_usuarios)

# --- UTILITÁRIOS ---
def format_to_time(decimal_hours):
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)
    seconds = int(round(((decimal_hours - hours) * 60 - minutes) * 60))
    if seconds == 60: seconds = 0; minutes += 1
    if minutes == 60: minutes = 0; hours += 1
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def converter_perfil(perfil_raw):
    try:
        res = ast.literal_eval(str(perfil_raw))
        return res if isinstance(res, list) else [str(perfil_raw)]
    except:
        return [str(perfil_raw)]

# --- CONSTANTES ---
LISTA_SETORES = ["Selecione o Setor...", "Departamento T.I.", "Departamento Pessoal", "Departamento Fiscal", "Departamento Contábil", "Diretoria", "Departamento R.H.", "Departamento Legalização", "Departamento Recepção"]
LISTA_LIDERES = ["Selecione o Líder...", "Victor Souza", "Thiago Ferreira", "Rafael Pires", "Priscila Barbosa", "Franceli Dario", "Thamiris Afonso", "Ruth Moreira"]
LISTA_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
LISTA_NOTAS_VALIDAS = [str(i) for i in range(1, 11)]
LISTA_NOTAS_CADASTRO = ["Selecione..."] + LISTA_NOTAS_VALIDAS

# --- ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("""
        <style>
        .stApp { background-color: #000000 !important; background: radial-gradient(circle, #4a0000 0%, #000000 100%) !important; color: white; min-height: 100vh; }
        [data-testid="stHorizontalBlock"] { background-color: rgba(255, 255, 255, 0.05) !important; padding: 50px !important; border-radius: 30px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; backdrop-filter: blur(20px) !important; box-shadow: 0 25px 50px rgba(0,0,0,0.5) !important; margin-top: 50px; }
        .main-title { font-family: sans-serif; font-size: 38px; font-weight: 900; color: white; text-transform: uppercase; text-align: center; }
        .sub-title { font-family: sans-serif; font-size: 16px; color: #ff4b4b; text-align: center; margin-bottom: 30px; letter-spacing: 2px; font-weight: bold; }
        .stButton>button { background-color: white !important; color: black !important; border-radius: 50px !important; font-weight: bold; width: 100%; padding: 12px; border: none !important; }
        .stButton>button:hover { background-color: #ff0000 !important; color: white !important; box-shadow: 0 0 25px rgba(255, 0, 0, 0.6); }
        </style>
    """, unsafe_allow_html=True)
    
    _, login_col, _ = st.columns([1, 1.5, 1])
    with login_col:
        st.markdown('<h1 class="main-title">BARBOSA CONTABILIDADE</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-title">Portal de Treinamentos Internos | Login</p>', unsafe_allow_html=True)
        u_in = st.text_input("Seu Nome de Usuário", placeholder="Ex: Matheus Oliveira")
        s_in = st.text_input("Senha de Acesso", type="password")
        if st.button("LOGIN"):
            users_df = carregar_usuarios()
            user_auth = users_df[(users_df['usuario'] == u_in) & (users_df['senha'].astype(str) == s_in)]
            if not user_auth.empty:
                st.session_state.autenticado = True
                st.session_state.usuario = u_in
                st.session_state.perfil = converter_perfil(user_auth.iloc[0]['perfil'])
                st.session_state.setor_usuario = user_auth.iloc[0]['setor']
                st.rerun()
            else: st.error("Credenciais incorretas.")

else:
    # --- CSS INTERNO (LOGADO) ---
    st.markdown("""
        <style>
        .stApp { background-color: #000000 !important; background: radial-gradient(circle, #4a0000 0%, #000000 100%) !important; color: white; min-height: 100vh; }
        section[data-testid="stSidebar"] { background-color: rgba(0, 0, 0, 0.8) !important; border-right: 1px solid #4a0000; }
        .main-title-logged { font-family: sans-serif; font-size: 30px; font-weight: 800; color: white; text-transform: uppercase; margin-bottom: 20px; }
        div[data-testid="stMetricValue"] { padding: 20px !important; border-radius: 15px !important; color: white !important; font-weight: bold !important; }
        .edit-container { background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; border: 1px solid #ff4b4b; }
        .metric-card { background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; text-align: center; border-bottom: 4px solid #ff4b4b; transition: transform 0.3s; }
        .metric-card:hover { transform: translateY(-5px); background-color: rgba(255, 255, 255, 0.1); }
        .metric-label { color: #aaaaaa; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
        .metric-value { color: white; font-size: 28px; font-weight: 800; }
        .inactive-alert { border-left: 5px solid #ff4b4b; background-color: rgba(255, 75, 75, 0.1); padding: 15px; border-radius: 5px; margin-bottom: 10px; }
        </style>
    """, unsafe_allow_html=True)
    
    df = carregar_dados()
    opcoes_menu = ["Dashboard", "Registrar Curso", "Relatório Geral"]
    if any(p in st.session_state.perfil for p in ["Admin", "Editor"]): 
        opcoes_menu.append("Painel Administrativo")
    
    menu = st.sidebar.selectbox("Menu", opcoes_menu)
    st.sidebar.divider()
    st.sidebar.write(f"👤 **{st.session_state.usuario}**")
    st.sidebar.write(f"🏷️ Perfis: **{', '.join(st.session_state.perfil)}**")
    st.sidebar.write(f"🏢 Setor: **{st.session_state.setor_usuario}**")

    # --- ALTERAR SENHA (NA SIDEBAR) ---
    with st.sidebar.expander("🔑 Alterar Minha Senha"):
        with st.form("form_alterar_senha_pessoal"):
            nova_senha = st.text_input("Nova Senha", type="password")
            conf_senha = st.text_input("Confirmar Senha", type="password")
            if st.form_submit_button("ATUALIZAR"):
                if nova_senha == conf_senha and nova_senha != "":
                    u_df = carregar_usuarios()
                    u_df.loc[u_df['usuario'] == st.session_state.usuario, 'senha'] = nova_senha
                    salvar_usuarios(u_df)
                    st.success("Senha alterada!")
                else: st.error("As senhas não coincidem.")

    # --- LÓGICA DASHBOARD ---
    if menu == "Dashboard":
        mes_sel = st.sidebar.selectbox("Mês", LISTA_MESES, index=datetime.now().month-1)
        ano_sel = st.sidebar.number_input("Ano", 2024, 2030, datetime.now().year)
        target_users = [st.session_state.usuario]
        titulo_dash = f"MEU DASHBOARD - {mes_sel.upper()}"
        status_filtro_radio = "Todos"

        if any(p in st.session_state.perfil for p in ["Gestor", "Admin"]):
            st.sidebar.divider()
            df_base_filtros = df.copy()
            if "Admin" in st.session_state.perfil or st.session_state.setor_usuario == "Diretoria":
                setor_f = st.sidebar.selectbox("Filtrar por Setor:", ["Todos"] + LISTA_SETORES[1:])
                if setor_f != "Todos": df_base_filtros = df_base_filtros[df_base_filtros["Setor"] == setor_f]
            else:
                df_base_filtros = df_base_filtros[df_base_filtros["Setor"] == st.session_state.setor_usuario]
            
            colaboradores_lista = sorted(df_base_filtros["Funcionário"].unique().tolist())
            f_colabs = st.sidebar.multiselect("Filtrar Colaboradores:", colaboradores_lista, placeholder="Escolha uma opção")
            status_filtro_radio = st.sidebar.radio("Filtrar por Status de Avaliação:", ["Todos", "✅ Avaliados", "⏳ Pendentes"])
            
            if f_colabs:
                target_users = f_colabs
                titulo_dash = f"DASHBOARD: {f_colabs[0].upper()}" if len(f_colabs) == 1 else f"DASHBOARD GRUPAL"
            else:
                target_users = colaboradores_lista if not df_base_filtros.empty else [st.session_state.usuario]

        # TRAVA CONTRA ERRO DE DATA VAZIA
        if df.empty or df["Data"].isnull().all():
            st.info("Aguardando registros para exibir o Dashboard.")
        else:
            user_df = df[(df["Funcionário"].isin(target_users)) & 
                         (df["Data"].dt.month == (LISTA_MESES.index(mes_sel)+1)) & 
                         (df["Data"].dt.year == ano_sel)].copy()
            
            user_df["Nota_Lider_Str"] = user_df["Nota_Lider"].apply(lambda x: str(x).replace('.0', ''))
            if status_filtro_radio == "✅ Avaliados":
                user_df = user_df[user_df["Nota_Lider_Str"].isin(LISTA_NOTAS_VALIDAS)]
            elif status_filtro_radio == "⏳ Pendentes":
                user_df = user_df[~user_df["Nota_Lider_Str"].isin(LISTA_NOTAS_VALIDAS)]
            
            horas_totais = user_df["Horas"].sum()
            meta_dinamica = 7.0 * (len(target_users) if target_users else 1)

            # Lógica de cores dinâmica do script original
            if horas_totais < (meta_dinamica * 0.4): cor_card, cor_graf = "linear-gradient(135deg, #ff0000 0%, #8b0000 100%)", "#ff4b4b"
            elif horas_totais < meta_dinamica: cor_card, cor_graf = "linear-gradient(135deg, #ff8c00 0%, #ff4500 100%)", "#ffa500"
            else: cor_card, cor_graf = "linear-gradient(135deg, #00ff00 0%, #006400 100%)", "#00ff00"

            st.markdown(f"<style>div[data-testid='stMetricValue'] {{ background: {cor_card} !important; }}</style>", unsafe_allow_html=True)
            st.markdown(f'<h1 class="main-title-logged">{titulo_dash}</h1>', unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("HORAS NO MÊS", format_to_time(horas_totais))
            c2.metric("META DO GRUPO", format_to_time(meta_dinamica))
            c3.metric("PROGRESSO", f"{min(100.0, (horas_totais/meta_dinamica)*100 if meta_dinamica > 0 else 0):.1f}%")
            c4.metric("STATUS", "EM DIA" if horas_totais >= meta_dinamica else "PENDENTE")

            # --- SEÇÃO DE META 7H (ORIGINAL) ---
            if any(p in st.session_state.perfil for p in ["Gestor", "Admin"]):
                st.divider()
                st.subheader("🚩 Status de Cumprimento da Meta (7h Individual)")
                udf_meta = carregar_usuarios()
                if not ("Admin" in st.session_state.perfil or st.session_state.setor_usuario == "Diretoria"):
                    udf_meta = udf_meta[udf_meta["setor"] == st.session_state.setor_usuario]
                
                todos_colabs = udf_meta["usuario"].unique()
                df_mes_meta = df[(df["Data"].dt.month == (LISTA_MESES.index(mes_sel)+1)) & (df["Data"].dt.year == ano_sel)]
                horas_por_colab = df_mes_meta.groupby("Funcionário")["Horas"].sum().reindex(todos_colabs, fill_value=0).reset_index()
                horas_por_colab.columns = ["Nome", "Total_Horas"]
                
                bateu_meta = horas_por_colab[horas_por_colab["Total_Horas"] >= 7.0]
                pendente_meta = horas_por_colab[horas_por_colab["Total_Horas"] < 7.0]
                
                m1, m2 = st.columns([1, 2])
                with m1:
                    fig_meta = px.pie(values=[len(bateu_meta), len(pendente_meta)], 
                                      names=['Concluiu Meta', 'Pendente'], 
                                      hole=0.6, color=['Concluiu Meta', 'Pendente'],
                                      color_discrete_map={'Concluiu Meta':'#00ff00', 'Pendente':'#ff4b4b'},
                                      title="Proporção da Equipe")
                    fig_meta.update_layout(showlegend=False, height=250, margin=dict(t=40, b=0, l=0, r=0), template="plotly_dark")
                    st.plotly_chart(fig_meta, use_container_width=True)
                
                with m2:
                    col_lista1, col_lista2 = st.columns(2)
                    with col_lista1:
                        with st.expander(f"✅ CONCLUÍRAM ({len(bateu_meta)})", expanded=False):
                            for _, row in bateu_meta.iterrows():
                                st.write(f"✔️ {row['Nome']} ({format_to_time(row['Total_Horas'])})")
                    with col_lista2:
                        with st.expander(f"⏳ PENDENTES ({len(pendente_meta)})", expanded=True):
                            for _, row in pendente_meta.iterrows():
                                falta = 7.0 - row['Total_Horas']
                                st.write(f"❌ {row['Nome']} - {format_to_time(row['Total_Horas'])} (Faltam {format_to_time(falta)})")

            # --- GRÁFICO E EDIÇÃO ---
            st.divider()
            cg1, cg2 = st.columns([1.5, 1])
            with cg1:
                st.subheader("Capacitação por Tema")
                if not user_df.empty:
                    cor_param = "Funcionário" if len(target_users) > 1 else None
                    fig = px.bar(user_df, x="Tema", y="Horas", color=cor_param, template="plotly_dark", 
                                 color_discrete_sequence=[cor_graf] if not cor_param else px.colors.qualitative.Pastel)
                    fig.update_traces(width=0.4) 
                    st.plotly_chart(fig, use_container_width=True)
            
            with cg2:
                st.subheader("Ajustar Treinamento")
                if not user_df.empty:
                    sel_id = st.selectbox("Selecionar Registro:", user_df.index, format_func=lambda x: f"[{user_df.loc[x, 'Funcionário']}] {user_df.loc[x, 'Tema']}")
                    col_btn1, col_btn2 = st.columns(2)
                    funcionario_do_registro = user_df.loc[sel_id, 'Funcionário']
                    sou_admin = "Admin" in st.session_state.perfil
                    sou_diretoria = st.session_state.setor_usuario == "Diretoria"
                    sou_gestor = "Gestor" in st.session_state.perfil
                    eh_meu_proprio_registro = (funcionario_do_registro == st.session_state.usuario)
                    pode_gerir_total = eh_meu_proprio_registro or sou_admin
                    pode_editar = pode_gerir_total or sou_gestor or sou_diretoria
                    
                    if col_btn1.button("❌ EXCLUIR", disabled=not pode_gerir_total):
                        df_exc = carregar_dados()
                        df_exc = df_exc.drop(sel_id)
                        salvar_dados(df_exc)
                        st.rerun()
                    if col_btn2.button("📝 EDITAR", disabled=not pode_editar):
                        st.session_state.editando_id = sel_id
                    
                    if 'editando_id' in st.session_state and st.session_state.editando_id == sel_id:
                        with st.container():
                            st.markdown('<div class="edit-container">', unsafe_allow_html=True)
                            with st.form("form_ed_multi"):
                                st.write(f"Editando: **{funcionario_do_registro}**")
                                trava_campos_origem = not pode_gerir_total
                                novo_tema = st.text_input("Tema", value=user_df.loc[sel_id, 'Tema'], disabled=trava_campos_origem)
                                n_c_raw = str(user_df.loc[sel_id, 'Avaliação']).replace('.0', '')
                                idx_c = LISTA_NOTAS_CADASTRO.index(n_c_raw) if n_c_raw in LISTA_NOTAS_CADASTRO else 0
                                nova_nota_colab = st.selectbox("Satisfação Colab.", LISTA_NOTAS_CADASTRO, index=idx_c, disabled=trava_campos_origem)
                                
                                pode_avaliar_lider = (sou_gestor or sou_diretoria or sou_admin) and not eh_meu_proprio_registro
                                n_l_raw = str(user_df.loc[sel_id, 'Nota_Lider']).replace('.0', '')
                                idx_l = LISTA_NOTAS_CADASTRO.index(n_l_raw) if n_l_raw in LISTA_NOTAS_CADASTRO else 0
                                
                                if sou_gestor or sou_diretoria or sou_admin:
                                    nova_nota_lider = st.selectbox("Avaliação Líder (Privada)", LISTA_NOTAS_CADASTRO, index=idx_l, disabled=not pode_avaliar_lider)
                                else: nova_nota_lider = n_l_raw

                                h_dec = user_df.loc[sel_id, 'Horas']; h_ed, m_total = int(h_dec), (h_dec - int(h_dec)) * 60
                                m_ed, s_ed = int(m_total), int(round((m_total - int(m_total)) * 60))
                                c_h, c_m, c_s = st.columns(3)
                                nh = c_h.number_input("Hora", 0, 23, h_ed, disabled=trava_campos_origem)
                                nm = c_m.number_input("Minuto", 0, 59, m_ed, disabled=trava_campos_origem)
                                ns = c_s.number_input("Segundo", 0, 59, s_ed, disabled=trava_campos_origem)

                                if st.form_submit_button("SALVAR"):
                                    df_b = carregar_dados()
                                    total_h_nova = nh + (nm/60) + (ns/3600)
                                    df_b.loc[sel_id, ["Tema", "Horas", "Avaliação", "Nota_Lider"]] = [novo_tema, total_h_nova, nova_nota_colab, nova_nota_lider]
                                    salvar_dados(df_b)
                                    del st.session_state.editando_id; st.rerun()
                            if st.button("Cancelar"): del st.session_state.editando_id; st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

            # --- HISTÓRICO ---
            st.divider(); st.subheader("📋 Histórico Detalhado")
            if not user_df.empty:
                disp = user_df.copy()
                def mascarar_nota_privada(row):
                    if row['Funcionário'] == st.session_state.usuario and "Admin" not in st.session_state.perfil: return "Nota Indisponível"
                    return row['Nota_Lider']
                disp["Nota_Lider"] = disp.apply(mascarar_nota_privada, axis=1)
                disp["Horas"] = disp["Horas"].apply(format_to_time)
                disp["Data"] = disp["Data"].dt.strftime('%d/%m/%Y')
                disp = disp.rename(columns={"Avaliação": "Satisfação Colab.", "Nota_Lider": "Avaliação Líder (Privada)"})
                cols_exibir = ["Data", "Funcionário", "Tema", "Horas", "Líder", "Satisfação Colab."]
                if any(p in st.session_state.perfil for p in ["Gestor", "Admin"]) or st.session_state.setor_usuario == "Diretoria": cols_exibir.append("Avaliação Líder (Privada)")
                st.dataframe(disp[cols_exibir], use_container_width=True)

    # --- LÓGICA REGISTRO ---
    elif menu == "Registrar Curso":
        st.markdown('<h1 class="main-title-logged">NOVO REGISTRO</h1>', unsafe_allow_html=True)
        with st.form("form_reg"):
            tema = st.text_input("Tema do Treinamento"); data = st.date_input("Data", format="DD/MM/YYYY")
            c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
            h, m, s = c1.number_input("Hora", 0, 23), c2.number_input("Minuto", 0, 59), c3.number_input("Segundo", 0, 59)
            nota_reg = c4.selectbox("Satisfação (1 a 10)", LISTA_NOTAS_CADASTRO, index=0); lider = st.selectbox("Líder Responsável", LISTA_LIDERES)
            if st.form_submit_button("SALVAR"):
                if not tema or lider == LISTA_LIDERES[0] or nota_reg == "Selecione...": st.error("Preencha tudo.")
                else:
                    total = h + (m/60) + (s/3600)
                    nova = pd.DataFrame([{"Data": data.strftime("%d/%m/%Y"), "Funcionário": st.session_state.usuario, "Setor": st.session_state.setor_usuario, "Líder": lider, "Tema": tema, "Horas": total, "Avaliação": nota_reg, "Nota_Lider": "-"}])
                    df_full = pd.concat([carregar_dados(), nova], ignore_index=True)
                    salvar_dados(df_full)
                    st.success("Registrado!"); st.rerun()

    # --- LÓGICA RELATÓRIO ---
    elif menu == "Relatório Geral":
        st.markdown('<h1 class="main-title-logged">RELATÓRIO DE DESEMPENHO</h1>', unsafe_allow_html=True)
        df_atual = carregar_dados()
        
        if not df_atual.empty and not df_atual["Data"].isnull().all():
            st.subheader("📈 Evolução Mensal da Equipe (Últimos 6 Meses)")
            df_hist = df_atual.copy()
            df_hist = df_hist.set_index('Data').resample('M')['Horas'].sum().reset_index()
            df_hist = df_hist.tail(6)
            fig_evolucao = px.line(df_hist, x='Data', y='Horas', markers=True, template="plotly_dark", color_discrete_sequence=["#ff4b4b"])
            st.plotly_chart(fig_evolucao, use_container_width=True)
            st.divider()

            # Filtros de Relatório
            if "Admin" in st.session_state.perfil or st.session_state.setor_usuario == "Diretoria":
                col_f1, col_f2, col_f3 = st.columns(3); f_setor = col_f1.selectbox("Filtrar Setor", ["Todos"] + LISTA_SETORES[1:]); df_rel = df_atual.copy()
                if f_setor != "Todos": df_rel = df_rel[df_rel["Setor"] == f_setor]
                lista_colabs = ["Todos"] + sorted(df_rel["Funcionário"].unique().tolist()); f_colab = col_f2.selectbox("Filtrar Colaborador", lista_colabs)
                if f_colab != "Todos": df_rel = df_rel[df_rel["Funcionário"] == f_colab]
                f_mes = col_f3.selectbox("Filtrar Mês", ["Todos"] + LISTA_MESES)
            elif "Gestor" in st.session_state.perfil:
                col_f1, col_f2, col_f3 = st.columns(3); f_setor = st.session_state.setor_usuario; col_f1.info(f"Setor: {f_setor}"); df_rel = df_atual[df_atual["Setor"] == f_setor].copy()
                lista_colabs = ["Todos"] + sorted(df_rel["Funcionário"].unique().tolist()); f_colab = col_f2.selectbox("Filtrar Colaborador", lista_colabs)
                if f_colab != "Todos": df_rel = df_rel[df_rel["Funcionário"] == f_colab]
                f_mes = col_f3.selectbox("Filtrar Mês", ["Todos"] + LISTA_MESES)
            else:
                col_f1, col_f3 = st.columns([1, 2]); df_rel = df_atual[df_atual["Funcionário"] == st.session_state.usuario].copy(); col_f1.info(f"Usuário: {st.session_state.usuario}"); f_mes = col_f3.selectbox("Filtrar Mês", ["Todos"] + LISTA_MESES)

            if f_mes != "Todos": df_rel = df_rel[df_rel["Data"].dt.month == LISTA_MESES.index(f_mes)+1]
            
            # Exportação Excel
            if not df_rel.empty:
                towrite = io.BytesIO()
                df_export = df_rel.copy()
                df_export['Data'] = df_export['Data'].dt.strftime('%d/%m/%Y')
                df_export.to_excel(towrite, index=False, engine='openpyxl')
                st.download_button(label="📥 Baixar Relatório Atual (Excel)", data=towrite.getvalue(), file_name=f"Relatorio_Barbosa_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.ms-excel")

                # Cards de Conquistas ou Ranking
                if any(p in st.session_state.perfil for p in ["Gestor", "Admin"]) or st.session_state.setor_usuario == "Diretoria":
                    st.subheader("🏆 Ranking de Notas (Líder)")
                    df_ranking = df_rel.copy()
                    df_ranking["Nota_Lider_Num"] = pd.to_numeric(df_ranking["Nota_Lider"], errors='coerce')
                    df_ranking = df_ranking.dropna(subset=['Nota_Lider_Num'])
                    if not df_ranking.empty:
                        ranking = df_ranking.groupby("Funcionário")["Nota_Lider_Num"].mean().reset_index().sort_values(by="Nota_Lider_Num", ascending=False).reset_index(drop=True)
                        ranking.index += 1; ranking["Média Final"] = ranking["Nota_Lider_Num"].map("{:.1f} ⭐".format)
                        st.table(ranking[["Funcionário", "Média Final"]])
                else:
                    st.subheader(f"🌟 Minhas Conquistas")
                    total_t, total_h = len(df_rel), format_to_time(df_rel["Horas"].sum()); tema_destaque = df_rel["Tema"].mode()[0] if not df_rel.empty else "-"
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(f'<div class="metric-card" style="border-bottom: 4px solid #007BFF;"><div class="metric-label">Treinos</div><div class="metric-value">{total_t}</div></div>', unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="metric-card" style="border-bottom: 4px solid #28A745;"><div class="metric-label">Horas</div><div class="metric-value">{total_h}</div></div>', unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="metric-card" style="border-bottom: 4px solid #6F42C1;"><div class="metric-label">Especialidade</div><div class="metric-value" style="font-size: 18px;">{tema_destaque}</div></div>', unsafe_allow_html=True)

    # --- PAINEL ADMINISTRATIVO ---
    elif menu == "Painel Administrativo":
        st.markdown('<h1 class="main-title-logged">PAINEL ADMINISTRATIVO</h1>', unsafe_allow_html=True)
        udf = carregar_usuarios()
        
        # Alertas de Inatividade
        st.subheader("⚠️ Atenção Crítica (Inativos > 15 dias)")
        df_inat = carregar_dados()
        if not df_inat.empty and not df_inat["Data"].isnull().all():
            hoje = datetime.now()
            ultimos_registros = df_inat.groupby("Funcionário")["Data"].max().reset_index()
            alertas = []
            for _, u_row in udf.iterrows():
                nome_u = u_row['usuario']
                reg = ultimos_registros[ultimos_registros["Funcionário"] == nome_u]
                if reg.empty: alertas.append(f"🔴 {nome_u}: Sem registros.")
                else:
                    dias = (hoje - reg.iloc[0]['Data']).days
                    if dias > 15: alertas.append(f"🟠 {nome_u}: Inativo há {dias} dias.")
            if alertas:
                for a in alertas: st.markdown(f'<div class="inactive-alert">{a}</div>', unsafe_allow_html=True)
            else: st.success("Equipe engajada!")

        # Gestão de Usuários
        t1, t2, t3 = st.tabs(["📋 Lista", "➕ Novo", "🛠️ Editar"])
        with t1:
            st.dataframe(udf, use_container_width=True)
        with t2:
            with st.form("form_nu", clear_on_submit=True):
                c_u, c_s = st.columns(2); nu, ns = c_u.text_input("Nome"), c_s.text_input("Senha", type="password")
                c_set, c_perf = st.columns(2); nset = c_set.selectbox("Setor", LISTA_SETORES[1:])
                np = c_perf.multiselect("Perfil", ["Comum", "Gestor", "Editor", "Admin"], default=["Comum"])
                if st.form_submit_button("CRIAR"):
                    if nu and ns:
                        new_u = pd.DataFrame([{"usuario": nu, "senha": ns, "perfil": str(np), "setor": nset}])
                        salvar_usuarios(pd.concat([udf, new_u], ignore_index=True))
                        st.success("Criado!"); st.rerun()
        with t3:
            u_sel = st.selectbox("Escolha para editar:", udf['usuario'].tolist())
            d = udf[udf['usuario'] == u_sel].iloc[0]
            with st.form("form_ed_adm"):
                es = st.text_input("Senha", value=str(d['senha']))
                eset = st.selectbox("Setor", LISTA_SETORES[1:], index=LISTA_SETORES[1:].index(d['setor']) if d['setor'] in LISTA_SETORES else 0)
                ep = st.multiselect("Perfil", ["Comum", "Gestor", "Editor", "Admin"], default=converter_perfil(d['perfil']))
                if st.form_submit_button("ATUALIZAR"):
                    udf.loc[udf['usuario'] == u_sel, ["senha", "perfil", "setor"]] = [es, str(ep), eset]
                    salvar_usuarios(udf); st.success("OK!"); st.rerun()

    if st.sidebar.button("SAIR"):
        st.session_state.autenticado = False
        st.rerun()