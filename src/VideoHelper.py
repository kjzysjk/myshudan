import os
import re
import shlex
import shutil
import subprocess
import cv2
import numpy as np


def ImageToVideo(self, image_paths, image_prefix, transition_duration,width, height):
    video_list = []
    # 创建视频
    for idx, img in enumerate(image_paths):
        try:

            # 安全读取图片（支持中文路径）
            img_data = cv2.imdecode(
                np.fromfile(img, dtype=np.uint8),
                cv2.IMREAD_COLOR
            )
            # 创建输出目录
            output_dir = os.path.dirname(image_prefix)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 创建视频
            output_path = f'{image_prefix}{idx}_video.mp4'
            fps = 30
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            # 写入帧
            for _ in range(5 * fps):
                out.write(img_data)

            self.log(f"成功生成片段视频: {output_path}")
            video_list.append(output_path)

        except Exception as e:
            self.task_wait = False
            self.err = False
            self.log(f"处理图片 {img} 时出错: {str(e)}")

        finally:
            if 'out' in locals():
                out.release()

    self.remove_file(self.result_file)
    merge_videos(self, video_list, self.result_file, transition_duration)


def merge_videos(self, video_list, output_file, transition_duration):
    try:
        # 规范化路径并验证文件
        video_list2 = []
        for video in video_list:
            normalized_path = video.replace('\\', '/')
            if not os.path.exists(video):
                self.log(f"视频文件未找到: {video}")
                self.task_wait = False
                self.err = True  # 注意：这里改为True可能更合适
                return False
            video_list2.append(normalized_path)

        # 规范化输出路径
        output_file = output_file.replace('\\', '/')
        temp_dir = self.TEMP_DIR.replace('\\', '/')

        # 构建命令字符串
        cmd = f'ffmpeg-concat -t InvertedPageCurl -O "{temp_dir}" -d {transition_duration} -o "{output_file}"'

        # 添加视频文件列表，确保路径被引号包围
        for video in video_list2:
            cmd += f' "{video}"'

        self.log(f"执行cmd: {cmd}")

        # 执行命令
        result = subprocess.run(cmd,
                                shell=True,
                                check=True,
                                capture_output=True,
                                text=True,
                                encoding='utf-8', errors='replace')

        # 如果有输出，记录到日志
        if result.stdout:
            self.log(f"命令输出: {result.stdout}")

        self.task_wait = False
        self.err = False
        self.err_message = ''
        self.log(f"成功合成结果视频: {output_file}")
        self.log(f"...")
        return True

    except subprocess.CalledProcessError as ex:
        self.task_wait = False
        self.err = True
        self.err_message = str(ex)
        self.log(f"命令执行失败: {ex}")
        if hasattr(ex, 'stderr'):
            self.log(f"错误输出: {ex.stderr}")
        self.log(f"...")
        return False

    except Exception as ex:
        self.task_wait = False
        self.err = True
        self.err_message = str(ex)
        self.log(f"执行过程出错: {ex}")
        self.log(f"...")
        return False

    finally:
        # 清理临时文件
        try:
            for video in video_list:
                self.remove_file(video)
            clean_raw_files(self, self.TEMP_DIR)
        except Exception as ex:
            self.log(f"清理临时文件时出错: {ex}")

def clean_raw_files(self, directory):
    # 帧文件
    for filename in os.listdir(directory):
        if filename.endswith('.raw'):
            file_path = os.path.join(directory, filename)
            self.remove_file(file_path)


def check_audio_stream(file_path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0", "-count_packets", "-show_entries",
           "stream=nb_read_packets", "-of", "csv=p=0", file_path]
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, startupinfo=startupinfo)
        result_str = result.decode('utf-8').strip()
        return result_str != "" and int(result_str) > 0
    except (subprocess.CalledProcessError, ValueError):
        return False


def adjust_audio_volume(self, input_audio_path, volume):
    if volume != 100:
        volume_scale = volume / 100.0
        b_name = os.path.basename(input_audio_path)
        temp_audio_path = os.path.join(self.TEMP_DIR, f"tmp_{b_name}")
        output_audio_path = os.path.join(self.TEMP_DIR, f"tmp_out_{b_name}")
        shutil.copy(input_audio_path, temp_audio_path)  # 操作镜像文件 不影响原文件

        command = [
            "ffmpeg",
            "-i", temp_audio_path,
            "-filter:a", f"volume={volume_scale}",
            "-y",  # 覆盖输出文件(如果存在)
            output_audio_path
        ]
        try:
            run_cmd_ffmpeg(self, command)
            self.remove_file(temp_audio_path)
            return output_audio_path
        except Exception as e:
            self.err = True
            self.task_wait = False
            self.log(f"BGM音量修改过程出错: {e}")
            return temp_audio_path
    else:
        return input_audio_path
        self.progress_text.insert(tk.END, f"无需要调整\n")
        self.progress_text.see(tk.END)

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
           "default=noprint_wrappers=1:nokey=1", file_path]
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, startupinfo=startupinfo)
        output = result.decode('utf-8', errors='replace').strip()

        duration_match = re.search(r'\d+\.\d+', output)
        if duration_match:
            return float(duration_match.group())
        else:
            raise ValueError(f"无法从输出中提取持续时间: {output}")
    except subprocess.CalledProcessError as e:
        error_output = e.output.decode('utf-8', errors='replace')
        raise ValueError(f"获取文件持续时间时出错: {error_output}")

def merge_backgroud_audio(self, full_video_path, full_audio_path, output_file, volume):
    self.log(f"{full_video_path}, {full_audio_path}, {output_file}, {volume}")
    full_audio_path = adjust_audio_volume(self, full_audio_path, volume)
    mute_original = False
    try:
        video_duration = get_duration(full_video_path)
        audio_duration = get_duration(full_audio_path)
    except ValueError as e:
        self.err = True
        self.task_wait = False
        self.log(f"BGM合成不成功: {e}")
        return

    has_audio = check_audio_stream(full_video_path)

    if not has_audio:
        mute_original = True

        # 构建基本命令
    command = ["ffmpeg", "-i", full_video_path, "-i", full_audio_path]

    # 构建复杂的滤镜图
    filter_complex = []

    if audio_duration > video_duration:
        # 处理音频比视频长的情况
        fade_duration = 3
        filter_complex.append(
            f"[1:a]atrim=0:{video_duration},asetpts=PTS-STARTPTS,afade=t=out:st={video_duration - fade_duration}:d={fade_duration}[trimmed_audio]"
        )
    else:
        # 处理视频比音频长的情况
        loop_count = int(video_duration / audio_duration) + 1
        filter_complex.append(f"[1:a]aloop=loop={loop_count}:size={int(audio_duration * 48000)}[looped_audio]")

    # 添加混音滤镜（如果不屏蔽原视频声音）
    if not mute_original and has_audio:
        if audio_duration > video_duration:
            filter_complex.append("[0:a][trimmed_audio]amix=inputs=2:duration=first[final_audio]")
        else:
            filter_complex.append("[0:a][looped_audio]amix=inputs=2:duration=first[final_audio]")
    else:
        if audio_duration > video_duration:
            filter_complex.append("[trimmed_audio]acopy[final_audio]")
        else:
            filter_complex.append("[looped_audio]acopy[final_audio]")

    # 合并滤镜图
    if filter_complex:
        command.extend(["-filter_complex", ";".join(filter_complex)])

    # 添加映射
    command.extend(["-map", "0:v:0", "-map", "[final_audio]"])

    # 添加其他参数
    command.extend(["-c:v", "copy", "-c:a", "aac", "-shortest", output_file])

    try:
        run_cmd_ffmpeg(self, command)
        if volume != 100:
            if full_audio_path.find("tmp") != -1:
                self.remove_file(full_audio_path)
        self.log(f"BGM 合并完成")
    except Exception as e:
        self.err = True
        self.task_wait = False
        self.log(f"BGM添加到视频失败: {e}")

def run_cmd_ffmpeg(self, cmd, format_cmd=True):
    try:
        if format_cmd:
            if isinstance(cmd, str):
                cmd = shlex.split(cmd)
            else:
                cmd = [str(item) for item in cmd]  # 确保所有项都是字符串

        # 添加 -loglevel debug 选项以获取详细输出
        # cmd = ['-loglevel', 'debug'] + cmd

        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace')

        for line in process.stdout:
            self.task_wait = False
            self.log(line)

        process.wait()
        if process.returncode != 0:
            self.err = True
            self.task_wait = False
            self.log(f"RETURN CODE ERROR: {process.returncode}")
    except Exception as e:
        self.err = True
        self.task_wait = False
        self.log(f"FFMPEG ERROR: {e}")
