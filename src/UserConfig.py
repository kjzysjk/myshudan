import json
import os
import tkinter as tk


def init(self):
    self.video_duration = tk.IntVar(value=5)
    self.transition_duration = tk.DoubleVar(value=1.2)
    self.out_resolution = tk.StringVar(value='自动')
    self.background_volume = tk.DoubleVar(value=50)

def load_settings(self, filename='settings.json'):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        self.out_resolution.set(settings.get('out_resolution', '自动'))
        self.video_duration.set(settings.get('video_duration', 5))
        self.background_volume.set(settings.get('background_volume', 50))
        self.transition_duration.set(settings.get('transition_duration', 0.75))
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        pass

def save_settings_to_json(self, filename='settings.json'):
    settings = {
        'video_duration': self.video_duration.get(),
        'transition_duration': self.transition_duration.get(),
        'out_resolution': self.out_resolution.get(),
        'background_volume': self.background_volume.get()
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)


def load_api_settings():
    config_file = "ApiSetting.cfg"
    try:
        # 检查配置文件是否存在
        if not os.path.exists(config_file):
            return None, None

        # 读取配置文件
        with open(config_file, 'r') as f:
            config_data = f.read().splitlines()

        api_host = None
        api_secret = None
        local_mode = None

        # 解析每一行
        for line in config_data:
            line = line.strip()
            if line.startswith('api_host='):
                api_host = line.split('=')[1].strip()
            elif line.startswith('api_secret='):
                api_secret = line.split('=')[1].strip()
            elif line.startswith('local_mode='):
                local_mode = line.split('=')[1].strip()

        return api_host, api_secret, local_mode

    except Exception as e:
        return None, None
