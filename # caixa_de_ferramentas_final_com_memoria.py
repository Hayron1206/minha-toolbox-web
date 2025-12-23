# caixa_de_ferramentas_final_com_memoria_de_pasta.py

# --- 1. IMPORTAÇÕES DE BIBLIOTECAS PADRÃO ---
import os
import shutil
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import time
import math
import sys
import hashlib
import json

# --- 2. IMPORTAÇÕES DE BIBLIOTECAS EXTERNAS ---
try:
    import pandas as pd
    from PIL import Image, ImageTk
    import fitz  # PyMuPDF
    import qrcode
    LIBS_INSTALADAS = True
except ImportError:
    LIBS_INSTALADAS = False

# --- 3. CONFIGURAÇÕES GLOBAIS DE ESTILO E TEMA ---
PAD_X, PAD_Y = 10, 5
FONT_LABEL = ("Segoe UI", 11)
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_BUTTON = ("Segoe UI", 10, "bold")
CONFIG_FILE = Path.home() / ".toolbox_config.json"
LAST_PATHS = {}

# --- Paletas de Cores para os Temas ---
THEMES = {
    "light": {
        "bg": "#f0f0f0", "fg": "black", "entry_bg": "white", "accent": "#0078D7",
        "notebook_bg": "#f0f0f0", "tab_bg": "#e0e0e0", "tab_fg": "black", "tab_active_bg": "#f0f0f0"
    },
    "dark": {
        "bg": "#2e2e2e", "fg": "white", "entry_bg": "#3c3c3c", "accent": "#0078D7",
        "notebook_bg": "#2e2e2e", "tab_bg": "#3c3c3c", "tab_fg": "white", "tab_active_bg": "#2e2e2e"
    }
}

# ############################################################################
# --- GERENCIAMENTO DE CONFIGURAÇÃO E CAMINHOS ---
# ############################################################################

def _save_last_path(key, path):
    """Salva o diretório de um caminho selecionado."""
    if path:
        dir_path = Path(path).parent if Path(path).is_file() else Path(path)
        LAST_PATHS[key] = str(dir_path)
        config = {"theme": current_theme.get(), "last_paths": LAST_PATHS}
        save_config(config)

def ask_open_file_with_memory(key, **options):
    options['initialdir'] = LAST_PATHS.get(key, Path.home())
    filepath = filedialog.askopenfilename(**options)
    if filepath: _save_last_path(key, filepath)
    return filepath

def ask_open_files_with_memory(key, **options):
    options['initialdir'] = LAST_PATHS.get(key, Path.home())
    filepaths = filedialog.askopenfilenames(**options)
    if filepaths: _save_last_path(key, filepaths[0])
    return filepaths

def ask_directory_with_memory(key, **options):
    options['initialdir'] = LAST_PATHS.get(key, Path.home())
    dirpath = filedialog.askdirectory(**options)
    if dirpath: _save_last_path(key, dirpath)
    return dirpath

def ask_save_as_with_memory(key, **options):
    options['initialdir'] = LAST_PATHS.get(key, Path.home())
    filepath = filedialog.asksaveasfilename(**options)
    if filepath: _save_last_path(key, filepath)
    return filepath

# ############################################################################
# --- ARQUITETURA DE OTIMIZAÇÃO E COMPONENTES AUXILIARES ---
# ############################################################################

class TaskRunner:
    """Gerencia a execução de uma função pesada em uma thread separada."""
    def __init__(self, tab_frame):
        self.tab_frame = tab_frame
        self.task_queue = queue.Queue()

    def run_task(self, task_func, on_done, *args, progress_bar=None, status_label=None):
        self.progress_bar = progress_bar
        self.status_label = status_label
        self.on_done = on_done
        thread = threading.Thread(target=self._task_wrapper, args=(task_func, args), daemon=True)
        thread.start()
        self.tab_frame.after(100, self.monitor_queue)

    def _task_wrapper(self, task_func, args):
        try:
            result = task_func(self.task_queue, *args)
            self.task_queue.put({'type': 'done', 'result': result})
        except Exception as e:
            self.task_queue.put({'type': 'error', 'message': str(e)})

    def monitor_queue(self):
        try:
            msg = self.task_queue.get(block=False)
            if msg['type'] == 'progress':
                if self.progress_bar:
                    if 'max' in msg: self.progress_bar['maximum'] = msg['max']
                    self.progress_bar['value'] = msg.get('value', 0)
                if self.status_label and 'text' in msg: self.status_label.config(text=msg['text'])
            elif msg['type'] == 'done':
                self.on_done(True, msg.get('result'))
                return
            elif msg['type'] == 'error':
                messagebox.showerror("Erro na Tarefa", msg['message'], parent=self.tab_frame)
                self.on_done(False, None)
                return
        except queue.Empty:
            pass
        self.tab_frame.after(100, self.monitor_queue)

def criar_widgets_progresso(parent_frame):
    """Cria e retorna um frame contendo uma barra de progresso e um label de status."""
    frame = ttk.Frame(parent_frame)
    progresso = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
    progresso.pack(pady=PAD_Y, fill='x')
    label_progresso = ttk.Label(frame, text="")
    label_progresso.pack(pady=PAD_Y)
    return frame, progresso, label_progresso

def _validate_numeric_input(P):
    """Valida a entrada para permitir apenas dígitos ou um campo vazio."""
    return P.isdigit() or P == ""


# ############################################################################
# --- FERRAMENTAS INDIVIDUAIS ---
# ############################################################################

def criar_aba_qrcode(tab_frame, vcmd):
    if not all(lib in sys.modules for lib in ['qrcode', 'PIL']):
        ttk.Label(tab_frame, text="Instale 'qrcode' e 'Pillow'.\npy -m pip install qrcode[pil]", font=FONT_LABEL, foreground="red").pack(pady=50); return
    qr_image_to_save = None; texto_entrada_var = tk.StringVar()
    def gerar_e_mostrar_qrcode():
        nonlocal qr_image_to_save; texto = texto_entrada_var.get().strip()
        if not texto: messagebox.showwarning("Atenção", "Insira um texto ou link.", parent=tab_frame); return
        try:
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=2); qr.add_data(texto); qr.make(fit=True)
            qr_image_to_save = qr.make_image(fill_color="black", back_color="white")
            preview_image = qr_image_to_save.resize((250, 250), Image.Resampling.NEAREST); photo = ImageTk.PhotoImage(preview_image)
            label_preview.config(image=photo, text=""); label_preview.image = photo; btn_salvar['state'] = 'normal'
            btn_salvar.focus_set()
        except Exception as e: messagebox.showerror("Erro", f"Ocorreu um erro ao gerar o QR Code:\n{e}", parent=tab_frame)
    def salvar_imagem():
        if not qr_image_to_save: messagebox.showerror("Erro", "Nenhum QR Code gerado.", parent=tab_frame); return
        caminho = ask_save_as_with_memory("qrcode_save", title="Salvar QR Code", defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if caminho:
            try: qr_image_to_save.save(caminho); messagebox.showinfo("Sucesso", f"QR Code salvo em:\n{caminho}", parent=tab_frame)
            except Exception as e: messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar a imagem:\n{e}", parent=tab_frame)
    ttk.Label(tab_frame, text="Gerador de QR Code", font=FONT_TITLE).pack(pady=(PAD_Y, PAD_Y * 2))
    f_entrada = ttk.Labelframe(tab_frame, text="1. Insira o texto ou link", padding=PAD_X); f_entrada.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Entry(f_entrada, textvariable=texto_entrada_var, font=FONT_LABEL).pack(fill='x', expand=True, ipady=4)
    btn_gerar = ttk.Button(tab_frame, text="Gerar QR Code", style="Accent.TButton", command=gerar_e_mostrar_qrcode); btn_gerar.pack(pady=PAD_Y*2, ipadx=10, ipady=4)
    f_preview = ttk.Labelframe(tab_frame, text="2. Pré-visualização", padding=PAD_X); f_preview.pack(pady=PAD_Y)
    label_preview = ttk.Label(f_preview, text="\nAguardando...\n", width=35, font=FONT_LABEL, relief='solid', anchor='center'); label_preview.pack(pady=PAD_Y, padx=PAD_X)
    btn_salvar = ttk.Button(tab_frame, text="Salvar Imagem...", command=salvar_imagem, state='disabled'); btn_salvar.pack(pady=(PAD_Y*2, PAD_Y))


def criar_aba_unir_planilhas(tab_frame, vcmd):
    if not LIBS_INSTALADAS:
        ttk.Label(tab_frame, text="Instale 'pandas' e 'openpyxl'.", font=FONT_LABEL, foreground="red").pack(pady=50); return

    state = {
        "p1_path": tk.StringVar(), "p2_path": tk.StringVar(), "saida_path": tk.StringVar(),
        "chave": tk.StringVar(), "df1": None, "df2": None,
        "colunas_selecionadas_df1": set(), "colunas_selecionadas_df2": set(),
    }
    main_frame = ttk.Frame(tab_frame)
    selection_frame = ttk.Frame(tab_frame)
    main_frame.pack(fill="both", expand=True)

    def show_frame(frame_to_show):
        main_frame.pack_forget(); selection_frame.pack_forget()
        frame_to_show.pack(fill="both", expand=True)

    def popular_tela_selecao(df, nome_planilha, state_key):
        for widget in selection_frame.winfo_children(): widget.destroy()
        
        ttk.Label(selection_frame, text=f"Selecionar Colunas - {nome_planilha}", font=FONT_TITLE).pack(pady=(PAD_Y, PAD_Y * 2))
        
        dual_list_frame = ttk.Frame(selection_frame); dual_list_frame.pack(fill='both', expand=True, padx=PAD_X, pady=PAD_Y)
        dual_list_frame.columnconfigure(0, weight=1); dual_list_frame.columnconfigure(2, weight=1)

        f_disponiveis = ttk.Labelframe(dual_list_frame, text="Colunas Disponíveis"); f_disponiveis.grid(row=1, column=0, sticky='nsew', padx=5)
        f_disponiveis.rowconfigure(1, weight=1)
        search_var = tk.StringVar()
        ttk.Entry(f_disponiveis, textvariable=search_var).pack(fill='x', padx=5, pady=5)
        list_disponiveis = tk.Listbox(f_disponiveis, selectmode='extended', exportselection=False); list_disponiveis.pack(fill='both', expand=True, padx=5, pady=5)
        
        f_selecionadas = ttk.Labelframe(dual_list_frame, text="Colunas Selecionadas"); f_selecionadas.grid(row=1, column=2, sticky='nsew', padx=5)
        f_selecionadas.rowconfigure(0, weight=1)
        list_selecionadas = tk.Listbox(f_selecionadas, selectmode='extended', exportselection=False); list_selecionadas.pack(fill='both', expand=True, padx=5, pady=5)

        todas_colunas = sorted(list(df.columns))
        colunas_ja_selecionadas = state[state_key]
        for col in todas_colunas:
            if col in colunas_ja_selecionadas: list_selecionadas.insert(tk.END, col)
            else: list_disponiveis.insert(tk.END, col)
        
        def update_search(*args):
            termo = search_var.get().lower()
            list_disponiveis.delete(0, tk.END)
            for col in todas_colunas:
                if termo in col.lower() and col not in list_selecionadas.get(0, tk.END): list_disponiveis.insert(tk.END, col)
        search_var.trace_add("write", update_search)

        f_botoes = ttk.Frame(dual_list_frame); f_botoes.grid(row=1, column=1, sticky='ns', padx=5)
        
        def mover(lista_origem, lista_destino, todos=False):
            selecionados_indices = lista_origem.curselection()
            if todos: selecionados_indices = range(lista_origem.size())
            if not selecionados_indices: return
            
            itens_para_mover = []
            for i in selecionados_indices:
                if lista_origem.get(i) != state["chave"].get():
                    itens_para_mover.append(lista_origem.get(i))

            for item in sorted(itens_para_mover): lista_destino.insert(tk.END, item)
            
            indices_para_deletar = []
            for i in selecionados_indices:
                if lista_origem.get(i) in itens_para_mover:
                    indices_para_deletar.append(i)

            for i in sorted(indices_para_deletar, reverse=True): lista_origem.delete(i)
        
        ttk.Button(f_botoes, text=">", command=lambda: mover(list_disponiveis, list_selecionadas)).pack(pady=5)
        ttk.Button(f_botoes, text="<", command=lambda: mover(list_selecionadas, list_disponiveis)).pack(pady=5)
        ttk.Button(f_botoes, text=">>", command=lambda: mover(list_disponiveis, list_selecionadas, todos=True)).pack(pady=20)
        ttk.Button(f_botoes, text="<<", command=lambda: mover(list_selecionadas, list_disponiveis, todos=True)).pack(pady=5)
        
        chave = state["chave"].get()
        if chave in list_disponiveis.get(0, tk.END):
            idx_chave_origem = list_disponiveis.get(0, tk.END).index(chave)
            list_disponiveis.select_set(idx_chave_origem)
            mover(list_disponiveis, list_selecionadas)
        
        if chave in list_selecionadas.get(0, tk.END):
            idx = list_selecionadas.get(0, tk.END).index(chave)
            list_selecionadas.itemconfig(idx, {'foreground':'gray'})

        def on_confirm():
            state[state_key] = set(list_selecionadas.get(0, tk.END))
            if state_key == "colunas_selecionadas_df1": btn_selecionar_cols1.config(text=f"Alterar Colunas P1 ({len(state[state_key])} sel.)")
            else: btn_selecionar_cols2.config(text=f"Alterar Colunas P2 ({len(state[state_key])} sel.)")
            btn_unir['state'] = 'normal' if state["colunas_selecionadas_df1"] and state["colunas_selecionadas_df2"] else 'disabled'
            show_frame(main_frame)

        ttk.Button(selection_frame, text="Confirmar e Voltar", command=on_confirm, style="Accent.TButton").pack(pady=PAD_Y * 2)
        show_frame(selection_frame)

    def carregar_planilhas():
        try:
            p1, p2, chave = state["p1_path"].get(), state["p2_path"].get(), state["chave"].get()
            if not all([p1, p2, chave]): raise ValueError("Preencha todos os campos.")
            state["df1"] = pd.read_excel(p1) if p1.endswith(('.xlsx', '.xls')) else pd.read_csv(p1)
            state["df2"] = pd.read_excel(p2) if p2.endswith(('.xlsx', '.xls')) else pd.read_csv(p2)
            if chave not in state["df1"].columns or chave not in state["df2"].columns: raise ValueError(f"A chave '{chave}' não existe em ambas as planilhas.")
            
            state["colunas_selecionadas_df1"] = set(state["df1"].columns)
            state["colunas_selecionadas_df2"] = set(state["df2"].columns)
            btn_selecionar_cols1.config(state='normal', text=f"Selecionar Colunas P1 ({len(state['df1'].columns)} sel.)")
            btn_selecionar_cols2.config(state='normal', text=f"Selecionar Colunas P2 ({len(state['df2'].columns)} sel.)")
            btn_unir.config(state='normal')
            messagebox.showinfo("Pronto", "Planilhas carregadas.", parent=tab_frame)
            btn_selecionar_cols1.focus_set()
        except Exception as e: messagebox.showerror("Erro ao Carregar", str(e), parent=tab_frame)

    def executar_uniao_final(q):
        saida, chave = state["saida_path"].get(), state["chave"].get()
        if not saida: raise ValueError("Escolha um local para salvar o arquivo.")
        if not state["colunas_selecionadas_df1"] or not state["colunas_selecionadas_df2"]: raise ValueError("Selecione as colunas.")
        if chave not in state["colunas_selecionadas_df1"] or chave not in state["colunas_selecionadas_df2"]: raise ValueError(f"A chave '{chave}' deve estar selecionada.")
        
        df1_copy, df2_copy = state["df1"].copy(), state["df2"].copy()
        df1_copy[chave] = df1_copy[chave].astype(str).str.strip().str.lower()
        df2_copy[chave] = df2_copy[chave].astype(str).str.strip().str.lower()
        
        df_final = pd.merge(df1_copy[list(state["colunas_selecionadas_df1"])], df2_copy[list(state["colunas_selecionadas_df2"])], on=chave, how="inner")
        df_final.to_excel(saida, index=False)
        return f"Planilha unida com {len(df_final)} linhas salva!"

    def on_unir_done(success, result):
        if success and result: messagebox.showinfo("Sucesso", result, parent=tab_frame)

    f1 = ttk.Labelframe(main_frame, text="1. Planilha Principal", padding=PAD_X); f1.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Entry(f1, textvariable=state['p1_path'], font=FONT_LABEL).pack(side='left', fill='x', expand=True, padx=(0, PAD_X))
    ttk.Button(f1, text="Procurar...", command=lambda: state['p1_path'].set(ask_open_file_with_memory("unir_p1", filetypes=[("Planilhas", "*.xlsx *.xls *.csv")]) or "")).pack(side='left')
    f2 = ttk.Labelframe(main_frame, text="2. Planilha Secundária", padding=PAD_X); f2.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Entry(f2, textvariable=state['p2_path'], font=FONT_LABEL).pack(side='left', fill='x', expand=True, padx=(0, PAD_X))
    ttk.Button(f2, text="Procurar...", command=lambda: state['p2_path'].set(ask_open_file_with_memory("unir_p2", filetypes=[("Planilhas", "*.xlsx *.xls *.csv")]) or "")).pack(side='left')
    f_chave = ttk.Labelframe(main_frame, text="3. Chave de União (Nome da coluna em comum)", padding=PAD_X); f_chave.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Entry(f_chave, textvariable=state['chave'], font=FONT_LABEL).pack(fill='x')
    ttk.Button(main_frame, text="Carregar Planilhas", command=carregar_planilhas).pack(pady=(PAD_Y*2, PAD_Y))
    f_selecao = ttk.Labelframe(main_frame, text="4. Selecionar Colunas", padding=PAD_X); f_selecao.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    btn_selecionar_cols1 = ttk.Button(f_selecao, text="Selecionar Colunas P1", state="disabled", command=lambda: popular_tela_selecao(state["df1"], "Planilha Principal", "colunas_selecionadas_df1"))
    btn_selecionar_cols1.pack(side='left', expand=True, fill='x', padx=PAD_X, pady=PAD_Y)
    btn_selecionar_cols2 = ttk.Button(f_selecao, text="Selecionar Colunas P2", state="disabled", command=lambda: popular_tela_selecao(state["df2"], "Planilha Secundária", "colunas_selecionadas_df2"))
    btn_selecionar_cols2.pack(side='left', expand=True, fill='x', padx=PAD_X, pady=PAD_Y)
    f_saida = ttk.Labelframe(main_frame, text="5. Salvar Resultado", padding=PAD_X); f_saida.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Entry(f_saida, textvariable=state['saida_path'], font=FONT_LABEL).pack(side='left', fill='x', expand=True, padx=(0, PAD_X))
    ttk.Button(f_saida, text="Salvar em...", command=lambda: state['saida_path'].set(ask_save_as_with_memory("unir_save", defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")]) or "")).pack(side='left')
    btn_unir = ttk.Button(main_frame, text="Unir Planilhas", command=lambda: TaskRunner(tab_frame).run_task(executar_uniao_final, on_unir_done), style="Accent.TButton", state="disabled")
    btn_unir.pack(pady=(PAD_Y*2, PAD_Y), ipadx=10, ipady=5)

def criar_aba_detector_duplicatas(tab_frame, vcmd):
    caminho_arquivo_var = tk.StringVar()
    def selecionar_arquivo():
        caminho = ask_open_file_with_memory("duplicatas_open", title="Selecione o arquivo .txt", filetypes=[("Arquivos de texto", "*.txt")])
        if caminho: 
            caminho_arquivo_var.set(caminho)
            btn_processar['state'] = 'normal'
            btn_processar.focus_set()
    def executar_processo():
        caminho_arquivo = caminho_arquivo_var.get()
        if not caminho_arquivo: return
        try:
            lista = [item.strip() for item in Path(caminho_arquivo).read_text(encoding='utf-8').splitlines() if item.strip()]
            unicos, vistos, duplicados = [], set(), set()
            for item in lista:
                if item in vistos: duplicados.add(item)
                else: vistos.add(item); unicos.append(item)
            pasta_destino = ask_directory_with_memory("duplicatas_save", title="Escolha onde salvar os arquivos de resultado")
            if not pasta_destino: return
            saida = Path(pasta_destino)
            (saida / "lista_unicos.txt").write_text('\n'.join(unicos), encoding='utf-8')
            (saida / "lista_duplicados.txt").write_text('\n'.join(sorted(list(duplicados))), encoding='utf-8')
            messagebox.showinfo("Sucesso", f"{len(unicos)} únicos e {len(duplicados)} duplicados encontrados.\n\nArquivos salvos em:\n{pasta_destino}", parent=tab_frame)
        except Exception as e: messagebox.showerror("Erro", str(e), parent=tab_frame)
    ttk.Label(tab_frame, text="Encontrar Itens Únicos e Duplicados", font=FONT_TITLE).pack(pady=(PAD_Y, PAD_Y * 2))
    f_sel = ttk.Labelframe(tab_frame, text="1. Selecionar Arquivo de Texto", padding=PAD_X); f_sel.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    entry_arquivo = ttk.Entry(f_sel, textvariable=caminho_arquivo_var, font=FONT_LABEL, state='readonly'); entry_arquivo.pack(side='left', fill='x', expand=True, padx=(0, PAD_X))
    btn_selecionar = ttk.Button(f_sel, text="Procurar...", command=selecionar_arquivo); btn_selecionar.pack(side='left')
    f_exec = ttk.Labelframe(tab_frame, text="2. Executar", padding=PAD_X); f_exec.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    btn_processar = ttk.Button(f_exec, text="Processar e Salvar em...", style="Accent.TButton", command=executar_processo, state='disabled'); btn_processar.pack(pady=PAD_Y)

def criar_aba_hash(tab_frame, vcmd):
    task_runner = TaskRunner(tab_frame)
    arquivo_var = tk.StringVar()
    md5_var = tk.StringVar()
    sha256_var = tk.StringVar()

    def selecionar_arquivo():
        caminho = ask_open_file_with_memory("hash_open", title="Selecione um arquivo")
        if caminho:
            arquivo_var.set(caminho)
            md5_var.set("")
            sha256_var.set("")
            btn_calcular['state'] = 'normal'
            btn_calcular.focus_set()

    def processo_hash(q, arquivo):
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        tamanho_total = os.path.getsize(arquivo)
        lido = 0
        buffer_size = 65536

        q.put({'type': 'progress', 'max': tamanho_total, 'value': 0, 'text': "Calculando..."})
        
        with open(arquivo, 'rb') as f:
            while True:
                data = f.read(buffer_size)
                if not data:
                    break
                md5.update(data)
                sha256.update(data)
                lido += len(data)
                q.put({'type': 'progress', 'value': lido})
        
        q.put({'type': 'progress', 'text': "Cálculo concluído!"})
        return {'md5': md5.hexdigest(), 'sha256': sha256.hexdigest()}

    def on_hash_done(success, result):
        if success:
            md5_var.set(result['md5'])
            sha256_var.set(result['sha256'])
        btn_calcular['state'] = 'normal'
        btn_selecionar['state'] = 'normal'

    def iniciar_calculo():
        arquivo = arquivo_var.get()
        if not arquivo or not os.path.exists(arquivo):
            messagebox.showerror("Erro", "Por favor, selecione um arquivo válido.", parent=tab_frame)
            return
        
        btn_calcular['state'] = 'disabled'
        btn_selecionar['state'] = 'disabled'
        md5_var.set("Calculando...")
        sha256_var.set("Calculando...")
        
        task_runner.run_task(processo_hash, on_hash_done, arquivo, progress_bar=progresso, status_label=label_progresso)
    
    def copiar_para_clipboard(valor):
        if not valor: return
        root = tab_frame.winfo_toplevel()
        root.clipboard_clear()
        root.clipboard_append(valor)
        messagebox.showinfo("Copiado", "Hash copiado para a área de transferência.", parent=tab_frame)


    ttk.Label(tab_frame, text="Calculadora de Hash de Arquivos", font=FONT_TITLE).pack(pady=(PAD_Y, PAD_Y * 2))

    f_sel = ttk.Labelframe(tab_frame, text="1. Selecionar Arquivo", padding=PAD_X); f_sel.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    entry_arquivo = ttk.Entry(f_sel, textvariable=arquivo_var, font=FONT_LABEL, state='readonly'); entry_arquivo.pack(side='left', fill='x', expand=True, padx=(0, PAD_X))
    btn_selecionar = ttk.Button(f_sel, text="Procurar...", command=selecionar_arquivo); btn_selecionar.pack(side='left')

    f_exec = ttk.Labelframe(tab_frame, text="2. Executar Cálculo", padding=PAD_X); f_exec.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    btn_calcular = ttk.Button(f_exec, text="Calcular Hashes", style="Accent.TButton", command=iniciar_calculo, state='disabled'); btn_calcular.pack(pady=PAD_Y)
    
    progress_frame, progresso, label_progresso = criar_widgets_progresso(f_exec)
    progress_frame.pack(fill='x')

    f_res = ttk.Labelframe(tab_frame, text="3. Resultados", padding=PAD_X); f_res.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    
    f_md5 = ttk.Frame(f_res); f_md5.pack(fill='x', padx=5, pady=5)
    ttk.Label(f_md5, text="MD5:").pack(side='left')
    entry_md5 = ttk.Entry(f_md5, textvariable=md5_var, state='readonly', font=("Courier New", 10)); entry_md5.pack(side='left', fill='x', expand=True, padx=5)
    ttk.Button(f_md5, text="Copiar", command=lambda: copiar_para_clipboard(md5_var.get())).pack(side='left')
    
    f_sha256 = ttk.Frame(f_res); f_sha256.pack(fill='x', padx=5, pady=5)
    ttk.Label(f_sha256, text="SHA-256:").pack(side='left')
    entry_sha256 = ttk.Entry(f_sha256, textvariable=sha256_var, state='readonly', font=("Courier New", 10)); entry_sha256.pack(side='left', fill='x', expand=True, padx=5)
    ttk.Button(f_sha256, text="Copiar", command=lambda: copiar_para_clipboard(sha256_var.get())).pack(side='left')

def criar_aba_divisor_planilhas(tab_frame, vcmd):
    if not LIBS_INSTALADAS: ttk.Label(tab_frame, text="Instale 'pandas' e 'openpyxl'.", font=FONT_LABEL, foreground="red").pack(pady=50); return
    task_runner = TaskRunner(tab_frame); arquivo_selecionado = tk.StringVar(); linhas_por_arquivo = tk.StringVar(value="10000")
    def selecionar_arquivo():
        tipos = [("Planilhas", "*.csv *.xlsx *.xls"), ("Todos", "*.*")]
        arquivo = ask_open_file_with_memory("divisor_open", title="Selecione a planilha", filetypes=tipos)
        if arquivo: 
            arquivo_selecionado.set(arquivo)
            btn_dividir['state'] = 'normal'
            btn_dividir.focus_set()
    def iniciar_divisao():
        arquivo = arquivo_selecionado.get()
        try: num_linhas = int(linhas_por_arquivo.get()); assert num_linhas > 0
        except: messagebox.showerror("Erro de Entrada", "O número de linhas deve ser um inteiro > 0."); return
        if not os.path.isfile(arquivo): messagebox.showerror("Erro", "Selecione um arquivo válido."); return
        pasta_destino = ask_directory_with_memory("divisor_save", title="Salvar os arquivos em...")
        if not pasta_destino: return
        btn_dividir['state'] = 'disabled'; btn_selecionar['state'] = 'disabled'
        task_runner.run_task(processo_divisor, on_done, arquivo, num_linhas, pasta_destino, progress_bar=progresso, status_label=label_progresso)
    def on_done(success, result):
        btn_dividir['state'] = 'normal'; btn_selecionar['state'] = 'normal'
        if success: messagebox.showinfo("Sucesso", f"Planilha dividida em {result} arquivo(s)!", parent=tab_frame)
    def processo_divisor(q, arquivo_path, chunk_size, pasta_destino):
        p_arquivo = Path(arquivo_path); q.put({'type': 'progress', 'text': "Lendo arquivo de origem..."})
        df = pd.read_csv(arquivo_path) if p_arquivo.suffix.lower() == '.csv' else pd.read_excel(arquivo_path)
        total_linhas = len(df); num_arquivos = math.ceil(total_linhas / chunk_size)
        q.put({'type': 'progress', 'max': num_arquivos, 'text': f"Total de {total_linhas} linhas."}); time.sleep(1)
        for i, start_row in enumerate(range(0, total_linhas, chunk_size)):
            q.put({'type': 'progress', 'value': i, 'text': f"Gerando arquivo {i+1}/{num_arquivos}..."})
            df_chunk = df.iloc[start_row : start_row + chunk_size]; novo_nome = f"{p_arquivo.stem}_parte_{i+1}{p_arquivo.suffix}"; caminho_saida = Path(pasta_destino) / novo_nome
            if p_arquivo.suffix.lower() == '.csv': df_chunk.to_csv(caminho_saida, index=False)
            else: df_chunk.to_excel(caminho_saida, index=False)
        q.put({'type': 'progress', 'value': num_arquivos, 'text': "Divisão concluída!"}); return num_arquivos
    ttk.Label(tab_frame, text="Divisor de Planilhas", font=FONT_TITLE).pack(pady=(PAD_Y, PAD_Y * 2))
    f_sel = ttk.Labelframe(tab_frame, text="1. Selecionar Planilha (CSV ou Excel)", padding=PAD_X); f_sel.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    entry_arquivo = ttk.Entry(f_sel, textvariable=arquivo_selecionado, font=FONT_LABEL); entry_arquivo.pack(side='left', fill='x', expand=True, padx=(0, PAD_X))
    btn_selecionar = ttk.Button(f_sel, text="Procurar...", command=selecionar_arquivo); btn_selecionar.pack(side='left')
    f_conf = ttk.Labelframe(tab_frame, text="2. Configurar Divisão", padding=PAD_X); f_conf.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Label(f_conf, text="Máximo de linhas por arquivo:").pack(side='left', padx=(0, PAD_X))
    entry_linhas = ttk.Entry(f_conf, textvariable=linhas_por_arquivo, width=15, font=FONT_LABEL, validate='key', validatecommand=vcmd)
    entry_linhas.pack(side='left')
    f_exec = ttk.Labelframe(tab_frame, text="3. Executar", padding=PAD_X); f_exec.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    btn_dividir = ttk.Button(f_exec, text="Dividir e Salvar em...", style="Accent.TButton", command=iniciar_divisao, state='disabled'); btn_dividir.pack(pady=PAD_Y)
    
    progress_frame, progresso, label_progresso = criar_widgets_progresso(f_exec)
    progress_frame.pack(fill='x')


def criar_aba_organizador(tab_frame, vcmd):
    task_runner = TaskRunner(tab_frame); pasta_selecionada = tk.StringVar(); modo_organizacao = tk.StringVar(value="categoria")
    CATEGORIAS = {
        "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"], "Vídeos": [".mp4", ".mov", ".avi", ".mkv", ".wmv"], "Músicas": [".mp3", ".wav", ".aac", ".flac"],
        "Documentos": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".csv"], "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz"], "Executáveis": [".exe", ".msi"],
    }
    def selecionar_pasta():
        pasta = ask_directory_with_memory("organizador_open", title="Selecione a pasta para organizar")
        if pasta: 
            pasta_selecionada.set(pasta)
            btn_organizar['state'] = 'normal'
            btn_organizar.focus_set()
    def iniciar_organizacao():
        pasta = pasta_selecionada.get()
        if not os.path.isdir(pasta): messagebox.showerror("Erro", "Selecione uma pasta válida."); return
        btn_organizar['state'] = 'disabled'; btn_selecionar['state'] = 'disabled'
        task_runner.run_task(processo_organizador, on_done, pasta, modo_organizacao.get(), progress_bar=progresso, status_label=label_progresso)
    def on_done(success, result):
        btn_organizar['state'] = 'normal'; btn_selecionar['state'] = 'normal'
        if success: messagebox.showinfo("Sucesso", f"{result} arquivo(s) organizado(s)!", parent=tab_frame)
    def processo_organizador(q, pasta, modo):
        arquivos = [f for f in os.listdir(pasta) if os.path.isfile(os.path.join(pasta, f))]
        total = len(arquivos); q.put({'type': 'progress', 'max': total, 'text': "Analisando..."}); time.sleep(1)
        movidos = 0
        for i, nome in enumerate(arquivos):
            q.put({'type': 'progress', 'value': i, 'text': f"Movendo: {nome}"})
            caminho_arq = os.path.join(pasta, nome); ext = Path(nome).suffix.lower(); pasta_dest_nome = "Outros"
            if modo == "categoria":
                for cat, exts in CATEGORIAS.items():
                    if ext in exts: pasta_dest_nome = cat; break
            elif modo == "extensao" and ext: pasta_dest_nome = ext[1:].upper()
            caminho_dest = os.path.join(pasta, pasta_dest_nome); os.makedirs(caminho_dest, exist_ok=True); shutil.move(caminho_arq, caminho_dest); movidos += 1; time.sleep(0.05)
        q.put({'type': 'progress', 'value': total, 'text': "Organização concluída!"}); return movidos
    ttk.Label(tab_frame, text="Organizador de Arquivos", font=FONT_TITLE).pack(pady=(PAD_Y, PAD_Y * 2))
    f_sel = ttk.Labelframe(tab_frame, text="1. Selecionar Pasta", padding=PAD_X); f_sel.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Entry(f_sel, textvariable=pasta_selecionada, font=FONT_LABEL).pack(side='left', fill='x', expand=True, padx=(0, PAD_X))
    btn_selecionar = ttk.Button(f_sel, text="Procurar...", command=selecionar_pasta); btn_selecionar.pack(side='left')
    f_modo = ttk.Labelframe(tab_frame, text="2. Modo de Organização", padding=PAD_X); f_modo.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Radiobutton(f_modo, text="Por Categoria (Imagens, Documentos...)", variable=modo_organizacao, value="categoria").pack(anchor='w')
    ttk.Radiobutton(f_modo, text="Por Extensão (.JPG, .PDF...)", variable=modo_organizacao, value="extensao").pack(anchor='w')
    f_exec = ttk.Labelframe(tab_frame, text="3. Executar", padding=PAD_X); f_exec.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    btn_organizar = ttk.Button(f_exec, text="Organizar Pasta", style="Accent.TButton", command=iniciar_organizacao, state='disabled'); btn_organizar.pack(pady=PAD_Y)
    
    progress_frame, progresso, label_progresso = criar_widgets_progresso(f_exec)
    progress_frame.pack(fill='x')

def criar_aba_conversor(tab_frame, vcmd):
    task_runner = TaskRunner(tab_frame); arquivos = []; limpar_auto_var = tk.BooleanVar(value=False)
    def selecionar():
        nonlocal arquivos
        tipos = [("Arquivos Suportados", "*.pdf *.jpg *.jpeg *.png *.webp"), ("Todos", "*.*")]
        f = ask_open_files_with_memory("conversor_open", title="Selecione PDFs ou Imagens", filetypes=tipos)
        if f: 
            arquivos = list(f); label_status_selecao.config(text=f"{len(arquivos)} arquivo(s) selecionado(s).")
            btn_converter['state'] = 'normal'; btn_converter.focus_set()
    def limpar():
        nonlocal arquivos; arquivos.clear(); label_status_selecao.config(text="Nenhum arquivo selecionado."); btn_converter['state'] = 'disabled'; progresso["value"] = 0; label_progresso.config(text="")
    def iniciar():
        if not arquivos: return
        modo = combo_conversao.get(); nome_pdf = nome_pdf_var.get().strip()
        destino = ask_directory_with_memory("conversor_save", title="Salvar arquivos convertidos em...")
        if not destino: return
        btn_converter['state'] = 'disabled'; btn_selecionar['state'] = 'disabled'; btn_limpar['state'] = 'disabled'
        task_runner.run_task(processo_conversao, on_done, modo, destino, arquivos.copy(), nome_pdf, progress_bar=progresso, status_label=label_progresso)
    def on_done(success, result):
        btn_converter['state'] = 'normal'; btn_selecionar['state'] = 'normal'; btn_limpar['state'] = 'normal'
        if success: 
            messagebox.showinfo("Sucesso", "Conversão concluída!", parent=tab_frame)
            if limpar_auto_var.get(): limpar()
    def processo_conversao(q, modo, pasta_destino, lista_arquivos, nome_pdf_unico=""):
        total = len(lista_arquivos); q.put({'type': 'progress', 'max': total, 'value': 0, 'text': "Iniciando..."}); time.sleep(0.5); imagens_para_pdf = []
        for i, path in enumerate(lista_arquivos):
            nome_base = Path(path).stem
            q.put({'type': 'progress', 'value': i, 'text': f"Processando {i+1}/{total}: {Path(path).name}"})
            if modo == "PDF para Imagens (JPG)" and path.lower().endswith(".pdf"):
                doc = fitz.open(path)
                for pag_num, pag in enumerate(doc):
                    pix = pag.get_pixmap(dpi=200); pix.save(Path(pasta_destino) / f"{nome_base}_pag_{pag_num+1}.jpg")
            elif modo.startswith("Imagens para PDF") and Path(path).suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                try:
                    img = Image.open(path).convert("RGB")
                    if modo.endswith("(Separados)"): img.save(Path(pasta_destino) / f"{nome_base}.pdf")
                    elif modo.endswith("(Único arquivo)"): imagens_para_pdf.append(img)
                except Exception as e: print(f"Erro ao processar a imagem {path}: {e}")
        if imagens_para_pdf:
            q.put({'type': 'progress', 'text': "Salvando PDF unificado..."})
            final_filename = f"{Path(nome_pdf_unico).stem}.pdf" if nome_pdf_unico else f"{Path(pasta_destino).name}.pdf"
            output_path = Path(pasta_destino) / final_filename
            imagens_para_pdf[0].save(output_path, save_all=True, append_images=imagens_para_pdf[1:])
        q.put({'type': 'progress', 'value': total, 'text': "Pronto."}); return True
    ttk.Label(tab_frame, text="Conversor de PDF e Imagens", font=FONT_TITLE).pack(pady=(PAD_Y, PAD_Y * 2))
    f_sel = ttk.Labelframe(tab_frame, text="1. Selecionar Arquivos", padding=PAD_X); f_sel.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    btn_selecionar = ttk.Button(f_sel, text="Procurar...", command=selecionar); btn_selecionar.pack(side='left'); btn_limpar = ttk.Button(f_sel, text="Limpar", command=limpar); btn_limpar.pack(side='left', padx=PAD_X)
    label_status_selecao = ttk.Label(f_sel, text="Nenhum arquivo selecionado."); label_status_selecao.pack(side='left', padx=PAD_X)
    f_modo = ttk.Labelframe(tab_frame, text="2. Modo de Conversão", padding=PAD_X); f_modo.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    nome_pdf_var = tk.StringVar()
    f_nome_pdf = ttk.Frame(f_modo)
    ttk.Label(f_nome_pdf, text="Nome do arquivo PDF (opcional):").pack(side='left', padx=(0, 5))
    ttk.Entry(f_nome_pdf, textvariable=nome_pdf_var).pack(side='left', fill='x', expand=True)
    def on_combo_select(event=None):
        if combo_conversao.get() == "Imagens para PDF (Único arquivo)": f_nome_pdf.pack(fill='x', pady=(PAD_Y, 0), before=combo_conversao)
        else: f_nome_pdf.pack_forget()
    combo_conversao = ttk.Combobox(f_modo, state="readonly", font=FONT_LABEL, values=["PDF para Imagens (JPG)", "Imagens para PDF (Separados)", "Imagens para PDF (Único arquivo)"]); combo_conversao.pack(fill='x'); combo_conversao.current(0); combo_conversao.bind("<<ComboboxSelected>>", on_combo_select); on_combo_select()
    f_exec = ttk.Labelframe(tab_frame, text="3. Executar", padding=PAD_X); f_exec.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    btn_converter = ttk.Button(f_exec, text="Iniciar Conversão", style="Accent.TButton", command=iniciar, state='disabled'); btn_converter.pack(side='left', pady=PAD_Y, padx=(0, PAD_X))
    ttk.Checkbutton(f_exec, text="Limpar seleção após concluir", variable=limpar_auto_var).pack(side='left')
    progress_frame, progresso, label_progresso = criar_widgets_progresso(tab_frame); progress_frame.pack(fill='x', padx=PAD_X, pady=PAD_Y)

def criar_aba_renomeador_arquivos(tab_frame, vcmd):
    task_runner = TaskRunner(tab_frame); entrada_origem_str, entrada_destino_str = tk.StringVar(), tk.StringVar(); limpar_auto_var = tk.BooleanVar(value=False)
    def selecionar_arquivos():
        arquivos = ask_open_files_with_memory("renomeador_open", title="Selecionar arquivos")
        if arquivos: 
            entrada_origem_str.set(";".join(arquivos))
            label_status_origem.config(text=f"{len(arquivos)} arquivo(s) selecionado(s).")
            btn_executar.focus_set()
    def selecionar_destino():
        pasta = ask_directory_with_memory("renomeador_dest")
        if pasta: entrada_destino_str.set(pasta); btn_executar.focus_set()
    def limpar():
        entrada_origem_str.set(""); label_status_origem.config(text="Nenhum arquivo selecionado."); barra_progresso["value"] = 0
    def iniciar_renomeacao():
        arquivos = entrada_origem_str.get().split(";"); destino = entrada_destino_str.get()
        if not arquivos or not arquivos[0] or not os.path.isdir(destino): messagebox.showerror("Erro", "Selecione arquivos e um destino válido."); return
        try: numero_inicial = int(entrada_numero.get())
        except (ValueError, TypeError): messagebox.showerror("Erro", "Número inicial inválido."); return
        btn_executar['state'] = 'disabled'
        task_runner.run_task(processo_renomeacao, on_done, arquivos, destino, numero_inicial, formato_var.get(), progress_bar=barra_progresso)
    def on_done(success, result):
        btn_executar['state'] = 'normal'
        if success: 
            messagebox.showinfo("Concluído", f"{result} arquivos copiados e renomeados!", parent=tab_frame)
            if limpar_auto_var.get(): limpar()
        barra_progresso["value"] = 0
    def processo_renomeacao(q, arquivos, destino, num_inicial, formato):
        total = len(arquivos); q.put({'type': 'progress', 'max': total, 'value': 0})
        for i, path in enumerate(arquivos):
            ext = os.path.splitext(path)[1]
            if formato == "01": nome = f"{num_inicial + i:02d}{ext}"
            elif formato == "001": nome = f"{num_inicial + i:03d}{ext}"
            else: nome = f"{num_inicial + i}{ext}"
            shutil.copy2(path, os.path.join(destino, nome)); q.put({'type': 'progress', 'value': i + 1})
        return total
    f_origem = ttk.Labelframe(tab_frame, text="1. Selecionar Arquivos", padding=PAD_X); f_origem.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Button(f_origem, text="Procurar...", command=selecionar_arquivos).pack(side='left')
    label_status_origem = ttk.Label(f_origem, text="Nenhum arquivo selecionado."); label_status_origem.pack(side='left', padx=PAD_X)
    f_destino = ttk.Labelframe(tab_frame, text="2. Pasta de Destino", padding=PAD_X); f_destino.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Entry(f_destino, textvariable=entrada_destino_str, font=FONT_LABEL).pack(side='left', fill='x', expand=True, padx=(0, PAD_X))
    ttk.Button(f_destino, text="Procurar...", command=selecionar_destino).pack(side='left')
    f_config = ttk.Labelframe(tab_frame, text="3. Configurações", padding=PAD_X); f_config.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Label(f_config, text="Número inicial:").pack(side='left')
    entrada_numero = ttk.Entry(f_config, width=10, validate='key', validatecommand=vcmd); entrada_numero.insert(0, "1"); entrada_numero.pack(side='left', padx=PAD_X)
    formato_var = tk.StringVar(value="Nenhum"); ttk.Radiobutton(f_config, text="Normal (1)", variable=formato_var, value="Nenhum").pack(side='left', padx=PAD_X); ttk.Radiobutton(f_config, text="Dezena (01)", variable=formato_var, value="01").pack(side='left', padx=PAD_X); ttk.Radiobutton(f_config, text="Centena (001)", variable=formato_var, value="001").pack(side='left', padx=PAD_X)
    
    f_exec = ttk.Frame(tab_frame); f_exec.pack(fill='x', padx=PAD_X, pady=(PAD_Y*2, PAD_Y))
    btn_executar = ttk.Button(f_exec, text="Copiar e Renomear", command=iniciar_renomeacao, style="Accent.TButton"); btn_executar.pack(side='left', ipadx=10, ipady=5)
    ttk.Checkbutton(f_exec, text="Limpar seleção após concluir", variable=limpar_auto_var).pack(side='left', padx=PAD_X)

    barra_progresso = ttk.Progressbar(tab_frame, orient="horizontal", mode="determinate"); barra_progresso.pack(pady=PAD_Y, fill='x', padx=PAD_X)

def criar_aba_compressor_imagem(tab_frame, vcmd):
    entrada = tk.StringVar(); escala_var = tk.IntVar(value=50); img_original = None
    
    def atualizar_preview(event=None):
        if not img_original: return
        
        preview_size = 250; escala = escala_var.get() / 100.0
        w, h = img_original.width, img_original.height
        novo_w, novo_h = int(w * escala), int(h * escala)
        img_preview = img_original.resize((novo_w, novo_h), Image.Resampling.LANCZOS)
        img_preview.thumbnail((preview_size, preview_size), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img_preview)
        label_preview.config(image=photo, text=""); label_preview.image = photo
        try:
            from io import BytesIO; buffer = BytesIO()
            img_para_salvar = img_original.resize((novo_w, novo_h), Image.Resampling.LANCZOS)
            if img_para_salvar.mode == 'RGBA': img_para_salvar = img_para_salvar.convert('RGB')
            img_para_salvar.save(buffer, format="JPEG", quality=85)
            tamanho_bytes = buffer.tell()
            if tamanho_bytes < 1024: tamanho_str = f"{tamanho_bytes} B"
            elif tamanho_bytes < 1024**2: tamanho_str = f"{tamanho_bytes/1024:.1f} KB"
            else: tamanho_str = f"{tamanho_bytes/1024**2:.2f} MB"
            label_tamanho.config(text=f"Tamanho estimado: {tamanho_str}\nDimensões: {novo_w}x{novo_h} px")
        except Exception: label_tamanho.config(text=f"Dimensões: {novo_w}x{novo_h} px")

    def selecionar_imagem():
        nonlocal img_original
        caminho = ask_open_file_with_memory("compressor_open", filetypes=[("Imagens", "*.jpg *.jpeg *.png")])
        if caminho:
            try:
                entrada.set(caminho); img_original = Image.open(caminho)
                atualizar_preview(); btn_reduzir['state'] = 'normal'; btn_reduzir.focus_set()
            except Exception as e:
                messagebox.showerror("Erro ao Abrir", f"Não foi possível abrir a imagem:\n{e}", parent=tab_frame); img_original = None
    
    def reduzir_imagem():
        if not img_original: messagebox.showwarning("Aviso", "Selecione uma imagem.", parent=tab_frame); return
        try:
            escala = escala_var.get() / 100.0
            novo_tamanho = (int(img_original.width * escala), int(img_original.height * escala))
            img_red = img_original.resize(novo_tamanho, Image.Resampling.LANCZOS)
            salvar = ask_save_as_with_memory("compressor_save", defaultextension=".jpg", filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])
            if salvar:
                if salvar.lower().endswith(('.jpg', '.jpeg')) and img_red.mode == 'RGBA': img_red = img_red.convert('RGB')
                params = {'quality': 85, 'optimize': True} if salvar.lower().endswith(('.jpg', '.jpeg')) else {}
                img_red.save(salvar, **params)
                messagebox.showinfo("Sucesso", f"Imagem salva em:\n{salvar}", parent=tab_frame)
        except Exception as e: messagebox.showerror("Erro", str(e), parent=tab_frame)

    f_sel = ttk.Labelframe(tab_frame, text="1. Selecionar Imagem", padding=PAD_X); f_sel.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Entry(f_sel, textvariable=entrada, font=FONT_LABEL, state='readonly').pack(side='left', fill='x', expand=True, padx=(0, PAD_X))
    ttk.Button(f_sel, text="Procurar...", command=selecionar_imagem).pack(side='left')
    main_content_frame = ttk.Frame(tab_frame); main_content_frame.pack(fill='both', expand=True, padx=PAD_X, pady=PAD_Y)
    main_content_frame.columnconfigure(0, weight=1, minsize=300); main_content_frame.columnconfigure(1, weight=1)
    f_preview = ttk.Labelframe(main_content_frame, text="Pré-visualização", padding=PAD_X); f_preview.grid(row=0, column=0, sticky='nsew', padx=(0, PAD_X))
    f_preview.rowconfigure(0, weight=1); f_preview.columnconfigure(0, weight=1)
    label_preview = ttk.Label(f_preview, text="\nAguardando imagem...\n", relief='solid', anchor='center'); label_preview.grid(row=0, column=0, sticky='nsew')
    label_tamanho = ttk.Label(f_preview, text="", anchor='center'); label_tamanho.grid(row=1, column=0, pady=PAD_Y)
    f_red = ttk.Labelframe(main_content_frame, text="2. Ajustar Qualidade/Tamanho", padding=PAD_X); f_red.grid(row=0, column=1, sticky='nsew')
    label_escala_valor = ttk.Label(f_red, text="50%", font=FONT_LABEL); label_escala_valor.pack(pady=PAD_Y)
    def update_label_escala(val): label_escala_valor.config(text=f"{int(float(val))}%")
    escala = ttk.Scale(f_red, from_=10, to=90, orient="horizontal", variable=escala_var, command=lambda v: (update_label_escala(v), atualizar_preview()))
    escala.pack(fill='x', expand=True, pady=PAD_Y, ipady=5)
    btn_reduzir = ttk.Button(f_red, text="Reduzir e Salvar...", command=reduzir_imagem, style="Accent.TButton", state='disabled'); btn_reduzir.pack(pady=(PAD_Y * 4, PAD_Y), ipadx=10, ipady=5)

def criar_aba_separador_lista(tab_frame, vcmd):
    def separar():
        try:
            itens = [item.strip() for item in entrada_itens.get("1.0", tk.END).strip().splitlines() if item.strip()]
            tamanho = int(entrada_tamanho.get())
            if not itens or tamanho <= 0: raise ValueError("Entrada inválida")
            grupos = [itens[i:i+tamanho] for i in range(0, len(itens), tamanho)]
            resultado.config(state=tk.NORMAL); resultado.delete("1.0", tk.END)
            for i, grupo in enumerate(grupos, 1):
                resultado.insert(tk.END, f"--- Grupo {i} ({len(grupo)} itens) ---\n" + "\n".join(grupo) + "\n\n")
            resultado.config(state=tk.DISABLED)
        except (ValueError, TypeError): messagebox.showerror("Erro", "Verifique a lista e o tamanho do grupo (deve ser um número > 0).", parent=tab_frame)
    f_entrada = ttk.Labelframe(tab_frame, text="1. Cole os itens", padding=PAD_X); f_entrada.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    entrada_itens = scrolledtext.ScrolledText(f_entrada, height=10, relief=tk.FLAT); entrada_itens.pack(fill='x', expand=True)
    f_ctrl = ttk.Frame(tab_frame); f_ctrl.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    ttk.Label(f_ctrl, text="Tamanho por grupo:").pack(side='left')
    entrada_tamanho = ttk.Entry(f_ctrl, width=10, validate='key', validatecommand=vcmd); entrada_tamanho.insert(0, "300"); entrada_tamanho.pack(side='left', padx=(PAD_X, PAD_X*2))
    ttk.Button(f_ctrl, text="Separar", command=separar, style="Accent.TButton").pack(side='left')
    ttk.Button(f_ctrl, text="Salvar...", command=lambda: Path(ask_save_as_with_memory("separador_save", defaultextension=".txt")).write_text(resultado.get("1.0", tk.END).strip(), encoding='utf-8')).pack(side='left', padx=PAD_X)
    f_res = ttk.Labelframe(tab_frame, text="2. Resultado", padding=PAD_X); f_res.pack(fill='both', expand=True, padx=PAD_X, pady=PAD_Y)
    resultado = scrolledtext.ScrolledText(f_res, state=tk.DISABLED, relief=tk.FLAT); resultado.pack(fill='both', expand=True)

def criar_aba_manipulador_pdf(tab_frame, vcmd):
    if 'fitz' not in sys.modules:
        ttk.Label(tab_frame, text="Instale 'PyMuPDF'.\npy -m pip install PyMuPDF", font=FONT_LABEL, foreground="red").pack(pady=50); return

    task_runner = TaskRunner(tab_frame)
    frame_unir = ttk.Labelframe(tab_frame, text="Unir PDFs", padding=PAD_X); frame_unir.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    lista_arquivos_unir = []
    listbox_unir = tk.Listbox(frame_unir, height=6); listbox_unir.pack(fill='x', expand=True, pady=5)
    def adicionar_pdfs_unir():
        files = ask_open_files_with_memory("pdf_unir_open", title="Selecione os PDFs para unir", filetypes=[("PDF", "*.pdf")])
        if files:
            for f in files:
                if f not in lista_arquivos_unir: lista_arquivos_unir.append(f); listbox_unir.insert(tk.END, os.path.basename(f))
            btn_unir['state'] = 'normal'; btn_unir.focus_set()
    def remover_pdf_unir():
        selecionado = listbox_unir.curselection()
        if not selecionado: return
        idx = selecionado[0]; listbox_unir.delete(idx); lista_arquivos_unir.pop(idx)
        if not lista_arquivos_unir: btn_unir['state'] = 'disabled'
    def mover_item(direcao):
        selecionado = listbox_unir.curselection()
        if not selecionado: return
        idx = selecionado[0]
        if (direcao == "up" and idx == 0) or (direcao == "down" and idx == listbox_unir.size() - 1): return
        novo_idx = idx - 1 if direcao == "up" else idx + 1
        lista_arquivos_unir[idx], lista_arquivos_unir[novo_idx] = lista_arquivos_unir[novo_idx], lista_arquivos_unir[idx]
        texto_item = listbox_unir.get(idx); texto_novo = listbox_unir.get(novo_idx)
        listbox_unir.delete(idx); listbox_unir.insert(idx, texto_novo)
        listbox_unir.delete(novo_idx); listbox_unir.insert(novo_idx, texto_item)
        listbox_unir.selection_clear(0, tk.END); listbox_unir.selection_set(novo_idx); listbox_unir.activate(novo_idx)
    botoes_unir_frame = ttk.Frame(frame_unir); botoes_unir_frame.pack(fill='x')
    ttk.Button(botoes_unir_frame, text="Adicionar", command=adicionar_pdfs_unir).pack(side='left', padx=2)
    ttk.Button(botoes_unir_frame, text="Remover", command=remover_pdf_unir).pack(side='left', padx=2)
    ttk.Button(botoes_unir_frame, text="Limpar", command=lambda: (lista_arquivos_unir.clear(), listbox_unir.delete(0, tk.END), setattr(btn_unir, 'state', 'disabled'))).pack(side='left', padx=2)
    ttk.Button(botoes_unir_frame, text="Subir", command=lambda: mover("up")).pack(side='left', padx=(20, 2))
    ttk.Button(botoes_unir_frame, text="Descer", command=lambda: mover("down")).pack(side='left', padx=2)
    btn_unir = ttk.Button(frame_unir, text="Unir e Salvar Como...", style="Accent.TButton", state='disabled', command=lambda: iniciar_processo("unir")); btn_unir.pack(pady=10)
    frame_dividir = ttk.Labelframe(tab_frame, text="Dividir PDF", padding=PAD_X); frame_dividir.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    def selecionar_pdf_dividir():
        caminho = ask_open_file_with_memory("pdf_dividir_open", title="Selecione o PDF para dividir", filetypes=[("PDF", "*.pdf")])
        if caminho: arquivo_dividir_var.set(caminho); btn_dividir['state'] = 'normal'; btn_dividir.focus_set()
    arquivo_dividir_var = tk.StringVar()
    ttk.Entry(frame_dividir, textvariable=arquivo_dividir_var, state='readonly').pack(side='left', fill='x', expand=True, padx=(0, 5))
    ttk.Button(frame_dividir, text="Procurar...", command=selecionar_pdf_dividir).pack(side='left')
    btn_dividir = ttk.Button(frame_dividir, text="Dividir e Salvar em...", style="Accent.TButton", state='disabled', command=lambda: iniciar_processo("dividir")); btn_dividir.pack(pady=10)
    progress_frame, progresso, label_progresso = criar_widgets_progresso(tab_frame); progress_frame.pack(fill='x', padx=PAD_X, pady=PAD_Y)
    def processo_pdf(q, modo, *args):
        if modo == "unir":
            arquivos, caminho_saida = args[0], args[1]
            q.put({'type': 'progress', 'text': 'Iniciando união...', 'max': len(arquivos)}); doc_final = fitz.open()
            for i, caminho_pdf in enumerate(arquivos):
                q.put({'type': 'progress', 'value': i, 'text': f'Adicionando {os.path.basename(caminho_pdf)}...'})
                with fitz.open(caminho_pdf) as doc: doc_final.insert_pdf(doc)
            q.put({'type': 'progress', 'text': 'Salvando arquivo final...'}); doc_final.save(caminho_saida)
            return f"{len(arquivos)} PDFs unidos com sucesso!"
        elif modo == "dividir":
            arquivo, pasta_saida = args[0], args[1]; nome_base = Path(arquivo).stem
            with fitz.open(arquivo) as doc:
                q.put({'type': 'progress', 'text': 'Iniciando divisão...', 'max': len(doc)})
                for i, page in enumerate(doc):
                    q.put({'type': 'progress', 'value': i, 'text': f'Extraindo página {i+1}...'})
                    doc_pagina = fitz.open(); doc_pagina.insert_pdf(doc, from_page=i, to_page=i)
                    caminho_saida = os.path.join(pasta_saida, f"{nome_base}_pagina_{i+1}.pdf"); doc_pagina.save(caminho_saida)
            return f"{len(doc)} páginas extraídas com sucesso!"
    def on_done(success, result):
        progresso['value'] = 0; label_progresso.config(text="")
        if success: messagebox.showinfo("Sucesso", result, parent=tab_frame)
    def iniciar_processo(modo):
        if modo == "unir":
            if not lista_arquivos_unir: return
            caminho_saida = ask_save_as_with_memory("pdf_unir_save", title="Salvar PDF unido como...", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if not caminho_saida: return
            task_runner.run_task(processo_pdf, on_done, "unir", lista_arquivos_unir, caminho_saida, progress_bar=progresso, status_label=label_progresso)
        elif modo == "dividir":
            arquivo = arquivo_dividir_var.get()
            if not arquivo: return
            pasta_saida = ask_directory_with_memory("pdf_dividir_save", title="Selecione a pasta para salvar as páginas")
            if not pasta_saida: return
            task_runner.run_task(processo_pdf, on_done, "dividir", arquivo, pasta_saida, progress_bar=progresso, status_label=label_progresso)

# ############################################################################
# --- APLICAÇÃO PRINCIPAL ---
# ############################################################################

def main():
    global current_theme, save_config, LAST_PATHS
    root = tk.Tk()
    root.title("Caixa de Ferramentas")
    root.geometry("850x650")
    root.minsize(750, 600)
    
    def load_config():
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {"theme": "light", "last_paths": {}}

    def save_config(config):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
            
    config = load_config()
    current_theme = tk.StringVar(value=config.get("theme", "light"))
    LAST_PATHS = config.get("last_paths", {})

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    def apply_theme(theme_name):
        colors = THEMES[theme_name]
        root.config(bg=colors["bg"])
        style.configure(".", background=colors["bg"], foreground=colors["fg"], fieldbackground=colors["entry_bg"])
        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        style.configure("TFrame", background=colors["bg"])
        style.configure("TLabelframe", background=colors["bg"], bordercolor=colors["fg"])
        style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["fg"])
        style.configure("TButton", background=colors["bg"], foreground=colors["fg"])
        style.configure("TRadiobutton", background=colors["bg"], foreground=colors["fg"])
        style.configure("TCheckbutton", background=colors["bg"], foreground=colors["fg"])
        style.configure("Accent.TButton", font=FONT_BUTTON, foreground="white", background=colors["accent"])
        style.map("Accent.TButton", background=[('active', '#005a9e'), ('disabled', '#a0a0a0')])
        
        style.configure("TNotebook", background=colors["notebook_bg"], borderwidth=1)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=[15, 5], width=20, background=colors["tab_bg"], foreground=colors["tab_fg"])
        style.map("TNotebook.Tab", background=[("selected", colors["tab_active_bg"])], foreground=[("selected", colors["fg"])])

        for widget in root.winfo_children():
            update_widget_theme(widget, colors)

    def update_widget_theme(widget, colors):
        if isinstance(widget, tk.Listbox):
            widget.config(background=colors["entry_bg"], foreground=colors["fg"], selectbackground=colors["accent"], selectforeground="white")
        elif isinstance(widget, (tk.Text, tk.scrolledtext.ScrolledText)):
            widget.config(background=colors["entry_bg"], foreground=colors["fg"], insertbackground=colors["fg"], selectbackground=colors["accent"])
        for child in widget.winfo_children():
            update_widget_theme(child, colors)

    def toggle_theme():
        new_theme = "dark" if current_theme.get() == "light" else "light"
        current_theme.set(new_theme)
        apply_theme(new_theme)
        config["theme"] = new_theme
        save_config(config)

    menu_bar = tk.Menu(root); root.config(menu=menu_bar)
    options_menu = tk.Menu(menu_bar, tearoff=0); menu_bar.add_cascade(label="Opções", menu=options_menu)
    options_menu.add_command(label="Mudar Tema", command=toggle_theme)
    
    notebook = ttk.Notebook(root, style="TNotebook"); notebook.pack(pady=10, padx=10, fill="both", expand=True)
    style.configure("TNotebook", tabposition='wn')
    
    vcmd = (root.register(_validate_numeric_input), '%P')
    
    tabs = {
        "Unir Planilhas": criar_aba_unir_planilhas,
        "Gerador QR Code": criar_aba_qrcode,
        "Manipulador de PDF": criar_aba_manipulador_pdf,
        "Divisor de Planilhas": criar_aba_divisor_planilhas,
        "Organizador": criar_aba_organizador,
        "Conversor PDF/Img": criar_aba_conversor,
        "Renomeador": criar_aba_renomeador_arquivos,
        "Duplicatas": criar_aba_detector_duplicatas,
        "Calculadora de Hash": criar_aba_hash,
        "Compressor Img": criar_aba_compressor_imagem,
        "Separador Listas": criar_aba_separador_lista,
    }

    for text, create_func in tabs.items():
        tab_frame = ttk.Frame(notebook, padding=PAD_X)
        notebook.add(tab_frame, text=text, sticky='nsew')
        create_func(tab_frame, vcmd)

    apply_theme(current_theme.get())
    root.mainloop()

if __name__ == "__main__":
    main()