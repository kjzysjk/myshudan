import os
import threading
import tkinter as tk
from datetime import datetime
import time
import cv2
import fitz
import numpy as np
import win32com.client
from PIL import Image, ImageTk
from tkinter import filedialog, ttk
import tkinter.font as tkFont
from docx2pdf import convert
from tkinter import filedialog, messagebox, ttk, colorchooser, scrolledtext
import requests
import UserConfig as UserConfig
import VideoHelper as VideoHelper

class ModernApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # 设置主题色
        self.colors = {
            'bg': '#F0F2F5',
            'sidebar': '#FFFFFF',
            'button': '#1890FF',
            'button_hover': '#40A9FF',
            'text': '#000000',
            'secondary_text': '#8C8C8C'
        }

        self.title("土豆书单视频制作软件 V1.10")
        self.geometry("1200x800")
        self.configure(bg=self.colors['bg'])
        self.minsize(1000, 700)
        self.configure(bg=self.colors['bg'])
        self.api_host, self.api_secret, self.local_mode = UserConfig.load_api_settings()
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.current_directory = current_directory
        iconphoto = os.path.join(current_directory, 'logo.png')
        self.iconphoto(True, tk.PhotoImage(file=iconphoto))
        self.TEMP_DIR = current_directory + "/TEMP"
        if not os.path.isdir(self.TEMP_DIR):
            os.mkdir(self.TEMP_DIR)

        self.result_file = ''
        self.err = False
        self.selected_button = None
        self.menu_buttons = {}  # 用于存储菜单按钮的引用
        # 创建自定义字体
        self.title_font = tkFont.Font(family="Microsoft YaHei UI", size=14, weight="bold")
        self.subtitle_font = tkFont.Font(family="Microsoft YaHei UI", size=12)
        self.button_font = tkFont.Font(family="Microsoft YaHei UI", size=10)

        # 保存音乐设置
        self.background_music = {
            'path': '',
            'volume': 0
        }


        UserConfig.init(self)
        UserConfig.load_settings(self)

        self.setup_ui()

    def setup_ui(self):
        # 创建主布局
        self.main_container = tk.Frame(self, bg=self.colors['bg'])
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 左侧边栏
        self.setup_sidebar()

        # 右侧内容区
        self.setup_content()

    def setup_sidebar(self):
        sidebar = tk.Frame(self.main_container, bg=self.colors['sidebar'], width=250)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar.pack_propagate(False)  # 固定宽度

        # Logo区域
        logo_frame = tk.Frame(sidebar, bg=self.colors['sidebar'])
        logo_frame.pack(fill=tk.X, pady=(30, 50))

        logo_label = tk.Label(logo_frame, text="📺", font=("Arial", 40), bg=self.colors['sidebar'])
        logo_label.pack()

        title_label = tk.Label(logo_frame, text="土豆书单视频软件", font=self.title_font,
                               bg=self.colors['sidebar'], fg=self.colors['text'])
        title_label.pack()

        # 菜单按钮
        self.create_menu_button(sidebar, "🏠 主页", self.show_content1)
        self.create_menu_button(sidebar, "⚙ 设置", self.show_content2)
        self.create_menu_button(sidebar, "❓ 帮助", self.help_info)

    def highlight_button(self, button):
        if self.selected_button:
            self.selected_button.config(bg=self.colors['sidebar'])  # 恢复之前选中按钮的颜色
        button.config(bg=self.colors['bg'])  # 高亮当前选中按钮
        self.selected_button = button

    def setup_content(self):
        # 创建一个框架来容纳所有可能的内容页面
        self.content_container = tk.Frame(self.main_container, bg=self.colors['bg'])
        self.content_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建不同的内容页面
        self.home_frame = self.create_home_page()
        self.settings_frame = self.create_settings_page()
        self.help_frame = self.create_help_page()

        # 默认显示主页
        self.show_frame(self.home_frame)

    def setup_file_selection(self, parent):
        file_frame = tk.Frame(parent, bg=self.colors['bg'])
        file_frame.pack(fill=tk.X, pady=(0, 20))

        # 文件输入框样式
        style = ttk.Style()
        style.configure('Modern.TEntry', padding=10)

        self.path_entry = ttk.Entry(file_frame, font=self.subtitle_font, style='Modern.TEntry')
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # 背景音乐按钮
        music_btn = tk.Button(file_frame, text="🎵 背景音乐", font=self.button_font,
                              bg=self.colors['button'], fg='white', padx=15, pady=10,
                              command=self.show_music_dialog, relief='flat')
        music_btn.pack(side=tk.RIGHT, padx=(5, 10))
        self.add_button_hover_effect(music_btn)

        select_btn = tk.Button(file_frame, text="选择文件", font=self.button_font,
                               bg=self.colors['button'], fg='white', padx=20, pady=10,
                               command=self.select_word_file, relief='flat')
        select_btn.pack(side=tk.RIGHT)
        self.add_button_hover_effect(select_btn)

        # select_btn = tk.Button(file_frame, text="选择文件", font=self.button_font,
        #                        bg=self.colors['button'], fg='white', padx=20, pady=10,
        #                        command=self.select_word_file, relief='flat')
        # select_btn.pack(side=tk.RIGHT)
        # self.add_button_hover_effect(select_btn)

    def show_music_dialog(self):
        # 创建一个新的顶层窗口
        self.music_dialog = tk.Toplevel(self)
        self.music_dialog.title("背景音乐设置")
        self.music_dialog.geometry("400x300")
        self.music_dialog.configure(bg=self.colors['bg'])

        # 设置模态
        self.music_dialog.transient(self)
        self.music_dialog.grab_set()

        # 创建音乐路径显示框
        music_frame = tk.Frame(self.music_dialog, bg=self.colors['bg'])
        music_frame.pack(fill=tk.X, padx=20, pady=20)

        self.music_path_entry = ttk.Entry(music_frame, font=self.subtitle_font)
        self.music_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # 选择音乐按钮
        select_music_btn = tk.Button(music_frame, text="选择音乐", font=self.button_font,
                                     bg=self.colors['button'], fg='white', padx=15, pady=5,
                                     command=self.select_background_music, relief='flat')
        select_music_btn.pack(side=tk.RIGHT)
        self.add_button_hover_effect(select_music_btn)

        # 音量控制滑块
        volume_frame = tk.Frame(self.music_dialog, bg=self.colors['bg'])
        volume_frame.pack(fill=tk.X, padx=20, pady=10)

        # 音量标签和数值显示框架
        volume_label_frame = tk.Frame(volume_frame, bg=self.colors['bg'])
        volume_label_frame.pack(fill=tk.X)

        tk.Label(volume_label_frame, text="音量控制:", font=self.subtitle_font,
                 bg=self.colors['bg']).pack(side=tk.LEFT)

        # 添加音量数值显示标签
        self.volume_label = tk.Label(volume_label_frame, text="50%", font=self.subtitle_font,
                                     bg=self.colors['bg'], fg=self.colors['text'])
        self.volume_label.pack(side=tk.RIGHT)

        # 音量滑块
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                      command=self.update_volume_label)
        self.volume_scale.set(50)  # 默认音量50%
        self.volume_scale.pack(fill=tk.X, pady=10)

        # 确认和取消按钮
        button_frame = tk.Frame(self.music_dialog, bg=self.colors['bg'])
        button_frame.pack(side=tk.BOTTOM, pady=20)

        confirm_btn = tk.Button(button_frame, text="确认", font=self.button_font,
                                bg=self.colors['button'], fg='white', padx=20, pady=5,
                                command=self.confirm_music_settings, relief='flat')
        confirm_btn.pack(side=tk.LEFT, padx=10)
        self.add_button_hover_effect(confirm_btn)

        cancel_btn = tk.Button(button_frame, text="取消", font=self.button_font,
                               bg=self.colors['button'], fg='white', padx=20, pady=5,
                               command=self.music_dialog.destroy, relief='flat')
        cancel_btn.pack(side=tk.LEFT, padx=10)
        self.add_button_hover_effect(cancel_btn)

    def update_volume_label(self, value):
        """更新音量显示标签"""
        # 将浮点数转换为整数显示
        volume = int(float(value))
        self.volume_label.config(text=f"{volume}%")

    def select_background_music(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("音频文件", "*.mp3;*.wav;")]
        )
        if file_path:
            self.music_path_entry.delete(0, tk.END)
            self.music_path_entry.insert(0, file_path)
            self.log("选取的BGM: " + file_path)

    def confirm_music_settings(self):
        music_path = self.music_path_entry.get()
        volume = self.volume_scale.get()
        # 保存音乐设置
        self.background_music = {
            'path': music_path,
            'volume': volume
        }
        self.music_dialog.destroy()

    def setup_action_buttons(self, parent):
        button_frame = tk.Frame(parent, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=20)

        # 生成按钮
        generate_btn = tk.Button(button_frame, text="开始生成", font=self.button_font,
                                 bg=self.colors['button'], fg='white', padx=30, pady=12,
                                 command=self.start_covert, relief='flat')
        generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.add_button_hover_effect(generate_btn)

        # 查看按钮
        view_btn = tk.Button(button_frame, text="查看视频", font=self.button_font,
                             bg=self.colors['button'], fg='white', padx=30, pady=12,
                             command=self.view_exported_video, relief='flat')
        view_btn.pack(side=tk.LEFT)
        self.add_button_hover_effect(view_btn)

    def setup_log_area(self, parent):
        log_frame = tk.Frame(parent, bg=self.colors['bg'])
        log_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="处理日志", font=self.subtitle_font,
                 bg=self.colors['bg']).pack(anchor='w', pady=(0, 10))

        self.log_text = tk.Text(log_frame, font=("Microsoft YaHei UI", 10),
                                bg='white', relief='flat', padx=10, pady=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def create_menu_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, font=self.subtitle_font,
                        bg=self.colors['sidebar'], fg=self.colors['text'],
                        bd=0, padx=50, pady=15, anchor='w',
                        command=command)
        btn.pack(fill=tk.X, pady=2)

        # 保存按钮引用
        self.menu_buttons[text] = btn

        def on_enter(e):
            if btn != self.selected_button:  # 如果不是当前选中的按钮
                btn['bg'] = self.colors['bg']

        def on_leave(e):
            if btn != self.selected_button:  # 如果不是当前选中的按钮
                btn['bg'] = self.colors['sidebar']

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def select_word_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Documents", "*.docx;*.pdf")])
        if file_path:
            self.path_entry.delete(0, tk.END)  # 清空文本框
            self.path_entry.insert(0, file_path)  # 显示选中的文件路径
            self.log("选取的文档: " + file_path)

    def add_button_hover_effect(self, button):
        def on_enter(e):
            button['bg'] = self.colors['button_hover']

        def on_leave(e):
            button['bg'] = self.colors['button']

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def log(self, message):
        current_time = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{current_time}] {message}\n")
        self.log_text.see(tk.END)  # 自动滚动到最新位置

    def start_covert(self):
        self.err = False
        thread = threading.Thread(target=self.start_generating_video)
        thread.start()

    def read_image_safe(image_path):
        # 处理中文路径
        img_data = cv2.imdecode(
            np.fromfile(image_path, dtype=np.uint8),
            cv2.IMREAD_COLOR
        )
        return img_data

    def post_api(self, url, data, image_paths):
        try:
            files = []
            for image_path in image_paths:
                with open(image_path, 'rb') as img_file:
                    files.append(('images', (image_path, img_file.read())))

            with requests.Session() as session:
                headers = {
                    'Connection': 'keep-alive',
                    'Keep-Alive': 'timeout=3600'
                }
                try:
                    # 提交任务
                    response = session.post(url, files=files, data=data, headers=headers, timeout=(600, 600))
                    self.log(f"api响应内容: {response.text}")
                    if response.status_code != 200:
                        self.task_wait = False
                        self.err = True
                        self.err_message = f"任务提交失败: {response.json().get('error')}"
                        return

                    # 获取task_id
                    task_id = response.json().get('task_id')
                    if not task_id:
                        self.task_wait = False
                        self.err = True
                        self.err_message = "未获取到task_id"
                        return

                    # 轮询检查任务状态
                    check_url = f"{self.api_host}/check_task/{task_id}"
                    max_retries = 60  # 最大重试次数
                    retry_interval = 5  # 重试间隔（秒）

                    for _ in range(max_retries):
                        check_response = session.get(check_url)
                        if check_response.status_code != 200:
                            time.sleep(retry_interval)
                            continue

                        task_status = check_response.json()
                        status = task_status.get('status')

                        if status == 'completed':
                            video_url = task_status.get('video_url')
                            if not video_url:
                                self.task_wait = False
                                self.err = True
                                self.err_message = "视频URL未找到"
                                return

                            # 下载视频
                            video_url = f"{self.api_host}{video_url}"
                            video_response = session.get(video_url, stream=True)
                            if video_response.status_code == 200:
                                video_path = self.result_file
                                self.remove_file(video_path)
                                with open(video_path, 'wb') as video_file:
                                    for chunk in video_response.iter_content(chunk_size=8192):
                                        video_file.write(chunk)
                                self.task_wait = False
                                self.err = False
                                self.err_message = video_path
                                return
                            else:
                                self.task_wait = False
                                self.err = True
                                self.err_message = f"视频下载失败: {video_response.status_code}"
                                return

                        elif status == 'failed':
                            self.task_wait = False
                            self.err = True
                            self.err_message = "视频生成失败"
                            return

                        time.sleep(retry_interval)

                    # 超时处理
                    self.task_wait = False
                    self.err = True
                    self.err_message = "任务处理超时"

                except requests.exceptions.RequestException as e:
                    self.task_wait = False
                    self.err = True
                    self.err_message = f"请求发生错误: {e}"

        except Exception as ex:
            self.task_wait = False
            self.err = True
            self.err_message = f"接口请求出错: {ex}"





    def convert_word_to_pdf(self, word_path, pdf_path):
        self.remove_file(pdf_path)
        try:
            self.log(f"尝试使用ms word")
            # 先尝试Microsoft Office
            word = win32com.client.Dispatch("Word.Application")
            doc = word.Documents.Open(word_path)
            doc.SaveAs(pdf_path, FileFormat=17)
            doc.Close()
            word.Quit()
        except:
            self.log(f"尝试使用wps word")
            try:
                # 如果失败，尝试WPS
                word = win32com.client.Dispatch("KWPS.Application")
                doc = word.Documents.Open(word_path)
                doc.SaveAs(pdf_path, FileFormat=17)
                doc.Close()
                word.Quit()
            except Exception as ex:
                self.log(f"{ex}")
                if not os.path.exists(pdf_path):
                    self.err = True
                    self.log(f"{ex}")
                    messagebox.showerror('错误',f"转换失败，请确保安装了 Microsoft Office 或 WPS: {ex}")

    def start_generating_video(self):
        file_path = self.path_entry.get()
        if not file_path:
            self.log(f"请先选取文档...")
            return
        self.log(f"模式设置:{self.local_mode}")
        if file_path.lower().endswith('.pdf'):
            pdf_path = file_path
            self.result_file = os.path.join(self.TEMP_DIR, os.path.basename(file_path).replace('.pdf', '.mp4'))
        else:
            # 把word转成Pdf
            self.log(f"预处理word文档...")
            pdf_path = file_path.replace('.docx', '.pdf')
            self.result_file = os.path.join(self.TEMP_DIR, os.path.basename(file_path).replace('.docx', '.mp4'))
            try:
                self.convert_word_to_pdf(file_path, pdf_path)
                #convert(file_path, pdf_path)
            except Exception as ex:
                self.log(f"{ex}")

        if self.err:
            messagebox.showerror('错误', '转换word文档时出错，请使用pdf文档或用其它工具把word转pdf')

        self.log(f"释放图片...")
        self.log(f"转为视频片段...")
        # 把图片转成视频
        pdf_document = fitz.open(pdf_path)
        image_prefix = os.path.join(self.TEMP_DIR, 'temp_image_')
        dpi = 120
        image_paths = []  # 存储图片路径
        total_pages = len(pdf_document)
        # 保存PDF页面为图片并收集图片信息
        for page_num in range(total_pages):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap(dpi=dpi)
            temp_image_path = f'{image_prefix}{page_num}.png'
            pix.save(temp_image_path)
            image_paths.append(temp_image_path)
        pdf_document.close()
        self.log(f"释放的图片{image_paths}...")

        if self.local_mode == '1':
            self.log("使用本地ffmpeg-contact合成最终视频...")
            total_time_minutes = total_pages  # 每个图片1分钟
            total_time_seconds = total_time_minutes * 60

            # 初始化进度条
            progress_bar_length = 100
            progress_bar = ['|'] * progress_bar_length
            progress_start = 0
            self.task_wait = True
            self.err = False
            self.err_message = ''

            with Image.open(image_paths[0]) as img:
                width, height = img.size

            if width % 2 != 0:
                width = width - 1

            if height % 2 != 0:
                height = height - 1

            ud_resolution = self.out_resolution.get()
            if ud_resolution != '自动':
                width, height = map(int, ud_resolution.split('x'))
            video_thread = threading.Thread(target=lambda: VideoHelper.ImageToVideo(self, image_paths, image_prefix, int(self.transition_duration.get()*1000), width, height))
            video_thread.start()
        else:
            self.log("调用接口合成最终视频视频...")
            # 计算总耗时
            total_time_minutes = total_pages  # 每个图片1分钟
            total_time_seconds = total_time_minutes * 60

            # 初始化进度条
            progress_bar_length = 100
            progress_bar = ['|'] * progress_bar_length
            progress_start = 0
            self.task_wait = True
            self.err = False
            self.err_message = ''

            with Image.open(image_paths[0]) as img:
                width, height = img.size

            if width % 2 != 0:
                width = width - 1

            if height % 2 != 0:
                height = height - 1

            ud_resolution = self.out_resolution.get()
            if ud_resolution != '自动':
                width, height = map(int, ud_resolution.split('x'))


            data = {
                'duration': self.video_duration.get(),  # 设置时长
                'transition_duration': int(self.transition_duration.get()*1000),
                'width': width,
                'height': height
            }

            self.log(f"参数：{data}")
            self.log("0%")


            post_url = f'{self.api_host}/upload'
            video_thread = threading.Thread(target=lambda: self.post_api(post_url, data, image_paths))
            video_thread.start()

        # 模拟进度
        while self.task_wait:
            progress_start += 1
            task_info = progress_start / total_time_seconds
            # 修正进度条计算，确保和百分比同步
            completed_lines = int(task_info * progress_bar_length)
            progress_display = ''.join(progress_bar[:completed_lines])
            time.sleep(1)

            # 删除最后一行
            last_line_start = self.log_text.index("end-2c linestart")
            self.log_text.delete(last_line_start, "end-1c")
            # 添加新的进度信息
            self.log(f"进度: {progress_display.ljust(progress_bar_length)} {task_info:.2%}")

        # 重置为满格
        progress_start = total_time_seconds
        task_info = progress_start / total_time_seconds
        # 修正进度条计算，确保和百分比同步
        completed_lines = int(task_info * progress_bar_length)
        progress_display = ''.join(progress_bar[:completed_lines])
        time.sleep(1)

        # 删除最后一行
        last_line_start = self.log_text.index("end-2c linestart")
        self.log_text.delete(last_line_start, "end-1c")
        # 添加新的进度信息
        self.log(f"进度: {progress_display.ljust(progress_bar_length)} {task_info:.2%}")
        self.log(f"{self.err_message}")

        # 删除临时文件
        for image in image_paths:
            self.remove_file(image)

        if not self.err:
            if self.background_music['path'] and self.background_music['volume'] > 0:
                try:
                    self.log("正在添加背景音乐...")
                    bgm_video_file = self.result_file.replace('.mp4', '_bgm.mp4')
                    volume_factor = self.background_music['volume']
                    VideoHelper.merge_backgroud_audio(self, self.result_file, self.background_music['path'],bgm_video_file, volume_factor)
                    self.log("完成背景音乐添加...")
                    self.log("视频生成完成...")
                    messagebox.showinfo('提示', '视频生成完成')
                except Exception as e:
                    self.log(f"添加背景音乐时发生错误: {str(e)}")
            else:
                messagebox.showinfo('提示', '视频生成完成')

    def remove_file(self, file_path):
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as ex:
                self.log(f"清理文件失败...{ex}")

    def view_exported_video(self):
        if os.path.exists(self.TEMP_DIR):
            os.startfile(self.TEMP_DIR)

    def create_home_page(self):
        """创建主页内容"""
        frame = tk.Frame(self.content_container, bg=self.colors['bg'])

        # 欢迎标题
        welcome_frame = tk.Frame(frame, bg=self.colors['bg'])
        welcome_frame.pack(fill=tk.X, pady=(0, 30))

        tk.Label(welcome_frame, text="欢迎使用Word/Pdf文档转书单视频工具",
                 font=self.title_font, bg=self.colors['bg']).pack(anchor='w')
        tk.Label(welcome_frame, text="请选择Word/Pdf文档开始转换，背景音乐不是必须的，如果用不到可以不去设置。",
                 font=self.subtitle_font, fg=self.colors['secondary_text'],
                 bg=self.colors['bg']).pack(anchor='w')

        # 文件选择区域
        self.setup_file_selection(frame)

        # 操作按钮区域
        self.setup_action_buttons(frame)

        # 日志区域
        self.setup_log_area(frame)

        return frame

    def create_settings_page(self):
        """创建设置页面"""
        frame = tk.Frame(self.content_container, bg=self.colors['bg'])

        # 设置页面标题
        tk.Label(frame, text="系统设置",
                 font=self.title_font, bg=self.colors['bg']).pack(pady=(0, 20))

        # 添加设置选项
        settings_frame = tk.Frame(frame, bg=self.colors['bg'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        # 视频画面持续时间设置
        self.create_duration_setting(settings_frame)

        # 翻页动作时间设置
        self.create_transition_setting(settings_frame)

        # 输出视频分辨率设置
        self.create_resolution_setting(settings_frame)

        return frame

    def create_help_page(self):
        """创建帮助页面"""
        import webbrowser  # 添加此导入语句到文件顶部

        frame = tk.Frame(self.content_container, bg=self.colors['bg'])

        # 帮助页面标题
        tk.Label(frame, text="使用帮助",
                 font=self.title_font, bg=self.colors['bg']).pack(pady=(0, 20))

        # 帮助内容
        help_text = tk.Text(frame, font=self.subtitle_font, bg='white',
                            relief='flat', padx=20, pady=20)
        help_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        help_content = """
            使用指南：

            1. 文档转换
               • 点击"选择文件"按钮选择要转换的Word文档
               • 确认文档后点击"开始生成"按钮
               • 等待转换完成

            2. 功能说明
               • 支持.docx格式文件
               • 自动识别文档结构
               • 智能生成视频内容

            3. 常见问题
               Q: 支持哪些文档格式？
               A: 目前支持.docx格式的Word文档和pdf文档

               Q: 转换需要多长时间？
               A: 根据文档长度不同，硬件配置不同而不同，开发者自用电脑测试2分钟可完成10页word的转书单视频

            4. 问题反馈（建议）
               • 软件代码已开源，欢迎向我提交issue
               • gitee："""

        help_text.insert('1.0', help_content)

        # 创建超链接样式
        help_text.tag_configure("hyperlink", foreground="blue", underline=1)

        # 添加第一个链接
        gitee_url = "https://gitee.com/"
        help_text.insert('end', gitee_url, "hyperlink")
        help_text.insert('end', "\n               • github：")

        # 添加第二个链接
        github_url = "https://github.com/"
        help_text.insert('end', github_url, "hyperlink")

        # 绑定点击事件
        def open_url(event, url):
            webbrowser.open_new(url)

        # 为链接添加点击事件
        help_text.tag_bind("hyperlink", "<Button-1>",
                           lambda e, url=gitee_url: open_url(e, url))
        help_text.tag_bind("hyperlink", "<Button-1>",
                           lambda e, url=github_url: open_url(e, url))

        # 改变鼠标样式
        def on_enter(event):
            help_text.config(cursor="hand2")

        def on_leave(event):
            help_text.config(cursor="")

        help_text.tag_bind("hyperlink", "<Enter>", on_enter)
        help_text.tag_bind("hyperlink", "<Leave>", on_leave)

        help_text.config(state='disabled')  # 设置为只读

        return frame

    def create_duration_setting(self, parent):
        """创建视频画面持续时间设置"""
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill=tk.X, pady=10)

        tk.Label(frame, text="视频画面持续时间(秒):",
                 font=self.subtitle_font, bg=self.colors['bg']).pack(side=tk.LEFT)

        def on_duration_change(*args):
            """当视频时长改变时的回调函数"""
            try:
                value = self.video_duration.get()
                # 可以添加值的验证
                if 1 <= value <= 60:  # 限制视频时长在1-60秒之间
                    UserConfig.save_settings_to_json(self)
                else:
                    # 如果值超出范围，重置为有效值
                    self.video_duration.set(min(max(1, value), 60))
            except tk.TclError:  # 处理无效输入
                self.video_duration.set(5)  # 重置为默认值



        def validate_duration(value):
            """验证输入是否为有效的整数"""
            if value == "":
                return True
            try:
                int_value = int(value)
                # 限制范围
                if int_value < 1 or int_value > 60:
                    return False
                return True
            except ValueError:
                return False

        vcmd = (frame.register(validate_duration), '%P')
        entry = tk.Entry(frame,
                         width=10,
                         validate='key',
                         validatecommand=vcmd,
                         textvariable=self.video_duration)
        entry.pack(side=tk.RIGHT)

        # 添加变量跟踪
        self.video_duration.trace_add('write', on_duration_change)

    def create_transition_setting(self, parent):
        """创建翻页动作时间设置"""
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill=tk.X, pady=10)

        tk.Label(frame, text="翻页动作持续时间(秒):",
                 font=self.subtitle_font, bg=self.colors['bg']).pack(side=tk.LEFT)

        def on_transition_change(*args):
            UserConfig.save_settings_to_json(self)


        vcmd = (frame.register(self.validate_float), '%P')
        entry = tk.Entry(frame,
                         width=10,
                         validate='key',
                         validatecommand=vcmd,
                         textvariable=self.transition_duration)
        entry.pack(side=tk.RIGHT)

        # 添加变量跟踪
        self.transition_duration.trace_add('write', on_transition_change)

    def create_resolution_setting(self, parent):
        """创建输出视频分辨率设置"""
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill=tk.X, pady=10)

        tk.Label(frame, text="输出视频分辨率:",
                 font=self.subtitle_font, bg=self.colors['bg']).pack(side=tk.LEFT)

        # 分辨率选项
        resolutions = [
            "自动",
            # 横屏
            "3840x2160",  # 4K
            "2560x1440",  # 2K
            "1920x1080",  # 1080p
            "1600x900",
            "1280x720",  # 720p
            "854x480",  # 480p
            "640x360",  # 360p
            # 竖屏
            "2160x3840",  # 4K
            "1440x2560",  # 2K
            "900x1600",
            "1080x1920",  # 1080p
            "720x1280",  # 720p
            "480x854",  # 480p
            "360x640",  # 360p
        ]

        def on_resolution_change(*args):
            UserConfig.save_settings_to_json(self)

        combo = ttk.Combobox(frame,
                             values=resolutions,
                             state='readonly',
                             textvariable=self.out_resolution)
        combo.pack(side=tk.RIGHT)

        # 添加变量跟踪
        self.out_resolution.trace_add('write', on_resolution_change)

    def validate_duration(self, value):
        """验证持续时间输入"""
        if value == "":
            return True
        try:
            val = int(value)
            return 2 <= val <= 60
        except ValueError:
            return False

    def validate_float(self, value):
        """验证浮点数输入"""
        if value == "":
            return True
        try:
            val = float(value)
            return val > 0
        except ValueError:
            return False

    def show_frame(self, frame):
        """显示指定的框架"""
        # 隐藏所有框架
        for f in (self.home_frame, self.settings_frame, self.help_frame):
            f.pack_forget()
        # 显示选定的框架
        frame.pack(fill=tk.BOTH, expand=True)

    def show_content1(self):
        """显示主页"""
        self.highlight_button(self.menu_buttons["🏠 主页"])
        self.show_frame(self.home_frame)

    def show_content2(self):
        """显示设置页面"""
        self.highlight_button(self.menu_buttons["⚙ 设置"])
        self.show_frame(self.settings_frame)

    def help_info(self):
        """显示帮助页面"""
        self.highlight_button(self.menu_buttons["❓ 帮助"])
        self.show_frame(self.help_frame)

    def reset_content(self):
        self.path_entry.delete(0, tk.END)
        self.log_text.delete(1.0, tk.END)  # 清空日志区域

    def help_info(self):
        """显示帮助页面"""
        self.highlight_button(self.menu_buttons["❓ 帮助"])
        self.show_frame(self.help_frame)


if __name__ == "__main__":
    app = ModernApp()
    app.mainloop()
