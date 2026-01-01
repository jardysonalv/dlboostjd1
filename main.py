# main.py
import uuid
import os
import threading
import shutil
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform
from kivymd.app import MDApp
from supabase import create_client

KV = '''
MDScreen:
    md_bg_color: [0.95, 0.96, 0.98, 1]
    MDBoxLayout:
        orientation: 'vertical'
        padding: "16dp"
        spacing: "12dp"

        MDLabel:
            text: "DLBOOST LITE (SEM ROOT)"
            halign: "center"
            font_style: "H5"
            bold: True
            theme_text_color: "Primary"

        MDCard:
            orientation: "vertical"
            padding: "12dp"
            size_hint: (1, None)
            height: "360dp"
            radius: [18, ]
            md_bg_color: [1, 1, 1, 1]
            elevation: 2

            MDLabel:
                id: id_display
                text: "ID: BUSCANDO HARDWARE..."
                halign: "center"
                theme_text_color: "Secondary"

            MDTextField:
                id: key_field
                hint_text: "CHAVE VIP (Supabase)"
                mode: "rectangle"
                icon_right: "shield-check"

            MDSeparator:

            MDBoxLayout:
                padding: 0,8
                spacing: 8
                MDRectangleFlatButton:
                    text: "ATIVAR"
                    on_release: app.autenticar_usuario()
                MDRectangleFlatButton:
                    text: "ABRIR CONFIG"
                    on_release: app.abrir_configuracoes()

            MDSeparator:

            MDLabel:
                text: "Otimizações disponíveis (sem root):"
                font_style: "Subtitle1"
                halign: "left"
                size_hint_y: None
                height: self.texture_size[1] + dp(8)

            MDGridLayout:
                cols: 2
                adaptive_height: True
                spacing: 8

                MDRaisedButton:
                    text: "Fechar apps em 2º plano"
                    on_release: app.acao_kill_bg()
                MDRaisedButton:
                    text: "Reduzir brilho"
                    on_release: app.acao_reduzir_brilho()

                MDRaisedButton:
                    text: "Modo Resfriamento"
                    on_release: app.acao_modo_resfriamento()
                MDRaisedButton:
                    text: "Limpar cache do app"
                    on_release: app.acao_limpar_cache()

            MDSeparator:

            MDLabel:
                id: sys_stats
                text: "Status: carregando..."
                halign: "left"
                theme_text_color: "Secondary"
                size_hint_y: None
                height: self.texture_size[1] + dp(8)

        MDLabel:
            id: log_output
            text: "Aguardando ativação..."
            halign: "center"
            font_style: "Caption"
            theme_text_color: "Secondary"
            size_hint_y: None
            height: self.texture_size[1] + dp(12)
'''

# --- CREDENCIAIS DO SEU SUPABASE (mesmas do código anterior) ---
URL = "https://wvvlsrulnwqhpzdbpoyl.supabase.co"
KEY = "sb_publishable_BJh5TycBWkSDG-RkLpvXMg_uEdH6wTg"
supabase = create_client(URL, KEY)

# Try to import Android-specific APIs if on Android
ANDROID = platform == "android"
if ANDROID:
    from jnius import autoclass, cast
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    Context = autoclass('android.content.Context')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    Settings = autoclass('android.provider.Settings')
    IntentFilter = autoclass('android.content.IntentFilter')
    ActivityManagerClass = autoclass('android.app.ActivityManager')
    MemInfoClass = autoclass('android.app.ActivityManager$MemoryInfo')
else:
    activity = None

class DlBoostApp(MDApp):
    def build(self):
        return Builder.load_string(KV)

    def on_start(self):
        try:
            self.user_id = str(uuid.getnode())[-8:].upper()
        except Exception:
            self.user_id = uuid.uuid4().hex[:8].upper()
        self.root.ids.id_display.text = f"ID: {self.user_id}"
        self.root.ids.log_output.text = "Insira a CHAVE VIP e pressione ATIVAR"
        # Start periodic status update
        Clock.schedule_interval(self.atualizar_stats, 3)

    def atualizar_stats(self, dt):
        # Exibe informações básicas: memória disponível e temperatura (se possível)
        try:
            if ANDROID:
                am = cast('android.app.ActivityManager', activity.getSystemService(Context.ACTIVITY_SERVICE))
                memInfo = MemInfoClass()
                am.getMemoryInfo(memInfo)
                avail = memInfo.availMem // (1024 * 1024)
                total = getattr(memInfo, 'totalMem', 0) // (1024 * 1024)
                # battery temp
                if activity:
                    ifilter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
                    bat = activity.registerReceiver(None, ifilter)
                    temp = bat.getIntExtra("temperature", 0) / 10.0
                else:
                    temp = 0.0
                self.root.ids.sys_stats.text = f"Memória livre: {avail} MB / {total} MB    Temp: {temp:.1f}°C"
            else:
                self.root.ids.sys_stats.text = "Executando fora do Android — algumas funções não são disponíveis."
        except Exception as e:
            self.root.ids.sys_stats.text = "Falha ao ler stats."

    def autenticar_usuario(self):
        key = self.root.ids.key_field.text.strip()
        if not key:
            self.root.ids.log_output.text = "⚠️ DIGITE A CHAVE VIP"
            return

        self.root.ids.log_output.text = "Verificando no servidor..."
        threading.Thread(target=self._verificar_key, args=(key,), daemon=True).start()

    def _verificar_key(self, key):
        try:
            res = supabase.table("ativacoes").select("*")\
                .eq("id_aparelho", self.user_id)\
                .eq("chave_vip", key)\
                .eq("vip", True).execute()
            if getattr(res, "data", None):
                Clock.schedule_once(lambda dt: self._on_ativado(), 0)
            else:
                Clock.schedule_once(lambda dt: self._set_log("❌ CHAVE INVÁLIDA PARA ESTE ID"), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._set_log("Erro de conexão com o servidor!"), 0)

    def _on_ativado(self):
        self.root.ids.log_output.text = "✅ ATIVADO: otimizações liberadas"
        # Aqui você pode habilitar/mostrar mais opções UI se desejar

    def _set_log(self, msg):
        self.root.ids.log_output.text = msg

    # ---------- Ações de otimização (sem root) ----------
    def abrir_configuracoes(self):
        if ANDROID:
            try:
                intent = Intent(Settings.ACTION_SETTINGS)
                activity.startActivity(intent)
                self._set_log("Abrindo configurações do sistema...")
            except Exception:
                self._set_log("Não foi possível abrir configurações.")
        else:
            self._set_log("Somente disponível no Android.")

    def acao_kill_bg(self):
        self._set_log("Encerrando apps em segundo plano (tentativa)...")
        threading.Thread(target=self._kill_background_processes, daemon=True).start()

    def _kill_background_processes(self):
        if not ANDROID:
            self._set_log("Funcionalidade disponível apenas no Android.")
            return
        try:
            ctx = activity
            am = cast('android.app.ActivityManager', ctx.getSystemService(Context.ACTIVITY_SERVICE))
            running = am.getRunningAppProcesses()
            own_pkg = ctx.getPackageName()
            count = 0
            if running:
                for proc in running.toArray():
                    try:
                        pkgs = proc.pkgList
                    except Exception:
                        # fallback: proc.processName
                        pkgs = [proc.processName]
                    for p in pkgs:
                        if p and p != own_pkg:
                            try:
                                am.killBackgroundProcesses(p)
                                count += 1
                            except Exception:
                                pass
            self._set_log(f"Encerradas ~{count} tarefas em segundo plano (somente o que o sistema permitir).")
        except Exception as e:
            self._set_log("Erro ao encerrar processos: " + str(e))

    def acao_reduzir_brilho(self):
        self._set_log("Tentando reduzir brilho (solicita permissão se necessário)...")
        threading.Thread(target=self._reduzir_brilho_thread, daemon=True).start()

    def _reduzir_brilho_thread(self):
        if not ANDROID:
            self._set_log("Disponível apenas no Android.")
            return
        try:
            ctx = activity
            package_uri = Uri.parse("package:" + ctx.getPackageName())
            # Solicita permissão de WRITE_SETTINGS abrindo tela de permissão para o usuário
            intent = Intent(Settings.ACTION_MANAGE_WRITE_SETTINGS)
            intent.setData(package_uri)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            ctx.startActivity(intent)
            # Após usuário conceder, tentar setar brilho (nota: o usuário precisa confirmar)
            # Aqui definimos um brilho de 30%
            try:
                cr = ctx.getContentResolver()
                val = int(255 * 0.3)
                Settings.System.putInt(cr, Settings.System.SCREEN_BRIGHTNESS, val)
                self._set_log("Brilho alterado para ~30% (se permitido).")
            except Exception:
                self._set_log("Solicitação enviada. Conceda permissão WRITE_SETTINGS manualmente e reexecute.")
        except Exception as e:
            self._set_log("Erro ao solicitar permissão de brilho: " + str(e))

    def acao_limpar_cache(self):
        self._set_log("Limpando cache do próprio app...")
        threading.Thread(target=self._limpar_cache_thread, daemon=True).start()

    def _limpar_cache_thread(self):
        try:
            cache_dir = self.user_data_dir if hasattr(self, 'user_data_dir') else None
            # Kivy: App user_data_dir
            cache_dir = self.user_data_dir if hasattr(self, 'user_data_dir') else None
            if not cache_dir:
                cache_dir = os.path.join(os.getcwd(), 'cache')
            if os.path.exists(cache_dir):
                try:
                    shutil.rmtree(cache_dir)
                except Exception:
                    # fallback: remove files
                    for root, dirs, files in os.walk(cache_dir):
                        for f in files:
                            try:
                                os.remove(os.path.join(root, f))
                            except Exception:
                                pass
                self._set_log("Cache do app limpo.")
            else:
                self._set_log("Nenhum cache de app encontrado.")
        except Exception as e:
            self._set_log("Erro ao limpar cache: " + str(e))

    def acao_modo_resfriamento(self):
        self._set_log("Modo Resfriamento: reduz brilho + encerra apps em 2º plano...")
        threading.Thread(target=self._modo_resfriamento_thread, daemon=True).start()

    def _modo_resfriamento_thread(self):
        # Combina redução de brilho e encerramento background
        try:
            self._reduzir_brilho_thread()
            self._kill_background_processes()
            self._set_log("Modo Resfriamento executado (ações aplicadas conforme permissões).")
        except Exception as e:
            self._set_log("Erro no modo resfriamento: " + str(e))


if __name__ == "__main__":
    DlBoostApp().run()